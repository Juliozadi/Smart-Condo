"""Agendamento de mudança.

O caminhão chegava sem aviso, ocupava o elevador de serviço a manhã
inteira e encontrava outra mudança na mesma hora; a portaria não sabia
se podia deixar entrar. O morador pede o dia e o horário dentro do que o
regimento permite, o síndico aprova ou recusa, e a portaria vê as
aprovadas. Uma mudança de cada vez em cada bloco: o elevador de serviço
é um só.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from app.api.deps import (
    conferir_que_mora, exigir_condominio, exigir_morador_residente, exigir_papel,
)
from app.core.database import get_db
from app.core.tempo import agora_local
from app.models.condominio import Condominio, Unidade
from app.models.enums import CanalVerificacao, Papel, StatusMudanca, StatusUsuario
from app.models.mudanca import HorarioMudanca, Mudanca
from app.models.usuario import Usuario
from app.schemas.mudanca import (
    ANTECEDENCIA_MAXIMA_DIAS, AvaliacaoMudanca, CancelamentoMudanca, HorarioDoDia,
    MudancaEntrada, MudancaSaida, RegrasMudanca, RegrasMudancaEntrada,
)
from app.services import notificacao, registro

router = APIRouter(prefix="/mudancas", tags=["Mudanças"])

# A regra padrão, para o condomínio cujo síndico ainda não definiu a do
# regimento: aviso prévio para o síndico avaliar e a portaria se preparar;
# de segunda a sábado, em horário comercial, e no sábado só de manhã (o
# barulho no fim de semana incomoda); domingo não.
ANTECEDENCIA_MINIMA_DIAS = 2
HORARIOS = {
    1: (time(8), time(18)), 2: (time(8), time(18)), 3: (time(8), time(18)),
    4: (time(8), time(18)), 5: (time(8), time(18)), 6: (time(8), time(12)),
}
# Pedidos de pé por apartamento: contra engano e contra quem segura vários
# horários "por via das dúvidas".
LIMITE_ATIVAS = 3

STATUS_QUE_OCUPAM = (StatusMudanca.PENDENTE, StatusMudanca.APROVADA)
MOTIVO_SEM_AVALIACAO = "O horário chegou sem a avaliação do síndico."


def _agora() -> datetime:
    return agora_local()


def _hora(t: time) -> str:
    return f"{t.hour}h" if not t.minute else f"{t.hour}h{t.minute:02d}"


def _quando(m: Mudanca) -> str:
    return f"{m.data:%d/%m/%Y}, das {m.hora_inicio:%H:%M} às {m.hora_fim:%H:%M}"


def _saida(m: Mudanca) -> MudancaSaida:
    return MudancaSaida(
        id=m.id, unidade_id=m.unidade_id, unidade=m.unidade.identificacao, tipo=m.tipo,
        data=m.data, hora_inicio=m.hora_inicio, hora_fim=m.hora_fim, empresa=m.empresa,
        observacao=m.observacao, status=m.status,
        solicitada_por_nome=m.solicitada_por.nome if m.solicitada_por else None,
        motivo_recusa=m.motivo_recusa,
        cancelada_pelo_sindico=bool(m.cancelada_por and m.cancelada_por.papel == Papel.SINDICO),
        motivo_cancelamento=m.motivo_cancelamento, criado_em=m.criado_em,
    )


def _consulta(condominio_id: int):
    return (
        select(Mudanca)
        .options(selectinload(Mudanca.unidade), selectinload(Mudanca.solicitada_por),
                 selectinload(Mudanca.cancelada_por))
        .where(Mudanca.condominio_id == condominio_id)
    )


def _do_morador(morador: Usuario):
    """As mudanças do apartamento pedidas desde que o morador mora lá: o
    novo morador não vê a saída de quem morava antes."""
    return and_(Mudanca.unidade_id == morador.unidade_id,
                Mudanca.criado_em >= morador.unidade_desde)


def _ja_comecou(m: Mudanca, agora: datetime) -> bool:
    return m.data < agora.date() or (m.data == agora.date() and m.hora_inicio <= agora.time())


def _encerrar_passadas(db: Session, condominio_id: int) -> None:
    """Como nas reservas: a aprovada cujo horário terminou vira concluída,
    e a pendente cujo horário chegou sem avaliação vira recusada."""
    agora = _agora()
    hoje, hora = agora.date(), agora.time()
    db.execute(
        update(Mudanca)
        .where(Mudanca.condominio_id == condominio_id, Mudanca.status == StatusMudanca.APROVADA,
               or_(Mudanca.data < hoje, and_(Mudanca.data == hoje, Mudanca.hora_fim <= hora)))
        .values(status=StatusMudanca.CONCLUIDA)
        .execution_options(synchronize_session=False)
    )
    db.execute(
        update(Mudanca)
        .where(Mudanca.condominio_id == condominio_id, Mudanca.status == StatusMudanca.PENDENTE,
               or_(Mudanca.data < hoje,
                   and_(Mudanca.data == hoje, Mudanca.hora_inicio <= hora)))
        .values(status=StatusMudanca.RECUSADA, motivo_recusa=MOTIVO_SEM_AVALIACAO)
        .execution_options(synchronize_session=False)
    )
    db.commit()


def _sindicos(db: Session, condominio_id: int) -> list[Usuario]:
    return list(db.scalars(select(Usuario).where(
        Usuario.condominio_id == condominio_id, Usuario.papel == Papel.SINDICO,
        Usuario.status == StatusUsuario.ATIVO,
    )).all())


def _moradores(db: Session, unidade_id: int) -> list[Usuario]:
    return list(db.scalars(select(Usuario).where(
        Usuario.unidade_id == unidade_id, Usuario.papel == Papel.MORADOR,
        Usuario.status == StatusUsuario.ATIVO, Usuario.reside.is_(True),
    )).all())


def _avisar(destinos: list[Usuario], titulo: str, mensagem: str) -> None:
    for u in destinos:
        notificacao.notificar(u.email, CanalVerificacao.EMAIL, titulo, mensagem)


NOS_DIAS = {1: "às segundas-feiras", 2: "às terças-feiras", 3: "às quartas-feiras",
            4: "às quintas-feiras", 5: "às sextas-feiras", 6: "aos sábados", 7: "aos domingos"}


def _regras_do_condominio(db: Session, condominio_id: int) -> tuple[int, dict[int, tuple]]:
    """O aviso mínimo e os horários de cada dia, como o síndico definiu;
    sem definição, a regra padrão."""
    linhas = db.scalars(select(HorarioMudanca).where(
        HorarioMudanca.condominio_id == condominio_id)).all()
    condominio = db.get(Condominio, condominio_id)
    antecedencia = condominio.mudanca_antecedencia_dias if condominio else ANTECEDENCIA_MINIMA_DIAS
    if not linhas:
        return antecedencia, dict(HORARIOS)
    return antecedencia, {h.dia_semana: (h.hora_inicio, h.hora_fim) for h in linhas}


def _conferir_regimento(dados: MudancaEntrada, hoje: date, antecedencia: int,
                        horarios: dict[int, tuple]) -> None:
    def recusar(motivo: str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=motivo)

    if dados.data < hoje + timedelta(days=antecedencia):
        recusar(f"Agende a mudança com pelo menos {antecedencia} dias de "
                "antecedência, para o síndico avaliar e a portaria se preparar.")
    dia = dados.data.isoweekday()
    horario = horarios.get(dia)
    if horario is None:
        recusar(f"Não há mudança {NOS_DIAS[dia]}, pelo regimento do condomínio.")
    inicio, fim = horario
    nos_dias = NOS_DIAS[dia][0].upper() + NOS_DIAS[dia][1:]
    if dados.hora_inicio < inicio:
        recusar(f"{nos_dias}, a mudança pode começar a partir das {_hora(inicio)}.")
    if dados.hora_fim > fim:
        recusar(f"{nos_dias}, a mudança precisa terminar até as {_hora(fim)}.")


def _mudanca_visivel(db: Session, usuario: Usuario, mudanca_id: int) -> Mudanca:
    """Travada até o commit: o síndico pode estar avaliando enquanto o
    morador cancela, e só um dos dois pode valer."""
    m = db.get(Mudanca, mudanca_id, with_for_update=True)
    visivel = m is not None and m.condominio_id == usuario.condominio_id and (
        usuario.papel == Papel.SINDICO
        or (usuario.papel == Papel.MORADOR and m.unidade_id == usuario.unidade_id
            and m.criado_em >= usuario.unidade_desde)
    )
    if not visivel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Mudança não encontrada.")
    return m


def _regras_saida(db: Session, condominio_id: int) -> RegrasMudanca:
    antecedencia, horarios = _regras_do_condominio(db, condominio_id)
    return RegrasMudanca(
        antecedencia_minima_dias=antecedencia,
        antecedencia_maxima_dias=ANTECEDENCIA_MAXIMA_DIAS,
        horarios={dia: HorarioDoDia(inicio=i, fim=f) for dia, (i, f) in sorted(horarios.items())},
    )


def _descrever(antecedencia: int, horarios: dict[int, tuple]) -> str:
    dias = "; ".join(f"{NOS_DIAS[d]} das {_hora(i)} às {_hora(f)}"
                     for d, (i, f) in sorted(horarios.items()))
    return f"Regras de mudança: {antecedencia} dias de aviso; {dias}"


@router.get("/regras", response_model=RegrasMudanca, summary="Regras do regimento para mudanças")
def regras(usuario: Usuario = Depends(exigir_condominio),
           db: Session = Depends(get_db)) -> RegrasMudanca:
    return _regras_saida(db, usuario.condominio_id)


@router.put("/regras", response_model=RegrasMudanca,
            summary="Define as regras de mudança do regimento")
def definir_regras(
    dados: RegrasMudancaEntrada,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> RegrasMudanca:
    """Valem para os pedidos feitos daqui em diante; as mudanças já
    agendadas continuam de pé (o síndico cancela, com motivo, se preciso)."""
    condominio = db.get(Condominio, sindico.condominio_id, with_for_update=True)
    antes = _descrever(*_regras_do_condominio(db, condominio.id))
    condominio.mudanca_antecedencia_dias = dados.antecedencia_minima_dias
    db.execute(delete(HorarioMudanca).where(HorarioMudanca.condominio_id == condominio.id))
    for dia, h in dados.horarios.items():
        db.add(HorarioMudanca(condominio_id=condominio.id, dia_semana=dia,
                              hora_inicio=h.inicio, hora_fim=h.fim))
    db.flush()
    depois = _descrever(*_regras_do_condominio(db, condominio.id))
    if depois != antes:
        registro.registrar(db, sindico, registro.EDITOU, registro.CONDOMINIO, condominio.id,
                           depois)
    db.commit()
    return _regras_saida(db, condominio.id)


@router.get("/ocupados", response_model=list[HorarioDoDia],
            summary="Horários já tomados num dia, sem dizer de quem")
def ocupados(
    data: date = Query(...),
    morador: Usuario = Depends(exigir_morador_residente),
    db: Session = Depends(get_db),
) -> list[HorarioDoDia]:
    unidade = db.get(Unidade, morador.unidade_id) if morador.unidade_id else None
    if unidade is None:
        return []
    linhas = db.execute(
        select(Mudanca.hora_inicio, Mudanca.hora_fim)
        .join(Unidade, Unidade.id == Mudanca.unidade_id)
        .where(Mudanca.condominio_id == morador.condominio_id, Unidade.bloco == unidade.bloco,
               Mudanca.data == data, Mudanca.status.in_(STATUS_QUE_OCUPAM))
        .order_by(Mudanca.hora_inicio)
    ).all()
    return [HorarioDoDia(inicio=i, fim=f) for i, f in linhas]


@router.get("", response_model=list[MudancaSaida], summary="Mudanças agendadas")
def listar(
    status_: StatusMudanca | None = Query(default=None, alias="status"),
    usuario: Usuario = Depends(exigir_papel(Papel.SINDICO, Papel.MORADOR, Papel.PORTEIRO)),
    db: Session = Depends(get_db),
) -> list[MudancaSaida]:
    """O morador vê as do apartamento; o síndico, todas; a portaria, as
    aprovadas de hoje em diante — é o que ela precisa para deixar entrar."""
    if usuario.condominio_id is None:
        return []
    _encerrar_passadas(db, usuario.condominio_id)
    consulta = _consulta(usuario.condominio_id)
    if usuario.papel == Papel.PORTEIRO:
        consulta = consulta.where(Mudanca.status == StatusMudanca.APROVADA,
                                  Mudanca.data >= _agora().date())
        ordem = (Mudanca.data, Mudanca.hora_inicio)
    else:
        if usuario.papel == Papel.MORADOR:
            conferir_que_mora(usuario)
            consulta = consulta.where(_do_morador(usuario))
        if status_ is not None:
            consulta = consulta.where(Mudanca.status == status_)
        ordem = (Mudanca.data.desc(), Mudanca.hora_inicio.desc())
    return [_saida(m) for m in db.scalars(consulta.order_by(*ordem).limit(300)).all()]


@router.post("", response_model=MudancaSaida, status_code=status.HTTP_201_CREATED,
             summary="Pedir a mudança")
def agendar(
    dados: MudancaEntrada,
    morador: Usuario = Depends(exigir_morador_residente),
    db: Session = Depends(get_db),
) -> MudancaSaida:
    unidade = db.get(Unidade, morador.unidade_id) if morador.unidade_id else None
    if unidade is None or unidade.condominio_id != morador.condominio_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Seu cadastro não está ligado a um apartamento.")
    agora = _agora()
    _conferir_regimento(dados, agora.date(), *_regras_do_condominio(db, morador.condominio_id))

    # Dois pedidos para o mesmo bloco e dia esperam um pelo outro; sem isso,
    # os dois passariam pela conferência de horário ao mesmo tempo.
    db.execute(select(func.pg_advisory_xact_lock(
        morador.condominio_id, func.hashtext(f"mudanca:{unidade.bloco}:{dados.data}"))))
    conflito = db.scalar(
        select(func.count()).select_from(Mudanca)
        .join(Unidade, Unidade.id == Mudanca.unidade_id)
        .where(Mudanca.condominio_id == morador.condominio_id, Unidade.bloco == unidade.bloco,
               Mudanca.data == dados.data, Mudanca.status.in_(STATUS_QUE_OCUPAM),
               Mudanca.hora_inicio < dados.hora_fim, Mudanca.hora_fim > dados.hora_inicio)
    )
    if conflito:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já há outra mudança marcada nesse horário — o elevador de serviço é um "
                   "só. Escolha outro horário.",
        )
    ativas = db.scalar(
        select(func.count()).select_from(Mudanca)
        .where(Mudanca.unidade_id == unidade.id, Mudanca.status.in_(STATUS_QUE_OCUPAM),
               Mudanca.data >= agora.date())
    )
    if ativas >= LIMITE_ATIVAS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O apartamento já tem {ativas} mudanças agendadas, o limite. Cancele "
                   "uma antes de pedir outra.",
        )

    m = Mudanca(condominio_id=morador.condominio_id, unidade_id=unidade.id,
                solicitada_por_id=morador.id, status=StatusMudanca.PENDENTE,
                **dados.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    _avisar(_sindicos(db, m.condominio_id), "Mudança para avaliar",
            f"O apartamento {unidade.identificacao} pediu uma mudança "
            f"({m.tipo.value}) em {_quando(m)}. Aprove ou recuse pelo SmartCondo.")
    return _saida(m)


@router.post("/{mudanca_id}/avaliacao", response_model=MudancaSaida,
             summary="Aprovar ou recusar a mudança")
def avaliar(
    mudanca_id: int,
    dados: AvaliacaoMudanca,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> MudancaSaida:
    m = _mudanca_visivel(db, sindico, mudanca_id)
    if m.status != StatusMudanca.PENDENTE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Esta mudança já foi avaliada ou cancelada.")
    if dados.aprovada and _ja_comecou(m, _agora()):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="O horário desta mudança já passou. Ela só pode ser recusada.")
    m.status = StatusMudanca.APROVADA if dados.aprovada else StatusMudanca.RECUSADA
    m.motivo_recusa = None if dados.aprovada else dados.motivo
    m.avaliada_por_id = sindico.id
    m.avaliada_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(m)
    if dados.aprovada:
        _avisar(_moradores(db, m.unidade_id), "Mudança aprovada",
                f"Sua mudança em {_quando(m)} foi aprovada. A portaria já está avisada.")
    else:
        _avisar(_moradores(db, m.unidade_id), "Mudança recusada",
                f"Sua mudança em {_quando(m)} foi recusada pelo síndico. Motivo: {m.motivo_recusa}")
    return _saida(m)


@router.post("/{mudanca_id}/cancelamento", response_model=MudancaSaida,
             summary="Cancelar a mudança")
def cancelar(
    mudanca_id: int,
    dados: CancelamentoMudanca | None = None,
    usuario: Usuario = Depends(exigir_papel(Papel.SINDICO, Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> MudancaSaida:
    conferir_que_mora(usuario)
    m = _mudanca_visivel(db, usuario, mudanca_id)
    if m.status not in STATUS_QUE_OCUPAM:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Esta mudança não está mais agendada.")
    if _ja_comecou(m, _agora()):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="O horário desta mudança já chegou.")
    motivo = dados.motivo if dados else None
    pelo_sindico = usuario.papel == Papel.SINDICO
    if pelo_sindico and not (motivo and len(motivo) >= 3):
        raise HTTPException(status_code=422,
                            detail="Informe o motivo do cancelamento; o morador recebe.")
    estava_aprovada = m.status == StatusMudanca.APROVADA
    m.status = StatusMudanca.CANCELADA
    m.cancelada_por_id = usuario.id
    m.cancelada_em = datetime.now(timezone.utc)
    m.motivo_cancelamento = motivo
    db.commit()
    db.refresh(m)
    if pelo_sindico:
        _avisar(_moradores(db, m.unidade_id), "Mudança cancelada",
                f"Sua mudança em {_quando(m)} foi cancelada pelo síndico. Motivo: {motivo}")
    elif estava_aprovada:
        _avisar(_sindicos(db, m.condominio_id), "Mudança cancelada",
                f"O apartamento {m.unidade.identificacao} cancelou a mudança aprovada "
                f"para {_quando(m)}.")
    return _saida(m)

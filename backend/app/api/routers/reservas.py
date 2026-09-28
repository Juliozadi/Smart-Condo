"""Espaços comuns, reservas e ocupação em tempo real.

Documentação, seção 6 (História do Usuário) e seção 13.5.3 (o síndico
aprova ou recusa e vê o histórico).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.api.deps import exigir_condominio, exigir_papel, get_usuario_atual
from app.core.config import settings
from app.core.database import get_db
from app.core.tempo import agora_local, hoje_local
from app.models.condominio import Unidade
from app.models.enums import Papel, StatusReserva
from app.models.espaco import EspacoComum, RegistroOcupacao, Reserva
from app.models.usuario import Usuario
from app.schemas.comuns import Mensagem
from app.schemas.condominio import (
    EspacoAtualizacao, EspacoEntrada, EspacoSaida, OcupacaoEntrada, OcupacaoSaida,
)
from app.schemas.reserva import (
    AvaliacaoReserva, OcupacaoAgenda, ReservaEntrada, ReservaSaida, ReservaSindicoSaida,
)
from app.services import registro

router = APIRouter(prefix="/espacos", tags=["Espaços e Reservas"])

# Uma reserva só bloqueia o espaço enquanto está de pé.
STATUS_QUE_OCUPAM = (StatusReserva.PENDENTE, StatusReserva.APROVADA)


def _espaco_do_condominio(db: Session, usuario: Usuario, espaco_id: int,
                          incluir_inativo: bool = False) -> EspacoComum:
    espaco = db.get(EspacoComum, espaco_id)
    if (espaco is None or espaco.condominio_id != usuario.condominio_id
            or (espaco.inativo and not incluir_inativo)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Espaço não encontrado."
        )
    return espaco


def _espacos_saida(db: Session, espacos, com_autoria: bool) -> list[EspacoSaida]:
    ultimas = registro.ultimas(db, registro.ESPACO, (e.id for e in espacos)) if com_autoria else {}
    return [
        EspacoSaida.model_validate(e).model_copy(update={"ultima_alteracao": ultimas.get(e.id)})
        for e in espacos
    ]


def _para_saida(reserva: Reserva) -> ReservaSaida:
    return ReservaSaida(
        id=reserva.id,
        espaco_id=reserva.espaco_id,
        espaco_nome=reserva.espaco.nome,
        data=reserva.data,
        hora_inicio=reserva.hora_inicio,
        hora_fim=reserva.hora_fim,
        pessoas_estimadas=reserva.pessoas_estimadas,
        observacoes=reserva.observacoes,
        status=reserva.status,
        motivo_recusa=reserva.motivo_recusa,
        criado_em=reserva.criado_em,
    )


# ── Espaços ──────────────────────────────────────────────────────────
@router.get("", response_model=list[EspacoSaida], summary="Lista os espaços do condomínio")
def listar_espacos(
    todos: bool = Query(default=False, description="Síndico: inclui os inativos."),
    usuario: Usuario = Depends(exigir_condominio), db: Session = Depends(get_db),
) -> list[EspacoSaida]:
    sindico = usuario.papel == Papel.SINDICO
    consulta = select(EspacoComum).where(EspacoComum.condominio_id == usuario.condominio_id)
    if not (todos and sindico):
        consulta = consulta.where(EspacoComum.inativo_em.is_(None))
    # Os inativos vão para o fim da lista.
    espacos = db.scalars(
        consulta.order_by(EspacoComum.inativo_em.is_not(None), EspacoComum.nome)
    ).all()
    return _espacos_saida(db, espacos, com_autoria=sindico)


@router.post(
    "",
    response_model=EspacoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um espaço comum",
)
def cadastrar_espaco(
    dados: EspacoEntrada,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> EspacoSaida:
    if sindico.condominio_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Cadastre o condomínio primeiro."
        )
    espaco = EspacoComum(condominio_id=sindico.condominio_id, **dados.model_dump())
    db.add(espaco)
    db.flush()
    registro.registrar(db, sindico, registro.CRIOU, registro.ESPACO, espaco.id)
    db.commit()
    db.refresh(espaco)
    return _espacos_saida(db, [espaco], com_autoria=True)[0]


ROTULOS_ESPACO = {
    "nome": "o nome", "descricao": "a descrição", "capacidade": "a capacidade",
    "reservavel": "o tipo", "uso_livre": "o tipo", "em_manutencao": "a manutenção",
}


def _espaco_travado(db: Session, sindico: Usuario, espaco_id: int) -> EspacoComum:
    espaco = _espaco_do_condominio(db, sindico, espaco_id, incluir_inativo=True)
    # Trava a linha: a reserva também trava o espaço antes de conferir.
    db.refresh(espaco, with_for_update=True)
    return espaco


@router.put("/{espaco_id}", response_model=EspacoSaida, summary="Edita um espaço comum")
def editar_espaco(
    espaco_id: int,
    dados: EspacoAtualizacao,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> EspacoSaida:
    espaco = _espaco_travado(db, sindico, espaco_id)
    novos = dados.model_dump(exclude_unset=True)
    reservavel = novos.get("reservavel", espaco.reservavel)
    uso_livre = novos.get("uso_livre", espaco.uso_livre)
    if not reservavel and not uso_livre:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O espaço precisa ser reservável ou de uso livre.",
        )
    mudaram = {c: v for c, v in novos.items() if getattr(espaco, c) != v}
    # "reservavel" e "uso_livre" mudam juntos quando o tipo troca: um rótulo só.
    rotulos = dict(ROTULOS_ESPACO)
    if "reservavel" in mudaram and "uso_livre" in mudaram:
        rotulos.pop("uso_livre")
    descricao = registro.campos_alterados(espaco, mudaram, rotulos)
    for campo, valor in mudaram.items():
        setattr(espaco, campo, valor)
    if descricao:
        registro.registrar(db, sindico, registro.EDITOU, registro.ESPACO, espaco.id, descricao)
    db.commit()
    db.refresh(espaco)
    return _espacos_saida(db, [espaco], com_autoria=True)[0]


@router.delete("/{espaco_id}", response_model=Mensagem, summary="Inativa um espaço comum")
def inativar_espaco(
    espaco_id: int,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> Mensagem:
    """Nada é apagado: o espaço some das telas, mas as reservas passadas e
    a ocupação continuam no histórico. As reservas de hoje em diante são
    canceladas, senão o morador ficava com uma reserva num espaço que não
    existe mais."""
    espaco = _espaco_travado(db, sindico, espaco_id)
    if espaco.inativo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Este espaço já está inativo."
        )
    canceladas = db.execute(
        update(Reserva)
        .where(
            Reserva.espaco_id == espaco.id,
            Reserva.status.in_(STATUS_QUE_OCUPAM),
            Reserva.data >= hoje_local(),
        )
        .values(status=StatusReserva.CANCELADA)
        .execution_options(synchronize_session=False)
    ).rowcount
    espaco.inativo_em = datetime.now(timezone.utc)
    espaco.inativado_por_id = sindico.id
    descricao = None
    if canceladas:
        descricao = ("1 reserva futura cancelada" if canceladas == 1
                     else f"{canceladas} reservas futuras canceladas")
    registro.registrar(db, sindico, registro.INATIVOU, registro.ESPACO, espaco.id, descricao)
    db.commit()
    return Mensagem(detalhe="Espaço inativado." + (f" {descricao}." if descricao else ""))


@router.post(
    "/{espaco_id}/reativacao", response_model=EspacoSaida, summary="Reativa um espaço comum"
)
def reativar_espaco(
    espaco_id: int,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> EspacoSaida:
    espaco = _espaco_travado(db, sindico, espaco_id)
    if not espaco.inativo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Este espaço já está ativo."
        )
    espaco.inativo_em = None
    espaco.inativado_por_id = None
    registro.registrar(db, sindico, registro.REATIVOU, registro.ESPACO, espaco.id)
    db.commit()
    db.refresh(espaco)
    return _espacos_saida(db, [espaco], com_autoria=True)[0]


# ── Ocupação em tempo real (seção 6) ─────────────────────────────────
@router.get(
    "/ocupacao",
    response_model=list[OcupacaoSaida],
    summary="Ocupação atual das áreas de uso livre",
)
def consultar_ocupacao(
    usuario: Usuario = Depends(exigir_condominio), db: Session = Depends(get_db)
) -> list[OcupacaoSaida]:
    """"Piscina: 23 pessoas no momento" (seção 6)."""
    espacos = db.scalars(
        select(EspacoComum)
        .where(
            EspacoComum.condominio_id == usuario.condominio_id,
            EspacoComum.uso_livre.is_(True),
            EspacoComum.inativo_em.is_(None),
        )
        .order_by(EspacoComum.nome)
    ).all()

    resposta: list[OcupacaoSaida] = []
    for espaco in espacos:
        ultimo = db.scalar(
            select(RegistroOcupacao)
            .where(RegistroOcupacao.espaco_id == espaco.id)
            .order_by(RegistroOcupacao.registrado_em.desc(), RegistroOcupacao.id.desc())
            .limit(1)
        )
        pessoas = ultimo.pessoas if ultimo else 0
        percentual = round(pessoas / espaco.capacidade * 100) if espaco.capacidade else 0
        resposta.append(
            OcupacaoSaida(
                espaco_id=espaco.id,
                espaco_nome=espaco.nome,
                pessoas=pessoas,
                capacidade=espaco.capacidade,
                percentual=min(percentual, 100),
                atualizado_em=ultimo.registrado_em if ultimo else None,
            )
        )
    return resposta


@router.post(
    "/{espaco_id}/ocupacao",
    response_model=OcupacaoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Registra a contagem de pessoas numa área",
)
def registrar_ocupacao(
    espaco_id: int,
    dados: OcupacaoEntrada,
    usuario: Usuario = Depends(exigir_papel(Papel.SINDICO, Papel.PORTEIRO)),
    db: Session = Depends(get_db),
) -> OcupacaoSaida:
    espaco = _espaco_do_condominio(db, usuario, espaco_id)
    if not espaco.uso_livre:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este espaço não é de uso livre; ele funciona por reserva.",
        )
    if espaco.capacidade and dados.pessoas > espaco.capacidade:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A contagem passa da capacidade do espaço ({espaco.capacidade}).",
        )

    agora = datetime.now(timezone.utc)
    db.add(
        RegistroOcupacao(
            espaco_id=espaco.id,
            pessoas=dados.pessoas,
            registrado_em=agora,
            registrado_por_id=usuario.id,
        )
    )
    db.commit()

    percentual = round(dados.pessoas / espaco.capacidade * 100) if espaco.capacidade else 0
    return OcupacaoSaida(
        espaco_id=espaco.id,
        espaco_nome=espaco.nome,
        pessoas=dados.pessoas,
        capacidade=espaco.capacidade,
        percentual=min(percentual, 100),
        atualizado_em=agora,
    )


# ── Agenda sigilosa (seção 6) ────────────────────────────────────────
@router.get(
    "/agenda",
    response_model=list[OcupacaoAgenda],
    summary="Agenda dos espaços, sem revelar quem reservou",
)
def consultar_agenda(
    inicio: date = Query(description="Primeiro dia do período."),
    fim: date = Query(description="Último dia do período."),
    espaco_id: int | None = Query(default=None),
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> list[OcupacaoAgenda]:
    """Documentação, seção 6: o morador vê que o espaço "está em ocupação
    nesta data e horário", e a autoria da reserva nunca aparece.
    """
    if fim < inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data final precisa ser igual ou posterior à inicial.",
        )

    consulta = (
        select(Reserva)
        .join(EspacoComum)
        .where(
            EspacoComum.condominio_id == usuario.condominio_id,
            EspacoComum.inativo_em.is_(None),
            Reserva.data >= inicio,
            Reserva.data <= fim,
            Reserva.status.in_(STATUS_QUE_OCUPAM),
        )
        .order_by(Reserva.data, Reserva.hora_inicio)
    )
    if espaco_id is not None:
        consulta = consulta.where(Reserva.espaco_id == espaco_id)

    # Nenhum campo de identificação do morador entra nesta resposta.
    return [
        OcupacaoAgenda(
            espaco_id=r.espaco_id,
            espaco_nome=r.espaco.nome,
            data=r.data,
            hora_inicio=r.hora_inicio,
            hora_fim=r.hora_fim,
            disponivel=False,
        )
        for r in db.scalars(consulta).all()
    ]


# ── Reservas ─────────────────────────────────────────────────────────
@router.post(
    "/reservas",
    response_model=ReservaSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Solicita uma reserva",
)
def solicitar_reserva(
    dados: ReservaEntrada,
    morador: Usuario = Depends(exigir_papel(Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> ReservaSaida:
    espaco = _espaco_do_condominio(db, morador, dados.espaco_id)
    # Trava o espaço até o fim da transação. Sem isso, dois moradores que
    # pedem o mesmo horário ao mesmo tempo passam juntos pela conferência
    # de conflito abaixo, e o espaço fica reservado duas vezes.
    # Relê depois de travar: o síndico pode ter inativado o espaço ou
    # posto em manutenção enquanto este pedido chegava.
    db.refresh(espaco, with_for_update=True)
    if espaco.inativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Espaço não encontrado."
        )

    if not espaco.reservavel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este espaço é de uso livre e não aceita reserva.",
        )
    if espaco.em_manutencao:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Este espaço está em manutenção."
        )
    agora = agora_local()
    if dados.data == agora.date() and dados.hora_inicio <= agora.time():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esse horário de hoje já passou. Escolha um horário mais tarde.",
        )
    if dados.data > agora.date() + timedelta(days=settings.RESERVA_ANTECEDENCIA_MAX_DIAS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "As reservas podem ser feitas com até "
                f"{settings.RESERVA_ANTECEDENCIA_MAX_DIAS} dias de antecedência."
            ),
        )
    if dados.data < agora.date():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Não é possível reservar uma data passada."
        )
    if espaco.capacidade and dados.pessoas_estimadas and dados.pessoas_estimadas > espaco.capacidade:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"O espaço comporta até {espaco.capacidade} pessoas.",
        )

    # "Caso esteja disponível, por ordem de chegada ou antecipação, o espaço
    # será alugado" (seção 6): dois períodos que se sobrepõem não passam.
    conflito = db.scalar(
        select(Reserva).where(
            Reserva.espaco_id == espaco.id,
            Reserva.data == dados.data,
            Reserva.status.in_(STATUS_QUE_OCUPAM),
            Reserva.hora_inicio < dados.hora_fim,
            Reserva.hora_fim > dados.hora_inicio,
        )
    )
    if conflito is not None:
        # A mensagem informa o horário, nunca quem reservou (seção 6).
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"O espaço já está ocupado neste dia das "
                f"{conflito.hora_inicio:%H:%M} às {conflito.hora_fim:%H:%M}."
            ),
        )

    reserva = Reserva(morador_id=morador.id, **dados.model_dump())
    db.add(reserva)
    db.commit()
    db.refresh(reserva)
    return _para_saida(reserva)


@router.get("/reservas/minhas", response_model=list[ReservaSaida], summary="Minhas reservas")
def minhas_reservas(
    morador: Usuario = Depends(exigir_papel(Papel.MORADOR)), db: Session = Depends(get_db)
) -> list[ReservaSaida]:
    reservas = db.scalars(
        select(Reserva)
        .where(Reserva.morador_id == morador.id)
        .order_by(Reserva.data.desc(), Reserva.hora_inicio)
    ).all()
    return [_para_saida(r) for r in reservas]


@router.delete(
    "/reservas/{reserva_id}", response_model=ReservaSaida, summary="Cancela a própria reserva"
)
def cancelar_reserva(
    reserva_id: int,
    morador: Usuario = Depends(exigir_papel(Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> ReservaSaida:
    # Travada até o commit: o síndico pode estar avaliando enquanto o
    # morador cancela, e só um dos dois pode valer.
    reserva = db.get(Reserva, reserva_id, with_for_update=True)
    # Um morador não pode nem ver nem mexer na reserva de outro.
    if reserva is None or reserva.morador_id != morador.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada."
        )
    if reserva.status not in STATUS_QUE_OCUPAM:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Esta reserva não pode mais ser cancelada."
        )

    reserva.status = StatusReserva.CANCELADA
    db.commit()
    db.refresh(reserva)
    return _para_saida(reserva)


# ── Aprovação pelo síndico (seção 13.5.3) ────────────────────────────
@router.get(
    "/reservas",
    response_model=list[ReservaSindicoSaida],
    summary="Reservas do condomínio (síndico)",
)
def listar_reservas_do_condominio(
    status_reserva: StatusReserva | None = Query(default=None, alias="status"),
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> list[ReservaSindicoSaida]:
    consulta = (
        select(Reserva)
        .join(EspacoComum)
        .where(EspacoComum.condominio_id == sindico.condominio_id)
        .order_by(Reserva.data.desc(), Reserva.hora_inicio)
        .options(selectinload(Reserva.morador).selectinload(Usuario.unidade))
    )
    if status_reserva is not None:
        consulta = consulta.where(Reserva.status == status_reserva)

    resposta: list[ReservaSindicoSaida] = []
    for r in db.scalars(consulta).all():
        unidade = r.morador.unidade
        resposta.append(
            ReservaSindicoSaida(
                **_para_saida(r).model_dump(),
                morador_id=r.morador_id,
                morador_nome=r.morador.nome,
                unidade=unidade.identificacao if unidade else None,
            )
        )
    return resposta


@router.post(
    "/reservas/{reserva_id}/avaliacao",
    response_model=ReservaSindicoSaida,
    summary="Aprova ou recusa uma reserva",
)
def avaliar_reserva(
    reserva_id: int,
    dados: AvaliacaoReserva,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> ReservaSindicoSaida:
    # Travada até o commit: o síndico pode estar avaliando enquanto o
    # morador cancela, e só um dos dois pode valer.
    reserva = db.get(Reserva, reserva_id, with_for_update=True)
    if reserva is None or reserva.espaco.condominio_id != sindico.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada."
        )
    if reserva.status != StatusReserva.PENDENTE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta reserva já foi avaliada.",
        )

    reserva.status = StatusReserva.APROVADA if dados.aprovada else StatusReserva.RECUSADA
    reserva.motivo_recusa = None if dados.aprovada else dados.motivo
    reserva.avaliada_por_id = sindico.id
    reserva.avaliada_em = datetime.now(timezone.utc)

    db.commit()
    db.refresh(reserva)

    unidade = db.get(Unidade, reserva.morador.unidade_id) if reserva.morador.unidade_id else None
    return ReservaSindicoSaida(
        **_para_saida(reserva).model_dump(),
        morador_id=reserva.morador_id,
        morador_nome=reserva.morador.nome,
        unidade=unidade.identificacao if unidade else None,
    )

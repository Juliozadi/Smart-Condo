"""Espaços comuns, reservas e ocupação em tempo real.

Documentação, seção 6 (História do Usuário) e seção 13.5.3 (o síndico
aprova ou recusa e vê o histórico).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import exigir_condominio, exigir_papel, get_usuario_atual
from app.core.config import settings
from app.core.database import get_db
from app.core.tempo import agora_local
from app.models.condominio import Unidade
from app.models.enums import Papel, StatusReserva
from app.models.espaco import EspacoComum, RegistroOcupacao, Reserva
from app.models.usuario import Usuario
from app.schemas.condominio import (
    EspacoEntrada, EspacoSaida, OcupacaoEntrada, OcupacaoSaida,
)
from app.schemas.reserva import (
    AvaliacaoReserva, OcupacaoAgenda, ReservaEntrada, ReservaSaida, ReservaSindicoSaida,
)

router = APIRouter(prefix="/espacos", tags=["Espaços e Reservas"])

# Uma reserva só bloqueia o espaço enquanto está de pé.
STATUS_QUE_OCUPAM = (StatusReserva.PENDENTE, StatusReserva.APROVADA)


def _espaco_do_condominio(db: Session, usuario: Usuario, espaco_id: int) -> EspacoComum:
    espaco = db.get(EspacoComum, espaco_id)
    if espaco is None or espaco.condominio_id != usuario.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Espaço não encontrado."
        )
    return espaco


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
    usuario: Usuario = Depends(exigir_condominio), db: Session = Depends(get_db)
) -> list[EspacoComum]:
    return list(
        db.scalars(
            select(EspacoComum)
            .where(EspacoComum.condominio_id == usuario.condominio_id)
            .order_by(EspacoComum.nome)
        ).all()
    )


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
) -> EspacoComum:
    if sindico.condominio_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Cadastre o condomínio primeiro."
        )
    espaco = EspacoComum(condominio_id=sindico.condominio_id, **dados.model_dump())
    db.add(espaco)
    db.commit()
    db.refresh(espaco)
    return espaco


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
    db.execute(select(EspacoComum.id).where(EspacoComum.id == espaco.id).with_for_update())

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
    )
    if status_reserva is not None:
        consulta = consulta.where(Reserva.status == status_reserva)

    resposta: list[ReservaSindicoSaida] = []
    for r in db.scalars(consulta).all():
        unidade = db.get(Unidade, r.morador.unidade_id) if r.morador.unidade_id else None
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

"""Portaria: visitantes, encomendas e ocorrências.

Documentação, seção 6 (História do Usuário):
  - porteiro: "gostaria que o sistema enviasse uma notificação de entrega
    para o cliente que realizou o pedido"
  - porteiro: "que uma notificação seja enviada para o cliente com a foto do
    indivíduo ou gravação em tempo real (vídeo porteiro)... e, assim, o
    cliente confirme se é ou não seu convidado"
  - morador: "o porteiro me envia pelo sistema uma foto ou vídeo para que eu
    confirmasse a minha entrega ou pedido"

O que o porteiro pode fazer aqui depende das permissões que o síndico
definiu (seção 9, caso de uso "Permissão do Porteiro").
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    exigir_condominio, exigir_papel, exigir_permissao_porteiro, get_usuario_atual,
)
from app.core.database import get_db
from app.models.condominio import Unidade
from app.models.enums import (
    CanalVerificacao, Papel, StatusEncomenda, StatusOcorrencia, StatusVisitante,
)
from app.models.portaria import Encomenda, Ocorrencia, Visitante
from app.models.usuario import Usuario
from app.schemas.portaria import (
    ConfirmacaoVisitante, EncomendaEntrada, EncomendaSaida, OcorrenciaEntrada,
    OcorrenciaSaida, RespostaOcorrencia, RetiradaEncomenda, VisitanteEntrada,
    VisitanteSaida,
)
from app.services import notificacao

router = APIRouter(prefix="/portaria", tags=["Portaria"])


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _unidade_do_condominio(db: Session, usuario: Usuario, unidade_id: int) -> Unidade:
    unidade = db.get(Unidade, unidade_id)
    if unidade is None or unidade.condominio_id != usuario.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada."
        )
    return unidade


def _avisar_moradores(db: Session, unidade: Unidade, titulo: str, mensagem: str) -> None:
    """Notifica quem mora na unidade."""
    moradores = db.scalars(
        select(Usuario).where(Usuario.unidade_id == unidade.id, Usuario.papel == Papel.MORADOR)
    ).all()
    for morador in moradores:
        notificacao.notificar(morador.email, CanalVerificacao.EMAIL, titulo, mensagem)


def _visitante_saida(v: Visitante, unidade: Unidade | None = None) -> VisitanteSaida:
    return VisitanteSaida(
        id=v.id, unidade_id=v.unidade_id,
        unidade=(unidade or v.unidade).identificacao,
        nome=v.nome, documento=v.documento, tipo_visita=v.tipo_visita,
        placa_veiculo=v.placa_veiculo, foto_url=v.foto_url, status=v.status,
        entrada_em=v.entrada_em, saida_em=v.saida_em,
        confirmado_em=v.confirmado_em, criado_em=v.criado_em,
    )


def _encomenda_saida(e: Encomenda) -> EncomendaSaida:
    return EncomendaSaida(
        id=e.id, unidade_id=e.unidade_id, unidade=e.unidade.identificacao,
        remetente=e.remetente, tipo_volume=e.tipo_volume,
        codigo_rastreio=e.codigo_rastreio, observacoes=e.observacoes,
        foto_url=e.foto_url, status=e.status, recebida_em=e.recebida_em,
        retirada_em=e.retirada_em, criado_em=e.criado_em,
    )


# ── Visitantes ───────────────────────────────────────────────────────
@router.post(
    "/visitantes",
    response_model=VisitanteSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Registra um visitante e notifica o morador",
)
def registrar_visitante(
    dados: VisitanteEntrada,
    usuario: Usuario = Depends(exigir_permissao_porteiro("registrar_visitantes")),
    db: Session = Depends(get_db),
) -> VisitanteSaida:
    unidade = _unidade_do_condominio(db, usuario, dados.unidade_id)

    visitante = Visitante(
        **dados.model_dump(),
        registrado_por_id=usuario.id,
        status=StatusVisitante.AGUARDANDO_CONFIRMACAO,
    )
    db.add(visitante)
    db.commit()
    db.refresh(visitante)

    # A notificação com a foto é o que permite o morador confirmar (seção 6).
    _avisar_moradores(
        db, unidade,
        "Visitante na portaria",
        f"{visitante.nome} diz ser seu convidado. Confirme ou recuse a entrada.",
    )
    return _visitante_saida(visitante, unidade)


@router.get(
    "/visitantes",
    response_model=list[VisitanteSaida],
    summary="Lista os visitantes",
)
def listar_visitantes(
    status_visitante: StatusVisitante | None = Query(default=None, alias="status"),
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> list[VisitanteSaida]:
    consulta = select(Visitante).join(Unidade).where(
        Unidade.condominio_id == usuario.condominio_id
    )
    # O morador só enxerga os visitantes da própria unidade.
    if usuario.papel == Papel.MORADOR:
        consulta = consulta.where(Visitante.unidade_id == usuario.unidade_id)
    if status_visitante is not None:
        consulta = consulta.where(Visitante.status == status_visitante)

    visitantes = db.scalars(consulta.order_by(Visitante.id.desc())).all()
    return [_visitante_saida(v) for v in visitantes]


@router.post(
    "/visitantes/{visitante_id}/confirmacao",
    response_model=VisitanteSaida,
    summary="O morador confirma ou recusa o visitante",
)
def confirmar_visitante(
    visitante_id: int,
    dados: ConfirmacaoVisitante,
    morador: Usuario = Depends(exigir_papel(Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> VisitanteSaida:
    """"o cliente confirme se é ou não seu convidado" (seção 6)."""
    visitante = db.get(Visitante, visitante_id)
    # Quem responde é o morador da unidade visitada, ninguém mais.
    if visitante is None or visitante.unidade_id != morador.unidade_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visitante não encontrado."
        )
    if visitante.status != StatusVisitante.AGUARDANDO_CONFIRMACAO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este visitante já foi respondido.",
        )

    agora = _agora()
    visitante.confirmado_por_id = morador.id
    visitante.confirmado_em = agora
    if dados.confirmado:
        visitante.status = StatusVisitante.DENTRO
        visitante.entrada_em = agora
    else:
        visitante.status = StatusVisitante.RECUSADO

    db.commit()
    db.refresh(visitante)

    if visitante.registrado_por_id:
        porteiro = db.get(Usuario, visitante.registrado_por_id)
        if porteiro:
            notificacao.notificar(
                porteiro.email, CanalVerificacao.EMAIL,
                "Resposta do morador",
                f"{visitante.nome}: entrada "
                f"{'liberada' if dados.confirmado else 'recusada'}.",
            )
    return _visitante_saida(visitante)


@router.post(
    "/visitantes/{visitante_id}/saida",
    response_model=VisitanteSaida,
    summary="Registra a saída do visitante",
)
def registrar_saida(
    visitante_id: int,
    usuario: Usuario = Depends(exigir_permissao_porteiro("registrar_visitantes")),
    db: Session = Depends(get_db),
) -> VisitanteSaida:
    visitante = db.get(Visitante, visitante_id)
    if visitante is None or visitante.unidade.condominio_id != usuario.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visitante não encontrado."
        )
    if visitante.status != StatusVisitante.DENTRO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este visitante não está registrado como dentro do condomínio.",
        )

    visitante.status = StatusVisitante.SAIU
    visitante.saida_em = _agora()
    db.commit()
    db.refresh(visitante)
    return _visitante_saida(visitante)


# ── Encomendas ───────────────────────────────────────────────────────
@router.post(
    "/encomendas",
    response_model=EncomendaSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Registra uma encomenda e notifica o morador",
)
def registrar_encomenda(
    dados: EncomendaEntrada,
    usuario: Usuario = Depends(exigir_permissao_porteiro("registrar_encomendas")),
    db: Session = Depends(get_db),
) -> EncomendaSaida:
    unidade = _unidade_do_condominio(db, usuario, dados.unidade_id)

    encomenda = Encomenda(
        **dados.model_dump(),
        registrada_por_id=usuario.id,
        recebida_em=_agora(),
        status=StatusEncomenda.AGUARDANDO_RETIRADA,
    )
    db.add(encomenda)
    db.commit()
    db.refresh(encomenda)

    # "notificação de entrega para o cliente que realizou o pedido" (seção 6)
    rastreio = f" (rastreio {encomenda.codigo_rastreio})" if encomenda.codigo_rastreio else ""
    _avisar_moradores(
        db, unidade,
        "Encomenda na portaria",
        f"{encomenda.tipo_volume} de {encomenda.remetente}{rastreio} chegou para você.",
    )
    return _encomenda_saida(encomenda)


@router.get("/encomendas", response_model=list[EncomendaSaida], summary="Lista as encomendas")
def listar_encomendas(
    status_encomenda: StatusEncomenda | None = Query(default=None, alias="status"),
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> list[EncomendaSaida]:
    consulta = select(Encomenda).join(Unidade).where(
        Unidade.condominio_id == usuario.condominio_id
    )
    if usuario.papel == Papel.MORADOR:
        consulta = consulta.where(Encomenda.unidade_id == usuario.unidade_id)
    if status_encomenda is not None:
        consulta = consulta.where(Encomenda.status == status_encomenda)

    return [_encomenda_saida(e) for e in db.scalars(consulta.order_by(Encomenda.id.desc())).all()]


@router.post(
    "/encomendas/{encomenda_id}/retirada",
    response_model=EncomendaSaida,
    summary="O morador confirma a retirada da encomenda",
)
def confirmar_retirada(
    encomenda_id: int,
    dados: RetiradaEncomenda,
    morador: Usuario = Depends(exigir_papel(Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> EncomendaSaida:
    """"o porteiro me envia... uma foto ou vídeo para que eu confirmasse a
    minha entrega ou pedido" (seção 6)."""
    encomenda = db.get(Encomenda, encomenda_id)
    if encomenda is None or encomenda.unidade_id != morador.unidade_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Encomenda não encontrada."
        )
    if encomenda.status != StatusEncomenda.AGUARDANDO_RETIRADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Esta encomenda já foi respondida."
        )

    if dados.confirmada:
        encomenda.status = StatusEncomenda.RETIRADA
        encomenda.retirada_em = _agora()
        encomenda.retirada_por_id = morador.id
    else:
        encomenda.status = StatusEncomenda.RECUSADA

    db.commit()
    db.refresh(encomenda)
    return _encomenda_saida(encomenda)


# ── Ocorrências ──────────────────────────────────────────────────────
@router.post(
    "/ocorrencias",
    response_model=OcorrenciaSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Abre uma ocorrência",
)
def abrir_ocorrencia(
    dados: OcorrenciaEntrada,
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> OcorrenciaSaida:
    if usuario.papel == Papel.PORTEIRO:
        # O porteiro só registra ocorrência se o síndico liberou (seção 9).
        from app.models.usuario import PermissaoPorteiro

        permissoes = db.scalar(
            select(PermissaoPorteiro).where(PermissaoPorteiro.porteiro_id == usuario.id)
        )
        if permissoes is None or not permissoes.registrar_ocorrencias:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="O síndico não liberou esta ação para o seu usuário.",
            )

    ocorrencia = Ocorrencia(
        condominio_id=usuario.condominio_id,
        aberta_por_id=usuario.id,
        unidade_id=usuario.unidade_id,
        **dados.model_dump(),
    )
    db.add(ocorrencia)
    db.commit()
    db.refresh(ocorrencia)
    return _ocorrencia_saida(db, ocorrencia)


def _ocorrencia_saida(db: Session, o: Ocorrencia) -> OcorrenciaSaida:
    unidade = db.get(Unidade, o.unidade_id) if o.unidade_id else None
    return OcorrenciaSaida(
        id=o.id, titulo=o.titulo, descricao=o.descricao, categoria=o.categoria,
        foto_url=o.foto_url, status=o.status, aberta_por_id=o.aberta_por_id,
        aberta_por_nome=o.aberta_por.nome,
        unidade=unidade.identificacao if unidade else None,
        resposta=o.resposta, respondida_em=o.respondida_em, criado_em=o.criado_em,
    )


@router.get("/ocorrencias", response_model=list[OcorrenciaSaida], summary="Lista as ocorrências")
def listar_ocorrencias(
    status_ocorrencia: StatusOcorrencia | None = Query(default=None, alias="status"),
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> list[OcorrenciaSaida]:
    consulta = select(Ocorrencia).where(Ocorrencia.condominio_id == usuario.condominio_id)
    # O morador acompanha só o que ele mesmo abriu.
    if usuario.papel == Papel.MORADOR:
        consulta = consulta.where(Ocorrencia.aberta_por_id == usuario.id)
    if status_ocorrencia is not None:
        consulta = consulta.where(Ocorrencia.status == status_ocorrencia)

    return [
        _ocorrencia_saida(db, o)
        for o in db.scalars(consulta.order_by(Ocorrencia.id.desc())).all()
    ]


@router.post(
    "/ocorrencias/{ocorrencia_id}/resposta",
    response_model=OcorrenciaSaida,
    summary="O síndico responde uma ocorrência",
)
def responder_ocorrencia(
    ocorrencia_id: int,
    dados: RespostaOcorrencia,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> OcorrenciaSaida:
    ocorrencia = db.get(Ocorrencia, ocorrencia_id)
    if ocorrencia is None or ocorrencia.condominio_id != sindico.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ocorrência não encontrada."
        )

    ocorrencia.status = dados.status
    ocorrencia.resposta = dados.resposta
    ocorrencia.respondida_por_id = sindico.id
    ocorrencia.respondida_em = _agora()

    db.commit()
    db.refresh(ocorrencia)
    return _ocorrencia_saida(db, ocorrencia)

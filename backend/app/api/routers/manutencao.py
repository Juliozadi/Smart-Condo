"""Ordens de serviço da manutenção.

Abertura e acompanhamento pelo síndico. O morador não abre ordem de
serviço: ele registra uma ocorrência, e o síndico decide se ela vira uma OS.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import exigir_condominio, exigir_papel
from app.core.database import get_db
from app.models.enums import Papel, PrioridadeOrdemServico, StatusOrdemServico
from app.models.operacao import OrdemServico
from app.models.usuario import Usuario
from app.schemas.comuns import Mensagem
from app.schemas.operacao import (
    OrdemServicoAtualizacao, OrdemServicoEntrada, OrdemServicoSaida, ResumoManutencao,
)

router = APIRouter(prefix="/manutencao", tags=["Manutenção"])

ZERO = Decimal("0.00")
EM_ABERTO = (StatusOrdemServico.ABERTA, StatusOrdemServico.EM_ANDAMENTO)


def _saida(db: Session, os_: OrdemServico) -> OrdemServicoSaida:
    autor = db.get(Usuario, os_.aberta_por_id) if os_.aberta_por_id else None
    return OrdemServicoSaida(
        id=os_.id, tipo=os_.tipo, descricao=os_.descricao, local=os_.local,
        prioridade=os_.prioridade, status=os_.status, fornecedor=os_.fornecedor,
        data_prevista=os_.data_prevista, custo_estimado=os_.custo_estimado,
        custo_real=os_.custo_real, observacoes=os_.observacoes,
        aberta_por_nome=autor.nome if autor else None,
        concluida_em=os_.concluida_em, criado_em=os_.criado_em,
    )


def _buscar(db: Session, usuario: Usuario, ordem_id: int) -> OrdemServico:
    ordem = db.get(OrdemServico, ordem_id)
    if ordem is None or ordem.condominio_id != usuario.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ordem de serviço não encontrada."
        )
    return ordem


@router.post(
    "",
    response_model=OrdemServicoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Abre uma ordem de serviço",
)
def abrir(
    dados: OrdemServicoEntrada,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> OrdemServicoSaida:
    if sindico.condominio_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seu usuário ainda não está vinculado a um condomínio.",
        )

    ordem = OrdemServico(
        condominio_id=sindico.condominio_id,
        aberta_por_id=sindico.id,
        status=StatusOrdemServico.ABERTA,
        **dados.model_dump(),
    )
    db.add(ordem)
    db.commit()
    db.refresh(ordem)
    return _saida(db, ordem)


@router.get("", response_model=list[OrdemServicoSaida], summary="Lista as ordens de serviço")
def listar(
    status_os: StatusOrdemServico | None = Query(default=None, alias="status"),
    prioridade: PrioridadeOrdemServico | None = Query(default=None),
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> list[OrdemServicoSaida]:
    # Moradores e porteiros acompanham o andamento, mas não abrem nem editam.
    consulta = select(OrdemServico).where(
        OrdemServico.condominio_id == usuario.condominio_id
    )
    if status_os is not None:
        consulta = consulta.where(OrdemServico.status == status_os)
    if prioridade is not None:
        consulta = consulta.where(OrdemServico.prioridade == prioridade)

    ordens = db.scalars(consulta.order_by(OrdemServico.id.desc())).all()
    return [_saida(db, o) for o in ordens]


@router.get("/resumo", response_model=ResumoManutencao, summary="Indicadores da manutenção")
def resumo(
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)), db: Session = Depends(get_db)
) -> ResumoManutencao:
    ordens = db.scalars(
        select(OrdemServico).where(OrdemServico.condominio_id == sindico.condominio_id)
    ).all()

    abertas = em_andamento = concluidas = 0
    previsto = realizado = ZERO
    for o in ordens:
        if o.status == StatusOrdemServico.ABERTA:
            abertas += 1
        elif o.status == StatusOrdemServico.EM_ANDAMENTO:
            em_andamento += 1
        elif o.status == StatusOrdemServico.CONCLUIDA:
            concluidas += 1
        # O previsto só conta o que ainda está de pé.
        if o.status in EM_ABERTO and o.custo_estimado:
            previsto += o.custo_estimado
        if o.custo_real:
            realizado += o.custo_real

    return ResumoManutencao(
        abertas=abertas, em_andamento=em_andamento, concluidas=concluidas,
        custo_previsto=previsto, custo_realizado=realizado,
    )


@router.put(
    "/{ordem_id}", response_model=OrdemServicoSaida, summary="Atualiza uma ordem de serviço"
)
def atualizar(
    ordem_id: int,
    dados: OrdemServicoAtualizacao,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> OrdemServicoSaida:
    ordem = _buscar(db, sindico, ordem_id)
    campos = dados.model_dump(exclude_unset=True)

    novo_status = campos.get("status")
    if novo_status == StatusOrdemServico.CONCLUIDA and ordem.concluida_em is None:
        ordem.concluida_em = datetime.now(timezone.utc)
    # Reabrir limpa a data de conclusão, senão ela ficaria mentindo.
    if novo_status in EM_ABERTO:
        ordem.concluida_em = None

    for campo, valor in campos.items():
        setattr(ordem, campo, valor)

    db.commit()
    db.refresh(ordem)
    return _saida(db, ordem)


@router.delete("/{ordem_id}", response_model=Mensagem, summary="Cancela uma ordem de serviço")
def cancelar(
    ordem_id: int,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> Mensagem:
    ordem = _buscar(db, sindico, ordem_id)
    if ordem.status == StatusOrdemServico.CONCLUIDA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Uma ordem concluída não pode ser cancelada.",
        )
    # Cancela em vez de apagar: o histórico de manutenção fica íntegro.
    ordem.status = StatusOrdemServico.CANCELADA
    db.commit()
    return Mensagem(detalhe="Ordem de serviço cancelada.")

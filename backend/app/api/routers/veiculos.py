"""Controle de veículos no estacionamento.

Documentação, seção 8: o porteiro registra entradas e saídas. O que ele
pode fazer aqui depende da permissão que o síndico definiu (seção 12).
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import (
    exigir_condominio, exigir_permissao_do_porteiro, exigir_permissao_porteiro,
)
from app.core.database import get_db
from app.models.condominio import Unidade
from app.models.enums import CategoriaVeiculo, Papel, TipoMovimentacao
from app.models.operacao import MovimentacaoVeiculo
from app.models.usuario import Usuario
from app.schemas.operacao import (
    MovimentacaoEntrada, MovimentacaoSaida, OcupacaoEstacionamento, VeiculoNoPatio,
)

router = APIRouter(prefix="/veiculos", tags=["Veículos"])


def _saida(m: MovimentacaoVeiculo) -> MovimentacaoSaida:
    return MovimentacaoSaida(
        id=m.id, placa=m.placa, tipo=m.tipo, categoria=m.categoria,
        unidade_id=m.unidade_id,
        unidade=m.unidade.identificacao if m.unidade else None,
        modelo=m.modelo, cor=m.cor, observacao=m.observacao,
        registrada_em=m.registrada_em,
    )


def _ultima_por_placa(condominio_id: int):
    """Subconsulta com a movimentação mais recente de cada placa."""
    return (
        select(
            MovimentacaoVeiculo.placa.label("placa"),
            func.max(MovimentacaoVeiculo.id).label("ultimo_id"),
        )
        .where(MovimentacaoVeiculo.condominio_id == condominio_id)
        .group_by(MovimentacaoVeiculo.placa)
        .subquery()
    )


@router.post(
    "",
    response_model=MovimentacaoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Registra a entrada ou a saída de um veículo",
)
def registrar_movimentacao(
    dados: MovimentacaoEntrada,
    usuario: Usuario = Depends(exigir_permissao_porteiro("registrar_veiculos")),
    db: Session = Depends(get_db),
) -> MovimentacaoSaida:
    unidade = None
    if dados.unidade_id is not None:
        unidade = db.get(Unidade, dados.unidade_id)
        if unidade is None or unidade.condominio_id != usuario.condominio_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada."
            )
    if dados.categoria == CategoriaVeiculo.MORADOR and unidade is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe a unidade do morador.",
        )

    # Duas entradas seguidas (ou duas saídas) deixariam o pátio errado.
    ultima = db.scalar(
        select(MovimentacaoVeiculo)
        .where(
            MovimentacaoVeiculo.condominio_id == usuario.condominio_id,
            MovimentacaoVeiculo.placa == dados.placa,
        )
        .order_by(MovimentacaoVeiculo.id.desc())
        .limit(1)
    )
    if ultima is not None and ultima.tipo == dados.tipo:
        ja = "entrada" if dados.tipo == TipoMovimentacao.ENTRADA else "saída"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A última movimentação desta placa já foi uma {ja}.",
        )
    if ultima is None and dados.tipo == TipoMovimentacao.SAIDA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este veículo não tem entrada registrada.",
        )

    movimentacao = MovimentacaoVeiculo(
        condominio_id=usuario.condominio_id,
        placa=dados.placa,
        modelo=dados.modelo,
        cor=dados.cor,
        tipo=dados.tipo,
        categoria=dados.categoria,
        unidade_id=dados.unidade_id,
        observacao=dados.observacao,
        registrada_por_id=usuario.id,
        registrada_em=datetime.now(timezone.utc),
    )
    db.add(movimentacao)
    db.commit()
    db.refresh(movimentacao)
    return _saida(movimentacao)


@router.get("/patio", response_model=list[VeiculoNoPatio], summary="Veículos no pátio agora")
def listar_no_patio(
    usuario: Usuario = Depends(exigir_permissao_porteiro("registrar_veiculos")),
    db: Session = Depends(get_db),
) -> list[VeiculoNoPatio]:
    """Quem está dentro sai da última movimentação de cada placa.

    Traz placa e unidade de todos os carros: é da portaria e do síndico. O
    morador vê só a ocupação, em números (GET /veiculos/ocupacao)."""
    ultimas = _ultima_por_placa(usuario.condominio_id)
    dentro = db.scalars(
        select(MovimentacaoVeiculo)
        .join(ultimas, MovimentacaoVeiculo.id == ultimas.c.ultimo_id)
        .where(MovimentacaoVeiculo.tipo == TipoMovimentacao.ENTRADA)
        .order_by(MovimentacaoVeiculo.registrada_em.desc())
    ).all()

    return [
        VeiculoNoPatio(
            placa=m.placa, categoria=m.categoria,
            unidade=m.unidade.identificacao if m.unidade else None,
            modelo=m.modelo, cor=m.cor, desde=m.registrada_em,
        )
        for m in dentro
    ]


@router.get(
    "/ocupacao",
    response_model=OcupacaoEstacionamento,
    summary="Ocupação do estacionamento",
)
def ocupacao(
    usuario: Usuario = Depends(exigir_condominio), db: Session = Depends(get_db)
) -> OcupacaoEstacionamento:
    """As vagas totais vêm da soma das vagas das unidades."""
    vagas = db.scalar(
        select(func.coalesce(func.sum(Unidade.vagas_garagem), 0)).where(
            Unidade.condominio_id == usuario.condominio_id
        )
    ) or 0

    ultimas = _ultima_por_placa(usuario.condominio_id)
    ocupadas = db.scalar(
        select(func.count())
        .select_from(MovimentacaoVeiculo)
        .join(ultimas, MovimentacaoVeiculo.id == ultimas.c.ultimo_id)
        .where(MovimentacaoVeiculo.tipo == TipoMovimentacao.ENTRADA)
    ) or 0

    percentual = round(ocupadas / vagas * 100) if vagas else 0
    return OcupacaoEstacionamento(
        vagas_totais=vagas,
        ocupadas=ocupadas,
        # Mais carros que vagas é possível (visitantes); não devolve negativo.
        livres=max(vagas - ocupadas, 0),
        percentual=min(percentual, 100),
    )


@router.get(
    "",
    response_model=list[MovimentacaoSaida],
    summary="Histórico de movimentações",
)
def listar_movimentacoes(
    placa: str | None = Query(default=None, description="Filtra por placa."),
    limite: int = Query(default=50, ge=1, le=200),
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> list[MovimentacaoSaida]:
    exigir_permissao_do_porteiro(db, usuario, "registrar_veiculos")
    consulta = select(MovimentacaoVeiculo).where(
        MovimentacaoVeiculo.condominio_id == usuario.condominio_id
    )
    # O morador acompanha apenas os veículos da própria unidade.
    if usuario.papel == Papel.MORADOR:
        consulta = consulta.where(MovimentacaoVeiculo.unidade_id == usuario.unidade_id)
    if placa:
        limpa = "".join(c for c in placa if c.isalnum()).upper()
        consulta = consulta.where(MovimentacaoVeiculo.placa == limpa)

    movimentacoes = db.scalars(
        consulta.order_by(MovimentacaoVeiculo.id.desc()).limit(limite)
    ).all()
    return [_saida(m) for m in movimentacoes]

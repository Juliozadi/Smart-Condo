"""Consulta do condomínio pelo síndico e pelos moradores.

Quem cadastra, edita e exclui condomínios é o administrador da plataforma
(app/api/routers/admin.py). Aqui ficam a consulta do próprio condomínio, o
cadastro de unidades pelo síndico e a conferência do código de acesso, que
é aberta porque a tela de cadastro do morador precisa dela antes do login.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import exigir_papel, get_usuario_atual
from app.core.database import get_db
from app.core.security import gerar_codigo_condominio
from app.models.condominio import Condominio, Unidade
from app.models.enums import Papel
from app.models.usuario import Usuario
from app.schemas.condominio import (
    CondominioPorCodigo, CondominioSaida, UnidadeEntrada, UnidadeSaida,
)

router = APIRouter(prefix="/condominios", tags=["Condomínio"])


@router.get(
    "/por-codigo/{codigo}",
    response_model=CondominioPorCodigo,
    summary="Confere um código de acesso (aberto, para a tela de cadastro)",
)
def buscar_por_codigo(codigo: str, db: Session = Depends(get_db)) -> Condominio:
    """Rota aberta: o morador precisa confirmar o condomínio antes de ter
    conta. Devolve só nome e cidade, para ele ver que digitou o código
    certo — e exige o código, em vez de listar todos os condomínios."""
    condominio = db.scalar(
        select(Condominio).where(Condominio.codigo_acesso == codigo.strip().upper())
    )
    if condominio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código de acesso não encontrado. Confira com o síndico.",
        )
    return condominio


@router.get("/meu", response_model=CondominioSaida, summary="Condomínio do usuário logado")
def meu_condominio(
    usuario: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)
) -> Condominio:
    if usuario.condominio_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Você ainda não está vinculado a um condomínio.",
        )
    condominio = db.get(Condominio, usuario.condominio_id)
    if condominio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Condomínio não encontrado."
        )
    return condominio


# ── Unidades ─────────────────────────────────────────────────────────
@router.get("/meu/unidades", response_model=list[UnidadeSaida], summary="Unidades do condomínio")
def listar_unidades(
    usuario: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)
) -> list[Unidade]:
    if usuario.condominio_id is None:
        return []
    return list(
        db.scalars(
            select(Unidade)
            .where(Unidade.condominio_id == usuario.condominio_id)
            .order_by(Unidade.bloco, Unidade.numero)
        ).all()
    )


@router.post(
    "/meu/unidades",
    response_model=UnidadeSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra uma unidade",
)
def cadastrar_unidade(
    dados: UnidadeEntrada,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> Unidade:
    if sindico.condominio_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Cadastre o condomínio primeiro."
        )

    ja_existe = db.scalar(
        select(Unidade).where(
            Unidade.condominio_id == sindico.condominio_id,
            Unidade.numero == dados.numero,
            Unidade.bloco == dados.bloco,
        )
    )
    if ja_existe is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Esta unidade já está cadastrada."
        )

    unidade = Unidade(condominio_id=sindico.condominio_id, **dados.model_dump())
    db.add(unidade)
    db.commit()
    db.refresh(unidade)
    return unidade


@router.post(
    "/meu/codigo-acesso",
    response_model=CondominioSaida,
    summary="Gera um novo código de acesso",
)
def renovar_codigo_acesso(
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> Condominio:
    """Útil quando o código circula fora de quem deveria ter recebido: o
    antigo deixa de valer para novos cadastros na hora."""
    if sindico.condominio_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Você não administra um condomínio."
        )
    condominio = db.get(Condominio, sindico.condominio_id)

    for _ in range(10):
        codigo = gerar_codigo_condominio(condominio.nome)
        if not db.scalar(select(Condominio).where(Condominio.codigo_acesso == codigo)):
            break
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível gerar o código de acesso. Tente de novo.",
        )

    condominio.codigo_acesso = codigo
    db.commit()
    db.refresh(condominio)
    return condominio

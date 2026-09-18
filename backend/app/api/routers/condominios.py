"""Cadastro e consulta do condomínio.

Documentação, seção 9 — caso de uso "Cadastro do condomínio":
usuário principal síndico, pré-requisito "existir um síndico ativo".
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import exigir_papel, get_usuario_atual
from app.core.database import get_db
from app.models.condominio import Condominio, Unidade
from app.models.enums import Papel
from app.models.usuario import Usuario
from app.schemas.condominio import (
    CondominioEntrada, CondominioPublico, CondominioSaida, UnidadeEntrada, UnidadeSaida,
)

router = APIRouter(prefix="/condominios", tags=["Condomínio"])


@router.get(
    "",
    response_model=list[CondominioPublico],
    summary="Lista os condomínios (aberto, para a tela de cadastro do morador)",
)
def listar_condominios(db: Session = Depends(get_db)) -> list[Condominio]:
    # Rota aberta de propósito: o morador precisa escolher o condomínio
    # antes de existir conta. Só devolve nome e cidade, nada sensível.
    return list(db.scalars(select(Condominio).order_by(Condominio.nome)).all())


@router.post(
    "",
    response_model=CondominioSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra o condomínio",
)
def cadastrar_condominio(
    dados: CondominioEntrada,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> Condominio:
    if sindico.condominio_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Você já administra um condomínio.",
        )
    if db.scalar(select(Condominio).where(Condominio.cnpj == dados.cnpj)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um condomínio com este CNPJ.",
        )

    condominio = Condominio(**dados.model_dump(), sindico_id=sindico.id)
    db.add(condominio)
    db.flush()

    sindico.condominio_id = condominio.id
    db.commit()
    db.refresh(condominio)
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


@router.put("/meu", response_model=CondominioSaida, summary="Atualiza os dados do condomínio")
def atualizar_condominio(
    dados: CondominioEntrada,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> Condominio:
    if sindico.condominio_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Você não administra um condomínio."
        )
    condominio = db.get(Condominio, sindico.condominio_id)

    outro = db.scalar(
        select(Condominio).where(Condominio.cnpj == dados.cnpj, Condominio.id != condominio.id)
    )
    if outro is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe outro condomínio com este CNPJ.",
        )

    for campo, valor in dados.model_dump().items():
        setattr(condominio, campo, valor)

    db.commit()
    db.refresh(condominio)
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

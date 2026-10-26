"""Livro da portaria: a passagem de turno.

O porteiro que sai anota o que o próximo precisa saber; o síndico lê
tudo e também orienta por aqui. A anotação importante pede ciência de
quem chega, e mostra quem já leu. Nada se apaga nem se edita. O morador
não lê: o livro é da equipe.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import exists, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, selectinload

from app.api.deps import exigir_papel
from app.core.database import get_db
from app.models.enums import Papel
from app.models.livro import AnotacaoPortaria, CienciaAnotacao
from app.models.usuario import Usuario
from app.schemas.livro import AnotacaoEntrada, AnotacaoSaida, Ciencia, Pendentes

router = APIRouter(prefix="/livro-portaria", tags=["Livro da portaria"])

equipe = exigir_papel(Papel.PORTEIRO, Papel.SINDICO)

# Passou disso, já não é passagem de turno: não aparece como pendente.
JANELA_PENDENTES = timedelta(days=7)


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _pendente_para(usuario: Usuario):
    """Condição SQL: importante, de outra pessoa, recente e sem a minha
    ciência."""
    return (
        AnotacaoPortaria.importante.is_(True)
        & ((AnotacaoPortaria.autor_id.is_(None)) | (AnotacaoPortaria.autor_id != usuario.id))
        & (AnotacaoPortaria.criado_em >= _agora() - JANELA_PENDENTES)
        & ~exists().where(CienciaAnotacao.anotacao_id == AnotacaoPortaria.id,
                          CienciaAnotacao.usuario_id == usuario.id)
    )


def _saida(a: AnotacaoPortaria, usuario: Usuario) -> AnotacaoSaida:
    leu = any(c.usuario_id == usuario.id for c in a.ciencias)
    return AnotacaoSaida(
        id=a.id, autor_nome=a.autor.nome if a.autor else None,
        autor_papel=a.autor.papel if a.autor else None, texto=a.texto,
        importante=a.importante, criado_em=a.criado_em,
        cientes=[Ciencia(nome=c.usuario.nome, em=c.ciente_em) for c in a.ciencias],
        preciso_ler=(a.importante and a.autor_id != usuario.id and not leu
                     and a.criado_em >= _agora() - JANELA_PENDENTES),
    )


def _consulta(condominio_id: int):
    return (
        select(AnotacaoPortaria)
        .options(selectinload(AnotacaoPortaria.autor),
                 selectinload(AnotacaoPortaria.ciencias).selectinload(CienciaAnotacao.usuario))
        .where(AnotacaoPortaria.condominio_id == condominio_id)
    )


@router.post("", response_model=AnotacaoSaida, status_code=status.HTTP_201_CREATED,
             summary="Anota no livro da portaria")
def anotar(
    dados: AnotacaoEntrada,
    usuario: Usuario = Depends(equipe),
    db: Session = Depends(get_db),
) -> AnotacaoSaida:
    a = AnotacaoPortaria(condominio_id=usuario.condominio_id, autor_id=usuario.id,
                         texto=dados.texto, importante=dados.importante)
    db.add(a)
    db.commit()
    a = db.scalar(_consulta(usuario.condominio_id).where(AnotacaoPortaria.id == a.id))
    return _saida(a, usuario)


@router.get("", response_model=list[AnotacaoSaida], summary="O livro, das mais recentes")
def listar(
    limite: int = Query(default=100, ge=1, le=300),
    usuario: Usuario = Depends(equipe),
    db: Session = Depends(get_db),
) -> list[AnotacaoSaida]:
    lista = db.scalars(_consulta(usuario.condominio_id)
                       .order_by(AnotacaoPortaria.criado_em.desc(), AnotacaoPortaria.id.desc())
                       .limit(limite)).all()
    return [_saida(a, usuario) for a in lista]


@router.get("/pendentes", response_model=Pendentes,
            summary="Quantas anotações importantes esperam a minha ciência")
def pendentes(usuario: Usuario = Depends(equipe), db: Session = Depends(get_db)) -> Pendentes:
    total = db.scalar(select(func.count()).select_from(AnotacaoPortaria).where(
        AnotacaoPortaria.condominio_id == usuario.condominio_id, _pendente_para(usuario)))
    return Pendentes(total=total or 0)


@router.post("/{anotacao_id}/ciencia", response_model=AnotacaoSaida, summary="Dá ciência")
def dar_ciencia(
    anotacao_id: int,
    usuario: Usuario = Depends(equipe),
    db: Session = Depends(get_db),
) -> AnotacaoSaida:
    a = db.get(AnotacaoPortaria, anotacao_id)
    if a is None or a.condominio_id != usuario.condominio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Anotação não encontrada.")
    # Quem escreveu já sabe: a ciência é de quem chega. Duas ciências ao
    # mesmo tempo (dois cliques) não duplicam: a restrição única decide, e
    # a segunda simplesmente não grava.
    if a.autor_id != usuario.id:
        db.execute(insert(CienciaAnotacao).values(anotacao_id=a.id, usuario_id=usuario.id)
                   .on_conflict_do_nothing(constraint="uq_ciencia_anotacao"))
        db.commit()
    a = db.scalar(_consulta(usuario.condominio_id).where(AnotacaoPortaria.id == a.id)
                  .execution_options(populate_existing=True))
    return _saida(a, usuario)

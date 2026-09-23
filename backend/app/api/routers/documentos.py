"""Documentos do condomínio.

Documentação, seção 13.6: o morador acessa atas, convenção e regimento
interno. Quem publica é o síndico.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import exigir_condominio, exigir_papel
from app.core.database import get_db
from app.models.condominio import Unidade
from app.models.enums import CategoriaDocumento, Papel
from app.models.operacao import Documento
from app.models.usuario import Usuario
from app.schemas.comuns import Mensagem
from app.schemas.operacao import DocumentoEntrada, DocumentoSaida

router = APIRouter(prefix="/documentos", tags=["Documentos"])


def _saida(db: Session, d: Documento) -> DocumentoSaida:
    unidade = db.get(Unidade, d.unidade_id) if d.unidade_id else None
    autor = db.get(Usuario, d.publicado_por_id) if d.publicado_por_id else None
    return DocumentoSaida(
        id=d.id, titulo=d.titulo, descricao=d.descricao, categoria=d.categoria,
        arquivo_url=d.arquivo_url, tamanho_kb=d.tamanho_kb,
        unidade=unidade.identificacao if unidade else None,
        publicado_por_nome=autor.nome if autor else None,
        publicado_em=d.publicado_em,
    )


@router.post(
    "",
    response_model=DocumentoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Publica um documento",
)
def publicar(
    dados: DocumentoEntrada,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> DocumentoSaida:
    if sindico.condominio_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seu usuário ainda não está vinculado a um condomínio.",
        )
    if dados.unidade_id is not None:
        unidade = db.get(Unidade, dados.unidade_id)
        if unidade is None or unidade.condominio_id != sindico.condominio_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada."
            )

    documento = Documento(
        condominio_id=sindico.condominio_id,
        publicado_por_id=sindico.id,
        publicado_em=datetime.now(timezone.utc),
        **dados.model_dump(),
    )
    db.add(documento)
    db.commit()
    db.refresh(documento)
    return _saida(db, documento)


@router.get("", response_model=list[DocumentoSaida], summary="Lista os documentos")
def listar(
    categoria: CategoriaDocumento | None = Query(default=None),
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> list[DocumentoSaida]:
    consulta = select(Documento).where(Documento.condominio_id == usuario.condominio_id)

    # Documento de uma unidade (a planta, por exemplo) só aparece para quem
    # mora nela. Os demais valem para todo o condomínio.
    if usuario.papel == Papel.MORADOR:
        consulta = consulta.where(
            or_(Documento.unidade_id.is_(None), Documento.unidade_id == usuario.unidade_id)
        )
    if categoria is not None:
        consulta = consulta.where(Documento.categoria == categoria)

    documentos = db.scalars(
        consulta.order_by(Documento.categoria, Documento.publicado_em.desc())
    ).all()
    return [_saida(db, d) for d in documentos]


@router.delete("/{documento_id}", response_model=Mensagem, summary="Remove um documento")
def remover(
    documento_id: int,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> Mensagem:
    documento = db.get(Documento, documento_id)
    if documento is None or documento.condominio_id != sindico.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado."
        )
    db.delete(documento)
    db.commit()
    return Mensagem(detalhe="Documento removido.")

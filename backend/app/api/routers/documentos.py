"""Documentos do condomínio.

Documentação, seção 13.6: o morador acessa atas, convenção e regimento
interno. Quem publica é o síndico, enviando o arquivo (PDF ou imagem).

O arquivo não tem endereço público: sai por GET /documentos/{id}/arquivo,
que confere o token. Documento de uma unidade (a planta, por exemplo) só
vai para o morador dela e para o síndico; os demais, para o condomínio.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import exigir_condominio, exigir_papel
from app.core.config import settings
from app.core.database import get_db
from app.models.condominio import Unidade
from app.models.enums import CategoriaDocumento, Papel
from app.models.operacao import Documento
from app.models.usuario import Usuario
from app.schemas.comuns import Mensagem
from app.schemas.operacao import DocumentoSaida
from app.services import arquivos, registro

router = APIRouter(prefix="/documentos", tags=["Documentos"])


def _saida(db: Session, d: Documento) -> DocumentoSaida:
    unidade = db.get(Unidade, d.unidade_id) if d.unidade_id else None
    autor = db.get(Usuario, d.publicado_por_id) if d.publicado_por_id else None
    return DocumentoSaida(
        id=d.id, titulo=d.titulo, descricao=d.descricao, categoria=d.categoria,
        url=f"/documentos/{d.id}/arquivo" if d.arquivo else None,
        tipo_conteudo=d.tipo_conteudo, tamanho_kb=d.tamanho_kb,
        unidade=unidade.identificacao if unidade else None,
        publicado_por_nome=autor.nome if autor else None,
        publicado_em=d.publicado_em,
    )


def _visiveis(usuario: Usuario):
    """Os documentos que o usuário pode ver: o síndico vê todos; os demais,
    os do condomínio inteiro e — o morador — os da própria unidade."""
    consulta = select(Documento).where(
        Documento.condominio_id == usuario.condominio_id, Documento.inativo_em.is_(None)
    )
    if usuario.papel == Papel.MORADOR:
        consulta = consulta.where(
            or_(Documento.unidade_id.is_(None), Documento.unidade_id == usuario.unidade_id)
        )
    elif usuario.papel != Papel.SINDICO:
        consulta = consulta.where(Documento.unidade_id.is_(None))
    return consulta


@router.post(
    "",
    response_model=DocumentoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Publica um documento",
)
def publicar(
    titulo: str = Form(min_length=3, max_length=180),
    categoria: CategoriaDocumento = Form(CategoriaDocumento.OUTRO),
    descricao: str | None = Form(default=None, max_length=1000),
    # Preenchido só quando o documento é de uma unidade (planta, por exemplo).
    unidade_id: int | None = Form(default=None),
    arquivo: UploadFile = File(..., description="PDF ou imagem JPG, PNG ou WebP"),
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> DocumentoSaida:
    if sindico.condominio_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seu usuário ainda não está vinculado a um condomínio.",
        )
    # Formulário com arquivo não passa pelo SchemaBase: apara aqui, antes
    # de conferir o tamanho — senão "   " passava pelo mínimo de 3.
    titulo = titulo.strip()
    descricao = (descricao or "").strip() or None
    if len(titulo) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Escreva um título com pelo menos 3 caracteres.",
        )
    if unidade_id is not None:
        unidade = db.get(Unidade, unidade_id)
        if unidade is None or unidade.condominio_id != sindico.condominio_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada."
            )

    conteudo = arquivo.file.read(settings.DOCUMENTO_MAX_KB * 1024 + 1)
    try:
        nome = arquivos.salvar_privado(
            arquivos.CONDOMINIO, conteudo, aceita_pdf=True, max_kb=settings.DOCUMENTO_MAX_KB
        )
    except arquivos.ArquivoRecusado as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro

    documento = Documento(
        condominio_id=sindico.condominio_id,
        publicado_por_id=sindico.id,
        publicado_em=datetime.now(timezone.utc),
        titulo=titulo,
        descricao=descricao,
        categoria=categoria,
        unidade_id=unidade_id,
        arquivo=nome,
        tipo_conteudo=arquivos.tipo_de_conteudo(nome),
        tamanho_kb=max(1, round(len(conteudo) / 1024)),
    )
    db.add(documento)
    try:
        db.flush()
        registro.registrar(db, sindico, registro.CRIOU, registro.DOCUMENTO, documento.id)
        db.commit()
    except Exception:
        db.rollback()
        arquivos.apagar_privado(arquivos.CONDOMINIO, nome)
        raise
    db.refresh(documento)
    return _saida(db, documento)


@router.get("", response_model=list[DocumentoSaida], summary="Lista os documentos")
def listar(
    categoria: CategoriaDocumento | None = Query(default=None),
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> list[DocumentoSaida]:
    consulta = _visiveis(usuario)
    if categoria is not None:
        consulta = consulta.where(Documento.categoria == categoria)
    documentos = db.scalars(
        consulta.order_by(Documento.categoria, Documento.publicado_em.desc())
    ).all()
    return [_saida(db, d) for d in documentos]


@router.get("/{documento_id}/arquivo", summary="Abre o arquivo de um documento")
def abrir(
    documento_id: int,
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> FileResponse:
    documento = db.scalar(_visiveis(usuario).where(Documento.id == documento_id))
    caminho = (
        arquivos.caminho_privado(arquivos.CONDOMINIO, documento.arquivo) if documento else None
    )
    if caminho is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado."
        )
    return FileResponse(
        caminho,
        media_type=documento.tipo_conteudo or arquivos.tipo_de_conteudo(caminho.name),
        headers={"Cache-Control": "private, no-store", "Content-Disposition": "inline"},
    )


@router.delete("/{documento_id}", response_model=Mensagem, summary="Remove (inativa) um documento")
def remover(
    documento_id: int,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> Mensagem:
    documento = db.get(Documento, documento_id, with_for_update=True)
    if (documento is None or documento.condominio_id != sindico.condominio_id
            or documento.inativo_em is not None):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado."
        )
    # Nada é apagado — nem o arquivo: o documento sai das telas e da rota
    # do arquivo, mas fica guardado com quem o removeu e quando.
    documento.inativo_em = datetime.now(timezone.utc)
    documento.inativado_por_id = sindico.id
    registro.registrar(db, sindico, registro.INATIVOU, registro.DOCUMENTO, documento.id)
    db.commit()
    return Mensagem(detalhe="Documento removido.")

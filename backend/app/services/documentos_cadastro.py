"""Documentos do cadastro do morador: gravar, listar e descartar."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.documento_cadastro import DocumentoCadastro
from app.models.enums import TipoDocumentoCadastro
from app.models.usuario import Usuario
from app.schemas.documento_cadastro import DocumentoCadastroSaida
from app.services import arquivos


def saida(documento: DocumentoCadastro) -> DocumentoCadastroSaida:
    return DocumentoCadastroSaida(
        id=documento.id, tipo=documento.tipo, tipo_conteudo=documento.tipo_conteudo,
        tamanho_bytes=documento.tamanho_bytes, enviado_em=documento.enviado_em,
        # Só o síndico do condomínio abre este endereço.
        url=f"/usuarios/{documento.usuario_id}/documentos/{documento.id}/arquivo",
    )


def listar(db: Session, usuario_id: int) -> list[DocumentoCadastro]:
    return list(db.scalars(
        select(DocumentoCadastro)
        .where(DocumentoCadastro.usuario_id == usuario_id)
        .order_by(DocumentoCadastro.tipo)
    ))


def salvar(
    db: Session, usuario: Usuario, tipo: TipoDocumentoCadastro, conteudo: bytes
) -> DocumentoCadastro:
    """Grava o arquivo; se já havia um do mesmo tipo, ele é substituído.

    Levanta arquivos.ArquivoRecusado se o conteúdo não for PDF ou imagem.
    """
    nome = arquivos.salvar_privado(
        arquivos.DOCUMENTOS, conteudo, aceita_pdf=True, max_kb=settings.DOCUMENTO_MAX_KB
    )
    documento = db.scalar(
        select(DocumentoCadastro).where(
            DocumentoCadastro.usuario_id == usuario.id, DocumentoCadastro.tipo == tipo
        )
    )
    anterior = documento.arquivo if documento else None
    if documento is None:
        documento = DocumentoCadastro(usuario_id=usuario.id, tipo=tipo)
        db.add(documento)
    documento.arquivo = nome
    documento.tipo_conteudo = arquivos.tipo_de_conteudo(nome)
    documento.tamanho_bytes = len(conteudo)
    try:
        db.commit()
    except Exception:
        # Sem registro no banco, o arquivo novo não serviria para nada.
        db.rollback()
        arquivos.apagar_privado(arquivos.DOCUMENTOS, nome)
        raise
    arquivos.apagar_privado(arquivos.DOCUMENTOS, anterior)
    db.refresh(documento)
    return documento


def descartar_todos(db: Session, usuario_id: int) -> None:
    """Apaga os documentos de um cadastro recusado ou de um usuário inativado.

    Nos dois casos acabou a finalidade que justificava guardar RG e
    comprovante de residência (LGPD, art. 6º, III, e art. 16).
    """
    documentos = listar(db, usuario_id)
    nomes = [d.arquivo for d in documentos]
    for documento in documentos:
        db.delete(documento)
    db.commit()
    # O arquivo só sai do disco depois que o registro saiu do banco.
    for nome in nomes:
        arquivos.apagar_privado(arquivos.DOCUMENTOS, nome)

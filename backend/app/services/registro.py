"""Registro de alterações: quem criou, editou, inativou ou reativou.

Toda ação de administrador (e as do síndico sobre cadastros, comunicados e
documentos) chama registrar() na mesma transação da alteração: se a
alteração não for gravada, o registro também não é.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.registro import RegistroAlteracao
from app.models.usuario import Usuario

# Ações
CRIOU = "criou"
EDITOU = "editou"
INATIVOU = "inativou"
REATIVOU = "reativou"
NOVO_CODIGO = "novo_codigo"
APROVOU = "aprovou"
RECUSOU = "recusou"

# Entidades
CONDOMINIO = "condominio"
USUARIO = "usuario"
COMUNICADO = "comunicado"
DOCUMENTO = "documento"

ROTULO_ACAO = {
    CRIOU: "Criado", EDITOU: "Editado", INATIVOU: "Inativado", REATIVOU: "Reativado",
    NOVO_CODIGO: "Novo código de acesso", APROVOU: "Aprovado", RECUSOU: "Recusado",
}


def registrar(db: Session, autor: Usuario | None, acao: str, entidade: str,
              entidade_id: int, descricao: str | None = None) -> None:
    db.add(RegistroAlteracao(
        autor_id=autor.id if autor else None, acao=acao, entidade=entidade,
        entidade_id=entidade_id, descricao=descricao,
    ))


def campos_alterados(objeto, novos: dict, rotulos: dict[str, str]) -> str | None:
    """"Alterou nome e telefone" — só os campos que de fato mudaram. A
    senha entra pelo nome, nunca pelo valor."""
    mudaram = [rotulos.get(campo, campo) for campo, valor in novos.items()
               if campo in rotulos and getattr(objeto, campo, None) != valor]
    if not mudaram:
        return None
    if len(mudaram) == 1:
        return f"Alterou {mudaram[0]}"
    return "Alterou " + ", ".join(mudaram[:-1]) + " e " + mudaram[-1]


def _saida(registro: RegistroAlteracao, autor_nome: str | None) -> dict:
    return {
        "acao": registro.acao,
        "rotulo": ROTULO_ACAO.get(registro.acao, registro.acao),
        "autor_nome": autor_nome,
        "feito_em": registro.feito_em,
        "descricao": registro.descricao,
    }


def _consulta(entidade: str):
    return (
        select(RegistroAlteracao, Usuario.nome)
        .outerjoin(Usuario, Usuario.id == RegistroAlteracao.autor_id)
        .where(RegistroAlteracao.entidade == entidade)
    )


def ultimas(db: Session, entidade: str, ids) -> dict[int, dict]:
    """A alteração mais recente de cada registro, numa consulta só."""
    ids = list(ids)
    if not ids:
        return {}
    linhas = db.execute(
        _consulta(entidade)
        .where(RegistroAlteracao.entidade_id.in_(ids))
        .distinct(RegistroAlteracao.entidade_id)
        .order_by(RegistroAlteracao.entidade_id, RegistroAlteracao.feito_em.desc(),
                  RegistroAlteracao.id.desc())
    ).all()
    return {r.entidade_id: _saida(r, nome) for r, nome in linhas}


def criadores(db: Session, entidade: str, ids) -> dict[int, str | None]:
    """Quem criou cada registro, numa consulta só."""
    ids = list(ids)
    if not ids:
        return {}
    linhas = db.execute(
        _consulta(entidade)
        .where(RegistroAlteracao.entidade_id.in_(ids), RegistroAlteracao.acao == CRIOU)
        .distinct(RegistroAlteracao.entidade_id)
        .order_by(RegistroAlteracao.entidade_id, RegistroAlteracao.feito_em,
                  RegistroAlteracao.id)
    ).all()
    return {r.entidade_id: nome for r, nome in linhas}


def historico(db: Session, entidade: str, entidade_id: int) -> list[dict]:
    """Todas as alterações de um registro, da mais recente para a mais antiga."""
    linhas = db.execute(
        _consulta(entidade)
        .where(RegistroAlteracao.entidade_id == entidade_id)
        .order_by(RegistroAlteracao.feito_em.desc(), RegistroAlteracao.id.desc())
    ).all()
    return [_saida(r, nome) for r, nome in linhas]

"""Quem recebe os avisos do condomínio, e o envio a cada um por e-mail.

Só cadastros ativos: o morador que se mudou (inativado), o cadastro
recusado ou ainda pendente e o síndico anterior não recebem mais nada.
"""
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import CanalVerificacao, Papel, StatusUsuario
from app.models.usuario import Usuario
from app.services import notificacao


def _ativos(papel: Papel):
    return (select(Usuario)
            .where(Usuario.papel == papel, Usuario.status == StatusUsuario.ATIVO)
            .order_by(Usuario.nome, Usuario.id))


def moradores_da_unidade(db: Session, unidade_id: int, *,
                         so_quem_mora: bool = True) -> list[Usuario]:
    """Os moradores do apartamento. Por padrão, só quem mora lá: o dono que
    não mora não recebe o visitante, a encomenda nem leva a chave. Com
    so_quem_mora=False entra também ele — a multa, a cobrança e a
    declaração de quitação são do condômino."""
    consulta = _ativos(Papel.MORADOR).where(Usuario.unidade_id == unidade_id)
    if so_quem_mora:
        consulta = consulta.where(Usuario.reside.is_(True))
    return list(db.scalars(consulta).all())


def moradores_do_condominio(db: Session, condominio_id: int) -> list[Usuario]:
    """Todos os condôminos, morem ou não no apartamento: a assembleia é de
    todos eles."""
    return list(db.scalars(
        _ativos(Papel.MORADOR).where(Usuario.condominio_id == condominio_id)).all())


def sindicos(db: Session, condominio_id: int) -> list[Usuario]:
    """O síndico atual (o anterior continua no banco, inativado)."""
    return list(db.scalars(
        _ativos(Papel.SINDICO).where(Usuario.condominio_id == condominio_id)).all())


def avisar(pessoas: Iterable[Usuario], titulo: str, mensagem: str) -> None:
    for pessoa in pessoas:
        notificacao.notificar(pessoa.email, CanalVerificacao.EMAIL, titulo, mensagem)

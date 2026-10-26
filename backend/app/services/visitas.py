"""Regras das autorizações de visita usadas pela portaria e pelo
controle de chaves: quando a autorização vale e o que a portaria vê do
documento."""
from __future__ import annotations

from datetime import date

from sqlalchemy import exists

from app.models.enums import Papel, StatusUsuario
from app.models.portaria import AutorizacaoVisita
from app.models.usuario import Usuario


def autorizador_mora_la():
    """Condição SQL: quem autorizou ainda mora no apartamento — ativo,
    na mesma unidade e desde antes de autorizar (o que se mudou e voltou
    não ressuscita as autorizações antigas)."""
    return exists().where(
        Usuario.id == AutorizacaoVisita.autorizado_por_id,
        Usuario.unidade_id == AutorizacaoVisita.unidade_id,
        Usuario.papel == Papel.MORADOR,
        Usuario.status == StatusUsuario.ATIVO,
        Usuario.reside.is_(True),
        Usuario.unidade_desde <= AutorizacaoVisita.criado_em,
    )


def vale_no_dia(a: AutorizacaoVisita, dia: date) -> bool:
    return (not a.inativo and a.valida_de <= dia <= a.valida_ate
            and (not a.dias_semana or str(dia.isoweekday()) in a.dias_semana))


def documento_mascarado(documento: str | None) -> str | None:
    """A portaria vê só o meio do CPF: ela digita o do documento que a
    pessoa apresenta, e o sistema confere — copiar da tela não serve."""
    if not documento:
        return None
    return f"***.{documento[3:6]}.{documento[6:9]}-**"

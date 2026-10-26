"""O código da declaração de quitação e quanto tempo ela vale."""
from __future__ import annotations

import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.declaracao import DeclaracaoQuitacao

# Quem recebe a declaração confia nela por este prazo; depois, pede outra.
VALIDADE_DIAS = 30
# Sem 0/O e 1/I, que se confundem ao digitar: 32 símbolos em 16 posições,
# 80 bits — não se adivinha.
ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
TAMANHO_CODIGO = 16


def novo_codigo(db: Session) -> str:
    while True:
        codigo = "".join(secrets.choice(ALFABETO) for _ in range(TAMANHO_CODIGO))
        if db.scalar(select(DeclaracaoQuitacao.id)
                     .where(DeclaracaoQuitacao.codigo == codigo)) is None:
            return codigo


def formatar(codigo: str) -> str:
    """CRDS-BGYH-AD9X-PM6J: como se lê e se digita."""
    return "-".join(codigo[i:i + 4] for i in range(0, TAMANHO_CODIGO, 4))

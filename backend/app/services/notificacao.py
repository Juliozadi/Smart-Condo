"""Envio de códigos e avisos.

Documentação, seção 9: o sistema "envia um código pelo meio escolhido pelo
usuário" (e-mail ou SMS).

Enquanto não há contrato com provedor de e-mail/SMS, o envio é registrado no
log. A interface já é a definitiva: trocar por SMTP ou por uma API de SMS é
substituir o corpo de `enviar`, sem mexer nas rotas.
"""
from __future__ import annotations

import logging

from app.models.enums import CanalVerificacao

logger = logging.getLogger("smartcondo.notificacao")


def mascarar_destino(destino: str, canal: CanalVerificacao) -> str:
    """Esconde parte do destino para não vazar o dado completo na resposta."""
    if canal == CanalVerificacao.EMAIL:
        usuario, _, dominio = destino.partition("@")
        if not dominio:
            return "***"
        visivel = usuario[:2] if len(usuario) > 2 else usuario[:1]
        return f"{visivel}{'*' * max(len(usuario) - len(visivel), 1)}@{dominio}"

    digitos = "".join(c for c in destino if c.isdigit())
    if len(digitos) < 4:
        return "***"
    return f"{'*' * (len(digitos) - 4)}{digitos[-4:]}"


def enviar_codigo(destino: str, canal: CanalVerificacao, codigo: str, finalidade: str) -> None:
    """Entrega o código ao usuário pelo canal escolhido."""
    logger.info(
        "Código de %s enviado por %s para %s: %s",
        finalidade, canal.value, mascarar_destino(destino, canal), codigo,
    )


def notificar(destino: str, canal: CanalVerificacao, titulo: str, mensagem: str) -> None:
    """Aviso avulso — chegada de encomenda, visitante na portaria, etc."""
    logger.info(
        "Notificação por %s para %s — %s: %s",
        canal.value, mascarar_destino(destino, canal), titulo, mensagem,
    )

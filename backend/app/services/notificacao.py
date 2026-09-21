"""Envio de códigos e avisos.

Documentação, seção 9: o sistema "envia um código pelo meio escolhido pelo
usuário" (e-mail ou SMS).

O e-mail sai por SMTP, configurado pelas variáveis SMTP_* do .env. Sem
SMTP_HOST o envio é apenas registrado no log — o que serve para
desenvolvimento, mas em produção deixaria o morador esperando um código
que nunca chega; por isso a aplicação avisa ao subir nessa situação.

SMS ainda não tem provedor. A interface não oferece a opção (o front-end
nunca manda o canal, então cai sempre em e-mail), mas se alguém chamar a
API pedindo SMS, a tentativa é registrada como não entregue em vez de
fingir sucesso.
"""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.models.enums import CanalVerificacao

logger = logging.getLogger("smartcondo.notificacao")


class FalhaDeEnvio(RuntimeError):
    """O provedor recusou ou não respondeu."""


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


# ── Textos ───────────────────────────────────────────────────────────
ASSUNTOS = {
    "confirmacao_cadastro": "Seu código de confirmação — SmartCondo",
    "recuperacao_senha": "Redefinição de senha — SmartCondo",
}

ABERTURAS = {
    "confirmacao_cadastro": (
        "Recebemos o seu cadastro no SmartCondo. Informe o código abaixo "
        "na tela de confirmação para ativar a conta."
    ),
    "recuperacao_senha": (
        "Você pediu para redefinir a sua senha do SmartCondo. Informe o "
        "código abaixo na tela de recuperação."
    ),
}


def _corpo_do_codigo(codigo: str, finalidade: str) -> tuple[str, str]:
    """Devolve (texto puro, html) da mensagem do código."""
    abertura = ABERTURAS.get(finalidade, "Use o código abaixo para continuar.")
    validade = settings.CODIGO_VERIFICACAO_EXPIRA_MIN

    texto = (
        f"{abertura}\n\n"
        f"    {codigo}\n\n"
        f"O código vale por {validade} minutos.\n\n"
        "Se não foi você que pediu, ignore esta mensagem: sem o código, "
        "nada acontece.\n\n"
        "— SmartCondo, gestão de condomínios"
    )
    html = (
        '<div style="font-family:Arial,Helvetica,sans-serif;font-size:15px;'
        'line-height:1.6;color:#0a1520;max-width:520px">'
        '<p style="font-size:20px;font-weight:700;margin:0 0 14px">SmartCondo</p>'
        f"<p>{abertura}</p>"
        '<p style="font-size:30px;font-weight:800;letter-spacing:6px;'
        'background:#f2f8f9;border:1px solid #c4d4d8;border-radius:8px;'
        f'padding:14px;text-align:center;margin:20px 0">{codigo}</p>'
        f"<p>O código vale por {validade} minutos.</p>"
        '<p style="color:#526975;font-size:13px">Se não foi você que pediu, '
        "ignore esta mensagem: sem o código, nada acontece.</p>"
        "</div>"
    )
    return texto, html


# ── Transporte ───────────────────────────────────────────────────────
def _entregar_email(destino: str, assunto: str, texto: str, html: str | None = None) -> None:
    """Manda a mensagem pelo SMTP configurado. Erra alto se não conseguir."""
    msg = EmailMessage()
    msg["Subject"] = assunto
    msg["From"] = settings.SMTP_REMETENTE
    msg["To"] = destino
    msg.set_content(texto)
    if html:
        msg.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP(
            settings.SMTP_HOST, settings.SMTP_PORTA, timeout=settings.SMTP_TIMEOUT_S
        ) as servidor:
            if settings.SMTP_TLS:
                servidor.starttls()
            if settings.SMTP_USUARIO:
                servidor.login(settings.SMTP_USUARIO, settings.SMTP_SENHA)
            servidor.send_message(msg)
    except Exception as erro:  # noqa: BLE001 — qualquer falha do provedor
        raise FalhaDeEnvio(str(erro)) from erro


def _registrar_sem_envio(canal: CanalVerificacao, destino: str, o_que: str) -> None:
    """Não há provedor para este canal: deixa claro que nada foi entregue."""
    logger.warning(
        "SEM ENVIO (%s não configurado) — %s para %s não foi entregue.",
        canal.value, o_que, mascarar_destino(destino, canal),
    )


# ── Interface usada pelas rotas ──────────────────────────────────────
def enviar_codigo(destino: str, canal: CanalVerificacao, codigo: str, finalidade: str) -> None:
    """Entrega o código ao usuário pelo canal escolhido.

    Não interrompe o cadastro se o provedor falhar: a conta já existe e o
    usuário pode pedir o reenvio. A falha fica no log como erro.
    """
    if canal != CanalVerificacao.EMAIL:
        _registrar_sem_envio(canal, destino, f"código de {finalidade}")
        return

    if not settings.email_configurado:
        # Em desenvolvimento o código aparece aqui e também volta na
        # resposta da API (campo codigo_debug), para testar sem provedor.
        if settings.DEBUG:
            logger.info(
                "SEM SMTP — código de %s para %s: %s",
                finalidade, mascarar_destino(destino, canal), codigo,
            )
        else:
            _registrar_sem_envio(canal, destino, f"código de {finalidade}")
        return

    assunto = ASSUNTOS.get(finalidade, "SmartCondo")
    texto, html = _corpo_do_codigo(codigo, finalidade)
    try:
        _entregar_email(destino, assunto, texto, html)
    except FalhaDeEnvio as erro:
        logger.error(
            "Falha ao enviar o código de %s para %s: %s",
            finalidade, mascarar_destino(destino, canal), erro,
        )
        return
    # O código nunca vai para o log quando foi de fato enviado: quem lê o
    # log do servidor tomaria qualquer conta.
    logger.info(
        "Código de %s enviado por e-mail para %s.",
        finalidade, mascarar_destino(destino, canal),
    )


def notificar(destino: str, canal: CanalVerificacao, titulo: str, mensagem: str) -> None:
    """Aviso avulso — chegada de encomenda, visitante na portaria, etc."""
    if canal != CanalVerificacao.EMAIL or not settings.email_configurado:
        logger.info(
            "Notificação por %s para %s — %s: %s",
            canal.value, mascarar_destino(destino, canal), titulo, mensagem,
        )
        return
    try:
        _entregar_email(destino, f"{titulo} — SmartCondo", mensagem)
    except FalhaDeEnvio as erro:
        logger.error(
            "Falha ao notificar %s: %s", mascarar_destino(destino, canal), erro
        )
        return
    logger.info("Notificação enviada para %s — %s.", mascarar_destino(destino, canal), titulo)

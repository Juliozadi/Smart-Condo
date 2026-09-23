"""Envio de códigos e avisos.

Documentação, seção 12: o sistema "envia um código pelo meio escolhido pelo
usuário" (e-mail ou SMS).

O e-mail sai por SMTP, configurado pelas variáveis SMTP_* do .env. Sem
SMTP_HOST o envio é apenas registrado no log — o que serve para
desenvolvimento, mas em produção deixaria o morador esperando um código
que nunca chega; por isso a aplicação avisa ao subir nessa situação.

O SMS sai pelo Twilio, configurado pelas variáveis SMS_* do .env. Sem
elas a tela não oferece a opção (GET /auth/canais diz o que está
ativo); se alguém chamar a API pedindo SMS mesmo assim, a tentativa é
registrada como não entregue em vez de fingir sucesso.
"""
from __future__ import annotations

import base64
import json
import logging
import re
import smtplib
import urllib.error
import urllib.parse
import urllib.request
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


def _texto_sms_do_codigo(codigo: str, finalidade: str) -> str:
    """Curto de propósito: SMS acima de 160 caracteres é cobrado em dobro."""
    para = "confirmar o cadastro" if finalidade == "confirmacao_cadastro" else "redefinir a senha"
    return (f"SmartCondo: seu código para {para} é {codigo}. "
            f"Vale por {settings.CODIGO_VERIFICACAO_EXPIRA_MIN} min. Não compartilhe.")


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


def telefone_internacional(telefone: str) -> str | None:
    """(67) 99999-0002 → +5567999990002. None se não parecer um celular.

    O provedor exige o formato internacional. Um número já com + é mantido.
    """
    if telefone.strip().startswith("+"):
        digitos = "+" + re.sub(r"\D", "", telefone)
        return digitos if len(digitos) >= 11 else None
    digitos = re.sub(r"\D", "", telefone)
    if digitos.startswith("55") and len(digitos) in (12, 13):
        digitos = digitos[2:]
    if len(digitos) not in (10, 11):
        return None
    return "+55" + digitos


URL_TWILIO = "https://api.twilio.com/2010-04-01/Accounts/{conta}/Messages.json"


def _entregar_sms(telefone: str, texto: str) -> None:
    """Manda o SMS pelo Twilio. Erra alto se não conseguir."""
    destino = telefone_internacional(telefone)
    if destino is None:
        raise FalhaDeEnvio("telefone em formato inválido")
    corpo = urllib.parse.urlencode(
        {"To": destino, "From": settings.SMS_REMETENTE, "Body": texto}
    ).encode()
    credencial = base64.b64encode(f"{settings.SMS_CONTA}:{settings.SMS_TOKEN}".encode()).decode()
    pedido = urllib.request.Request(
        URL_TWILIO.format(conta=urllib.parse.quote(settings.SMS_CONTA, safe="")),
        data=corpo,
        headers={"Authorization": f"Basic {credencial}",
                 "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(pedido, timeout=settings.SMS_TIMEOUT_S) as resposta:
            if resposta.status >= 300:
                raise FalhaDeEnvio(f"provedor respondeu {resposta.status}")
    except urllib.error.HTTPError as erro:
        # O Twilio explica o motivo no corpo (número inválido, saldo...).
        try:
            motivo = json.loads(erro.read().decode()).get("message", "")
        except Exception:  # noqa: BLE001
            motivo = ""
        raise FalhaDeEnvio(f"provedor respondeu {erro.code} {motivo}".strip()) from erro
    except FalhaDeEnvio:
        raise
    except Exception as erro:  # noqa: BLE001 — rede, DNS, tempo esgotado
        raise FalhaDeEnvio(str(erro)) from erro


def canal_disponivel(canal: CanalVerificacao) -> bool:
    if canal == CanalVerificacao.EMAIL:
        return settings.email_configurado
    return settings.sms_configurado


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
    if not canal_disponivel(canal):
        # Em desenvolvimento o código aparece aqui e também volta na
        # resposta da API (campo codigo_debug), para testar sem provedor.
        if settings.DEBUG:
            logger.info(
                "SEM PROVEDOR — código de %s para %s: %s",
                finalidade, mascarar_destino(destino, canal), codigo,
            )
        else:
            _registrar_sem_envio(canal, destino, f"código de {finalidade}")
        return

    try:
        if canal == CanalVerificacao.SMS:
            _entregar_sms(destino, _texto_sms_do_codigo(codigo, finalidade))
        else:
            assunto = ASSUNTOS.get(finalidade, "SmartCondo")
            texto, html = _corpo_do_codigo(codigo, finalidade)
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
        "Código de %s enviado por %s para %s.",
        finalidade, "SMS" if canal == CanalVerificacao.SMS else "e-mail",
        mascarar_destino(destino, canal),
    )


def notificar(destino: str, canal: CanalVerificacao, titulo: str, mensagem: str) -> None:
    """Aviso avulso — chegada de encomenda, visitante na portaria, etc."""
    if not canal_disponivel(canal):
        logger.info(
            "Notificação por %s para %s — %s: %s",
            canal.value, mascarar_destino(destino, canal), titulo, mensagem,
        )
        return
    try:
        if canal == CanalVerificacao.SMS:
            _entregar_sms(destino, f"SmartCondo — {titulo}: {mensagem}"[:320])
        else:
            _entregar_email(destino, f"{titulo} — SmartCondo", mensagem)
    except FalhaDeEnvio as erro:
        logger.error(
            "Falha ao notificar %s: %s", mascarar_destino(destino, canal), erro
        )
        return
    logger.info("Notificação enviada para %s — %s.", mascarar_destino(destino, canal), titulo)

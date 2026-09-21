"""Entrega dos códigos de confirmação e de recuperação de senha.

Documentação, seção 9. O que estes testes protegem: sem envio real, o
morador que se cadastra fica preso esperando um código que nunca chega.
"""
from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import settings
from app.models.enums import CanalVerificacao
from app.services import notificacao


@pytest.fixture
def smtp_configurado(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.exemplo.com")
    monkeypatch.setattr(settings, "SMTP_PORTA", 587)
    monkeypatch.setattr(settings, "SMTP_USUARIO", "conta@exemplo.com")
    monkeypatch.setattr(settings, "SMTP_SENHA", "segredo")
    monkeypatch.setattr(settings, "SMTP_TLS", True)


def test_com_smtp_a_mensagem_sai_pelo_servidor(smtp_configurado):
    with patch("app.services.notificacao.smtplib.SMTP") as SMTP:
        servidor = MagicMock()
        SMTP.return_value.__enter__.return_value = servidor
        notificacao.enviar_codigo(
            "morador@exemplo.com", CanalVerificacao.EMAIL, "123456", "confirmacao_cadastro"
        )

    SMTP.assert_called_once()
    servidor.starttls.assert_called_once()
    servidor.login.assert_called_once_with("conta@exemplo.com", "segredo")
    servidor.send_message.assert_called_once()

    msg = servidor.send_message.call_args[0][0]
    assert msg["To"] == "morador@exemplo.com"
    assert "confirmação" in msg["Subject"]
    assert "123456" in msg.get_body(("plain",)).get_content()


def test_codigo_nao_vai_para_o_log_quando_e_enviado(smtp_configurado, caplog):
    """Quem lê o log do servidor não pode tomar a conta de ninguém."""
    with patch("app.services.notificacao.smtplib.SMTP") as SMTP:
        SMTP.return_value.__enter__.return_value = MagicMock()
        with caplog.at_level(logging.DEBUG, logger="smartcondo.notificacao"):
            notificacao.enviar_codigo(
                "morador@exemplo.com", CanalVerificacao.EMAIL, "987654", "recuperacao_senha"
            )

    registrado = " ".join(r.getMessage() for r in caplog.records)
    assert "987654" not in registrado
    assert "enviado" in registrado


def test_destino_aparece_mascarado_no_log(smtp_configurado, caplog):
    with patch("app.services.notificacao.smtplib.SMTP") as SMTP:
        SMTP.return_value.__enter__.return_value = MagicMock()
        with caplog.at_level(logging.INFO, logger="smartcondo.notificacao"):
            notificacao.enviar_codigo(
                "fulano@exemplo.com", CanalVerificacao.EMAIL, "111222", "confirmacao_cadastro"
            )

    registrado = " ".join(r.getMessage() for r in caplog.records)
    assert "fulano@exemplo.com" not in registrado
    assert "fu****@exemplo.com" in registrado


def test_falha_do_provedor_nao_derruba_o_cadastro(smtp_configurado, caplog):
    """A conta já existe; o usuário pode pedir o reenvio."""
    with patch("app.services.notificacao.smtplib.SMTP", side_effect=OSError("recusado")):
        with caplog.at_level(logging.ERROR, logger="smartcondo.notificacao"):
            notificacao.enviar_codigo(
                "morador@exemplo.com", CanalVerificacao.EMAIL, "333444", "confirmacao_cadastro"
            )
    assert any(r.levelno == logging.ERROR for r in caplog.records)
    assert "333444" not in " ".join(r.getMessage() for r in caplog.records)


def test_sem_smtp_nao_tenta_enviar(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    with patch("app.services.notificacao.smtplib.SMTP") as SMTP:
        notificacao.enviar_codigo(
            "morador@exemplo.com", CanalVerificacao.EMAIL, "555666", "confirmacao_cadastro"
        )
    SMTP.assert_not_called()


def test_sms_nao_finge_que_entregou(smtp_configurado, caplog):
    """Não há provedor de SMS: registrar como não entregue, não como envio."""
    with patch("app.services.notificacao.smtplib.SMTP") as SMTP:
        with caplog.at_level(logging.WARNING, logger="smartcondo.notificacao"):
            notificacao.enviar_codigo(
                "67999990000", CanalVerificacao.SMS, "777888", "confirmacao_cadastro"
            )
    SMTP.assert_not_called()
    assert "SEM ENVIO" in " ".join(r.getMessage() for r in caplog.records)


def test_mascara_esconde_o_destino():
    assert notificacao.mascarar_destino("joao@exemplo.com", CanalVerificacao.EMAIL) == "jo**@exemplo.com"
    assert notificacao.mascarar_destino("67999990000", CanalVerificacao.SMS) == "*******0000"

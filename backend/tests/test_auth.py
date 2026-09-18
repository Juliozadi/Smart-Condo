"""Testes dos casos de uso da seção 9 da documentação."""
from __future__ import annotations

import pytest

from app.models.enums import Papel, StatusUsuario
from app.models.usuario import Usuario

CPF_A = "529.982.247-25"
CPF_B = "168.995.350-09"


def dados_sindico(**extra):
    base = {
        "nome": "Roberto Nascimento",
        "email": "roberto@exemplo.com",
        "cpf": CPF_A,
        "telefone": "(67) 99999-8888",
        "senha": "senhaforte123",
    }
    base.update(extra)
    return base


def cadastrar_e_confirmar_sindico(cliente, **extra):
    """Atalho: cadastra o síndico e já confirma o código."""
    r = cliente.post("/api/v1/auth/cadastro/sindico", json=dados_sindico(**extra))
    assert r.status_code == 201, r.text
    corpo = r.json()

    conf = cliente.post(
        "/api/v1/auth/confirmar",
        json={"email": corpo["usuario"]["email"], "codigo": corpo["codigo_debug"]},
    )
    assert conf.status_code == 200, conf.text
    return conf.json()


def logar(cliente, email, senha):
    r = cliente.post("/api/v1/auth/login", json={"email": email, "senha": senha})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


# ── Cadastro (seção 9) ───────────────────────────────────────────────
def test_cadastro_do_sindico_gera_codigo_e_fica_aguardando(cliente):
    r = cliente.post("/api/v1/auth/cadastro/sindico", json=dados_sindico())
    assert r.status_code == 201, r.text
    corpo = r.json()

    assert corpo["usuario"]["papel"] == Papel.SINDICO.value
    assert corpo["usuario"]["status"] == StatusUsuario.AGUARDANDO_CODIGO.value
    assert corpo["canal"] == "email"
    # O destino volta mascarado, não em texto puro.
    assert corpo["codigo_enviado_para"] == "ro*****@exemplo.com"
    assert len(corpo["codigo_debug"]) == 6


def test_cpf_invalido_e_recusado(cliente):
    r = cliente.post("/api/v1/auth/cadastro/sindico", json=dados_sindico(cpf="111.111.111-11"))
    assert r.status_code == 422
    assert "CPF inválido" in r.text


def test_email_repetido_e_recusado(cliente):
    cliente.post("/api/v1/auth/cadastro/sindico", json=dados_sindico())
    r = cliente.post("/api/v1/auth/cadastro/sindico", json=dados_sindico(cpf=CPF_B))
    assert r.status_code == 409
    assert "e-mail" in r.json()["detalhe"]


def test_cpf_repetido_e_recusado(cliente):
    cliente.post("/api/v1/auth/cadastro/sindico", json=dados_sindico())
    r = cliente.post("/api/v1/auth/cadastro/sindico", json=dados_sindico(email="outro@exemplo.com"))
    assert r.status_code == 409
    assert "CPF" in r.json()["detalhe"]


def test_a_senha_nunca_e_guardada_em_texto_puro(cliente, db):
    cliente.post("/api/v1/auth/cadastro/sindico", json=dados_sindico())
    usuario = db.query(Usuario).filter(Usuario.email == "roberto@exemplo.com").one()
    assert usuario.senha_hash != "senhaforte123"
    assert usuario.senha_hash.startswith("$2b$")


# ── Confirmação do código ────────────────────────────────────────────
def test_codigo_errado_nao_confirma(cliente):
    r = cliente.post("/api/v1/auth/cadastro/sindico", json=dados_sindico())
    codigo_certo = r.json()["codigo_debug"]
    errado = "000000" if codigo_certo != "000000" else "111111"

    conf = cliente.post(
        "/api/v1/auth/confirmar", json={"email": "roberto@exemplo.com", "codigo": errado}
    )
    assert conf.status_code == 400
    assert conf.json()["detalhe"] == "Código incorreto."


def test_o_codigo_so_pode_ser_usado_uma_vez(cliente):
    r = cliente.post("/api/v1/auth/cadastro/sindico", json=dados_sindico())
    codigo = r.json()["codigo_debug"]

    primeira = cliente.post(
        "/api/v1/auth/confirmar", json={"email": "roberto@exemplo.com", "codigo": codigo}
    )
    assert primeira.status_code == 200

    segunda = cliente.post(
        "/api/v1/auth/confirmar", json={"email": "roberto@exemplo.com", "codigo": codigo}
    )
    assert segunda.status_code == 409


def test_reenviar_invalida_o_codigo_anterior(cliente):
    r = cliente.post("/api/v1/auth/cadastro/sindico", json=dados_sindico())
    codigo_antigo = r.json()["codigo_debug"]

    reenvio = cliente.post(
        "/api/v1/auth/codigo/reenviar", json={"email": "roberto@exemplo.com"}
    )
    assert reenvio.status_code == 200

    conf = cliente.post(
        "/api/v1/auth/confirmar", json={"email": "roberto@exemplo.com", "codigo": codigo_antigo}
    )
    assert conf.status_code == 400


def test_reenvio_para_email_inexistente_nao_revela_nada(cliente):
    r = cliente.post("/api/v1/auth/codigo/reenviar", json={"email": "ninguem@exemplo.com"})
    assert r.status_code == 200
    assert "Se houver" in r.json()["detalhe"]


def test_sindico_fica_ativo_apos_confirmar(cliente):
    usuario = cadastrar_e_confirmar_sindico(cliente)
    assert usuario["status"] == StatusUsuario.ATIVO.value


# ── Login (seção 9) ──────────────────────────────────────────────────
def test_login_devolve_token(cliente):
    cadastrar_e_confirmar_sindico(cliente)
    r = cliente.post(
        "/api/v1/auth/login",
        json={"email": "roberto@exemplo.com", "senha": "senhaforte123"},
    )
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["usuario"]["papel"] == "sindico"
    assert corpo["access_token"]


def test_senha_errada_nao_loga(cliente):
    cadastrar_e_confirmar_sindico(cliente)
    r = cliente.post(
        "/api/v1/auth/login", json={"email": "roberto@exemplo.com", "senha": "errada12345"}
    )
    assert r.status_code == 401


def test_email_inexistente_da_a_mesma_mensagem_da_senha_errada(cliente):
    """Não revela quais e-mails estão cadastrados."""
    cadastrar_e_confirmar_sindico(cliente)
    a = cliente.post(
        "/api/v1/auth/login", json={"email": "roberto@exemplo.com", "senha": "errada12345"}
    )
    b = cliente.post(
        "/api/v1/auth/login", json={"email": "ninguem@exemplo.com", "senha": "errada12345"}
    )
    assert a.status_code == b.status_code == 401
    assert a.json()["detalhe"] == b.json()["detalhe"]


def test_sem_confirmar_o_codigo_nao_loga(cliente):
    cliente.post("/api/v1/auth/cadastro/sindico", json=dados_sindico())
    r = cliente.post(
        "/api/v1/auth/login", json={"email": "roberto@exemplo.com", "senha": "senhaforte123"}
    )
    assert r.status_code == 403
    assert "Confirme o código" in r.json()["detalhe"]


# ── Rota protegida ───────────────────────────────────────────────────
def test_rota_protegida_exige_token(cliente):
    assert cliente.get("/api/v1/auth/eu").status_code == 401
    assert cliente.get(
        "/api/v1/auth/eu", headers={"Authorization": "Bearer token-invalido"}
    ).status_code == 401


def test_rota_protegida_com_token_valido(cliente):
    cadastrar_e_confirmar_sindico(cliente)
    token = logar(cliente, "roberto@exemplo.com", "senhaforte123")

    r = cliente.get("/api/v1/auth/eu", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "roberto@exemplo.com"


# ── Esqueci minha senha (seção 9) ────────────────────────────────────
def test_recuperacao_de_senha_completa(cliente, db):
    from app.models.enums import FinalidadeCodigo
    from app.models.usuario import CodigoVerificacao
    from app.core.security import gerar_hash_codigo

    cadastrar_e_confirmar_sindico(cliente)

    pedido = cliente.post(
        "/api/v1/auth/senha/recuperar", json={"email": "roberto@exemplo.com"}
    )
    assert pedido.status_code == 200

    # O código não volta na resposta; é lido do banco, como o usuário leria
    # no e-mail. O que está gravado é o hash, então testamos por comparação.
    registro = (
        db.query(CodigoVerificacao)
        .filter(CodigoVerificacao.finalidade == FinalidadeCodigo.RECUPERACAO_SENHA)
        .order_by(CodigoVerificacao.id.desc())
        .first()
    )
    assert registro is not None
    codigo = next(
        f"{n:06d}" for n in range(1000000)
        if gerar_hash_codigo(f"{n:06d}") == registro.codigo_hash
    )

    troca = cliente.post(
        "/api/v1/auth/senha/redefinir",
        json={
            "email": "roberto@exemplo.com",
            "codigo": codigo,
            "nova_senha": "novasenha456",
            "confirmacao_senha": "novasenha456",
        },
    )
    assert troca.status_code == 200, troca.text

    assert cliente.post(
        "/api/v1/auth/login", json={"email": "roberto@exemplo.com", "senha": "senhaforte123"}
    ).status_code == 401
    assert cliente.post(
        "/api/v1/auth/login", json={"email": "roberto@exemplo.com", "senha": "novasenha456"}
    ).status_code == 200


def test_recuperacao_para_email_inexistente_nao_revela_nada(cliente):
    r = cliente.post("/api/v1/auth/senha/recuperar", json={"email": "ninguem@exemplo.com"})
    assert r.status_code == 200
    assert "Se o e-mail estiver cadastrado" in r.json()["detalhe"]


def test_confirmacao_divergente_e_recusada(cliente):
    cadastrar_e_confirmar_sindico(cliente)
    r = cliente.post(
        "/api/v1/auth/senha/redefinir",
        json={
            "email": "roberto@exemplo.com",
            "codigo": "123456",
            "nova_senha": "novasenha456",
            "confirmacao_senha": "outrasenha789",
        },
    )
    assert r.status_code == 422
    assert "confirmação não confere" in r.text


def test_troca_de_senha_logado(cliente):
    cadastrar_e_confirmar_sindico(cliente)
    token = logar(cliente, "roberto@exemplo.com", "senhaforte123")
    cab = {"Authorization": f"Bearer {token}"}

    errada = cliente.post(
        "/api/v1/auth/senha/trocar",
        json={"senha_atual": "naoehessa1", "nova_senha": "novasenha456"},
        headers=cab,
    )
    assert errada.status_code == 400

    certa = cliente.post(
        "/api/v1/auth/senha/trocar",
        json={"senha_atual": "senhaforte123", "nova_senha": "novasenha456"},
        headers=cab,
    )
    assert certa.status_code == 200
    assert cliente.post(
        "/api/v1/auth/login", json={"email": "roberto@exemplo.com", "senha": "novasenha456"}
    ).status_code == 200


def test_saude(cliente):
    r = cliente.get("/api/v1/saude")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

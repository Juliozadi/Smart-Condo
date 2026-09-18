"""Testes de cadastro, login e recuperação de senha.

Documentação, seção 9. Com a hierarquia atual, o único cadastro público é o
do morador: síndico é criado pelo administrador e porteiro pelo síndico.
"""
from __future__ import annotations

import pytest

from app.models.enums import Papel, StatusUsuario
from app.models.usuario import Usuario
from tests.fixtures import CPFS, cab, montar_condominio, token

CPF_MORADOR = CPFS[1]


@pytest.fixture
def cenario(cliente, db):
    return montar_condominio(cliente, db)


def dados_morador(cenario, **extra):
    base = {
        "nome": "João Silva",
        "email": "joao@exemplo.com",
        "cpf": CPF_MORADOR,
        "telefone": "(67) 99999-8888",
        "senha": "senhaforte123",
        "codigo_condominio": cenario["cond"]["codigo_acesso"],
        "unidade_numero": "204",
        "tipo_ocupacao": "proprietario",
    }
    base.update(extra)
    return base


def cadastrar(cliente, cenario, **extra):
    return cliente.post("/api/v1/auth/cadastro/morador", json=dados_morador(cenario, **extra))


def cadastrar_e_confirmar(cliente, cenario, **extra):
    r = cadastrar(cliente, cenario, **extra)
    assert r.status_code == 201, r.text
    corpo = r.json()
    conf = cliente.post(
        "/api/v1/auth/confirmar",
        json={"email": corpo["usuario"]["email"], "codigo": corpo["codigo_debug"]},
    )
    assert conf.status_code == 200, conf.text
    return conf.json()


def aprovar(cliente, cenario, usuario_id):
    r = cliente.post(
        f"/api/v1/usuarios/{usuario_id}/aprovacao",
        json={"aprovado": True},
        headers=cab(cenario["sindico"]),
    )
    assert r.status_code == 200, r.text


# ── Só o morador se cadastra sozinho ─────────────────────────────────
def test_nao_existe_mais_cadastro_publico_de_sindico(cliente):
    r = cliente.post(
        "/api/v1/auth/cadastro/sindico",
        json={
            "nome": "Quem Quiser", "email": "qualquer@exemplo.com", "cpf": CPFS[0],
            "telefone": "(67) 99999-0001", "senha": "senhaforte123",
        },
    )
    assert r.status_code in (404, 405)


def test_cadastro_do_morador_gera_codigo(cliente, cenario):
    r = cadastrar(cliente, cenario)
    assert r.status_code == 201, r.text
    corpo = r.json()

    assert corpo["usuario"]["papel"] == Papel.MORADOR.value
    assert corpo["usuario"]["status"] == StatusUsuario.AGUARDANDO_CODIGO.value
    assert corpo["canal"] == "email"
    # O destino volta mascarado, não em texto puro.
    assert corpo["codigo_enviado_para"] == "jo**@exemplo.com"
    assert len(corpo["codigo_debug"]) == 6


def test_cpf_invalido_e_recusado(cliente, cenario):
    r = cadastrar(cliente, cenario, cpf="111.111.111-11")
    assert r.status_code == 422
    assert "CPF inválido" in r.text


def test_senha_fraca_e_recusada(cliente, cenario):
    r = cadastrar(cliente, cenario, senha="senhasenha")
    assert r.status_code == 422
    assert "número ou símbolo" in r.text


def test_email_repetido_e_recusado(cliente, cenario):
    cadastrar(cliente, cenario)
    r = cadastrar(cliente, cenario, cpf=CPFS[3])
    assert r.status_code == 409
    assert "e-mail" in r.json()["detalhe"]


def test_cpf_repetido_e_recusado(cliente, cenario):
    cadastrar(cliente, cenario)
    r = cadastrar(cliente, cenario, email="outro@exemplo.com")
    assert r.status_code == 409
    assert "CPF" in r.json()["detalhe"]


def test_a_senha_nunca_e_guardada_em_texto_puro(cliente, cenario, db):
    cadastrar(cliente, cenario)
    usuario = db.query(Usuario).filter(Usuario.email == "joao@exemplo.com").one()
    assert usuario.senha_hash != "senhaforte123"
    assert usuario.senha_hash.startswith("$2b$")


# ── Confirmação do código ────────────────────────────────────────────
def test_codigo_errado_nao_confirma(cliente, cenario):
    codigo_certo = cadastrar(cliente, cenario).json()["codigo_debug"]
    errado = "000000" if codigo_certo != "000000" else "111111"

    conf = cliente.post(
        "/api/v1/auth/confirmar", json={"email": "joao@exemplo.com", "codigo": errado}
    )
    assert conf.status_code == 400
    assert conf.json()["detalhe"] == "Código incorreto."


def test_o_codigo_so_pode_ser_usado_uma_vez(cliente, cenario):
    codigo = cadastrar(cliente, cenario).json()["codigo_debug"]
    corpo = {"email": "joao@exemplo.com", "codigo": codigo}

    assert cliente.post("/api/v1/auth/confirmar", json=corpo).status_code == 200
    assert cliente.post("/api/v1/auth/confirmar", json=corpo).status_code == 409


def test_reenviar_invalida_o_codigo_anterior(cliente, cenario):
    antigo = cadastrar(cliente, cenario).json()["codigo_debug"]

    reenvio = cliente.post("/api/v1/auth/codigo/reenviar", json={"email": "joao@exemplo.com"})
    assert reenvio.status_code == 200

    conf = cliente.post(
        "/api/v1/auth/confirmar", json={"email": "joao@exemplo.com", "codigo": antigo}
    )
    assert conf.status_code == 400


def test_reenvio_para_email_inexistente_nao_revela_nada(cliente):
    r = cliente.post("/api/v1/auth/codigo/reenviar", json={"email": "ninguem@exemplo.com"})
    assert r.status_code == 200
    assert "Se houver" in r.json()["detalhe"]


def test_apos_confirmar_o_morador_aguarda_o_sindico(cliente, cenario):
    """Quem se cadastra sozinho ainda depende da aprovação do síndico."""
    usuario = cadastrar_e_confirmar(cliente, cenario)
    assert usuario["status"] == StatusUsuario.AGUARDANDO_APROVACAO.value


# ── Código de acesso do condomínio ───────────────────────────────────
def test_codigo_de_condominio_errado(cliente, cenario):
    r = cadastrar(cliente, cenario, codigo_condominio="XXXX-9999")
    assert r.status_code == 404
    assert "Confira com o síndico" in r.json()["detalhe"]


def test_o_codigo_de_condominio_nao_diferencia_maiusculas(cliente, cenario):
    r = cadastrar(cliente, cenario, codigo_condominio=cenario["cond"]["codigo_acesso"].lower())
    assert r.status_code == 201


# ── Login ────────────────────────────────────────────────────────────
def test_login_devolve_token(cliente, cenario):
    usuario = cadastrar_e_confirmar(cliente, cenario)
    aprovar(cliente, cenario, usuario["id"])

    r = cliente.post(
        "/api/v1/auth/login", json={"email": "joao@exemplo.com", "senha": "senhaforte123"}
    )
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["usuario"]["papel"] == "morador"
    assert corpo["access_token"]


def test_senha_errada_nao_loga(cliente, cenario):
    usuario = cadastrar_e_confirmar(cliente, cenario)
    aprovar(cliente, cenario, usuario["id"])

    r = cliente.post(
        "/api/v1/auth/login", json={"email": "joao@exemplo.com", "senha": "errada12345"}
    )
    assert r.status_code == 401


def test_email_inexistente_da_a_mesma_mensagem_da_senha_errada(cliente, cenario):
    """Não revela quais e-mails estão cadastrados."""
    usuario = cadastrar_e_confirmar(cliente, cenario)
    aprovar(cliente, cenario, usuario["id"])

    a = cliente.post(
        "/api/v1/auth/login", json={"email": "joao@exemplo.com", "senha": "errada12345"}
    )
    b = cliente.post(
        "/api/v1/auth/login", json={"email": "ninguem@exemplo.com", "senha": "errada12345"}
    )
    assert a.status_code == b.status_code == 401
    assert a.json()["detalhe"] == b.json()["detalhe"]


def test_sem_confirmar_o_codigo_nao_loga(cliente, cenario):
    cadastrar(cliente, cenario)
    r = cliente.post(
        "/api/v1/auth/login", json={"email": "joao@exemplo.com", "senha": "senhaforte123"}
    )
    assert r.status_code == 403
    assert "Confirme o código" in r.json()["detalhe"]


def test_sem_aprovacao_do_sindico_nao_loga(cliente, cenario):
    cadastrar_e_confirmar(cliente, cenario)
    r = cliente.post(
        "/api/v1/auth/login", json={"email": "joao@exemplo.com", "senha": "senhaforte123"}
    )
    assert r.status_code == 403
    assert "aguarda aprovação" in r.json()["detalhe"]


# ── Rota protegida ───────────────────────────────────────────────────
def test_rota_protegida_exige_token(cliente):
    assert cliente.get("/api/v1/auth/eu").status_code == 401
    assert cliente.get(
        "/api/v1/auth/eu", headers={"Authorization": "Bearer token-invalido"}
    ).status_code == 401


def test_rota_protegida_com_token_valido(cliente, cenario):
    r = cliente.get("/api/v1/auth/eu", headers=cab(cenario["sindico"]))
    assert r.status_code == 200
    assert r.json()["email"] == "sindico@exemplo.com"
    assert r.json()["papel"] == "sindico"


# ── Esqueci minha senha ──────────────────────────────────────────────
def test_recuperacao_de_senha_completa(cliente, cenario, db):
    from app.core.security import gerar_hash_codigo
    from app.models.enums import FinalidadeCodigo
    from app.models.usuario import CodigoVerificacao

    pedido = cliente.post(
        "/api/v1/auth/senha/recuperar", json={"email": "sindico@exemplo.com"}
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
            "email": "sindico@exemplo.com", "codigo": codigo,
            "nova_senha": "novasenha456", "confirmacao_senha": "novasenha456",
        },
    )
    assert troca.status_code == 200, troca.text

    assert cliente.post(
        "/api/v1/auth/login",
        json={"email": "sindico@exemplo.com", "senha": "senhaforte123"},
    ).status_code == 401
    assert cliente.post(
        "/api/v1/auth/login",
        json={"email": "sindico@exemplo.com", "senha": "novasenha456"},
    ).status_code == 200


def test_recuperacao_para_email_inexistente_nao_revela_nada(cliente):
    r = cliente.post("/api/v1/auth/senha/recuperar", json={"email": "ninguem@exemplo.com"})
    assert r.status_code == 200
    assert "Se o e-mail estiver cadastrado" in r.json()["detalhe"]


def test_confirmacao_divergente_e_recusada(cliente, cenario):
    r = cliente.post(
        "/api/v1/auth/senha/redefinir",
        json={
            "email": "sindico@exemplo.com", "codigo": "123456",
            "nova_senha": "novasenha456", "confirmacao_senha": "outrasenha789",
        },
    )
    assert r.status_code == 422
    assert "confirmação não confere" in r.text


def test_troca_de_senha_logado(cliente, cenario):
    errada = cliente.post(
        "/api/v1/auth/senha/trocar",
        json={"senha_atual": "naoehessa1", "nova_senha": "novasenha456"},
        headers=cab(cenario["sindico"]),
    )
    assert errada.status_code == 400

    certa = cliente.post(
        "/api/v1/auth/senha/trocar",
        json={"senha_atual": "senhaforte123", "nova_senha": "novasenha456"},
        headers=cab(cenario["sindico"]),
    )
    assert certa.status_code == 200
    assert cliente.post(
        "/api/v1/auth/login",
        json={"email": "sindico@exemplo.com", "senha": "novasenha456"},
    ).status_code == 200


def test_saude(cliente):
    r = cliente.get("/api/v1/saude")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

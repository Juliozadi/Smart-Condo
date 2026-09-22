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


def test_perfil_traz_cpf_e_nascimento_mas_a_listagem_nao(cliente, cenario):
    """O usuário vê o próprio CPF; a listagem do síndico não expõe o dos outros."""
    meu = cliente.get("/api/v1/auth/eu", headers=cab(cenario["sindico"])).json()
    assert "cpf" in meu
    assert "data_nascimento" in meu

    lista = cliente.get("/api/v1/usuarios", headers=cab(cenario["sindico"])).json()
    assert lista, "o síndico precisa enxergar alguém na listagem"
    assert all("cpf" not in u for u in lista)


def test_usuario_atualiza_o_proprio_perfil(cliente, cenario):
    """A tela de perfil grava nome, telefone e data de nascimento."""
    r = cliente.patch(
        "/api/v1/usuarios/eu",
        json={"nome": "Roberto do Nascimento", "telefone": "(67) 98888-7777",
              "data_nascimento": "1990-04-15"},
        headers=cab(cenario["sindico"]),
    )
    assert r.status_code == 200, r.text
    assert r.json()["nome"] == "Roberto do Nascimento"
    assert r.json()["data_nascimento"] == "1990-04-15"

    de_novo = cliente.get("/api/v1/auth/eu", headers=cab(cenario["sindico"])).json()
    assert de_novo["telefone"] == "67988887777"
    assert de_novo["data_nascimento"] == "1990-04-15"


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


# ── Limite de tentativas de login ────────────────────────────────────
def test_senha_errada_repetida_tranca_a_conta(cliente, cenario):
    """Sem limite, adivinhar a senha é só questão de tempo."""
    from app.core.config import settings

    corpo = {"email": "sindico@exemplo.com", "senha": "senha-errada"}
    for _ in range(settings.MAX_TENTATIVAS_LOGIN):
        r = cliente.post("/api/v1/auth/login", json=corpo)
        assert r.status_code == 401

    # A seguinte já bate na trava, e a mensagem diz quanto falta.
    r = cliente.post("/api/v1/auth/login", json=corpo)
    assert r.status_code == 429
    assert "minuto" in r.json()["detalhe"]


def test_conta_trancada_recusa_ate_a_senha_certa(cliente, cenario):
    """Enquanto está trancada, nem a senha correta entra."""
    from app.core.config import settings

    for _ in range(settings.MAX_TENTATIVAS_LOGIN):
        cliente.post(
            "/api/v1/auth/login",
            json={"email": "sindico@exemplo.com", "senha": "senha-errada"},
        )
    r = cliente.post(
        "/api/v1/auth/login",
        json={"email": "sindico@exemplo.com", "senha": "senhaforte123"},
    )
    assert r.status_code == 429


def test_acertar_a_senha_zera_o_contador(cliente, db, cenario):
    """Quem erra e depois acerta não fica com tentativa acumulada."""
    from app.models.usuario import Usuario
    from sqlalchemy import select

    for _ in range(2):
        cliente.post(
            "/api/v1/auth/login",
            json={"email": "sindico@exemplo.com", "senha": "senha-errada"},
        )
    db.expire_all()
    u = db.scalar(select(Usuario).where(Usuario.email == "sindico@exemplo.com"))
    assert u.tentativas_login == 2

    r = cliente.post(
        "/api/v1/auth/login",
        json={"email": "sindico@exemplo.com", "senha": "senhaforte123"},
    )
    assert r.status_code == 200

    db.expire_all()
    u = db.scalar(select(Usuario).where(Usuario.email == "sindico@exemplo.com"))
    assert u.tentativas_login == 0
    assert u.bloqueado_ate is None


def test_bloqueio_vencido_deixa_entrar_de_novo(cliente, db, cenario):
    """O bloqueio é temporário: vencido, a senha certa volta a valer."""
    from datetime import datetime, timedelta, timezone

    from app.models.usuario import Usuario
    from sqlalchemy import select

    u = db.scalar(select(Usuario).where(Usuario.email == "sindico@exemplo.com"))
    u.bloqueado_ate = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()

    r = cliente.post(
        "/api/v1/auth/login",
        json={"email": "sindico@exemplo.com", "senha": "senhaforte123"},
    )
    assert r.status_code == 200

    db.expire_all()
    u = db.scalar(select(Usuario).where(Usuario.email == "sindico@exemplo.com"))
    assert u.bloqueado_ate is None


def test_email_inexistente_nao_tranca_nada(cliente, cenario):
    """Sem conta não há o que contar — e a resposta continua 401."""
    from app.core.config import settings

    for _ in range(settings.MAX_TENTATIVAS_LOGIN + 2):
        r = cliente.post(
            "/api/v1/auth/login",
            json={"email": "ninguem@exemplo.com", "senha": "qualquer-coisa"},
        )
        assert r.status_code == 401


# ── Força bruta no código de verificação ─────────────────────────────
def test_codigo_de_recuperacao_trava_depois_de_cinco_erros(cliente, cenario):
    """O contador precisa sobreviver à requisição que falhou.

    O incremento acontece e logo depois a rota levanta exceção. Sem um
    commit antes do raise, a sessão é desfeita, a contagem volta a zero
    e o limite nunca fecha — os seis dígitos ficariam abertos à força
    bruta, que é tomada de conta.
    """
    from app.services.auth import MAX_TENTATIVAS_CODIGO

    cliente.post("/api/v1/auth/senha/recuperar", json={"email": "sindico@exemplo.com"})

    for _ in range(MAX_TENTATIVAS_CODIGO):
        r = cliente.post(
            "/api/v1/auth/senha/redefinir",
            json={"email": "sindico@exemplo.com", "codigo": "000000",
                  "nova_senha": "outrasenha123", "confirmacao_senha": "outrasenha123"},
        )
        assert r.status_code == 400

    r = cliente.post(
        "/api/v1/auth/senha/redefinir",
        json={"email": "sindico@exemplo.com", "codigo": "000000",
              "nova_senha": "outrasenha123", "confirmacao_senha": "outrasenha123"},
    )
    assert r.status_code == 429


def test_tentativa_errada_fica_gravada(cliente, db, cenario):
    """A contagem precisa estar no banco, não só na sessão da requisição."""
    from app.models.usuario import CodigoVerificacao
    from sqlalchemy import select

    cliente.post("/api/v1/auth/senha/recuperar", json={"email": "sindico@exemplo.com"})
    cliente.post(
        "/api/v1/auth/senha/redefinir",
        json={"email": "sindico@exemplo.com", "codigo": "000000",
              "nova_senha": "outrasenha123", "confirmacao_senha": "outrasenha123"},
    )

    db.expire_all()
    registro = db.scalar(
        select(CodigoVerificacao).order_by(CodigoVerificacao.id.desc())
    )
    assert registro.tentativas == 1


def test_codigo_expirado_e_queimado(cliente, db, cenario):
    """Código vencido não pode continuar pendente para novas tentativas."""
    from datetime import datetime, timedelta, timezone

    from app.models.usuario import CodigoVerificacao
    from sqlalchemy import select

    cliente.post("/api/v1/auth/senha/recuperar", json={"email": "sindico@exemplo.com"})
    registro = db.scalar(select(CodigoVerificacao).order_by(CodigoVerificacao.id.desc()))
    registro.expira_em = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()

    r = cliente.post(
        "/api/v1/auth/senha/redefinir",
        json={"email": "sindico@exemplo.com", "codigo": "000000",
              "nova_senha": "outrasenha123", "confirmacao_senha": "outrasenha123"},
    )
    assert r.status_code == 400

    db.expire_all()
    registro = db.scalar(select(CodigoVerificacao).order_by(CodigoVerificacao.id.desc()))
    assert registro.consumido_em is not None

"""Testes do cadastro do condomínio, da aprovação e das permissões.

Documentação, seções 8, 9 (casos de uso "Cadastro do condomínio" e
"Permissão do Porteiro") e 11.2.
"""
from __future__ import annotations

import pytest

from tests.fixtures import (
    CPFS, cab, cadastrar_morador, cadastrar_porteiro, cadastrar_sindico, criar_condominio,
)


@pytest.fixture
def sindico(cliente):
    return cadastrar_sindico(cliente)


@pytest.fixture
def condominio(cliente, sindico):
    return criar_condominio(cliente, sindico)


# ── Cadastro do condomínio (seção 9) ─────────────────────────────────
def test_sindico_cadastra_condominio(cliente, sindico):
    r = cliente.post(
        "/api/v1/condominios",
        json={
            "nome": "Residencial das Palmeiras", "cnpj": "11.222.333/0001-81",
            "cep": "79000-000", "logradouro": "Rua das Flores", "numero": "100",
            "bairro": "Centro", "cidade": "Campo Grande", "uf": "MS",
        },
        headers=cab(sindico),
    )
    assert r.status_code == 201, r.text
    assert r.json()["cnpj"] == "11222333000181"
    assert r.json()["uf"] == "MS"

    # O síndico passa a estar vinculado ao condomínio que criou.
    eu = cliente.get("/api/v1/auth/eu", headers=cab(sindico))
    assert eu.json()["condominio_id"] == r.json()["id"]


def test_cnpj_invalido_e_recusado(cliente, sindico):
    r = cliente.post(
        "/api/v1/condominios",
        json={
            "nome": "Teste", "cnpj": "11.222.333/0001-99", "cep": "79000-000",
            "logradouro": "Rua X", "numero": "1", "bairro": "Centro",
            "cidade": "Campo Grande", "uf": "MS",
        },
        headers=cab(sindico),
    )
    assert r.status_code == 422
    assert "CNPJ inválido" in r.text


def test_um_sindico_nao_cadastra_dois_condominios(cliente, sindico, condominio):
    r = cliente.post(
        "/api/v1/condominios",
        json={
            "nome": "Outro", "cnpj": "45.997.418/0001-53", "cep": "79000-000",
            "logradouro": "Rua Y", "numero": "2", "bairro": "Centro",
            "cidade": "Campo Grande", "uf": "MS",
        },
        headers=cab(sindico),
    )
    assert r.status_code == 409


def test_morador_nao_cadastra_condominio(cliente, sindico, condominio):
    _, tok = cadastrar_morador(cliente, sindico, condominio["id"], cpf=CPFS[1])
    r = cliente.post(
        "/api/v1/condominios",
        json={
            "nome": "Invasao", "cnpj": "45.997.418/0001-53", "cep": "79000-000",
            "logradouro": "Rua Z", "numero": "3", "bairro": "Centro",
            "cidade": "Campo Grande", "uf": "MS",
        },
        headers=cab(tok),
    )
    assert r.status_code == 403


def test_lista_publica_de_condominios_nao_expoe_cnpj(cliente, condominio):
    """Rota aberta, usada na tela de cadastro do morador."""
    r = cliente.get("/api/v1/condominios")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert set(r.json()[0]) == {"id", "nome", "cidade", "uf"}
    assert "cnpj" not in r.text


# ── Aprovação do cadastro (telas "aguardando aprovação") ─────────────
def test_morador_fica_aguardando_aprovacao(cliente, sindico, condominio):
    usuario_id, _ = cadastrar_morador(
        cliente, sindico, condominio["id"], cpf=CPFS[1], aprovar=False
    )
    lista = cliente.get(
        "/api/v1/usuarios", params={"status": "aguardando_aprovacao"}, headers=cab(sindico)
    )
    assert lista.status_code == 200
    assert [u["id"] for u in lista.json()] == [usuario_id]


def test_morador_nao_aprovado_nao_loga(cliente, sindico, condominio):
    cadastrar_morador(
        cliente, sindico, condominio["id"], email="pendente@exemplo.com",
        cpf=CPFS[1], aprovar=False,
    )
    r = cliente.post(
        "/api/v1/auth/login",
        json={"email": "pendente@exemplo.com", "senha": "senhaforte123"},
    )
    assert r.status_code == 403
    assert "aguarda aprovação" in r.json()["detalhe"]


def test_morador_recusado_nao_loga(cliente, sindico, condominio):
    usuario_id, _ = cadastrar_morador(
        cliente, sindico, condominio["id"], email="recusado@exemplo.com",
        cpf=CPFS[1], aprovar=False,
    )
    rec = cliente.post(
        f"/api/v1/usuarios/{usuario_id}/aprovacao",
        json={"aprovado": False, "motivo": "Sem vínculo"},
        headers=cab(sindico),
    )
    assert rec.status_code == 200
    assert rec.json()["status"] == "recusado"

    r = cliente.post(
        "/api/v1/auth/login",
        json={"email": "recusado@exemplo.com", "senha": "senhaforte123"},
    )
    assert r.status_code == 403


def test_sindico_nao_avalia_o_proprio_cadastro(cliente, sindico, condominio):
    eu = cliente.get("/api/v1/auth/eu", headers=cab(sindico)).json()
    r = cliente.post(
        f"/api/v1/usuarios/{eu['id']}/aprovacao", json={"aprovado": True}, headers=cab(sindico)
    )
    assert r.status_code == 400


def test_sindico_nao_ve_usuario_de_outro_condominio(cliente, sindico, condominio):
    """Um síndico de outro condomínio não enxerga nem aprova alguém de fora."""
    usuario_id, _ = cadastrar_morador(
        cliente, sindico, condominio["id"], cpf=CPFS[1], aprovar=False
    )

    outro = cadastrar_sindico(cliente, email="outro@exemplo.com", cpf=CPFS[4])
    cliente.post(
        "/api/v1/condominios",
        json={
            "nome": "Outro Condominio", "cnpj": "45.997.418/0001-53", "cep": "79000-000",
            "logradouro": "Rua Y", "numero": "2", "bairro": "Centro",
            "cidade": "Campo Grande", "uf": "MS",
        },
        headers=cab(outro),
    )

    # O outro síndico enxerga o próprio usuário, mas nunca o morador de fora.
    vistos = cliente.get("/api/v1/usuarios", headers=cab(outro)).json()
    assert usuario_id not in [u["id"] for u in vistos]
    assert {u["email"] for u in vistos} == {"outro@exemplo.com"}

    r = cliente.post(
        f"/api/v1/usuarios/{usuario_id}/aprovacao", json={"aprovado": True}, headers=cab(outro)
    )
    assert r.status_code == 404


# ── Permissões do porteiro (seção 9) ─────────────────────────────────
def test_sistema_mostra_as_acoes_do_porteiro(cliente, sindico):
    """"O sistema mostra as possibilidades de ações do porteiro" (seção 9)."""
    r = cliente.get("/api/v1/usuarios/porteiros/acoes", headers=cab(sindico))
    assert r.status_code == 200
    chaves = {a["chave"] for a in r.json()}
    assert chaves == {
        "registrar_visitantes", "registrar_encomendas", "registrar_veiculos",
        "registrar_ocorrencias", "acessar_financeiro",
    }


def test_porteiro_nasce_com_as_permissoes_escolhidas(cliente, sindico, condominio):
    """Seção 11.2: o cadastro termina com as permissões de uso no sistema."""
    porteiro_id, _ = cadastrar_porteiro(
        cliente, sindico, condominio["id"], cpf=CPFS[2],
        permissoes={
            "registrar_visitantes": True, "registrar_encomendas": False,
            "registrar_veiculos": False, "registrar_ocorrencias": True,
            "acessar_financeiro": False,
        },
    )
    r = cliente.get(
        f"/api/v1/usuarios/porteiros/{porteiro_id}/permissoes", headers=cab(sindico)
    )
    assert r.status_code == 200
    p = r.json()
    assert p["registrar_visitantes"] is True
    assert p["registrar_encomendas"] is False
    assert p["acessar_financeiro"] is False


def test_o_financeiro_nao_vem_liberado_por_padrao(cliente, sindico, condominio):
    porteiro_id, _ = cadastrar_porteiro(cliente, sindico, condominio["id"], cpf=CPFS[2])
    r = cliente.get(
        f"/api/v1/usuarios/porteiros/{porteiro_id}/permissoes", headers=cab(sindico)
    )
    assert r.json()["acessar_financeiro"] is False


def test_sindico_altera_as_permissoes(cliente, sindico, condominio):
    """"O síndico escolhe quais estarão disponíveis para o porteiro" (seção 9)."""
    porteiro_id, _ = cadastrar_porteiro(cliente, sindico, condominio["id"], cpf=CPFS[2])

    r = cliente.put(
        f"/api/v1/usuarios/porteiros/{porteiro_id}/permissoes",
        json={
            "registrar_visitantes": False, "registrar_encomendas": True,
            "registrar_veiculos": True, "registrar_ocorrencias": False,
            "acessar_financeiro": True,
        },
        headers=cab(sindico),
    )
    assert r.status_code == 200
    assert r.json()["registrar_visitantes"] is False
    assert r.json()["acessar_financeiro"] is True


def test_porteiro_nao_mexe_nas_proprias_permissoes(cliente, sindico, condominio):
    porteiro_id, tok_porteiro = cadastrar_porteiro(
        cliente, sindico, condominio["id"], cpf=CPFS[2]
    )
    r = cliente.put(
        f"/api/v1/usuarios/porteiros/{porteiro_id}/permissoes",
        json={
            "registrar_visitantes": True, "registrar_encomendas": True,
            "registrar_veiculos": True, "registrar_ocorrencias": True,
            "acessar_financeiro": True,
        },
        headers=cab(tok_porteiro),
    )
    assert r.status_code == 403


def test_so_o_sindico_cadastra_porteiro(cliente, sindico, condominio):
    _, tok_morador = cadastrar_morador(cliente, sindico, condominio["id"], cpf=CPFS[1])
    r = cliente.post(
        "/api/v1/usuarios/porteiros",
        json={
            "nome": "Falso", "email": "falso@exemplo.com", "cpf": CPFS[5],
            "telefone": "(67) 99999-0009", "senha": "senhaforte123",
            "condominio_id": condominio["id"],
        },
        headers=cab(tok_morador),
    )
    assert r.status_code == 403


def test_sindico_nao_cadastra_porteiro_em_outro_condominio(cliente, sindico, condominio):
    outro = cadastrar_sindico(cliente, email="outro@exemplo.com", cpf=CPFS[4])
    r = cliente.post(
        "/api/v1/usuarios/porteiros",
        json={
            "nome": "Carlos", "email": "carlos@exemplo.com", "cpf": CPFS[2],
            "telefone": "(67) 99999-0003", "senha": "senhaforte123",
            "condominio_id": condominio["id"],
        },
        headers=cab(outro),
    )
    assert r.status_code == 403


# ── Unidades e perfil ────────────────────────────────────────────────
def test_unidade_e_criada_no_cadastro_do_morador(cliente, sindico, condominio):
    cadastrar_morador(cliente, sindico, condominio["id"], cpf=CPFS[1], unidade="204")
    r = cliente.get("/api/v1/condominios/meu/unidades", headers=cab(sindico))
    assert r.status_code == 200
    assert [u["numero"] for u in r.json()] == ["204"]


def test_dois_moradores_na_mesma_unidade_nao_duplicam(cliente, sindico, condominio):
    cadastrar_morador(
        cliente, sindico, condominio["id"], email="a@exemplo.com", cpf=CPFS[1], unidade="204"
    )
    cadastrar_morador(
        cliente, sindico, condominio["id"], email="b@exemplo.com", cpf=CPFS[3], unidade="204"
    )
    r = cliente.get("/api/v1/condominios/meu/unidades", headers=cab(sindico))
    assert len(r.json()) == 1


def test_morador_atualiza_o_proprio_perfil(cliente, sindico, condominio):
    _, tok = cadastrar_morador(cliente, sindico, condominio["id"], cpf=CPFS[1])
    r = cliente.patch(
        "/api/v1/usuarios/eu",
        json={"nome": "João da Silva", "telefone": "(67) 98888-7777"},
        headers=cab(tok),
    )
    assert r.status_code == 200
    assert r.json()["nome"] == "João da Silva"
    assert r.json()["telefone"] == "67988887777"


def test_usuario_inativado_nao_loga(cliente, sindico, condominio):
    usuario_id, _ = cadastrar_morador(
        cliente, sindico, condominio["id"], email="sai@exemplo.com", cpf=CPFS[1]
    )
    assert cliente.delete(
        f"/api/v1/usuarios/{usuario_id}", headers=cab(sindico)
    ).status_code == 200

    r = cliente.post(
        "/api/v1/auth/login", json={"email": "sai@exemplo.com", "senha": "senhaforte123"}
    )
    assert r.status_code == 403

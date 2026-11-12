"""Uma pessoa, vários perfis.

Situações reais:
  - o síndico mora no condomínio: paga a taxa, reserva o salão e vota
    como qualquer morador — e o CPF só podia ter um cadastro;
  - o morador é eleito síndico: com outro e-mail, teria duas contas e
    duas senhas;
  - o proprietário tem mais de um apartamento: paga e vota por cada um,
    mas não deve ver as visitas e as encomendas do inquilino do que
    alugou.

A pessoa tem um login só (o cadastro principal) e troca de perfil no
topo da tela; cada perfil é um cadastro vinculado, sem senha própria.
"""
from __future__ import annotations

import pytest

from app.services import notificacao
from tests.fixtures import (
    CPFS, cab, cadastrar_morador, cadastrar_porteiro, montar_condominio, token,
)
from tests.test_portaria import registrar_visitante

PERFIS = "/api/v1/auth/perfis"
APTOS = "/api/v1/usuarios/eu/apartamentos"
SENHA = "senhaforte123"


@pytest.fixture
def cenario(cliente, db):
    base = montar_condominio(cliente, db)
    tok_sindico, cond = base["sindico"], base["cond"]
    ana_id, tok_ana = cadastrar_morador(cliente, tok_sindico, cond, email="ana@exemplo.com",
                                        cpf=CPFS[1], unidade="204")
    _, tok_bruno = cadastrar_morador(cliente, tok_sindico, cond, email="bruno@exemplo.com",
                                     cpf=CPFS[3], unidade="301")
    _, tok_porteiro = cadastrar_porteiro(cliente, tok_sindico, cond, cpf=CPFS[2])
    for numero in ("101", "410"):
        r = cliente.post("/api/v1/condominios/meu/unidades", json={"numero": numero},
                         headers=cab(tok_sindico))
        assert r.status_code == 201, r.text
    unidades = {u["numero"]: u["id"] for u in cliente.get(
        "/api/v1/condominios/meu/unidades", headers=cab(tok_sindico)).json()}
    return {**base, "ana": tok_ana, "ana_id": ana_id, "bruno": tok_bruno,
            "porteiro": tok_porteiro, "u": unidades}


def vincular(cliente, tok, unidade_id, **extra):
    corpo = {"unidade_id": unidade_id, "tipo_ocupacao": "proprietario", "reside": True}
    corpo.update(extra)
    return cliente.post(APTOS, json=corpo, headers=cab(tok))


def trocar(cliente, tok, usuario_id):
    return cliente.post(f"{PERFIS}/{usuario_id}", headers=cab(tok))


def perfis(cliente, tok):
    return cliente.get(PERFIS, headers=cab(tok)).json()


def eu(cliente, tok):
    return cliente.get("/api/v1/auth/eu", headers=cab(tok)).json()


# ── O síndico que mora no condomínio ─────────────────────────────────

def test_sindico_que_mora_no_condominio(cliente, cenario):
    r = vincular(cliente, cenario["sindico"], cenario["u"]["101"])
    assert r.status_code == 201, r.text
    perfil = r.json()
    # O síndico é quem aprova moradores: o perfil dele já nasce ativo.
    assert perfil["papel"] == "morador" and perfil["unidade"] == "101"
    assert perfil["status"] == "ativo"

    lista = perfis(cliente, cenario["sindico"])
    assert [(p["papel"], p["atual"]) for p in lista] == [("sindico", True), ("morador", False)]

    r = trocar(cliente, cenario["sindico"], perfil["usuario_id"])
    assert r.status_code == 200, r.text
    tok_casa = r.json()["access_token"]
    dados = eu(cliente, tok_casa)
    assert dados["papel"] == "morador" and dados["unidade"]["numero"] == "101"
    assert dados["possui_outros_perfis"] is True
    # Como morador, faz o que o morador faz — e só isso.
    assert cliente.get("/api/v1/espacos/reservas/minhas", headers=cab(tok_casa)).status_code == 200
    assert cliente.get("/api/v1/usuarios", headers=cab(tok_casa)).status_code == 403

    # Volta a ser síndico sem digitar a senha de novo.
    r = trocar(cliente, tok_casa, lista[0]["usuario_id"])
    assert r.status_code == 200
    assert eu(cliente, r.json()["access_token"])["papel"] == "sindico"
    # O login continua sendo o do síndico.
    assert eu(cliente, token(cliente, "sindico@exemplo.com", SENHA))["papel"] == "sindico"


def test_trocar_a_senha_vale_para_todos_os_perfis(cliente, cenario):
    perfil = vincular(cliente, cenario["sindico"], cenario["u"]["101"]).json()
    tok_casa = trocar(cliente, cenario["sindico"], perfil["usuario_id"]).json()["access_token"]
    r = cliente.post("/api/v1/auth/senha/trocar",
                     json={"senha_atual": SENHA, "nova_senha": "outrasenha456"},
                     headers=cab(tok_casa))
    assert r.status_code == 200, r.text
    assert eu(cliente, r.json()["access_token"])["papel"] == "morador"
    # As sessões abertas, em qualquer perfil, caem.
    assert cliente.get("/api/v1/auth/eu", headers=cab(cenario["sindico"])).status_code == 401
    assert cliente.get("/api/v1/auth/eu", headers=cab(tok_casa)).status_code == 401
    assert token(cliente, "sindico@exemplo.com", "outrasenha456")


def test_ex_sindico_continua_morando(cliente, cenario):
    perfil = vincular(cliente, cenario["sindico"], cenario["u"]["101"]).json()
    r = cliente.delete(f"/api/v1/admin/usuarios/{cenario['sindico_id']}",
                       headers=cab(cenario["admin"]))
    assert r.status_code == 200, r.text
    # O mandato acabou, a casa não: entra com o mesmo e-mail e senha.
    tok = token(cliente, "sindico@exemplo.com", SENHA)
    dados = eu(cliente, tok)
    assert dados["papel"] == "morador" and dados["id"] == perfil["usuario_id"]
    assert [p["papel"] for p in perfis(cliente, tok)] == ["morador"]


def test_morador_eleito_sindico(cliente, cenario):
    r = cliente.delete(f"/api/v1/admin/usuarios/{cenario['sindico_id']}",
                       headers=cab(cenario["admin"]))
    assert r.status_code == 200
    # O administrador cadastra a síndica com o e-mail e o CPF que ela já usa.
    r = cliente.post(f"/api/v1/admin/condominios/{cenario['cond']['id']}/usuarios", json={
        "nome": "Ana Beatriz", "email": "ana@exemplo.com", "cpf": CPFS[1],
        "telefone": "(67) 99999-0002", "senha": "outrasenha789", "papel": "sindico",
    }, headers=cab(cenario["admin"]))
    assert r.status_code == 201, r.text
    # Ela entra com a senha de sempre, como moradora, e troca para síndica.
    tok = token(cliente, "ana@exemplo.com", SENHA)
    lista = perfis(cliente, tok)
    assert sorted(p["papel"] for p in lista) == ["morador", "sindico"]
    sindica = next(p for p in lista if p["papel"] == "sindico")
    tok_sindica = trocar(cliente, tok, sindica["usuario_id"]).json()["access_token"]
    assert cliente.get("/api/v1/usuarios", headers=cab(tok_sindica)).status_code == 200
    # A senha que o administrador digitou não abre nada: a conta é a dela.
    r = cliente.post("/api/v1/auth/login", json={"email": "ana@exemplo.com",
                                                 "senha": "outrasenha789"})
    assert r.status_code == 401


def test_email_de_um_e_cpf_de_outro_continua_recusado(cliente, cenario):
    cliente.delete(f"/api/v1/admin/usuarios/{cenario['sindico_id']}",
                   headers=cab(cenario["admin"]))
    r = cliente.post(f"/api/v1/admin/condominios/{cenario['cond']['id']}/usuarios", json={
        "nome": "Ana Beatriz", "email": "ana@exemplo.com", "cpf": CPFS[3],
        "telefone": "(67) 99999-0002", "senha": "outrasenha789", "papel": "sindico",
    }, headers=cab(cenario["admin"]))
    assert r.status_code == 409


# ── O proprietário de mais de um apartamento ─────────────────────────

def test_proprietario_de_outro_apartamento(cliente, cenario, monkeypatch):
    avisos = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: avisos.append(destino))
    r = vincular(cliente, cenario["ana"], cenario["u"]["410"], reside=False)
    assert r.status_code == 201, r.text
    pedido = r.json()
    # Dizer que é dono de um apartamento precisa do aval do síndico.
    assert pedido["status"] == "aguardando_aprovacao"
    assert avisos == ["sindico@exemplo.com"]
    assert trocar(cliente, cenario["ana"], pedido["usuario_id"]).status_code == 409

    r = cliente.post(f"/api/v1/usuarios/{pedido['usuario_id']}/aprovacao",
                     json={"aprovado": True}, headers=cab(cenario["sindico"]))
    assert r.status_code == 200, r.text
    assert avisos[-1] == "ana@exemplo.com"

    tok_410 = trocar(cliente, cenario["ana"], pedido["usuario_id"]).json()["access_token"]
    dados = eu(cliente, tok_410)
    assert dados["unidade"]["numero"] == "410" and dados["reside"] is False
    # O que é do proprietário: cobranças, prestação de contas, assembleias.
    for url in ("/api/v1/financeiro/cobrancas", "/api/v1/assembleias", "/api/v1/comunicados"):
        assert cliente.get(url, headers=cab(tok_410)).status_code == 200, url
    # O que é de quem mora lá, não.
    for url in ("/api/v1/portaria/visitantes", "/api/v1/portaria/encomendas",
                "/api/v1/portaria/autorizacoes", "/api/v1/espacos/reservas/minhas",
                "/api/v1/veiculos/cadastrados", "/api/v1/mudancas"):
        r = cliente.get(url, headers=cab(tok_410))
        assert r.status_code == 403, (url, r.text)
        assert "não mora" in r.json()["detalhe"]


def test_visita_do_apartamento_alugado_nao_vai_para_o_dono(cliente, cenario, monkeypatch):
    pedido = vincular(cliente, cenario["ana"], cenario["u"]["410"], reside=False).json()
    cliente.post(f"/api/v1/usuarios/{pedido['usuario_id']}/aprovacao",
                 json={"aprovado": True}, headers=cab(cenario["sindico"]))
    avisos = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: avisos.append(destino))
    r = registrar_visitante(cliente, cenario["porteiro"], cenario["u"]["410"])
    assert r.status_code == 201, r.text
    assert "ana@exemplo.com" not in avisos


def test_quem_mora_no_outro_apartamento_tem_tudo(cliente, cenario):
    """O dono que mora nos dois (cobertura e apartamento do filho, por
    exemplo) usa a portaria nos dois."""
    pedido = vincular(cliente, cenario["ana"], cenario["u"]["410"], reside=True).json()
    cliente.post(f"/api/v1/usuarios/{pedido['usuario_id']}/aprovacao",
                 json={"aprovado": True}, headers=cab(cenario["sindico"]))
    tok_410 = trocar(cliente, cenario["ana"], pedido["usuario_id"]).json()["access_token"]
    assert cliente.get("/api/v1/portaria/encomendas", headers=cab(tok_410)).status_code == 200


def test_vinculos_que_nao_fazem_sentido(cliente, cenario):
    # O próprio apartamento.
    assert vincular(cliente, cenario["ana"], cenario["u"]["204"]).status_code == 409
    # O mesmo duas vezes, mesmo aguardando aprovação.
    assert vincular(cliente, cenario["ana"], cenario["u"]["410"]).status_code == 201
    assert vincular(cliente, cenario["ana"], cenario["u"]["410"]).status_code == 409
    # Apartamento que não existe (ou de outro condomínio).
    assert vincular(cliente, cenario["ana"], 999999).status_code == 404
    # O porteiro de serviço não ganha apartamento por aqui sem o síndico.
    r = vincular(cliente, cenario["porteiro"], cenario["u"]["101"])
    assert r.status_code == 201 and r.json()["status"] == "aguardando_aprovacao"


def test_nao_troca_para_o_perfil_de_outra_pessoa(cliente, cenario):
    pedido = vincular(cliente, cenario["ana"], cenario["u"]["410"]).json()
    assert trocar(cliente, cenario["bruno"], pedido["usuario_id"]).status_code == 404
    assert trocar(cliente, cenario["bruno"], cenario["ana_id"]).status_code == 404
    assert trocar(cliente, cenario["bruno"], cenario["sindico_id"]).status_code == 404


def test_vendeu_o_apartamento(cliente, cenario):
    pedido = vincular(cliente, cenario["ana"], cenario["u"]["410"]).json()
    cliente.post(f"/api/v1/usuarios/{pedido['usuario_id']}/aprovacao",
                 json={"aprovado": True}, headers=cab(cenario["sindico"]))
    tok_410 = trocar(cliente, cenario["ana"], pedido["usuario_id"]).json()["access_token"]
    # Só a dona remove — e não o apartamento em que está o login.
    assert cliente.delete(f"{APTOS}/{pedido['usuario_id']}",
                          headers=cab(cenario["bruno"])).status_code == 404
    assert cliente.delete(f"{APTOS}/{cenario['ana_id']}",
                          headers=cab(cenario["ana"])).status_code == 409
    r = cliente.delete(f"{APTOS}/{pedido['usuario_id']}", headers=cab(cenario["ana"]))
    assert r.status_code == 200, r.text
    assert [p["usuario_id"] for p in perfis(cliente, cenario["ana"])] == [cenario["ana_id"]]
    assert cliente.get("/api/v1/auth/eu", headers=cab(tok_410)).status_code == 403


def test_saiu_do_apartamento_principal_e_ficou_com_o_outro(cliente, cenario):
    pedido = vincular(cliente, cenario["ana"], cenario["u"]["410"], reside=True).json()
    cliente.post(f"/api/v1/usuarios/{pedido['usuario_id']}/aprovacao",
                 json={"aprovado": True}, headers=cab(cenario["sindico"]))
    # A Ana se muda do 204 para o 410: o síndico inativa o cadastro do 204.
    r = cliente.delete(f"/api/v1/usuarios/{cenario['ana_id']}", headers=cab(cenario["sindico"]))
    assert r.status_code == 200, r.text
    tok = token(cliente, "ana@exemplo.com", SENHA)
    assert eu(cliente, tok)["unidade"]["numero"] == "410"


def test_email_e_cpf_continuam_de_uma_pessoa_so(cliente, cenario):
    vincular(cliente, cenario["sindico"], cenario["u"]["101"])
    r = cliente.post("/api/v1/auth/cadastro/morador", json={
        "nome": "Outra Pessoa", "email": "sindico@exemplo.com", "cpf": CPFS[5],
        "telefone": "(67) 99999-0009", "senha": SENHA,
        "codigo_condominio": cenario["cond"]["codigo_acesso"], "unidade_numero": "410",
        "tipo_ocupacao": "proprietario",
    })
    assert r.status_code == 409
    r = cliente.post("/api/v1/auth/cadastro/morador", json={
        "nome": "Outra Pessoa", "email": "outra@exemplo.com", "cpf": CPFS[0],
        "telefone": "(67) 99999-0009", "senha": SENHA,
        "codigo_condominio": cenario["cond"]["codigo_acesso"], "unidade_numero": "410",
        "tipo_ocupacao": "proprietario",
    })
    assert r.status_code == 409


def test_nome_e_telefone_sao_da_pessoa(cliente, cenario):
    perfil = vincular(cliente, cenario["sindico"], cenario["u"]["101"]).json()
    tok_casa = trocar(cliente, cenario["sindico"], perfil["usuario_id"]).json()["access_token"]
    r = cliente.patch("/api/v1/usuarios/eu", json={"telefone": "(67) 98888-7777"},
                      headers=cab(tok_casa))
    assert r.status_code == 200, r.text
    assert eu(cliente, cenario["sindico"])["telefone"] == eu(cliente, tok_casa)["telefone"]

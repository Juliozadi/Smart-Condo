"""Testes do painel do administrador.

O administrador opera a plataforma: cadastra condomínios e, dentro deles,
cria, edita e remove síndicos, porteiros e moradores.
"""
from __future__ import annotations

import pytest

from tests.fixtures import (
    CPFS, cab, criar_condominio_como_admin, criar_sindico, montar_condominio, token_admin,
)


@pytest.fixture
def admin(cliente, db):
    return token_admin(cliente, db)


@pytest.fixture
def cenario(cliente, db):
    return montar_condominio(cliente, db)


def criar_usuario(cliente, tok, condominio_id, papel, **extra):
    corpo = {
        "nome": "Fulano de Tal", "email": f"{papel}@exemplo.com", "cpf": CPFS[2],
        "telefone": "(67) 99999-1111", "senha": "senhaforte123", "papel": papel,
    }
    if papel == "morador":
        corpo.update({"unidade_numero": "204", "tipo_ocupacao": "proprietario"})
    corpo.update(extra)
    return cliente.post(
        f"/api/v1/admin/condominios/{condominio_id}/usuarios", json=corpo, headers=cab(tok)
    )


# ── Acesso ───────────────────────────────────────────────────────────
def test_somente_admin_entra_no_painel(cliente, cenario):
    for rota in ["/api/v1/admin/resumo", "/api/v1/admin/condominios", "/api/v1/admin/usuarios"]:
        assert cliente.get(rota, headers=cab(cenario["sindico"])).status_code == 403
        assert cliente.get(rota).status_code == 401


def test_admin_atravessa_condominios(cliente, db, admin):
    """Todo outro papel só enxerga o próprio condomínio; o admin vê todos."""
    a = criar_condominio_como_admin(cliente, admin, nome="Condo A", cnpj="11.222.333/0001-81")
    b = criar_condominio_como_admin(cliente, admin, nome="Condo B", cnpj="45.997.418/0001-53")

    r = cliente.get("/api/v1/admin/condominios", headers=cab(admin))
    assert r.status_code == 200
    assert {c["nome"] for c in r.json()} == {"Condo A", "Condo B"}
    assert {a["id"], b["id"]} == {c["id"] for c in r.json()}


# ── Condomínios ──────────────────────────────────────────────────────
def test_criar_editar_e_detalhar_condominio(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    assert cond["sindico_nome"] is None
    assert cond["total_unidades"] == 0

    r = cliente.put(
        f"/api/v1/admin/condominios/{cond['id']}",
        json={
            "nome": "Residencial Renomeado", "cnpj": "11.222.333/0001-81",
            "cep": "79000-111", "logradouro": "Rua Outra", "numero": "200",
            "bairro": "Centro", "cidade": "Dourados", "uf": "MS",
        },
        headers=cab(admin),
    )
    assert r.status_code == 200
    assert r.json()["nome"] == "Residencial Renomeado"
    assert r.json()["cidade"] == "Dourados"
    # Renomear não troca o código que os moradores já receberam.
    assert r.json()["codigo_acesso"] == cond["codigo_acesso"]

    d = cliente.get(f"/api/v1/admin/condominios/{cond['id']}", headers=cab(admin))
    assert d.json()["nome"] == "Residencial Renomeado"


def test_busca_de_condominio(cliente, admin):
    criar_condominio_como_admin(cliente, admin, nome="Palmeiras", cnpj="11.222.333/0001-81")
    criar_condominio_como_admin(cliente, admin, nome="Aurora", cnpj="45.997.418/0001-53")

    r = cliente.get("/api/v1/admin/condominios", params={"busca": "palm"}, headers=cab(admin))
    assert [c["nome"] for c in r.json()] == ["Palmeiras"]


def test_excluir_condominio_vazio(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    assert cliente.delete(
        f"/api/v1/admin/condominios/{cond['id']}", headers=cab(admin)
    ).status_code == 200
    assert cliente.get(
        f"/api/v1/admin/condominios/{cond['id']}", headers=cab(admin)
    ).status_code == 404


def test_nao_exclui_condominio_com_gente_dentro(cliente, db, admin):
    """Apagar levaria junto reservas, cobranças e portaria por cascata."""
    cond = criar_condominio_como_admin(cliente, admin)
    criar_sindico(cliente, admin, cond["id"], cpf=CPFS[0])

    r = cliente.delete(f"/api/v1/admin/condominios/{cond['id']}", headers=cab(admin))
    assert r.status_code == 409
    assert "usuário(s) ativo(s)" in r.json()["detalhe"]


def test_renovar_codigo_de_acesso(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    antigo = cond["codigo_acesso"]

    r = cliente.post(
        f"/api/v1/admin/condominios/{cond['id']}/codigo-acesso", headers=cab(admin)
    )
    assert r.status_code == 200
    assert r.json()["codigo_acesso"] != antigo
    assert cliente.get("/api/v1/condominios/por-codigo/" + antigo).status_code == 404


# ── Usuários ─────────────────────────────────────────────────────────
def test_admin_cria_os_tres_papeis(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)

    s = criar_usuario(cliente, admin, cond["id"], "sindico", cpf=CPFS[0])
    assert s.status_code == 201, s.text
    # Quem é criado por dentro do sistema já nasce ativo.
    assert s.json()["status"] == "ativo"
    assert s.json()["condominio_nome"] == "Residencial das Palmeiras"

    p = criar_usuario(cliente, admin, cond["id"], "porteiro", cpf=CPFS[2])
    assert p.status_code == 201
    assert p.json()["status"] == "ativo"

    m = criar_usuario(cliente, admin, cond["id"], "morador", cpf=CPFS[1])
    assert m.status_code == 201
    assert m.json()["unidade"] == "204"
    assert m.json()["tipo_ocupacao"] == "proprietario"


def test_usuario_criado_pelo_admin_ja_loga(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    criar_usuario(cliente, admin, cond["id"], "sindico", cpf=CPFS[0],
                  email="novo.sindico@exemplo.com")

    r = cliente.post(
        "/api/v1/auth/login",
        json={"email": "novo.sindico@exemplo.com", "senha": "senhaforte123"},
    )
    assert r.status_code == 200, r.text


def test_porteiro_criado_pelo_admin_nasce_com_permissoes(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    _, tok_sindico = criar_sindico(cliente, admin, cond["id"], cpf=CPFS[0])
    p = criar_usuario(cliente, admin, cond["id"], "porteiro", cpf=CPFS[2])

    r = cliente.get(
        f"/api/v1/usuarios/porteiros/{p.json()['id']}/permissoes", headers=cab(tok_sindico)
    )
    assert r.status_code == 200
    assert r.json()["registrar_visitantes"] is True
    assert r.json()["acessar_financeiro"] is False


def test_um_condominio_tem_um_sindico_ativo(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    assert criar_usuario(cliente, admin, cond["id"], "sindico", cpf=CPFS[0]).status_code == 201

    segundo = criar_usuario(
        cliente, admin, cond["id"], "sindico", cpf=CPFS[3], email="outro@exemplo.com"
    )
    assert segundo.status_code == 409
    assert "já tem um síndico ativo" in segundo.json()["detalhe"]


def test_morador_precisa_de_unidade(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    r = cliente.post(
        f"/api/v1/admin/condominios/{cond['id']}/usuarios",
        json={
            "nome": "Sem Unidade", "email": "sem@exemplo.com", "cpf": CPFS[1],
            "telefone": "(67) 99999-1111", "senha": "senhaforte123", "papel": "morador",
        },
        headers=cab(admin),
    )
    assert r.status_code == 400
    assert "unidade do morador" in r.json()["detalhe"]


def test_porteiro_nao_recebe_unidade(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    r = criar_usuario(
        cliente, admin, cond["id"], "porteiro", cpf=CPFS[2],
        unidade_numero="204", tipo_ocupacao="proprietario",
    )
    assert r.status_code == 400
    assert "só para morador" in r.json()["detalhe"]


def test_admin_nao_cria_outro_admin_por_aqui(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    r = criar_usuario(cliente, admin, cond["id"], "admin", cpf=CPFS[2])
    assert r.status_code == 400


def test_editar_usuario(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    m = criar_usuario(cliente, admin, cond["id"], "morador", cpf=CPFS[1]).json()

    r = cliente.put(
        f"/api/v1/admin/usuarios/{m['id']}",
        json={"nome": "Nome Corrigido", "unidade_numero": "301", "telefone": "(67) 98888-2222"},
        headers=cab(admin),
    )
    assert r.status_code == 200, r.text
    assert r.json()["nome"] == "Nome Corrigido"
    assert r.json()["unidade"] == "301"
    assert r.json()["telefone"] == "67988882222"


def test_trocar_a_senha_de_um_usuario(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    s = criar_usuario(cliente, admin, cond["id"], "sindico", cpf=CPFS[0],
                      email="troca@exemplo.com").json()

    r = cliente.put(
        f"/api/v1/admin/usuarios/{s['id']}",
        json={"senha": "outrasenha456"}, headers=cab(admin),
    )
    assert r.status_code == 200

    assert cliente.post(
        "/api/v1/auth/login", json={"email": "troca@exemplo.com", "senha": "senhaforte123"}
    ).status_code == 401
    assert cliente.post(
        "/api/v1/auth/login", json={"email": "troca@exemplo.com", "senha": "outrasenha456"}
    ).status_code == 200


def test_email_repetido_na_edicao(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    criar_usuario(cliente, admin, cond["id"], "sindico", cpf=CPFS[0], email="a@exemplo.com")
    b = criar_usuario(cliente, admin, cond["id"], "morador", cpf=CPFS[1],
                      email="b@exemplo.com").json()

    r = cliente.put(
        f"/api/v1/admin/usuarios/{b['id']}", json={"email": "a@exemplo.com"}, headers=cab(admin)
    )
    assert r.status_code == 409


def test_remover_usuario_inativa_e_impede_login(cliente, admin):
    """Inativa em vez de apagar: o histórico aponta para o usuário."""
    cond = criar_condominio_como_admin(cliente, admin)
    s = criar_usuario(cliente, admin, cond["id"], "sindico", cpf=CPFS[0],
                      email="sai@exemplo.com").json()

    assert cliente.delete(
        f"/api/v1/admin/usuarios/{s['id']}", headers=cab(admin)
    ).status_code == 200

    d = cliente.get(f"/api/v1/admin/usuarios/{s['id']}", headers=cab(admin))
    assert d.json()["status"] == "inativo"
    assert cliente.post(
        "/api/v1/auth/login", json={"email": "sai@exemplo.com", "senha": "senhaforte123"}
    ).status_code == 403


def test_remover_o_sindico_solta_o_condominio(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    sindico_id, _ = criar_sindico(cliente, admin, cond["id"], cpf=CPFS[0])

    antes = cliente.get(f"/api/v1/admin/condominios/{cond['id']}", headers=cab(admin))
    assert antes.json()["sindico_id"] == sindico_id

    cliente.delete(f"/api/v1/admin/usuarios/{sindico_id}", headers=cab(admin))
    depois = cliente.get(f"/api/v1/admin/condominios/{cond['id']}", headers=cab(admin))
    assert depois.json()["sindico_id"] is None
    assert depois.json()["sindico_nome"] is None


def test_admin_nao_remove_a_si_mesmo(cliente, db, admin):
    eu = cliente.get("/api/v1/auth/eu", headers=cab(admin)).json()
    r = cliente.delete(f"/api/v1/admin/usuarios/{eu['id']}", headers=cab(admin))
    assert r.status_code == 400


def test_filtros_da_lista_de_usuarios(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    criar_usuario(cliente, admin, cond["id"], "sindico", cpf=CPFS[0], email="s@exemplo.com")
    criar_usuario(cliente, admin, cond["id"], "porteiro", cpf=CPFS[2], email="p@exemplo.com")
    criar_usuario(cliente, admin, cond["id"], "morador", cpf=CPFS[1], email="m@exemplo.com")

    por_papel = cliente.get(
        "/api/v1/admin/usuarios", params={"papel": "porteiro"}, headers=cab(admin)
    )
    assert [u["email"] for u in por_papel.json()] == ["p@exemplo.com"]

    por_condominio = cliente.get(
        "/api/v1/admin/usuarios", params={"condominio_id": cond["id"]}, headers=cab(admin)
    )
    # O próprio administrador não pertence a condomínio nenhum.
    assert len(por_condominio.json()) == 3

    por_busca = cliente.get(
        "/api/v1/admin/usuarios", params={"busca": "m@exemplo"}, headers=cab(admin)
    )
    assert [u["email"] for u in por_busca.json()] == ["m@exemplo.com"]


def test_resumo_da_plataforma(cliente, db, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    criar_usuario(cliente, admin, cond["id"], "sindico", cpf=CPFS[0], email="s@exemplo.com")
    criar_usuario(cliente, admin, cond["id"], "porteiro", cpf=CPFS[2], email="p@exemplo.com")
    criar_usuario(cliente, admin, cond["id"], "morador", cpf=CPFS[1], email="m@exemplo.com")

    r = cliente.get("/api/v1/admin/resumo", headers=cab(admin))
    assert r.status_code == 200
    assert r.json() == {
        "condominios": 1, "sindicos": 1, "porteiros": 1,
        "moradores": 1, "aguardando_aprovacao": 0,
    }


# ── O síndico cadastra a equipe e os moradores ───────────────────────
def test_sindico_cadastra_porteiro_e_morador(cliente, cenario):
    for papel, cpf, email in [("porteiro", CPFS[2], "port@exemplo.com"),
                              ("morador", CPFS[1], "mor@exemplo.com")]:
        corpo = {
            "nome": "Novo " + papel, "email": email, "cpf": cpf,
            "telefone": "(67) 99999-2222", "senha": "senhaforte123", "papel": papel,
        }
        if papel == "morador":
            corpo.update({"unidade_numero": "305", "tipo_ocupacao": "inquilino"})

        r = cliente.post("/api/v1/usuarios", json=corpo, headers=cab(cenario["sindico"]))
        assert r.status_code == 201, r.text
        # Criado pelo síndico, entra ativo — sem código nem aprovação.
        assert r.json()["status"] == "ativo"
        assert cliente.post(
            "/api/v1/auth/login", json={"email": email, "senha": "senhaforte123"}
        ).status_code == 200


def test_sindico_nao_cadastra_outro_sindico(cliente, cenario):
    """Um síndico não nomeia o próprio substituto; isso é do administrador."""
    r = cliente.post(
        "/api/v1/usuarios",
        json={
            "nome": "Substituto", "email": "sub@exemplo.com", "cpf": CPFS[3],
            "telefone": "(67) 99999-3333", "senha": "senhaforte123", "papel": "sindico",
        },
        headers=cab(cenario["sindico"]),
    )
    assert r.status_code == 403
    assert "apenas porteiros e moradores" in r.json()["detalhe"]


def test_morador_nao_cadastra_ninguem(cliente, cenario):
    from tests.fixtures import cadastrar_morador

    _, tok = cadastrar_morador(cliente, cenario["sindico"], cenario["cond"], cpf=CPFS[1])
    r = cliente.post(
        "/api/v1/usuarios",
        json={
            "nome": "Alguem", "email": "alguem@exemplo.com", "cpf": CPFS[3],
            "telefone": "(67) 99999-4444", "senha": "senhaforte123", "papel": "morador",
            "unidade_numero": "999", "tipo_ocupacao": "inquilino",
        },
        headers=cab(tok),
    )
    assert r.status_code == 403


def test_sindico_edita_morador_do_proprio_condominio(cliente, cenario):
    from tests.fixtures import cadastrar_morador

    morador_id, _ = cadastrar_morador(
        cliente, cenario["sindico"], cenario["cond"], cpf=CPFS[1], unidade="204"
    )
    r = cliente.put(
        f"/api/v1/usuarios/{morador_id}",
        json={"unidade_numero": "402"},
        headers=cab(cenario["sindico"]),
    )
    assert r.status_code == 200
    assert r.json()["unidade"] == "402"


def test_sindico_nao_edita_a_si_mesmo_por_essa_rota(cliente, cenario):
    r = cliente.put(
        f"/api/v1/usuarios/{cenario['sindico_id']}",
        json={"nome": "Eu Mesmo"},
        headers=cab(cenario["sindico"]),
    )
    assert r.status_code == 403

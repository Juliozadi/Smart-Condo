"""O que o síndico faz também mostra quem fez.

O administrador vê "editado por fulano" em cada usuário e condomínio. Sem
isso, uma inativação feita pelo síndico aparecia como "criado por…" e a
última alteração ficava escondida.
"""
from __future__ import annotations

from tests.fixtures import (
    CPFS, cab, cadastrar_morador, cadastrar_porteiro, montar_condominio,
)


def historico(cliente, admin, entidade, entidade_id):
    r = cliente.get("/api/v1/admin/historico", headers=cab(admin),
                    params={"entidade": entidade, "entidade_id": entidade_id})
    assert r.status_code == 200, r.text
    return r.json()


def nome_sindico(cliente, base):
    return cliente.get("/api/v1/auth/eu", headers=cab(base["sindico"])).json()["nome"]


def test_sindico_edita_inativa_e_reativa_morador_com_registro(cliente, db):
    base = montar_condominio(cliente, db)
    morador_id, _ = cadastrar_morador(cliente, base["sindico"], base["cond"])
    quem = nome_sindico(cliente, base)
    url = f"/api/v1/usuarios/{morador_id}"

    r = cliente.put(url, headers=cab(base["sindico"]), json={"telefone": "(67) 98888-7777"})
    assert r.status_code == 200, r.text
    ultimo = historico(cliente, base["admin"], "usuario", morador_id)[0]
    assert (ultimo["acao"], ultimo["autor_nome"]) == ("editou", quem)
    assert ultimo["descricao"] == "Alterou o telefone"

    assert cliente.put(url, headers=cab(base["sindico"]),
                       json={"status": "inativo"}).status_code == 200
    assert historico(cliente, base["admin"], "usuario", morador_id)[0]["acao"] == "inativou"

    assert cliente.put(url, headers=cab(base["sindico"]),
                       json={"status": "ativo"}).status_code == 200
    ultimo = historico(cliente, base["admin"], "usuario", morador_id)[0]
    assert (ultimo["acao"], ultimo["autor_nome"]) == ("reativou", quem)

    # A lista do administrador mostra a última alteração, não só a criação.
    lista = cliente.get("/api/v1/admin/usuarios", headers=cab(base["admin"])).json()
    linha = next(u for u in lista if u["id"] == morador_id)
    assert linha["ultima_alteracao"]["acao"] == "reativou"


def test_salvar_sem_mudar_nada_nao_registra(cliente, db):
    base = montar_condominio(cliente, db)
    morador_id, _ = cadastrar_morador(cliente, base["sindico"], base["cond"])
    antes = len(historico(cliente, base["admin"], "usuario", morador_id))
    r = cliente.put(f"/api/v1/usuarios/{morador_id}", headers=cab(base["sindico"]),
                    json={"nome": "João Silva", "unidade_numero": "204"})
    assert r.status_code == 200, r.text
    assert len(historico(cliente, base["admin"], "usuario", morador_id)) == antes


def test_porteiro_cadastrado_e_permissoes_ficam_registrados(cliente, db):
    base = montar_condominio(cliente, db)
    porteiro_id, _ = cadastrar_porteiro(cliente, base["sindico"], base["cond"])
    quem = nome_sindico(cliente, base)
    registros = historico(cliente, base["admin"], "usuario", porteiro_id)
    assert registros[-1]["acao"] == "criou" and registros[-1]["autor_nome"] == quem

    r = cliente.put(f"/api/v1/usuarios/porteiros/{porteiro_id}/permissoes",
                    headers=cab(base["sindico"]),
                    json={"registrar_visitantes": True, "registrar_encomendas": False,
                          "registrar_veiculos": True, "registrar_ocorrencias": True,
                          "acessar_financeiro": False})
    assert r.status_code == 200, r.text
    ultimo = historico(cliente, base["admin"], "usuario", porteiro_id)[0]
    assert (ultimo["acao"], ultimo["autor_nome"]) == ("editou", quem)
    assert "permiss" in ultimo["descricao"]


def test_sindico_gera_novo_codigo_com_registro(cliente, db):
    base = montar_condominio(cliente, db)
    r = cliente.post("/api/v1/condominios/meu/codigo-acesso", headers=cab(base["sindico"]))
    assert r.status_code == 200, r.text
    ultimo = historico(cliente, base["admin"], "condominio", base["cond"]["id"])[0]
    assert (ultimo["acao"], ultimo["autor_nome"]) == ("novo_codigo", nome_sindico(cliente, base))

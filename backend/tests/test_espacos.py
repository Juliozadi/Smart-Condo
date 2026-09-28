"""Gestão dos espaços comuns pelo síndico.

Não havia tela para cadastrar espaços: só a carga de demonstração os
criava, e um condomínio novo ficava sem reserva. Também não havia como
editar, pôr em manutenção depois de criado, nem tirar um espaço de uso.
Nada é apagado: "excluir" inativa, e o espaço pode ser reativado.
"""
from __future__ import annotations

from tests.fixtures import cab, cadastrar_morador, criar_espaco, montar_condominio
from tests.test_reservas import AMANHA, cenario, reservar  # noqa: F401  (fixture)


def url(espaco):
    return f"/api/v1/espacos/{espaco['id']}"


def historico(cliente, admin, espaco_id):
    return cliente.get("/api/v1/admin/historico", headers=cab(admin),
                       params={"entidade": "espaco", "entidade_id": espaco_id}).json()


def test_sindico_edita_e_a_lista_mostra_quem_editou(cliente, cenario):
    r = cliente.put(url(cenario["salao"]), headers=cab(cenario["sindico"]),
                    json={"capacidade": 100, "em_manutencao": True, "nome": "Salão de Festas"})
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["capacidade"] == 100 and corpo["em_manutencao"] is True
    assert corpo["ultima_alteracao"]["acao"] == "editou"
    assert corpo["ultima_alteracao"]["descricao"] == "Alterou a capacidade e a manutenção"
    assert corpo["ultima_alteracao"]["autor_nome"]
    # Em manutenção, a reserva é recusada.
    assert reservar(cliente, cenario["ana"], cenario["salao"]["id"]).status_code == 409


def test_trocar_o_tipo_conta_uma_vez_so(cliente, cenario):
    r = cliente.put(url(cenario["salao"]), headers=cab(cenario["sindico"]),
                    json={"reservavel": False, "uso_livre": True})
    assert r.json()["ultima_alteracao"]["descricao"] == "Alterou o tipo"


def test_espaco_sem_uso_nenhum_e_recusado(cliente, cenario):
    h = cab(cenario["sindico"])
    r = cliente.post("/api/v1/espacos", headers=h, json={
        "nome": "Depósito", "reservavel": False, "uso_livre": False})
    assert r.status_code == 422
    r = cliente.put(url(cenario["salao"]), headers=h, json={"reservavel": False})
    assert r.status_code == 422
    r = cliente.put(url(cenario["salao"]), headers=h, json={"nome": None})
    assert r.status_code == 422


def test_so_o_sindico_do_condominio_mexe_no_espaco(cliente, cenario, db):
    assert cliente.put(url(cenario["salao"]), headers=cab(cenario["ana"]),
                       json={"capacidade": 1}).status_code == 403
    assert cliente.delete(url(cenario["salao"]), headers=cab(cenario["porteiro"])).status_code == 403
    outro = montar_condominio(cliente, db, nome="Outro", cnpj="11.444.777/0001-61",
                              email_sindico="s2@exemplo.com", cpf_sindico="52998224725",
                              email_admin="a2@exemplo.com", cpf_admin="16899535009")
    assert cliente.put(url(cenario["salao"]), headers=cab(outro["sindico"]),
                       json={"capacidade": 1}).status_code == 404
    assert cliente.delete(url(cenario["salao"]), headers=cab(outro["sindico"])).status_code == 404


def test_inativar_esconde_cancela_futuras_e_reativar_devolve(cliente, cenario):
    h = cab(cenario["sindico"])
    assert reservar(cliente, cenario["ana"], cenario["salao"]["id"]).status_code == 201

    r = cliente.delete(url(cenario["salao"]), headers=h)
    assert r.status_code == 200, r.text
    assert "1 reserva futura cancelada" in r.json()["detalhe"]
    assert cliente.delete(url(cenario["salao"]), headers=h).status_code == 409

    # Some para o morador, a reserva dele aparece cancelada, e não dá para reservar.
    nomes = [e["nome"] for e in cliente.get("/api/v1/espacos", headers=cab(cenario["ana"])).json()]
    assert "Salão de Festas" not in nomes
    minhas = cliente.get("/api/v1/espacos/reservas/minhas", headers=cab(cenario["ana"])).json()
    assert [m["status"] for m in minhas] == ["cancelada"]
    assert reservar(cliente, cenario["bruno"], cenario["salao"]["id"]).status_code == 404
    # "todos" só vale para o síndico.
    nomes = [e["nome"] for e in cliente.get("/api/v1/espacos", params={"todos": True},
                                            headers=cab(cenario["ana"])).json()]
    assert "Salão de Festas" not in nomes

    # O síndico ainda vê (no fim da lista) e reativa.
    lista = cliente.get("/api/v1/espacos", params={"todos": True}, headers=h).json()
    assert lista[-1]["nome"] == "Salão de Festas" and lista[-1]["inativo"] is True
    assert lista[-1]["ultima_alteracao"]["acao"] == "inativou"
    r = cliente.post(url(cenario["salao"]) + "/reativacao", headers=h)
    assert r.status_code == 200 and r.json()["inativo"] is False
    assert cliente.post(url(cenario["salao"]) + "/reativacao", headers=h).status_code == 409
    assert reservar(cliente, cenario["bruno"], cenario["salao"]["id"]).status_code == 201


def test_area_de_uso_livre_inativa_sai_da_ocupacao(cliente, cenario):
    h = cab(cenario["sindico"])
    cliente.delete(url(cenario["piscina"]), headers=h)
    ocupacao = cliente.get("/api/v1/espacos/ocupacao", headers=h).json()
    assert all(o["espaco_id"] != cenario["piscina"]["id"] for o in ocupacao)
    r = cliente.post(url(cenario["piscina"]) + "/ocupacao", headers=cab(cenario["porteiro"]),
                     json={"pessoas": 3})
    assert r.status_code == 404


def test_historico_completo_para_o_administrador(cliente, db):
    base = montar_condominio(cliente, db)
    espaco = criar_espaco(cliente, base["sindico"], nome="Churrasqueira")
    cliente.put(url(espaco), headers=cab(base["sindico"]), json={"descricao": "Coberta"})
    cliente.delete(url(espaco), headers=cab(base["sindico"]))
    acoes = [h["acao"] for h in historico(cliente, base["admin"], espaco["id"])]
    assert acoes == ["inativou", "editou", "criou"]


def test_condominio_novo_comeca_sem_espacos_e_o_sindico_cadastra(cliente, db):
    base = montar_condominio(cliente, db)
    _, tok_morador = cadastrar_morador(cliente, base["sindico"], base["cond"])
    assert cliente.get("/api/v1/espacos", headers=cab(tok_morador)).json() == []
    espaco = criar_espaco(cliente, base["sindico"], nome="Salão", descricao="Com cozinha")
    assert espaco["ultima_alteracao"]["acao"] == "criou"
    assert reservar(cliente, tok_morador, espaco["id"]).status_code == 201

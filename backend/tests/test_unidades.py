"""Unidades e vagas de garagem pelo síndico.

As vagas somam a capacidade do estacionamento que a portaria acompanha,
mas nenhuma tela as preenchia: fora da carga de demonstração, o
condomínio ficava com 0 vagas.
"""
from __future__ import annotations

from tests.fixtures import CPFS, cab, cadastrar_morador, cadastrar_porteiro, montar_condominio


def unidade(cliente, tok, numero):
    lista = cliente.get("/api/v1/condominios/meu/unidades", headers=cab(tok)).json()
    return next(u for u in lista if u["numero"] == numero)


def test_sindico_define_as_vagas_e_o_estacionamento_passa_a_contar(cliente, db):
    base = montar_condominio(cliente, db)
    cadastrar_morador(cliente, base["sindico"], base["cond"], unidade="204")
    _, porteiro = cadastrar_porteiro(cliente, base["sindico"], base["cond"], cpf=CPFS[2])
    assert cliente.get("/api/v1/veiculos/ocupacao",
                       headers=cab(porteiro)).json()["vagas_totais"] == 0

    u = unidade(cliente, base["sindico"], "204")
    assert u["total_moradores"] == 1
    r = cliente.put(f"/api/v1/condominios/meu/unidades/{u['id']}", headers=cab(base["sindico"]),
                    json={"vagas_garagem": 2, "andar": 2})
    assert r.status_code == 200, r.text
    assert r.json()["ultima_alteracao"]["descricao"] == "Alterou o andar e as vagas de garagem"
    assert cliente.get("/api/v1/veiculos/ocupacao",
                       headers=cab(porteiro)).json()["vagas_totais"] == 2
    # O porteiro vê as unidades, mas não quantos moram em cada uma.
    assert unidade(cliente, porteiro, "204")["total_moradores"] is None


def test_cadastro_de_unidade_fica_no_historico(cliente, db):
    base = montar_condominio(cliente, db)
    r = cliente.post("/api/v1/condominios/meu/unidades", headers=cab(base["sindico"]),
                     json={"numero": "101", "vagas_garagem": 1})
    assert r.status_code == 201, r.text
    historico = cliente.get("/api/v1/admin/historico", headers=cab(base["admin"]), params={
        "entidade": "unidade", "entidade_id": r.json()["id"]}).json()
    assert [h["acao"] for h in historico] == ["criou"]


def test_so_o_sindico_do_condominio_edita_e_vagas_nao_ficam_vazias(cliente, db):
    base = montar_condominio(cliente, db)
    _, morador = cadastrar_morador(cliente, base["sindico"], base["cond"], unidade="204")
    u = unidade(cliente, base["sindico"], "204")
    url = f"/api/v1/condominios/meu/unidades/{u['id']}"
    assert cliente.put(url, headers=cab(morador), json={"vagas_garagem": 9}).status_code == 403
    assert cliente.put(url, headers=cab(base["sindico"]),
                       json={"vagas_garagem": None}).status_code == 422
    assert cliente.put(url, headers=cab(base["sindico"]),
                       json={"vagas_garagem": 21}).status_code == 422
    outro = montar_condominio(cliente, db, nome="Outro", cnpj="11.444.777/0001-61",
                              email_sindico="s2@exemplo.com", cpf_sindico=CPFS[4],
                              email_admin="a2@exemplo.com", cpf_admin=CPFS[5])
    assert cliente.put(url, headers=cab(outro["sindico"]),
                       json={"vagas_garagem": 1}).status_code == 404


def _numeros(cliente, tok):
    return {u["numero"] for u in cliente.get("/api/v1/condominios/meu/unidades",
                                             headers=cab(tok)).json()}


def test_autocadastro_nao_aprovado_nao_cria_unidade_nas_listas(cliente, db):
    """Quem tem o código de acesso se cadastra numa unidade qualquer ("9999")
    e nunca confirma, ou é recusado: a unidade não pode aparecer para a
    portaria e para o síndico como se existisse."""
    base = montar_condominio(cliente, db)
    _, porteiro = cadastrar_porteiro(cliente, base["sindico"], base["cond"], cpf=CPFS[2])

    cliente.post("/api/v1/auth/cadastro/morador", json={
        "nome": "Nunca Confirma", "email": "nunca@exemplo.com", "cpf": CPFS[3],
        "telefone": "(67) 99999-0003", "senha": "senhaforte123",
        "codigo_condominio": base["cond"]["codigo_acesso"],
        "unidade_numero": "9999", "tipo_ocupacao": "proprietario",
    })
    recusado, _ = cadastrar_morador(cliente, base["sindico"], base["cond"], unidade="8888",
                                    aprovar=False)
    r = cliente.post(f"/api/v1/usuarios/{recusado}/aprovacao", headers=cab(base["sindico"]),
                     json={"aprovado": False, "motivo": "Não mora aqui"})
    assert r.status_code == 200, r.text

    for tok in (base["sindico"], porteiro):
        assert _numeros(cliente, tok) & {"9999", "8888"} == set()


def test_aprovar_o_morador_confirma_a_unidade(cliente, db):
    base = montar_condominio(cliente, db)
    morador, _ = cadastrar_morador(cliente, base["sindico"], base["cond"], unidade="301",
                                   aprovar=False)
    assert "301" not in _numeros(cliente, base["sindico"])
    r = cliente.post(f"/api/v1/usuarios/{morador}/aprovacao", headers=cab(base["sindico"]),
                     json={"aprovado": True})
    assert r.status_code == 200, r.text
    assert "301" in _numeros(cliente, base["sindico"])


def test_sindico_cadastra_a_unidade_que_so_existia_pendente(cliente, db):
    base = montar_condominio(cliente, db)
    cadastrar_morador(cliente, base["sindico"], base["cond"], unidade="402", aprovar=False)
    r = cliente.post("/api/v1/condominios/meu/unidades", headers=cab(base["sindico"]),
                     json={"numero": "402", "vagas_garagem": 1})
    assert r.status_code == 201, r.text
    assert "402" in _numeros(cliente, base["sindico"])
    # Agora sim, cadastrada: a segunda vez é repetição.
    r = cliente.post("/api/v1/condominios/meu/unidades", headers=cab(base["sindico"]),
                     json={"numero": "402"})
    assert r.status_code == 409

"""Animais de estimação dos apartamentos.

Situação real: o regimento pede o cadastro dos animais e a vacina
antirrábica em dia; o síndico não sabia quais apartamentos têm animal, e
a portaria, diante de um cachorro solto na garagem, não sabia de quem era.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from app.api.routers import animais as rota
from app.core.tempo import agora_utc, hoje_local
from app.models.usuario import Usuario
from app.services import notificacao
from tests.fixtures import cab, montar_condominio
from tests.test_financeiro import cenario  # noqa: F401

URL = "/api/v1/animais"


def cadastrar(cliente, tok, **extra):
    corpo = {"nome": "Thor", "especie": "cao", "porte": "grande", "raca": "Labrador",
             "cor": "Caramelo", "vacina_antirrabica_ate": (hoje_local() + timedelta(days=200)).isoformat()}
    corpo.update(extra)
    return cliente.post(URL, json=corpo, headers=cab(tok))


def listar(cliente, tok, **params):
    return cliente.get(URL, params=params, headers=cab(tok)).json()


def test_morador_cadastra_no_dele_e_cada_um_ve_o_seu(cliente, cenario):
    r = cadastrar(cliente, cenario["ana"])
    assert r.status_code == 201, r.text
    thor = r.json()
    assert thor["unidade"] == "204" and thor["vacina"] == "em_dia" and thor["pode_editar"]
    # Mesmo informando outro apartamento, o morador cadastra no dele.
    r = cadastrar(cliente, cenario["bruno"], nome="Mimi", especie="gato", porte="pequeno",
                  unidade_id=cenario["u204"])
    assert r.status_code == 201 and r.json()["unidade"] == "301"
    assert [a["nome"] for a in listar(cliente, cenario["ana"])] == ["Thor"]
    assert [a["nome"] for a in listar(cliente, cenario["bruno"])] == ["Mimi"]
    # Síndico e portaria veem todos; a portaria não edita.
    assert [a["nome"] for a in listar(cliente, cenario["sindico"])] == ["Thor", "Mimi"]
    da_portaria = listar(cliente, cenario["porteiro"])
    assert len(da_portaria) == 2 and not any(a["pode_editar"] for a in da_portaria)
    assert listar(cliente, cenario["sindico"], unidade_id=cenario["u301"])[0]["nome"] == "Mimi"


def test_editar_e_remover_so_quem_pode(cliente, cenario):
    thor = cadastrar(cliente, cenario["ana"]).json()
    # Outro morador nem enxerga; a portaria não mexe.
    assert cliente.put(f"{URL}/{thor['id']}", json={"cor": "Preto"},
                       headers=cab(cenario["bruno"])).status_code == 404
    assert cliente.put(f"{URL}/{thor['id']}", json={"cor": "Preto"},
                       headers=cab(cenario["porteiro"])).status_code == 403
    assert cliente.delete(f"{URL}/{thor['id']}", headers=cab(cenario["bruno"])).status_code == 404
    r = cliente.put(f"{URL}/{thor['id']}", json={"observacao": "Usar focinheira no elevador",
                                                "raca": ""}, headers=cab(cenario["ana"]))
    assert r.status_code == 200, r.text
    assert r.json()["observacao"] == "Usar focinheira no elevador" and r.json()["raca"] is None
    # Nome, espécie e porte não ficam em branco.
    assert cliente.put(f"{URL}/{thor['id']}", json={"nome": None},
                       headers=cab(cenario["ana"])).status_code == 422
    r = cliente.delete(f"{URL}/{thor['id']}", headers=cab(cenario["sindico"]))
    assert r.status_code == 200
    assert listar(cliente, cenario["ana"]) == []
    assert cliente.delete(f"{URL}/{thor['id']}", headers=cab(cenario["ana"])).status_code == 404


def test_sindico_cadastra_por_qualquer_apartamento(cliente, cenario):
    assert cadastrar(cliente, cenario["sindico"]).status_code == 422
    r = cadastrar(cliente, cenario["sindico"], unidade_id=cenario["u301"])
    assert r.status_code == 201 and r.json()["unidade"] == "301"
    assert cadastrar(cliente, cenario["sindico"], unidade_id=999999).status_code == 404


def test_situacao_da_vacina_e_filtro_de_pendentes(cliente, cenario):
    cadastrar(cliente, cenario["ana"])
    cadastrar(cliente, cenario["ana"], nome="Luna", especie="gato", porte="pequeno",
              vacina_antirrabica_ate=(hoje_local() - timedelta(days=3)).isoformat())
    cadastrar(cliente, cenario["bruno"], nome="Piu", especie="ave", porte="pequeno",
              vacina_antirrabica_ate=None)
    situacoes = {a["nome"]: a["vacina"] for a in listar(cliente, cenario["sindico"])}
    assert situacoes == {"Thor": "em_dia", "Luna": "vencida", "Piu": "sem_registro"}
    pendentes = [a["nome"] for a in listar(cliente, cenario["sindico"], vacina="pendente")]
    assert sorted(pendentes) == ["Luna", "Piu"]
    assert cliente.get(URL, params={"vacina": "outra"},
                       headers=cab(cenario["sindico"])).status_code == 422


def test_lembrete_da_vacina_uma_vez_por_semana(cliente, cenario, monkeypatch):
    avisos = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: avisos.append((destino, mensagem)))
    luna = cadastrar(cliente, cenario["ana"], nome="Luna", especie="gato", porte="pequeno",
                     vacina_antirrabica_ate=(hoje_local() - timedelta(days=3)).isoformat()).json()
    cadastrar(cliente, cenario["ana"], nome="Rex", vacina_antirrabica_ate=None)
    cadastrar(cliente, cenario["bruno"], nome="Mimi", especie="gato", porte="pequeno")
    assert cliente.post(f"{URL}/lembrete-vacina",
                        headers=cab(cenario["ana"])).status_code == 403
    r = cliente.post(f"{URL}/lembrete-vacina", headers=cab(cenario["sindico"]))
    assert r.status_code == 200 and r.json() == {"animais": 2, "apartamentos": 1}
    assert len(avisos) == 1 and avisos[0][0] == "ana@exemplo.com"
    assert "Luna (gato)" in avisos[0][1] and "Rex (cachorro)" in avisos[0][1]
    # De novo na mesma semana: ninguém é lembrado duas vezes.
    avisos.clear()
    r = cliente.post(f"{URL}/lembrete-vacina", headers=cab(cenario["sindico"]))
    assert r.json() == {"animais": 0, "apartamentos": 0} and avisos == []
    # Vacina atualizada: sai dos pendentes; uma semana depois, só o Rex volta.
    cliente.put(f"{URL}/{luna['id']}", headers=cab(cenario["ana"]),
                json={"vacina_antirrabica_ate": (hoje_local() + timedelta(days=360)).isoformat()})
    monkeypatch.setattr(rota, "_agora", lambda: agora_utc() + timedelta(days=8))
    r = cliente.post(f"{URL}/lembrete-vacina", headers=cab(cenario["sindico"]))
    assert r.json() == {"animais": 1, "apartamentos": 1}
    assert "Rex (cachorro)" in avisos[0][1] and "Luna" not in avisos[0][1]


@pytest.mark.parametrize("extra", [
    {"nome": ""},
    {"nome": "x" * 61},
    {"especie": "dinossauro"},
    {"porte": "gigante"},
    {"vacina_antirrabica_ate": (hoje_local() + timedelta(days=401)).isoformat()},
    {"observacao": "x" * 301},
])
def test_dados_invalidos(cliente, cenario, extra):
    assert cadastrar(cliente, cenario["ana"], **extra).status_code == 422


def test_limite_por_apartamento(cliente, cenario, monkeypatch):
    monkeypatch.setattr(rota, "LIMITE_ANIMAIS", 2)
    assert cadastrar(cliente, cenario["ana"]).status_code == 201
    assert cadastrar(cliente, cenario["ana"], nome="Luna").status_code == 201
    r = cadastrar(cliente, cenario["ana"], nome="Pipoca")
    assert r.status_code == 409 and "limite de 2 animais" in r.json()["detalhe"]


def test_quem_se_muda_leva_os_animais_da_lista(cliente, db, cenario):
    cadastrar(cliente, cenario["ana"])
    ana = db.query(Usuario).filter(Usuario.email == "ana@exemplo.com").one()
    ana.unidade_desde = agora_utc() + timedelta(minutes=5)  # "chegou" depois do cadastro
    db.commit()
    assert listar(cliente, cenario["sindico"]) == []


def test_proprietario_que_nao_mora_nao_cadastra(cliente, db, cenario):
    ana = db.query(Usuario).filter(Usuario.email == "ana@exemplo.com").one()
    ana.reside = False
    db.commit()
    r = cadastrar(cliente, cenario["ana"])
    assert r.status_code == 403 and "não mora" in r.json()["detalhe"]


def test_outro_condominio_nao_alcanca(cliente, db, cenario):
    thor = cadastrar(cliente, cenario["ana"]).json()
    outro = montar_condominio(cliente, db, nome="Outro", cnpj="11.444.777/0001-61",
                              email_sindico="s2@exemplo.com", cpf_sindico="52998224725",
                              email_admin="a2@exemplo.com", cpf_admin="16899535009")
    s2 = outro["sindico"]
    assert listar(cliente, s2) == []
    assert cliente.put(f"{URL}/{thor['id']}", json={"cor": "Preto"},
                       headers=cab(s2)).status_code == 404
    assert cliente.delete(f"{URL}/{thor['id']}", headers=cab(s2)).status_code == 404
    assert cadastrar(cliente, s2, unidade_id=cenario["u204"]).status_code == 404
    assert cliente.post(f"{URL}/lembrete-vacina", headers=cab(s2)).json()["animais"] == 0

"""Veículos cadastrados do apartamento.

Situação real: o carro do morador chega ao portão e a portaria não sabe
de quem é — precisa perguntar o apartamento e escolher na lista, todo
dia. O sistema só registrava as passagens, sem saber quais placas são
dos moradores.
"""
from __future__ import annotations

import pytest

from app.api.routers import veiculos as rota
from tests.fixtures import CPFS, cab, cadastrar_morador
from tests.test_operacao import cenario, mover  # noqa: F401

URL = "/api/v1/veiculos/cadastrados"


def cadastrar(cliente, tok, placa="abc-1d23", **extra):
    return cliente.post(URL, json={"placa": placa, "modelo": "Gol", "cor": "Prata", **extra},
                        headers=cab(tok))


def test_morador_cadastra_e_ve_os_do_apartamento(cliente, cenario):
    r = cadastrar(cliente, cenario["morador"])
    assert r.status_code == 201, r.text
    v = r.json()
    assert v["placa"] == "ABC1D23" and v["unidade"] == "204" and v["modelo"] == "Gol"
    assert [x["placa"] for x in cliente.get(URL, headers=cab(cenario["morador"])).json()] == [
        "ABC1D23"]
    # O vizinho não vê as placas do 204; o síndico e a portaria, sim.
    assert cliente.get(URL, headers=cab(cenario["outro"])).json() == []
    assert len(cliente.get(URL, headers=cab(cenario["sindico"])).json()) == 1
    assert len(cliente.get(URL, headers=cab(cenario["porteiro"])).json()) == 1


def test_a_portaria_reconhece_a_placa(cliente, cenario):
    cadastrar(cliente, cenario["morador"])
    r = cliente.get(f"{URL}/placa/abc1d23", headers=cab(cenario["porteiro"]))
    assert r.status_code == 200, r.text
    assert r.json()["unidade"] == "204" and r.json()["cor"] == "Prata"
    assert cliente.get(f"{URL}/placa/XYZ9A99", headers=cab(cenario["porteiro"])).status_code == 404
    # Morador não consulta placa de ninguém.
    assert cliente.get(f"{URL}/placa/ABC1D23", headers=cab(cenario["outro"])).status_code == 403


def test_entrada_de_morador_sem_escolher_o_apartamento(cliente, cenario):
    """Placa cadastrada: a portaria não precisa escolher o apartamento."""
    cadastrar(cliente, cenario["morador"])
    r = mover(cliente, cenario["porteiro"], placa="ABC1D23", categoria="morador")
    assert r.status_code == 201, r.text
    assert r.json()["unidade"] == "204"
    # Placa desconhecida continua pedindo a unidade.
    r = mover(cliente, cenario["porteiro"], placa="XYZ9A99", categoria="morador")
    assert r.status_code == 400


def test_placa_ja_cadastrada_em_outro_apartamento(cliente, cenario):
    cadastrar(cliente, cenario["morador"])
    r = cadastrar(cliente, cenario["outro"])
    assert r.status_code == 409
    # Não diz de quem é: placa de vizinho é dado dele.
    assert "outro apartamento" in r.json()["detalhe"] and "204" not in r.json()["detalhe"]
    assert cadastrar(cliente, cenario["morador"]).status_code == 409


def test_remover(cliente, cenario):
    v = cadastrar(cliente, cenario["morador"]).json()
    assert cliente.delete(f"{URL}/{v['id']}", headers=cab(cenario["outro"])).status_code == 404
    assert cliente.delete(f"{URL}/{v['id']}", headers=cab(cenario["morador"])).status_code == 200
    assert cliente.get(f"{URL}/placa/ABC1D23", headers=cab(cenario["porteiro"])).status_code == 404
    # Removida, a placa pode ser cadastrada de novo (carro vendido ao vizinho).
    assert cadastrar(cliente, cenario["outro"]).status_code == 201


def test_carro_de_quem_se_mudou_deixa_de_ser_reconhecido(cliente, cenario):
    carla_id, tok_carla = cadastrar_morador(cliente, cenario["sindico"], cenario["cond"],
                                            email="carla@exemplo.com", cpf=CPFS[4], unidade="204")
    cadastrar(cliente, tok_carla, placa="CAR1A23")
    assert cliente.delete(f"/api/v1/usuarios/{carla_id}",
                          headers=cab(cenario["sindico"])).status_code == 200
    assert cliente.get(f"{URL}/placa/CAR1A23", headers=cab(cenario["porteiro"])).status_code == 404
    assert cliente.get(URL, headers=cab(cenario["morador"])).json() == []
    # E a placa fica livre para outro apartamento.
    assert cadastrar(cliente, cenario["outro"], placa="CAR1A23").status_code == 201


def test_sindico_cadastra_para_um_apartamento(cliente, cenario):
    r = cadastrar(cliente, cenario["sindico"], unidade_id=cenario["u301"])
    assert r.status_code == 201, r.text
    assert r.json()["unidade"] == "301"
    assert cadastrar(cliente, cenario["sindico"], placa="XYZ9A99").status_code == 422


def test_porteiro_nao_cadastra(cliente, cenario):
    assert cadastrar(cliente, cenario["porteiro"], unidade_id=cenario["u204"]).status_code == 403


def test_limite_por_apartamento(cliente, cenario, monkeypatch):
    monkeypatch.setattr(rota, "LIMITE_VEICULOS", 2)
    assert cadastrar(cliente, cenario["morador"], placa="AAA1A11").status_code == 201
    assert cadastrar(cliente, cenario["morador"], placa="BBB1B11").status_code == 201
    r = cadastrar(cliente, cenario["morador"], placa="CCC1C11")
    assert r.status_code == 409 and "limite" in r.json()["detalhe"]


@pytest.mark.parametrize("placa", ["AB1234", "ABC12345", "ÁBC1D23", ""])
def test_placa_invalida(cliente, cenario, placa):
    assert cadastrar(cliente, cenario["morador"], placa=placa).status_code == 422

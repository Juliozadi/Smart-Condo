"""Achados e perdidos da portaria.

Situação real: o guarda-chuva esquecido no salão ia para uma gaveta da
portaria, e o dono só sabia se perguntasse ao porteiro certo. O que
ninguém reclamava ficava ali para sempre.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from app.api.routers import achados as rota
from app.core.tempo import hoje_local
from app.services import notificacao
from tests.fixtures import CPFS, cab, cadastrar_porteiro, montar_condominio
from tests.test_financeiro import cenario  # noqa: F401

URL = "/api/v1/achados"


def registrar(cliente, tok, **extra):
    corpo = {"descricao": "Guarda-chuva preto", "local": "Salão de festas",
             "encontrado_em": hoje_local().isoformat()}
    corpo.update(extra)
    return cliente.post(URL, json=corpo, headers=cab(tok))


def listar(cliente, tok, **params):
    return cliente.get(URL, params=params, headers=cab(tok)).json()


def test_portaria_registra_e_morador_ve_sem_dados_da_equipe(cliente, cenario):
    r = registrar(cliente, cenario["porteiro"])
    assert r.status_code == 201, r.text
    achado = r.json()
    assert achado["status"] == "guardado" and achado["registrado_por"]
    assert achado["pode_devolver"] and not achado["pode_descartar"]
    vistos = listar(cliente, cenario["ana"])
    assert [a["descricao"] for a in vistos] == ["Guarda-chuva preto"]
    assert vistos[0]["registrado_por"] is None and vistos[0]["pode_reclamar"]
    assert not vistos[0]["pode_devolver"]


def test_reclamar_desistir_e_so_um_dono_por_vez(cliente, cenario):
    achado = registrar(cliente, cenario["porteiro"]).json()
    r = cliente.post(f"{URL}/{achado['id']}/reclamacao", headers=cab(cenario["ana"]))
    assert r.status_code == 200 and r.json()["reclamado_por_mim"] and r.json()["pode_desistir"]
    # De novo: nada muda.
    assert cliente.post(f"{URL}/{achado['id']}/reclamacao",
                        headers=cab(cenario["ana"])).status_code == 200
    # Outro morador: o objeto já tem quem diga que é dele.
    r = cliente.post(f"{URL}/{achado['id']}/reclamacao", headers=cab(cenario["bruno"]))
    assert r.status_code == 409 and "Outro morador" in r.json()["detalhe"]
    visto_por_bruno = listar(cliente, cenario["bruno"])[0]
    assert visto_por_bruno["reclamado"] and not visto_por_bruno["pode_reclamar"]
    assert visto_por_bruno["reclamado_por"] is None
    # A equipe vê quem reclamou e de qual apartamento.
    da_portaria = listar(cliente, cenario["porteiro"])[0]
    assert da_portaria["reclamado_por"].endswith("apto 204")
    # Quem não reclamou não desfaz; quem reclamou, sim.
    assert cliente.delete(f"{URL}/{achado['id']}/reclamacao",
                          headers=cab(cenario["bruno"])).status_code == 409
    r = cliente.delete(f"{URL}/{achado['id']}/reclamacao", headers=cab(cenario["ana"]))
    assert r.status_code == 200 and not r.json()["reclamado"]
    assert cliente.post(f"{URL}/{achado['id']}/reclamacao",
                        headers=cab(cenario["bruno"])).status_code == 200


def test_entrega_avisa_quem_reclamou(cliente, cenario, monkeypatch):
    avisos = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: avisos.append((destino, mensagem)))
    achado = registrar(cliente, cenario["porteiro"]).json()
    cliente.post(f"{URL}/{achado['id']}/reclamacao", headers=cab(cenario["ana"]))
    r = cliente.post(f"{URL}/{achado['id']}/devolucao", headers=cab(cenario["porteiro"]),
                     json={"entregue_a": "Ana Beatriz Rocha"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "devolvido" and r.json()["entregue_a"] == "Ana Beatriz Rocha"
    assert len(avisos) == 1 and avisos[0][0] == "ana@exemplo.com"
    assert "foi entregue a Ana Beatriz Rocha" in avisos[0][1]
    assert "Se não foi você" in avisos[0][1]
    # Entregue não se entrega de novo, nem se reclama.
    r = cliente.post(f"{URL}/{achado['id']}/devolucao", headers=cab(cenario["porteiro"]),
                     json={"entregue_a": "Outra pessoa"})
    assert r.status_code == 409 and "já foi entregue" in r.json()["detalhe"]
    # A Ana continua vendo o dela, com a entrega; o Bruno não vê mais.
    da_ana = listar(cliente, cenario["ana"])
    assert da_ana[0]["status"] == "devolvido" and da_ana[0]["entregue_a"] == "Ana Beatriz Rocha"
    assert listar(cliente, cenario["bruno"]) == []
    assert cliente.post(f"{URL}/{achado['id']}/reclamacao",
                        headers=cab(cenario["bruno"])).status_code == 404


def test_entrega_sem_reclamacao_nao_avisa_ninguem(cliente, cenario, monkeypatch):
    avisos = []
    monkeypatch.setattr(notificacao, "notificar", lambda *a: avisos.append(a))
    achado = registrar(cliente, cenario["porteiro"]).json()
    r = cliente.post(f"{URL}/{achado['id']}/devolucao", headers=cab(cenario["sindico"]),
                     json={"entregue_a": "Visitante do 301"})
    assert r.status_code == 200 and avisos == []


def test_descarte_so_pelo_sindico_depois_do_prazo(cliente, cenario, monkeypatch):
    achado = registrar(cliente, cenario["porteiro"],
                       encontrado_em=(hoje_local() - timedelta(days=10)).isoformat()).json()
    corpo = {"destino": "Doado ao bazar da paróquia"}
    assert cliente.post(f"{URL}/{achado['id']}/descarte", headers=cab(cenario["porteiro"]),
                        json=corpo).status_code == 403
    r = cliente.post(f"{URL}/{achado['id']}/descarte", headers=cab(cenario["sindico"]), json=corpo)
    assert r.status_code == 409 and "faltam 20 dias" in r.json()["detalhe"]
    # Passados os 30 dias.
    monkeypatch.setattr(rota, "_hoje", lambda: hoje_local() + timedelta(days=20))
    assert listar(cliente, cenario["sindico"])[0]["pode_descartar"]
    r = cliente.post(f"{URL}/{achado['id']}/descarte", headers=cab(cenario["sindico"]), json=corpo)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "descartado" and r.json()["destino"] == corpo["destino"]
    # O morador não vê o descartado.
    assert listar(cliente, cenario["ana"]) == []


def test_reclamado_nao_se_descarta(cliente, cenario, monkeypatch):
    achado = registrar(cliente, cenario["porteiro"],
                       encontrado_em=(hoje_local() - timedelta(days=5)).isoformat()).json()
    cliente.post(f"{URL}/{achado['id']}/reclamacao", headers=cab(cenario["ana"]))
    monkeypatch.setattr(rota, "_hoje", lambda: hoje_local() + timedelta(days=60))
    r = cliente.post(f"{URL}/{achado['id']}/descarte", headers=cab(cenario["sindico"]),
                     json={"destino": "Doado"})
    assert r.status_code == 409 and "entregue a ele" in r.json()["detalhe"]


@pytest.mark.parametrize("extra", [
    {"descricao": "ab"},
    {"local": "x"},
    {"descricao": "x" * 201},
    {"encontrado_em": (hoje_local() + timedelta(days=1)).isoformat()},
    {"encontrado_em": (hoje_local() - timedelta(days=31)).isoformat()},
])
def test_dados_invalidos(cliente, cenario, extra):
    assert registrar(cliente, cenario["porteiro"], **extra).status_code == 422


def test_quem_pode_o_que(cliente, cenario):
    assert registrar(cliente, cenario["ana"]).status_code == 403
    achado = registrar(cliente, cenario["sindico"]).json()
    assert cliente.post(f"{URL}/{achado['id']}/reclamacao",
                        headers=cab(cenario["porteiro"])).status_code == 403
    assert cliente.post(f"{URL}/{achado['id']}/devolucao", headers=cab(cenario["ana"]),
                        json={"entregue_a": "Ana"}).status_code == 403
    assert cliente.get(URL).status_code == 401


def test_porteiro_sem_a_permissao_nao_ve_nem_registra(cliente, cenario):
    _, tok = cadastrar_porteiro(
        cliente, cenario["sindico"], cenario["cond"], email="limitado@exemplo.com", cpf=CPFS[4],
        permissoes={"registrar_visitantes": True, "registrar_encomendas": False,
                    "registrar_veiculos": True, "registrar_ocorrencias": True,
                    "acessar_financeiro": False})
    assert registrar(cliente, tok).status_code == 403
    assert cliente.get(URL, headers=cab(tok)).status_code == 403


def test_outro_condominio_nao_alcanca(cliente, db, cenario):
    achado = registrar(cliente, cenario["porteiro"]).json()
    outro = montar_condominio(cliente, db, nome="Outro", cnpj="11.444.777/0001-61",
                              email_sindico="s2@exemplo.com", cpf_sindico="52998224725",
                              email_admin="a2@exemplo.com", cpf_admin="16899535009")
    s2 = outro["sindico"]
    assert listar(cliente, s2) == []
    assert cliente.post(f"{URL}/{achado['id']}/devolucao", headers=cab(s2),
                        json={"entregue_a": "Invasor"}).status_code == 404
    assert cliente.post(f"{URL}/{achado['id']}/descarte", headers=cab(s2),
                        json={"destino": "Lixo"}).status_code == 404


def test_filtro_por_situacao(cliente, cenario):
    a = registrar(cliente, cenario["porteiro"]).json()
    registrar(cliente, cenario["porteiro"], descricao="Óculos de sol", local="Piscina")
    cliente.post(f"{URL}/{a['id']}/devolucao", headers=cab(cenario["porteiro"]),
                 json={"entregue_a": "Dona do guarda-chuva"})
    guardados = listar(cliente, cenario["sindico"], status="guardado")
    assert [x["descricao"] for x in guardados] == ["Óculos de sol"]
    todos = listar(cliente, cenario["sindico"])
    # Os guardados vêm primeiro.
    assert [x["status"] for x in todos] == ["guardado", "devolvido"]

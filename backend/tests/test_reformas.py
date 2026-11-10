"""Obras e reformas nos apartamentos (NBR 16280).

Situação real: a quebradeira começa num sábado de manhã, o porteiro não
sabe se deixa o pedreiro subir e ninguém conferiu se a parede derrubada
era estrutural. A norma pede que a reforma seja comunicada ao síndico
antes, com o prazo e — se mexer em estrutura, paredes ou instalações —
o responsável técnico e a ART ou o RRT.
"""
from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import text

from app.api.routers import reformas as rota
from app.core.tempo import hoje_local
from app.services import notificacao
from tests.fixtures import CPFS, cab, cadastrar_morador
from tests.test_portaria import cenario  # noqa: F401

URL = "/api/v1/reformas"


def comunicar(cliente, tok, inicio=5, dias=20, **extra):
    hoje = hoje_local()
    corpo = {"descricao": "Troca do piso da sala e pintura dos quartos",
             "empresa": "Reformas Pantanal",
             "inicio": (hoje + timedelta(days=inicio)).isoformat(),
             "fim": (hoje + timedelta(days=inicio + dias)).isoformat()}
    corpo.update(extra)
    return cliente.post(URL, json=corpo, headers=cab(tok))


def avaliar(cliente, tok, reforma_id, aprovada=True, **extra):
    return cliente.post(f"{URL}/{reforma_id}/avaliacao", json={"aprovada": aprovada, **extra},
                        headers=cab(tok))


def adiantar(monkeypatch, dias):
    """Faz o "hoje" das reformas andar `dias` para a frente."""
    hoje = hoje_local() + timedelta(days=dias)
    monkeypatch.setattr(rota, "_hoje", lambda: hoje)


def anotar(monkeypatch):
    avisos = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: avisos.append((destino, titulo,
                                                                                mensagem)))
    return avisos


def test_morador_comunica_e_sindico_aprova_com_condicoes(cliente, cenario, monkeypatch):
    avisos = anotar(monkeypatch)
    r = comunicar(cliente, cenario["ana"])
    assert r.status_code == 201, r.text
    ref = r.json()
    assert ref["status"] == "pendente" and ref["situacao"] == "aguardando"
    assert ref["unidade"] == "204" and ref["pode_cancelar"] and not ref["pode_avaliar"]
    assert [a[0] for a in avisos] == ["sindico@exemplo.com"]

    r = avaliar(cliente, cenario["sindico"], ref["id"],
                condicoes="Só das 8h às 17h; entulho em caçamba, não no corredor.")
    assert r.status_code == 200, r.text
    ref = r.json()
    assert ref["status"] == "aprovada" and ref["situacao"] == "agendada"
    assert ref["condicoes"].startswith("Só das 8h") and ref["pode_prorrogar"]
    destino, titulo, mensagem = avisos[-1]
    assert destino == "ana@exemplo.com" and titulo == "Reforma aprovada"
    assert "caçamba" in mensagem and "Visitantes Autorizados" in mensagem
    # Quem mora no apartamento vê; o vizinho, não.
    assert len(cliente.get(URL, headers=cab(cenario["ana"])).json()) == 1
    assert cliente.get(URL, headers=cab(cenario["bruno"])).json() == []


def test_portaria_ve_so_as_aprovadas_no_prazo(cliente, cenario, monkeypatch):
    pendente = comunicar(cliente, cenario["ana"]).json()
    aprovada = comunicar(cliente, cenario["bruno"], inicio=3, dias=10).json()
    assert avaliar(cliente, cenario["sindico"], aprovada["id"]).status_code == 200
    vistas = cliente.get(URL, headers=cab(cenario["porteiro"])).json()
    assert [v["id"] for v in vistas] == [aprovada["id"]]
    assert pendente["id"] not in [v["id"] for v in vistas]
    assert not any(vistas[0][k] for k in ("pode_avaliar", "pode_cancelar", "pode_concluir"))

    # Em andamento durante o prazo; passado o fim, a portaria não deixa
    # mais entrar — e a obra some da lista dela.
    adiantar(monkeypatch, 5)
    assert cliente.get(URL, headers=cab(cenario["porteiro"])).json()[0]["situacao"] == \
        "em_andamento"
    adiantar(monkeypatch, 14)
    assert cliente.get(URL, headers=cab(cenario["porteiro"])).json() == []
    do_sindico = {v["id"]: v for v in cliente.get(URL, headers=cab(cenario["sindico"])).json()}
    assert do_sindico[aprovada["id"]]["situacao"] == "prazo_encerrado"


def test_recusa_exige_motivo(cliente, cenario, monkeypatch):
    avisos = anotar(monkeypatch)
    ref = comunicar(cliente, cenario["ana"]).json()
    assert avaliar(cliente, cenario["sindico"], ref["id"], aprovada=False).status_code == 422
    r = avaliar(cliente, cenario["sindico"], ref["id"], aprovada=False,
                motivo="Falta o projeto da nova parede da cozinha.")
    assert r.status_code == 200
    assert r.json()["status"] == "recusada" and r.json()["condicoes"] is None
    assert avisos[-1][1] == "Reforma recusada" and "cozinha" in avisos[-1][2]
    # Avaliada uma vez, não se avalia de novo.
    assert avaliar(cliente, cenario["sindico"], ref["id"]).status_code == 409


def test_estrutura_exige_responsavel_tecnico(cliente, cenario):
    r = comunicar(cliente, cenario["ana"], altera_estrutura=True)
    assert r.status_code == 422 and "ART" in r.text
    r = comunicar(cliente, cenario["ana"], altera_estrutura=True,
                  responsavel_tecnico="Eng. Paula Ramos", art_rrt="   ")
    assert r.status_code == 422
    r = comunicar(cliente, cenario["ana"], descricao="Troca do quadro elétrico e da fiação",
                  altera_estrutura=True, responsavel_tecnico="Eng. Paula Ramos",
                  art_rrt="ART 1220260012345")
    assert r.status_code == 201, r.text
    assert r.json()["responsavel_tecnico"] == "Eng. Paula Ramos"


def test_comunica_com_antecedencia(cliente, cenario):
    r = comunicar(cliente, cenario["ana"], inicio=rota.ANTECEDENCIA_MINIMA_DIAS - 1)
    assert r.status_code == 400 and "antecedência" in r.json()["detalhe"]
    assert comunicar(cliente, cenario["ana"],
                     inicio=rota.ANTECEDENCIA_MINIMA_DIAS).status_code == 201


@pytest.mark.parametrize("extra", [
    {"descricao": "Pintura"},                                     # curta demais
    {"fim": (hoje_local() + timedelta(days=4)).isoformat()},      # termina antes de começar
    {"fim": (hoje_local() + timedelta(days=500)).isoformat()},    # mais de um ano
    {"inicio": 400, "dias": 1},                                   # começa daqui a mais de um ano
    {"art_rrt": "RRT 998877"},                                    # ART sem responsável
])
def test_dados_invalidos(cliente, cenario, extra):
    assert comunicar(cliente, cenario["ana"], **extra).status_code == 422


def test_quem_pode(cliente, cenario):
    assert comunicar(cliente, cenario["porteiro"]).status_code == 403
    assert comunicar(cliente, cenario["sindico"]).status_code == 403
    ref = comunicar(cliente, cenario["ana"]).json()
    assert avaliar(cliente, cenario["ana"], ref["id"]).status_code == 403
    assert avaliar(cliente, cenario["porteiro"], ref["id"]).status_code == 403
    # O vizinho não acha a reforma de outro apartamento.
    assert cliente.post(f"{URL}/{ref['id']}/cancelamento",
                        headers=cab(cenario["bruno"])).status_code == 404
    assert cliente.post(f"{URL}/{ref['id']}/prorrogacao",
                        json={"fim": (hoje_local() + timedelta(days=60)).isoformat()},
                        headers=cab(cenario["ana"])).status_code == 403


def test_dono_que_nao_mora_comunica_a_reforma(cliente, cenario, db):
    # O dono reforma o apartamento antes de alugar: mesmo sem morar lá, é
    # ele quem responde pela obra.
    db.execute(text("UPDATE usuarios SET reside = false WHERE email = 'bruno@exemplo.com'"))
    db.commit()
    r = comunicar(cliente, cenario["bruno"])
    assert r.status_code == 201, r.text
    assert r.json()["unidade"] == "301"


def test_morador_desiste_e_o_sindico_fica_sabendo_se_ja_aprovada(cliente, cenario, monkeypatch):
    avisos = anotar(monkeypatch)
    pendente = comunicar(cliente, cenario["ana"]).json()
    r = cliente.post(f"{URL}/{pendente['id']}/cancelamento", headers=cab(cenario["ana"]))
    assert r.status_code == 200 and r.json()["status"] == "cancelada"
    assert avisos[-1][1] == "Reforma para avaliar"     # nada novo para o síndico

    aprovada = comunicar(cliente, cenario["ana"]).json()
    avaliar(cliente, cenario["sindico"], aprovada["id"])
    r = cliente.post(f"{URL}/{aprovada['id']}/cancelamento", headers=cab(cenario["ana"]))
    assert r.status_code == 200 and not r.json()["cancelada_pelo_sindico"]
    assert avisos[-1][:2] == ("sindico@exemplo.com", "Reforma cancelada")
    assert cliente.post(f"{URL}/{aprovada['id']}/cancelamento",
                        headers=cab(cenario["ana"])).status_code == 409


def test_sindico_embarga_a_obra_com_motivo(cliente, cenario, monkeypatch):
    avisos = anotar(monkeypatch)
    ref = comunicar(cliente, cenario["ana"]).json()
    avaliar(cliente, cenario["sindico"], ref["id"])
    r = cliente.post(f"{URL}/{ref['id']}/cancelamento", headers=cab(cenario["sindico"]))
    assert r.status_code == 422
    r = cliente.post(f"{URL}/{ref['id']}/cancelamento",
                     json={"motivo": "Parede estrutural derrubada sem ART."},
                     headers=cab(cenario["sindico"]))
    assert r.status_code == 200 and r.json()["cancelada_pelo_sindico"]
    assert avisos[-1][:2] == ("ana@exemplo.com", "Reforma cancelada")
    assert "sem ART" in avisos[-1][2]


def test_sindico_prorroga_o_prazo(cliente, cenario, monkeypatch):
    avisos = anotar(monkeypatch)
    ref = comunicar(cliente, cenario["ana"], inicio=3, dias=10).json()
    url = f"{URL}/{ref['id']}/prorrogacao"
    novo_fim = (hoje_local() + timedelta(days=30)).isoformat()
    # Só a aprovada.
    assert cliente.post(url, json={"fim": novo_fim},
                        headers=cab(cenario["sindico"])).status_code == 409
    avaliar(cliente, cenario["sindico"], ref["id"])
    assert cliente.post(url, json={"fim": ref["fim"]},
                        headers=cab(cenario["sindico"])).status_code == 400
    assert cliente.post(url, json={"fim": (hoje_local() + timedelta(days=400)).isoformat()},
                        headers=cab(cenario["sindico"])).status_code == 400
    r = cliente.post(url, json={"fim": novo_fim, "motivo": "Atraso na entrega do porcelanato."},
                     headers=cab(cenario["sindico"]))
    assert r.status_code == 200 and r.json()["fim"] == novo_fim
    assert avisos[-1][:2] == ("ana@exemplo.com", "Reforma prorrogada")


def test_conclusao(cliente, cenario, monkeypatch):
    avisos = anotar(monkeypatch)
    ref = comunicar(cliente, cenario["ana"], inicio=3, dias=10).json()
    url = f"{URL}/{ref['id']}/conclusao"
    assert cliente.post(url, headers=cab(cenario["ana"])).status_code == 409   # pendente
    avaliar(cliente, cenario["sindico"], ref["id"])
    assert cliente.post(url, headers=cab(cenario["ana"])).status_code == 409   # nem começou
    adiantar(monkeypatch, 8)
    assert cliente.get(URL, headers=cab(cenario["ana"])).json()[0]["pode_concluir"]
    r = cliente.post(url, headers=cab(cenario["ana"]))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "concluida" and r.json()["concluida_em"]
    assert avisos[-1][:2] == ("sindico@exemplo.com", "Reforma concluída")
    assert cliente.post(url, headers=cab(cenario["ana"])).status_code == 409
    # A concluída sai da lista da portaria.
    assert cliente.get(URL, headers=cab(cenario["porteiro"])).json() == []


def test_aprovar_depois_do_prazo(cliente, cenario, monkeypatch):
    ref = comunicar(cliente, cenario["ana"], inicio=3, dias=5).json()
    adiantar(monkeypatch, 10)
    vista = cliente.get(URL, headers=cab(cenario["sindico"])).json()[0]
    assert not vista["pode_avaliar"]
    r = avaliar(cliente, cenario["sindico"], ref["id"])
    assert r.status_code == 409 and "prazo" in r.json()["detalhe"]
    # Recusar ainda pode, para encerrar o pedido.
    assert avaliar(cliente, cenario["sindico"], ref["id"], aprovada=False,
                   motivo="Prazo vencido.").status_code == 200


def test_limite_por_apartamento(cliente, cenario, monkeypatch):
    monkeypatch.setattr(rota, "LIMITE_ATIVAS", 2)
    assert comunicar(cliente, cenario["ana"]).status_code == 201
    assert comunicar(cliente, cenario["ana"]).status_code == 201
    r = comunicar(cliente, cenario["ana"])
    assert r.status_code == 409 and "limite" in r.json()["detalhe"]
    # Outro apartamento não entra na conta.
    assert comunicar(cliente, cenario["bruno"]).status_code == 201


def test_quem_chega_nao_ve_a_reforma_de_quem_saiu(cliente, cenario):
    carla_id, tok_carla = cadastrar_morador(cliente, cenario["sindico"], cenario["cond"],
                                            email="carla@exemplo.com", cpf=CPFS[4], unidade="204")
    ref = comunicar(cliente, tok_carla).json()
    assert cliente.delete(f"/api/v1/usuarios/{carla_id}",
                          headers=cab(cenario["sindico"])).status_code == 200
    _, tok_dani = cadastrar_morador(cliente, cenario["sindico"], cenario["cond"],
                                    email="dani@exemplo.com", cpf=CPFS[5], unidade="204")
    assert cliente.get(URL, headers=cab(tok_dani)).json() == []
    assert cliente.post(f"{URL}/{ref['id']}/cancelamento",
                        headers=cab(tok_dani)).status_code == 404
    # A Ana já morava lá: continua vendo.
    assert [x["id"] for x in cliente.get(URL, headers=cab(cenario["ana"])).json()] == [ref["id"]]


def test_filtro_por_situacao(cliente, cenario):
    a = comunicar(cliente, cenario["ana"]).json()
    comunicar(cliente, cenario["bruno"])
    avaliar(cliente, cenario["sindico"], a["id"])
    r = cliente.get(URL, params={"status": "pendente"}, headers=cab(cenario["sindico"]))
    assert [x["unidade"] for x in r.json()] == ["301"]
    assert cliente.get(URL, params={"status": "xyz"},
                       headers=cab(cenario["sindico"])).status_code == 422

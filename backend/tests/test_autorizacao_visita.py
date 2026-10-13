"""Visitante autorizado com antecedência pelo morador.

Situação real: a diarista vem toda terça e sexta, o pedreiro trabalha no
apartamento a semana inteira, os convidados do aniversário chegam no
sábado. Sem a autorização prévia, a portaria interfonava a cada entrada e
o visitante esperava a resposta de um morador que podia estar no trabalho
— e, depois de duas horas sem resposta, ficava do lado de fora.
"""
from __future__ import annotations

import time
from datetime import timedelta

import pytest

from app.api.routers import portaria
from app.core.tempo import hoje_local
from app.services import notificacao
from tests.fixtures import CPFS, cab, cadastrar_morador
from tests.test_concorrencia import ao_mesmo_tempo
from tests.test_portaria import DOC_VISITANTE, cenario  # noqa: F401

URL = "/api/v1/portaria/autorizacoes"


def _dia(n=0):
    return (hoje_local() + timedelta(days=n)).isoformat()


def autorizar(cliente, tok, **extra):
    corpo = {"nome": "Maria Diarista", "tipo": "Diarista", "valida_de": _dia(),
             "valida_ate": _dia(30)}
    corpo.update(extra)
    return cliente.post(URL, json=corpo, headers=cab(tok))


def entrar(cliente, tok, unidade_id, autorizacao_id, documento=DOC_VISITANTE, **extra):
    corpo = {"unidade_id": unidade_id, "nome": "Maria Diarista", "documento": documento,
             "tipo_visita": "Diarista", "autorizacao_id": autorizacao_id}
    corpo.update(extra)
    return cliente.post("/api/v1/portaria/visitantes", json=corpo, headers=cab(tok))


@pytest.fixture
def avisos(monkeypatch):
    lista = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: lista.append((destino, mensagem)))
    return lista


def test_autorizado_entra_sem_esperar_resposta(cliente, cenario, avisos):
    a = autorizar(cliente, cenario["ana"], documento=DOC_VISITANTE)
    assert a.status_code == 201, a.text
    a = a.json()
    assert a["unidade"] == "204" and a["vale_hoje"] is True
    assert a["autorizado_por_nome"] == "João Silva"

    assert a["documento"] == "01740740262"
    hoje = cliente.get(URL, headers=cab(cenario["porteiro"])).json()
    assert [x["id"] for x in hoje] == [a["id"]]
    # A portaria vê só o meio do CPF: digita o do documento apresentado,
    # e o sistema confere.
    assert hoje[0]["documento"] == "***.407.402-**" and hoje[0]["ja_dentro"] is False

    avisos.clear()
    r = entrar(cliente, cenario["porteiro"], cenario["u204"], a["id"], nome="Outro Nome")
    assert r.status_code == 201, r.text
    v = r.json()
    assert v["status"] == "dentro" and v["entrada_em"] is not None
    assert v["autorizacao_id"] == a["id"]
    # Quem entra é a pessoa autorizada, com o nome que o morador deu.
    assert v["nome"] == "Maria Diarista"
    # O morador é avisado de que ela entrou, sem precisar responder.
    assert [d for d, _ in avisos] == ["ana@exemplo.com"]
    assert "autorização" in avisos[0][1]
    assert cliente.get(URL, headers=cab(cenario["porteiro"])).json()[0]["ja_dentro"] is True
    # E não há o que confirmar.
    r = cliente.post(f"/api/v1/portaria/visitantes/{v['id']}/confirmacao",
                     json={"confirmado": False}, headers=cab(cenario["ana"]))
    assert r.status_code == 409


def test_documento_precisa_conferir(cliente, cenario):
    a = autorizar(cliente, cenario["ana"], documento=DOC_VISITANTE).json()
    r = entrar(cliente, cenario["porteiro"], cenario["u204"], a["id"], documento=CPFS[5])
    assert r.status_code == 400
    assert "documento" in r.json()["detalhe"]
    # Sem documento na autorização, vale o que a portaria conferiu.
    b = autorizar(cliente, cenario["ana"], nome="Convidado da Festa", tipo="Convidado").json()
    assert b["documento"] is None
    assert entrar(cliente, cenario["porteiro"], cenario["u204"], b["id"],
                  documento=CPFS[5]).status_code == 201


def test_autorizacao_de_outra_unidade_nao_serve(cliente, cenario):
    a = autorizar(cliente, cenario["ana"]).json()
    r = entrar(cliente, cenario["porteiro"], cenario["u301"], a["id"])
    assert r.status_code == 404
    assert entrar(cliente, cenario["porteiro"], cenario["u204"], 999999).status_code == 404


def test_so_nos_dias_da_semana_escolhidos(cliente, cenario):
    outro_dia = hoje_local().isoweekday() % 7 + 1
    a = autorizar(cliente, cenario["ana"], dias_semana=[outro_dia]).json()
    assert a["dias_semana"] == [outro_dia] and a["vale_hoje"] is False
    assert cliente.get(URL, headers=cab(cenario["porteiro"])).json() == []
    r = entrar(cliente, cenario["porteiro"], cenario["u204"], a["id"])
    assert r.status_code == 409
    assert "não vale hoje" in r.json()["detalhe"]

    b = autorizar(cliente, cenario["ana"],
                  dias_semana=[hoje_local().isoweekday(), outro_dia, outro_dia]).json()
    assert b["vale_hoje"] is True and len(b["dias_semana"]) == 2
    assert entrar(cliente, cenario["porteiro"], cenario["u204"], b["id"]).status_code == 201


def test_periodo_futuro_ainda_nao_vale(cliente, cenario):
    a = autorizar(cliente, cenario["ana"], valida_de=_dia(3), valida_ate=_dia(3),
                  nome="Convidado do Sábado", tipo="Convidado").json()
    assert a["vale_hoje"] is False
    # O morador vê a que está por vir; a portaria, só as de hoje.
    assert [x["id"] for x in cliente.get(URL, headers=cab(cenario["ana"])).json()] == [a["id"]]
    assert cliente.get(URL, headers=cab(cenario["porteiro"])).json() == []
    assert entrar(cliente, cenario["porteiro"], cenario["u204"], a["id"]).status_code == 409


def test_morador_revoga(cliente, cenario):
    a = autorizar(cliente, cenario["ana"]).json()
    # Outro apartamento não revoga.
    assert cliente.delete(f"{URL}/{a['id']}", headers=cab(cenario["bruno"])).status_code == 404
    assert cliente.delete(f"{URL}/{a['id']}", headers=cab(cenario["porteiro"])).status_code == 403
    # Quem mora no mesmo apartamento, sim (a diarista foi dispensada).
    _, tok_filha = cadastrar_morador(cliente, cenario["sindico"], cenario["cond"],
                                     email="filha@exemplo.com", cpf=CPFS[4], unidade="204")
    r = cliente.delete(f"{URL}/{a['id']}", headers=cab(tok_filha))
    assert r.status_code == 200, r.text
    assert cliente.get(URL, headers=cab(cenario["porteiro"])).json() == []
    assert cliente.get(URL, headers=cab(cenario["ana"])).json() == []
    r = entrar(cliente, cenario["porteiro"], cenario["u204"], a["id"])
    assert r.status_code == 409
    assert "revogada" in r.json()["detalhe"]
    assert cliente.delete(f"{URL}/{a['id']}", headers=cab(tok_filha)).status_code == 409


def test_quem_se_mudou_nao_autoriza_mais(cliente, cenario):
    """A autorização é de quem mora lá: o morador que se mudou não deixa a
    diarista dele com a entrada liberada no apartamento do vizinho novo."""
    _, tok_carla = cadastrar_morador(cliente, cenario["sindico"], cenario["cond"],
                                     email="carla@exemplo.com", cpf=CPFS[4], unidade="204")
    a = autorizar(cliente, tok_carla).json()
    carla = next(u for u in cliente.get("/api/v1/usuarios", headers=cab(cenario["sindico"])).json()
                 if u["email"] == "carla@exemplo.com")
    assert cliente.delete(f"/api/v1/usuarios/{carla['id']}",
                          headers=cab(cenario["sindico"])).status_code == 200

    assert cliente.get(URL, headers=cab(cenario["porteiro"])).json() == []
    assert cliente.get(URL, headers=cab(cenario["ana"])).json() == []
    r = entrar(cliente, cenario["porteiro"], cenario["u204"], a["id"])
    assert r.status_code == 409
    assert "não mora mais" in r.json()["detalhe"]


def test_morador_ve_so_as_do_proprio_apartamento(cliente, cenario):
    autorizar(cliente, cenario["ana"])
    assert cliente.get(URL, headers=cab(cenario["bruno"])).json() == []
    # O síndico acompanha as de hoje, como a portaria.
    assert len(cliente.get(URL, headers=cab(cenario["sindico"])).json()) == 1


def test_quem_pode_autorizar(cliente, cenario):
    assert autorizar(cliente, cenario["porteiro"]).status_code == 403
    assert autorizar(cliente, cenario["sindico"]).status_code == 403


def test_porteiro_sem_permissao_nao_ve(cliente, cenario):
    porteiros = cliente.get("/api/v1/usuarios", headers=cab(cenario["sindico"])).json()
    porteiro = next(u for u in porteiros if u["papel"] == "porteiro")
    r = cliente.put(f"/api/v1/usuarios/porteiros/{porteiro['id']}/permissoes",
                    headers=cab(cenario["sindico"]), json={
                        "registrar_visitantes": False, "registrar_encomendas": True,
                        "registrar_veiculos": True, "registrar_ocorrencias": True,
                        "acessar_financeiro": False})
    assert r.status_code == 200, r.text
    assert cliente.get(URL, headers=cab(cenario["porteiro"])).status_code == 403


def test_nao_entra_duas_vezes_ao_mesmo_tempo(cliente, cenario):
    a = autorizar(cliente, cenario["ana"]).json()
    v = entrar(cliente, cenario["porteiro"], cenario["u204"], a["id"]).json()
    r = entrar(cliente, cenario["porteiro"], cenario["u204"], a["id"])
    assert r.status_code == 409
    assert "já está dentro" in r.json()["detalhe"]
    # Saiu para almoçar e voltou: entra de novo pela mesma autorização.
    assert cliente.post(f"/api/v1/portaria/visitantes/{v['id']}/saida",
                        headers=cab(cenario["porteiro"])).status_code == 200
    assert entrar(cliente, cenario["porteiro"], cenario["u204"], a["id"]).status_code == 201


def test_duas_portarias_registram_a_mesma_entrada(cliente, cenario, monkeypatch):
    """Clique duplo, ou a portaria e a guarita ao mesmo tempo: sem trava na
    autorização, as duas conferiam "já está dentro?" antes de a outra
    gravar. A pausa depois da conferência deixa a janela larga."""
    original = portaria._autorizacao_para_entrada

    def conferir_devagar(*args, **kwargs):
        autorizacao = original(*args, **kwargs)
        time.sleep(0.3)
        return autorizacao

    monkeypatch.setattr(portaria, "_autorizacao_para_entrada", conferir_devagar)
    a = autorizar(cliente, cenario["ana"]).json()
    codigos = ao_mesmo_tempo(4, lambda i: entrar(
        cliente, cenario["porteiro"], cenario["u204"], a["id"]).status_code)
    assert sorted(codigos) == [201, 409, 409, 409], codigos


def test_limite_de_autorizacoes_por_apartamento(cliente, cenario, monkeypatch):
    monkeypatch.setattr(portaria, "LIMITE_AUTORIZACOES", 2)
    assert autorizar(cliente, cenario["ana"]).status_code == 201
    b = autorizar(cliente, cenario["ana"]).json()
    r = autorizar(cliente, cenario["ana"])
    assert r.status_code == 409
    assert "limite" in r.json()["detalhe"]
    # Revogar libera espaço; o vizinho tem o próprio limite.
    cliente.delete(f"{URL}/{b['id']}", headers=cab(cenario["ana"]))
    assert autorizar(cliente, cenario["ana"]).status_code == 201
    assert autorizar(cliente, cenario["bruno"]).status_code == 201


@pytest.mark.parametrize("dados", [
    {"valida_de": _dia(-1)},
    {"valida_de": _dia(5), "valida_ate": _dia(4)},
    {"valida_ate": _dia(400)},
    {"valida_de": _dia(400), "valida_ate": _dia(401)},
    {"dias_semana": [0]},
    {"dias_semana": [8]},
    {"documento": "123.456.789-00"},
    {"nome": "Al"},
    {"tipo": ""},
    {"observacao": "x" * 301},
])
def test_dados_invalidos(cliente, cenario, dados):
    r = autorizar(cliente, cenario["ana"], **dados)
    assert r.status_code in (400, 422), (dados, r.text)


def test_documento_em_branco_e_sem_documento(cliente, cenario):
    a = autorizar(cliente, cenario["ana"], documento="  ", dias_semana=[])
    assert a.status_code == 201, a.text
    assert a.json()["documento"] is None and a.json()["dias_semana"] is None

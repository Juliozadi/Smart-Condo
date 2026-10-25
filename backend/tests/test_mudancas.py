"""Agendamento de mudança.

Situação real: o caminhão de mudança chega sem aviso, ocupa o elevador
de serviço a manhã inteira e encontra outra mudança marcada na mesma
hora; a portaria não sabe se pode deixar entrar. O regimento costuma
permitir mudanças de segunda a sábado, em horário comercial, com aviso
prévio e uma de cada vez.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

import pytest
from sqlalchemy import text

from app.api.routers import mudancas as rota
from app.core.tempo import agora_local, hoje_local
from app.services import notificacao
from tests.fixtures import CPFS, cab, cadastrar_morador
from tests.test_portaria import cenario  # noqa: F401

URL = "/api/v1/mudancas"


def dia_util(a_partir=3):
    """Um dia de semana daqui a pelo menos `a_partir` dias."""
    dia = hoje_local() + timedelta(days=a_partir)
    while dia.isoweekday() > 5:
        dia += timedelta(days=1)
    return dia


def proximo(dia_semana, a_partir=3):
    """O próximo dia da semana (1 = segunda ... 7 = domingo)."""
    dia = hoje_local() + timedelta(days=a_partir)
    while dia.isoweekday() != dia_semana:
        dia += timedelta(days=1)
    return dia


def agendar(cliente, tok, dia=None, inicio="08:00", fim="12:00", **extra):
    corpo = {"tipo": "chegada", "data": (dia or dia_util()).isoformat(),
             "hora_inicio": inicio, "hora_fim": fim, "empresa": "Mudanças Rápidas"}
    corpo.update(extra)
    return cliente.post(URL, json=corpo, headers=cab(tok))


def avaliar(cliente, tok, mudanca_id, aprovada=True, motivo=None):
    corpo = {"aprovada": aprovada}
    if motivo:
        corpo["motivo"] = motivo
    return cliente.post(f"{URL}/{mudanca_id}/avaliacao", json=corpo, headers=cab(tok))


def test_morador_agenda_e_sindico_aprova(cliente, cenario, monkeypatch):
    avisos = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: avisos.append(destino))
    r = agendar(cliente, cenario["ana"])
    assert r.status_code == 201, r.text
    m = r.json()
    assert m["status"] == "pendente" and m["unidade"] == "204"
    assert avisos == ["sindico@exemplo.com"]

    r = avaliar(cliente, cenario["sindico"], m["id"])
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "aprovada"
    assert avisos[-1] == "ana@exemplo.com"
    # Quem mora no apartamento vê; o vizinho, não.
    assert len(cliente.get(URL, headers=cab(cenario["ana"])).json()) == 1
    assert cliente.get(URL, headers=cab(cenario["bruno"])).json() == []


def test_portaria_ve_as_aprovadas(cliente, cenario):
    m = agendar(cliente, cenario["ana"]).json()
    assert cliente.get(URL, headers=cab(cenario["porteiro"])).json() == []
    avaliar(cliente, cenario["sindico"], m["id"])
    vistas = cliente.get(URL, headers=cab(cenario["porteiro"])).json()
    assert [v["unidade"] for v in vistas] == ["204"]


def test_recusa_com_motivo(cliente, cenario):
    m = agendar(cliente, cenario["ana"]).json()
    assert avaliar(cliente, cenario["sindico"], m["id"], aprovada=False).status_code == 422
    r = avaliar(cliente, cenario["sindico"], m["id"], aprovada=False, motivo="Elevador em manutenção")
    assert r.status_code == 200
    assert r.json()["status"] == "recusada" and r.json()["motivo_recusa"] == "Elevador em manutenção"
    assert avaliar(cliente, cenario["sindico"], m["id"]).status_code == 409


def test_uma_mudanca_de_cada_vez(cliente, cenario):
    dia = dia_util()
    m = agendar(cliente, cenario["ana"], dia, "08:00", "12:00").json()
    r = agendar(cliente, cenario["bruno"], dia, "11:00", "15:00")
    assert r.status_code == 409 and "outra mudança" in r.json()["detalhe"]
    # Recusada, o horário fica livre.
    avaliar(cliente, cenario["sindico"], m["id"], aprovada=False, motivo="Data errada")
    assert agendar(cliente, cenario["bruno"], dia, "11:00", "15:00").status_code == 201
    # Encostar não é sobrepor.
    assert agendar(cliente, cenario["ana"], dia, "15:00", "17:00").status_code == 201


@pytest.mark.parametrize("ajuste,trecho", [
    ({"dia": "domingo"}, "domingo"),
    ({"dia": "sabado", "fim": "14:00"}, "sábado"),
    ({"inicio": "07:00"}, "8h"),
    ({"fim": "19:00"}, "18h"),
    ({"dia": "amanha"}, "antecedência"),
])
def test_regras_do_regimento(cliente, cenario, ajuste, trecho):
    dias = {"domingo": proximo(7), "sabado": proximo(6),
            "amanha": hoje_local() + timedelta(days=1)}
    dia = dias.get(ajuste.get("dia"), dia_util())
    r = agendar(cliente, cenario["ana"], dia, ajuste.get("inicio", "08:00"),
                ajuste.get("fim", "12:00"))
    assert r.status_code == 400, r.text
    assert trecho in r.json()["detalhe"], r.json()["detalhe"]


def test_sabado_de_manha_pode(cliente, cenario):
    assert agendar(cliente, cenario["ana"], proximo(6), "08:00", "12:00").status_code == 201


@pytest.mark.parametrize("corpo", [
    {"hora_inicio": "12:00", "hora_fim": "10:00"},
    {"tipo": "festa"},
    {"empresa": "x" * 121},
    {"data": (date.today() + timedelta(days=400)).isoformat()},
])
def test_dados_invalidos(cliente, cenario, corpo):
    r = agendar(cliente, cenario["ana"], **corpo)
    assert r.status_code in (400, 422), (corpo, r.text)


def test_morador_cancela_a_sua(cliente, cenario):
    m = agendar(cliente, cenario["ana"]).json()
    assert cliente.post(f"{URL}/{m['id']}/cancelamento",
                        headers=cab(cenario["bruno"])).status_code == 404
    r = cliente.post(f"{URL}/{m['id']}/cancelamento", headers=cab(cenario["ana"]))
    assert r.status_code == 200 and r.json()["status"] == "cancelada"
    assert cliente.post(f"{URL}/{m['id']}/cancelamento",
                        headers=cab(cenario["ana"])).status_code == 409


def test_quem_pode(cliente, cenario):
    assert agendar(cliente, cenario["porteiro"]).status_code == 403
    assert agendar(cliente, cenario["sindico"]).status_code == 403
    m = agendar(cliente, cenario["ana"]).json()
    assert avaliar(cliente, cenario["ana"], m["id"]).status_code == 403
    assert avaliar(cliente, cenario["porteiro"], m["id"]).status_code == 403


def test_regras_estao_na_api(cliente, cenario):
    r = cliente.get(f"{URL}/regras", headers=cab(cenario["ana"]))
    assert r.status_code == 200
    assert r.json()["antecedencia_minima_dias"] == rota.ANTECEDENCIA_MINIMA_DIAS


def test_sindico_cancela_com_motivo(cliente, cenario, monkeypatch):
    m = agendar(cliente, cenario["ana"]).json()
    avaliar(cliente, cenario["sindico"], m["id"])
    avisos = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: avisos.append((destino, mensagem)))
    url = f"{URL}/{m['id']}/cancelamento"
    assert cliente.post(url, headers=cab(cenario["porteiro"])).status_code == 403
    assert cliente.post(url, headers=cab(cenario["sindico"])).status_code == 422
    r = cliente.post(url, json={"motivo": "Elevador de serviço quebrado"},
                     headers=cab(cenario["sindico"]))
    assert r.status_code == 200, r.text
    assert r.json()["cancelada_pelo_sindico"] is True
    assert avisos == [("ana@exemplo.com", avisos[0][1])]
    assert "Elevador de serviço quebrado" in avisos[0][1]
    # A portaria deixa de ver.
    assert cliente.get(URL, headers=cab(cenario["porteiro"])).json() == []


def test_morador_desiste_da_aprovada_e_o_sindico_fica_sabendo(cliente, cenario, monkeypatch):
    m = agendar(cliente, cenario["ana"]).json()
    avaliar(cliente, cenario["sindico"], m["id"])
    avisos = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: avisos.append(destino))
    r = cliente.post(f"{URL}/{m['id']}/cancelamento", headers=cab(cenario["ana"]))
    assert r.status_code == 200 and r.json()["cancelada_pelo_sindico"] is False
    assert avisos == ["sindico@exemplo.com"]


def test_o_horario_passa_sem_avaliacao(cliente, cenario, monkeypatch):
    dia = dia_util()
    pendente = agendar(cliente, cenario["ana"], dia, "08:00", "10:00").json()
    aprovada = agendar(cliente, cenario["bruno"], dia, "10:00", "12:00").json()
    avaliar(cliente, cenario["sindico"], aprovada["id"])
    # No dia, às 13h: a pendente vira recusada; a aprovada, concluída.
    fuso = agora_local().tzinfo
    monkeypatch.setattr(rota, "_agora", lambda: datetime.combine(dia, time(13), fuso))
    todas = {m["id"]: m for m in cliente.get(URL, headers=cab(cenario["sindico"])).json()}
    assert todas[pendente["id"]]["status"] == "recusada"
    assert todas[pendente["id"]]["motivo_recusa"] == rota.MOTIVO_SEM_AVALIACAO
    assert todas[aprovada["id"]]["status"] == "concluida"
    # Passada, não se aprova nem se cancela.
    assert avaliar(cliente, cenario["sindico"], pendente["id"]).status_code == 409
    assert cliente.post(f"{URL}/{aprovada['id']}/cancelamento",
                        headers=cab(cenario["bruno"])).status_code == 409


def test_aprovar_depois_da_hora(cliente, cenario, monkeypatch):
    dia = dia_util()
    m = agendar(cliente, cenario["ana"], dia, "08:00", "12:00").json()
    fuso = agora_local().tzinfo
    monkeypatch.setattr(rota, "_agora", lambda: datetime.combine(dia, time(9), fuso))
    r = avaliar(cliente, cenario["sindico"], m["id"])
    assert r.status_code == 409 and "já passou" in r.json()["detalhe"]


def test_blocos_diferentes_tem_elevadores_diferentes(cliente, cenario, db):
    db.execute(text("UPDATE unidades SET bloco = 'B' WHERE id = :id"), {"id": cenario["u301"]})
    db.commit()
    dia = dia_util()
    assert agendar(cliente, cenario["ana"], dia, "08:00", "12:00").status_code == 201
    assert agendar(cliente, cenario["bruno"], dia, "09:00", "11:00").status_code == 201
    # O morador vê o que está tomado no próprio bloco, sem saber de quem.
    r = cliente.get(f"{URL}/ocupados", params={"data": dia.isoformat()},
                    headers=cab(cenario["ana"]))
    assert r.status_code == 200
    assert r.json() == [{"inicio": "08:00:00", "fim": "12:00:00"}]


def test_limite_por_apartamento(cliente, cenario, monkeypatch):
    monkeypatch.setattr(rota, "LIMITE_ATIVAS", 2)
    dia = dia_util()
    assert agendar(cliente, cenario["ana"], dia, "08:00", "09:00").status_code == 201
    assert agendar(cliente, cenario["ana"], dia, "09:00", "10:00").status_code == 201
    r = agendar(cliente, cenario["ana"], dia, "10:00", "11:00")
    assert r.status_code == 409 and "limite" in r.json()["detalhe"]


def test_quem_chega_nao_ve_a_mudanca_de_quem_saiu(cliente, cenario):
    carla_id, tok_carla = cadastrar_morador(cliente, cenario["sindico"], cenario["cond"],
                                            email="carla@exemplo.com", cpf=CPFS[4], unidade="204")
    m = agendar(cliente, tok_carla, tipo="saida").json()
    assert cliente.delete(f"/api/v1/usuarios/{carla_id}",
                          headers=cab(cenario["sindico"])).status_code == 200
    _, tok_dani = cadastrar_morador(cliente, cenario["sindico"], cenario["cond"],
                                    email="dani@exemplo.com", cpf=CPFS[5], unidade="204")
    assert cliente.get(URL, headers=cab(tok_dani)).json() == []
    assert cliente.post(f"{URL}/{m['id']}/cancelamento",
                        headers=cab(tok_dani)).status_code == 404
    # A Ana já morava lá: continua vendo.
    assert [x["id"] for x in cliente.get(URL, headers=cab(cenario["ana"])).json()] == [m["id"]]


# ── Regras do regimento de cada condomínio ───────────────────────────

def definir_regras(cliente, tok, antecedencia=2, horarios=None):
    horarios = horarios if horarios is not None else {
        str(d): {"inicio": "08:00", "fim": "18:00"} for d in range(1, 6)}
    return cliente.put(f"{URL}/regras", json={"antecedencia_minima_dias": antecedencia,
                                              "horarios": horarios}, headers=cab(tok))


def test_sindico_define_as_regras_do_condominio(cliente, cenario):
    """Cada regimento é um: aqui, 5 dias de aviso, das 9h às 17h, e nada
    de mudança no sábado."""
    horarios = {str(d): {"inicio": "09:00", "fim": "17:00"} for d in range(1, 6)}
    r = definir_regras(cliente, cenario["sindico"], antecedencia=5, horarios=horarios)
    assert r.status_code == 200, r.text
    regras = cliente.get(f"{URL}/regras", headers=cab(cenario["ana"])).json()
    assert regras["antecedencia_minima_dias"] == 5
    assert sorted(regras["horarios"]) == ["1", "2", "3", "4", "5"]

    # O primeiro dia útil entre amanhã e daqui a 4 dias: cedo demais.
    cedo = next(d for d in (hoje_local() + timedelta(days=n) for n in range(1, 5))
                if d.isoweekday() <= 5)
    r = agendar(cliente, cenario["ana"], cedo, "09:00", "12:00")
    assert r.status_code == 400 and "5 dias" in r.json()["detalhe"]
    r = agendar(cliente, cenario["ana"], proximo(6, a_partir=6), "09:00", "11:00")
    assert r.status_code == 400 and "sábado" in r.json()["detalhe"]
    r = agendar(cliente, cenario["ana"], dia_util(6), "08:00", "12:00")
    assert r.status_code == 400 and "9h" in r.json()["detalhe"]
    assert agendar(cliente, cenario["ana"], dia_util(6), "09:00", "17:00").status_code == 201


def test_domingo_liberado(cliente, cenario):
    horarios = {"7": {"inicio": "10:00", "fim": "14:00"}, "1": {"inicio": "08:00", "fim": "18:00"}}
    assert definir_regras(cliente, cenario["sindico"], horarios=horarios).status_code == 200
    assert agendar(cliente, cenario["ana"], proximo(7), "10:00", "13:30").status_code == 201
    r = agendar(cliente, cenario["ana"], proximo(7), "10:00", "15:00")
    assert r.status_code == 400 and "14h" in r.json()["detalhe"]


@pytest.mark.parametrize("antecedencia,horarios", [
    (2, {"1": {"inicio": "18:00", "fim": "08:00"}}),     # fim antes do início
    (2, {}),                                              # nenhum dia
    (2, {"8": {"inicio": "08:00", "fim": "18:00"}}),      # dia que não existe
    (61, {"1": {"inicio": "08:00", "fim": "18:00"}}),     # antecedência demais
    (-1, {"1": {"inicio": "08:00", "fim": "18:00"}}),
])
def test_regras_invalidas(cliente, cenario, antecedencia, horarios):
    r = definir_regras(cliente, cenario["sindico"], antecedencia, horarios)
    assert r.status_code == 422, r.text


def test_so_o_sindico_define_as_regras(cliente, cenario):
    assert definir_regras(cliente, cenario["ana"]).status_code == 403
    assert definir_regras(cliente, cenario["porteiro"]).status_code == 403

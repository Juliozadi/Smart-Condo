"""Testes dos requisitos da seção 6 e da seção 13.5.3 da documentação."""
from __future__ import annotations

from datetime import timedelta

import pytest

from app.core.tempo import hoje_local
from tests.fixtures import (
    CPFS, cab, cadastrar_morador, cadastrar_porteiro, criar_espaco, montar_condominio,
)

AMANHA = (hoje_local() + timedelta(days=1)).isoformat()


@pytest.fixture
def cenario(cliente, db):
    """Um condomínio com síndico, dois moradores, um porteiro e dois espaços."""
    base = montar_condominio(cliente, db)
    tok_sindico, cond = base["sindico"], base["cond"]

    _, tok_a = cadastrar_morador(
        cliente, tok_sindico, cond, email="ana@exemplo.com", cpf=CPFS[1], unidade="204"
    )
    _, tok_b = cadastrar_morador(
        cliente, tok_sindico, cond, email="bruno@exemplo.com", cpf=CPFS[3], unidade="301"
    )
    _, tok_porteiro = cadastrar_porteiro(cliente, tok_sindico, cond, cpf=CPFS[2])

    salao = criar_espaco(cliente, tok_sindico, nome="Salão de Festas", capacidade=80)
    piscina = criar_espaco(
        cliente, tok_sindico, nome="Piscina", capacidade=60,
        reservavel=False, uso_livre=True,
    )
    return {
        "cond": cond, "sindico": tok_sindico, "ana": tok_a, "bruno": tok_b,
        "porteiro": tok_porteiro, "salao": salao, "piscina": piscina,
    }


def reservar(cliente, tok, espaco_id, inicio="14:00", fim="22:00", data=AMANHA, **extra):
    corpo = {
        "espaco_id": espaco_id, "data": data,
        "hora_inicio": inicio, "hora_fim": fim, "pessoas_estimadas": 50,
    }
    corpo.update(extra)
    return cliente.post("/api/v1/espacos/reservas", json=corpo, headers=cab(tok))


# ── Sigilo da reserva (seção 6) ──────────────────────────────────────
def test_a_agenda_nao_revela_quem_reservou(cliente, cenario):
    """Seção 6: "eu gostaria que não mostrasse quem alugou, para evitar
    conflitos". O Bruno vê o espaço ocupado, mas não vê a Ana."""
    assert reservar(cliente, cenario["ana"], cenario["salao"]["id"]).status_code == 201

    r = cliente.get(
        "/api/v1/espacos/agenda",
        params={"inicio": AMANHA, "fim": AMANHA},
        headers=cab(cenario["bruno"]),
    )
    assert r.status_code == 200, r.text
    agenda = r.json()
    assert len(agenda) == 1

    item = agenda[0]
    assert item["data"] == AMANHA
    assert item["hora_inicio"] == "14:00:00"
    assert item["disponivel"] is False

    # Nenhum vestígio da autoria na resposta.
    texto = r.text.lower()
    for proibido in ["ana", "morador_id", "morador_nome", "unidade", "204"]:
        assert proibido not in texto, f"a agenda vazou {proibido!r}"


def test_o_conflito_de_horario_nao_revela_quem_reservou(cliente, cenario):
    reservar(cliente, cenario["ana"], cenario["salao"]["id"], "14:00", "22:00")

    r = reservar(cliente, cenario["bruno"], cenario["salao"]["id"], "18:00", "23:00")
    assert r.status_code == 409
    detalhe = r.json()["detalhe"]
    assert "14:00" in detalhe and "22:00" in detalhe
    assert "Ana" not in detalhe and "204" not in detalhe


def test_morador_nao_ve_a_reserva_de_outro(cliente, cenario):
    reservar(cliente, cenario["ana"], cenario["salao"]["id"])

    r = cliente.get("/api/v1/espacos/reservas/minhas", headers=cab(cenario["bruno"]))
    assert r.status_code == 200
    assert r.json() == []


def test_morador_nao_pode_cancelar_a_reserva_de_outro(cliente, cenario):
    criada = reservar(cliente, cenario["ana"], cenario["salao"]["id"]).json()

    r = cliente.delete(
        f"/api/v1/espacos/reservas/{criada['id']}", headers=cab(cenario["bruno"])
    )
    assert r.status_code == 404


def test_morador_nao_acessa_a_lista_do_sindico(cliente, cenario):
    r = cliente.get("/api/v1/espacos/reservas", headers=cab(cenario["ana"]))
    assert r.status_code == 403


def test_o_sindico_ve_quem_reservou(cliente, cenario):
    """Seção 11.5.3: é ele quem aprova, então precisa saber de quem é."""
    reservar(cliente, cenario["ana"], cenario["salao"]["id"])

    r = cliente.get("/api/v1/espacos/reservas", headers=cab(cenario["sindico"]))
    assert r.status_code == 200
    item = r.json()[0]
    assert item["morador_nome"] == "João Silva"
    assert item["unidade"] == "204"


# ── Ordem de chegada (seção 6) ───────────────────────────────────────
@pytest.mark.parametrize(
    "inicio, fim, esperado",
    [
        ("18:00", "23:00", 409),  # sobrepõe o fim
        ("12:00", "15:00", 409),  # sobrepõe o início
        ("15:00", "20:00", 409),  # dentro do intervalo
        ("10:00", "23:00", 409),  # engloba
        ("22:00", "23:30", 201),  # começa quando o outro acaba
        ("09:00", "14:00", 201),  # acaba quando o outro começa
    ],
)
def test_sobreposicao_de_horario(cliente, cenario, inicio, fim, esperado):
    reservar(cliente, cenario["ana"], cenario["salao"]["id"], "14:00", "22:00")
    r = reservar(cliente, cenario["bruno"], cenario["salao"]["id"], inicio, fim)
    assert r.status_code == esperado, r.text


def test_reserva_cancelada_libera_o_horario(cliente, cenario):
    criada = reservar(cliente, cenario["ana"], cenario["salao"]["id"]).json()
    cliente.delete(f"/api/v1/espacos/reservas/{criada['id']}", headers=cab(cenario["ana"]))

    r = reservar(cliente, cenario["bruno"], cenario["salao"]["id"])
    assert r.status_code == 201


def test_nao_reserva_data_passada(cliente, cenario):
    ontem = (hoje_local() - timedelta(days=1)).isoformat()
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"], data=ontem)
    assert r.status_code == 400


def test_nao_reserva_horario_de_hoje_que_ja_passou(cliente, cenario):
    hoje = hoje_local().isoformat()
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"], "00:00", "00:30", data=hoje)
    assert r.status_code == 400
    assert "já passou" in r.json()["detalhe"]


def test_antecedencia_maxima(cliente, cenario):
    from app.core.config import settings
    longe = (hoje_local() + timedelta(days=settings.RESERVA_ANTECEDENCIA_MAX_DIAS + 1)).isoformat()
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"], data=longe)
    assert r.status_code == 400
    assert "antecedência" in r.json()["detalhe"]


def test_hora_fim_antes_do_inicio_e_recusada(cliente, cenario):
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"], "22:00", "14:00")
    assert r.status_code == 422


def test_acima_da_capacidade_e_recusado(cliente, cenario):
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"], pessoas_estimadas=200)
    assert r.status_code == 400
    assert "80 pessoas" in r.json()["detalhe"]


def test_espaco_de_uso_livre_nao_aceita_reserva(cliente, cenario):
    r = reservar(cliente, cenario["ana"], cenario["piscina"]["id"])
    assert r.status_code == 400


# ── Aprovação (seção 13.5.3) ─────────────────────────────────────────
def test_sindico_aprova_e_recusa(cliente, cenario):
    a = reservar(cliente, cenario["ana"], cenario["salao"]["id"], "14:00", "18:00").json()
    assert a["status"] == "pendente"

    ap = cliente.post(
        f"/api/v1/espacos/reservas/{a['id']}/avaliacao",
        json={"aprovada": True},
        headers=cab(cenario["sindico"]),
    )
    assert ap.status_code == 200
    assert ap.json()["status"] == "aprovada"

    b = reservar(cliente, cenario["bruno"], cenario["salao"]["id"], "19:00", "22:00").json()
    rec = cliente.post(
        f"/api/v1/espacos/reservas/{b['id']}/avaliacao",
        json={"aprovada": False, "motivo": "Obra no salão"},
        headers=cab(cenario["sindico"]),
    )
    assert rec.status_code == 200
    assert rec.json()["status"] == "recusada"
    assert rec.json()["motivo_recusa"] == "Obra no salão"


def test_reserva_recusada_libera_o_horario(cliente, cenario):
    a = reservar(cliente, cenario["ana"], cenario["salao"]["id"]).json()
    cliente.post(
        f"/api/v1/espacos/reservas/{a['id']}/avaliacao",
        json={"aprovada": False, "motivo": "Indisponível"},
        headers=cab(cenario["sindico"]),
    )
    assert reservar(cliente, cenario["bruno"], cenario["salao"]["id"]).status_code == 201


def test_nao_avalia_duas_vezes(cliente, cenario):
    a = reservar(cliente, cenario["ana"], cenario["salao"]["id"]).json()
    corpo = {"aprovada": True}
    assert cliente.post(
        f"/api/v1/espacos/reservas/{a['id']}/avaliacao", json=corpo, headers=cab(cenario["sindico"])
    ).status_code == 200
    assert cliente.post(
        f"/api/v1/espacos/reservas/{a['id']}/avaliacao", json=corpo, headers=cab(cenario["sindico"])
    ).status_code == 409


# ── Ocupação em tempo real (seção 6) ─────────────────────────────────
def test_ocupacao_da_piscina(cliente, cenario):
    """Seção 6: "Piscina: 23 pessoas no momento"."""
    r = cliente.post(
        f"/api/v1/espacos/{cenario['piscina']['id']}/ocupacao",
        json={"pessoas": 23},
        headers=cab(cenario["porteiro"]),
    )
    assert r.status_code == 201, r.text

    consulta = cliente.get("/api/v1/espacos/ocupacao", headers=cab(cenario["ana"]))
    assert consulta.status_code == 200
    piscina = next(e for e in consulta.json() if e["espaco_nome"] == "Piscina")
    assert piscina["pessoas"] == 23
    assert piscina["capacidade"] == 60
    assert piscina["percentual"] == 38


def test_ocupacao_usa_a_leitura_mais_recente(cliente, cenario):
    for n in (23, 41, 7):
        cliente.post(
            f"/api/v1/espacos/{cenario['piscina']['id']}/ocupacao",
            json={"pessoas": n}, headers=cab(cenario["porteiro"]),
        )
    r = cliente.get("/api/v1/espacos/ocupacao", headers=cab(cenario["ana"]))
    assert next(e for e in r.json() if e["espaco_nome"] == "Piscina")["pessoas"] == 7


def test_ocupacao_so_lista_areas_de_uso_livre(cliente, cenario):
    r = cliente.get("/api/v1/espacos/ocupacao", headers=cab(cenario["ana"]))
    nomes = [e["espaco_nome"] for e in r.json()]
    assert nomes == ["Piscina"]


def test_morador_nao_registra_ocupacao(cliente, cenario):
    r = cliente.post(
        f"/api/v1/espacos/{cenario['piscina']['id']}/ocupacao",
        json={"pessoas": 10}, headers=cab(cenario["ana"]),
    )
    assert r.status_code == 403


def test_ocupacao_acima_da_capacidade_e_recusada(cliente, cenario):
    r = cliente.post(
        f"/api/v1/espacos/{cenario['piscina']['id']}/ocupacao",
        json={"pessoas": 999}, headers=cab(cenario["porteiro"]),
    )
    assert r.status_code == 400


def test_nao_registra_ocupacao_em_espaco_reservavel(cliente, cenario):
    r = cliente.post(
        f"/api/v1/espacos/{cenario['salao']['id']}/ocupacao",
        json={"pessoas": 10}, headers=cab(cenario["porteiro"]),
    )
    assert r.status_code == 400


# ── Morador que deixa o condomínio ───────────────────────────────────
def test_inativar_o_morador_libera_as_reservas_futuras(cliente, db, cenario):
    """Antes, o salão continuava bloqueado pela reserva de quem já tinha se
    mudado. As reservas passadas ficam no histórico."""
    from datetime import time

    from app.models.enums import StatusReserva
    from app.models.espaco import Reserva

    ana_id = cliente.get("/api/v1/auth/eu", headers=cab(cenario["ana"])).json()["id"]
    salao = cenario["salao"]["id"]
    dia = (hoje_local() + timedelta(days=10)).isoformat()
    futura = reservar(cliente, cenario["ana"], salao, data=dia).json()
    cliente.post(f"/api/v1/espacos/reservas/{futura['id']}/avaliacao",
                 json={"aprovada": True}, headers=cab(cenario["sindico"]))
    passada = Reserva(espaco_id=salao, morador_id=ana_id,
                      data=hoje_local() - timedelta(days=10),
                      hora_inicio=time(14), hora_fim=time(18), status=StatusReserva.APROVADA)
    db.add(passada)
    db.commit()

    r = cliente.delete(f"/api/v1/usuarios/{ana_id}", headers=cab(cenario["sindico"]))
    assert r.status_code == 200, r.text

    db.expire_all()
    assert db.get(Reserva, futura["id"]).status == StatusReserva.CANCELADA
    assert db.get(Reserva, passada.id).status == StatusReserva.APROVADA
    # O horário ficou livre para os outros.
    assert reservar(cliente, cenario["bruno"], salao, data=dia).status_code == 201

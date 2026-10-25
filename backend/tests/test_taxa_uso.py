"""Taxa de uso dos espaços.

Situação real: o salão de festas tem taxa de uso (limpeza, gás, desgaste)
que vem no boleto de quem reservou. O sistema reservava o salão, mas a
taxa era cobrada à mão — e, cancelada a festa, alguém precisava lembrar
de tirar a cobrança.
"""
from __future__ import annotations

from app.core.tempo import hoje_local
from tests.fixtures import cab
from tests.test_reservas import AMANHA, cenario, reservar  # noqa: F401

ESPACOS = "/api/v1/espacos"
RESERVAS = "/api/v1/espacos/reservas"


def com_taxa(cliente, cenario, taxa="150.00"):
    r = cliente.put(f"{ESPACOS}/{cenario['salao']['id']}", json={"taxa_uso": taxa},
                    headers=cab(cenario["sindico"]))
    assert r.status_code == 200, r.text
    return r.json()


def aprovar(cliente, cenario, reserva_id):
    r = cliente.post(f"{RESERVAS}/{reserva_id}/avaliacao", json={"aprovada": True},
                     headers=cab(cenario["sindico"]))
    assert r.status_code == 200, r.text
    return r.json()


def taxas(cliente, tok):
    return [c for c in cliente.get("/api/v1/financeiro/cobrancas", headers=cab(tok)).json()
            if c["origem"] == "uso_espaco"]


def test_a_reserva_aprovada_entra_nas_cobrancas(cliente, cenario):
    assert com_taxa(cliente, cenario)["taxa_uso"] == "150.00"
    # O morador vê a taxa antes de reservar.
    espacos = cliente.get(ESPACOS, headers=cab(cenario["ana"])).json()
    assert next(e for e in espacos if e["nome"] == "Salão de Festas")["taxa_uso"] == "150.00"

    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"])
    assert r.status_code == 201 and r.json()["taxa_uso"] == "150.00"
    assert taxas(cliente, cenario["ana"]) == []      # pendente ainda não cobra

    aprovada = aprovar(cliente, cenario, r.json()["id"])
    assert aprovada["cobranca_id"]
    [taxa] = taxas(cliente, cenario["ana"])
    assert taxa["valor"] == "150.00" and "Salão de Festas" in taxa["descricao"]
    assert taxa["vencimento"] == AMANHA
    # O vizinho não paga a festa da Ana.
    assert taxas(cliente, cenario["bruno"]) == []


def test_recusada_nao_cobra(cliente, cenario):
    com_taxa(cliente, cenario)
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"]).json()
    cliente.post(f"{RESERVAS}/{r['id']}/avaliacao", json={"aprovada": False, "motivo": "Obra"},
                 headers=cab(cenario["sindico"]))
    assert taxas(cliente, cenario["ana"]) == []


def test_espaco_sem_taxa_nao_cobra(cliente, cenario):
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"]).json()
    assert r["taxa_uso"] is None
    assert aprovar(cliente, cenario, r["id"])["cobranca_id"] is None


def test_morador_cancela_e_a_taxa_sai(cliente, cenario):
    com_taxa(cliente, cenario)
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"]).json()
    aprovar(cliente, cenario, r["id"])
    assert cliente.delete(f"{RESERVAS}/{r['id']}", headers=cab(cenario["ana"])).status_code == 200
    assert [t["status"] for t in taxas(cliente, cenario["ana"])] == ["cancelada"]


def test_sindico_cancela_e_a_taxa_sai(cliente, cenario):
    com_taxa(cliente, cenario)
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"]).json()
    aprovar(cliente, cenario, r["id"])
    c = cliente.post(f"{RESERVAS}/{r['id']}/cancelamento", json={"motivo": "Vazamento no salão"},
                     headers=cab(cenario["sindico"]))
    assert c.status_code == 200, c.text
    assert [t["status"] for t in taxas(cliente, cenario["ana"])] == ["cancelada"]


def test_espaco_inativado_e_morador_inativado(cliente, cenario):
    com_taxa(cliente, cenario)
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"]).json()
    aprovar(cliente, cenario, r["id"])
    assert cliente.delete(f"{ESPACOS}/{cenario['salao']['id']}",
                          headers=cab(cenario["sindico"])).status_code == 200
    assert [t["status"] for t in taxas(cliente, cenario["ana"])] == ["cancelada"]


def test_morador_inativado_nao_paga_a_festa_que_nao_vai_ter(cliente, cenario):
    com_taxa(cliente, cenario)
    r = reservar(cliente, cenario["bruno"], cenario["salao"]["id"]).json()
    aprovar(cliente, cenario, r["id"])
    sindico = cab(cenario["sindico"])
    bruno = next(u for u in cliente.get("/api/v1/usuarios", headers=sindico).json()
                 if u["email"] == "bruno@exemplo.com")
    assert cliente.delete(f"/api/v1/usuarios/{bruno['id']}", headers=sindico).status_code == 200
    lista = cliente.get("/api/v1/financeiro/cobrancas", headers=sindico).json()
    assert [c["status"] for c in lista if c["origem"] == "uso_espaco"] == ["cancelada"]


def test_taxa_ja_paga_fica_e_o_sindico_resolve(cliente, cenario):
    """Pagou e cancelou: a devolução é com o síndico; o sistema não apaga
    um pagamento."""
    com_taxa(cliente, cenario)
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"]).json()
    cobranca_id = aprovar(cliente, cenario, r["id"])["cobranca_id"]
    p = cliente.post(f"/api/v1/financeiro/cobrancas/{cobranca_id}/pagamentos",
                     json={"valor": "150.00", "forma": "pix"}, headers=cab(cenario["sindico"]))
    assert p.status_code == 201, p.text
    cliente.delete(f"{RESERVAS}/{r['id']}", headers=cab(cenario["ana"]))
    assert [t["status"] for t in taxas(cliente, cenario["ana"])] == ["paga"]


def test_taxa_invalida(cliente, cenario):
    for taxa in ("-1.00", "0", "100000000.00"):
        r = cliente.put(f"{ESPACOS}/{cenario['salao']['id']}", json={"taxa_uso": taxa},
                        headers=cab(cenario["sindico"]))
        assert r.status_code == 422, (taxa, r.text)
    # Sem taxa de novo: vazio.
    com_taxa(cliente, cenario)
    r = cliente.put(f"{ESPACOS}/{cenario['salao']['id']}", json={"taxa_uso": None},
                    headers=cab(cenario["sindico"]))
    assert r.status_code == 200 and r.json()["taxa_uso"] is None


def test_hoje_vence_hoje(cliente, cenario):
    """A reserva de hoje (mais tarde) vence hoje, não no passado."""
    com_taxa(cliente, cenario)
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"], "23:00", "23:30",
                 data=hoje_local().isoformat())
    if r.status_code != 201:      # já passou das 23h: não há horário hoje
        return
    aprovar(cliente, cenario, r.json()["id"])
    [taxa] = taxas(cliente, cenario["ana"])
    assert taxa["vencimento"] == hoje_local().isoformat()

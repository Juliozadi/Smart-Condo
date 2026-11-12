"""O síndico cancela uma reserva já aprovada.

Situação real: vazamento no salão, obra, evento do próprio condomínio. O
síndico só conseguia avaliar as pendentes; a aprovada ficava de pé, e o
morador chegava no dia sem saber. Agora ele cancela com um motivo, o
morador é avisado e o horário fica livre. Fica registrado quem cancelou.
"""
from __future__ import annotations

from datetime import timedelta

from app.core.tempo import hoje_local
from tests.fixtures import cab
from tests.test_reservas import cenario, reservar  # noqa: F401

URL = "/api/v1/espacos/reservas/{}/cancelamento"


def _aprovada(cliente, cenario, **extra):
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"], **extra)
    assert r.status_code == 201, r.text
    reserva = r.json()
    a = cliente.post(f"/api/v1/espacos/reservas/{reserva['id']}/avaliacao",
                     headers=cab(cenario["sindico"]), json={"aprovada": True})
    assert a.status_code == 200, a.text
    return reserva


def test_sindico_cancela_a_aprovada_com_motivo_e_libera_o_horario(cliente, cenario):
    reserva = _aprovada(cliente, cenario)
    r = cliente.post(URL.format(reserva["id"]), headers=cab(cenario["sindico"]),
                     json={"motivo": "Vazamento no salão; conserto marcado para o dia."})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cancelada"

    minha = next(x for x in cliente.get("/api/v1/espacos/reservas/minhas",
                                        headers=cab(cenario["ana"])).json()
                 if x["id"] == reserva["id"])
    assert minha["status"] == "cancelada"
    assert minha["cancelada_pelo_sindico"] is True
    assert minha["motivo_cancelamento"].startswith("Vazamento")

    # O horário voltou a ficar livre.
    outra = reservar(cliente, cenario["bruno"], cenario["salao"]["id"])
    assert outra.status_code == 201, outra.text


def test_motivo_e_obrigatorio(cliente, cenario):
    reserva = _aprovada(cliente, cenario)
    r = cliente.post(URL.format(reserva["id"]), headers=cab(cenario["sindico"]),
                     json={"motivo": "  "})
    assert r.status_code == 422


def test_pendente_se_recusa_em_vez_de_cancelar(cliente, cenario):
    pendente = reservar(cliente, cenario["ana"], cenario["salao"]["id"]).json()
    r = cliente.post(URL.format(pendente["id"]), headers=cab(cenario["sindico"]),
                     json={"motivo": "Obra no salão"})
    assert r.status_code == 409
    assert "Recusar" in r.json()["detalhe"]


def test_so_o_sindico_cancela_assim(cliente, cenario):
    reserva = _aprovada(cliente, cenario)
    for tok in (cenario["ana"], cenario["porteiro"]):
        r = cliente.post(URL.format(reserva["id"]), headers=cab(tok),
                         json={"motivo": "Quero cancelar"})
        assert r.status_code == 403


def test_reserva_de_outro_condominio_nao_e_encontrada(cliente, db, cenario):
    from tests.fixtures import CPFS, montar_condominio

    reserva = _aprovada(cliente, cenario)
    outro = montar_condominio(cliente, db, nome="Outro", cnpj="11.444.777/0001-61",
                              email_sindico="s2@exemplo.com", cpf_sindico=CPFS[4],
                              email_admin="a2@exemplo.com", cpf_admin=CPFS[5])
    r = cliente.post(URL.format(reserva["id"]), headers=cab(outro["sindico"]),
                     json={"motivo": "Obra no salão"})
    assert r.status_code == 404


def test_a_que_ja_aconteceu_nao_se_cancela(cliente, cenario, db):
    from sqlalchemy import update

    from app.models.espaco import Reserva

    reserva = _aprovada(cliente, cenario)
    db.execute(update(Reserva).where(Reserva.id == reserva["id"])
               .values(data=hoje_local() - timedelta(days=3)))
    db.commit()
    r = cliente.post(URL.format(reserva["id"]), headers=cab(cenario["sindico"]),
                     json={"motivo": "Obra no salão"})
    assert r.status_code == 409


def test_cancelada_pelo_proprio_morador_nao_aparece_como_do_sindico(cliente, cenario):
    reserva = reservar(cliente, cenario["ana"], cenario["salao"]["id"]).json()
    assert cliente.delete(f"/api/v1/espacos/reservas/{reserva['id']}",
                          headers=cab(cenario["ana"])).status_code == 200
    minha = next(x for x in cliente.get("/api/v1/espacos/reservas/minhas",
                                        headers=cab(cenario["ana"])).json()
                 if x["id"] == reserva["id"])
    assert minha["cancelada_pelo_sindico"] is False
    assert minha["motivo_cancelamento"] is None


def test_inativar_o_espaco_explica_o_cancelamento(cliente, cenario):
    reserva = _aprovada(cliente, cenario)
    assert cliente.delete(f"/api/v1/espacos/{cenario['salao']['id']}",
                          headers=cab(cenario["sindico"])).status_code == 200
    minha = next(x for x in cliente.get("/api/v1/espacos/reservas/minhas",
                                        headers=cab(cenario["ana"])).json()
                 if x["id"] == reserva["id"])
    assert minha["status"] == "cancelada"
    assert minha["cancelada_pelo_sindico"] is True
    assert "inativado" in minha["motivo_cancelamento"]

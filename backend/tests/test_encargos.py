"""Multa e juros por atraso na cobrança.

Situação real: o boleto venceu e o morador paga dez dias depois. O
Código Civil (art. 1.336, § 1º) permite multa de até 2% sobre o débito e
juros de 1% ao mês, salvo outro valor na convenção. O sistema cobrava o
mesmo valor no dia do vencimento e meses depois: quem atrasava pagava
igual a quem pagava em dia.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from app.core.tempo import hoje_local
from app.services import notificacao
from tests.fixtures import cab
from tests.test_financeiro import cenario, gerar_cobranca  # noqa: F401

URL = "/api/v1/financeiro"


def _vencida_ha(cliente, cenario, dias, valor="300.00"):
    vencimento = hoje_local() - timedelta(days=dias)
    r = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"], valor=valor,
                       competencia=vencimento.replace(day=1).isoformat(),
                       vencimento=vencimento.isoformat())
    assert r.status_code == 201, r.text
    return r.json()


def _da_ana(cliente, cenario, cobranca_id):
    return next(c for c in cliente.get(f"{URL}/cobrancas", headers=cab(cenario["ana"])).json()
                if c["id"] == cobranca_id)


def _pagar(cliente, tok, cobranca_id, valor, **extra):
    return cliente.post(f"{URL}/cobrancas/{cobranca_id}/pagamentos", headers=cab(tok),
                        json={"valor": valor, "forma": "pix", **extra})


def test_cobranca_vencida_mostra_multa_e_juros(cliente, cenario):
    c = _vencida_ha(cliente, cenario, 10)
    c = _da_ana(cliente, cenario, c["id"])
    # Padrão do Código Civil: multa de 2% e juros de 1% ao mês, por dia.
    assert c["dias_atraso"] == 10
    assert Decimal(c["multa"]) == Decimal("6.00")
    assert Decimal(c["juros"]) == Decimal("1.00")
    assert Decimal(c["total_atualizado"]) == Decimal("307.00")


def test_em_dia_nao_tem_encargo(cliente, cenario):
    c = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"],
                       vencimento=hoje_local().isoformat()).json()
    c = _da_ana(cliente, cenario, c["id"])
    assert c["dias_atraso"] == 0 and Decimal(c["multa"]) == 0 and Decimal(c["juros"]) == 0
    assert Decimal(c["total_atualizado"]) == Decimal(c["valor"])


def test_pagar_o_total_atualizado_quita(cliente, cenario, monkeypatch):
    avisos = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: avisos.append(mensagem))
    c = _vencida_ha(cliente, cenario, 10)
    r = _pagar(cliente, cenario["ana"], c["id"], "307.00")
    assert r.status_code == 201, r.text
    assert Decimal(r.json()["encargos"]) == Decimal("7.00")
    c = _da_ana(cliente, cenario, c["id"])
    assert c["status"] == "paga" and Decimal(c["total_pago"]) == Decimal("300.00")
    assert Decimal(c["total_atualizado"]) == 0
    assert "multa e juros" in avisos[-1]


def test_pagamento_parcial_abate_primeiro_os_encargos(cliente, cenario):
    """Código Civil, art. 354: havendo juros, o pagamento imputa-se
    primeiro neles. A multa entra uma vez sobre cada parte do débito."""
    c = _vencida_ha(cliente, cenario, 10)
    r = _pagar(cliente, cenario["ana"], c["id"], "300.00")
    assert r.status_code == 201, r.text
    assert Decimal(r.json()["encargos"]) == Decimal("7.00")
    c = _da_ana(cliente, cenario, c["id"])
    assert c["status"] == "vencida" and Decimal(c["total_pago"]) == Decimal("293.00")
    # Sobre os R$ 7,00 que faltam: multa de 0,14 e juros de 0,02.
    assert Decimal(c["total_atualizado"]) == Decimal("7.16")
    assert _pagar(cliente, cenario["ana"], c["id"], "7.16").status_code == 201
    assert _da_ana(cliente, cenario, c["id"])["status"] == "paga"


def test_pagamento_menor_que_os_encargos_e_recusado(cliente, cenario):
    c = _vencida_ha(cliente, cenario, 10)
    r = _pagar(cliente, cenario["ana"], c["id"], "5.00")
    assert r.status_code == 400
    assert "multa e os juros" in r.json()["detalhe"]


def test_pagamento_acima_do_total_atualizado_e_recusado(cliente, cenario):
    c = _vencida_ha(cliente, cenario, 10)
    r = _pagar(cliente, cenario["ana"], c["id"], "307.01")
    assert r.status_code == 400
    assert "307.00" in r.json()["detalhe"]


def test_sindico_define_os_percentuais(cliente, cenario):
    r = cliente.get(f"{URL}/encargos", headers=cab(cenario["ana"]))
    assert r.status_code == 200
    assert Decimal(r.json()["multa_atraso"]) == Decimal("2.00")
    assert Decimal(r.json()["juros_mensais"]) == Decimal("1.00")

    r = cliente.put(f"{URL}/encargos", headers=cab(cenario["sindico"]),
                    json={"multa_atraso": "0", "juros_mensais": "0.5"})
    assert r.status_code == 200, r.text
    c = _vencida_ha(cliente, cenario, 30)
    c = _da_ana(cliente, cenario, c["id"])
    assert Decimal(c["multa"]) == 0 and Decimal(c["juros"]) == Decimal("1.50")


@pytest.mark.parametrize("dados", [
    {"multa_atraso": "2.01", "juros_mensais": "1"},
    {"multa_atraso": "2", "juros_mensais": "1.01"},
    {"multa_atraso": "-1", "juros_mensais": "1"},
    {"multa_atraso": "2"},
])
def test_percentuais_fora_da_lei_sao_recusados(cliente, cenario, dados):
    r = cliente.put(f"{URL}/encargos", headers=cab(cenario["sindico"]), json=dados)
    assert r.status_code == 422, r.text


def test_so_o_sindico_muda_os_percentuais(cliente, cenario):
    corpo = {"multa_atraso": "0", "juros_mensais": "0"}
    assert cliente.put(f"{URL}/encargos", headers=cab(cenario["ana"]),
                       json=corpo).status_code == 403
    assert cliente.put(f"{URL}/encargos", headers=cab(cenario["porteiro"]),
                       json=corpo).status_code == 403


def test_sindico_dispensa_os_encargos_num_acordo(cliente, cenario):
    c = _vencida_ha(cliente, cenario, 10)
    r = _pagar(cliente, cenario["ana"], c["id"], "300.00", dispensar_encargos=True)
    assert r.status_code == 403
    r = _pagar(cliente, cenario["sindico"], c["id"], "300.00", dispensar_encargos=True)
    assert r.status_code == 201, r.text
    assert Decimal(r.json()["encargos"]) == 0
    assert _da_ana(cliente, cenario, c["id"])["status"] == "paga"
    # A dispensa fica registrada, com quem dispensou e quanto.
    do_sindico = next(x for x in cliente.get(f"{URL}/cobrancas",
                                             headers=cab(cenario["sindico"])).json()
                      if x["id"] == c["id"])
    assert do_sindico["ultima_alteracao"]["descricao"] == "Dispensou R$ 7.00 de multa e juros"


def test_dispensa_no_pagamento_parcial_vale_so_para_o_que_foi_pago(cliente, cenario):
    """R$ 100,00 dos R$ 300,00, sem encargos: o registro diz quanto foi
    dispensado sobre esses R$ 100,00, e o resto continua com multa e juros."""
    c = _vencida_ha(cliente, cenario, 10)
    r = _pagar(cliente, cenario["sindico"], c["id"], "100.00", dispensar_encargos=True)
    assert r.status_code == 201, r.text
    do_sindico = next(x for x in cliente.get(f"{URL}/cobrancas",
                                             headers=cab(cenario["sindico"])).json()
                      if x["id"] == c["id"])
    # Sobre R$ 100,00: multa de 2,00 e juros de 0,33.
    assert do_sindico["ultima_alteracao"]["descricao"] == "Dispensou R$ 2.33 de multa e juros"
    assert Decimal(do_sindico["total_pago"]) == Decimal("100.00")
    # Sobre os R$ 200,00 que faltam: multa de 4,00 e juros de 0,67.
    assert Decimal(do_sindico["total_atualizado"]) == Decimal("204.67")


def test_resumo_conta_os_encargos_recebidos(cliente, cenario):
    c = _vencida_ha(cliente, cenario, 10)
    _pagar(cliente, cenario["ana"], c["id"], "307.00")
    r = cliente.get(f"{URL}/resumo", headers=cab(cenario["sindico"])).json()
    assert Decimal(r["total_recebido"]) == Decimal("307.00")


def test_cobranca_com_pagamento_nao_e_cancelada(cliente, cenario):
    """Mesmo quando o que entrou foram só multa e juros, entrou dinheiro."""
    c = _vencida_ha(cliente, cenario, 10)
    _pagar(cliente, cenario["ana"], c["id"], "7.00")
    r = cliente.post(f"{URL}/cobrancas/{c['id']}/cancelamento", headers=cab(cenario["sindico"]),
                     json={"motivo": "Lançada errada"})
    assert r.status_code == 409

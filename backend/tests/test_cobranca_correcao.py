"""Correção e cancelamento de cobrança pelo síndico.

A cobrança lançada errada não tinha correção: a unidade ficava em atraso
para sempre. Nada é apagado — a cancelada fica guardada, com o motivo e
quem cancelou, e não impede lançar a certa no mesmo mês.
"""
from __future__ import annotations

from tests.fixtures import cab
from tests.test_financeiro import COMPETENCIA, cenario, gerar_cobranca  # noqa: F401


def url(c):
    return f"/api/v1/financeiro/cobrancas/{c['id']}"


def historico(cliente, admin_tok, cobranca_id):
    return cliente.get("/api/v1/admin/historico", headers=cab(admin_tok), params={
        "entidade": "cobranca", "entidade_id": cobranca_id}).json()


def test_corrigir_o_valor_e_o_historico_mostra_quem(cliente, cenario):
    c = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"], valor="3200.00").json()
    r = cliente.put(url(c), headers=cab(cenario["sindico"]), json={"valor": "320.00"})
    assert r.status_code == 200, r.text
    assert r.json()["valor"] == "320.00"
    assert r.json()["ultima_alteracao"]["descricao"] == "Alterou o valor"
    lista = cliente.get("/api/v1/financeiro/cobrancas", headers=cab(cenario["sindico"])).json()
    assert next(x for x in lista if x["id"] == c["id"])["ultima_alteracao"]["acao"] == "editou"
    # O morador não recebe o histórico.
    da_ana = cliente.get("/api/v1/financeiro/cobrancas", headers=cab(cenario["ana"])).json()
    assert all(x["ultima_alteracao"] is None for x in da_ana)


def test_valor_nao_fica_abaixo_do_que_ja_foi_pago_e_quitar_fecha(cliente, cenario):
    c = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"], valor="320.00").json()
    cliente.post(url(c) + "/pagamentos", headers=cab(cenario["ana"]),
                 json={"valor": "200.00", "forma": "pix"})
    assert cliente.put(url(c), headers=cab(cenario["sindico"]),
                       json={"valor": "150.00"}).status_code == 409
    r = cliente.put(url(c), headers=cab(cenario["sindico"]), json={"valor": "200.00"})
    assert r.status_code == 200 and r.json()["status"] == "paga"
    # Paga não se edita mais.
    assert cliente.put(url(c), headers=cab(cenario["sindico"]),
                       json={"descricao": "Outra"}).status_code == 409


def test_cancelar_guarda_e_libera_o_mes_para_a_correta(cliente, cenario):
    errada = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"]).json()
    assert gerar_cobranca(cliente, cenario["sindico"], cenario["u204"]).status_code == 409
    r = cliente.post(url(errada) + "/cancelamento", headers=cab(cenario["sindico"]),
                     json={"motivo": "Lançada na unidade errada"})
    assert r.status_code == 200 and r.json()["status"] == "cancelada"
    assert cliente.post(url(errada) + "/cancelamento", headers=cab(cenario["sindico"]),
                        json={"motivo": "De novo"}).status_code == 409
    # Nada some: continua na lista, e o mês aceita a cobrança certa.
    lista = cliente.get("/api/v1/financeiro/cobrancas", headers=cab(cenario["sindico"])).json()
    assert any(x["id"] == errada["id"] and x["status"] == "cancelada" for x in lista)
    assert gerar_cobranca(cliente, cenario["sindico"], cenario["u204"]).status_code == 201
    # Cancelada não recebe pagamento.
    assert cliente.post(url(errada) + "/pagamentos", headers=cab(cenario["ana"]),
                        json={"valor": "10.00", "forma": "pix"}).status_code == 409


def test_nao_cancela_cobranca_com_pagamento(cliente, cenario):
    c = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"]).json()
    cliente.post(url(c) + "/pagamentos", headers=cab(cenario["ana"]),
                 json={"valor": "10.00", "forma": "pix"})
    r = cliente.post(url(c) + "/cancelamento", headers=cab(cenario["sindico"]),
                     json={"motivo": "Engano"})
    assert r.status_code == 409


def test_so_o_sindico_corrige_e_cancela(cliente, cenario):
    c = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"]).json()
    for tok in (cenario["ana"], cenario["porteiro"]):
        assert cliente.put(url(c), headers=cab(tok), json={"valor": "1.00"}).status_code == 403
        assert cliente.post(url(c) + "/cancelamento", headers=cab(tok),
                            json={"motivo": "Engano"}).status_code == 403
    assert cliente.put(url(c), headers=cab(cenario["sindico"]),
                       json={"valor": None}).status_code == 422


def test_sindico_registra_pagamento_recebido_fora_do_app(cliente, cenario, monkeypatch):
    """O morador pagou o boleto no banco: o síndico registra, a cobrança
    fecha, e o aviso vai para o morador — não para o próprio síndico."""
    from app.services import notificacao
    enviados = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: enviados.append(destino))
    c = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"], valor="320.00").json()
    r = cliente.post(url(c) + "/pagamentos", headers=cab(cenario["sindico"]),
                     json={"valor": "320.00", "forma": "boleto", "observacao": "Pago no banco"})
    assert r.status_code == 201, r.text
    assert enviados == ["ana@exemplo.com"]
    lista = cliente.get("/api/v1/financeiro/cobrancas", headers=cab(cenario["ana"])).json()
    assert next(x for x in lista if x["id"] == c["id"])["status"] == "paga"

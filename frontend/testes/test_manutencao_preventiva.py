"""Manutenção preventiva: o síndico cadastra um plano já vencido, registra
a realização com o custo lançado nas despesas, vê o prazo renovado e o
histórico, e remove o plano."""
from __future__ import annotations

import random
from datetime import date, timedelta

from conftest import abrir, ir, token_da_aba

API = "http://127.0.0.1:8000/api/v1"


def test_plano_realizacao_e_historico(navegador):
    nome = f"Limpeza das calhas, teste {random.randint(1000, 9999)}"
    ctx, pg = abrir(navegador, papel="sindico")
    tok = token_da_aba(pg)
    despesa_id = None
    try:
        ir(pg, "pages/sindico/preventiva.html", 1500)
        # A demonstração já traz a recarga dos extintores vencida.
        assert int(pg.inner_text("#totVencidas")) >= 1
        pg.fill("#pNome", nome)
        pg.fill("#pPeriodicidade", "6")
        pg.fill("#pVencimento", (date.today() - timedelta(days=3)).isoformat())
        pg.fill("#pFornecedor", "Calhas Campo Grande")
        pg.click("#btnSalvarPlano")
        pg.wait_for_selector("#erroPlano.sucesso", timeout=8000)
        cartao = pg.locator(".plano", has_text=nome)
        cartao.get_by_text("Venceu há", exact=False).wait_for(timeout=8000)

        cartao.get_by_role("button", name=f"Registrar realização de {nome}").click()
        cartao.locator("input[type=number]").fill("250")
        cartao.locator("input[type=checkbox]").check()
        cartao.get_by_role("button", name="Salvar").click()
        cartao = pg.locator(".plano", has_text=nome)
        cartao.get_by_text("Em dia", exact=True).wait_for(timeout=8000)

        cartao.get_by_role("button", name=f"Histórico de {nome}").click()
        cartao.get_by_text("lançado nas despesas", exact=False).wait_for(timeout=8000)
        despesa = next(d for d in pg.request.get(f"{API}/financeiro/despesas", headers=tok).json()
                       if nome in d["descricao"])
        despesa_id = despesa["id"]
        assert despesa["valor"] == "250.00" and despesa["categoria"] == "manutencao"

        pg.once("dialog", lambda d: d.accept())
        cartao.get_by_role("button", name=f"Remover {nome}").click()
        pg.locator(".plano", has_text=nome).wait_for(state="detached", timeout=8000)
        assert pg.erros == []
    finally:
        # A despesa de teste sai do balancete (cancelada), como faria o síndico.
        if despesa_id:
            pg.request.post(f"{API}/financeiro/despesas/{despesa_id}/cancelamento", headers=tok,
                            data={"motivo": "Lançada pelo teste automatizado"})
        ctx.close()

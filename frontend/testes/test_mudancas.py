"""Agendamento de mudança: o morador pede pela tela, o síndico aprova, e a
portaria vê a mudança aprovada."""
from __future__ import annotations

from datetime import date, timedelta

from conftest import FRONT, abrir, ir, token_da_aba

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def dia_util(a_partir=20):
    """Um dia de semana longe das mudanças de demonstração."""
    dia = date.today() + timedelta(days=a_partir)
    while dia.isoweekday() > 5:
        dia += timedelta(days=1)
    return dia


def test_morador_pede_sindico_aprova_e_portaria_ve(navegador):
    dia = dia_util()
    rotulo = dia.strftime("%d/%m/%Y")
    ctx, pg = abrir(navegador, papel="morador")
    morador = token_da_aba(pg)
    try:
        ir(pg, "pages/morador/mudancas.html", 1500)
        # As regras do regimento estão na tela.
        pg.get_by_text("Segunda a sexta, das 8h às 18h.").wait_for(timeout=8000)
        # Domingo: a tela avisa antes de pedir.
        domingo = dia + timedelta(days=7 - dia.isoweekday())
        pg.fill("#mData", domingo.isoformat())
        pg.dispatch_event("#mData", "change")
        pg.get_by_text("Nesse dia não há mudança").wait_for(timeout=4000)

        pg.select_option("#mTipo", "chegada")
        pg.fill("#mData", dia.isoformat())
        pg.dispatch_event("#mData", "change")
        pg.get_by_text("Nenhuma outra mudança marcada.").wait_for(timeout=8000)
        pg.fill("#mInicio", "13:00")
        pg.fill("#mFim", "17:00")
        pg.fill("#mEmpresa", "Mudanças do Teste")
        pg.click("#formMudanca button[type=submit]")
        pg.wait_for_selector("#erroMudanca.sucesso", timeout=8000)
        # Rodado de novo, o teste encontra os cancelados de antes: vale o pendente.
        cartao = pg.locator("#listaMudancas .mudanca", has_text="Mudanças do Teste").filter(
            has_text="Aguardando o síndico")
        cartao.wait_for(timeout=8000)
        assert pg.erros == []
        ctx.close()

        ctx, pg = abrir(navegador, papel="sindico")
        ir(pg, "pages/sindico/mudancas.html", 1500)
        cartao = pg.locator("#listaPendentes .mudanca", has_text="Mudanças do Teste")
        cartao.wait_for(timeout=8000)
        assert "Apto 204" in cartao.inner_text()
        cartao.get_by_role("button", name=f"Aprovar a mudança do apto 204 em {rotulo}").click()
        pg.locator("#listaAprovadas .mudanca", has_text="Mudanças do Teste").wait_for(timeout=8000)
        assert pg.erros == []
        ctx.close()

        ctx, pg = abrir(navegador, papel="porteiro")
        ir(pg, "pages/porteiro/mudancas.html", 1500)
        cartao = pg.locator("#listaProximas .mudanca", has_text="Mudanças do Teste")
        cartao.wait_for(timeout=8000)
        assert "13:00 – 17:00" in cartao.inner_text()
        assert pg.erros == []
    finally:
        for m in pg.request.get(f"{API}/mudancas", headers=morador).json():
            if m["empresa"] == "Mudanças do Teste" and m["status"] in ("pendente", "aprovada"):
                pg.request.post(f"{API}/mudancas/{m['id']}/cancelamento", headers=morador,
                                data={})
        ctx.close()


PADRAO = {"antecedencia_minima_dias": 2,
          "horarios": {**{str(d): {"inicio": "08:00", "fim": "18:00"} for d in range(1, 6)},
                       "6": {"inicio": "08:00", "fim": "12:00"}}}


def test_sindico_muda_as_regras_e_o_morador_ve(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    sindico = token_da_aba(pg)
    try:
        ir(pg, "pages/sindico/mudancas.html", 1500)
        pg.click("#btnEditarRegras")
        pg.fill("#rAntecedencia", "4")
        domingo = pg.locator(".regra-dia[data-dia='7']")
        domingo.locator(".regra-permite").check()
        pg.fill("#rIni7", "10:00")
        pg.fill("#rFim7", "14:00")
        # Fim antes do início não sai da tela.
        pg.fill("#rFim1", "07:00")
        pg.click("#formRegras button[type=submit]")
        pg.get_by_text("o fim do horário precisa ser depois do início").wait_for(timeout=4000)
        pg.fill("#rFim1", "18:00")
        pg.click("#formRegras button[type=submit]")
        pg.wait_for_selector("#erroRegras.sucesso", timeout=8000)
        pg.get_by_text("Domingo, das 10h às 14h.").wait_for(timeout=4000)
        assert pg.erros == []
        ctx.close()

        ctx, pg = abrir(navegador, papel="morador")
        ir(pg, "pages/morador/mudancas.html", 1500)
        pg.get_by_text("Peça com pelo menos 4 dias de antecedência").wait_for(timeout=8000)
        pg.get_by_text("Domingo, das 10h às 14h.").wait_for(timeout=4000)
        assert pg.erros == []
    finally:
        pg.request.put(f"{API}/mudancas/regras", headers=sindico, data=PADRAO)
        ctx.close()

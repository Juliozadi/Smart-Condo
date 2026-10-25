"""Taxa de uso dos espaços: o morador vê a taxa antes de reservar, e a da
reserva aprovada aparece nas cobranças do apartamento; o síndico define
a taxa no cadastro do espaço."""
from __future__ import annotations

from conftest import FRONT, abrir, ir, token_da_aba

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def test_morador_ve_a_taxa_e_a_cobranca(navegador):
    ctx, pg = abrir(navegador, largura=420, papel="morador")
    try:
        ir(pg, "pages/morador/reservas.html", 1500)
        valor = pg.locator("#reserv_espacoDesejado option", has_text="Salão de Festas") \
            .get_attribute("value")
        pg.select_option("#reserv_espacoDesejado", value=valor)
        pg.locator("#regrasEspaco", has_text="taxa de uso de R$ 150,00").wait_for(timeout=4000)
        # A festa aprovada da demonstração já tem a taxa.
        pg.get_by_text("taxa de uso R$ 150,00").first.wait_for(timeout=8000)
        ir(pg, "pages/morador/financeiro.html", 1500)
        pg.get_by_text("Uso do espaço Salão de Festas").first.wait_for(timeout=8000)
        assert pg.erros == []
    finally:
        ctx.close()


def test_sindico_define_a_taxa_do_espaco(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    sindico = token_da_aba(pg)
    churrasqueira = next(e for e in pg.request.get(f"{API}/espacos", headers=sindico).json()
                         if e["nome"] == "Churrasqueira 1")
    try:
        ir(pg, "pages/sindico/reservas.html", 1500)
        pg.get_by_role("button", name="Editar Churrasqueira 1").click()
        pg.fill("#eTaxa", "75")
        pg.click("#btnSalvar")
        pg.get_by_text("taxa de uso R$ 75,00").first.wait_for(timeout=8000)
        assert pg.erros == []
    finally:
        pg.request.put(f"{API}/espacos/{churrasqueira['id']}", headers=sindico,
                       data={"taxa_uso": "60.00"})
        ctx.close()

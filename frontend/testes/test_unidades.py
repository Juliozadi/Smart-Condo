"""Unidades e vagas: o síndico define as vagas de garagem pela tela.

As vagas somam a capacidade do estacionamento que a portaria acompanha,
e nenhuma tela as preenchia.
"""
from __future__ import annotations

from conftest import FRONT, abrir, ir

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def vagas_totais(pg):
    r = pg.request.post(f"{API}/auth/login",
                        data={"email": "porteiro@smartcondo.com", "senha": "smartcondo123"})
    cab = {"Authorization": "Bearer " + r.json()["access_token"]}
    return pg.request.get(f"{API}/veiculos/ocupacao", headers=cab).json()["vagas_totais"]


def test_sindico_muda_as_vagas_e_a_portaria_ve(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    ir(pg, "pages/sindico/moradores.html", 1500)
    antes = vagas_totais(pg)
    linha = pg.locator("#tabelaUnidades .table-row", has_text="302")
    vagas = int(linha.locator("span").nth(2).inner_text())
    linha.get_by_role("button", name="Editar unidade 302").click()
    # Número e bloco não mudam depois do cadastro.
    assert pg.is_disabled("#uNumero") and pg.input_value("#uNumero") == "302"
    pg.fill("#uVagas", str(vagas + 1))
    pg.click("#formUnidade button[type=submit]")
    pg.wait_for_timeout(1200)
    linha = pg.locator("#tabelaUnidades .table-row", has_text="302")
    assert "Editado por Roberto Nascimento em" in linha.inner_text()
    assert vagas_totais(pg) == antes + 1
    # Volta como estava, para não mexer nos outros testes.
    linha.get_by_role("button", name="Editar unidade 302").click()
    pg.fill("#uVagas", str(vagas))
    pg.click("#formUnidade button[type=submit]")
    pg.wait_for_timeout(1000)
    assert vagas_totais(pg) == antes
    assert pg.erros == []
    ctx.close()

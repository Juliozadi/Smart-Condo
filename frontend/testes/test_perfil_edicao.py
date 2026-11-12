"""Editar o próprio perfil: salvar mostra o resultado e devolve o botão.

O aviso de "Perfil atualizado" chamava uma função que já não existia: o
dado era salvo, mas a tela travava com o botão desabilitado e sem dizer
nada, e o erro de carregar o perfil também não aparecia."""
from __future__ import annotations

import pytest

from conftest import abrir, ir, token_da_aba

API = "http://127.0.0.1:8000/api/v1"


@pytest.mark.parametrize("papel", ["morador", "porteiro", "sindico"])
def test_salvar_o_perfil(navegador, papel):
    ctx, pg = abrir(navegador, largura=420, papel=papel)
    tok = token_da_aba(pg)
    original = pg.request.get(f"{API}/auth/eu", headers=tok).json()
    try:
        ir(pg, f"pages/{papel}/perfil.html", 1500)
        pg.get_by_role("button", name="Editar Perfil").click()

        # Nome curto demais: avisa e não sai da edição.
        pg.fill("#edit-nome", "Jo")
        pg.get_by_role("button", name="Salvar Alterações").click()
        assert "pelo menos 3 caracteres" in pg.inner_text("#avisoPerfil")
        assert pg.is_visible("#editActions")

        pg.fill("#edit-nome", original["nome"])
        pg.fill("#edit-tel", "(67) 98888-7766")
        salvar = pg.get_by_role("button", name="Salvar Alterações")
        salvar.click()
        pg.wait_for_selector("#avisoPerfil.sucesso", timeout=8000)
        assert pg.is_visible("#viewActions")
        assert "(67) 98888-7766" in pg.inner_text("#val-tel")
        # Editar de novo: o botão voltou a funcionar e o aviso antigo saiu.
        pg.get_by_role("button", name="Editar Perfil").click()
        assert salvar.is_enabled()
        assert pg.inner_text("#avisoPerfil") == ""
        assert pg.erros == []
    finally:
        pg.request.patch(f"{API}/usuarios/eu", headers=tok,
                         data={"nome": original["nome"], "telefone": original["telefone"]})
        ctx.close()

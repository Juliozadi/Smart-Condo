"""Painel do administrador: vários administradores, quem editou o quê e
nada apagado (pedidos do grupo)."""
from __future__ import annotations

import random

from conftest import FRONT, abrir, ir

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def token_admin(pg):
    r = pg.request.post(f"{API}/auth/login",
                        data={"email": "admin@smartcondo.com", "senha": "smartcondo123"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def cpf_valido() -> str:
    base = [random.randint(0, 9) for _ in range(9)]
    for _ in range(2):
        soma = sum(d * p for d, p in zip(base, range(len(base) + 1, 1, -1)))
        base.append(0 if soma % 11 < 2 else 11 - soma % 11)
    return "".join(map(str, base))


def test_admin_cadastra_outro_admin_pela_tela(navegador):
    ctx, pg = abrir(navegador, papel="admin")
    ir(pg, "pages/admin/usuarios.html", 1200)
    pg.click("#btnNovoUsuario")
    pg.select_option("#uPapel", "admin")
    # Administrador não pertence a condomínio: o campo some.
    assert not pg.is_visible("#uCondominio")
    sufixo = random.randint(1000, 9999)
    nome = f"Carla Admin {sufixo}"
    email = f"carla{sufixo}@smartcondo.com"
    pg.fill("#uNome", nome)
    pg.fill("#uEmail", email)
    pg.fill("#uCpf", cpf_valido())
    pg.fill("#uTelefone", "67999998888")
    pg.fill("#uSenha", "senhaforte123")
    pg.click("#btnSalvar")
    linha = pg.locator("#tabela .table-row", has_text=nome)
    linha.wait_for(timeout=8000)
    assert "Administrador" in linha.inner_text()
    assert "Toda a plataforma" in linha.inner_text()
    assert "Criado por Administrador SmartCondo em" in linha.inner_text()
    # O novo administrador entra.
    r = pg.request.post(f"{API}/auth/login", data={"email": email, "senha": "senhaforte123"})
    assert r.ok and r.json()["usuario"]["papel"] == "admin"
    # E o próprio usuário não tem botão de se inativar.
    eu = pg.locator("#tabela .table-row", has_text="admin@smartcondo.com")
    assert eu.locator("[data-acao=inativar]").count() == 0
    assert pg.erros == []
    ctx.close()


def test_edicao_mostra_quem_editou_na_linha_e_no_historico(navegador):
    ctx, pg = abrir(navegador, papel="admin")
    ir(pg, "pages/admin/condominios.html", 1200)
    linha = pg.locator("#tabela .table-row", has_text="Residencial das Palmeiras")
    assert "Criado por Administrador SmartCondo" in linha.inner_text()
    linha.locator("[data-acao=editar]").click()
    pg.fill("#cTelefone", f"(67) 3{random.randint(100, 999)}-{random.randint(1000, 9999)}")
    pg.click("#btnSalvar")
    pg.wait_for_timeout(1200)
    linha = pg.locator("#tabela .table-row", has_text="Residencial das Palmeiras")
    assert "Editado por Administrador SmartCondo em" in linha.inner_text()
    linha.locator("[data-acao=editar]").click()
    historico = pg.locator("#historicoLista li")
    historico.first.wait_for(timeout=5000)
    textos = historico.all_inner_texts()
    assert "Alterou o telefone" in textos[0]
    assert textos[-1].startswith("Criado por Administrador SmartCondo")
    assert pg.erros == []
    ctx.close()


def test_inativar_e_reativar_condominio_pela_tela(navegador):
    ctx, pg = abrir(navegador, papel="admin")
    cab = token_admin(pg)
    nome = f"Edifício Teste {random.randint(1000, 9999)}"
    r = pg.request.post(f"{API}/admin/condominios", headers=cab, data={
        "nome": nome, "cnpj": "04.252.011/0001-10", "cep": "79000-000",
        "logradouro": "Rua das Flores", "numero": "10", "bairro": "Centro",
        "cidade": "Campo Grande", "uf": "MS"})
    if r.status == 409:   # já criado numa execução anterior
        existente = next(c for c in pg.request.get(f"{API}/admin/condominios", headers=cab).json()
                         if c["cnpj"] == "04252011000110")
        if existente["inativo"]:
            pg.request.post(f"{API}/admin/condominios/{existente['id']}/reativacao", headers=cab)
        nome = existente["nome"]
    ir(pg, "pages/admin/condominios.html", 1200)
    avisos = []
    pg.once("dialog", lambda d: (avisos.append(d.message), d.accept()))
    pg.locator("#tabela .table-row", has_text=nome).locator("[data-acao=inativar]").click()
    pg.wait_for_timeout(1200)
    assert "Nada é apagado" in avisos[0]
    linha = pg.locator("#tabela .table-row", has_text=nome)
    assert "Inativo" in linha.inner_text()
    assert "Inativado por Administrador SmartCondo" in linha.inner_text()
    pg.once("dialog", lambda d: d.accept())
    linha.locator("[data-acao=reativar]").click()
    pg.wait_for_timeout(1200)
    linha = pg.locator("#tabela .table-row", has_text=nome)
    assert "Inativo" not in linha.inner_text()
    assert "Reativado por Administrador SmartCondo" in linha.inner_text()
    assert pg.erros == []
    ctx.close()


def test_mascaras_formatam_enquanto_digita(navegador):
    """O CNPJ virava "11.222.33300/0181" e todo telefone fixo ganhava o
    formato de celular, "(67) 37017-071". E, ao editar, CNPJ e CEP abriam
    crus, sem a máscara."""
    ctx, pg = abrir(navegador, papel="admin")
    ir(pg, "pages/admin/condominios.html", 1200)
    pg.click("#btnNovoCondominio")
    casos = [
        ("#cCnpj", "11222333000181", "11.222.333/0001-81"),
        ("#cTelefone", "6737017071", "(67) 3701-7071"),
        ("#cTelefone", "67999998888", "(67) 99999-8888"),
        ("#cCep", "79000000", "79000-000"),
    ]
    for campo, digitos, esperado in casos:
        pg.fill(campo, "")
        pg.type(campo, digitos)
        assert pg.input_value(campo) == esperado, campo
    pg.keyboard.press("Escape")
    linha = pg.locator("#tabela .table-row", has_text="Residencial das Palmeiras")
    linha.locator("[data-acao=editar]").click()
    assert pg.input_value("#cCnpj") == "11.222.333/0001-81"
    assert pg.input_value("#cCep") == "79000-000"
    assert pg.erros == []
    ctx.close()

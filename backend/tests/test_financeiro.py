"""Testes do financeiro e dos comunicados.

Documentação, seção 6 (cobrança na data escolhida, formas de pagamento e
aviso ao síndico) e seções 11.5.4 / 11.6.4 (comunicados).
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from tests.fixtures import (
    CPFS, cab, cadastrar_morador, cadastrar_porteiro, cadastrar_sindico, criar_condominio,
)

COMPETENCIA = date.today().replace(day=1).isoformat()


@pytest.fixture
def cenario(cliente):
    tok_sindico = cadastrar_sindico(cliente)
    cond = criar_condominio(cliente, tok_sindico)
    _, tok_ana = cadastrar_morador(
        cliente, tok_sindico, cond["id"], email="ana@exemplo.com", cpf=CPFS[1], unidade="204"
    )
    _, tok_bruno = cadastrar_morador(
        cliente, tok_sindico, cond["id"], email="bruno@exemplo.com", cpf=CPFS[3], unidade="301"
    )
    _, tok_porteiro = cadastrar_porteiro(cliente, tok_sindico, cond["id"], cpf=CPFS[2])

    unidades = cliente.get("/api/v1/condominios/meu/unidades", headers=cab(tok_sindico)).json()
    return {
        "cond": cond, "sindico": tok_sindico, "ana": tok_ana, "bruno": tok_bruno,
        "porteiro": tok_porteiro,
        "u204": next(u for u in unidades if u["numero"] == "204")["id"],
        "u301": next(u for u in unidades if u["numero"] == "301")["id"],
    }


FUTURO = (date.today() + timedelta(days=7)).isoformat()


def gerar_cobranca(cliente, tok, unidade_id, valor="320.00", **extra):
    corpo = {
        "unidade_id": unidade_id, "competencia": COMPETENCIA,
        "descricao": "Taxa de condomínio", "valor": valor,
        # Vencimento explicito por padrao, para o resultado nao mudar
        # conforme o dia em que a suite roda.
        "vencimento": FUTURO,
    }
    corpo.update(extra)
    return cliente.post("/api/v1/financeiro/cobrancas", json=corpo, headers=cab(tok))


# ── Preferência de cobrança (seção 6) ────────────────────────────────
def test_preferencia_tem_padrao_sem_gravar(cliente, cenario):
    r = cliente.get("/api/v1/financeiro/preferencia", headers=cab(cenario["ana"]))
    assert r.status_code == 200
    assert r.json()["dia_vencimento"] == 10
    assert r.json()["forma_preferida"] == "boleto"


def test_morador_escolhe_o_dia_e_a_forma(cliente, cenario):
    """"uma cobrança mensal na data em que eu escolhesse" (seção 6)."""
    r = cliente.put(
        "/api/v1/financeiro/preferencia",
        json={"dia_vencimento": 20, "forma_preferida": "pix"},
        headers=cab(cenario["ana"]),
    )
    assert r.status_code == 200, r.text
    assert r.json()["dia_vencimento"] == 20
    assert r.json()["forma_preferida"] == "pix"

    de_volta = cliente.get("/api/v1/financeiro/preferencia", headers=cab(cenario["ana"]))
    assert de_volta.json()["dia_vencimento"] == 20


@pytest.mark.parametrize("dia", [0, 29, 31, -1])
def test_dia_fora_da_faixa_e_recusado(cliente, cenario, dia):
    """Acima de 28 o dia não existiria em fevereiro."""
    r = cliente.put(
        "/api/v1/financeiro/preferencia",
        json={"dia_vencimento": dia, "forma_preferida": "pix"},
        headers=cab(cenario["ana"]),
    )
    assert r.status_code == 422


def test_a_cobranca_usa_o_dia_escolhido_pelo_morador(cliente, cenario):
    cliente.put(
        "/api/v1/financeiro/preferencia",
        json={"dia_vencimento": 20, "forma_preferida": "pix"},
        headers=cab(cenario["ana"]),
    )
    # Sem vencimento explicito: a API calcula pelo dia escolhido.
    r = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"], vencimento=None)
    assert r.status_code == 201, r.text
    assert r.json()["vencimento"].endswith("-20")


def test_cada_morador_tem_a_propria_preferencia(cliente, cenario):
    cliente.put(
        "/api/v1/financeiro/preferencia",
        json={"dia_vencimento": 5, "forma_preferida": "pix"},
        headers=cab(cenario["ana"]),
    )
    r = cliente.get("/api/v1/financeiro/preferencia", headers=cab(cenario["bruno"]))
    assert r.json()["dia_vencimento"] == 10


# ── Cobranças ────────────────────────────────────────────────────────
def test_nao_duplica_competencia(cliente, cenario):
    assert gerar_cobranca(cliente, cenario["sindico"], cenario["u204"]).status_code == 201
    assert gerar_cobranca(cliente, cenario["sindico"], cenario["u204"]).status_code == 409


def test_morador_nao_gera_cobranca(cliente, cenario):
    assert gerar_cobranca(cliente, cenario["ana"], cenario["u204"]).status_code == 403


def test_morador_so_ve_as_cobrancas_da_propria_unidade(cliente, cenario):
    gerar_cobranca(cliente, cenario["sindico"], cenario["u204"], valor="320.00")
    gerar_cobranca(cliente, cenario["sindico"], cenario["u301"], valor="410.00")

    da_ana = cliente.get("/api/v1/financeiro/cobrancas", headers=cab(cenario["ana"])).json()
    assert [c["unidade"] for c in da_ana] == ["204"]

    do_sindico = cliente.get(
        "/api/v1/financeiro/cobrancas", headers=cab(cenario["sindico"])
    ).json()
    assert len(do_sindico) == 2


def test_porteiro_nao_acessa_o_financeiro(cliente, cenario):
    r = cliente.get("/api/v1/financeiro/cobrancas", headers=cab(cenario["porteiro"]))
    assert r.status_code == 403


def test_cobranca_vencida_aparece_como_vencida(cliente, cenario):
    ontem = (date.today() - timedelta(days=1)).isoformat()
    r = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"], vencimento=ontem)
    assert r.json()["status"] == "vencida"


# ── Pagamentos (seção 6) ─────────────────────────────────────────────
@pytest.mark.parametrize("forma", ["pix", "boleto", "debito_automatico", "cartao"])
def test_formas_variadas_de_pagamento(cliente, cenario, forma):
    """"variadas opções para formas de pagamento" (seção 6)."""
    c = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"]).json()
    r = cliente.post(
        f"/api/v1/financeiro/cobrancas/{c['id']}/pagamentos",
        json={"valor": "320.00", "forma": forma},
        headers=cab(cenario["ana"]),
    )
    assert r.status_code == 201, r.text
    assert r.json()["forma"] == forma


def test_pagamento_total_quita_a_cobranca(cliente, cenario):
    c = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"]).json()
    cliente.post(
        f"/api/v1/financeiro/cobrancas/{c['id']}/pagamentos",
        json={"valor": "320.00", "forma": "pix"},
        headers=cab(cenario["ana"]),
    )
    lista = cliente.get("/api/v1/financeiro/cobrancas", headers=cab(cenario["ana"])).json()
    assert lista[0]["status"] == "paga"
    assert lista[0]["total_pago"] == "320.00"


def test_pagamento_parcial_mantem_a_cobranca_aberta(cliente, cenario):
    c = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"]).json()
    cliente.post(
        f"/api/v1/financeiro/cobrancas/{c['id']}/pagamentos",
        json={"valor": "100.00", "forma": "pix"},
        headers=cab(cenario["ana"]),
    )
    lista = cliente.get("/api/v1/financeiro/cobrancas", headers=cab(cenario["ana"])).json()
    assert lista[0]["status"] != "paga"
    assert lista[0]["total_pago"] == "100.00"

    # A segunda parcela fecha.
    cliente.post(
        f"/api/v1/financeiro/cobrancas/{c['id']}/pagamentos",
        json={"valor": "220.00", "forma": "boleto"},
        headers=cab(cenario["ana"]),
    )
    lista = cliente.get("/api/v1/financeiro/cobrancas", headers=cab(cenario["ana"])).json()
    assert lista[0]["status"] == "paga"


def test_nao_paga_mais_do_que_deve(cliente, cenario):
    c = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"]).json()
    r = cliente.post(
        f"/api/v1/financeiro/cobrancas/{c['id']}/pagamentos",
        json={"valor": "500.00", "forma": "pix"},
        headers=cab(cenario["ana"]),
    )
    assert r.status_code == 400


def test_nao_paga_cobranca_ja_paga(cliente, cenario):
    c = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"]).json()
    corpo = {"valor": "320.00", "forma": "pix"}
    url = f"/api/v1/financeiro/cobrancas/{c['id']}/pagamentos"
    assert cliente.post(url, json=corpo, headers=cab(cenario["ana"])).status_code == 201
    assert cliente.post(url, json=corpo, headers=cab(cenario["ana"])).status_code == 409


def test_morador_nao_paga_cobranca_de_outra_unidade(cliente, cenario):
    c = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"]).json()
    r = cliente.post(
        f"/api/v1/financeiro/cobrancas/{c['id']}/pagamentos",
        json={"valor": "320.00", "forma": "pix"},
        headers=cab(cenario["bruno"]),
    )
    assert r.status_code == 404


def test_historico_registra_meio_quem_e_quando(cliente, cenario):
    """"com qual meio o pagamento foi realizado, por quem e a data" (seção 6)."""
    c = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"]).json()
    cliente.post(
        f"/api/v1/financeiro/cobrancas/{c['id']}/pagamentos",
        json={"valor": "320.00", "forma": "pix", "comprovante_url": "https://x/comp.pdf"},
        headers=cab(cenario["ana"]),
    )
    r = cliente.get(
        f"/api/v1/financeiro/cobrancas/{c['id']}/pagamentos", headers=cab(cenario["sindico"])
    )
    assert r.status_code == 200
    p = r.json()[0]
    assert p["forma"] == "pix"
    assert p["pago_por_nome"] == "João Silva"
    assert p["pago_em"] is not None
    assert p["comprovante_url"] == "https://x/comp.pdf"


def test_resumo_do_sindico(cliente, cenario):
    ontem = (date.today() - timedelta(days=1)).isoformat()
    semana_que_vem = (date.today() + timedelta(days=7)).isoformat()
    gerar_cobranca(
        cliente, cenario["sindico"], cenario["u204"], valor="320.00", vencimento=semana_que_vem
    )
    gerar_cobranca(cliente, cenario["sindico"], cenario["u301"], valor="410.00", vencimento=ontem)

    r = cliente.get("/api/v1/financeiro/resumo", headers=cab(cenario["sindico"]))
    assert r.status_code == 200
    resumo = r.json()
    assert resumo["cobrancas_abertas"] == 2
    assert resumo["total_aberto"] == "730.00"
    assert resumo["total_vencido"] == "410.00"
    assert resumo["unidades_inadimplentes"] == 1


# ── Comunicados (seções 11.5.4 e 11.6.4) ─────────────────────────────
def publicar(cliente, tok, **extra):
    corpo = {"titulo": "Manutenção da piscina", "conteudo": "A piscina fica fechada dia 20."}
    corpo.update(extra)
    return cliente.post("/api/v1/comunicados", json=corpo, headers=cab(tok))


def test_sindico_publica_e_morador_le(cliente, cenario):
    assert publicar(cliente, cenario["sindico"]).status_code == 201

    r = cliente.get("/api/v1/comunicados", headers=cab(cenario["ana"]))
    assert r.status_code == 200
    assert r.json()[0]["titulo"] == "Manutenção da piscina"
    assert r.json()[0]["autor_nome"] == "Roberto Nascimento"
    assert r.json()[0]["lido"] is False


def test_morador_nao_publica(cliente, cenario):
    assert publicar(cliente, cenario["ana"]).status_code == 403


def test_marcar_como_lido_e_idempotente(cliente, cenario):
    c = publicar(cliente, cenario["sindico"]).json()
    url = f"/api/v1/comunicados/{c['id']}/leitura"
    assert cliente.post(url, headers=cab(cenario["ana"])).status_code == 200
    assert cliente.post(url, headers=cab(cenario["ana"])).status_code == 200

    lista = cliente.get("/api/v1/comunicados", headers=cab(cenario["ana"])).json()
    assert lista[0]["lido"] is True
    # O Bruno não leu — a marcação é por usuário.
    do_bruno = cliente.get("/api/v1/comunicados", headers=cab(cenario["bruno"])).json()
    assert do_bruno[0]["lido"] is False


def test_filtro_por_categoria(cliente, cenario):
    publicar(cliente, cenario["sindico"], titulo="Aviso geral", categoria="geral")
    publicar(cliente, cenario["sindico"], titulo="Corte de água", categoria="manutencao")

    r = cliente.get(
        "/api/v1/comunicados", params={"categoria": "manutencao"}, headers=cab(cenario["ana"])
    )
    assert [c["titulo"] for c in r.json()] == ["Corte de água"]


def test_filtro_de_nao_lidos(cliente, cenario):
    a = publicar(cliente, cenario["sindico"], titulo="Primeiro").json()
    publicar(cliente, cenario["sindico"], titulo="Segundo")
    cliente.post(f"/api/v1/comunicados/{a['id']}/leitura", headers=cab(cenario["ana"]))

    r = cliente.get(
        "/api/v1/comunicados", params={"apenas_nao_lidos": True}, headers=cab(cenario["ana"])
    )
    assert [c["titulo"] for c in r.json()] == ["Segundo"]


def test_fixado_vem_primeiro(cliente, cenario):
    publicar(cliente, cenario["sindico"], titulo="Comum")
    publicar(cliente, cenario["sindico"], titulo="Importante", fixado=True)

    r = cliente.get("/api/v1/comunicados", headers=cab(cenario["ana"]))
    assert [c["titulo"] for c in r.json()] == ["Importante", "Comum"]

"""Prestação de contas: despesas do condomínio e balancete do mês.

Situação real: o morador paga a taxa todo mês e não sabe para onde vai o
dinheiro. O síndico precisa prestar contas (Código Civil, art. 1.348,
VIII), e o sistema só registrava o que entrava — nenhuma despesa.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from app.core.tempo import hoje_local
from tests.fixtures import cab, criar_condominio_como_admin, criar_sindico, token_admin
from tests.test_financeiro import cenario, gerar_cobranca  # noqa: F401

URL = "/api/v1/financeiro"
PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def _mes(dia):
    return dia.strftime("%Y-%m")


def lancar(cliente, tok, **extra):
    corpo = {"categoria": "manutencao", "descricao": "Troca da bomba d'água",
             "valor": "1500.00", "data": hoje_local().isoformat(),
             "fornecedor": "Hidráulica Silva"}
    corpo.update(extra)
    return cliente.post(f"{URL}/despesas", json=corpo, headers=cab(tok))


def test_sindico_lanca_e_morador_ve(cliente, cenario):
    r = lancar(cliente, cenario["sindico"])
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["categoria"] == "manutencao" and Decimal(d["valor"]) == Decimal("1500.00")
    assert d["lancada_por_nome"] == "Roberto Nascimento"
    lista = cliente.get(f"{URL}/despesas?mes={_mes(hoje_local())}", headers=cab(cenario["ana"]))
    assert lista.status_code == 200
    assert [x["descricao"] for x in lista.json()] == ["Troca da bomba d'água"]


def test_quem_nao_pode(cliente, cenario):
    assert lancar(cliente, cenario["ana"]).status_code == 403
    assert lancar(cliente, cenario["porteiro"]).status_code == 403
    assert cliente.get(f"{URL}/despesas", headers=cab(cenario["porteiro"])).status_code == 403
    assert cliente.get(f"{URL}/balancete", headers=cab(cenario["porteiro"])).status_code == 403


def test_balancete_do_mes(cliente, cenario):
    hoje = hoje_local()
    mes_passado = hoje.replace(day=1) - timedelta(days=1)
    lancar(cliente, cenario["sindico"], valor="100.00", data=mes_passado.isoformat(),
           categoria="limpeza", descricao="Material de limpeza")
    lancar(cliente, cenario["sindico"], valor="50.00", categoria="energia",
           descricao="Conta de luz das áreas comuns")
    lancar(cliente, cenario["sindico"], valor="30.00", categoria="energia",
           descricao="Lâmpadas do hall")
    c = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"]).json()
    cliente.post(f"{URL}/cobrancas/{c['id']}/pagamentos", headers=cab(cenario["ana"]),
                 json={"valor": "320.00", "forma": "pix"})

    b = cliente.get(f"{URL}/balancete?mes={_mes(hoje)}", headers=cab(cenario["bruno"]))
    assert b.status_code == 200, b.text
    b = b.json()
    assert b["mes"] == _mes(hoje)
    assert Decimal(b["receitas"]) == Decimal("320.00")
    assert Decimal(b["despesas"]) == Decimal("80.00")
    assert Decimal(b["saldo_do_mes"]) == Decimal("240.00")
    assert Decimal(b["saldo_anterior"]) == Decimal("-100.00")
    assert Decimal(b["saldo_acumulado"]) == Decimal("140.00")
    assert [(x["categoria"], Decimal(x["total"])) for x in b["por_categoria"]] == [
        ("energia", Decimal("80.00"))]

    anterior = cliente.get(f"{URL}/balancete?mes={_mes(mes_passado)}",
                           headers=cab(cenario["bruno"])).json()
    assert Decimal(anterior["despesas"]) == Decimal("100.00")
    assert Decimal(anterior["saldo_acumulado"]) == Decimal("-100.00")


def test_correcao_e_cancelamento_ficam_registrados(cliente, cenario):
    d = lancar(cliente, cenario["sindico"]).json()
    r = cliente.put(f"{URL}/despesas/{d['id']}", headers=cab(cenario["sindico"]),
                    json={"valor": "1450.00"})
    assert r.status_code == 200, r.text
    assert r.json()["ultima_alteracao"]["descricao"] == "Alterou o valor"
    assert cliente.put(f"{URL}/despesas/{d['id']}", headers=cab(cenario["ana"]),
                       json={"valor": "1.00"}).status_code == 403

    r = cliente.post(f"{URL}/despesas/{d['id']}/cancelamento", headers=cab(cenario["sindico"]),
                     json={"motivo": "Lançada em duplicidade"})
    assert r.status_code == 200, r.text
    # Nada é apagado: some das telas e do balancete, e o motivo fica.
    assert cliente.get(f"{URL}/despesas", headers=cab(cenario["ana"])).json() == []
    b = cliente.get(f"{URL}/balancete", headers=cab(cenario["ana"])).json()
    assert Decimal(b["despesas"]) == 0
    hist = cliente.get(f"{URL}/despesas?incluir_canceladas=true",
                       headers=cab(cenario["sindico"])).json()
    assert hist[0]["cancelada"] is True
    assert hist[0]["ultima_alteracao"]["descricao"] == "Lançada em duplicidade"
    assert cliente.post(f"{URL}/despesas/{d['id']}/cancelamento",
                        headers=cab(cenario["sindico"]),
                        json={"motivo": "De novo"}).status_code == 409
    assert cliente.put(f"{URL}/despesas/{d['id']}", headers=cab(cenario["sindico"]),
                       json={"valor": "2.00"}).status_code == 409


def test_comprovante_so_para_quem_e_do_condominio(cliente, cenario):
    d = lancar(cliente, cenario["sindico"]).json()
    url = f"{URL}/despesas/{d['id']}/comprovante"
    assert cliente.put(url, headers=cab(cenario["ana"]),
                       files={"arquivo": ("nota.pdf", PDF, "application/pdf")}).status_code == 403
    r = cliente.put(url, headers=cab(cenario["sindico"]),
                    files={"arquivo": ("nota.pdf", PDF, "application/pdf")})
    assert r.status_code == 200, r.text
    assert r.json()["comprovante_url"] == f"/financeiro/despesas/{d['id']}/comprovante"
    baixado = cliente.get(url, headers=cab(cenario["ana"]))
    assert baixado.status_code == 200 and baixado.content.startswith(b"%PDF")
    assert "no-store" in baixado.headers["cache-control"]
    assert cliente.get(url, headers=cab(cenario["porteiro"])).status_code == 403
    # Arquivo que não é PDF nem imagem é recusado.
    assert cliente.put(url, headers=cab(cenario["sindico"]),
                       files={"arquivo": ("x.exe", b"MZ\x90\x00", "application/pdf")}
                       ).status_code == 422


def test_outro_condominio_nao_ve(cliente, cenario, db):
    d = lancar(cliente, cenario["sindico"]).json()
    admin2 = token_admin(cliente, db, email="adm2@exemplo.com", cpf="111.444.777-35")
    outro = criar_condominio_como_admin(cliente, admin2, nome="Aurora",
                                        cnpj="45.997.418/0001-53")
    _, sindico2 = criar_sindico(cliente, admin2, outro["id"], email="s2@exemplo.com",
                                cpf="529.982.247-25")
    assert cliente.get(f"{URL}/despesas", headers=cab(sindico2)).json() == []
    assert cliente.put(f"{URL}/despesas/{d['id']}", headers=cab(sindico2),
                       json={"valor": "1.00"}).status_code == 404
    assert cliente.get(f"{URL}/despesas/{d['id']}/comprovante",
                       headers=cab(sindico2)).status_code == 404


@pytest.mark.parametrize("dados", [
    {"valor": "0"},
    {"valor": "-10"},
    {"data": (hoje_local() + timedelta(days=1)).isoformat()},
    {"data": (hoje_local() - timedelta(days=6 * 366)).isoformat()},
    {"categoria": "festa"},
    {"descricao": "ab"},
])
def test_dados_invalidos(cliente, cenario, dados):
    r = lancar(cliente, cenario["sindico"], **dados)
    assert r.status_code == 422, (dados, r.text)


@pytest.mark.parametrize("mes", ["2026-13", "abc", "2026-1"])
def test_mes_invalido(cliente, cenario, mes):
    assert cliente.get(f"{URL}/balancete?mes={mes}",
                       headers=cab(cenario["ana"])).status_code == 422

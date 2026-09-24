"""Testes de veículos, ordens de serviço e documentos.

Três módulos que o front-end já apresentava e que não tinham back-end.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from tests.fixtures import (
    CPFS, cab, cadastrar_morador, cadastrar_porteiro, montar_condominio,
)


@pytest.fixture
def cenario(cliente, db):
    base = montar_condominio(cliente, db)
    tok_sindico, cond = base["sindico"], base["cond"]

    _, tok_morador = cadastrar_morador(
        cliente, tok_sindico, cond, email="ana@exemplo.com", cpf=CPFS[1], unidade="204"
    )
    _, tok_outro = cadastrar_morador(
        cliente, tok_sindico, cond, email="bruno@exemplo.com", cpf=CPFS[3], unidade="301"
    )
    _, tok_porteiro = cadastrar_porteiro(cliente, tok_sindico, cond, cpf=CPFS[2])

    unidades = cliente.get("/api/v1/condominios/meu/unidades", headers=cab(tok_sindico)).json()
    return {
        "cond": cond, "sindico": tok_sindico, "morador": tok_morador,
        "outro": tok_outro, "porteiro": tok_porteiro,
        "u204": next(u for u in unidades if u["numero"] == "204")["id"],
        "u301": next(u for u in unidades if u["numero"] == "301")["id"],
    }


# ══ VEÍCULOS ═════════════════════════════════════════════════════════
def mover(cliente, tok, **extra):
    corpo = {
        "placa": "ABC1D23", "tipo": "entrada", "categoria": "visitante",
    }
    corpo.update(extra)
    return cliente.post("/api/v1/veiculos", json=corpo, headers=cab(tok))


def test_registra_entrada_e_saida(cliente, cenario):
    e = mover(cliente, cenario["porteiro"])
    assert e.status_code == 201, e.text
    assert e.json()["tipo"] == "entrada"

    s = mover(cliente, cenario["porteiro"], tipo="saida")
    assert s.status_code == 201
    assert s.json()["tipo"] == "saida"


@pytest.mark.parametrize(
    "informada, guardada",
    [("ABC-1D23", "ABC1D23"), ("abc1d23", "ABC1D23"), ("ABC 1D23", "ABC1D23")],
)
def test_a_placa_e_normalizada(cliente, cenario, informada, guardada):
    """Sem normalizar, ABC-1D23 e ABC1D23 seriam dois veículos diferentes."""
    r = mover(cliente, cenario["porteiro"], placa=informada)
    assert r.status_code == 201, r.text
    assert r.json()["placa"] == guardada


def test_placa_com_tamanho_errado_e_recusada(cliente, cenario):
    assert mover(cliente, cenario["porteiro"], placa="ABC123").status_code == 422


def test_nao_registra_duas_entradas_seguidas(cliente, cenario):
    """Duas entradas sem saída deixariam o pátio contando errado."""
    assert mover(cliente, cenario["porteiro"]).status_code == 201
    r = mover(cliente, cenario["porteiro"])
    assert r.status_code == 409
    assert "já foi uma entrada" in r.json()["detalhe"]


def test_nao_registra_saida_sem_entrada(cliente, cenario):
    r = mover(cliente, cenario["porteiro"], tipo="saida")
    assert r.status_code == 409
    assert "não tem entrada registrada" in r.json()["detalhe"]


def test_morador_precisa_de_unidade(cliente, cenario):
    r = mover(cliente, cenario["porteiro"], categoria="morador")
    assert r.status_code == 400
    assert "unidade do morador" in r.json()["detalhe"]

    ok = mover(
        cliente, cenario["porteiro"], categoria="morador", unidade_id=cenario["u204"]
    )
    assert ok.status_code == 201
    assert ok.json()["unidade"] == "204"


def test_patio_mostra_so_quem_entrou_e_nao_saiu(cliente, cenario):
    mover(cliente, cenario["porteiro"], placa="AAA1A11")
    mover(cliente, cenario["porteiro"], placa="BBB2B22")
    mover(cliente, cenario["porteiro"], placa="AAA1A11", tipo="saida")

    r = cliente.get("/api/v1/veiculos/patio", headers=cab(cenario["porteiro"]))
    assert r.status_code == 200
    assert [v["placa"] for v in r.json()] == ["BBB2B22"]


def test_ocupacao_do_estacionamento(cliente, cenario):
    """As vagas totais saem da soma das vagas das unidades."""
    vazio = cliente.get("/api/v1/veiculos/ocupacao", headers=cab(cenario["porteiro"]))
    assert vazio.status_code == 200
    assert vazio.json()["ocupadas"] == 0

    mover(cliente, cenario["porteiro"], placa="AAA1A11")
    mover(cliente, cenario["porteiro"], placa="BBB2B22")

    r = cliente.get("/api/v1/veiculos/ocupacao", headers=cab(cenario["porteiro"]))
    assert r.json()["ocupadas"] == 2
    assert r.json()["livres"] >= 0


def test_porteiro_sem_permissao_nao_registra_veiculo(cliente, cenario):
    """Documentação, seção 12: vale o que o síndico liberou."""
    _, tok = cadastrar_porteiro(
        cliente, cenario["sindico"], cenario["cond"],
        email="semvei@exemplo.com", cpf=CPFS[4],
        permissoes={
            "registrar_visitantes": True, "registrar_encomendas": True,
            "registrar_veiculos": False, "registrar_ocorrencias": True,
            "acessar_financeiro": False,
        },
    )
    r = mover(cliente, tok)
    assert r.status_code == 403
    assert "não liberou" in r.json()["detalhe"]


def test_porteiro_sem_permissao_nao_consulta_veiculos(cliente, cenario):
    """A Política de Privacidade promete que o porteiro só vê o que o
    síndico liberou — vale para consultar, não só para registrar."""
    _, tok = cadastrar_porteiro(
        cliente, cenario["sindico"], cenario["cond"],
        email="semvei2@exemplo.com", cpf=CPFS[4],
        permissoes={
            "registrar_visitantes": True, "registrar_encomendas": True,
            "registrar_veiculos": False, "registrar_ocorrencias": True,
            "acessar_financeiro": False,
        },
    )
    assert cliente.get("/api/v1/veiculos/patio", headers=cab(tok)).status_code == 403
    assert cliente.get("/api/v1/veiculos", headers=cab(tok)).status_code == 403


def test_morador_nao_ve_as_placas_do_patio(cliente, cenario):
    """O pátio traz placa e unidade de todos os carros; o morador fica com
    a ocupação em números."""
    mover(cliente, cenario["porteiro"])
    assert cliente.get("/api/v1/veiculos/patio", headers=cab(cenario["morador"])).status_code == 403
    assert cliente.get("/api/v1/veiculos/ocupacao", headers=cab(cenario["morador"])).status_code == 200


def test_morador_nao_registra_veiculo(cliente, cenario):
    assert mover(cliente, cenario["morador"]).status_code == 403


def test_morador_so_ve_as_movimentacoes_da_propria_unidade(cliente, cenario):
    mover(cliente, cenario["porteiro"], placa="AAA1A11",
          categoria="morador", unidade_id=cenario["u204"])
    mover(cliente, cenario["porteiro"], placa="BBB2B22",
          categoria="morador", unidade_id=cenario["u301"])

    da_ana = cliente.get("/api/v1/veiculos", headers=cab(cenario["morador"])).json()
    assert [m["placa"] for m in da_ana] == ["AAA1A11"]

    do_porteiro = cliente.get("/api/v1/veiculos", headers=cab(cenario["porteiro"])).json()
    assert len(do_porteiro) == 2


def test_filtro_por_placa_aceita_formatacao(cliente, cenario):
    mover(cliente, cenario["porteiro"], placa="AAA1A11")
    r = cliente.get(
        "/api/v1/veiculos", params={"placa": "aaa-1a11"}, headers=cab(cenario["porteiro"])
    )
    assert [m["placa"] for m in r.json()] == ["AAA1A11"]


# ══ MANUTENÇÃO ═══════════════════════════════════════════════════════
def abrir_os(cliente, tok, **extra):
    corpo = {
        "tipo": "Elétrica", "descricao": "Lâmpada queimada na garagem.",
        "prioridade": "media",
    }
    corpo.update(extra)
    return cliente.post("/api/v1/manutencao", json=corpo, headers=cab(tok))


def test_sindico_abre_ordem_de_servico(cliente, cenario):
    r = abrir_os(cliente, cenario["sindico"], fornecedor="Elétrica Silva",
                 custo_estimado="450.00", local="Garagem")
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "aberta"
    assert r.json()["fornecedor"] == "Elétrica Silva"
    assert r.json()["aberta_por_nome"] == "Roberto Nascimento"


def test_morador_e_porteiro_nao_abrem_os(cliente, cenario):
    assert abrir_os(cliente, cenario["morador"]).status_code == 403
    assert abrir_os(cliente, cenario["porteiro"]).status_code == 403


def test_todos_acompanham_o_andamento(cliente, cenario):
    abrir_os(cliente, cenario["sindico"])
    for quem in ("morador", "porteiro", "sindico"):
        r = cliente.get("/api/v1/manutencao", headers=cab(cenario[quem]))
        assert r.status_code == 200, quem
        assert len(r.json()) == 1


def test_concluir_marca_a_data(cliente, cenario):
    os_ = abrir_os(cliente, cenario["sindico"]).json()
    assert os_["concluida_em"] is None

    r = cliente.put(
        f"/api/v1/manutencao/{os_['id']}",
        json={"status": "concluida", "custo_real": "380.00"},
        headers=cab(cenario["sindico"]),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "concluida"
    assert r.json()["concluida_em"] is not None
    assert r.json()["custo_real"] == "380.00"


def test_reabrir_limpa_a_data_de_conclusao(cliente, cenario):
    """Se não limpar, a data ficaria dizendo que já acabou."""
    os_ = abrir_os(cliente, cenario["sindico"]).json()
    cliente.put(
        f"/api/v1/manutencao/{os_['id']}", json={"status": "concluida"},
        headers=cab(cenario["sindico"]),
    )
    r = cliente.put(
        f"/api/v1/manutencao/{os_['id']}", json={"status": "em_andamento"},
        headers=cab(cenario["sindico"]),
    )
    assert r.json()["status"] == "em_andamento"
    assert r.json()["concluida_em"] is None


def test_cancelar_nao_apaga(cliente, cenario):
    os_ = abrir_os(cliente, cenario["sindico"]).json()
    assert cliente.delete(
        f"/api/v1/manutencao/{os_['id']}", headers=cab(cenario["sindico"])
    ).status_code == 200

    lista = cliente.get("/api/v1/manutencao", headers=cab(cenario["sindico"])).json()
    assert [o["status"] for o in lista] == ["cancelada"]


def test_nao_cancela_ordem_concluida(cliente, cenario):
    os_ = abrir_os(cliente, cenario["sindico"]).json()
    cliente.put(
        f"/api/v1/manutencao/{os_['id']}", json={"status": "concluida"},
        headers=cab(cenario["sindico"]),
    )
    r = cliente.delete(f"/api/v1/manutencao/{os_['id']}", headers=cab(cenario["sindico"]))
    assert r.status_code == 409


def test_filtros_de_status_e_prioridade(cliente, cenario):
    abrir_os(cliente, cenario["sindico"], tipo="Hidráulica", prioridade="urgente")
    abrir_os(cliente, cenario["sindico"], tipo="Pintura", prioridade="baixa")

    urgentes = cliente.get(
        "/api/v1/manutencao", params={"prioridade": "urgente"}, headers=cab(cenario["sindico"])
    )
    assert [o["tipo"] for o in urgentes.json()] == ["Hidráulica"]


def test_resumo_da_manutencao(cliente, cenario):
    """O previsto conta só o que ainda está de pé."""
    a = abrir_os(cliente, cenario["sindico"], custo_estimado="500.00").json()
    abrir_os(cliente, cenario["sindico"], custo_estimado="300.00")
    cliente.put(
        f"/api/v1/manutencao/{a['id']}",
        json={"status": "concluida", "custo_real": "480.00"},
        headers=cab(cenario["sindico"]),
    )

    r = cliente.get("/api/v1/manutencao/resumo", headers=cab(cenario["sindico"]))
    assert r.status_code == 200
    assert r.json()["abertas"] == 1
    assert r.json()["concluidas"] == 1
    assert r.json()["custo_previsto"] == "300.00"
    assert r.json()["custo_realizado"] == "480.00"


def test_custo_negativo_e_recusado(cliente, cenario):
    assert abrir_os(cliente, cenario["sindico"], custo_estimado="-10.00").status_code == 422


# ══ DOCUMENTOS ═══════════════════════════════════════════════════════
def publicar_doc(cliente, tok, **extra):
    corpo = {
        "titulo": "Convenção do Condomínio", "categoria": "convencao",
        "arquivo_url": "https://cdn.exemplo.com/convencao.pdf",
    }
    corpo.update(extra)
    return cliente.post("/api/v1/documentos", json=corpo, headers=cab(tok))


def test_sindico_publica_e_morador_le(cliente, cenario):
    r = publicar_doc(cliente, cenario["sindico"], tamanho_kb=820)
    assert r.status_code == 201, r.text
    assert r.json()["publicado_por_nome"] == "Roberto Nascimento"

    lista = cliente.get("/api/v1/documentos", headers=cab(cenario["morador"]))
    assert lista.status_code == 200
    assert lista.json()[0]["titulo"] == "Convenção do Condomínio"


def test_morador_nao_publica(cliente, cenario):
    assert publicar_doc(cliente, cenario["morador"]).status_code == 403


def test_documento_de_unidade_so_aparece_para_quem_mora_nela(cliente, cenario):
    """A planta do apto 204 não é da conta do morador do 301."""
    publicar_doc(cliente, cenario["sindico"], titulo="Convenção")
    publicar_doc(
        cliente, cenario["sindico"], titulo="Planta do 204",
        categoria="planta", unidade_id=cenario["u204"],
    )

    da_ana = cliente.get("/api/v1/documentos", headers=cab(cenario["morador"])).json()
    assert {d["titulo"] for d in da_ana} == {"Convenção", "Planta do 204"}

    do_bruno = cliente.get("/api/v1/documentos", headers=cab(cenario["outro"])).json()
    assert {d["titulo"] for d in do_bruno} == {"Convenção"}


def test_sindico_ve_todos_os_documentos(cliente, cenario):
    publicar_doc(cliente, cenario["sindico"], titulo="Convenção")
    publicar_doc(
        cliente, cenario["sindico"], titulo="Planta do 204",
        categoria="planta", unidade_id=cenario["u204"],
    )
    r = cliente.get("/api/v1/documentos", headers=cab(cenario["sindico"]))
    assert len(r.json()) == 2


def test_filtro_por_categoria(cliente, cenario):
    publicar_doc(cliente, cenario["sindico"], titulo="Convenção", categoria="convencao")
    publicar_doc(cliente, cenario["sindico"], titulo="Ata de março", categoria="ata")

    r = cliente.get(
        "/api/v1/documentos", params={"categoria": "ata"}, headers=cab(cenario["morador"])
    )
    assert [d["titulo"] for d in r.json()] == ["Ata de março"]


def test_unidade_de_outro_condominio_e_recusada(cliente, db, cenario):
    outra = montar_condominio(
        cliente, db, nome="Outro", cnpj="45.997.418/0001-53",
        email_sindico="outro@exemplo.com", cpf_sindico=CPFS[4],
        email_admin="admin2@exemplo.com", cpf_admin=CPFS[7],
    )
    r = publicar_doc(cliente, outra["sindico"], unidade_id=cenario["u204"])
    assert r.status_code == 404


def test_remover_documento(cliente, cenario):
    doc = publicar_doc(cliente, cenario["sindico"]).json()
    assert cliente.delete(
        f"/api/v1/documentos/{doc['id']}", headers=cab(cenario["sindico"])
    ).status_code == 200
    assert cliente.get("/api/v1/documentos", headers=cab(cenario["morador"])).json() == []


def test_morador_nao_remove_documento(cliente, cenario):
    doc = publicar_doc(cliente, cenario["sindico"]).json()
    r = cliente.delete(f"/api/v1/documentos/{doc['id']}", headers=cab(cenario["morador"]))
    assert r.status_code == 403

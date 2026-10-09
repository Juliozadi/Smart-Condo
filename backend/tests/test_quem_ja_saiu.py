"""Quem saiu do condomínio não recebe nem decide mais nada.

Inativar é o que acontece quando o morador se muda ou o síndico é trocado:
o cadastro fica guardado, mas os avisos da portaria, o aviso de pagamento
e a preferência de vencimento são de quem está lá agora.
"""
from __future__ import annotations

import pytest

from app.services import notificacao
from tests.fixtures import (
    CPFS, cab, cadastrar_morador, cadastrar_porteiro, criar_sindico, montar_condominio,
)
from tests.test_financeiro import COMPETENCIA, FUTURO
from tests.test_portaria import DOC_VISITANTE


@pytest.fixture
def enviados(monkeypatch):
    lista = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: lista.append(destino))
    return lista


@pytest.fixture
def predio(cliente, db):
    """Unidade 204: a Carla se mudou (inativada) e a Ana mora lá agora."""
    base = montar_condominio(cliente, db)
    carla_id, tok_carla = cadastrar_morador(
        cliente, base["sindico"], base["cond"], email="carla@exemplo.com", cpf=CPFS[3],
        unidade="204")
    _, tok_ana = cadastrar_morador(
        cliente, base["sindico"], base["cond"], email="ana@exemplo.com", cpf=CPFS[1],
        unidade="204")
    _, tok_porteiro = cadastrar_porteiro(cliente, base["sindico"], base["cond"], cpf=CPFS[2])
    unidades = cliente.get("/api/v1/condominios/meu/unidades", headers=cab(base["sindico"])).json()
    return {**base, "carla_id": carla_id, "carla": tok_carla, "ana": tok_ana,
            "porteiro": tok_porteiro,
            "u204": next(u for u in unidades if u["numero"] == "204")["id"]}


def mudar_se(cliente, predio):
    r = cliente.delete(f"/api/v1/usuarios/{predio['carla_id']}", headers=cab(predio["sindico"]))
    assert r.status_code == 200, r.text


def test_visitante_e_encomenda_so_avisam_quem_mora_la(cliente, predio, enviados):
    mudar_se(cliente, predio)
    enviados.clear()
    r = cliente.post("/api/v1/portaria/visitantes", headers=cab(predio["porteiro"]), json={
        "unidade_id": predio["u204"], "nome": "Marcos Alves", "documento": DOC_VISITANTE,
        "tipo_visita": "Visita pessoal"})
    assert r.status_code == 201, r.text
    r = cliente.post("/api/v1/portaria/encomendas", headers=cab(predio["porteiro"]), json={
        "unidade_id": predio["u204"], "remetente": "Loja X", "tipo_volume": "Caixa média"})
    assert r.status_code == 201, r.text
    assert enviados == ["ana@exemplo.com", "ana@exemplo.com"]


def test_pagamento_avisa_o_sindico_atual_e_nao_o_antigo(cliente, predio, enviados):
    # O administrador troca o síndico: o antigo é inativado.
    admin = predio["admin"]
    assert cliente.delete(f"/api/v1/admin/usuarios/{predio['sindico_id']}",
                          headers=cab(admin)).status_code == 200
    _, tok_novo = criar_sindico(cliente, admin, predio["cond"]["id"],
                                email="novo@exemplo.com", cpf=CPFS[5])
    cobranca = cliente.post("/api/v1/financeiro/cobrancas", headers=cab(tok_novo), json={
        "unidade_id": predio["u204"], "competencia": COMPETENCIA,
        "descricao": "Taxa de condomínio", "valor": "320.00", "vencimento": FUTURO}).json()
    enviados.clear()
    r = cliente.post(f"/api/v1/financeiro/cobrancas/{cobranca['id']}/pagamentos",
                     headers=cab(predio["ana"]), json={"valor": "320.00", "forma": "pix"})
    assert r.status_code == 201, r.text
    assert enviados == ["novo@exemplo.com"]


def test_vencimento_usa_a_preferencia_de_quem_mora_la(cliente, predio):
    h = {"forma_preferida": "pix"}
    assert cliente.put("/api/v1/financeiro/preferencia", headers=cab(predio["carla"]),
                       json={**h, "dia_vencimento": 5}).status_code == 200
    mudar_se(cliente, predio)
    assert cliente.put("/api/v1/financeiro/preferencia", headers=cab(predio["ana"]),
                       json={**h, "dia_vencimento": 20}).status_code == 200
    r = cliente.post("/api/v1/financeiro/cobrancas", headers=cab(predio["sindico"]), json={
        "unidade_id": predio["u204"], "competencia": COMPETENCIA,
        "descricao": "Taxa de condomínio", "valor": "320.00"})
    assert r.status_code == 201, r.text
    assert r.json()["vencimento"].endswith("-20")


def test_morador_novo_nao_ve_os_visitantes_e_encomendas_do_anterior(cliente, db):
    """O visitante da Carla (nome, CPF e foto) é dado pessoal: a Ana, que
    entrou no apartamento depois, não o vê. A encomenda que ainda está na
    portaria aparece, para a Ana poder dizer que não é dela."""
    from tests.test_portaria import registrar_encomenda, registrar_visitante
    from tests.test_portaria_fotos import enviar_foto

    base = montar_condominio(cliente, db)
    carla_id, tok_carla = cadastrar_morador(
        cliente, base["sindico"], base["cond"], email="carla@exemplo.com", cpf=CPFS[3],
        unidade="204")
    _, porteiro = cadastrar_porteiro(cliente, base["sindico"], base["cond"], cpf=CPFS[2])
    u204 = next(u["id"] for u in cliente.get("/api/v1/condominios/meu/unidades",
                                            headers=cab(base["sindico"])).json()
                if u["numero"] == "204")

    antigo = registrar_visitante(cliente, porteiro, u204).json()
    assert enviar_foto(cliente, porteiro,
                       f"/portaria/visitantes/{antigo['id']}/foto").status_code == 200
    entregue = registrar_encomenda(cliente, porteiro, u204).json()
    cliente.post(f"/api/v1/portaria/encomendas/{entregue['id']}/retirada",
                 headers=cab(tok_carla), json={"confirmada": True})
    parada = registrar_encomenda(cliente, porteiro, u204).json()
    cliente.delete(f"/api/v1/usuarios/{carla_id}", headers=cab(base["sindico"]))

    _, ana = cadastrar_morador(cliente, base["sindico"], base["cond"],
                               email="ana@exemplo.com", cpf=CPFS[1], unidade="204")
    novo = registrar_visitante(cliente, porteiro, u204).json()

    visitantes = cliente.get("/api/v1/portaria/visitantes", headers=cab(ana)).json()
    assert [v["id"] for v in visitantes] == [novo["id"]]
    assert cliente.get(f"/api/v1/portaria/visitantes/{antigo['id']}/foto",
                       headers=cab(ana)).status_code == 404
    assert cliente.post(f"/api/v1/portaria/visitantes/{antigo['id']}/confirmacao",
                        headers=cab(ana), json={"confirmado": True}).status_code == 404
    encomendas = cliente.get("/api/v1/portaria/encomendas", headers=cab(ana)).json()
    assert [e["id"] for e in encomendas] == [parada["id"]]
    # O síndico continua vendo tudo.
    todos = cliente.get("/api/v1/portaria/visitantes", headers=cab(base["sindico"])).json()
    assert {v["id"] for v in todos} == {antigo["id"], novo["id"]}


def test_transferido_e_reativado_so_veem_o_que_chegou_depois(cliente, db):
    """O morador transferido de apartamento não vê os visitantes de quem
    estava no novo antes dele; quem saiu e voltou não vê o que chegou para
    outro morador no meio tempo."""
    from tests.test_portaria import registrar_visitante

    base = montar_condominio(cliente, db)
    ana_id, ana = cadastrar_morador(cliente, base["sindico"], base["cond"],
                                    email="ana@exemplo.com", cpf=CPFS[1], unidade="204")
    _, porteiro = cadastrar_porteiro(cliente, base["sindico"], base["cond"], cpf=CPFS[2])
    unidades = cliente.get("/api/v1/condominios/meu/unidades", headers=cab(base["sindico"])).json()
    cliente.post("/api/v1/condominios/meu/unidades", headers=cab(base["sindico"]),
                 json={"numero": "305"})
    u305 = next(u["id"] for u in cliente.get("/api/v1/condominios/meu/unidades",
                                            headers=cab(base["sindico"])).json()
                if u["numero"] == "305")
    u204 = next(u["id"] for u in unidades if u["numero"] == "204")

    antes_da_mudanca = registrar_visitante(cliente, porteiro, u305).json()
    r = cliente.put(f"/api/v1/usuarios/{ana_id}", headers=cab(base["sindico"]),
                    json={"unidade_numero": "305"})
    assert r.status_code == 200, r.text
    depois = registrar_visitante(cliente, porteiro, u305).json()
    vistos = [v["id"] for v in cliente.get("/api/v1/portaria/visitantes", headers=cab(ana)).json()]
    assert vistos == [depois["id"]]
    assert antes_da_mudanca["id"] not in vistos

    # Sai, chega visitante para a unidade, volta: não vê o do meio tempo.
    cliente.delete(f"/api/v1/usuarios/{ana_id}", headers=cab(base["sindico"]))
    no_meio = registrar_visitante(cliente, porteiro, u305).json()
    assert cliente.put(f"/api/v1/usuarios/{ana_id}", headers=cab(base["sindico"]),
                       json={"status": "ativo"}).status_code == 200
    ana = cliente.post("/api/v1/auth/login", json={
        "email": "ana@exemplo.com", "senha": "senhaforte123"}).json()["access_token"]
    vistos = [v["id"] for v in cliente.get("/api/v1/portaria/visitantes", headers=cab(ana)).json()]
    assert no_meio["id"] not in vistos
    assert u204  # a unidade antiga continua existindo

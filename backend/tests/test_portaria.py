"""Testes da portaria — seção 6 da documentação (vídeo porteiro,
confirmação do visitante e notificação de encomenda) e seção 9
(as permissões que o síndico definiu para o porteiro)."""
from __future__ import annotations

import pytest

from tests.fixtures import (
    CPFS, cab, cadastrar_morador, cadastrar_porteiro, criar_espaco, montar_condominio,
)

DOC_VISITANTE = CPFS[6]


@pytest.fixture
def cenario(cliente, db):
    base = montar_condominio(cliente, db)
    tok_sindico, cond = base["sindico"], base["cond"]

    _, tok_ana = cadastrar_morador(
        cliente, tok_sindico, cond, email="ana@exemplo.com", cpf=CPFS[1], unidade="204"
    )
    _, tok_bruno = cadastrar_morador(
        cliente, tok_sindico, cond, email="bruno@exemplo.com", cpf=CPFS[3], unidade="301"
    )
    _, tok_porteiro = cadastrar_porteiro(cliente, tok_sindico, cond, cpf=CPFS[2])

    unidades = cliente.get("/api/v1/condominios/meu/unidades", headers=cab(tok_sindico)).json()
    u204 = next(u for u in unidades if u["numero"] == "204")
    u301 = next(u for u in unidades if u["numero"] == "301")

    return {
        "cond": cond, "sindico": tok_sindico, "ana": tok_ana, "bruno": tok_bruno,
        "porteiro": tok_porteiro, "u204": u204["id"], "u301": u301["id"],
    }


def registrar_visitante(cliente, tok, unidade_id, **extra):
    corpo = {
        "unidade_id": unidade_id, "nome": "Marcos Alves", "documento": DOC_VISITANTE,
        "tipo_visita": "Visita pessoal",
        "foto_url": "https://cdn.exemplo.com/videoporteiro/1.jpg",
    }
    corpo.update(extra)
    return cliente.post("/api/v1/portaria/visitantes", json=corpo, headers=cab(tok))


def registrar_encomenda(cliente, tok, unidade_id, **extra):
    corpo = {
        "unidade_id": unidade_id, "remetente": "Correios", "tipo_volume": "Caixa média",
        "codigo_rastreio": "BR987654321",
        "foto_url": "https://cdn.exemplo.com/encomendas/1.jpg",
    }
    corpo.update(extra)
    return cliente.post("/api/v1/portaria/encomendas", json=corpo, headers=cab(tok))


# ── Vídeo porteiro e confirmação (seção 6) ───────────────────────────
def test_visitante_entra_aguardando_confirmacao_com_a_foto(cliente, cenario):
    r = registrar_visitante(cliente, cenario["porteiro"], cenario["u204"])
    assert r.status_code == 201, r.text
    v = r.json()
    assert v["status"] == "aguardando_confirmacao"
    assert v["foto_url"] == "https://cdn.exemplo.com/videoporteiro/1.jpg"
    assert v["unidade"] == "204"
    assert v["entrada_em"] is None


def test_morador_confirma_a_entrada(cliente, cenario):
    v = registrar_visitante(cliente, cenario["porteiro"], cenario["u204"]).json()

    r = cliente.post(
        f"/api/v1/portaria/visitantes/{v['id']}/confirmacao",
        json={"confirmado": True}, headers=cab(cenario["ana"]),
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "dentro"
    assert r.json()["entrada_em"] is not None


def test_morador_recusa_a_entrada(cliente, cenario):
    v = registrar_visitante(cliente, cenario["porteiro"], cenario["u204"]).json()

    r = cliente.post(
        f"/api/v1/portaria/visitantes/{v['id']}/confirmacao",
        json={"confirmado": False}, headers=cab(cenario["ana"]),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "recusado"
    assert r.json()["entrada_em"] is None


def test_so_o_morador_da_unidade_visitada_responde(cliente, cenario):
    """O visitante é da 204; o morador da 301 não pode responder."""
    v = registrar_visitante(cliente, cenario["porteiro"], cenario["u204"]).json()

    r = cliente.post(
        f"/api/v1/portaria/visitantes/{v['id']}/confirmacao",
        json={"confirmado": True}, headers=cab(cenario["bruno"]),
    )
    assert r.status_code == 404


def test_porteiro_nao_confirma_no_lugar_do_morador(cliente, cenario):
    v = registrar_visitante(cliente, cenario["porteiro"], cenario["u204"]).json()
    r = cliente.post(
        f"/api/v1/portaria/visitantes/{v['id']}/confirmacao",
        json={"confirmado": True}, headers=cab(cenario["porteiro"]),
    )
    assert r.status_code == 403


def test_nao_responde_duas_vezes(cliente, cenario):
    v = registrar_visitante(cliente, cenario["porteiro"], cenario["u204"]).json()
    corpo = {"confirmado": True}
    url = f"/api/v1/portaria/visitantes/{v['id']}/confirmacao"
    assert cliente.post(url, json=corpo, headers=cab(cenario["ana"])).status_code == 200
    assert cliente.post(url, json=corpo, headers=cab(cenario["ana"])).status_code == 409


def test_morador_so_ve_os_visitantes_da_propria_unidade(cliente, cenario):
    registrar_visitante(cliente, cenario["porteiro"], cenario["u204"], nome="Visita da Ana")
    registrar_visitante(
        cliente, cenario["porteiro"], cenario["u301"], nome="Visita do Bruno", documento=CPFS[7]
    )

    da_ana = cliente.get("/api/v1/portaria/visitantes", headers=cab(cenario["ana"])).json()
    assert [v["nome"] for v in da_ana] == ["Visita da Ana"]

    do_porteiro = cliente.get(
        "/api/v1/portaria/visitantes", headers=cab(cenario["porteiro"])
    ).json()
    assert len(do_porteiro) == 2


def test_saida_so_apos_a_entrada(cliente, cenario):
    v = registrar_visitante(cliente, cenario["porteiro"], cenario["u204"]).json()

    cedo = cliente.post(
        f"/api/v1/portaria/visitantes/{v['id']}/saida", headers=cab(cenario["porteiro"])
    )
    assert cedo.status_code == 409

    cliente.post(
        f"/api/v1/portaria/visitantes/{v['id']}/confirmacao",
        json={"confirmado": True}, headers=cab(cenario["ana"]),
    )
    r = cliente.post(
        f"/api/v1/portaria/visitantes/{v['id']}/saida", headers=cab(cenario["porteiro"])
    )
    assert r.status_code == 200
    assert r.json()["status"] == "saiu"
    assert r.json()["saida_em"] is not None


# ── Permissões do porteiro (seção 9) ─────────────────────────────────
def test_porteiro_sem_permissao_nao_registra_visitante(cliente, cenario):
    """Documentação, seção 9: vale o que o síndico liberou."""
    porteiro_id, tok = cadastrar_porteiro(
        cliente, cenario["sindico"], cenario["cond"],
        email="limitado@exemplo.com", cpf=CPFS[4],
        permissoes={
            "registrar_visitantes": False, "registrar_encomendas": True,
            "registrar_veiculos": False, "registrar_ocorrencias": False,
            "acessar_financeiro": False,
        },
    )
    bloqueado = registrar_visitante(cliente, tok, cenario["u204"])
    assert bloqueado.status_code == 403
    assert "não liberou" in bloqueado.json()["detalhe"]

    # A encomenda, que foi liberada, passa.
    assert registrar_encomenda(cliente, tok, cenario["u204"]).status_code == 201


def test_permissao_revogada_passa_a_valer(cliente, cenario):
    porteiro_id, tok = cadastrar_porteiro(
        cliente, cenario["sindico"], cenario["cond"],
        email="revog@exemplo.com", cpf=CPFS[5],
    )
    assert registrar_visitante(cliente, tok, cenario["u204"]).status_code == 201

    cliente.put(
        f"/api/v1/usuarios/porteiros/{porteiro_id}/permissoes",
        json={
            "registrar_visitantes": False, "registrar_encomendas": True,
            "registrar_veiculos": True, "registrar_ocorrencias": True,
            "acessar_financeiro": False,
        },
        headers=cab(cenario["sindico"]),
    )
    assert registrar_visitante(cliente, tok, cenario["u204"]).status_code == 403


def test_morador_nao_registra_visitante(cliente, cenario):
    r = registrar_visitante(cliente, cenario["ana"], cenario["u204"])
    assert r.status_code == 403


def test_sindico_registra_mesmo_sem_registro_de_permissoes(cliente, cenario):
    r = registrar_visitante(cliente, cenario["sindico"], cenario["u204"])
    assert r.status_code == 201


# ── Encomendas (seção 6) ─────────────────────────────────────────────
def test_encomenda_com_foto_fica_aguardando_retirada(cliente, cenario):
    r = registrar_encomenda(cliente, cenario["porteiro"], cenario["u204"])
    assert r.status_code == 201, r.text
    e = r.json()
    assert e["status"] == "aguardando_retirada"
    assert e["foto_url"] == "https://cdn.exemplo.com/encomendas/1.jpg"
    assert e["codigo_rastreio"] == "BR987654321"


def test_morador_confirma_a_retirada(cliente, cenario):
    e = registrar_encomenda(cliente, cenario["porteiro"], cenario["u204"]).json()
    r = cliente.post(
        f"/api/v1/portaria/encomendas/{e['id']}/retirada",
        json={"confirmada": True}, headers=cab(cenario["ana"]),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "retirada"
    assert r.json()["retirada_em"] is not None


def test_morador_diz_que_a_encomenda_nao_e_dele(cliente, cenario):
    e = registrar_encomenda(cliente, cenario["porteiro"], cenario["u204"]).json()
    r = cliente.post(
        f"/api/v1/portaria/encomendas/{e['id']}/retirada",
        json={"confirmada": False}, headers=cab(cenario["ana"]),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "recusada"


def test_morador_nao_retira_encomenda_de_outra_unidade(cliente, cenario):
    e = registrar_encomenda(cliente, cenario["porteiro"], cenario["u204"]).json()
    r = cliente.post(
        f"/api/v1/portaria/encomendas/{e['id']}/retirada",
        json={"confirmada": True}, headers=cab(cenario["bruno"]),
    )
    assert r.status_code == 404


def test_morador_so_ve_as_proprias_encomendas(cliente, cenario):
    registrar_encomenda(cliente, cenario["porteiro"], cenario["u204"], remetente="Amazon")
    registrar_encomenda(cliente, cenario["porteiro"], cenario["u301"], remetente="Shopee")

    da_ana = cliente.get("/api/v1/portaria/encomendas", headers=cab(cenario["ana"])).json()
    assert [e["remetente"] for e in da_ana] == ["Amazon"]


def test_unidade_de_outro_condominio_e_recusada(cliente, db, cenario):
    outra = montar_condominio(
        cliente, db, nome="Outro Condominio", cnpj="45.997.418/0001-53",
        email_sindico="outro@exemplo.com", cpf_sindico=CPFS[4],
        email_admin="admin2@exemplo.com", cpf_admin=CPFS[7],
    )
    outro = outra["sindico"]
    r = registrar_visitante(cliente, outro, cenario["u204"])
    assert r.status_code == 404


# ── Ocorrências ──────────────────────────────────────────────────────
def test_morador_abre_e_sindico_responde(cliente, cenario):
    abertura = cliente.post(
        "/api/v1/portaria/ocorrencias",
        json={
            "titulo": "Barulho no 302", "descricao": "Som alto depois das 23h.",
            "categoria": "convivencia",
        },
        headers=cab(cenario["ana"]),
    )
    assert abertura.status_code == 201, abertura.text
    o = abertura.json()
    assert o["status"] == "aberta"
    assert o["unidade"] == "204"

    resposta = cliente.post(
        f"/api/v1/portaria/ocorrencias/{o['id']}/resposta",
        json={"status": "resolvida", "resposta": "Aviso verbal dado ao morador."},
        headers=cab(cenario["sindico"]),
    )
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "resolvida"


def test_morador_so_ve_as_proprias_ocorrencias(cliente, cenario):
    cliente.post(
        "/api/v1/portaria/ocorrencias",
        json={"titulo": "Da Ana", "descricao": "Descricao da Ana."},
        headers=cab(cenario["ana"]),
    )
    cliente.post(
        "/api/v1/portaria/ocorrencias",
        json={"titulo": "Do Bruno", "descricao": "Descricao do Bruno."},
        headers=cab(cenario["bruno"]),
    )

    da_ana = cliente.get("/api/v1/portaria/ocorrencias", headers=cab(cenario["ana"])).json()
    assert [o["titulo"] for o in da_ana] == ["Da Ana"]

    do_sindico = cliente.get(
        "/api/v1/portaria/ocorrencias", headers=cab(cenario["sindico"])
    ).json()
    assert len(do_sindico) == 2


def test_porteiro_sem_permissao_nao_abre_ocorrencia(cliente, cenario):
    _, tok = cadastrar_porteiro(
        cliente, cenario["sindico"], cenario["cond"],
        email="semocr@exemplo.com", cpf=CPFS[4],
        permissoes={
            "registrar_visitantes": True, "registrar_encomendas": True,
            "registrar_veiculos": True, "registrar_ocorrencias": False,
            "acessar_financeiro": False,
        },
    )
    r = cliente.post(
        "/api/v1/portaria/ocorrencias",
        json={"titulo": "Teste", "descricao": "Descricao qualquer."},
        headers=cab(tok),
    )
    assert r.status_code == 403


def test_morador_nao_responde_ocorrencia(cliente, cenario):
    o = cliente.post(
        "/api/v1/portaria/ocorrencias",
        json={"titulo": "Da Ana", "descricao": "Descricao da Ana."},
        headers=cab(cenario["ana"]),
    ).json()
    r = cliente.post(
        f"/api/v1/portaria/ocorrencias/{o['id']}/resposta",
        json={"status": "resolvida", "resposta": "Eu mesma resolvo."},
        headers=cab(cenario["ana"]),
    )
    assert r.status_code == 403

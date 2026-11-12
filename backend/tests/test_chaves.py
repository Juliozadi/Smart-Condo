"""Controle de chaves na portaria.

Situação real: a portaria guarda a chave do salão, da piscina, da casa
de máquinas — e a do apartamento que o morador deixa para a diarista ou
para o eletricista. Ninguém sabia quem tinha levado a chave do salão, e
a chave de um apartamento entregue à pessoa errada é a porta aberta para
um furto. Agora cada chave tem dono do registro: quem retirou, quando,
quem entregou e quem recebeu de volta; a do apartamento só sai para quem
mora lá ou para quem o morador autorizou, com o CPF conferido.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from app.core.tempo import hoje_local
from app.services import notificacao
from tests.fixtures import cab, montar_condominio
from tests.test_autorizacao_visita import autorizar
from tests.test_portaria import DOC_VISITANTE, cenario  # noqa: F401

URL = "/api/v1/chaves"


def criar(cliente, tok, nome="Salão de festas", **extra):
    return cliente.post(URL, json={"nome": nome, **extra}, headers=cab(tok))


def retirar(cliente, tok, chave_id, **corpo):
    return cliente.post(f"{URL}/{chave_id}/retirada", json=corpo, headers=cab(tok))


def devolver(cliente, tok, chave_id):
    return cliente.post(f"{URL}/{chave_id}/devolucao", json={}, headers=cab(tok))


@pytest.fixture
def avisos(monkeypatch):
    lista = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: lista.append((destino, mensagem)))
    return lista


def test_chave_da_area_comum_sai_e_volta(cliente, cenario):
    p = cenario["porteiro"]
    r = criar(cliente, cenario["sindico"], posicao="A1")
    assert r.status_code == 201, r.text
    chave = r.json()
    assert chave["na_portaria"] is True and chave["unidade"] is None

    r = retirar(cliente, p, chave["id"], nome="Carla, da limpeza do salão",
                documento="12.345.678-9")
    assert r.status_code == 201, r.text
    lista = cliente.get(URL, headers=cab(p)).json()
    assert lista[0]["na_portaria"] is False
    assert lista[0]["com"] == "Carla, da limpeza do salão"

    # Não sai duas vezes ao mesmo tempo.
    assert retirar(cliente, p, chave["id"], nome="Outra pessoa").status_code == 409

    assert devolver(cliente, p, chave["id"]).status_code == 200
    assert devolver(cliente, p, chave["id"]).status_code == 409
    historico = cliente.get(f"{URL}/{chave['id']}/movimentacoes", headers=cab(p)).json()
    assert len(historico) == 1
    h = historico[0]
    assert h["retirada_por_nome"] == "Carla, da limpeza do salão"
    assert h["devolvida_em"] and h["retirada_registrada_por_nome"] == "Carlos Pereira"
    assert h["devolucao_registrada_por_nome"] == "Carlos Pereira"


def test_chave_da_area_comum_pede_o_nome(cliente, cenario):
    chave = criar(cliente, cenario["sindico"]).json()
    assert retirar(cliente, cenario["porteiro"], chave["id"]).status_code == 422


def test_chave_do_apartamento_sai_para_quem_mora(cliente, cenario, avisos):
    c = cenario
    chave = criar(cliente, c["porteiro"], nome="Apto 204 — cópia", unidade_id=c["u204"]).json()
    assert chave["unidade"] == "204"
    quem = cliente.get(f"{URL}/{chave['id']}/quem-pode-retirar", headers=cab(c["porteiro"])).json()
    morador = next(q for q in quem if q["tipo"] == "morador")

    # Um nome qualquer não leva a chave do apartamento.
    r = retirar(cliente, c["porteiro"], chave["id"], nome="Fulano que diz ser primo")
    assert r.status_code == 403
    r = retirar(cliente, c["porteiro"], chave["id"], morador_id=morador["id"])
    assert r.status_code == 201, r.text
    assert r.json()["retirada_por_nome"] == morador["nome"]
    # O apartamento fica sabendo.
    assert [destino for destino, _ in avisos] == ["ana@exemplo.com"]


def test_morador_de_outro_apartamento_nao_leva(cliente, cenario):
    c = cenario
    chave = criar(cliente, c["porteiro"], nome="Apto 204", unidade_id=c["u204"]).json()
    eu_bruno = cliente.get("/api/v1/auth/eu", headers=cab(c["bruno"])).json()
    r = retirar(cliente, c["porteiro"], chave["id"], morador_id=eu_bruno["id"])
    assert r.status_code == 403


def test_autorizado_pelo_morador_leva_com_o_cpf(cliente, cenario, avisos):
    c = cenario
    a = autorizar(cliente, c["ana"], documento=DOC_VISITANTE, pode_retirar_chave=True).json()
    assert a["pode_retirar_chave"] is True
    chave = criar(cliente, c["porteiro"], nome="Apto 204", unidade_id=c["u204"]).json()
    quem = cliente.get(f"{URL}/{chave['id']}/quem-pode-retirar", headers=cab(c["porteiro"])).json()
    autorizada = next(q for q in quem if q["tipo"] == "autorizacao")
    assert autorizada["id"] == a["id"] and autorizada["nome"] == "Maria Diarista"
    # A portaria vê só o meio do CPF e digita o do documento apresentado.
    assert autorizada["documento"].startswith("***.")

    r = retirar(cliente, c["porteiro"], chave["id"], autorizacao_id=a["id"], documento="52998224725")
    assert r.status_code == 403
    r = retirar(cliente, c["porteiro"], chave["id"], autorizacao_id=a["id"], documento=DOC_VISITANTE)
    assert r.status_code == 201, r.text
    assert r.json()["retirada_por_nome"] == "Maria Diarista"
    assert "Maria Diarista" in avisos[-1][1]


def test_autorizacao_sem_a_chave_nao_serve(cliente, cenario):
    c = cenario
    a = autorizar(cliente, c["ana"], documento=DOC_VISITANTE).json()
    assert a["pode_retirar_chave"] is False
    chave = criar(cliente, c["porteiro"], nome="Apto 204", unidade_id=c["u204"]).json()
    r = retirar(cliente, c["porteiro"], chave["id"], autorizacao_id=a["id"], documento=DOC_VISITANTE)
    assert r.status_code == 403


def test_autorizacao_fora_do_dia_nao_serve(cliente, cenario):
    c = cenario
    amanha = (hoje_local() + timedelta(days=1)).isoformat()
    a = autorizar(cliente, c["ana"], documento=DOC_VISITANTE, pode_retirar_chave=True,
                  valida_de=amanha).json()
    chave = criar(cliente, c["porteiro"], nome="Apto 204", unidade_id=c["u204"]).json()
    r = retirar(cliente, c["porteiro"], chave["id"], autorizacao_id=a["id"], documento=DOC_VISITANTE)
    assert r.status_code == 403


def test_chave_exige_cpf_na_autorizacao(cliente, cenario):
    r = autorizar(cliente, cenario["ana"], pode_retirar_chave=True)
    assert r.status_code == 422


def test_autorizacao_de_outro_apartamento_nao_serve(cliente, cenario):
    c = cenario
    a = autorizar(cliente, c["bruno"], documento=DOC_VISITANTE, pode_retirar_chave=True).json()
    chave = criar(cliente, c["porteiro"], nome="Apto 204", unidade_id=c["u204"]).json()
    r = retirar(cliente, c["porteiro"], chave["id"], autorizacao_id=a["id"], documento=DOC_VISITANTE)
    assert r.status_code == 403


def test_morador_ve_so_as_chaves_do_apartamento(cliente, cenario):
    c = cenario
    criar(cliente, c["sindico"])
    chave = criar(cliente, c["porteiro"], nome="Apto 204", unidade_id=c["u204"]).json()
    criar(cliente, c["porteiro"], nome="Apto 301", unidade_id=c["u301"])
    assert [k["nome"] for k in cliente.get(URL, headers=cab(c["ana"])).json()] == ["Apto 204"]
    # E não cadastra, não retira, não devolve.
    assert criar(cliente, c["ana"], nome="Minha chave").status_code == 403
    assert retirar(cliente, c["ana"], chave["id"], nome="Eu").status_code == 403
    assert cliente.get(f"{URL}/{chave['id']}/quem-pode-retirar",
                       headers=cab(c["ana"])).status_code == 403
    # O histórico da chave dela, sim.
    assert cliente.get(f"{URL}/{chave['id']}/movimentacoes", headers=cab(c["ana"])).status_code == 200
    outra = cliente.get(URL, headers=cab(c["porteiro"])).json()
    da_301 = next(k for k in outra if k["unidade"] == "301")
    assert cliente.get(f"{URL}/{da_301['id']}/movimentacoes",
                       headers=cab(c["ana"])).status_code == 404


def test_nome_repetido_e_remocao(cliente, cenario):
    c = cenario
    chave = criar(cliente, c["sindico"]).json()
    assert criar(cliente, c["porteiro"], nome="SALÃO DE FESTAS").status_code == 409
    retirar(cliente, c["porteiro"], chave["id"], nome="Carla")
    # Fora da portaria, não se remove: primeiro ela volta.
    assert cliente.delete(f"{URL}/{chave['id']}", headers=cab(c["sindico"])).status_code == 409
    devolver(cliente, c["porteiro"], chave["id"])
    assert cliente.delete(f"{URL}/{chave['id']}", headers=cab(c["sindico"])).status_code == 200
    assert cliente.get(URL, headers=cab(c["sindico"])).json() == []
    assert criar(cliente, c["sindico"]).status_code == 201


def test_editar(cliente, cenario):
    chave = criar(cliente, cenario["sindico"], posicao="A1").json()
    r = cliente.put(f"{URL}/{chave['id']}", json={"posicao": "B3", "observacao": "Chave reserva"},
                    headers=cab(cenario["porteiro"]))
    assert r.status_code == 200, r.text
    assert r.json()["posicao"] == "B3" and r.json()["observacao"] == "Chave reserva"


@pytest.mark.parametrize("corpo", [{"nome": ""}, {"nome": "x" * 81}, {"nome": "Ok", "posicao": "x" * 21}])
def test_cadastro_invalido(cliente, cenario, corpo):
    assert cliente.post(URL, json=corpo, headers=cab(cenario["sindico"])).status_code == 422


def test_outro_condominio_nao_alcanca(cliente, db, cenario):
    c = cenario
    chave = criar(cliente, c["sindico"]).json()
    outro = montar_condominio(cliente, db, nome="Outro", cnpj="11.444.777/0001-61",
                              email_sindico="s2@exemplo.com", cpf_sindico="52998224725",
                              email_admin="a2@exemplo.com", cpf_admin="16899535009")
    s2 = outro["sindico"]
    assert cliente.get(URL, headers=cab(s2)).json() == []
    assert retirar(cliente, s2, chave["id"], nome="Invasor").status_code == 404
    assert devolver(cliente, s2, chave["id"]).status_code == 404
    assert cliente.get(f"{URL}/{chave['id']}/movimentacoes", headers=cab(s2)).status_code == 404
    assert cliente.delete(f"{URL}/{chave['id']}", headers=cab(s2)).status_code == 404
    # Nem cadastra chave para apartamento de outro condomínio.
    assert criar(cliente, s2, nome="Apto 204", unidade_id=c["u204"]).status_code == 404

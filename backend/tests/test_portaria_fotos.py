"""Testes das fotos de visitantes e encomendas (vídeo porteiro, seção 6).

O que estes testes protegem: a foto é dado pessoal de terceiros (LGPD).
Ela só é gravada se for imagem de verdade, não tem endereço público e só
sai para quem tem direito — a portaria com a permissão, o síndico e o
morador da unidade. Depois do prazo de guarda, o arquivo é apagado.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models.portaria import Visitante
from app.services import arquivos
from tests.fixtures import CPFS, cab, cadastrar_porteiro, montar_condominio
from tests.test_portaria import cenario, registrar_encomenda, registrar_visitante  # noqa: F401

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


def enviar_foto(cliente, tok, caminho, conteudo=PNG, nome="foto.png", tipo="image/png"):
    return cliente.put(
        f"/api/v1{caminho}", files={"arquivo": (nome, conteudo, tipo)}, headers=cab(tok)
    )


def visitante_com_foto(cliente, cenario, conteudo=PNG):
    v = registrar_visitante(cliente, cenario["porteiro"], cenario["u204"]).json()
    r = enviar_foto(cliente, cenario["porteiro"], f"/portaria/visitantes/{v['id']}/foto", conteudo)
    assert r.status_code == 200, r.text
    return r.json()


def pasta_da_portaria():
    return arquivos._pasta(arquivos.PORTARIA)


# ── Envio ────────────────────────────────────────────────────────────
def test_porteiro_envia_a_foto_e_o_morador_da_unidade_ve(cliente, cenario):
    v = visitante_com_foto(cliente, cenario)
    assert v["foto_url"] == f"/portaria/visitantes/{v['id']}/foto"

    r = cliente.get(f"/api/v1{v['foto_url']}", headers=cab(cenario["ana"]))
    assert r.status_code == 200
    assert r.content == PNG
    assert r.headers["content-type"] == "image/png"
    # Dado pessoal: o navegador não guarda cópia.
    assert "no-store" in r.headers["cache-control"]

    # A listagem do morador traz o caminho da foto.
    lista = cliente.get("/api/v1/portaria/visitantes", headers=cab(cenario["ana"])).json()
    assert lista[0]["foto_url"] == v["foto_url"]


def test_arquivo_que_nao_e_imagem_e_recusado(cliente, cenario):
    v = registrar_visitante(cliente, cenario["porteiro"], cenario["u204"]).json()
    r = enviar_foto(
        cliente, cenario["porteiro"], f"/portaria/visitantes/{v['id']}/foto",
        b"<html><script>alert(1)</script></html>", nome="foto.jpg", tipo="image/jpeg",
    )
    assert r.status_code == 422
    assert list(pasta_da_portaria().iterdir()) == []


def test_foto_grande_demais_e_recusada(cliente, cenario):
    from app.core.config import settings

    v = registrar_visitante(cliente, cenario["porteiro"], cenario["u204"]).json()
    grande = PNG + b"\x00" * (settings.FOTO_MAX_KB * 1024)
    r = enviar_foto(cliente, cenario["porteiro"], f"/portaria/visitantes/{v['id']}/foto", grande)
    assert r.status_code == 422


def test_endereco_de_foto_no_registro_e_ignorado(cliente, cenario):
    """Antes a foto era um endereço livre: dava para a portaria fazer a tela
    do morador carregar uma imagem de um servidor qualquer."""
    r = registrar_visitante(
        cliente, cenario["porteiro"], cenario["u204"],
        foto_url="https://rastreador.exemplo.com/pixel.png",
    )
    assert r.status_code == 201
    assert r.json()["foto_url"] is None


def test_trocar_a_foto_apaga_a_anterior(cliente, cenario):
    v = visitante_com_foto(cliente, cenario, PNG)
    assert len(list(pasta_da_portaria().iterdir())) == 1
    r = enviar_foto(cliente, cenario["porteiro"], f"/portaria/visitantes/{v['id']}/foto", JPG)
    assert r.status_code == 200
    arquivos_no_disco = list(pasta_da_portaria().iterdir())
    assert len(arquivos_no_disco) == 1
    assert arquivos_no_disco[0].suffix == ".jpg"


def test_foto_nao_muda_depois_da_resposta_do_morador(cliente, cenario):
    v = visitante_com_foto(cliente, cenario)
    cliente.post(
        f"/api/v1/portaria/visitantes/{v['id']}/confirmacao",
        json={"confirmado": False}, headers=cab(cenario["ana"]),
    )
    r = enviar_foto(cliente, cenario["porteiro"], f"/portaria/visitantes/{v['id']}/foto", JPG)
    assert r.status_code == 409


def test_morador_nao_envia_foto(cliente, cenario):
    v = registrar_visitante(cliente, cenario["porteiro"], cenario["u204"]).json()
    r = enviar_foto(cliente, cenario["ana"], f"/portaria/visitantes/{v['id']}/foto")
    assert r.status_code == 403


# ── Quem pode ver ────────────────────────────────────────────────────
def test_morador_de_outra_unidade_nao_ve(cliente, cenario):
    v = visitante_com_foto(cliente, cenario)
    r = cliente.get(f"/api/v1{v['foto_url']}", headers=cab(cenario["bruno"]))
    # 404, e não 403: nem confirma que o visitante existe.
    assert r.status_code == 404


def test_sem_token_nao_ve(cliente, cenario):
    v = visitante_com_foto(cliente, cenario)
    assert cliente.get(f"/api/v1{v['foto_url']}").status_code == 401


def test_sindico_ve(cliente, cenario):
    v = visitante_com_foto(cliente, cenario)
    assert cliente.get(f"/api/v1{v['foto_url']}", headers=cab(cenario["sindico"])).status_code == 200


def test_porteiro_sem_a_permissao_nao_ve(cliente, cenario):
    v = visitante_com_foto(cliente, cenario)
    _, tok = cadastrar_porteiro(
        cliente, cenario["sindico"], cenario["cond"],
        email="limitado@exemplo.com", cpf=CPFS[4],
        permissoes={
            "registrar_visitantes": False, "registrar_encomendas": True,
            "registrar_veiculos": False, "registrar_ocorrencias": False,
            "acessar_financeiro": False,
        },
    )
    assert cliente.get(f"/api/v1{v['foto_url']}", headers=cab(tok)).status_code == 404


def test_sindico_de_outro_condominio_nao_ve(cliente, db, cenario):
    v = visitante_com_foto(cliente, cenario)
    outro = montar_condominio(
        cliente, db, nome="Edifício Aurora", cnpj="04.252.011/0001-10",
        email_sindico="sindico2@exemplo.com", cpf_sindico=CPFS[4],
        email_admin="admin2@exemplo.com", cpf_admin=CPFS[5],
    )
    assert cliente.get(f"/api/v1{v['foto_url']}", headers=cab(outro["sindico"])).status_code == 404


def test_foto_da_portaria_nao_sai_pela_rota_publica(cliente, cenario):
    visitante_com_foto(cliente, cenario)
    nome = next(pasta_da_portaria().iterdir()).name
    assert cliente.get(f"/api/v1/arquivos/fotos/{nome}").status_code == 404


# ── Encomendas ───────────────────────────────────────────────────────
def test_foto_da_encomenda(cliente, cenario):
    e = registrar_encomenda(cliente, cenario["porteiro"], cenario["u204"]).json()
    r = enviar_foto(cliente, cenario["porteiro"], f"/portaria/encomendas/{e['id']}/foto", JPG)
    assert r.status_code == 200, r.text
    url = r.json()["foto_url"]
    assert url == f"/portaria/encomendas/{e['id']}/foto"

    assert cliente.get(f"/api/v1{url}", headers=cab(cenario["ana"])).content == JPG
    assert cliente.get(f"/api/v1{url}", headers=cab(cenario["bruno"])).status_code == 404

    cliente.post(
        f"/api/v1/portaria/encomendas/{e['id']}/retirada",
        json={"confirmada": True}, headers=cab(cenario["ana"]),
    )
    r = enviar_foto(cliente, cenario["porteiro"], f"/portaria/encomendas/{e['id']}/foto")
    assert r.status_code == 409


# ── Prazo de guarda (LGPD) ───────────────────────────────────────────
def test_foto_vencida_e_apagada_no_proximo_registro(cliente, db, cenario):
    from app.core.config import settings

    v = visitante_com_foto(cliente, cenario)
    assert len(list(pasta_da_portaria().iterdir())) == 1

    antigo = db.get(Visitante, v["id"])
    antigo.criado_em = datetime.now(timezone.utc) - timedelta(days=settings.FOTO_PORTARIA_DIAS + 1)
    db.commit()

    registrar_visitante(cliente, cenario["porteiro"], cenario["u204"])

    assert list(pasta_da_portaria().iterdir()) == []
    db.expire_all()
    assert db.get(Visitante, v["id"]).foto_arquivo is None
    r = cliente.get(f"/api/v1/portaria/visitantes/{v['id']}/foto", headers=cab(cenario["ana"]))
    assert r.status_code == 404

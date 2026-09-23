"""Testes da foto de perfil.

O que estes testes protegem: só entra imagem de verdade (a assinatura do
arquivo decide, não a extensão), o nome gravado nunca vem do usuário, a
foto antiga sai do disco quando é trocada, e o perfil não aceita mais um
endereço de foto escrito à mão.
"""
from __future__ import annotations

import pytest

from app.core.config import settings
from app.services import arquivos
from tests.fixtures import cab, cadastrar_morador, montar_condominio

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 64


@pytest.fixture(autouse=True)
def pasta_temporaria(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOADS_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def morador(cliente, db):
    cen = montar_condominio(cliente, db)
    _, tok = cadastrar_morador(cliente, cen["sindico"], cen["cond"])
    return tok


def enviar(cliente, tok, conteudo, nome="foto.png", tipo="image/png"):
    return cliente.put(
        "/api/v1/usuarios/eu/foto",
        files={"arquivo": (nome, conteudo, tipo)},
        headers=cab(tok),
    )


@pytest.mark.parametrize("conteudo,ext", [(PNG, "png"), (JPG, "jpg"), (WEBP, "webp")])
def test_envia_e_serve_a_foto(cliente, morador, conteudo, ext):
    r = enviar(cliente, morador, conteudo)
    assert r.status_code == 200, r.text
    url = r.json()["foto_url"]
    assert url.startswith("/arquivos/fotos/") and url.endswith("." + ext)

    servida = cliente.get("/api/v1" + url)
    assert servida.status_code == 200
    assert servida.content == conteudo
    assert servida.headers["content-type"] == arquivos.TIPOS[ext]


def test_recusa_arquivo_que_nao_e_imagem_mesmo_com_extensao_de_imagem(cliente, morador):
    """Um HTML renomeado para .png não pode ser servido de volta a ninguém."""
    r = enviar(cliente, morador, b"<html><script>alert(1)</script></html>", nome="x.png")
    assert r.status_code == 422
    assert "JPG, PNG ou WebP" in r.json()["detalhe"]


def test_recusa_arquivo_vazio_e_grande_demais(cliente, morador, monkeypatch):
    assert enviar(cliente, morador, b"").status_code == 422
    monkeypatch.setattr(settings, "FOTO_MAX_KB", 50)
    grande = PNG + b"\x00" * (51 * 1024)
    r = enviar(cliente, morador, grande)
    assert r.status_code == 422
    assert "MB" in r.json()["detalhe"]


def test_nome_gravado_nao_vem_do_usuario(cliente, morador, pasta_temporaria):
    r = enviar(cliente, morador, PNG, nome="../../app/main.py")
    assert r.status_code == 200
    gravados = list((pasta_temporaria / "fotos").iterdir())
    assert len(gravados) == 1
    assert "main" not in gravados[0].name and ".." not in gravados[0].name


def test_trocar_apaga_a_anterior_e_remover_limpa(cliente, morador, pasta_temporaria):
    primeira = enviar(cliente, morador, PNG).json()["foto_url"]
    segunda = enviar(cliente, morador, JPG).json()["foto_url"]
    assert primeira != segunda
    assert cliente.get("/api/v1" + primeira).status_code == 404
    assert len(list((pasta_temporaria / "fotos").iterdir())) == 1

    r = cliente.delete("/api/v1/usuarios/eu/foto", headers=cab(morador))
    assert r.status_code == 200
    assert r.json()["foto_url"] is None
    assert list((pasta_temporaria / "fotos").iterdir()) == []


def test_exige_sessao(cliente):
    r = cliente.put("/api/v1/usuarios/eu/foto", files={"arquivo": ("f.png", PNG, "image/png")})
    assert r.status_code == 401


@pytest.mark.parametrize("nome", ["..%2F..%2Fapp%2Fmain.py", "curto.png", "nome-valido-mas-inexistente-aaaaaa.png"])
def test_nomes_invalidos_ou_inexistentes_dao_404(cliente, nome):
    assert cliente.get(f"/api/v1/arquivos/fotos/{nome}").status_code == 404


def test_perfil_nao_aceita_mais_endereco_de_foto(cliente, morador):
    """A foto só muda pelo envio do arquivo."""
    r = cliente.patch(
        "/api/v1/usuarios/eu",
        json={"foto_url": "https://rastreador.exemplo.com/pixel.png"},
        headers=cab(morador),
    )
    perfil = cliente.get("/api/v1/auth/eu", headers=cab(morador)).json()
    assert perfil["foto_url"] is None
    assert r.status_code in (200, 422)

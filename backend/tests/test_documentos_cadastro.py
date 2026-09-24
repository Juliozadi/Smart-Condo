"""Testes dos documentos do cadastro do morador (seções 13.3 e 13.5.1).

O que estes testes protegem: o cadastro público devolve uma autorização
que serve só para enviar os documentos — não abre sessão, nem depois da
aprovação — e só enquanto o cadastro não foi avaliado. Só PDF e imagem de
verdade entram. Só o síndico do condomínio abre os arquivos, e a recusa
do cadastro os apaga (LGPD).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import FINALIDADE_DOCUMENTOS
from app.services import arquivos
from tests.fixtures import CPFS, cab, cadastrar_morador, cadastrar_porteiro, montar_condominio

PDF = b"%PDF-1.4\n" + b"0" * 64 + b"\n%%EOF"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture
def base(cliente, db):
    return montar_condominio(cliente, db)


def cadastrar(cliente, base, email="novo@exemplo.com", cpf=CPFS[1]):
    r = cliente.post(
        "/api/v1/auth/cadastro/morador",
        json={
            "nome": "Paula Nogueira", "email": email, "cpf": cpf,
            "telefone": "(67) 99999-0005", "senha": "senhaforte123",
            "codigo_condominio": base["cond"]["codigo_acesso"],
            "unidade_numero": "402", "tipo_ocupacao": "proprietario",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def confirmar(cliente, cadastro):
    r = cliente.post("/api/v1/auth/confirmar", json={
        "email": cadastro["usuario"]["email"], "codigo": cadastro["codigo_debug"],
    })
    assert r.status_code == 200, r.text


def enviar(cliente, token, tipo, conteudo=PDF, nome="doc.pdf", mime="application/pdf"):
    return cliente.put(
        f"/api/v1/auth/cadastro/documentos/{tipo}",
        files={"arquivo": (nome, conteudo, mime)},
        headers=cab(token),
    )


def pasta():
    return arquivos._pasta(arquivos.DOCUMENTOS)


# ── Envio ────────────────────────────────────────────────────────────
def test_cadastro_devolve_a_autorizacao_e_os_documentos_sao_gravados(cliente, base):
    cad = cadastrar(cliente, base)
    assert cad["token_documentos"]
    assert cad["token_documentos_expira_min"] == settings.TOKEN_DOCUMENTOS_MIN

    r = enviar(cliente, cad["token_documentos"], "identidade")
    assert r.status_code == 200, r.text
    assert [d["tipo"] for d in r.json()] == ["identidade"]

    # Enviar depois de confirmar o código também vale: o cadastro ainda
    # aguarda a aprovação.
    confirmar(cliente, cad)
    r = enviar(cliente, cad["token_documentos"], "comprovante_residencia", PNG, "conta.png", "image/png")
    assert r.status_code == 200, r.text
    docs = {d["tipo"]: d for d in r.json()}
    assert set(docs) == {"identidade", "comprovante_residencia"}
    assert docs["identidade"]["tipo_conteudo"] == "application/pdf"
    assert docs["comprovante_residencia"]["tipo_conteudo"] == "image/png"
    assert len(list(pasta().iterdir())) == 2


def test_arquivo_que_nao_e_pdf_nem_imagem_e_recusado(cliente, base):
    cad = cadastrar(cliente, base)
    r = enviar(cliente, cad["token_documentos"], "identidade",
               b"MZ\x90\x00programa", "rg.pdf", "application/pdf")
    assert r.status_code == 422
    assert list(pasta().iterdir()) == []


def test_documento_grande_demais_e_recusado(cliente, base):
    cad = cadastrar(cliente, base)
    grande = PDF + b"0" * (settings.DOCUMENTO_MAX_KB * 1024)
    assert enviar(cliente, cad["token_documentos"], "identidade", grande).status_code == 422


def test_reenviar_o_mesmo_tipo_substitui(cliente, base):
    cad = cadastrar(cliente, base)
    enviar(cliente, cad["token_documentos"], "identidade", PDF)
    r = enviar(cliente, cad["token_documentos"], "identidade", PNG, "rg.png", "image/png")
    assert r.status_code == 200
    assert len(r.json()) == 1
    arquivos_no_disco = list(pasta().iterdir())
    assert len(arquivos_no_disco) == 1
    assert arquivos_no_disco[0].suffix == ".png"


def test_tipo_desconhecido_e_recusado(cliente, base):
    cad = cadastrar(cliente, base)
    assert enviar(cliente, cad["token_documentos"], "passaporte").status_code == 422


# ── A autorização ────────────────────────────────────────────────────
def test_autorizacao_nao_abre_sessao_nem_depois_de_aprovado(cliente, base):
    cad = cadastrar(cliente, base)
    token = cad["token_documentos"]
    assert cliente.get("/api/v1/auth/eu", headers=cab(token)).status_code == 401

    confirmar(cliente, cad)
    cliente.post(
        f"/api/v1/usuarios/{cad['usuario']['id']}/aprovacao",
        json={"aprovado": True}, headers=cab(base["sindico"]),
    )
    assert cliente.get("/api/v1/auth/eu", headers=cab(token)).status_code == 401
    assert cliente.get("/api/v1/portaria/visitantes", headers=cab(token)).status_code == 401


def test_token_de_sessao_nao_envia_documento(cliente, base):
    _, tok_morador = cadastrar_morador(cliente, base["sindico"], base["cond"], cpf=CPFS[3])
    assert enviar(cliente, tok_morador, "identidade").status_code == 401


def test_sem_autorizacao_ou_vencida_e_recusado(cliente, base):
    cad = cadastrar(cliente, base)
    assert cliente.put(
        "/api/v1/auth/cadastro/documentos/identidade",
        files={"arquivo": ("rg.pdf", PDF, "application/pdf")},
    ).status_code == 401

    vencido = jwt.encode(
        {
            "sub": str(cad["usuario"]["id"]), "finalidade": FINALIDADE_DOCUMENTOS,
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.SECRET_KEY, algorithm=settings.ALGORITMO_JWT,
    )
    assert enviar(cliente, vencido, "identidade").status_code == 401


def test_depois_da_avaliacao_nao_troca_mais(cliente, base):
    cad = cadastrar(cliente, base)
    confirmar(cliente, cad)
    cliente.post(
        f"/api/v1/usuarios/{cad['usuario']['id']}/aprovacao",
        json={"aprovado": True}, headers=cab(base["sindico"]),
    )
    assert enviar(cliente, cad["token_documentos"], "identidade").status_code == 409


def test_cadastro_feito_pelo_sindico_nao_traz_autorizacao(cliente, base):
    r = cliente.post(
        "/api/v1/usuarios/porteiros",
        json={
            "nome": "Carlos Pereira", "email": "porteiro@exemplo.com", "cpf": CPFS[2],
            "telefone": "(67) 99999-0003", "senha": "senhaforte123",
            "condominio_id": base["cond"]["id"],
        },
        headers=cab(base["sindico"]),
    )
    assert r.status_code == 201
    assert r.json()["token_documentos"] is None


# ── O síndico confere ────────────────────────────────────────────────
def test_sindico_lista_e_abre_os_documentos(cliente, base):
    cad = cadastrar(cliente, base)
    enviar(cliente, cad["token_documentos"], "identidade", PDF)
    confirmar(cliente, cad)
    uid = cad["usuario"]["id"]

    lista = cliente.get(f"/api/v1/usuarios/{uid}/documentos", headers=cab(base["sindico"]))
    assert lista.status_code == 200
    doc = lista.json()[0]
    assert doc["url"] == f"/usuarios/{uid}/documentos/{doc['id']}/arquivo"

    r = cliente.get(f"/api/v1{doc['url']}", headers=cab(base["sindico"]))
    assert r.status_code == 200
    assert r.content == PDF
    assert r.headers["content-type"] == "application/pdf"
    assert "no-store" in r.headers["cache-control"]
    assert r.headers["content-disposition"] == "inline"


def test_so_o_sindico_do_condominio_abre(cliente, db, base):
    cad = cadastrar(cliente, base)
    enviar(cliente, cad["token_documentos"], "identidade", PDF)
    uid = cad["usuario"]["id"]
    doc = cliente.get(f"/api/v1/usuarios/{uid}/documentos", headers=cab(base["sindico"])).json()[0]

    _, tok_morador = cadastrar_morador(cliente, base["sindico"], base["cond"], cpf=CPFS[3],
                                       email="vizinho@exemplo.com")
    _, tok_porteiro = cadastrar_porteiro(cliente, base["sindico"], base["cond"], cpf=CPFS[2])
    outro = montar_condominio(
        cliente, db, nome="Edifício Aurora", cnpj="04.252.011/0001-10",
        email_sindico="sindico2@exemplo.com", cpf_sindico=CPFS[4],
        email_admin="admin2@exemplo.com", cpf_admin=CPFS[5],
    )

    assert cliente.get(f"/api/v1{doc['url']}", headers=cab(tok_morador)).status_code == 403
    assert cliente.get(f"/api/v1{doc['url']}", headers=cab(tok_porteiro)).status_code == 403
    assert cliente.get(f"/api/v1{doc['url']}", headers=cab(outro["sindico"])).status_code == 404
    assert cliente.get(f"/api/v1{doc['url']}").status_code == 401
    assert cliente.get(
        f"/api/v1/usuarios/{uid}/documentos", headers=cab(outro["sindico"])
    ).status_code == 404


def test_documento_de_outro_usuario_pelo_caminho_errado(cliente, base):
    """O id do documento tem que ser do usuário do caminho."""
    a = cadastrar(cliente, base)
    b = cadastrar(cliente, base, email="outro@exemplo.com", cpf=CPFS[3])
    enviar(cliente, a["token_documentos"], "identidade", PDF)
    doc_a = cliente.get(
        f"/api/v1/usuarios/{a['usuario']['id']}/documentos", headers=cab(base["sindico"])
    ).json()[0]
    r = cliente.get(
        f"/api/v1/usuarios/{b['usuario']['id']}/documentos/{doc_a['id']}/arquivo",
        headers=cab(base["sindico"]),
    )
    assert r.status_code == 404


def test_recusar_o_cadastro_apaga_os_documentos(cliente, base):
    cad = cadastrar(cliente, base)
    enviar(cliente, cad["token_documentos"], "identidade", PDF)
    enviar(cliente, cad["token_documentos"], "comprovante_residencia", PNG, "c.png", "image/png")
    confirmar(cliente, cad)
    assert len(list(pasta().iterdir())) == 2

    uid = cad["usuario"]["id"]
    r = cliente.post(
        f"/api/v1/usuarios/{uid}/aprovacao",
        json={"aprovado": False, "motivo": "Documento ilegível"},
        headers=cab(base["sindico"]),
    )
    assert r.status_code == 200
    assert list(pasta().iterdir()) == []
    assert cliente.get(
        f"/api/v1/usuarios/{uid}/documentos", headers=cab(base["sindico"])
    ).json() == []


def test_aprovar_mantem_os_documentos(cliente, base):
    cad = cadastrar(cliente, base)
    enviar(cliente, cad["token_documentos"], "identidade", PDF)
    confirmar(cliente, cad)
    uid = cad["usuario"]["id"]
    cliente.post(f"/api/v1/usuarios/{uid}/aprovacao", json={"aprovado": True},
                 headers=cab(base["sindico"]))
    assert len(cliente.get(
        f"/api/v1/usuarios/{uid}/documentos", headers=cab(base["sindico"])
    ).json()) == 1


# ── Foto de perfil escolhida no cadastro ─────────────────────────────
def test_foto_do_cadastro_vira_a_foto_de_perfil(cliente, base):
    cad = cadastrar(cliente, base)
    r = cliente.put(
        "/api/v1/auth/cadastro/foto",
        files={"arquivo": ("eu.png", PNG, "image/png")},
        headers=cab(cad["token_documentos"]),
    )
    assert r.status_code == 200, r.text
    confirmar(cliente, cad)
    uid = cad["usuario"]["id"]
    cliente.post(f"/api/v1/usuarios/{uid}/aprovacao", json={"aprovado": True},
                 headers=cab(base["sindico"]))
    login = cliente.post("/api/v1/auth/login",
                         json={"email": "novo@exemplo.com", "senha": "senhaforte123"}).json()
    foto = login["usuario"]["foto_url"]
    assert foto and foto.startswith("/arquivos/fotos/")
    assert cliente.get(f"/api/v1{foto}").content == PNG


def test_foto_do_cadastro_exige_a_autorizacao(cliente, base):
    _, tok_morador = cadastrar_morador(cliente, base["sindico"], base["cond"], cpf=CPFS[3])
    r = cliente.put("/api/v1/auth/cadastro/foto",
                    files={"arquivo": ("eu.png", PNG, "image/png")}, headers=cab(tok_morador))
    assert r.status_code == 401


def test_inativar_o_morador_apaga_os_documentos(cliente, base):
    cad = cadastrar(cliente, base)
    enviar(cliente, cad["token_documentos"], "identidade", PDF)
    confirmar(cliente, cad)
    uid = cad["usuario"]["id"]
    cliente.post(f"/api/v1/usuarios/{uid}/aprovacao", json={"aprovado": True},
                 headers=cab(base["sindico"]))
    assert len(list(pasta().iterdir())) == 1

    r = cliente.delete(f"/api/v1/usuarios/{uid}", headers=cab(base["sindico"]))
    assert r.status_code == 200, r.text
    assert list(pasta().iterdir()) == []


def test_inativar_pela_edicao_tambem_apaga_os_documentos(cliente, base):
    """A situação também muda pelo formulário de edição; o descarte vale
    por qualquer caminho."""
    cad = cadastrar(cliente, base)
    enviar(cliente, cad["token_documentos"], "identidade", PDF)
    confirmar(cliente, cad)
    uid = cad["usuario"]["id"]
    cliente.post(f"/api/v1/usuarios/{uid}/aprovacao", json={"aprovado": True},
                 headers=cab(base["sindico"]))
    r = cliente.put(f"/api/v1/usuarios/{uid}", json={"status": "inativo"},
                    headers=cab(base["sindico"]))
    assert r.status_code == 200, r.text
    assert list(pasta().iterdir()) == []

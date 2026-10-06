"""Tamanho máximo do corpo do pedido.

O FastAPI lê o corpo inteiro antes de conferir o login, e não havia
limite: um corpo de 50 MB mandado ao /auth/login, sem conta nenhuma,
fazia o servidor ocupar centenas de MB de memória, e poucos pedidos
assim ao mesmo tempo derrubavam a API. Arquivo enviado ia para o disco
do mesmo jeito, sem teto.
"""
from __future__ import annotations

from app.core.config import settings
from tests.fixtures import cab
from tests.test_portaria import cenario  # noqa: F401

ORIGEM = "http://localhost:5500"


def _json_de(tamanho: int) -> bytes:
    # Espaços entre os campos: JSON válido, de qualquer tamanho.
    return b'{"email":"ninguem@exemplo.com",' + b" " * tamanho + b'"senha":"senhaforte123"}'


def test_corpo_grande_demais_e_recusado_antes_do_login(cliente, db):
    r = cliente.post(
        "/api/v1/auth/login", content=_json_de(settings.CORPO_MAX_KB * 1024),
        headers={"Content-Type": "application/json", "Origin": ORIGEM},
    )
    assert r.status_code == 413
    assert "grande demais" in r.json()["detalhe"]
    # A tela recebe a mensagem: a resposta passa pelo CORS.
    assert r.headers.get("access-control-allow-origin") == ORIGEM


def test_corpo_sem_tamanho_declarado_tambem_tem_limite(cliente, db):
    """Sem Content-Length (envio em partes), o limite é contado na chegada."""
    def partes():
        for _ in range(settings.CORPO_MAX_KB // 64 + 2):
            yield b" " * (64 * 1024)
    r = cliente.post("/api/v1/auth/login", content=partes(),
                     headers={"Content-Type": "application/json"})
    assert r.status_code == 413


def test_corpo_normal_continua_passando(cliente, db):
    r = cliente.post("/api/v1/auth/login", content=_json_de(1000),
                     headers={"Content-Type": "application/json"})
    assert r.status_code == 401


def test_arquivo_acima_do_maior_limite_e_recusado(cliente, cenario):
    grande = b"%PDF-" + b"0" * (settings.DOCUMENTO_MAX_KB * 1024 + 200 * 1024)
    r = cliente.post(
        "/api/v1/documentos",
        data={"titulo": "Ata da assembleia", "categoria": "ata"},
        files={"arquivo": ("ata.pdf", grande, "application/pdf")},
        headers=cab(cenario["sindico"]),
    )
    assert r.status_code == 413


def test_foto_um_pouco_acima_do_limite_recebe_a_mensagem_da_rota(cliente, cenario):
    """O teto do corpo fica acima do maior arquivo aceito: quem passa um
    pouco do limite da foto continua vendo a mensagem que diz o limite."""
    foto = b"\xff\xd8\xff" + b"0" * (settings.FOTO_MAX_KB * 1024 + 10)
    r = cliente.put(
        "/api/v1/usuarios/eu/foto",
        files={"arquivo": ("foto.jpg", foto, "image/jpeg")},
        headers=cab(cenario["ana"]),
    )
    assert r.status_code in (400, 422)
    assert "MB" in r.json()["detalhe"]

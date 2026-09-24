"""Configuração dos testes de interface.

Precisam do sistema no ar, com os dados de demonstração:

    cd backend  && python -m alembic upgrade head && python -m app.seed --limpar
    cd backend  && python -m uvicorn app.main:app          (porta 8000)
    cd frontend && python servidor.py                      (porta 5500)
    cd frontend && python -m pytest testes

Endereço do front-end em SMARTCONDO_FRONT (padrão http://127.0.0.1:5500).
Para usar um Chromium já instalado, aponte CHROMIUM_PATH para ele.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

FRONT = os.environ.get("SMARTCONDO_FRONT", "http://127.0.0.1:5500").rstrip("/")
RAIZ = Path(__file__).resolve().parents[1]
SENHA = "smartcondo123"
PAPEIS = ("admin", "sindico", "porteiro", "morador")

# Telas abertas sem login.
PUBLICAS = ["index.html", "404.html", "diagnostico.html"] + sorted(
    str(p.relative_to(RAIZ)).replace(os.sep, "/")
    for pasta in ("cadastro", "login", "legal")
    for p in (RAIZ / "pages" / pasta).glob("*.html")
) + sorted(
    str(p.relative_to(RAIZ)).replace(os.sep, "/")
    for p in (RAIZ / "pages").glob("*/aguardando_aprovacao.html")
) + ["pages/sindico/cadastro_privado.html"]


def paginas_do_papel(papel: str) -> list[str]:
    """As telas internas de um papel (as de espera ficam nas públicas)."""
    return sorted(
        f"pages/{papel}/{p.name}"
        for p in (RAIZ / "pages" / papel).glob("*.html")
        if p.name not in ("aguardando_aprovacao.html", "cadastro_privado.html")
    )


@pytest.fixture(scope="session")
def navegador():
    with sync_playwright() as p:
        # A câmera falsa do Chromium permite testar a captura do vídeo
        # porteiro sem câmera de verdade e sem o pedido de permissão.
        opcoes = {"args": ["--no-sandbox", "--use-fake-device-for-media-stream",
                           "--use-fake-ui-for-media-stream"]}
        if os.environ.get("CHROMIUM_PATH"):
            opcoes["executable_path"] = os.environ["CHROMIUM_PATH"]
        b = p.chromium.launch(**opcoes)
        yield b
        b.close()


def abrir(navegador, largura=1280, tema="light", papel=None):
    """Nova aba no tamanho e tema pedidos; com papel, já logada."""
    # O navegador fica no fuso do condomínio, como o de quem mora lá: a
    # API decide "hoje" por ele (FUSO_HORARIO), e a máquina do CI está em UTC.
    ctx = navegador.new_context(viewport={"width": largura, "height": 850}, color_scheme=tema,
                                timezone_id="America/Campo_Grande")
    pg = ctx.new_page()
    pg.erros = []
    pg.on("pageerror", lambda e: pg.erros.append(str(e)))
    if papel:
        pg.goto(f"{FRONT}/index.html")
        pg.fill("#emailInput", f"{papel}@smartcondo.com")
        pg.fill("#senhaInput", SENHA)
        pg.click("#btnEntrar")
        pg.wait_for_url(f"**/{papel}/dashboard.html", timeout=15000)
    return ctx, pg


def ir(pg, pagina, espera=700):
    pg.goto(f"{FRONT}/{pagina}")
    pg.wait_for_timeout(espera)
    pg.mouse.move(1, 1)   # mouse fora dos elementos: nada em estado de hover

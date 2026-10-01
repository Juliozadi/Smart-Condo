"""Limite de pedidos por origem (IP) nas rotas abertas.

As rotas que não pedem login — consulta do código de acesso, cadastro,
login, confirmação e recuperação de senha — já tinham limites por pessoa
(tentativas de senha, palpites e envios de código). Faltava o limite por
origem: o código de acesso tem cerca de um milhão de combinações e podia
ser adivinhado em poucas horas por um script, e cada cadastro novo
começava seus próprios limites, disparando e-mails e SMS pagos.

A contagem fica na memória do processo, numa janela deslizante de um
minuto. Com mais de um processo da API, cada um conta o seu; para a fase
de publicação, o mesmo limite pode ir para o proxy (nginx) ou para um
Redis.
"""
from __future__ import annotations

import threading
import time
from collections import deque

from fastapi import HTTPException, Request, status

from app.core.config import settings

JANELA_S = 60.0

_pedidos: dict[tuple[str, str], deque[float]] = {}
_trava = threading.Lock()


def _origem(request: Request) -> str:
    # O X-Forwarded-For não é lido de propósito: qualquer um o escreve.
    # Atrás de um proxy, quem limita é o proxy.
    return request.client.host if request.client else "desconhecida"


def limitar(grupo: str, por_minuto: int):
    """Dependência do FastAPI: até `por_minuto` pedidos por origem no grupo."""

    def conferir(request: Request) -> None:
        if not settings.LIMITE_POR_ORIGEM:
            return
        agora = time.monotonic()
        chave = (grupo, _origem(request))
        with _trava:
            fila = _pedidos.setdefault(chave, deque())
            while fila and fila[0] <= agora - JANELA_S:
                fila.popleft()
            if len(fila) >= por_minuto:
                espera = int(fila[0] + JANELA_S - agora) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Muitas tentativas em pouco tempo. Aguarde um minuto e tente de novo.",
                    headers={"Retry-After": str(espera)},
                )
            fila.append(agora)
            # Sem isto, cada IP que já passou por aqui ficaria na memória.
            if len(_pedidos) > 10_000:
                for k in [k for k, f in _pedidos.items() if not f or f[-1] <= agora - JANELA_S]:
                    del _pedidos[k]

    return conferir


def zerar() -> None:
    """Para os testes: cada um começa sem pedidos contados."""
    with _trava:
        _pedidos.clear()

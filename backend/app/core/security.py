"""Hash de senha, tokens JWT e códigos de verificação."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# O bcrypt trunca em 72 bytes. A validação dos schemas já barra senhas
# maiores, mas a checagem fica aqui também para não depender disso.
BCRYPT_MAX_BYTES = 72


def gerar_hash_senha(senha: str) -> str:
    dados = senha.encode("utf-8")
    if len(dados) > BCRYPT_MAX_BYTES:
        raise ValueError(f"A senha não pode passar de {BCRYPT_MAX_BYTES} bytes.")
    return bcrypt.hashpw(dados, bcrypt.gensalt(settings.BCRYPT_ROUNDS)).decode("utf-8")


def conferir_senha(senha: str, hash_armazenado: str) -> bool:
    dados = senha.encode("utf-8")
    if len(dados) > BCRYPT_MAX_BYTES:
        return False
    try:
        return bcrypt.checkpw(dados, hash_armazenado.encode("utf-8"))
    except ValueError:
        # Hash malformado no banco: trata como senha inválida.
        return False


def criar_token_acesso(subject: str, papel: str, expira_min: int | None = None) -> str:
    minutos = expira_min or settings.ACCESS_TOKEN_EXPIRA_MIN
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "papel": papel,
        "iat": agora,
        "exp": agora + timedelta(minutes=minutos),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITMO_JWT)


def ler_token_acesso(token: str) -> dict | None:
    """Devolve o payload do token, ou None se for inválido ou expirado."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITMO_JWT])
    except JWTError:
        return None


# ── Códigos de verificação ───────────────────────────────────────────
# Documentação, seção 9: no cadastro "o sistema salva e envia um código de
# confirmação pelo meio escolhido"; em "Esqueci minha senha", "o sistema
# envia um código pelo meio escolhido pelo usuário".

def gerar_codigo_verificacao(digitos: int = 6) -> str:
    """Código numérico aleatório, gerado por fonte criptográfica."""
    maximo = 10 ** digitos
    return str(secrets.randbelow(maximo)).zfill(digitos)


def gerar_hash_codigo(codigo: str) -> str:
    """O código é guardado em hash — nunca em texto puro."""
    return hashlib.sha256(f"{settings.SECRET_KEY}{codigo}".encode("utf-8")).hexdigest()


def conferir_codigo(codigo: str, hash_armazenado: str) -> bool:
    return hmac.compare_digest(gerar_hash_codigo(codigo), hash_armazenado)


def gerar_codigo_condominio(nome: str) -> str:
    """Código de acesso do condomínio, no formato COND-XXXX-YYYY.

    Documentação, seção 11.3: o morador informa o condomínio ao se
    cadastrar. Com o código, ele entra sem que o sistema precise expor
    uma lista pública de todos os condomínios.

    Sem I, O, 0 e 1, que se confundem quando alguém lê em voz alta ou
    copia de um papel.
    """
    alfabeto = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    letras = "".join(c for c in nome.upper() if c.isalpha())[:4] or "COND"
    sufixo = "".join(secrets.choice(alfabeto) for _ in range(4))
    return f"{letras.ljust(4, 'X')}-{sufixo}"

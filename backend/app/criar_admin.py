"""Cria um administrador da plataforma.

    python -m app.criar_admin

O administrador é quem cadastra os condomínios e os síndicos, então o
primeiro deles não pode ser criado pela própria API — nasce por aqui.
Pede os dados no terminal; a senha não aparece enquanto é digitada.
"""
from __future__ import annotations

import getpass
import sys

from pydantic import ValidationError
from sqlalchemy import select

from app.core.database import SessionLocal, engine
from app.core.security import gerar_hash_senha
from app.models.enums import Papel, StatusUsuario
from app.models.usuario import Usuario
from app.schemas.admin import UsuarioAdminEntrada


def perguntar(rotulo: str) -> str:
    valor = input(f"{rotulo}: ").strip()
    if not valor:
        print("Campo obrigatório.", file=sys.stderr)
        return perguntar(rotulo)
    return valor


def main() -> int:
    print("Criação de administrador do SmartCondo\n")

    nome = perguntar("Nome completo")
    email = perguntar("E-mail")
    cpf = perguntar("CPF")
    telefone = perguntar("Telefone (com DDD)")

    senha = getpass.getpass("Senha: ")
    if senha != getpass.getpass("Repita a senha: "):
        print("As senhas não conferem.", file=sys.stderr)
        return 1

    # Valida com o mesmo schema da API, para as regras não divergirem.
    try:
        dados = UsuarioAdminEntrada(
            nome=nome, email=email, cpf=cpf, telefone=telefone,
            senha=senha, papel=Papel.ADMIN,
        )
    except ValidationError as erro:
        print("\nDados inválidos:", file=sys.stderr)
        for problema in erro.errors():
            campo = problema["loc"][-1] if problema["loc"] else "?"
            msg = problema["msg"].replace("Value error, ", "")
            print(f"  {campo}: {msg}", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        if db.scalar(select(Usuario).where(Usuario.email == dados.email.lower())):
            print("\nJá existe um usuário com este e-mail.", file=sys.stderr)
            return 1
        if db.scalar(select(Usuario).where(Usuario.cpf == dados.cpf)):
            print("\nJá existe um usuário com este CPF.", file=sys.stderr)
            return 1

        db.add(Usuario(
            nome=dados.nome,
            email=dados.email.lower(),
            cpf=dados.cpf,
            telefone=dados.telefone,
            senha_hash=gerar_hash_senha(dados.senha),
            papel=Papel.ADMIN,
            status=StatusUsuario.ATIVO,
        ))
        db.commit()

    print(f"\nAdministrador criado: {dados.email}")
    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

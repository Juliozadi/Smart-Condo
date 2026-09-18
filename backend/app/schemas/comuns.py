"""Tipos e validadores compartilhados pelos schemas."""
from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

# O bcrypt trabalha com no máximo 72 bytes; a senha é barrada aqui antes
# de chegar ao hash.
Senha = Annotated[str, Field(min_length=8, max_length=72)]


def _so_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def validar_cpf(valor: str) -> str:
    """Valida o CPF pelos dois dígitos verificadores e devolve só os dígitos."""
    cpf = _so_digitos(valor)
    if len(cpf) != 11:
        raise ValueError("O CPF precisa ter 11 dígitos.")
    if cpf == cpf[0] * 11:
        raise ValueError("CPF inválido.")

    for tamanho in (9, 10):
        soma = sum(int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != int(cpf[tamanho]):
            raise ValueError("CPF inválido.")
    return cpf


def validar_cnpj(valor: str) -> str:
    """Valida o CNPJ pelos dois dígitos verificadores e devolve só os dígitos."""
    cnpj = _so_digitos(valor)
    if len(cnpj) != 14:
        raise ValueError("O CNPJ precisa ter 14 dígitos.")
    if cnpj == cnpj[0] * 14:
        raise ValueError("CNPJ inválido.")

    for tamanho in (12, 13):
        pesos = list(range(tamanho - 7, 1, -1)) + list(range(9, 1, -1))
        soma = sum(int(cnpj[i]) * pesos[i] for i in range(tamanho))
        resto = soma % 11
        digito = 0 if resto < 2 else 11 - resto
        if digito != int(cnpj[tamanho]):
            raise ValueError("CNPJ inválido.")
    return cnpj


def validar_telefone(valor: str) -> str:
    tel = _so_digitos(valor)
    if len(tel) not in (10, 11):
        raise ValueError("O telefone precisa ter DDD e 8 ou 9 dígitos.")
    return tel


def validar_uf(valor: str) -> str:
    ufs = {
        "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
        "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
        "SP", "SE", "TO",
    }
    uf = (valor or "").strip().upper()
    if uf not in ufs:
        raise ValueError("UF inválida.")
    return uf


def validar_cep(valor: str) -> str:
    cep = _so_digitos(valor)
    if len(cep) != 8:
        raise ValueError("O CEP precisa ter 8 dígitos.")
    return cep


CPF = Annotated[str, AfterValidator(validar_cpf)]
CNPJ = Annotated[str, AfterValidator(validar_cnpj)]
Telefone = Annotated[str, AfterValidator(validar_telefone)]
UF = Annotated[str, AfterValidator(validar_uf)]
CEP = Annotated[str, AfterValidator(validar_cep)]


class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Mensagem(SchemaBase):
    detalhe: str

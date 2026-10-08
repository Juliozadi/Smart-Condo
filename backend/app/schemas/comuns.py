"""Tipos e validadores compartilhados pelos schemas."""
from __future__ import annotations

import re
import unicodedata
from datetime import date

from app.core.tempo import hoje_local
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

def validar_forca_senha(valor: str) -> str:
    """Regras mostradas ao usuário na tela de nova senha.

    Mantidas iguais dos dois lados: a tela não pode prometer uma exigência
    que o servidor não cobra.
    """
    if not any(c.isalpha() for c in valor):
        raise ValueError("A senha precisa ter ao menos uma letra.")
    if not any(c.isdigit() or not c.isalnum() for c in valor):
        raise ValueError("A senha precisa ter ao menos um número ou símbolo.")
    return valor


# A senha é a exceção ao aparo de espaços do SchemaBase: um espaço no
# começo ou no fim é parte da senha, e apará-lo a mudaria em silêncio.
SenhaDigitada = Annotated[str, StringConstraints(strip_whitespace=False)]

# O bcrypt trabalha com no máximo 72 bytes; a senha é barrada aqui antes
# de chegar ao hash.
Senha = Annotated[
    SenhaDigitada, Field(min_length=8, max_length=72), AfterValidator(validar_forca_senha)
]


def _so_digitos(valor: str) -> str:
    # [^0-9] e não \D: o \d do Python também casa com "٠١٢" e "０１２".
    # O mesmo CPF escrito com eles passava pelos dígitos verificadores, era
    # gravado como outro texto e a regra de um cadastro por CPF não valia.
    return re.sub(r"[^0-9]", "", valor or "")


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


def validar_data_nascimento(valor: date) -> date:
    """Nem no futuro, nem de alguém com mais de 120 anos: os dois são
    erro de digitação (ano trocado, dia e mês invertidos)."""
    hoje = hoje_local()
    if valor > hoje:
        raise ValueError("A data de nascimento não pode estar no futuro.")
    if valor.year < hoje.year - 120:
        raise ValueError("Confira o ano da data de nascimento.")
    return valor


def validar_endereco_web(valor: str) -> str:
    """Só http e https. Um endereço guardado vira link na tela de outra
    pessoa; "javascript:" ou "data:" executariam código no clique."""
    endereco = (valor or "").strip()
    if not re.match(r"^https?://[^\s/$.?#].[^\s]*$", endereco, re.IGNORECASE):
        raise ValueError("Informe um endereço que comece com http:// ou https://.")
    return endereco


def limpar_placa(valor: str) -> str:
    """Tira hífen, ponto e espaço e passa para maiúsculas: ABC-1D23,
    abc1d23 e ABC 1D23 são a mesma placa."""
    return re.sub(r"[\s.\-]", "", valor).upper()


def validar_placa(valor: str) -> str:
    """Placa brasileira, antiga ou Mercosul: 7 letras A-Z e dígitos 0-9.

    Só ASCII: "Á", "²" ou "Ａ" passavam pelo isalnum() de antes e viravam
    outra placa — o mesmo carro entrava duas vezes no pátio."""
    limpa = limpar_placa(valor)
    if not re.fullmatch(r"[A-Z0-9]{7}", limpa):
        raise ValueError("A placa precisa ter 7 letras ou números (ex.: ABC1D23).")
    return limpa


def normalizar_unidade(valor: str) -> str:
    """Número ou bloco da unidade, como o síndico vê na tela.

    "２０４" (largura total) aparece igual a "204", mas era gravado como
    outra unidade: o síndico aprovaria alguém num apartamento que não é o
    204. O NFKC os torna iguais; dígitos de outro alfabeto ("٢٠٤"), que
    nenhuma normalização converte, são recusados."""
    valor = unicodedata.normalize("NFKC", valor).strip()
    if any(c.isdigit() and c not in "0123456789" for c in valor):
        raise ValueError("Use os algarismos de 0 a 9.")
    return valor


CPF = Annotated[str, AfterValidator(validar_cpf)]
CNPJ = Annotated[str, AfterValidator(validar_cnpj)]
Telefone = Annotated[str, AfterValidator(validar_telefone)]
UF = Annotated[str, AfterValidator(validar_uf)]
CEP = Annotated[str, AfterValidator(validar_cep)]
DataNascimento = Annotated[date, AfterValidator(validar_data_nascimento)]
EnderecoWeb = Annotated[str, Field(max_length=500), AfterValidator(validar_endereco_web)]
Placa = Annotated[str, Field(max_length=10), AfterValidator(validar_placa)]
IdUnidade = Annotated[str, AfterValidator(normalizar_unidade)]


class SchemaBase(BaseModel):
    # Espaços no começo e no fim saem antes da validação: sem isso, um
    # título "   " passava pelo mínimo de 3 caracteres e virava um
    # comunicado em branco, enviado a todos os moradores.
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class Mensagem(SchemaBase):
    detalhe: str

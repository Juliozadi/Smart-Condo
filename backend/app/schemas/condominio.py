"""Schemas do condomínio, unidades e espaços comuns.

Documentação, seção 12 — caso de uso "Cadastro do condomínio" (síndico).
"""
from __future__ import annotations

from datetime import datetime

from pydantic import Field, model_validator

from app.schemas.admin import RegistroSaida
from app.schemas.comuns import CEP, CNPJ, SchemaBase, Telefone, UF


class CondominioEntrada(SchemaBase):
    nome: str = Field(min_length=3, max_length=160)
    cnpj: CNPJ
    cep: CEP
    logradouro: str = Field(min_length=3, max_length=180)
    numero: str = Field(min_length=1, max_length=20)
    bairro: str = Field(min_length=2, max_length=100)
    cidade: str = Field(min_length=2, max_length=100)
    uf: UF
    telefone: Telefone | None = None


class CondominioSaida(SchemaBase):
    id: int
    nome: str
    cnpj: str
    # Só volta para o síndico; é o que ele repassa a quem vai morar ali.
    codigo_acesso: str
    cep: str
    logradouro: str
    numero: str
    bairro: str
    cidade: str
    uf: str
    telefone: str | None = None
    sindico_id: int | None = None
    criado_em: datetime


class CondominioPorCodigo(SchemaBase):
    """O que a tela de cadastro mostra ao conferir o código digitado:
    só o suficiente para o morador confirmar que é o condomínio certo."""
    id: int
    nome: str
    cidade: str
    uf: str


class UnidadeEntrada(SchemaBase):
    numero: str = Field(min_length=1, max_length=20)
    bloco: str = Field(default="unico", max_length=20)
    andar: int | None = Field(default=None, ge=0, le=200)
    vagas_garagem: int = Field(default=0, ge=0, le=20)


class UnidadeSaida(UnidadeEntrada):
    id: int
    condominio_id: int


class EspacoEntrada(SchemaBase):
    nome: str = Field(min_length=2, max_length=120)
    descricao: str | None = Field(default=None, max_length=2000)
    capacidade: int = Field(default=0, ge=0, le=10000)
    reservavel: bool = True
    uso_livre: bool = False
    em_manutencao: bool = False

    @model_validator(mode="after")
    def _tem_uso(self):
        # Nem reservável nem de uso livre: o espaço não serviria para nada.
        if not self.reservavel and not self.uso_livre:
            raise ValueError("O espaço precisa ser reservável ou de uso livre.")
        return self


class EspacoAtualizacao(SchemaBase):
    """Só o que veio muda. Campos obrigatórios não aceitam null."""
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    descricao: str | None = Field(default=None, max_length=2000)
    capacidade: int | None = Field(default=None, ge=0, le=10000)
    reservavel: bool | None = None
    uso_livre: bool | None = None
    em_manutencao: bool | None = None

    @model_validator(mode="after")
    def _sem_null_nos_obrigatorios(self):
        for campo in ("nome", "capacidade", "reservavel", "uso_livre", "em_manutencao"):
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"O campo {campo} não pode ficar vazio.")
        return self


class EspacoSaida(SchemaBase):
    id: int
    condominio_id: int
    nome: str
    descricao: str | None = None
    capacidade: int
    reservavel: bool
    uso_livre: bool
    em_manutencao: bool
    inativo: bool = False
    # Só para o síndico: "Editado por Fulano em 28/09 14:32".
    ultima_alteracao: RegistroSaida | None = None


class OcupacaoEntrada(SchemaBase):
    """Leitura da contagem de pessoas numa área de uso livre."""
    pessoas: int = Field(ge=0, le=10000)


class OcupacaoSaida(SchemaBase):
    """Documentação, seção 6: "Piscina: 23 pessoas no momento"."""
    espaco_id: int
    espaco_nome: str
    pessoas: int
    capacidade: int
    percentual: int
    atualizado_em: datetime | None = None

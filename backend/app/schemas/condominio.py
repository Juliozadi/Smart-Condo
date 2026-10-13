"""Schemas do condomínio, unidades e espaços comuns.

Documentação, seção 12 — caso de uso "Cadastro do condomínio" (síndico).
"""
from __future__ import annotations

from datetime import datetime, time

from pydantic import Field, field_validator, model_validator

from app.schemas.admin import RegistroSaida
from app.schemas.comuns import CEP, CNPJ, IdUnidade, SchemaBase, Telefone, UF


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
    numero: IdUnidade = Field(min_length=1, max_length=20)
    bloco: IdUnidade = Field(default="unico", max_length=20)
    andar: int | None = Field(default=None, ge=0, le=200)
    vagas_garagem: int = Field(default=0, ge=0, le=20)


class UnidadeSaida(UnidadeEntrada):
    id: int
    condominio_id: int
    # Só para o síndico: quantos moradores ativos e quem mexeu por último.
    total_moradores: int | None = None
    ultima_alteracao: RegistroSaida | None = None


class UnidadeAtualizacao(SchemaBase):
    """Andar e vagas. Número e bloco não mudam: moradores, cobranças e a
    portaria apontam para a unidade por eles."""
    andar: int | None = Field(default=None, ge=0, le=200)
    vagas_garagem: int | None = Field(default=None, ge=0, le=20)

    @model_validator(mode="after")
    def _vagas_nao_nulas(self):
        if "vagas_garagem" in self.model_fields_set and self.vagas_garagem is None:
            raise ValueError("Informe o número de vagas (0 se não houver).")
        return self


class RegrasDoEspaco(SchemaBase):
    """Regras de uso do espaço, definidas pelo síndico. Vazio = sem a regra.

    O salão que funciona até as 22h (lei do silêncio), a reserva com dois
    dias de antecedência, a churrasqueira por no máximo seis horas, uma
    reserva futura por apartamento."""
    horario_abertura: time | None = None
    horario_fechamento: time | None = None
    antecedencia_minima_dias: int | None = Field(default=None, ge=0, le=180)
    duracao_maxima_horas: int | None = Field(default=None, ge=1, le=24)
    limite_por_unidade: int | None = Field(default=None, ge=1, le=50)

    @field_validator("horario_abertura", "horario_fechamento")
    @classmethod
    def _sem_fuso(cls, valor: time | None) -> time | None:
        if valor is not None and valor.tzinfo is not None:
            raise ValueError("Informe o horário sem fuso, no horário do condomínio.")
        return valor

    @model_validator(mode="after")
    def _horario_coerente(self):
        abre, fecha = self.horario_abertura, self.horario_fechamento
        if abre is not None and fecha is not None and fecha <= abre:
            raise ValueError("O horário de fechamento precisa ser depois do de abertura.")
        return self


def conferir_par_de_horarios(abre: time | None, fecha: time | None) -> str | None:
    """Abertura e fechamento andam juntos: só um deles não diz nada."""
    if (abre is None) != (fecha is None):
        return "Informe o horário de abertura e o de fechamento, ou nenhum dos dois."
    return None


class EspacoEntrada(RegrasDoEspaco):
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
        erro = conferir_par_de_horarios(self.horario_abertura, self.horario_fechamento)
        if erro:
            raise ValueError(erro)
        return self


class EspacoAtualizacao(RegrasDoEspaco):
    """Só o que veio muda. Campos obrigatórios não aceitam null; as regras
    aceitam (null tira a regra)."""
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
    horario_abertura: time | None = None
    horario_fechamento: time | None = None
    antecedencia_minima_dias: int | None = None
    duracao_maxima_horas: int | None = None
    limite_por_unidade: int | None = None
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

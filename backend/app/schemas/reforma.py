"""Schemas das obras e reformas nos apartamentos."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from pydantic import Field, field_validator, model_validator

from app.core.tempo import hoje_local
from app.models.enums import StatusReforma
from app.schemas.comuns import SchemaBase, vazio_e_nada

# Prazo de uma reforma e até quando se comunica com antecedência: mais
# que um ano é engano na data (a obra longa é prorrogada pelo síndico).
PRAZO_MAXIMO_DIAS = 365


def _conferir_prazo(inicio: date, fim: date) -> None:
    if fim < inicio:
        raise ValueError("O fim previsto precisa ser no dia do início ou depois.")
    if (fim - inicio).days > PRAZO_MAXIMO_DIAS:
        raise ValueError("A reforma pode durar até um ano; depois, o síndico prorroga.")


class ReformaEntrada(SchemaBase):
    descricao: str = Field(min_length=10, max_length=500)
    empresa: str | None = Field(default=None, max_length=120)
    # Estrutura, vedações (paredes) ou instalações do prédio (gás, elétrica,
    # hidráulica): a NBR 16280 exige o responsável técnico.
    altera_estrutura: bool = False
    responsavel_tecnico: str | None = Field(default=None, min_length=3, max_length=160)
    art_rrt: str | None = Field(default=None, min_length=3, max_length=40)
    inicio: date
    fim: date

    _vazios = field_validator("empresa", "responsavel_tecnico", "art_rrt",
                              mode="before")(vazio_e_nada)

    @field_validator("inicio")
    @classmethod
    def nao_muito_longe(cls, valor: date) -> date:
        if valor > hoje_local() + timedelta(days=PRAZO_MAXIMO_DIAS):
            raise ValueError("A reforma pode ser comunicada com até um ano de antecedência.")
        return valor

    @model_validator(mode="after")
    def conferir(self) -> "ReformaEntrada":
        _conferir_prazo(self.inicio, self.fim)
        if self.altera_estrutura and not (self.responsavel_tecnico and self.art_rrt):
            raise ValueError(
                "Reforma que mexe em estrutura, paredes ou instalações precisa do responsável "
                "técnico e do número da ART ou do RRT (NBR 16280).")
        if not self.altera_estrutura and self.art_rrt and not self.responsavel_tecnico:
            raise ValueError("Informe o responsável técnico da ART ou do RRT.")
        return self


class AvaliacaoReforma(SchemaBase):
    aprovada: bool
    # Na aprovação, as condições (opcionais); na recusa, o motivo.
    condicoes: str | None = Field(default=None, max_length=300)
    motivo: str | None = Field(default=None, max_length=300)

    _vazios = field_validator("condicoes", "motivo", mode="before")(vazio_e_nada)

    @model_validator(mode="after")
    def recusa_tem_motivo(self) -> "AvaliacaoReforma":
        # O morador precisa saber o que corrigir para pedir de novo.
        if not self.aprovada and not (self.motivo and len(self.motivo) >= 3):
            raise ValueError("Informe o motivo da recusa.")
        return self


class ProrrogacaoReforma(SchemaBase):
    fim: date
    motivo: str | None = Field(default=None, max_length=300)

    _vazios = field_validator("motivo", mode="before")(vazio_e_nada)


class CancelamentoReforma(SchemaBase):
    motivo: str | None = Field(default=None, max_length=300)

    _vazios = field_validator("motivo", mode="before")(vazio_e_nada)


class ReformaSaida(SchemaBase):
    id: int
    unidade_id: int
    unidade: str
    descricao: str
    empresa: str | None = None
    altera_estrutura: bool
    responsavel_tecnico: str | None = None
    art_rrt: str | None = None
    inicio: date
    fim: date
    status: StatusReforma
    # aguardando, agendada, em_andamento, prazo_encerrado, recusada,
    # cancelada ou concluida — o que a tela mostra.
    situacao: str
    solicitada_por_nome: str | None = None
    condicoes: str | None = None
    motivo_recusa: str | None = None
    cancelada_pelo_sindico: bool = False
    motivo_cancelamento: str | None = None
    concluida_em: datetime | None = None
    criado_em: datetime
    # O que quem está vendo pode fazer com ela.
    pode_avaliar: bool = False
    pode_cancelar: bool = False
    pode_concluir: bool = False
    pode_prorrogar: bool = False

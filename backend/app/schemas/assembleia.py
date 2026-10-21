"""Schemas da assembleia virtual."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from pydantic import Field, field_validator, model_validator

from app.core.tempo import agora_local
from app.models.enums import EscolhaVoto, MaioriaExigida
from app.schemas.comuns import SchemaBase

# A votação dura no máximo 30 dias, e a convocação é de até um ano antes.
DURACAO_MAXIMA = timedelta(days=30)
ANTECEDENCIA_MAXIMA = timedelta(days=365)
# Folga para o relógio de quem preenche a tela: "começa agora" não é passado.
TOLERANCIA = timedelta(minutes=5)


def _com_fuso(momento: datetime) -> datetime:
    """Hora sem fuso (a do campo datetime-local da tela) é a do condomínio."""
    if momento.tzinfo is None:
        return momento.replace(tzinfo=agora_local().tzinfo)
    return momento


class ItemPautaEntrada(SchemaBase):
    titulo: str = Field(min_length=3, max_length=180)
    descricao: str | None = Field(default=None, max_length=2000)
    maioria: MaioriaExigida = MaioriaExigida.SIMPLES


class AssembleiaEntrada(SchemaBase):
    titulo: str = Field(min_length=3, max_length=180)
    descricao: str | None = Field(default=None, max_length=4000)
    abre_em: datetime
    encerra_em: datetime
    itens: list[ItemPautaEntrada] = Field(min_length=1, max_length=20)

    @field_validator("abre_em", "encerra_em")
    @classmethod
    def _fuso(cls, momento: datetime) -> datetime:
        return _com_fuso(momento)

    @model_validator(mode="after")
    def _periodo(self) -> "AssembleiaEntrada":
        agora = datetime.now(timezone.utc)
        if self.abre_em < agora - TOLERANCIA:
            raise ValueError("A votação não pode começar no passado.")
        if self.abre_em > agora + ANTECEDENCIA_MAXIMA:
            raise ValueError("A votação pode começar em até um ano.")
        if self.encerra_em <= self.abre_em:
            raise ValueError("O fim da votação precisa ser depois do início.")
        if self.encerra_em - self.abre_em > DURACAO_MAXIMA:
            raise ValueError("A votação fica aberta por no máximo 30 dias.")
        return self


class VotoEntrada(SchemaBase):
    item_id: int
    escolha: EscolhaVoto


class CedulaEntrada(SchemaBase):
    """O voto do apartamento em todos os itens da pauta, de uma vez."""
    votos: list[VotoEntrada] = Field(min_length=1, max_length=20)


class CancelamentoAssembleia(SchemaBase):
    motivo: str = Field(min_length=3, max_length=300)


class ResultadoItem(SchemaBase):
    a_favor: int
    contra: int
    abstencao: int
    aprovado: bool


class ItemPautaSaida(SchemaBase):
    id: int
    ordem: int
    titulo: str
    descricao: str | None = None
    maioria: MaioriaExigida
    # Só depois de encerrada: durante a votação ninguém vê o placar.
    resultado: ResultadoItem | None = None
    # O voto do próprio apartamento, para o morador conferir.
    meu_voto: EscolhaVoto | None = None


class AssembleiaSaida(SchemaBase):
    id: int
    titulo: str
    descricao: str | None = None
    abre_em: datetime
    encerra_em: datetime
    # agendada, aberta, encerrada ou cancelada
    situacao: str
    convocada_por_nome: str | None = None
    motivo_cancelamento: str | None = None
    itens: list[ItemPautaSaida]
    total_unidades: int
    unidades_que_votaram: int
    # Para o morador.
    meu_apartamento_votou: bool | None = None
    posso_votar: bool | None = None
    motivo_sem_voto: str | None = None
    criado_em: datetime

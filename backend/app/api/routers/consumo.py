"""Medição individual de água e gás.

O síndico, ou o porteiro a quem ele liberou as leituras, lança as
leituras do mês de todos os apartamentos numa tela só; o consumo sai da
diferença para a leitura anterior (ou da própria leitura, se o medidor
foi trocado). O consumo acima do dobro da média dos meses anteriores
avisa o apartamento — costuma ser vazamento. O síndico informa a tarifa
da concessionária e a cobrança de cada apartamento sai pelo consumo. O
morador vê o histórico do apartamento.
"""
from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import exigir_papel, exigir_permissao_do_porteiro
from app.api.routers.financeiro import _dia_de_vencimento
from app.core.database import get_db
from app.core.formato import reais
from app.core.tempo import hoje_local, somar_meses
from app.models.condominio import Unidade
from app.models.consumo import LeituraConsumo
from app.models.enums import OrigemCobranca, Papel, StatusCobranca, TipoConsumo
from app.models.financeiro import Cobranca
from app.models.usuario import Usuario
from app.schemas.consumo import (
    CobrancaConsumoEntrada, HistoricoConsumo, LeiturasEntrada, LinhaLeitura,
)
from app.schemas.financeiro import LoteSaida
from app.services import destinatarios, registro

router = APIRouter(prefix="/consumo", tags=["Medição de consumo"])

equipe = exigir_papel(Papel.SINDICO, Papel.PORTEIRO)
so_sindico = exigir_papel(Papel.SINDICO)
quem_ve = exigir_papel(Papel.SINDICO, Papel.PORTEIRO, Papel.MORADOR)
PERMISSAO = "registrar_leituras"
NOME = {TipoConsumo.AGUA: "água", TipoConsumo.GAS: "gás"}
# Acima do dobro da média e com pelo menos 2 m³ a mais: os meses de um
# consumo muito pequeno não disparam alerta por meio metro cúbico.
FATOR_ALERTA = Decimal("2")
DIFERENCA_MINIMA = Decimal("2")
_hoje = hoje_local


def _m3(valor: Decimal) -> str:
    """12,5 m³ — sem os zeros que sobram."""
    texto = f"{valor:.3f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",") + " m³"


def _tarifa(valor: Decimal) -> str:
    texto = f"{valor:.4f}".rstrip("0")
    if len(texto.split(".")[1]) < 2:
        texto = f"{valor:.2f}"
    inteiro, centavos = texto.split(".")
    return reais(Decimal(inteiro))[:-3] + "," + centavos


def _mes(competencia: date) -> str:
    return competencia.strftime("%m/%Y")


def _cobrada(leitura: LeituraConsumo | None) -> bool:
    return (leitura is not None and leitura.cobranca is not None
            and leitura.cobranca.status != StatusCobranca.CANCELADA)


def _media(anteriores: list[LeituraConsumo]) -> Decimal | None:
    consumos = [l.consumo for l in anteriores if l.consumo is not None][-3:]
    if not consumos:
        return None
    return (sum(consumos) / len(consumos)).quantize(Decimal("0.001"))


def _acima(consumo: Decimal | None, media: Decimal | None) -> bool:
    return (consumo is not None and media is not None and media > 0
            and consumo > media * FATOR_ALERTA and consumo - media >= DIFERENCA_MINIMA)


def _travar(db: Session, condominio_id: int) -> None:
    """Duas pessoas lançando leituras ou gerando cobranças ao mesmo tempo
    esperam uma pela outra."""
    db.execute(select(func.pg_advisory_xact_lock(condominio_id, func.hashtext("consumo"))))


def _leituras_por_unidade(db: Session, condominio_id: int, tipo: TipoConsumo,
                          travar: bool = False) -> dict[int, list[LeituraConsumo]]:
    consulta = (select(LeituraConsumo)
                .options(selectinload(LeituraConsumo.cobranca))
                .where(LeituraConsumo.condominio_id == condominio_id,
                       LeituraConsumo.tipo == tipo)
                .order_by(LeituraConsumo.competencia))
    if travar:
        consulta = consulta.with_for_update(of=LeituraConsumo)
    por_unidade: dict[int, list[LeituraConsumo]] = {}
    for l in db.scalars(consulta).all():
        por_unidade.setdefault(l.unidade_id, []).append(l)
    return por_unidade


def _unidades(db: Session, condominio_id: int) -> list[Unidade]:
    return db.scalars(select(Unidade).where(
        Unidade.condominio_id == condominio_id, Unidade.pendente.is_(False))
        .order_by(Unidade.bloco, Unidade.numero)).all()


def _grade(db: Session, condominio_id: int, tipo: TipoConsumo,
           competencia: date) -> list[LinhaLeitura]:
    por_unidade = _leituras_por_unidade(db, condominio_id, tipo)
    linhas = []
    for u in _unidades(db, condominio_id):
        todas = por_unidade.get(u.id, [])
        antes = [l for l in todas if l.competencia < competencia]
        atual = next((l for l in todas if l.competencia == competencia), None)
        depois = any(l.competencia > competencia for l in todas)
        anterior = antes[-1] if antes else None
        linhas.append(LinhaLeitura(
            unidade_id=u.id, apartamento=u.identificacao,
            anterior_competencia=anterior.competencia if anterior else None,
            anterior_leitura=anterior.leitura if anterior else None,
            leitura=atual.leitura if atual else None,
            consumo=atual.consumo if atual else None,
            troca_medidor=atual.troca_medidor if atual else False,
            acima_do_normal=atual.acima_do_normal if atual else False,
            media=_media(antes), cobrada=_cobrada(atual),
            valor_cobrado=atual.cobranca.valor if _cobrada(atual) else None,
            pode_editar=not depois and not _cobrada(atual),
        ))
    return linhas


@router.get("/leituras", response_model=list[LinhaLeitura],
            summary="As leituras de um mês, apartamento por apartamento")
def ver_leituras(
    tipo: TipoConsumo,
    competencia: date,
    usuario: Usuario = Depends(equipe),
    db: Session = Depends(get_db),
) -> list[LinhaLeitura]:
    exigir_permissao_do_porteiro(db, usuario, PERMISSAO)
    return _grade(db, usuario.condominio_id, tipo, competencia.replace(day=1))


@router.post("/leituras", response_model=list[LinhaLeitura],
             summary="Lança (ou corrige) as leituras do mês")
def lancar_leituras(
    dados: LeiturasEntrada,
    usuario: Usuario = Depends(equipe),
    db: Session = Depends(get_db),
) -> list[LinhaLeitura]:
    exigir_permissao_do_porteiro(db, usuario, PERMISSAO)
    condominio_id = usuario.condominio_id
    _travar(db, condominio_id)
    unidades = {u.id: u for u in _unidades(db, condominio_id)}
    por_unidade = _leituras_por_unidade(db, condominio_id, dados.tipo, travar=True)
    mes = _mes(dados.competencia)
    avisos = []
    for item in dados.leituras:
        u = unidades.get(item.unidade_id)
        if u is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Unidade não encontrada.")
        todas = por_unidade.get(u.id, [])
        if any(l.competencia > dados.competencia for l in todas):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"O apto {u.identificacao} já tem leitura de um mês depois de {mes}.")
        atual = next((l for l in todas if l.competencia == dados.competencia), None)
        if _cobrada(atual):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A leitura de {mes} do apto {u.identificacao} já foi cobrada; "
                       "cancele a cobrança no financeiro para corrigir.")
        antes = [l for l in todas if l.competencia < dados.competencia]
        anterior = antes[-1] if antes else None
        if item.troca_medidor:
            consumo = item.leitura
        elif anterior is None:
            consumo = None
        elif item.leitura < anterior.leitura:
            raise HTTPException(
                status_code=422,
                detail=f"A leitura do apto {u.identificacao} ({_m3(item.leitura)}) é menor "
                       f"que a de {_mes(anterior.competencia)} ({_m3(anterior.leitura)}). "
                       "Se o medidor foi trocado, marque a troca.")
        else:
            consumo = item.leitura - anterior.leitura
        media = _media(antes)
        acima = _acima(consumo, media)
        if atual is None:
            atual = LeituraConsumo(condominio_id=condominio_id, unidade_id=u.id,
                                   tipo=dados.tipo, competencia=dados.competencia,
                                   leitura=item.leitura)
            db.add(atual)
            ja_avisado = False
        else:
            ja_avisado = atual.acima_do_normal and atual.consumo == consumo
        atual.leitura = item.leitura
        atual.consumo = consumo
        atual.troca_medidor = item.troca_medidor
        atual.acima_do_normal = acima
        atual.registrada_por_id = usuario.id
        if acima and not ja_avisado:
            avisos.append((u.id, (
                f"O consumo de {NOME[dados.tipo]} do apartamento em {mes} foi de {_m3(consumo)}, "
                f"mais que o dobro da média dos meses anteriores ({_m3(media)}). Pode ser um "
                "vazamento: confira torneiras, descargas e o registro.")))
    db.commit()
    for unidade_id, texto in avisos:
        destinatarios.avisar(destinatarios.moradores_da_unidade(db, unidade_id),
                             f"Consumo de {NOME[dados.tipo]} acima do normal", texto)
    return _grade(db, condominio_id, dados.tipo, dados.competencia)


@router.post("/cobrancas", response_model=LoteSaida, status_code=status.HTTP_201_CREATED,
             summary="Gera a cobrança do consumo do mês")
def gerar_cobrancas(
    dados: CobrancaConsumoEntrada,
    sindico: Usuario = Depends(so_sindico),
    db: Session = Depends(get_db),
) -> LoteSaida:
    condominio_id = sindico.condominio_id
    _travar(db, condominio_id)
    leituras = db.scalars(
        select(LeituraConsumo)
        .options(selectinload(LeituraConsumo.cobranca), selectinload(LeituraConsumo.unidade))
        .join(Unidade, Unidade.id == LeituraConsumo.unidade_id)
        .where(LeituraConsumo.condominio_id == condominio_id,
               LeituraConsumo.tipo == dados.tipo,
               LeituraConsumo.competencia == dados.competencia)
        .order_by(Unidade.bloco, Unidade.numero)
        .with_for_update(of=LeituraConsumo)).all()
    mes = _mes(dados.competencia)
    if not leituras:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Nenhuma leitura de {NOME[dados.tipo]} em {mes}.")
    hoje = _hoje()
    geradas, puladas = [], []
    for l in leituras:
        valor = None
        if l.consumo is not None:
            valor = (l.consumo * dados.tarifa).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if _cobrada(l) or valor is None or valor <= 0:
            puladas.append(l.unidade.identificacao)
            continue
        vencimento = dados.vencimento or _dia_de_vencimento(
            db, l.unidade_id, somar_meses(dados.competencia, 1))
        c = Cobranca(
            unidade_id=l.unidade_id, competencia=dados.competencia,
            descricao=(f"Consumo de {NOME[dados.tipo]} {mes}: {_m3(l.consumo)} × "
                       f"{_tarifa(dados.tarifa)}/m³"),
            valor=valor, vencimento=vencimento, origem=OrigemCobranca.CONSUMO,
            status=StatusCobranca.VENCIDA if vencimento < hoje else StatusCobranca.ABERTA,
        )
        db.add(c)
        db.flush()
        l.cobranca_id = c.id
        registro.registrar(db, sindico, registro.CRIOU, registro.COBRANCA, c.id)
        geradas.append(c)
    total = sum((c.valor for c in geradas), Decimal("0.00"))
    quantas = len(geradas)
    db.commit()
    return LoteSaida(geradas=quantas, puladas=puladas, total=total)


@router.get("/historico", response_model=list[HistoricoConsumo],
            summary="O consumo de um apartamento, mês a mês")
def historico(
    tipo: TipoConsumo,
    unidade_id: int | None = Query(default=None),
    usuario: Usuario = Depends(quem_ve),
    db: Session = Depends(get_db),
) -> list[HistoricoConsumo]:
    """O morador vê o do apartamento dele; a equipe informa o apartamento."""
    if usuario.papel == Papel.MORADOR:
        unidade_id = usuario.unidade_id
    else:
        exigir_permissao_do_porteiro(db, usuario, PERMISSAO)
        if unidade_id is None:
            raise HTTPException(status_code=422, detail="Informe o apartamento.")
    leituras = db.scalars(
        select(LeituraConsumo).options(selectinload(LeituraConsumo.cobranca))
        .where(LeituraConsumo.condominio_id == usuario.condominio_id,
               LeituraConsumo.unidade_id == unidade_id, LeituraConsumo.tipo == tipo)
        .order_by(LeituraConsumo.competencia.desc()).limit(12)).all()
    return [HistoricoConsumo(
        competencia=l.competencia, leitura=l.leitura, consumo=l.consumo,
        troca_medidor=l.troca_medidor, acima_do_normal=l.acima_do_normal,
        valor_cobrado=l.cobranca.valor if _cobrada(l) else None,
    ) for l in leituras]

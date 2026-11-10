"""Acordo de parcelamento das cobranças vencidas.

O apartamento em atraso não consegue pagar tudo de uma vez, e o síndico
fazia o acordo de boca, lançando as parcelas à mão e lembrando de dar
baixa nas cobranças antigas. Agora o síndico escolhe as cobranças
vencidas do apartamento; o sistema soma o que falta de cada uma com a
multa e os juros do dia (ou sem eles, se o síndico dispensar), divide em
até 24 parcelas mensais sem perder centavo e lança cada parcela como uma
cobrança. As cobranças do acordo ficam "negociadas": não contam mais como
atraso — a dívida passa a ser as parcelas, que têm multa e juros próprios
se atrasarem. O acordo lançado errado se desfaz enquanto nenhuma parcela
foi paga.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import exigir_papel
from app.core.database import get_db
from app.core.formato import reais
from app.core.tempo import agora_utc, hoje_local, somar_meses
from app.models.condominio import Condominio, Unidade
from app.models.enums import OrigemCobranca, Papel, StatusCobranca
from app.models.financeiro import Acordo, Cobranca, Pagamento
from app.models.usuario import Usuario
from app.schemas.acordo import AcordoEntrada, AcordoSaida, CancelamentoAcordo, CobrancaDoAcordo
from app.services import encargos as calculo_encargos
from app.services import registro
from app.services.cobrancas import ratear, totais_pagos
from app.services.destinatarios import avisar, moradores_da_unidade

router = APIRouter(prefix="/financeiro/acordos", tags=["Financeiro"])

ZERO = Decimal("0.00")
# Parcela de centavos não é acordo: é engano no número de parcelas.
PARCELA_MINIMA = Decimal("10.00")
EM_ABERTO = (StatusCobranca.ABERTA, StatusCobranca.VENCIDA)


def _hoje() -> date:
    return hoje_local()


def _cobrancas(db: Session, acordo_ids: list[int]) -> dict[int, list[Cobranca]]:
    por_acordo: dict[int, list[Cobranca]] = {i: [] for i in acordo_ids}
    if acordo_ids:
        for c in db.scalars(select(Cobranca).where(Cobranca.acordo_id.in_(acordo_ids))
                            .order_by(Cobranca.vencimento, Cobranca.id)).all():
            por_acordo[c.acordo_id].append(c)
    return por_acordo


def _saida(db: Session, acordos: list[Acordo], usuario: Usuario) -> list[AcordoSaida]:
    hoje = _hoje()
    por_acordo = _cobrancas(db, [a.id for a in acordos])
    pagos = totais_pagos(db, [c.id for lista in por_acordo.values() for c in lista])
    saida = []
    for a in acordos:
        def item(c: Cobranca) -> CobrancaDoAcordo:
            return CobrancaDoAcordo(id=c.id, descricao=c.descricao, valor=c.valor,
                                    vencimento=c.vencimento, status=c.status, origem=c.origem,
                                    total_pago=pagos.get(c.id, ZERO))
        cobrancas = por_acordo[a.id]
        parcelas = [c for c in cobrancas if c.origem == OrigemCobranca.ACORDO]
        negociadas = [c for c in cobrancas if c.origem != OrigemCobranca.ACORDO]
        devidas = [p for p in parcelas if p.status != StatusCobranca.CANCELADA]
        if a.cancelado_em is not None:
            situacao = "cancelado"
        elif devidas and all(p.status == StatusCobranca.PAGA for p in devidas):
            situacao = "quitado"
        elif any(p.status in EM_ABERTO and p.vencimento < hoje for p in devidas):
            situacao = "em_atraso"
        else:
            situacao = "em_dia"
        saida.append(AcordoSaida(
            id=a.id, unidade_id=a.unidade_id, unidade=a.unidade.identificacao,
            principal=a.principal, encargos=a.encargos, total=a.total,
            dispensou_encargos=a.dispensou_encargos, parcelas=a.parcelas,
            primeiro_vencimento=a.primeiro_vencimento, observacao=a.observacao,
            criado_por_nome=a.criado_por.nome if a.criado_por else None, criado_em=a.criado_em,
            cancelado_em=a.cancelado_em, motivo_cancelamento=a.motivo_cancelamento,
            situacao=situacao, negociadas=[item(c) for c in negociadas],
            lista_parcelas=[item(p) for p in parcelas],
            pode_cancelar=(usuario.papel == Papel.SINDICO and a.cancelado_em is None
                           and not any(pagos.get(p.id, ZERO) > 0
                                       or p.status == StatusCobranca.PAGA for p in parcelas)),
        ))
    return saida


@router.get("", response_model=list[AcordoSaida], summary="Acordos de parcelamento")
def listar(
    usuario: Usuario = Depends(exigir_papel(Papel.SINDICO, Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> list[AcordoSaida]:
    """O síndico vê todos; o morador, os do apartamento — a dívida é do
    apartamento, como as cobranças."""
    if usuario.condominio_id is None:
        return []
    consulta = (select(Acordo).options(selectinload(Acordo.unidade),
                                       selectinload(Acordo.criado_por))
                .where(Acordo.condominio_id == usuario.condominio_id))
    if usuario.papel == Papel.MORADOR:
        consulta = consulta.where(Acordo.unidade_id == usuario.unidade_id)
    acordos = db.scalars(consulta.order_by(Acordo.criado_em.desc(), Acordo.id.desc())
                         .limit(200)).all()
    return _saida(db, list(acordos), usuario)


@router.post("", response_model=AcordoSaida, status_code=status.HTTP_201_CREATED,
             summary="Fazer um acordo de parcelamento")
def criar(
    dados: AcordoEntrada,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> AcordoSaida:
    unidade = db.get(Unidade, dados.unidade_id)
    if unidade is None or unidade.condominio_id != sindico.condominio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Apartamento não encontrado.")
    condominio = db.get(Condominio, sindico.condominio_id)
    hoje = _hoje()
    # Travadas: um pagamento ou outro acordo ao mesmo tempo não pode
    # mexer nelas enquanto o acordo é feito.
    cobrancas = db.scalars(
        select(Cobranca).where(Cobranca.id.in_(dados.cobranca_ids))
        .order_by(Cobranca.vencimento, Cobranca.id).with_for_update()
    ).all()
    if len(cobrancas) != len(dados.cobranca_ids) or any(
            c.unidade_id != unidade.id for c in cobrancas):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Cobrança não encontrada neste apartamento.")
    for c in cobrancas:
        if c.status not in EM_ABERTO:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"\"{c.descricao}\" não está em aberto.")
        if c.vencimento >= hoje:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"\"{c.descricao}\" ainda não venceu: só entram no "
                                       "acordo as cobranças vencidas.")

    pagos = totais_pagos(db, [c.id for c in cobrancas])
    principal = sum((c.valor - pagos.get(c.id, ZERO) for c in cobrancas), ZERO)
    encargos = ZERO if dados.dispensar_encargos else sum(
        (calculo_encargos.calcular(c.valor - pagos.get(c.id, ZERO), c.vencimento, hoje,
                                   condominio.multa_atraso, condominio.juros_mensais).total
         for c in cobrancas), ZERO)
    total = principal + encargos
    valores = ratear(total, [Decimal(1)] * dados.parcelas)
    if min(valores) < PARCELA_MINIMA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cada parcela precisa ser de pelo menos {reais(PARCELA_MINIMA)}: "
                   f"{reais(total)} em {dados.parcelas} parcelas não dá. Use menos parcelas.")

    acordo = Acordo(condominio_id=condominio.id, unidade_id=unidade.id, criado_por_id=sindico.id,
                    principal=principal, encargos=encargos, total=total,
                    dispensou_encargos=dados.dispensar_encargos, parcelas=dados.parcelas,
                    primeiro_vencimento=dados.primeiro_vencimento, observacao=dados.observacao)
    db.add(acordo)
    db.flush()
    for i, valor in enumerate(valores):
        vencimento = somar_meses(dados.primeiro_vencimento, i)
        db.add(Cobranca(
            unidade_id=unidade.id, competencia=vencimento.replace(day=1),
            descricao=f"Acordo nº {acordo.id} — parcela {i + 1}/{dados.parcelas}",
            valor=valor, vencimento=vencimento, status=StatusCobranca.ABERTA,
            origem=OrigemCobranca.ACORDO, acordo_id=acordo.id,
        ))
    for c in cobrancas:
        c.status = StatusCobranca.NEGOCIADA
        c.acordo_id = acordo.id
        registro.registrar(db, sindico, registro.EDITOU, registro.COBRANCA, c.id,
                           f"Negociada no acordo nº {acordo.id}")
    registro.registrar(
        db, sindico, registro.CRIOU, registro.ACORDO, acordo.id,
        f"{reais(total)} em {dados.parcelas}x"
        + (" (multa e juros dispensados)" if dados.dispensar_encargos else ""))
    db.commit()
    db.refresh(acordo)

    parcela = (f"{dados.parcelas} parcelas de {reais(valores[-1])}" if dados.parcelas > 1
               else "uma parcela")
    avisar(moradores_da_unidade(db, unidade.id, so_quem_mora=False), "Acordo de parcelamento",
           f"O acordo nº {acordo.id} do apartamento {unidade.identificacao} junta "
           f"{len(cobrancas)} {'cobrança vencida' if len(cobrancas) == 1 else 'cobranças vencidas'}"
           f" em {reais(total)}: {parcela}, a primeira em "
           f"{dados.primeiro_vencimento:%d/%m/%Y}. As parcelas estão nas suas cobranças.")
    return _saida(db, [acordo], sindico)[0]


@router.post("/{acordo_id}/cancelamento", response_model=AcordoSaida,
             summary="Desfazer o acordo lançado errado")
def cancelar(
    acordo_id: int,
    dados: CancelamentoAcordo,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> AcordoSaida:
    """Só antes de qualquer parcela ser paga: as parcelas são canceladas e
    as cobranças negociadas voltam a ser devidas como eram."""
    acordo = db.get(Acordo, acordo_id, with_for_update=True)
    if acordo is None or acordo.condominio_id != sindico.condominio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Acordo não encontrado.")
    if acordo.cancelado_em is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Este acordo já foi desfeito.")
    cobrancas = db.scalars(select(Cobranca).where(Cobranca.acordo_id == acordo.id)
                           .with_for_update()).all()
    parcelas = [c for c in cobrancas if c.origem == OrigemCobranca.ACORDO]
    pagamentos = db.scalar(select(func.count()).select_from(Pagamento)
                           .where(Pagamento.cobranca_id.in_([p.id for p in parcelas])))
    if pagamentos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já há parcela paga: o acordo não pode ser desfeito. Corrija as parcelas "
                   "que faltam, se preciso.")
    hoje = _hoje()
    for p in parcelas:
        p.status = StatusCobranca.CANCELADA
    for c in cobrancas:
        if c.status == StatusCobranca.NEGOCIADA:
            c.status = StatusCobranca.VENCIDA if c.vencimento < hoje else StatusCobranca.ABERTA
            registro.registrar(db, sindico, registro.EDITOU, registro.COBRANCA, c.id,
                               f"Voltou a ser devida: o acordo nº {acordo.id} foi desfeito")
    acordo.cancelado_em = agora_utc()
    acordo.cancelado_por_id = sindico.id
    acordo.motivo_cancelamento = dados.motivo
    registro.registrar(db, sindico, registro.CANCELOU, registro.ACORDO, acordo.id, dados.motivo)
    db.commit()
    db.refresh(acordo)
    avisar(moradores_da_unidade(db, acordo.unidade_id, so_quem_mora=False), "Acordo desfeito",
           f"O acordo nº {acordo.id} do apartamento {acordo.unidade.identificacao} foi desfeito "
           f"pelo síndico: as parcelas saíram e as cobranças voltaram como eram. "
           f"Motivo: {dados.motivo}")
    return _saida(db, [acordo], sindico)[0]

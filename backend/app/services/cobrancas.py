"""Cobranças que nascem de outras coisas — a taxa de uso de um espaço — e
o quanto já foi pago de cada uma.

A taxa de uso entra nas cobranças do apartamento quando o síndico aprova
a reserva; cancelada a reserva, sai — a não ser que já tenha sido paga
(ou paga em parte): pagamento não se apaga, e a devolução fica com o
síndico.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import OrigemCobranca, StatusCobranca
from app.models.espaco import EspacoComum, Reserva
from app.models.financeiro import Cobranca, Pagamento


# O que abateu do valor da cobrança: cada pagamento menos a parte que foi
# para a multa e os juros do atraso.
_ABATIDO = Pagamento.valor - Pagamento.encargos


def total_pago(db: Session, cobranca_id: int) -> Decimal:
    """Soma, no banco, o que já abateu do valor da cobrança.

    Ler pela relacionamento `cobranca.pagamentos` nao serve logo depois de
    inserir um pagamento: a coleção já foi carregada antes do flush e fica
    desatualizada, o que fazia a cobrança quitada continuar em aberto.
    """
    total = db.scalar(
        select(func.coalesce(func.sum(_ABATIDO), 0)).where(
            Pagamento.cobranca_id == cobranca_id
        )
    )
    return Decimal(total or 0)


def totais_pagos(db: Session, ids: list[int]) -> dict[int, Decimal]:
    """O total pago de várias cobranças numa consulta só. Somar uma a uma
    fazia a lista de um ano de um prédio passar de mil consultas."""
    if not ids:
        return {}
    linhas = db.execute(
        select(Pagamento.cobranca_id, func.sum(_ABATIDO))
        .where(Pagamento.cobranca_id.in_(ids))
        .group_by(Pagamento.cobranca_id)
    ).all()
    return {cobranca_id: Decimal(total) for cobranca_id, total in linhas}


def gerar_taxa_de_uso(db: Session, reserva: Reserva, espaco: EspacoComum, unidade_id: int,
                      hoje: date) -> Cobranca | None:
    if not espaco.taxa_uso or reserva.cobranca_id is not None:
        return None
    cobranca = Cobranca(
        unidade_id=unidade_id, competencia=reserva.data.replace(day=1),
        descricao=f"Uso do espaço {espaco.nome} em {reserva.data:%d/%m/%Y}"[:180],
        valor=espaco.taxa_uso, vencimento=max(reserva.data, hoje),
        status=StatusCobranca.ABERTA, origem=OrigemCobranca.USO_ESPACO,
    )
    db.add(cobranca)
    db.flush()
    reserva.cobranca_id = cobranca.id
    return cobranca


def cancelar_taxa_de_uso(db: Session, cobranca_id: int | None) -> bool:
    """Cancela a taxa da reserva cancelada, se nada dela foi pago."""
    if cobranca_id is None:
        return False
    cobranca = db.get(Cobranca, cobranca_id, with_for_update=True)
    if cobranca is None or cobranca.status not in (StatusCobranca.ABERTA, StatusCobranca.VENCIDA):
        return False
    pago = db.scalar(select(func.count()).select_from(Pagamento)
                     .where(Pagamento.cobranca_id == cobranca.id))
    if pago:
        return False
    cobranca.status = StatusCobranca.CANCELADA
    return True


def ratear(total: Decimal, pesos: list[Decimal]) -> list[Decimal]:
    """Divide `total` na proporção dos `pesos`, em centavos, sem perder nem
    criar centavo: cada parte é arredondada para baixo e os centavos que
    sobram vão, um a um, para as partes que mais perderam no arredondamento
    (e, no empate, para as primeiras). Pesos iguais dividem por igual:
    R$ 100,00 em 3 parcelas são 33,34 + 33,33 + 33,33."""
    centavos = int((total * 100).to_integral_value())
    soma = sum(pesos)
    if soma <= 0 or not pesos:
        raise ValueError("Os pesos do rateio precisam somar mais que zero.")
    exatas = [Decimal(centavos) * p / soma for p in pesos]
    partes = [int(e) for e in exatas]
    sobra = centavos - sum(partes)
    ordem = sorted(range(len(pesos)), key=lambda i: (-(exatas[i] - partes[i]), i))
    for i in ordem[:sobra]:
        partes[i] += 1
    return [(Decimal(p) / 100).quantize(Decimal("0.01")) for p in partes]

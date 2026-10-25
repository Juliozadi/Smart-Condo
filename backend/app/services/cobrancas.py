"""Cobranças que nascem de outras coisas: a taxa de uso de um espaço.

A taxa de uso entra nas cobranças do apartamento quando o síndico aprova
a reserva; cancelada a reserva, sai — a não ser que já tenha sido paga
(ou paga em parte): pagamento não se apaga, e a devolução fica com o
síndico.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import OrigemCobranca, StatusCobranca
from app.models.espaco import EspacoComum, Reserva
from app.models.financeiro import Cobranca, Pagamento


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

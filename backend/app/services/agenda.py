"""O que vale para tudo o que se marca com data e horário — a reserva do
espaço e a mudança: quando o horário já chegou, e o fechamento do que
passou."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, or_, update
from sqlalchemy.orm import Session

MOTIVO_SEM_AVALIACAO = "O horário chegou sem a avaliação do síndico."


def ja_comecou(marcado, agora: datetime) -> bool:
    """A de ontem, ou a de hoje cujo horário já chegou."""
    return marcado.data < agora.date() or (
        marcado.data == agora.date() and marcado.hora_inicio <= agora.time()
    )


def encerrar_passadas(db: Session, modelo, status, onde, agora: datetime) -> None:
    """Nada marcava como realizada: a aprovada do mês passado continuava
    "em aberto" para o morador, e a pendente esquecida ficava pendente para
    sempre. Como a cobrança vencida, isso se acerta na consulta: a aprovada
    cujo horário terminou vira concluída, e a pendente cujo horário chegou
    sem avaliação vira recusada.

    `status` é o enum do modelo (StatusReserva, StatusMudanca); `onde`, a
    condição que limita ao condomínio."""
    hoje, hora = agora.date(), agora.time()
    db.execute(
        update(modelo)
        .where(onde, modelo.status == status.APROVADA,
               or_(modelo.data < hoje, and_(modelo.data == hoje, modelo.hora_fim <= hora)))
        .values(status=status.CONCLUIDA)
        .execution_options(synchronize_session=False)
    )
    db.execute(
        update(modelo)
        .where(onde, modelo.status == status.PENDENTE,
               or_(modelo.data < hoje, and_(modelo.data == hoje, modelo.hora_inicio <= hora)))
        .values(status=status.RECUSADA, motivo_recusa=MOTIVO_SEM_AVALIACAO)
        .execution_options(synchronize_session=False)
    )
    db.commit()

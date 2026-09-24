"""As listagens fazem o mesmo número de consultas com 3 ou com 30 itens.

Antes, cada linha buscava a sua unidade e somava os seus pagamentos: a
lista de cobranças de um ano de um prédio de 60 unidades passava de mil
e seiscentas consultas ao banco, e a de reservas, de quatrocentas. Estes
testes medem as consultas de cada listagem, acrescentam itens e exigem
que o número não cresça.
"""
from __future__ import annotations

from datetime import time, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import event

from app.core.database import engine
from app.core.tempo import hoje_local
from app.models.condominio import Unidade
from app.models.enums import FormaPagamento, Papel, StatusCobranca, StatusReserva, StatusUsuario
from app.models.espaco import Reserva
from app.models.financeiro import Cobranca, Pagamento
from app.models.usuario import Usuario
from tests.fixtures import cab
from tests.test_reservas import cenario  # noqa: F401


def consultas(cliente, rota, tok):
    contagem = [0]

    def contar(*_):
        contagem[0] += 1

    event.listen(engine, "before_cursor_execute", contar)
    try:
        r = cliente.get(rota, headers=cab(tok))
    finally:
        event.remove(engine, "before_cursor_execute", contar)
    assert r.status_code == 200, r.text
    return contagem[0]


def acrescentar(db, cenario, quantos, inicio):
    """Unidades com morador, cobranças pagas pela metade e reservas."""
    sindico = db.query(Usuario).filter(Usuario.papel == Papel.SINDICO).first()
    for i in range(inicio, inicio + quantos):
        unidade = Unidade(condominio_id=sindico.condominio_id, bloco=f"B{i}",
                          numero=str(100 + i), vagas_garagem=1)
        db.add(unidade)
        db.flush()
        morador = Usuario(
            nome=f"Morador {i}", email=f"m{i}@exemplo.com", cpf=f"{i:011d}",
            telefone="67999990000", senha_hash="x", papel=Papel.MORADOR,
            status=StatusUsuario.ATIVO, condominio_id=sindico.condominio_id,
            unidade_id=unidade.id,
        )
        db.add(morador)
        db.flush()
        for m in range(3):
            competencia = (hoje_local().replace(day=1) - timedelta(days=31 * m)).replace(day=1)
            cobranca = Cobranca(unidade_id=unidade.id, competencia=competencia,
                                descricao="Taxa", valor=Decimal("320.00"),
                                vencimento=competencia + timedelta(days=9),
                                status=StatusCobranca.ABERTA)
            db.add(cobranca)
            db.flush()
            db.add(Pagamento(cobranca_id=cobranca.id, pago_por_id=sindico.id,
                             valor=Decimal("100.00"), forma=FormaPagamento.PIX,
                             pago_em=cobranca.criado_em or hoje_local()))
        db.add(Reserva(espaco_id=cenario["salao"]["id"], morador_id=morador.id,
                       data=hoje_local() - timedelta(days=i + 1),
                       hora_inicio=time(10), hora_fim=time(12),
                       status=StatusReserva.CONCLUIDA))
    db.commit()


@pytest.mark.parametrize("papel, rota", [
    ("sindico", "/api/v1/financeiro/cobrancas"),
    ("sindico", "/api/v1/financeiro/resumo"),
    ("sindico", "/api/v1/espacos/reservas"),
    ("sindico", "/api/v1/usuarios"),
    ("sindico", "/api/v1/mensagens/contatos"),
    ("admin", "/api/v1/admin/usuarios"),
])
def test_listagem_nao_cresce_com_os_itens(cliente, db, cenario, papel, rota):
    from tests.fixtures import token

    tok = cenario["sindico"] if papel == "sindico" else token(
        cliente, "admin@exemplo.com", "senhaforte123")
    acrescentar(db, cenario, 3, inicio=1)
    poucos = consultas(cliente, rota, tok)
    acrescentar(db, cenario, 27, inicio=4)
    muitos = consultas(cliente, rota, tok)
    assert muitos == poucos, f"{rota}: {poucos} consultas com 3 itens, {muitos} com 30"

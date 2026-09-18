"""Modelos do SmartCondo.

Importar tudo aqui garante que o Alembic e o SQLAlchemy enxerguem todas as
tabelas ao resolver o mapeamento e gerar as migrações.
"""
from app.models.comunicado import Comunicado, LeituraComunicado
from app.models.condominio import Condominio, Unidade
from app.models.enums import (
    CanalVerificacao, CategoriaComunicado, FinalidadeCodigo, FormaPagamento, Papel,
    StatusCobranca, StatusEncomenda, StatusOcorrencia, StatusReserva, StatusUsuario,
    StatusVisitante, TipoOcupacao,
)
from app.models.espaco import EspacoComum, RegistroOcupacao, Reserva
from app.models.financeiro import Cobranca, Pagamento, PreferenciaCobranca
from app.models.portaria import Encomenda, Ocorrencia, Visitante
from app.models.usuario import CodigoVerificacao, PermissaoPorteiro, Usuario

__all__ = [
    "Cobranca", "CodigoVerificacao", "Comunicado", "Condominio", "Encomenda",
    "EspacoComum", "LeituraComunicado", "Ocorrencia", "Pagamento",
    "PermissaoPorteiro", "PreferenciaCobranca", "RegistroOcupacao", "Reserva",
    "Unidade", "Usuario", "Visitante",
    "CanalVerificacao", "CategoriaComunicado", "FinalidadeCodigo", "FormaPagamento",
    "Papel", "StatusCobranca", "StatusEncomenda", "StatusOcorrencia", "StatusReserva",
    "StatusUsuario", "StatusVisitante", "TipoOcupacao",
]

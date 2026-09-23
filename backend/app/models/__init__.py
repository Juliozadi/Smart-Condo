"""Modelos do SmartCondo.

Importar tudo aqui garante que o Alembic e o SQLAlchemy enxerguem todas as
tabelas ao resolver o mapeamento e gerar as migrações.
"""
from app.models.comunicado import Comunicado, LeituraComunicado
from app.models.condominio import Condominio, Unidade
from app.models.documento_cadastro import DocumentoCadastro
from app.models.enums import (
    CanalVerificacao, CategoriaComunicado, CategoriaDocumento, CategoriaVeiculo,
    FinalidadeCodigo, FormaPagamento, Papel, PrioridadeOrdemServico, StatusCobranca,
    StatusEncomenda, StatusOcorrencia, StatusOrdemServico, StatusReserva, StatusUsuario,
    StatusVisitante, TipoDocumentoCadastro, TipoMovimentacao, TipoOcupacao,
)
from app.models.mensagem import Mensagem
from app.models.espaco import EspacoComum, RegistroOcupacao, Reserva
from app.models.operacao import Documento, MovimentacaoVeiculo, OrdemServico
from app.models.financeiro import Cobranca, Pagamento, PreferenciaCobranca
from app.models.portaria import Encomenda, Ocorrencia, Visitante
from app.models.usuario import CodigoVerificacao, PermissaoPorteiro, Usuario

__all__ = [
    "Cobranca", "CodigoVerificacao", "Comunicado", "Condominio", "Documento",
    "DocumentoCadastro",
    "Encomenda", "EspacoComum", "LeituraComunicado", "Mensagem", "MovimentacaoVeiculo",
    "Ocorrencia", "OrdemServico", "Pagamento", "PermissaoPorteiro",
    "PreferenciaCobranca", "RegistroOcupacao", "Reserva", "Unidade", "Usuario",
    "Visitante",
    "CanalVerificacao", "CategoriaComunicado", "CategoriaDocumento", "CategoriaVeiculo",
    "FinalidadeCodigo", "FormaPagamento", "Papel", "PrioridadeOrdemServico",
    "StatusCobranca", "StatusEncomenda", "StatusOcorrencia", "StatusOrdemServico",
    "StatusReserva", "StatusUsuario", "StatusVisitante", "TipoDocumentoCadastro",
    "TipoMovimentacao", "TipoOcupacao",
]

"""Modelos do SmartCondo.

Importar tudo aqui garante que o Alembic e o SQLAlchemy enxerguem todas as
tabelas ao resolver o mapeamento e gerar as migrações.
"""
from app.models.assembleia import Assembleia, ItemPauta, Voto
from app.models.comunicado import Comunicado, LeituraComunicado
from app.models.condominio import Condominio, Unidade
from app.models.documento_cadastro import DocumentoCadastro
from app.models.enums import (
    CanalVerificacao, CategoriaComunicado, CategoriaDespesa, CategoriaDocumento, CategoriaVeiculo,
    EscolhaVoto, MaioriaExigida,
    FinalidadeCodigo, FormaPagamento, Papel, PrioridadeOrdemServico, StatusCobranca,
    StatusEncomenda, StatusOcorrencia, StatusOrdemServico, StatusReserva, StatusUsuario,
    OrigemCobranca, StatusInfracao, StatusMudanca, StatusVisitante, TipoDocumentoCadastro,
    TipoInfracao, TipoMovimentacao, TipoMudanca, TipoOcupacao,
)
from app.models.declaracao import DeclaracaoQuitacao
from app.models.preventiva import PlanoManutencao, RealizacaoManutencao
from app.models.infracao import Infracao
from app.models.livro import AnotacaoPortaria, CienciaAnotacao
from app.models.mensagem import Mensagem
from app.models.mudanca import HorarioMudanca, Mudanca
from app.models.espaco import EspacoComum, RegistroOcupacao, Reserva
from app.models.operacao import Documento, MovimentacaoVeiculo, OrdemServico, VeiculoUnidade
from app.models.financeiro import Cobranca, Despesa, Pagamento, PreferenciaCobranca
from app.models.portaria import AutorizacaoVisita, Encomenda, Ocorrencia, Visitante
from app.models.registro import RegistroAlteracao
from app.models.usuario import CodigoVerificacao, PermissaoPorteiro, Usuario

__all__ = [
    "Assembleia", "ItemPauta", "Voto",
    "Cobranca", "CodigoVerificacao", "Comunicado", "Condominio", "Despesa", "Documento",
    "DocumentoCadastro",
    "Encomenda", "EspacoComum", "LeituraComunicado", "Mensagem", "MovimentacaoVeiculo", "Mudanca",
    "HorarioMudanca", "Infracao", "AnotacaoPortaria", "CienciaAnotacao", "DeclaracaoQuitacao",
    "PlanoManutencao", "RealizacaoManutencao",
    "Ocorrencia", "OrdemServico", "Pagamento", "PermissaoPorteiro",
    "PreferenciaCobranca", "RegistroAlteracao", "RegistroOcupacao", "Reserva", "Unidade",
    "Usuario", "VeiculoUnidade",
    "AutorizacaoVisita", "Visitante",
    "CanalVerificacao", "CategoriaComunicado", "CategoriaDespesa", "CategoriaDocumento",
    "CategoriaVeiculo", "EscolhaVoto", "MaioriaExigida",
    "FinalidadeCodigo", "FormaPagamento", "Papel", "PrioridadeOrdemServico",
    "StatusCobranca", "StatusEncomenda", "StatusOcorrencia", "StatusOrdemServico",
    "StatusMudanca", "StatusReserva", "StatusUsuario", "StatusVisitante", "TipoDocumentoCadastro",
    "TipoMovimentacao", "TipoMudanca", "TipoOcupacao", "OrigemCobranca", "StatusInfracao",
    "TipoInfracao",
]

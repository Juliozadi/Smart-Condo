"""Enumerações do domínio (documentação, seções 8 e 9)."""
import enum


class Papel(str, enum.Enum):
    """Documentação, seção 8 — Descrição dos Usuários.

    O administrador não é um papel do condomínio: é quem opera a
    plataforma. Cadastra os condomínios e os síndicos de cada um, e pode
    administrar qualquer usuário de qualquer condomínio.
    """
    ADMIN = "admin"
    SINDICO = "sindico"
    PORTEIRO = "porteiro"
    MORADOR = "morador"


class StatusUsuario(str, enum.Enum):
    """O cadastro passa por confirmação do código e aprovação do síndico."""
    AGUARDANDO_CODIGO = "aguardando_codigo"
    AGUARDANDO_APROVACAO = "aguardando_aprovacao"
    ATIVO = "ativo"
    RECUSADO = "recusado"
    INATIVO = "inativo"


class CanalVerificacao(str, enum.Enum):
    """"o sistema envia um código pelo meio escolhido pelo usuário" (seção 9)."""
    EMAIL = "email"
    SMS = "sms"


class FinalidadeCodigo(str, enum.Enum):
    CONFIRMACAO_CADASTRO = "confirmacao_cadastro"
    RECUPERACAO_SENHA = "recuperacao_senha"


class TipoOcupacao(str, enum.Enum):
    PROPRIETARIO = "proprietario"
    INQUILINO = "inquilino"
    COABITANTE = "coabitante"


class StatusReserva(str, enum.Enum):
    """O síndico aprova ou recusa (seção 11.5.3)."""
    PENDENTE = "pendente"
    APROVADA = "aprovada"
    RECUSADA = "recusada"
    CANCELADA = "cancelada"
    CONCLUIDA = "concluida"


class FormaPagamento(str, enum.Enum):
    """"variadas opções para formas de pagamento" (seção 6)."""
    PIX = "pix"
    BOLETO = "boleto"
    DEBITO_AUTOMATICO = "debito_automatico"
    CARTAO = "cartao"


class StatusCobranca(str, enum.Enum):
    ABERTA = "aberta"
    PAGA = "paga"
    VENCIDA = "vencida"
    CANCELADA = "cancelada"


class StatusVisitante(str, enum.Enum):
    """O morador confirma ou recusa a entrada do visitante (seção 6)."""
    AGUARDANDO_CONFIRMACAO = "aguardando_confirmacao"
    CONFIRMADO = "confirmado"
    RECUSADO = "recusado"
    DENTRO = "dentro"
    SAIU = "saiu"


class StatusEncomenda(str, enum.Enum):
    AGUARDANDO_RETIRADA = "aguardando_retirada"
    RETIRADA = "retirada"
    RECUSADA = "recusada"


class StatusOcorrencia(str, enum.Enum):
    ABERTA = "aberta"
    EM_ANALISE = "em_analise"
    RESOLVIDA = "resolvida"
    ARQUIVADA = "arquivada"


class PrioridadeOcorrencia(str, enum.Enum):
    """Quanto o caso corre: alimenta a fila de atendimento do síndico."""
    BAIXA = "baixa"
    NORMAL = "normal"
    ALTA = "alta"
    URGENTE = "urgente"


class CategoriaComunicado(str, enum.Enum):
    GERAL = "geral"
    MANUTENCAO = "manutencao"
    FINANCEIRO = "financeiro"
    SEGURANCA = "seguranca"
    EVENTO = "evento"
    URGENTE = "urgente"


class TipoMovimentacao(str, enum.Enum):
    """Documentação, seção 8: o porteiro registra entradas e saídas."""
    ENTRADA = "entrada"
    SAIDA = "saida"


class CategoriaVeiculo(str, enum.Enum):
    MORADOR = "morador"
    VISITANTE = "visitante"
    PRESTADOR = "prestador"


class PrioridadeOrdemServico(str, enum.Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"


class StatusOrdemServico(str, enum.Enum):
    ABERTA = "aberta"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


class CategoriaDocumento(str, enum.Enum):
    """Documentação, seção 11.6: atas, convenção e regimento interno."""
    CONVENCAO = "convencao"
    REGIMENTO = "regimento"
    ATA = "ata"
    PLANTA = "planta"
    PRESTACAO_CONTAS = "prestacao_contas"
    OUTRO = "outro"

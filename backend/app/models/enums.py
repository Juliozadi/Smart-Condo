"""Enumerações do domínio (documentação, seções 8 e 12)."""
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
    """"o sistema envia um código pelo meio escolhido pelo usuário" (seção 12)."""
    EMAIL = "email"
    SMS = "sms"


class FinalidadeCodigo(str, enum.Enum):
    CONFIRMACAO_CADASTRO = "confirmacao_cadastro"
    RECUPERACAO_SENHA = "recuperacao_senha"


class TipoOcupacao(str, enum.Enum):
    PROPRIETARIO = "proprietario"
    INQUILINO = "inquilino"
    COABITANTE = "coabitante"


class TipoDocumentoCadastro(str, enum.Enum):
    """Documentos que o morador envia ao se cadastrar."""
    IDENTIDADE = "identidade"            # RG ou CNH
    COMPROVANTE_RESIDENCIA = "comprovante_residencia"  # ou contrato de locação
    ESCRITURA = "escritura"              # só proprietário; opcional


class StatusReserva(str, enum.Enum):
    """O síndico aprova ou recusa (seção 13.5.3)."""
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
    # O morador não respondeu a tempo: o visitante não fica "aguardando"
    # para sempre na portaria, nem é confirmado dias depois.
    SEM_RESPOSTA = "sem_resposta"


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


class MaioriaExigida(str, enum.Enum):
    """Quantos votos um item da pauta precisa para ser aprovado."""
    SIMPLES = "simples"            # mais a favor que contra (art. 1.352)
    DOIS_TERCOS = "dois_tercos"    # 2/3 de todas as unidades (arts. 1.341 e 1.351)
    UNANIMIDADE = "unanimidade"    # todas as unidades


class EscolhaVoto(str, enum.Enum):
    A_FAVOR = "a_favor"
    CONTRA = "contra"
    ABSTENCAO = "abstencao"


class CategoriaDespesa(str, enum.Enum):
    """Para onde vai o dinheiro do condomínio, na prestação de contas."""
    AGUA = "agua"
    ENERGIA = "energia"
    LIMPEZA = "limpeza"
    MANUTENCAO = "manutencao"
    SEGURANCA = "seguranca"
    PESSOAL = "pessoal"
    ADMINISTRACAO = "administracao"
    OBRAS = "obras"
    OUTROS = "outros"


class TipoMudanca(str, enum.Enum):
    """Quem está chegando ao apartamento ou saindo dele."""
    CHEGADA = "chegada"
    SAIDA = "saida"


class StatusMudanca(str, enum.Enum):
    """O síndico aprova ou recusa; a portaria só deixa entrar a aprovada."""
    PENDENTE = "pendente"
    APROVADA = "aprovada"
    RECUSADA = "recusada"
    CANCELADA = "cancelada"
    CONCLUIDA = "concluida"


class CategoriaDocumento(str, enum.Enum):
    """Documentação, seção 13.6: atas, convenção e regimento interno."""
    CONVENCAO = "convencao"
    REGIMENTO = "regimento"
    ATA = "ata"
    PLANTA = "planta"
    PRESTACAO_CONTAS = "prestacao_contas"
    OUTRO = "outro"

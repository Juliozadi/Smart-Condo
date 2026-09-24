"""Schemas de cadastro, login e recuperação de senha.

Documentação, seção 12 — casos de uso "Cadastro", "Login do usuário",
"Esqueci minha senha" e "Permissão do Porteiro".
"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import EmailStr, Field, model_validator

from app.models.enums import (
    CanalVerificacao, Papel, StatusUsuario, TipoOcupacao,
)
from app.schemas.comuns import CPF, DataNascimento, SchemaBase, Senha, Telefone


# ── Cadastro (seção 12) ───────────────────────────────────────────────
class CadastroBase(SchemaBase):
    nome: str = Field(min_length=3, max_length=160)
    email: EmailStr
    cpf: CPF
    telefone: Telefone
    data_nascimento: DataNascimento | None = None
    senha: Senha
    # "o sistema salva e envia um código de confirmação pelo meio escolhido"
    canal_confirmacao: CanalVerificacao = CanalVerificacao.EMAIL


class CadastroSindico(CadastroBase):
    """O síndico se cadastra sozinho e depois cadastra o condomínio."""


class CadastroMorador(CadastroBase):
    """Seção 11.3: o morador informa o condomínio, o bloco/torre, as vagas
    de garagem e o vínculo dele com o estabelecimento."""

    # O morador informa o código que recebeu do síndico, não o id.
    codigo_condominio: str = Field(min_length=4, max_length=20)
    unidade_numero: str = Field(min_length=1, max_length=20)
    unidade_bloco: str = Field(default="unico", max_length=20)
    tipo_ocupacao: TipoOcupacao


class CadastroPorteiro(CadastroBase):
    """Seção 11.2: o cadastro do porteiro leva os dados pessoais e, por fim,
    as permissões de uso no sistema. Quem cadastra é o síndico."""

    condominio_id: int
    permissoes: "PermissoesPorteiroEntrada | None" = None


# ── Confirmação do cadastro ──────────────────────────────────────────
class ConfirmacaoCodigo(SchemaBase):
    email: EmailStr
    codigo: str = Field(min_length=4, max_length=8)


class ReenvioCodigo(SchemaBase):
    email: EmailStr
    canal: CanalVerificacao = CanalVerificacao.EMAIL


# ── Login (seção 12) ──────────────────────────────────────────────────
class LoginEntrada(SchemaBase):
    email: EmailStr
    senha: str = Field(min_length=1, max_length=72)


class TokenSaida(SchemaBase):
    access_token: str
    token_type: str = "bearer"
    expira_em_min: int
    usuario: "UsuarioSaida"


class SenhaTrocadaSaida(SchemaBase):
    detalhe: str
    access_token: str
    expira_em_min: int


# ── Esqueci minha senha (seção 12) ────────────────────────────────────
class SolicitacaoRecuperacao(SchemaBase):
    email: EmailStr
    canal: CanalVerificacao = CanalVerificacao.EMAIL


class RedefinicaoSenha(SchemaBase):
    email: EmailStr
    codigo: str = Field(min_length=4, max_length=8)
    nova_senha: Senha
    confirmacao_senha: str

    @model_validator(mode="after")
    def conferir_confirmacao(self) -> "RedefinicaoSenha":
        if self.nova_senha != self.confirmacao_senha:
            raise ValueError("A confirmação não confere com a nova senha.")
        return self


class TrocaSenha(SchemaBase):
    senha_atual: str = Field(min_length=1, max_length=72)
    nova_senha: Senha


# ── Permissões do porteiro (seção 12) ─────────────────────────────────
class PermissoesPorteiroEntrada(SchemaBase):
    registrar_visitantes: bool = True
    registrar_encomendas: bool = True
    registrar_veiculos: bool = True
    registrar_ocorrencias: bool = True
    acessar_financeiro: bool = False


class PermissoesPorteiroSaida(PermissoesPorteiroEntrada):
    porteiro_id: int


# ── Saída ────────────────────────────────────────────────────────────
class UnidadeResumo(SchemaBase):
    id: int
    numero: str
    bloco: str
    andar: int | None = None
    vagas_garagem: int


class UsuarioSaida(SchemaBase):
    id: int
    nome: str
    email: EmailStr
    telefone: str
    papel: Papel
    status: StatusUsuario
    condominio_id: int | None = None
    unidade: UnidadeResumo | None = None
    tipo_ocupacao: TipoOcupacao | None = None
    foto_url: str | None = None
    criado_em: datetime

    # Quem avaliou o cadastro, quando e — na recusa — por quê. O síndico
    # e o administrador precisam disso na fila de aprovação; o próprio
    # usuário recusado precisa saber o motivo.
    avaliado_em: datetime | None = None
    motivo_recusa: str | None = None


class PerfilSaida(UsuarioSaida):
    """O que o usuário vê do próprio cadastro.

    Traz CPF e data de nascimento, que ficam de fora de UsuarioSaida
    justamente para não aparecerem nas listagens que o síndico e o
    administrador enxergam.
    """
    cpf: str
    data_nascimento: DataNascimento | None = None


class UsuarioAtualizacao(SchemaBase):
    nome: str | None = Field(default=None, min_length=3, max_length=160)
    telefone: Telefone | None = None
    data_nascimento: DataNascimento | None = None
    # A foto não entra aqui: ela só muda pelo envio do arquivo
    # (PUT /usuarios/eu/foto). Aceitar um endereço livre deixava qualquer
    # usuário apontar a própria foto para um servidor de terceiros, que
    # passaria a ver quem abre a tela.


class AprovacaoUsuario(SchemaBase):
    """O síndico aprova ou recusa o cadastro (telas de aguardando aprovação)."""
    aprovado: bool
    motivo: str | None = Field(default=None, max_length=300)


class CadastroSaida(SchemaBase):
    """Resposta do cadastro: o usuário criado e para onde o código foi."""
    usuario: UsuarioSaida
    codigo_enviado_para: str
    canal: CanalVerificacao
    expira_em_min: int
    # Só preenchido quando DEBUG está ligado, para testar sem e-mail/SMS real.
    codigo_debug: str | None = None
    # Só no cadastro feito pelo próprio morador: autoriza apenas o envio
    # dos documentos (PUT /auth/cadastro/documentos/{tipo}) e não abre
    # sessão. Quem o síndico cadastra por dentro não envia documentos.
    token_documentos: str | None = None
    token_documentos_expira_min: int | None = None


CadastroPorteiro.model_rebuild()
TokenSaida.model_rebuild()


class CanaisSaida(SchemaBase):
    """Por onde o código pode ser enviado neste servidor."""
    email: bool
    sms: bool

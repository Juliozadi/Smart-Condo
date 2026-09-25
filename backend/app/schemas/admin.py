"""Schemas do painel do administrador.

O administrador opera a plataforma: cadastra os condomínios e, dentro de
cada um, cria, edita e inativa síndicos, porteiros e moradores — e cadastra
outros administradores. Cada alteração guarda quem a fez.
"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import EmailStr, Field

from app.models.enums import Papel, StatusUsuario, TipoOcupacao
from app.schemas.comuns import CPF, DataNascimento, SchemaBase, Senha, Telefone


class UsuarioAdminEntrada(SchemaBase):
    """Criação de um usuário pelo administrador ou pelo síndico.

    Quem é criado por dentro do sistema já nasce ativo: não faz sentido
    pedir confirmação por código nem aprovação de quem acabou de ser
    cadastrado por um responsável.
    """
    nome: str = Field(min_length=3, max_length=160)
    email: EmailStr
    cpf: CPF
    telefone: Telefone
    senha: Senha
    data_nascimento: DataNascimento | None = None
    papel: Papel

    # Só para morador.
    unidade_numero: str | None = Field(default=None, max_length=20)
    unidade_bloco: str = Field(default="unico", max_length=20)
    tipo_ocupacao: TipoOcupacao | None = None


class AdministradorEntrada(SchemaBase):
    """Um administrador cadastra outro. Administrador não pertence a
    condomínio nenhum: atravessa todos."""
    nome: str = Field(min_length=3, max_length=160)
    email: EmailStr
    cpf: CPF
    telefone: Telefone
    senha: Senha
    data_nascimento: DataNascimento | None = None


class RegistroSaida(SchemaBase):
    """Uma linha do histórico: "Editado por Fulano em 25/09 14:32"."""
    acao: str
    rotulo: str
    autor_nome: str | None = None
    feito_em: datetime
    descricao: str | None = None


class UsuarioAdminAtualizacao(SchemaBase):
    nome: str | None = Field(default=None, min_length=3, max_length=160)
    email: EmailStr | None = None
    telefone: Telefone | None = None
    data_nascimento: DataNascimento | None = None
    status: StatusUsuario | None = None
    senha: Senha | None = Field(default=None, description="Só envie para trocar a senha.")

    unidade_numero: str | None = Field(default=None, max_length=20)
    unidade_bloco: str | None = Field(default=None, max_length=20)
    tipo_ocupacao: TipoOcupacao | None = None


class UsuarioAdminSaida(SchemaBase):
    id: int
    nome: str
    email: EmailStr
    cpf: str
    telefone: str
    papel: Papel
    status: StatusUsuario
    condominio_id: int | None = None
    condominio_nome: str | None = None
    unidade: str | None = None
    tipo_ocupacao: TipoOcupacao | None = None
    criado_em: datetime
    criado_por: str | None = None
    ultima_alteracao: RegistroSaida | None = None


class CondominioAdminSaida(SchemaBase):
    id: int
    nome: str
    cnpj: str
    codigo_acesso: str
    # O endereço completo vai junto porque é o administrador quem edita o
    # condomínio: sem estes campos o formulário de edição abriria vazio.
    cep: str
    logradouro: str
    numero: str
    bairro: str
    cidade: str
    uf: str
    telefone: str | None = None
    sindico_id: int | None = None
    sindico_nome: str | None = None
    total_unidades: int
    total_moradores: int
    total_porteiros: int
    criado_em: datetime
    inativo: bool = False
    inativo_em: datetime | None = None
    criado_por: str | None = None
    ultima_alteracao: RegistroSaida | None = None


class ResumoPlataforma(SchemaBase):
    """Indicadores do painel do administrador."""
    condominios: int
    sindicos: int
    porteiros: int
    moradores: int
    aguardando_aprovacao: int

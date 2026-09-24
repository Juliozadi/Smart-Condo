"""Criação e edição de usuários por quem é responsável por eles.

Duas portas levam aqui: o administrador, que mexe em qualquer condomínio,
e o síndico, que mexe apenas no próprio. A regra de negócio é a mesma, por
isso fica num lugar só.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import gerar_hash_senha
from app.models.condominio import Condominio, Unidade
from app.models.enums import Papel, StatusUsuario
from app.models.usuario import PermissaoPorteiro, Usuario
from app.services import auth as servico_auth


def obter_ou_criar_unidade(
    db: Session, condominio_id: int, numero: str, bloco: str = "unico"
) -> Unidade:
    unidade = db.scalar(
        select(Unidade).where(
            Unidade.condominio_id == condominio_id,
            Unidade.numero == numero,
            Unidade.bloco == bloco,
        )
    )
    if unidade is None:
        unidade = Unidade(condominio_id=condominio_id, numero=numero, bloco=bloco)
        db.add(unidade)
        db.flush()
    return unidade


def criar_usuario(
    db: Session,
    condominio: Condominio | None,
    dados,
    criado_por: Usuario,
) -> Usuario:
    """Cria um usuário já ativo.

    Quem é cadastrado por um responsável não passa por código de
    confirmação nem por aprovação — o responsável é a aprovação.
    """
    if dados.papel == Papel.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administradores não são criados por aqui.",
        )
    if dados.papel != Papel.MORADOR and (dados.unidade_numero or dados.tipo_ocupacao):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unidade e tipo de ocupação são só para morador.",
        )
    if dados.papel == Papel.MORADOR and not dados.unidade_numero:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe a unidade do morador.",
        )
    if condominio is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe o condomínio do usuário.",
        )

    servico_auth.garantir_email_e_cpf_livres(db, dados.email, dados.cpf)

    # Um condomínio tem um síndico responsável de cada vez.
    if dados.papel == Papel.SINDICO:
        atual = db.scalar(
            select(Usuario).where(
                Usuario.condominio_id == condominio.id,
                Usuario.papel == Papel.SINDICO,
                Usuario.status != StatusUsuario.INATIVO,
            )
        )
        if atual is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"{condominio.nome} já tem um síndico ativo ({atual.nome}). "
                    "Inative o atual antes de cadastrar outro."
                ),
            )

    unidade = None
    if dados.papel == Papel.MORADOR:
        unidade = obter_ou_criar_unidade(
            db, condominio.id, dados.unidade_numero, dados.unidade_bloco
        )

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email.lower(),
        cpf=dados.cpf,
        telefone=dados.telefone,
        data_nascimento=dados.data_nascimento,
        senha_hash=gerar_hash_senha(dados.senha),
        papel=dados.papel,
        status=StatusUsuario.ATIVO,
        condominio_id=condominio.id,
        unidade_id=unidade.id if unidade else None,
        tipo_ocupacao=dados.tipo_ocupacao if dados.papel == Papel.MORADOR else None,
    )
    db.add(usuario)
    db.flush()

    if dados.papel == Papel.PORTEIRO:
        db.add(PermissaoPorteiro(porteiro_id=usuario.id, definidas_por_id=criado_por.id))

    if dados.papel == Papel.SINDICO and condominio.sindico_id is None:
        condominio.sindico_id = usuario.id

    return usuario


def atualizar_usuario(db: Session, usuario: Usuario, dados) -> Usuario:
    campos = dados.model_dump(exclude_unset=True)

    novo_email = campos.pop("email", None)
    if novo_email and novo_email.lower() != usuario.email:
        if servico_auth.buscar_por_email(db, novo_email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um cadastro com este e-mail.",
            )
        usuario.email = novo_email.lower()

    nova_senha = campos.pop("senha", None)
    if nova_senha:
        usuario.senha_hash = gerar_hash_senha(nova_senha)

    numero = campos.pop("unidade_numero", None)
    bloco = campos.pop("unidade_bloco", None)
    if numero or bloco:
        if usuario.papel != Papel.MORADOR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Só morador tem unidade.",
            )
        atual = db.get(Unidade, usuario.unidade_id) if usuario.unidade_id else None
        unidade = obter_ou_criar_unidade(
            db,
            usuario.condominio_id,
            numero or (atual.numero if atual else ""),
            bloco or (atual.bloco if atual else "unico"),
        )
        usuario.unidade_id = unidade.id

    if campos.get("tipo_ocupacao") and usuario.papel != Papel.MORADOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de ocupação é só para morador.",
        )

    # Inativar pela edição tem o mesmo efeito de remover (remover_usuario).
    if campos.get("status") == StatusUsuario.INATIVO:
        _soltar_do_condominio_se_sindico(db, usuario)

    for campo, valor in campos.items():
        setattr(usuario, campo, valor)

    db.flush()
    return usuario


def _soltar_do_condominio_se_sindico(db: Session, usuario: Usuario) -> None:
    """O condomínio não pode ficar apontando para um síndico inativo."""
    if usuario.papel == Papel.SINDICO and usuario.condominio_id:
        condominio = db.get(Condominio, usuario.condominio_id)
        if condominio is not None and condominio.sindico_id == usuario.id:
            condominio.sindico_id = None


def remover_usuario(db: Session, usuario: Usuario, quem_remove: Usuario) -> None:
    """Inativa em vez de apagar.

    O histórico de portaria, reservas e financeiro aponta para o usuário;
    apagar a linha levaria junto registros que precisam continuar existindo.
    """
    if usuario.id == quem_remove.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode remover o próprio usuário.",
        )

    _soltar_do_condominio_se_sindico(db, usuario)
    usuario.status = StatusUsuario.INATIVO
    db.flush()

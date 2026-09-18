"""Regras de cadastro, confirmação, login e recuperação de senha.

Documentação, seção 9 — casos de uso "Cadastro", "Login do usuário" e
"Esqueci minha senha".
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    conferir_codigo, conferir_senha, gerar_codigo_verificacao, gerar_hash_codigo,
    gerar_hash_senha,
)
from app.models.enums import CanalVerificacao, FinalidadeCodigo, Papel, StatusUsuario
from app.models.usuario import CodigoVerificacao, Usuario
from app.services import notificacao

MAX_TENTATIVAS_CODIGO = 5


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def buscar_por_email(db: Session, email: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(Usuario.email == email.lower()))


def buscar_por_cpf(db: Session, cpf: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(Usuario.cpf == cpf))


def garantir_email_e_cpf_livres(db: Session, email: str, cpf: str) -> None:
    if buscar_por_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um cadastro com este e-mail.",
        )
    if buscar_por_cpf(db, cpf):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um cadastro com este CPF.",
        )


def emitir_codigo(
    db: Session,
    usuario: Usuario,
    finalidade: FinalidadeCodigo,
    canal: CanalVerificacao,
) -> str:
    """Gera, guarda (em hash) e envia um novo código.

    Qualquer código pendente da mesma finalidade é invalidado, para que só o
    mais recente valha.
    """
    pendentes = db.scalars(
        select(CodigoVerificacao).where(
            CodigoVerificacao.usuario_id == usuario.id,
            CodigoVerificacao.finalidade == finalidade,
            CodigoVerificacao.consumido_em.is_(None),
        )
    ).all()
    for pendente in pendentes:
        pendente.consumido_em = _agora()

    destino = usuario.email if canal == CanalVerificacao.EMAIL else usuario.telefone
    codigo = gerar_codigo_verificacao()

    registro = CodigoVerificacao(
        usuario_id=usuario.id,
        codigo_hash=gerar_hash_codigo(codigo),
        finalidade=finalidade,
        canal=canal,
        expira_em=_agora() + timedelta(minutes=settings.CODIGO_VERIFICACAO_EXPIRA_MIN),
        destino=destino,
    )
    db.add(registro)
    db.flush()

    notificacao.enviar_codigo(destino, canal, codigo, finalidade.value)
    return codigo


def validar_codigo(
    db: Session,
    usuario: Usuario,
    codigo_informado: str,
    finalidade: FinalidadeCodigo,
) -> CodigoVerificacao:
    """Confere o código e o marca como consumido. Erra alto se não servir."""
    registro = db.scalar(
        select(CodigoVerificacao)
        .where(
            CodigoVerificacao.usuario_id == usuario.id,
            CodigoVerificacao.finalidade == finalidade,
            CodigoVerificacao.consumido_em.is_(None),
        )
        .order_by(CodigoVerificacao.id.desc())
    )
    if registro is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não há código pendente. Solicite um novo.",
        )

    expira_em = registro.expira_em
    if expira_em.tzinfo is None:
        expira_em = expira_em.replace(tzinfo=timezone.utc)
    if expira_em < _agora():
        registro.consumido_em = _agora()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O código expirou. Solicite um novo.",
        )

    if registro.tentativas >= MAX_TENTATIVAS_CODIGO:
        registro.consumido_em = _agora()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas. Solicite um novo código.",
        )

    if not conferir_codigo(codigo_informado, registro.codigo_hash):
        registro.tentativas += 1
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código incorreto.",
        )

    registro.consumido_em = _agora()
    return registro


def status_apos_confirmacao(papel: Papel) -> StatusUsuario:
    """Depois de confirmar o código, o cadastro ainda espera o síndico.

    Só o morador se cadastra sozinho, e a tela "aguardando aprovação" do
    front-end existe para esse intervalo. Quem é criado por dentro do
    sistema (pelo administrador ou pelo síndico) já nasce ativo e nem passa
    por aqui.
    """
    return StatusUsuario.AGUARDANDO_APROVACAO


def autenticar(db: Session, email: str, senha: str) -> Usuario:
    """Valida as credenciais do login (seção 9)."""
    usuario = buscar_por_email(db, email)

    # A mensagem é a mesma para e-mail inexistente e senha errada, para não
    # revelar quais e-mails estão cadastrados.
    if usuario is None or not conferir_senha(senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
        )
    return usuario


def trocar_senha(db: Session, usuario: Usuario, senha_atual: str, nova_senha: str) -> None:
    if not conferir_senha(senha_atual, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha atual está incorreta.",
        )
    usuario.senha_hash = gerar_hash_senha(nova_senha)
    db.flush()

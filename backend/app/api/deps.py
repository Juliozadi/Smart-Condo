"""Dependências do FastAPI: sessão, usuário autenticado e controle de acesso."""
from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import ler_token_acesso
from app.models.enums import Papel, StatusUsuario
from app.models.usuario import PermissaoPorteiro, Usuario

esquema_bearer = HTTPBearer(auto_error=False, description="Token JWT obtido no login.")

CREDENCIAL_INVALIDA = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciais inválidas ou expiradas.",
    headers={"WWW-Authenticate": "Bearer"},
)

SESSAO_ENCERRADA = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="A senha desta conta foi alterada. Entre de novo.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_usuario_atual(
    credencial: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    if credencial is None:
        raise CREDENCIAL_INVALIDA

    payload = ler_token_acesso(credencial.credentials)
    if not payload or not payload.get("sub"):
        raise CREDENCIAL_INVALIDA

    try:
        usuario_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise CREDENCIAL_INVALIDA

    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise CREDENCIAL_INVALIDA

    # A senha foi trocada ou redefinida depois que este token saiu: a
    # sessão é encerrada, inclusive a de quem tivesse roubado o token.
    # Token de antes desta regra não tem "sv" e vale como versão 0.
    if payload.get("sv", 0) != usuario.versao_sessao:
        raise SESSAO_ENCERRADA

    if usuario.status != StatusUsuario.ATIVO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_motivo_inativo(usuario.status),
        )
    return usuario


def _motivo_inativo(status_usuario: StatusUsuario) -> str:
    return {
        StatusUsuario.AGUARDANDO_CODIGO: "Confirme o código enviado para ativar o cadastro.",
        StatusUsuario.AGUARDANDO_APROVACAO: "Seu cadastro aguarda aprovação do síndico.",
        StatusUsuario.RECUSADO: "Seu cadastro foi recusado pelo síndico.",
        StatusUsuario.INATIVO: "Este cadastro está inativo.",
    }.get(status_usuario, "Cadastro indisponível.")


def exigir_papel(*papeis: Papel) -> Callable[[Usuario], Usuario]:
    """Restringe a rota aos papéis informados (documentação, seção 8)."""

    def verificar(usuario: Usuario = Depends(get_usuario_atual)) -> Usuario:
        if usuario.papel not in papeis:
            permitidos = ", ".join(p.value for p in papeis)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Esta ação é permitida apenas para: {permitidos}.",
            )
        return usuario

    return verificar


def exigir_permissao_porteiro(nome_permissao: str) -> Callable[..., Usuario]:
    """Aplica as permissões que o síndico definiu para o porteiro.

    Documentação, seção 12 — "Permissão do Porteiro": o síndico escolhe
    quais ações ficam disponíveis. O síndico passa direto; o morador nunca.
    """

    def verificar(
        usuario: Usuario = Depends(get_usuario_atual),
        db: Session = Depends(get_db),
    ) -> Usuario:
        if usuario.papel == Papel.SINDICO:
            return usuario
        if usuario.papel != Papel.PORTEIRO:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Esta ação é permitida apenas para síndico e porteiro.",
            )

        exigir_permissao_do_porteiro(db, usuario, nome_permissao)
        return usuario

    return verificar


def porteiro_tem_permissao(db: Session, porteiro: Usuario, nome_permissao: str) -> bool:
    permissoes = (
        db.query(PermissaoPorteiro)
        .filter(PermissaoPorteiro.porteiro_id == porteiro.id)
        .one_or_none()
    )
    # Sem registro de permissões, o porteiro não recebe acesso implícito.
    return permissoes is not None and bool(getattr(permissoes, nome_permissao, False))


def exigir_permissao_do_porteiro(db: Session, usuario: Usuario, nome_permissao: str) -> None:
    """Para rotas abertas a vários papéis: se quem chama é porteiro, ele
    precisa da permissão. Vale também para consultar — a Política de
    Privacidade promete que o porteiro só vê o que o síndico liberou."""
    if usuario.papel == Papel.PORTEIRO and not porteiro_tem_permissao(db, usuario, nome_permissao):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O síndico não liberou esta ação para o seu usuário.",
        )


def exigir_condominio(usuario: Usuario = Depends(get_usuario_atual)) -> Usuario:
    """Garante que o usuário já está vinculado a um condomínio."""
    if usuario.condominio_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seu usuário ainda não está vinculado a um condomínio.",
        )
    return usuario

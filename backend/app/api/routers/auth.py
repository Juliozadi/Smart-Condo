"""Cadastro, login e recuperação de senha.

Documentação, seção 9 — casos de uso "Cadastro", "Login do usuário" e
"Esqueci minha senha".

Quem se cadastra sozinho é apenas o morador, e ainda assim depende da
aprovação do síndico. Síndico, porteiro e demais moradores são criados por
dentro do sistema: o administrador cadastra os síndicos (app/api/routers/
admin.py) e o síndico cadastra porteiros e moradores do seu condomínio
(app/api/routers/usuarios.py).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_usuario_atual
from app.core.config import settings
from app.core.database import get_db
from app.core.security import criar_token_acesso, gerar_hash_senha
from app.models.condominio import Condominio, Unidade
from app.models.enums import CanalVerificacao, FinalidadeCodigo, Papel, StatusUsuario
from app.models.usuario import Usuario
from app.schemas.comuns import Mensagem
from app.schemas.usuario import (
    CadastroMorador, CadastroSaida, ConfirmacaoCodigo, LoginEntrada, PerfilSaida,
    RedefinicaoSenha, ReenvioCodigo, SolicitacaoRecuperacao, TokenSaida, TrocaSenha,
    UsuarioSaida,
)
from app.services import auth as servico_auth
from app.services.notificacao import mascarar_destino

router = APIRouter(prefix="/auth", tags=["Autenticação"])


def _resposta_cadastro(usuario: Usuario, codigo: str, canal: CanalVerificacao) -> CadastroSaida:
    destino = usuario.email if canal == CanalVerificacao.EMAIL else usuario.telefone
    return CadastroSaida(
        usuario=UsuarioSaida.model_validate(usuario),
        codigo_enviado_para=mascarar_destino(destino, canal),
        canal=canal,
        expira_em_min=settings.CODIGO_VERIFICACAO_EXPIRA_MIN,
        # O código só volta na resposta em modo de desenvolvimento, para dar
        # para testar o fluxo sem provedor de e-mail/SMS configurado.
        codigo_debug=codigo if settings.DEBUG else None,
    )


@router.post(
    "/cadastro/morador",
    response_model=CadastroSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um morador",
)
def cadastrar_morador(dados: CadastroMorador, db: Session = Depends(get_db)) -> CadastroSaida:
    servico_auth.garantir_email_e_cpf_livres(db, dados.email, dados.cpf)

    condominio = db.scalar(
        select(Condominio).where(
            Condominio.codigo_acesso == dados.codigo_condominio.strip().upper()
        )
    )
    if condominio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código de acesso não encontrado. Confira com o síndico.",
        )

    # A unidade é criada na primeira vez que alguém se cadastra nela.
    unidade = (
        db.query(Unidade)
        .filter(
            Unidade.condominio_id == condominio.id,
            Unidade.numero == dados.unidade_numero,
            Unidade.bloco == dados.unidade_bloco,
        )
        .one_or_none()
    )
    if unidade is None:
        unidade = Unidade(
            condominio_id=condominio.id,
            numero=dados.unidade_numero,
            bloco=dados.unidade_bloco,
        )
        db.add(unidade)
        db.flush()

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email.lower(),
        cpf=dados.cpf,
        telefone=dados.telefone,
        data_nascimento=dados.data_nascimento,
        senha_hash=gerar_hash_senha(dados.senha),
        papel=Papel.MORADOR,
        status=StatusUsuario.AGUARDANDO_CODIGO,
        condominio_id=condominio.id,
        unidade_id=unidade.id,
        tipo_ocupacao=dados.tipo_ocupacao,
    )
    db.add(usuario)
    db.flush()

    codigo = servico_auth.emitir_codigo(
        db, usuario, FinalidadeCodigo.CONFIRMACAO_CADASTRO, dados.canal_confirmacao
    )
    db.commit()
    db.refresh(usuario)
    return _resposta_cadastro(usuario, codigo, dados.canal_confirmacao)


@router.post(
    "/confirmar",
    response_model=UsuarioSaida,
    summary="Confirma o cadastro com o código recebido",
)
def confirmar_cadastro(dados: ConfirmacaoCodigo, db: Session = Depends(get_db)) -> Usuario:
    usuario = servico_auth.buscar_por_email(db, dados.email)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cadastro não encontrado."
        )
    if usuario.status != StatusUsuario.AGUARDANDO_CODIGO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Este cadastro já foi confirmado."
        )

    servico_auth.validar_codigo(db, usuario, dados.codigo, FinalidadeCodigo.CONFIRMACAO_CADASTRO)
    usuario.status = servico_auth.status_apos_confirmacao(usuario.papel)

    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/codigo/reenviar", response_model=Mensagem, summary="Reenvia o código de cadastro")
def reenviar_codigo(dados: ReenvioCodigo, db: Session = Depends(get_db)) -> Mensagem:
    usuario = servico_auth.buscar_por_email(db, dados.email)
    if usuario is not None and usuario.status == StatusUsuario.AGUARDANDO_CODIGO:
        servico_auth.emitir_codigo(
            db, usuario, FinalidadeCodigo.CONFIRMACAO_CADASTRO, dados.canal
        )
        db.commit()

    # Resposta igual em qualquer caso, para não revelar quem está cadastrado.
    return Mensagem(detalhe="Se houver um cadastro pendente, um novo código foi enviado.")


@router.post("/login", response_model=TokenSaida, summary="Efetua a sessão do usuário")
def login(dados: LoginEntrada, db: Session = Depends(get_db)) -> TokenSaida:
    usuario = servico_auth.autenticar(db, dados.email, dados.senha)

    if usuario.status == StatusUsuario.AGUARDANDO_CODIGO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Confirme o código enviado para ativar o cadastro.",
        )
    if usuario.status == StatusUsuario.AGUARDANDO_APROVACAO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu cadastro aguarda aprovação do síndico.",
        )
    if usuario.status != StatusUsuario.ATIVO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Este cadastro está indisponível."
        )

    return TokenSaida(
        access_token=criar_token_acesso(str(usuario.id), usuario.papel.value),
        expira_em_min=settings.ACCESS_TOKEN_EXPIRA_MIN,
        usuario=UsuarioSaida.model_validate(usuario),
    )


@router.post(
    "/senha/recuperar",
    response_model=Mensagem,
    summary="Solicita o código de recuperação de senha",
)
def solicitar_recuperacao(
    dados: SolicitacaoRecuperacao, db: Session = Depends(get_db)
) -> Mensagem:
    usuario = servico_auth.buscar_por_email(db, dados.email)
    if usuario is not None:
        servico_auth.emitir_codigo(
            db, usuario, FinalidadeCodigo.RECUPERACAO_SENHA, dados.canal
        )
        db.commit()

    return Mensagem(detalhe="Se o e-mail estiver cadastrado, um código foi enviado.")


@router.post("/senha/redefinir", response_model=Mensagem, summary="Redefine a senha com o código")
def redefinir_senha(dados: RedefinicaoSenha, db: Session = Depends(get_db)) -> Mensagem:
    usuario = servico_auth.buscar_por_email(db, dados.email)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Não há código pendente. Solicite um novo."
        )

    servico_auth.validar_codigo(db, usuario, dados.codigo, FinalidadeCodigo.RECUPERACAO_SENHA)
    usuario.senha_hash = gerar_hash_senha(dados.nova_senha)

    db.commit()
    return Mensagem(detalhe="Senha redefinida. Faça o login com a nova senha.")


@router.get("/eu", response_model=PerfilSaida, summary="Dados do usuário autenticado")
def usuario_autenticado(usuario: Usuario = Depends(get_usuario_atual)) -> Usuario:
    return usuario


@router.post("/senha/trocar", response_model=Mensagem, summary="Troca a senha estando logado")
def trocar_senha(
    dados: TrocaSenha,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
) -> Mensagem:
    servico_auth.trocar_senha(db, usuario, dados.senha_atual, dados.nova_senha)
    db.commit()
    return Mensagem(detalhe="Senha alterada.")

"""Cadastro, login e recuperação de senha.

Documentação, seção 12 — casos de uso "Cadastro", "Login do usuário" e
"Esqueci minha senha".

Quem se cadastra sozinho é apenas o morador, e ainda assim depende da
aprovação do síndico. Síndico, porteiro e demais moradores são criados por
dentro do sistema: o administrador cadastra os síndicos (app/api/routers/
admin.py) e o síndico cadastra porteiros e moradores do seu condomínio
(app/api/routers/usuarios.py).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import esquema_bearer, get_usuario_atual
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    criar_token_acesso, criar_token_documentos, gerar_hash_senha, ler_token_documentos,
)
from app.models.condominio import Condominio, Unidade
from app.models.enums import (
    CanalVerificacao, FinalidadeCodigo, Papel, StatusUsuario, TipoDocumentoCadastro,
)
from app.models.usuario import Usuario
from app.schemas.comuns import Mensagem
from app.schemas.documento_cadastro import DocumentoCadastroSaida
from app.schemas.usuario import (
    CanaisSaida,
    CadastroMorador, CadastroSaida, ConfirmacaoCodigo, LoginEntrada, PerfilSaida,
    RedefinicaoSenha, ReenvioCodigo, SenhaTrocadaSaida, SolicitacaoRecuperacao, TokenSaida,
    TrocaSenha,
    UsuarioSaida,
)
from app.services import arquivos
from app.services import auth as servico_auth
from app.services import documentos_cadastro
from app.services.notificacao import mascarar_destino

router = APIRouter(prefix="/auth", tags=["Autenticação"])


def _exigir_canal(canal: CanalVerificacao) -> None:
    """Recusa SMS quando não há provedor, em vez de gerar um código que
    nunca chegaria. E-mail é sempre aceito: sem SMTP, em desenvolvimento
    o código volta na resposta."""
    if canal == CanalVerificacao.SMS and not settings.sms_configurado:
        raise HTTPException(
            status_code=422,
            detail="O envio por SMS não está disponível. Escolha receber o código por e-mail.",
        )


@router.get("/canais", response_model=CanaisSaida, summary="Canais disponíveis para o código")
def canais() -> CanaisSaida:
    """A tela só oferece SMS quando ele funciona de verdade."""
    return CanaisSaida(email=True, sms=settings.sms_configurado)


def _resposta_cadastro(usuario: Usuario, codigo: str, canal: CanalVerificacao) -> CadastroSaida:
    """Resposta do cadastro público, que é sempre o de um morador."""
    destino = usuario.email if canal == CanalVerificacao.EMAIL else usuario.telefone
    return CadastroSaida(
        usuario=UsuarioSaida.model_validate(usuario),
        codigo_enviado_para=mascarar_destino(destino, canal),
        canal=canal,
        expira_em_min=settings.CODIGO_VERIFICACAO_EXPIRA_MIN,
        # O código só volta na resposta em modo de desenvolvimento, para dar
        # para testar o fluxo sem provedor de e-mail/SMS configurado.
        codigo_debug=codigo if settings.DEBUG else None,
        token_documentos=criar_token_documentos(usuario.id),
        token_documentos_expira_min=settings.TOKEN_DOCUMENTOS_MIN,
    )


@router.post(
    "/cadastro/morador",
    response_model=CadastroSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um morador",
)
def cadastrar_morador(dados: CadastroMorador, db: Session = Depends(get_db)) -> CadastroSaida:
    _exigir_canal(dados.canal_confirmacao)
    servico_auth.garantir_email_e_cpf_livres(db, dados.email, dados.cpf)

    condominio = db.scalar(
        select(Condominio).where(
            Condominio.codigo_acesso == dados.codigo_condominio.strip().upper(),
            # Condomínio inativado não recebe cadastro novo.
            Condominio.inativo_em.is_(None),
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


def _cadastro_do_token(
    credencial: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    """O cadastro autorizado pelo token_documentos, enquanto ainda não foi avaliado."""
    usuario_id = ler_token_documentos(credencial.credentials) if credencial else None
    usuario = db.get(Usuario, usuario_id) if usuario_id else None
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A autorização para enviar documentos é inválida ou expirou.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Depois que o síndico decidiu, os documentos não mudam mais.
    if usuario.status not in (StatusUsuario.AGUARDANDO_CODIGO, StatusUsuario.AGUARDANDO_APROVACAO):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este cadastro já foi avaliado; os documentos não podem mais ser trocados.",
        )
    return usuario


@router.put(
    "/cadastro/documentos/{tipo}",
    response_model=list[DocumentoCadastroSaida],
    summary="Envia um documento do cadastro do morador",
)
def enviar_documento_cadastro(
    tipo: TipoDocumentoCadastro,
    arquivo: UploadFile = File(..., description="PDF ou imagem JPG, PNG ou WebP"),
    usuario: Usuario = Depends(_cadastro_do_token),
    db: Session = Depends(get_db),
) -> list[DocumentoCadastroSaida]:
    """Usa o token_documentos devolvido pelo cadastro, não o de sessão.

    Devolve todos os documentos já enviados, para a tela conferir o que
    falta.
    """
    conteudo = arquivo.file.read(settings.DOCUMENTO_MAX_KB * 1024 + 1)
    try:
        documentos_cadastro.salvar(db, usuario, tipo, conteudo)
    except arquivos.ArquivoRecusado as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro
    return [documentos_cadastro.saida(d) for d in documentos_cadastro.listar(db, usuario.id)]


@router.put(
    "/cadastro/foto",
    response_model=Mensagem,
    summary="Envia a foto de perfil escolhida no cadastro do morador",
)
def enviar_foto_cadastro(
    arquivo: UploadFile = File(..., description="Imagem JPG, PNG ou WebP"),
    usuario: Usuario = Depends(_cadastro_do_token),
    db: Session = Depends(get_db),
) -> Mensagem:
    """Mesma autorização dos documentos. Depois de aprovado, o morador
    troca a foto pelo perfil (PUT /usuarios/eu/foto)."""
    conteudo = arquivo.file.read(settings.FOTO_MAX_KB * 1024 + 1)
    try:
        nova = arquivos.salvar_foto(conteudo)
    except arquivos.ArquivoRecusado as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro
    anterior = usuario.foto_url
    usuario.foto_url = nova
    db.commit()
    arquivos.apagar_foto(anterior)
    return Mensagem(detalhe="Foto recebida.")


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
    _exigir_canal(dados.canal)
    usuario = servico_auth.buscar_por_email(db, dados.email)
    if usuario is not None and usuario.status == StatusUsuario.AGUARDANDO_CODIGO:
        try:
            servico_auth.emitir_codigo(
                db, usuario, FinalidadeCodigo.CONFIRMACAO_CADASTRO, dados.canal
            )
            db.commit()
        except servico_auth.CodigoMuitoFrequente:
            # Mesma resposta: um aviso diferente revelaria que o e-mail
            # existe. A tela já espera o intervalo antes de reenviar.
            db.rollback()

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
        access_token=criar_token_acesso(str(usuario.id), usuario.papel.value, usuario.versao_sessao),
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
    _exigir_canal(dados.canal)
    usuario = servico_auth.buscar_por_email(db, dados.email)
    if usuario is not None:
        try:
            servico_auth.emitir_codigo(
                db, usuario, FinalidadeCodigo.RECUPERACAO_SENHA, dados.canal
            )
            db.commit()
        except servico_auth.CodigoMuitoFrequente:
            db.rollback()

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
    # Quem recebeu o código provou que é o dono da conta: o bloqueio por
    # senhas erradas (talvez de outra pessoa tentando entrar) sai, e as
    # sessões abertas com a senha antiga são encerradas.
    usuario.tentativas_login = 0
    usuario.bloqueado_ate = None
    servico_auth.encerrar_sessoes(usuario)

    db.commit()
    return Mensagem(detalhe="Senha redefinida. Faça o login com a nova senha.")


@router.get("/eu", response_model=PerfilSaida, summary="Dados do usuário autenticado")
def usuario_autenticado(usuario: Usuario = Depends(get_usuario_atual)) -> Usuario:
    return usuario


@router.post("/senha/trocar", response_model=SenhaTrocadaSaida, summary="Troca a senha estando logado")
def trocar_senha(
    dados: TrocaSenha,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
) -> SenhaTrocadaSaida:
    """As outras sessões são encerradas; esta continua com o token novo
    que vai na resposta."""
    servico_auth.trocar_senha(db, usuario, dados.senha_atual, dados.nova_senha)
    db.commit()
    return SenhaTrocadaSaida(
        detalhe="Senha alterada. As sessões abertas em outros aparelhos foram encerradas.",
        access_token=criar_token_acesso(str(usuario.id), usuario.papel.value, usuario.versao_sessao),
        expira_em_min=settings.ACCESS_TOKEN_EXPIRA_MIN,
    )

"""Gestão de usuários pelo síndico.

Documentação:
  - seção 8: "Síndico: responsável pelo cadastro dos funcionários... 
    administrar os moradores"
  - seção 12, caso de uso "Permissão do Porteiro": "o sistema mostra as
    possibilidades de ações do porteiro" e "o síndico escolhe quais estarão
    disponíveis para o porteiro"
  - seção 13.2: "o cadastro do porteiro deve ser fomentado com dados
    pessoais, e por fim as permissões de uso no sistema"
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import exigir_papel, get_usuario_atual
from app.core.database import get_db
from app.core.security import gerar_hash_senha
from app.models.documento_cadastro import DocumentoCadastro
from app.models.enums import CanalVerificacao, FinalidadeCodigo, Papel, StatusUsuario
from app.models.usuario import PermissaoPorteiro, Usuario
from app.schemas.comuns import Mensagem
from app.schemas.documento_cadastro import DocumentoCadastroSaida
from app.schemas.admin import (
    UsuarioAdminAtualizacao, UsuarioAdminEntrada, UsuarioAdminSaida,
)
from app.schemas.usuario import (
    AprovacaoUsuario, CadastroPorteiro, CadastroSaida, PerfilSaida,
    PermissoesPorteiroEntrada, PermissoesPorteiroSaida, UsuarioAtualizacao, UsuarioSaida,
)
from app.services import arquivos as servico_arquivos
from app.services import documentos_cadastro
from app.services import usuarios as servico_usuarios
from app.services import auth as servico_auth
from app.services import notificacao
from app.services.notificacao import mascarar_destino

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

# As ações que o síndico pode liberar ou bloquear para o porteiro.
ACOES_DO_PORTEIRO = [
    {"chave": "registrar_visitantes", "rotulo": "Registrar visitantes"},
    {"chave": "registrar_encomendas", "rotulo": "Registrar encomendas"},
    {"chave": "registrar_veiculos", "rotulo": "Registrar veículos"},
    {"chave": "registrar_ocorrencias", "rotulo": "Registrar ocorrências"},
    {"chave": "acessar_financeiro", "rotulo": "Acessar o financeiro"},
]


def _buscar_do_meu_condominio(db: Session, sindico: Usuario, usuario_id: int) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None or usuario.condominio_id != sindico.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado."
        )
    return usuario


# ── Cadastro do porteiro (seções 12 e 13.2) ───────────────────────────
@router.post(
    "/porteiros",
    response_model=CadastroSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um porteiro com as permissões de uso",
)
def cadastrar_porteiro(
    dados: CadastroPorteiro,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> CadastroSaida:
    from app.core.config import settings

    if sindico.condominio_id != dados.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode cadastrar porteiros no seu condomínio.",
        )
    servico_auth.garantir_email_e_cpf_livres(db, dados.email, dados.cpf)

    porteiro = Usuario(
        nome=dados.nome,
        email=dados.email.lower(),
        cpf=dados.cpf,
        telefone=dados.telefone,
        data_nascimento=dados.data_nascimento,
        senha_hash=gerar_hash_senha(dados.senha),
        papel=Papel.PORTEIRO,
        status=StatusUsuario.AGUARDANDO_CODIGO,
        condominio_id=dados.condominio_id,
    )
    db.add(porteiro)
    db.flush()

    permissoes = dados.permissoes or PermissoesPorteiroEntrada()
    db.add(
        PermissaoPorteiro(
            porteiro_id=porteiro.id, definidas_por_id=sindico.id, **permissoes.model_dump()
        )
    )

    codigo = servico_auth.emitir_codigo(
        db, porteiro, FinalidadeCodigo.CONFIRMACAO_CADASTRO, dados.canal_confirmacao
    )
    db.commit()
    db.refresh(porteiro)

    canal = dados.canal_confirmacao
    destino = porteiro.email if canal == CanalVerificacao.EMAIL else porteiro.telefone
    return CadastroSaida(
        usuario=UsuarioSaida.model_validate(porteiro),
        codigo_enviado_para=mascarar_destino(destino, canal),
        canal=canal,
        expira_em_min=settings.CODIGO_VERIFICACAO_EXPIRA_MIN,
        codigo_debug=codigo if settings.DEBUG else None,
    )


# ── Permissões (seção 12) ─────────────────────────────────────────────
@router.get(
    "/porteiros/acoes",
    summary="Lista as ações que podem ser liberadas ao porteiro",
)
def listar_acoes_do_porteiro(
    _: Usuario = Depends(exigir_papel(Papel.SINDICO)),
) -> list[dict[str, str]]:
    """"O sistema mostra as possibilidades de ações do porteiro" (seção 12)."""
    return ACOES_DO_PORTEIRO


@router.get(
    "/eu/permissoes",
    response_model=PermissoesPorteiroSaida,
    summary="Permissões do porteiro logado",
)
def minhas_permissoes(
    usuario: Usuario = Depends(exigir_papel(Papel.PORTEIRO)),
    db: Session = Depends(get_db),
) -> PermissoesPorteiroSaida:
    """O porteiro precisa saber o que pode fazer.

    A consulta por id é do síndico, que administra os outros. Sem esta,
    o front-end do porteiro não tinha como saber o que esconder: ele
    exibia o módulo, deixava preencher o formulário e só no envio a API
    recusava com 403, o que parece defeito do sistema.

    Isto é conveniência de tela. Quem decide continua sendo a API, que
    confere a permissão em cada gravação.
    """
    permissoes = db.scalar(
        select(PermissaoPorteiro).where(PermissaoPorteiro.porteiro_id == usuario.id)
    )
    if permissoes is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suas permissões ainda não foram definidas pelo síndico.",
        )
    return PermissoesPorteiroSaida(porteiro_id=usuario.id, **permissoes.como_dicionario())


@router.get(
    "/porteiros/{porteiro_id}/permissoes",
    response_model=PermissoesPorteiroSaida,
    summary="Consulta as permissões de um porteiro",
)
def consultar_permissoes(
    porteiro_id: int,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> PermissoesPorteiroSaida:
    porteiro = _buscar_do_meu_condominio(db, sindico, porteiro_id)
    if porteiro.papel != Papel.PORTEIRO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Este usuário não é porteiro."
        )

    permissoes = db.scalar(
        select(PermissaoPorteiro).where(PermissaoPorteiro.porteiro_id == porteiro.id)
    )
    if permissoes is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Este porteiro ainda não tem permissões definidas.",
        )
    return PermissoesPorteiroSaida(porteiro_id=porteiro.id, **permissoes.como_dicionario())


@router.put(
    "/porteiros/{porteiro_id}/permissoes",
    response_model=PermissoesPorteiroSaida,
    summary="Define as permissões do porteiro",
)
def definir_permissoes(
    porteiro_id: int,
    dados: PermissoesPorteiroEntrada,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> PermissoesPorteiroSaida:
    """"O síndico escolhe quais estarão disponíveis para o porteiro" (seção 12)."""
    porteiro = _buscar_do_meu_condominio(db, sindico, porteiro_id)
    if porteiro.papel != Papel.PORTEIRO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Este usuário não é porteiro."
        )

    permissoes = db.scalar(
        select(PermissaoPorteiro).where(PermissaoPorteiro.porteiro_id == porteiro.id)
    )
    if permissoes is None:
        permissoes = PermissaoPorteiro(porteiro_id=porteiro.id)
        db.add(permissoes)

    for campo, valor in dados.model_dump().items():
        setattr(permissoes, campo, valor)
    permissoes.definidas_por_id = sindico.id

    db.commit()
    db.refresh(permissoes)
    return PermissoesPorteiroSaida(porteiro_id=porteiro.id, **permissoes.como_dicionario())


# ── O síndico cadastra a equipe e os moradores ───────────────────────
@router.post(
    "",
    response_model=UsuarioAdminSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um porteiro ou morador no condomínio",
)
def cadastrar_usuario(
    dados: UsuarioAdminEntrada,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> UsuarioAdminSaida:
    """O síndico cria porteiro e morador do seu condomínio, já ativos.

    Síndico é criado pelo administrador, não por aqui: um síndico não
    nomeia o próprio substituto.
    """
    if sindico.condominio_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seu usuário ainda não está vinculado a um condomínio.",
        )
    if dados.papel not in (Papel.PORTEIRO, Papel.MORADOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você pode cadastrar apenas porteiros e moradores.",
        )

    from app.models.condominio import Condominio

    condominio = db.get(Condominio, sindico.condominio_id)
    usuario = servico_usuarios.criar_usuario(db, condominio, dados, sindico)
    db.commit()
    db.refresh(usuario)
    return _para_saida_admin(db, usuario)


@router.put(
    "/{usuario_id}",
    response_model=UsuarioAdminSaida,
    summary="Edita um porteiro ou morador do condomínio",
)
def editar_usuario(
    usuario_id: int,
    dados: UsuarioAdminAtualizacao,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> UsuarioAdminSaida:
    usuario = _buscar_do_meu_condominio(db, sindico, usuario_id)
    if usuario.papel not in (Papel.PORTEIRO, Papel.MORADOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você pode editar apenas porteiros e moradores.",
        )
    servico_usuarios.atualizar_usuario(db, usuario, dados)
    db.commit()
    documentos_cadastro.descartar_se_encerrado(db, usuario)
    db.refresh(usuario)
    return _para_saida_admin(db, usuario)


def _para_saida_admin(db: Session, u: Usuario) -> UsuarioAdminSaida:
    from app.models.condominio import Condominio, Unidade

    condominio = db.get(Condominio, u.condominio_id) if u.condominio_id else None
    unidade = db.get(Unidade, u.unidade_id) if u.unidade_id else None
    return UsuarioAdminSaida(
        id=u.id, nome=u.nome, email=u.email, cpf=u.cpf, telefone=u.telefone,
        papel=u.papel, status=u.status, condominio_id=u.condominio_id,
        condominio_nome=condominio.nome if condominio else None,
        unidade=unidade.identificacao if unidade else None,
        tipo_ocupacao=u.tipo_ocupacao, criado_em=u.criado_em,
    )


# ── Administração dos cadastros ──────────────────────────────────────
@router.get("", response_model=list[UsuarioSaida], summary="Lista os usuários do condomínio")
def listar_usuarios(
    papel: Papel | None = Query(default=None, description="Filtra por papel."),
    status_usuario: StatusUsuario | None = Query(
        default=None, alias="status", description="Filtra por status."
    ),
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> list[Usuario]:
    consulta = select(Usuario).where(Usuario.condominio_id == sindico.condominio_id)
    if papel is not None:
        consulta = consulta.where(Usuario.papel == papel)
    if status_usuario is not None:
        consulta = consulta.where(Usuario.status == status_usuario)
    return list(db.scalars(consulta.order_by(Usuario.nome)).all())


@router.post(
    "/{usuario_id}/aprovacao",
    response_model=UsuarioSaida,
    summary="Aprova ou recusa um cadastro",
)
def aprovar_usuario(
    usuario_id: int,
    dados: AprovacaoUsuario,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> Usuario:
    """Alimenta as telas "aguardando aprovação" do front-end."""
    usuario = _buscar_do_meu_condominio(db, sindico, usuario_id)
    # Relê travado até o commit: com duas abas, "aprovar" e "recusar"
    # passavam juntos pela conferência do status, e o morador recebia os
    # dois e-mails.
    db.refresh(usuario, with_for_update=True)

    if usuario.id == sindico.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode avaliar o próprio cadastro.",
        )
    if usuario.status != StatusUsuario.AGUARDANDO_APROVACAO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este cadastro não está aguardando aprovação.",
        )

    usuario.status = StatusUsuario.ATIVO if dados.aprovado else StatusUsuario.RECUSADO
    # Fica o registro de quem decidiu e quando, como em reservas e
    # ocorrências. O motivo só faz sentido na recusa; aprovar limpa o
    # que tiver sobrado de uma recusa anterior.
    usuario.avaliado_por_id = sindico.id
    usuario.avaliado_em = datetime.now(timezone.utc)
    usuario.motivo_recusa = None if dados.aprovado else dados.motivo
    db.commit()
    if not dados.aprovado:
        documentos_cadastro.descartar_todos(db, usuario.id)

    # A tela do cadastro promete avisar por e-mail quando o síndico decidir.
    if dados.aprovado:
        titulo, mensagem = (
            "Cadastro aprovado",
            "O síndico aprovou o seu cadastro. Você já pode entrar com o seu e-mail e senha.",
        )
    else:
        titulo = "Cadastro recusado"
        mensagem = "O síndico recusou o seu cadastro."
        if dados.motivo:
            mensagem += f" Motivo: {dados.motivo}"
        mensagem += " Em caso de dúvida, fale com a administração do condomínio."
    notificacao.notificar(usuario.email, CanalVerificacao.EMAIL, titulo, mensagem)

    db.refresh(usuario)
    return usuario


@router.get(
    "/{usuario_id}/documentos",
    response_model=list[DocumentoCadastroSaida],
    summary="Documentos enviados no cadastro do morador",
)
def listar_documentos(
    usuario_id: int,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> list[DocumentoCadastroSaida]:
    """Para o síndico conferir antes de aprovar (seção 13.5.1)."""
    usuario = _buscar_do_meu_condominio(db, sindico, usuario_id)
    return [documentos_cadastro.saida(d) for d in documentos_cadastro.listar(db, usuario.id)]


@router.get(
    "/{usuario_id}/documentos/{documento_id}/arquivo",
    summary="Abre um documento do cadastro",
)
def abrir_documento(
    usuario_id: int,
    documento_id: int,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> FileResponse:
    usuario = _buscar_do_meu_condominio(db, sindico, usuario_id)
    documento = db.get(DocumentoCadastro, documento_id)
    caminho = (
        servico_arquivos.caminho_privado(servico_arquivos.DOCUMENTOS, documento.arquivo)
        if documento is not None and documento.usuario_id == usuario.id else None
    )
    if caminho is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado."
        )
    return FileResponse(
        caminho,
        media_type=documento.tipo_conteudo,
        headers={
            "Cache-Control": "private, no-store",
            # Mostra no navegador (imagem ou PDF), sem baixar sozinho.
            "Content-Disposition": "inline",
        },
    )


@router.patch("/eu", response_model=PerfilSaida, summary="Atualiza o próprio perfil")
def atualizar_perfil(
    dados: UsuarioAtualizacao,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
) -> Usuario:
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(usuario, campo, valor)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.put("/eu/foto", response_model=PerfilSaida, summary="Envia ou troca a foto de perfil")
def enviar_foto(
    arquivo: UploadFile = File(..., description="Imagem JPG, PNG ou WebP"),
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
) -> Usuario:
    from app.core.config import settings

    # Lê só até um byte além do limite: o bastante para saber que
    # passou, sem carregar na memória um arquivo de qualquer tamanho.
    conteudo = arquivo.file.read(settings.FOTO_MAX_KB * 1024 + 1)
    try:
        nova = servico_arquivos.salvar_foto(conteudo)
    except servico_arquivos.ArquivoRecusado as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro

    anterior = usuario.foto_url
    usuario.foto_url = nova
    db.commit()
    # A antiga só sai do disco depois que a nova foi gravada no banco:
    # se o commit falhasse, o usuário não ficaria sem nenhuma.
    servico_arquivos.apagar_foto(anterior)
    db.refresh(usuario)
    return usuario


@router.delete("/eu/foto", response_model=PerfilSaida, summary="Remove a foto de perfil")
def remover_foto(
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
) -> Usuario:
    anterior = usuario.foto_url
    usuario.foto_url = None
    db.commit()
    servico_arquivos.apagar_foto(anterior)
    db.refresh(usuario)
    return usuario


@router.delete(
    "/{usuario_id}",
    response_model=Mensagem,
    summary="Inativa um usuário",
)
def inativar_usuario(
    usuario_id: int,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> Mensagem:
    usuario = _buscar_do_meu_condominio(db, sindico, usuario_id)
    if usuario.id == sindico.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode inativar o próprio usuário.",
        )
    # Inativa em vez de apagar: o histórico de portaria, reservas e
    # financeiro precisa continuar apontando para o usuário.
    usuario.status = StatusUsuario.INATIVO
    db.commit()
    # Os registros ficam; os documentos do cadastro, não: sem vínculo com
    # o condomínio, acabou a finalidade de guardá-los (LGPD, art. 16).
    documentos_cadastro.descartar_todos(db, usuario.id)
    return Mensagem(detalhe="Usuário inativado.")

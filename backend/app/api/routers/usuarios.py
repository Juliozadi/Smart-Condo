"""Gestão de usuários pelo síndico.

Documentação:
  - seção 8: "Síndico: responsável pelo cadastro dos funcionários... 
    administrar os moradores"
  - seção 9, caso de uso "Permissão do Porteiro": "o sistema mostra as
    possibilidades de ações do porteiro" e "o síndico escolhe quais estarão
    disponíveis para o porteiro"
  - seção 11.2: "o cadastro do porteiro deve ser fomentado com dados
    pessoais, e por fim as permissões de uso no sistema"
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import exigir_papel, get_usuario_atual
from app.core.database import get_db
from app.core.security import gerar_hash_senha
from app.models.enums import CanalVerificacao, FinalidadeCodigo, Papel, StatusUsuario
from app.models.usuario import PermissaoPorteiro, Usuario
from app.schemas.comuns import Mensagem
from app.schemas.admin import (
    UsuarioAdminAtualizacao, UsuarioAdminEntrada, UsuarioAdminSaida,
)
from app.schemas.usuario import (
    AprovacaoUsuario, CadastroPorteiro, CadastroSaida, PerfilSaida,
    PermissoesPorteiroEntrada, PermissoesPorteiroSaida, UsuarioAtualizacao, UsuarioSaida,
)
from app.services import usuarios as servico_usuarios
from app.services import auth as servico_auth
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


# ── Cadastro do porteiro (seções 9 e 11.2) ───────────────────────────
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


# ── Permissões (seção 9) ─────────────────────────────────────────────
@router.get(
    "/porteiros/acoes",
    summary="Lista as ações que podem ser liberadas ao porteiro",
)
def listar_acoes_do_porteiro(
    _: Usuario = Depends(exigir_papel(Papel.SINDICO)),
) -> list[dict[str, str]]:
    """"O sistema mostra as possibilidades de ações do porteiro" (seção 9)."""
    return ACOES_DO_PORTEIRO


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
    """"O síndico escolhe quais estarão disponíveis para o porteiro" (seção 9)."""
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
    db.commit()
    db.refresh(usuario)
    return usuario


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
    return Mensagem(detalhe="Usuário inativado.")

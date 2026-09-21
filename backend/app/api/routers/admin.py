"""Painel do administrador da plataforma.

O administrador cadastra os condomínios e, dentro de cada um, cria, edita e
remove síndicos, porteiros e moradores. É o único papel que atravessa
condomínios: os demais só enxergam o próprio.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import exigir_papel
from app.core.database import get_db
from app.core.security import gerar_codigo_condominio
from app.models.condominio import Condominio, Unidade
from app.models.enums import Papel, StatusUsuario
from app.models.usuario import Usuario
from app.schemas.admin import (
    CondominioAdminSaida, ResumoPlataforma, UsuarioAdminAtualizacao,
    UsuarioAdminEntrada, UsuarioAdminSaida,
)
from app.schemas.comuns import Mensagem
from app.schemas.condominio import CondominioEntrada
from app.services import usuarios as servico_usuarios

router = APIRouter(prefix="/admin", tags=["Administrador"])

# Toda rota daqui exige o papel de administrador.
SomenteAdmin = Depends(exigir_papel(Papel.ADMIN))


def _gerar_codigo_unico(db: Session, nome: str) -> str:
    for _ in range(10):
        codigo = gerar_codigo_condominio(nome)
        if not db.scalar(select(Condominio).where(Condominio.codigo_acesso == codigo)):
            return codigo
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Não foi possível gerar o código de acesso. Tente de novo.",
    )


def _contar(db: Session, condominio_id: int, papel: Papel) -> int:
    return db.scalar(
        select(func.count(Usuario.id)).where(
            Usuario.condominio_id == condominio_id,
            Usuario.papel == papel,
            Usuario.status != StatusUsuario.INATIVO,
        )
    ) or 0


def _condominio_saida(db: Session, c: Condominio) -> CondominioAdminSaida:
    sindico = db.get(Usuario, c.sindico_id) if c.sindico_id else None
    unidades = db.scalar(
        select(func.count(Unidade.id)).where(Unidade.condominio_id == c.id)
    ) or 0
    return CondominioAdminSaida(
        id=c.id, nome=c.nome, cnpj=c.cnpj, codigo_acesso=c.codigo_acesso,
        cep=c.cep, logradouro=c.logradouro, numero=c.numero,
        complemento=c.complemento, bairro=c.bairro, cidade=c.cidade, uf=c.uf,
        telefone=c.telefone,
        sindico_id=sindico.id if sindico else None,
        sindico_nome=sindico.nome if sindico else None,
        total_unidades=unidades,
        total_moradores=_contar(db, c.id, Papel.MORADOR),
        total_porteiros=_contar(db, c.id, Papel.PORTEIRO),
        criado_em=c.criado_em,
    )


def _usuario_saida(db: Session, u: Usuario) -> UsuarioAdminSaida:
    condominio = db.get(Condominio, u.condominio_id) if u.condominio_id else None
    unidade = db.get(Unidade, u.unidade_id) if u.unidade_id else None
    return UsuarioAdminSaida(
        id=u.id, nome=u.nome, email=u.email, cpf=u.cpf, telefone=u.telefone,
        papel=u.papel, status=u.status, condominio_id=u.condominio_id,
        condominio_nome=condominio.nome if condominio else None,
        unidade=unidade.identificacao if unidade else None,
        tipo_ocupacao=u.tipo_ocupacao, criado_em=u.criado_em,
    )


# Quem digita "Joao" precisa encontrar "João". O ilike do Postgres é
# indiferente a maiúsculas, mas não a acentos; o translate abaixo tira os
# acentos dos dois lados sem depender da extensão unaccent, que nem toda
# instalação tem.
_COM_ACENTO = "áàâãäéèêëíìîïóòôõöúùûüçñÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑ"
_SEM_ACENTO = "aaaaaeeeeiiiiooooouuuucnAAAAAEEEEIIIIOOOOOUUUUCN"


def _sem_acento(coluna):
    """Versão da coluna sem acentos, para comparar com o termo buscado."""
    return func.translate(coluna, _COM_ACENTO, _SEM_ACENTO)


def _termo_sem_acento(busca: str) -> str:
    tabela = str.maketrans(_COM_ACENTO, _SEM_ACENTO)
    return f"%{busca.strip().translate(tabela)}%"


def _buscar_condominio(db: Session, condominio_id: int) -> Condominio:
    condominio = db.get(Condominio, condominio_id)
    if condominio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Condomínio não encontrado."
        )
    return condominio


# ══ Visão geral ═══════════════════════════════════════════════════════
@router.get("/resumo", response_model=ResumoPlataforma, summary="Indicadores da plataforma")
def resumo(_: Usuario = SomenteAdmin, db: Session = Depends(get_db)) -> ResumoPlataforma:
    def conta_papel(papel: Papel) -> int:
        return db.scalar(
            select(func.count(Usuario.id)).where(
                Usuario.papel == papel, Usuario.status != StatusUsuario.INATIVO
            )
        ) or 0

    return ResumoPlataforma(
        condominios=db.scalar(select(func.count(Condominio.id))) or 0,
        sindicos=conta_papel(Papel.SINDICO),
        porteiros=conta_papel(Papel.PORTEIRO),
        moradores=conta_papel(Papel.MORADOR),
        aguardando_aprovacao=db.scalar(
            select(func.count(Usuario.id)).where(
                Usuario.status == StatusUsuario.AGUARDANDO_APROVACAO
            )
        ) or 0,
    )


# ══ Condomínios ═══════════════════════════════════════════════════════
@router.get(
    "/condominios", response_model=list[CondominioAdminSaida], summary="Lista os condomínios"
)
def listar_condominios(
    busca: str | None = Query(default=None, description="Filtra por nome, cidade ou CNPJ."),
    _: Usuario = SomenteAdmin,
    db: Session = Depends(get_db),
) -> list[CondominioAdminSaida]:
    consulta = select(Condominio).order_by(Condominio.nome)
    if busca:
        termo = _termo_sem_acento(busca)
        consulta = consulta.where(
            _sem_acento(Condominio.nome).ilike(termo)
            | _sem_acento(Condominio.cidade).ilike(termo)
            | Condominio.cnpj.ilike(termo)
        )
    return [_condominio_saida(db, c) for c in db.scalars(consulta).all()]


@router.post(
    "/condominios",
    response_model=CondominioAdminSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um condomínio",
)
def criar_condominio(
    dados: CondominioEntrada, _: Usuario = SomenteAdmin, db: Session = Depends(get_db)
) -> CondominioAdminSaida:
    if db.scalar(select(Condominio).where(Condominio.cnpj == dados.cnpj)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um condomínio com este CNPJ.",
        )

    condominio = Condominio(
        **dados.model_dump(), codigo_acesso=_gerar_codigo_unico(db, dados.nome)
    )
    db.add(condominio)
    db.commit()
    db.refresh(condominio)
    return _condominio_saida(db, condominio)


@router.get(
    "/condominios/{condominio_id}",
    response_model=CondominioAdminSaida,
    summary="Detalha um condomínio",
)
def detalhar_condominio(
    condominio_id: int, _: Usuario = SomenteAdmin, db: Session = Depends(get_db)
) -> CondominioAdminSaida:
    return _condominio_saida(db, _buscar_condominio(db, condominio_id))


@router.put(
    "/condominios/{condominio_id}",
    response_model=CondominioAdminSaida,
    summary="Edita um condomínio",
)
def editar_condominio(
    condominio_id: int,
    dados: CondominioEntrada,
    _: Usuario = SomenteAdmin,
    db: Session = Depends(get_db),
) -> CondominioAdminSaida:
    condominio = _buscar_condominio(db, condominio_id)

    outro = db.scalar(
        select(Condominio).where(Condominio.cnpj == dados.cnpj, Condominio.id != condominio.id)
    )
    if outro is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe outro condomínio com este CNPJ.",
        )

    for campo, valor in dados.model_dump().items():
        setattr(condominio, campo, valor)

    db.commit()
    db.refresh(condominio)
    return _condominio_saida(db, condominio)


@router.delete(
    "/condominios/{condominio_id}", response_model=Mensagem, summary="Exclui um condomínio"
)
def excluir_condominio(
    condominio_id: int, _: Usuario = SomenteAdmin, db: Session = Depends(get_db)
) -> Mensagem:
    condominio = _buscar_condominio(db, condominio_id)

    # Apagar levaria junto reservas, cobranças e portaria por cascata.
    # Enquanto houver gente ativa, o condomínio não sai.
    ativos = db.scalar(
        select(func.count(Usuario.id)).where(
            Usuario.condominio_id == condominio.id, Usuario.status != StatusUsuario.INATIVO
        )
    ) or 0
    if ativos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Este condomínio ainda tem {ativos} usuário(s) ativo(s). "
                "Remova-os antes de excluí-lo."
            ),
        )

    # O síndico é apontado pelo condomínio; solta antes de apagar.
    condominio.sindico_id = None
    db.flush()
    db.delete(condominio)
    db.commit()
    return Mensagem(detalhe="Condomínio excluído.")


@router.post(
    "/condominios/{condominio_id}/codigo-acesso",
    response_model=CondominioAdminSaida,
    summary="Gera um novo código de acesso",
)
def renovar_codigo(
    condominio_id: int, _: Usuario = SomenteAdmin, db: Session = Depends(get_db)
) -> CondominioAdminSaida:
    condominio = _buscar_condominio(db, condominio_id)
    condominio.codigo_acesso = _gerar_codigo_unico(db, condominio.nome)
    db.commit()
    db.refresh(condominio)
    return _condominio_saida(db, condominio)


# ══ Usuários ══════════════════════════════════════════════════════════
@router.get("/usuarios", response_model=list[UsuarioAdminSaida], summary="Lista os usuários")
def listar_usuarios(
    condominio_id: int | None = Query(default=None),
    papel: Papel | None = Query(default=None),
    status_usuario: StatusUsuario | None = Query(default=None, alias="status"),
    busca: str | None = Query(default=None, description="Filtra por nome, e-mail ou CPF."),
    _: Usuario = SomenteAdmin,
    db: Session = Depends(get_db),
) -> list[UsuarioAdminSaida]:
    consulta = select(Usuario).order_by(Usuario.nome)
    if condominio_id is not None:
        consulta = consulta.where(Usuario.condominio_id == condominio_id)
    if papel is not None:
        consulta = consulta.where(Usuario.papel == papel)
    if status_usuario is not None:
        consulta = consulta.where(Usuario.status == status_usuario)
    if busca:
        termo = _termo_sem_acento(busca)
        consulta = consulta.where(
            _sem_acento(Usuario.nome).ilike(termo)
            | Usuario.email.ilike(termo)
            | Usuario.cpf.ilike(termo)
        )
    return [_usuario_saida(db, u) for u in db.scalars(consulta).all()]


@router.post(
    "/condominios/{condominio_id}/usuarios",
    response_model=UsuarioAdminSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um usuário no condomínio",
)
def criar_usuario(
    condominio_id: int,
    dados: UsuarioAdminEntrada,
    admin: Usuario = SomenteAdmin,
    db: Session = Depends(get_db),
) -> UsuarioAdminSaida:
    condominio = _buscar_condominio(db, condominio_id)
    usuario = servico_usuarios.criar_usuario(db, condominio, dados, admin)
    db.commit()
    db.refresh(usuario)
    return _usuario_saida(db, usuario)


@router.get(
    "/usuarios/{usuario_id}", response_model=UsuarioAdminSaida, summary="Detalha um usuário"
)
def detalhar_usuario(
    usuario_id: int, _: Usuario = SomenteAdmin, db: Session = Depends(get_db)
) -> UsuarioAdminSaida:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado."
        )
    return _usuario_saida(db, usuario)


@router.put(
    "/usuarios/{usuario_id}", response_model=UsuarioAdminSaida, summary="Edita um usuário"
)
def editar_usuario(
    usuario_id: int,
    dados: UsuarioAdminAtualizacao,
    _: Usuario = SomenteAdmin,
    db: Session = Depends(get_db),
) -> UsuarioAdminSaida:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado."
        )
    servico_usuarios.atualizar_usuario(db, usuario, dados)
    db.commit()
    db.refresh(usuario)
    return _usuario_saida(db, usuario)


@router.delete("/usuarios/{usuario_id}", response_model=Mensagem, summary="Remove um usuário")
def remover_usuario(
    usuario_id: int, admin: Usuario = SomenteAdmin, db: Session = Depends(get_db)
) -> Mensagem:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado."
        )
    servico_usuarios.remover_usuario(db, usuario, admin)
    db.commit()
    return Mensagem(detalhe="Usuário removido.")

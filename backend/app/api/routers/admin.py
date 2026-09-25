"""Painel do administrador da plataforma.

O administrador cadastra os condomínios e, dentro de cada um, cria, edita e
inativa síndicos, porteiros e moradores; também cadastra outros
administradores. É o único papel que atravessa condomínios: os demais só
enxergam o próprio.

Nada é apagado: "excluir" inativa, e o registro pode ser reativado. Toda
criação, edição, inativação e reativação guarda quem a fez e quando
(registros_alteracao), e as telas mostram "Editado por fulano".
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import exigir_papel
from app.core.database import get_db, pre_carregar
from app.core.security import gerar_codigo_condominio
from app.models.condominio import Condominio, Unidade
from app.models.enums import Papel, StatusUsuario
from app.models.usuario import Usuario
from app.schemas.admin import (
    AdministradorEntrada, CondominioAdminSaida, RegistroSaida, ResumoPlataforma,
    UsuarioAdminAtualizacao, UsuarioAdminEntrada, UsuarioAdminSaida,
)
from app.schemas.comuns import Mensagem
from app.schemas.condominio import CondominioEntrada
from app.services import documentos_cadastro
from app.services import registro
from app.services import usuarios as servico_usuarios

router = APIRouter(prefix="/admin", tags=["Administrador"])

# Toda rota daqui exige o papel de administrador.
SomenteAdmin = Depends(exigir_papel(Papel.ADMIN))

ROTULOS_CONDOMINIO = {
    "nome": "o nome", "cnpj": "o CNPJ", "cep": "o CEP", "logradouro": "o logradouro",
    "numero": "o número", "bairro": "o bairro", "cidade": "a cidade", "uf": "a UF",
    "telefone": "o telefone",
}
ROTULOS_USUARIO = {
    "nome": "o nome", "email": "o e-mail", "telefone": "o telefone",
    "data_nascimento": "a data de nascimento", "tipo_ocupacao": "o tipo de ocupação",
}


def _gerar_codigo_unico(db: Session, nome: str) -> str:
    for _ in range(10):
        codigo = gerar_codigo_condominio(nome)
        if not db.scalar(select(Condominio).where(Condominio.codigo_acesso == codigo)):
            return codigo
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Não foi possível gerar o código de acesso. Tente de novo.",
    )


def _condominios_saida(db: Session, condominios) -> list[CondominioAdminSaida]:
    """Monta a saída de vários condomínios com um número fixo de consultas:
    contagens agrupadas, síndicos e registros de alteração de uma vez."""
    ids = [c.id for c in condominios]
    if not ids:
        return []
    unidades = dict(db.execute(
        select(Unidade.condominio_id, func.count(Unidade.id))
        .where(Unidade.condominio_id.in_(ids)).group_by(Unidade.condominio_id)
    ).all())
    pessoas = {
        (cid, papel): total for cid, papel, total in db.execute(
            select(Usuario.condominio_id, Usuario.papel, func.count(Usuario.id))
            .where(Usuario.condominio_id.in_(ids), Usuario.status != StatusUsuario.INATIVO)
            .group_by(Usuario.condominio_id, Usuario.papel)
        ).all()
    }
    sindicos = {u.id: u for u in pre_carregar(db, Usuario, (c.sindico_id for c in condominios))}
    ultimas = registro.ultimas(db, registro.CONDOMINIO, ids)
    criadores = registro.criadores(db, registro.CONDOMINIO, ids)

    saida = []
    for c in condominios:
        sindico = sindicos.get(c.sindico_id)
        saida.append(CondominioAdminSaida(
            id=c.id, nome=c.nome, cnpj=c.cnpj, codigo_acesso=c.codigo_acesso,
            cep=c.cep, logradouro=c.logradouro, numero=c.numero,
            bairro=c.bairro, cidade=c.cidade, uf=c.uf, telefone=c.telefone,
            sindico_id=sindico.id if sindico else None,
            sindico_nome=sindico.nome if sindico else None,
            total_unidades=unidades.get(c.id, 0),
            total_moradores=pessoas.get((c.id, Papel.MORADOR), 0),
            total_porteiros=pessoas.get((c.id, Papel.PORTEIRO), 0),
            criado_em=c.criado_em,
            inativo=c.inativo_em is not None, inativo_em=c.inativo_em,
            criado_por=criadores.get(c.id),
            ultima_alteracao=ultimas.get(c.id),
        ))
    return saida


def _condominio_saida(db: Session, c: Condominio) -> CondominioAdminSaida:
    return _condominios_saida(db, [c])[0]


def _usuarios_saida(db: Session, usuarios) -> list[UsuarioAdminSaida]:
    ids = [u.id for u in usuarios]
    carregados = (  # noqa: F841 — mantém os objetos vivos na sessão
        pre_carregar(db, Unidade, (u.unidade_id for u in usuarios)),
        pre_carregar(db, Condominio, (u.condominio_id for u in usuarios)),
    )
    ultimas = registro.ultimas(db, registro.USUARIO, ids)
    criadores = registro.criadores(db, registro.USUARIO, ids)
    saida = []
    for u in usuarios:
        condominio = db.get(Condominio, u.condominio_id) if u.condominio_id else None
        unidade = db.get(Unidade, u.unidade_id) if u.unidade_id else None
        saida.append(UsuarioAdminSaida(
            id=u.id, nome=u.nome, email=u.email, cpf=u.cpf, telefone=u.telefone,
            papel=u.papel, status=u.status, condominio_id=u.condominio_id,
            condominio_nome=condominio.nome if condominio else None,
            unidade=unidade.identificacao if unidade else None,
            tipo_ocupacao=u.tipo_ocupacao, criado_em=u.criado_em,
            criado_por=criadores.get(u.id),
            ultima_alteracao=ultimas.get(u.id),
        ))
    return saida


def _usuario_saida(db: Session, u: Usuario) -> UsuarioAdminSaida:
    return _usuarios_saida(db, [u])[0]


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


def _buscar_condominio(db: Session, condominio_id: int, travar: bool = False) -> Condominio:
    condominio = db.get(Condominio, condominio_id, with_for_update=travar)
    if condominio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Condomínio não encontrado."
        )
    return condominio


def _buscar_usuario(db: Session, usuario_id: int) -> Usuario:
    """Relê o usuário travado. Se for administrador, trava antes todos os
    administradores, na mesma ordem de garantir_outro_admin_ativo: se A e B
    se inativassem ao mesmo tempo, cada um veria o outro ainda ativo."""
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado."
        )
    if usuario.papel == Papel.ADMIN:
        servico_usuarios.travar_administradores(db)
    db.refresh(usuario, with_for_update=True)
    return usuario


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
        condominios=db.scalar(
            select(func.count(Condominio.id)).where(Condominio.inativo_em.is_(None))
        ) or 0,
        sindicos=conta_papel(Papel.SINDICO),
        porteiros=conta_papel(Papel.PORTEIRO),
        moradores=conta_papel(Papel.MORADOR),
        aguardando_aprovacao=db.scalar(
            select(func.count(Usuario.id)).where(
                Usuario.status == StatusUsuario.AGUARDANDO_APROVACAO
            )
        ) or 0,
    )


@router.get(
    "/historico", response_model=list[RegistroSaida], summary="Histórico de alterações de um registro"
)
def historico(
    entidade: str = Query(pattern="^(condominio|usuario|comunicado|documento)$"),
    entidade_id: int = Query(),
    _: Usuario = SomenteAdmin,
    db: Session = Depends(get_db),
) -> list[dict]:
    return registro.historico(db, entidade, entidade_id)


# ══ Condomínios ═══════════════════════════════════════════════════════
@router.get(
    "/condominios", response_model=list[CondominioAdminSaida], summary="Lista os condomínios"
)
def listar_condominios(
    busca: str | None = Query(default=None, description="Filtra por nome, cidade ou CNPJ."),
    _: Usuario = SomenteAdmin,
    db: Session = Depends(get_db),
) -> list[CondominioAdminSaida]:
    # Os inativos vêm por último: continuam na lista para serem reativados.
    consulta = select(Condominio).order_by(
        Condominio.inativo_em.is_not(None), Condominio.nome
    )
    if busca:
        termo = _termo_sem_acento(busca)
        consulta = consulta.where(
            _sem_acento(Condominio.nome).ilike(termo)
            | _sem_acento(Condominio.cidade).ilike(termo)
            | Condominio.cnpj.ilike(termo)
        )
    return _condominios_saida(db, db.scalars(consulta).all())


@router.post(
    "/condominios",
    response_model=CondominioAdminSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um condomínio",
)
def criar_condominio(
    dados: CondominioEntrada, admin: Usuario = SomenteAdmin, db: Session = Depends(get_db)
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
    db.flush()
    registro.registrar(db, admin, registro.CRIOU, registro.CONDOMINIO, condominio.id)
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
    admin: Usuario = SomenteAdmin,
    db: Session = Depends(get_db),
) -> CondominioAdminSaida:
    condominio = _buscar_condominio(db, condominio_id, travar=True)

    outro = db.scalar(
        select(Condominio).where(Condominio.cnpj == dados.cnpj, Condominio.id != condominio.id)
    )
    if outro is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe outro condomínio com este CNPJ.",
        )

    novos = dados.model_dump()
    descricao = registro.campos_alterados(condominio, novos, ROTULOS_CONDOMINIO)
    for campo, valor in novos.items():
        setattr(condominio, campo, valor)
    if descricao:
        registro.registrar(db, admin, registro.EDITOU, registro.CONDOMINIO, condominio.id,
                           descricao)

    db.commit()
    db.refresh(condominio)
    return _condominio_saida(db, condominio)


@router.delete(
    "/condominios/{condominio_id}", response_model=Mensagem, summary="Inativa um condomínio"
)
def inativar_condominio(
    condominio_id: int, admin: Usuario = SomenteAdmin, db: Session = Depends(get_db)
) -> Mensagem:
    """Nada é apagado: o condomínio sai das telas e o código de acesso
    deixa de valer, mas reservas, cobranças e portaria continuam no banco,
    e ele pode ser reativado."""
    condominio = _buscar_condominio(db, condominio_id, travar=True)
    if condominio.inativo_em is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Este condomínio já está inativo."
        )

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
                "Inative-os antes de inativá-lo."
            ),
        )

    condominio.inativo_em = datetime.now(timezone.utc)
    condominio.inativado_por_id = admin.id
    registro.registrar(db, admin, registro.INATIVOU, registro.CONDOMINIO, condominio.id)
    db.commit()
    return Mensagem(detalhe="Condomínio inativado.")


@router.post(
    "/condominios/{condominio_id}/reativacao",
    response_model=CondominioAdminSaida,
    summary="Reativa um condomínio",
)
def reativar_condominio(
    condominio_id: int, admin: Usuario = SomenteAdmin, db: Session = Depends(get_db)
) -> CondominioAdminSaida:
    condominio = _buscar_condominio(db, condominio_id, travar=True)
    if condominio.inativo_em is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Este condomínio já está ativo."
        )
    condominio.inativo_em = None
    condominio.inativado_por_id = None
    registro.registrar(db, admin, registro.REATIVOU, registro.CONDOMINIO, condominio.id)
    db.commit()
    db.refresh(condominio)
    return _condominio_saida(db, condominio)


@router.post(
    "/condominios/{condominio_id}/codigo-acesso",
    response_model=CondominioAdminSaida,
    summary="Gera um novo código de acesso",
)
def renovar_codigo(
    condominio_id: int, admin: Usuario = SomenteAdmin, db: Session = Depends(get_db)
) -> CondominioAdminSaida:
    condominio = _buscar_condominio(db, condominio_id, travar=True)
    condominio.codigo_acesso = _gerar_codigo_unico(db, condominio.nome)
    registro.registrar(db, admin, registro.NOVO_CODIGO, registro.CONDOMINIO, condominio.id)
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
    return _usuarios_saida(db, db.scalars(consulta).all())


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
    registro.registrar(db, admin, registro.CRIOU, registro.USUARIO, usuario.id)
    db.commit()
    db.refresh(usuario)
    return _usuario_saida(db, usuario)


@router.post(
    "/administradores",
    response_model=UsuarioAdminSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra outro administrador",
)
def criar_administrador(
    dados: AdministradorEntrada, admin: Usuario = SomenteAdmin, db: Session = Depends(get_db)
) -> UsuarioAdminSaida:
    novo = servico_usuarios.criar_administrador(db, dados)
    registro.registrar(db, admin, registro.CRIOU, registro.USUARIO, novo.id)
    db.commit()
    db.refresh(novo)
    return _usuario_saida(db, novo)


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
    admin: Usuario = SomenteAdmin,
    db: Session = Depends(get_db),
) -> UsuarioAdminSaida:
    usuario = _buscar_usuario(db, usuario_id)
    campos = dados.model_dump(exclude_unset=True)
    novo_status = campos.get("status")
    if usuario.id == admin.id and novo_status not in (None, StatusUsuario.ATIVO):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode inativar o próprio usuário.",
        )

    status_antes = usuario.status
    descricao = registro.campos_alterados(usuario, campos, ROTULOS_USUARIO)
    if campos.get("senha"):
        descricao = (descricao + " e a senha") if descricao else "Alterou a senha"
    if campos.get("unidade_numero") or campos.get("unidade_bloco"):
        # A tela sempre manda a unidade do morador: só conta se mudou.
        atual = db.get(Unidade, usuario.unidade_id) if usuario.unidade_id else None
        nova = (campos.get("unidade_numero") or (atual.numero if atual else ""),
                campos.get("unidade_bloco") or (atual.bloco if atual else "unico"))
        if atual is None or nova != (atual.numero, atual.bloco):
            descricao = (descricao + " e a unidade") if descricao else "Alterou a unidade"

    servico_usuarios.atualizar_usuario(db, usuario, dados)

    if usuario.status != status_antes and usuario.status == StatusUsuario.INATIVO:
        registro.registrar(db, admin, registro.INATIVOU, registro.USUARIO, usuario.id, descricao)
    elif usuario.status != status_antes and status_antes == StatusUsuario.INATIVO:
        registro.registrar(db, admin, registro.REATIVOU, registro.USUARIO, usuario.id, descricao)
    elif descricao or usuario.status != status_antes:
        registro.registrar(db, admin, registro.EDITOU, registro.USUARIO, usuario.id, descricao)

    db.commit()
    documentos_cadastro.descartar_se_encerrado(db, usuario)
    db.refresh(usuario)
    return _usuario_saida(db, usuario)


@router.delete("/usuarios/{usuario_id}", response_model=Mensagem, summary="Inativa um usuário")
def remover_usuario(
    usuario_id: int, admin: Usuario = SomenteAdmin, db: Session = Depends(get_db)
) -> Mensagem:
    usuario = _buscar_usuario(db, usuario_id)
    if usuario.status == StatusUsuario.INATIVO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Este usuário já está inativo."
        )
    servico_usuarios.remover_usuario(db, usuario, admin)
    registro.registrar(db, admin, registro.INATIVOU, registro.USUARIO, usuario.id)
    db.commit()
    # Sem vínculo com o condomínio, acabou a finalidade dos documentos.
    documentos_cadastro.descartar_todos(db, usuario.id)
    return Mensagem(detalhe="Usuário inativado.")

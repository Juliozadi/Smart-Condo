"""Uma pessoa, vários perfis.

O síndico que mora no condomínio, o morador eleito síndico, o dono de
mais de um apartamento: a mesma pessoa precisa agir em mais de um papel
ou apartamento. Cada perfil é um cadastro (uma linha de usuarios) — e
por isso tudo o que o sistema já faz para o morador e para o síndico
vale para ele sem mudança. O que os une é conta_principal_id: só o
cadastro principal tem login (e-mail e senha); os vinculados apontam
para ele e não têm senha própria. A pessoa troca de perfil já logada.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.condominio import Unidade
from app.models.enums import Papel, StatusUsuario, TipoOcupacao
from app.models.usuario import Usuario
from app.schemas.usuario import PerfilDisponivel

# Não é um hash do bcrypt: nenhuma senha confere com ele. O login procura
# só cadastros principais, mas, se algum caminho chegasse aqui, falharia.
SEM_SENHA = "!perfil-vinculado"

# Apartamentos vinculados por pessoa: contra engano e abuso.
LIMITE_PERFIS = 10

# Status em que o perfil ainda conta (aparece e ocupa o lugar).
VIGENTES = (StatusUsuario.ATIVO, StatusUsuario.AGUARDANDO_APROVACAO)


def principal(usuario: Usuario) -> Usuario:
    """O cadastro com login da pessoa."""
    return usuario.conta_principal or usuario


def da_pessoa(db: Session, usuario: Usuario) -> list[Usuario]:
    """Todos os perfis da pessoa, o principal primeiro."""
    dono = principal(usuario)
    vinculados = db.scalars(
        select(Usuario).where(Usuario.conta_principal_id == dono.id).order_by(Usuario.id)
    ).all()
    return [dono, *vinculados]


def possui_outros(db: Session, usuario: Usuario) -> bool:
    return sum(1 for p in da_pessoa(db, usuario) if p.status in VIGENTES) > 1


def com_perfis(db: Session, usuario: Usuario, esquema):
    """A saída do usuário dizendo se a tela mostra a troca de perfil."""
    return esquema.model_validate(usuario).model_copy(
        update={"possui_outros_perfis": possui_outros(db, usuario)})


def disponivel(p: Usuario, atual: Usuario) -> PerfilDisponivel:
    return PerfilDisponivel(
        usuario_id=p.id, papel=p.papel, status=p.status,
        condominio=p.condominio.nome if p.condominio else None,
        unidade=p.unidade.identificacao if p.unidade else None,
        tipo_ocupacao=p.tipo_ocupacao, reside=p.reside, atual=p.id == atual.id,
    )


def e_sindico_do_condominio(db: Session, usuario: Usuario, condominio_id: int) -> bool:
    return any(p.papel == Papel.SINDICO and p.status == StatusUsuario.ATIVO
               and p.condominio_id == condominio_id for p in da_pessoa(db, usuario))


def _copia(dono: Usuario, **campos) -> Usuario:
    return Usuario(
        nome=dono.nome, email=dono.email, cpf=dono.cpf, telefone=dono.telefone,
        data_nascimento=dono.data_nascimento, foto_url=dono.foto_url,
        senha_hash=SEM_SENHA, conta_principal_id=dono.id, **campos,
    )


def vincular_apartamento(db: Session, usuario: Usuario, unidade_id: int,
                         tipo_ocupacao: TipoOcupacao, reside: bool) -> Usuario:
    """Novo perfil de morador da pessoa em outro apartamento do mesmo
    condomínio. Vale na hora se a pessoa é a síndica de lá (é ela quem
    aprova moradores); senão, espera o síndico."""
    dono = principal(usuario)
    if dono.papel == Papel.ADMIN or dono.condominio_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Só quem é do condomínio vincula um apartamento.")
    unidade = db.get(Unidade, unidade_id)
    if unidade is None or unidade.condominio_id != usuario.condominio_id or unidade.pendente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Apartamento não encontrado.")
    # Travado até o commit: dois pedidos iguais ao mesmo tempo.
    db.refresh(dono, with_for_update=True)
    perfis = da_pessoa(db, dono)
    if any(p.unidade_id == unidade.id and p.status in VIGENTES for p in perfis):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Este apartamento já está no seu cadastro.")
    if sum(1 for p in perfis if p.status in VIGENTES) > LIMITE_PERFIS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Você chegou ao limite de apartamentos no cadastro.")

    ja_vale = e_sindico_do_condominio(db, dono, unidade.condominio_id)
    perfil = _copia(
        dono, papel=Papel.MORADOR, condominio_id=unidade.condominio_id, unidade_id=unidade.id,
        tipo_ocupacao=tipo_ocupacao, reside=reside,
        status=StatusUsuario.ATIVO if ja_vale else StatusUsuario.AGUARDANDO_APROVACAO,
    )
    db.add(perfil)
    db.flush()
    return perfil


def pessoa_com_email_e_cpf(db: Session, email: str, cpf: str) -> Usuario | None:
    """O cadastro principal que tem os dois — a mesma pessoa. Só um dos
    dois coincidindo é outra pessoa (ou erro de digitação): recusa."""
    return db.scalar(select(Usuario).where(
        Usuario.email == email.lower(), Usuario.cpf == cpf,
        Usuario.conta_principal_id.is_(None), Usuario.papel != Papel.ADMIN,
        Usuario.status == StatusUsuario.ATIVO,
    ))


def vincular_sindico(db: Session, dono: Usuario, condominio_id: int) -> Usuario:
    """O morador eleito síndico (ou o síndico profissional de mais de um
    condomínio): o administrador cadastra com o e-mail e o CPF que a
    pessoa já usa, e ela ganha o perfil de síndico na mesma conta."""
    perfil = _copia(dono, papel=Papel.SINDICO, condominio_id=condominio_id,
                    status=StatusUsuario.ATIVO)
    db.add(perfil)
    db.flush()
    return perfil


def promover_se_preciso(db: Session, inativado: Usuario) -> Usuario | None:
    """O cadastro com login foi inativado (o mandato acabou, a pessoa saiu
    do apartamento principal), mas ela continua com outro perfil ativo:
    esse perfil passa a ser o principal, com a mesma senha, e os outros
    — o inativado inclusive — passam a apontar para ele. Assim a pessoa
    continua entrando com o mesmo e-mail e senha."""
    if inativado.conta_principal_id is not None:
        return None
    vinculados = db.scalars(
        select(Usuario).where(Usuario.conta_principal_id == inativado.id).order_by(Usuario.id)
    ).all()
    ativos = [p for p in vinculados if p.status == StatusUsuario.ATIVO]
    if not ativos:
        return None
    novo = ativos[0]
    # O e-mail e o CPF são únicos entre os principais: o antigo deixa de
    # ser principal antes de o novo passar a ser.
    inativado.conta_principal_id = novo.id
    db.flush()
    novo.conta_principal_id = None
    novo.senha_hash = inativado.senha_hash
    inativado.senha_hash = SEM_SENHA
    db.flush()
    for p in vinculados:
        if p is not novo:
            p.conta_principal_id = novo.id
    db.flush()
    for p in (inativado, *vinculados):
        db.expire(p, ["conta_principal"])
    return novo


def sincronizar_dados(db: Session, usuario: Usuario, campos: dict) -> None:
    """Nome, telefone, nascimento e foto são da pessoa, não do perfil."""
    for p in da_pessoa(db, usuario):
        for campo, valor in campos.items():
            setattr(p, campo, valor)

"""Criação e edição de usuários por quem é responsável por eles.

Duas portas levam aqui: o administrador, que mexe em qualquer condomínio,
e o síndico, que mexe apenas no próprio. A regra de negócio é a mesma, por
isso fica num lugar só.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.security import gerar_hash_senha
from app.models.condominio import Condominio, Unidade
from app.core.tempo import hoje_local
from app.models.enums import Papel, StatusReserva, StatusUsuario
from app.models.espaco import Reserva
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
            detail="Administradores são cadastrados em /admin/administradores.",
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
    if condominio.inativo_em is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este condomínio está inativo. Reative-o antes de cadastrar alguém.",
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
        # Trocada por outra pessoa (o administrador, numa conta invadida),
        # a senha antiga não pode continuar valendo nas sessões abertas.
        servico_auth.encerrar_sessoes(usuario)

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

    novo_status = campos.get("status")
    if novo_status is not None and novo_status != StatusUsuario.ATIVO:
        garantir_outro_admin_ativo(db, usuario)
    # Inativar pela edição tem o mesmo efeito de remover (remover_usuario).
    if novo_status == StatusUsuario.INATIVO:
        _soltar_do_condominio_se_sindico(db, usuario)
        cancelar_reservas_futuras(db, usuario)
    if novo_status == StatusUsuario.ATIVO and usuario.status != StatusUsuario.ATIVO:
        _conferir_reativacao(db, usuario)

    for campo, valor in campos.items():
        setattr(usuario, campo, valor)

    db.flush()
    return usuario


def cancelar_reservas_futuras(db: Session, usuario: Usuario) -> int:
    """Quem deixa o condomínio não segura mais os espaços: as reservas de
    hoje em diante, pendentes ou aprovadas, são canceladas. Sem isso, o
    salão continuava bloqueado por quem já tinha se mudado. As passadas
    ficam como estão, no histórico."""
    return db.execute(
        update(Reserva)
        .where(
            Reserva.morador_id == usuario.id,
            Reserva.status.in_((StatusReserva.PENDENTE, StatusReserva.APROVADA)),
            Reserva.data >= hoje_local(),
        )
        .values(status=StatusReserva.CANCELADA)
        .execution_options(synchronize_session=False)
    ).rowcount


def travar_administradores(db: Session) -> None:
    """Trava as linhas de todos os administradores, sempre na mesma ordem
    (por id): duas operações simultâneas esperam uma pela outra, em vez de
    cada uma travar um e ficar esperando o outro para sempre."""
    db.execute(
        select(Usuario.id).where(Usuario.papel == Papel.ADMIN)
        .order_by(Usuario.id).with_for_update()
    )


def garantir_outro_admin_ativo(db: Session, usuario: Usuario) -> None:
    """A plataforma nunca fica sem administrador ativo: sem ele, ninguém
    mais cadastra condomínios nem reativa quem foi inativado."""
    if usuario.papel != Papel.ADMIN or usuario.status != StatusUsuario.ATIVO:
        return
    # Trava todos os administradores: se A inativasse B enquanto B inativa
    # A, cada um veria o outro ainda ativo, e não sobraria nenhum.
    travar_administradores(db)
    outros = db.scalar(
        select(func.count(Usuario.id)).where(
            Usuario.papel == Papel.ADMIN, Usuario.status == StatusUsuario.ATIVO,
            Usuario.id != usuario.id,
        )
    )
    if not outros:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este é o único administrador ativo. Cadastre outro antes de inativá-lo.",
        )


def _conferir_reativacao(db: Session, usuario: Usuario) -> None:
    """Reativar segue as regras de quem é cadastrado agora: o condomínio
    precisa estar ativo, e só pode haver um síndico ativo nele. Antes, a
    reativação deixava o condomínio com dois síndicos."""
    if usuario.condominio_id is None:
        return
    condominio = db.get(Condominio, usuario.condominio_id)
    if condominio is not None and condominio.inativo_em is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O condomínio deste usuário está inativo. Reative o condomínio antes.",
        )
    if usuario.papel == Papel.SINDICO and condominio is not None:
        atual = db.scalar(
            select(Usuario).where(
                Usuario.condominio_id == condominio.id, Usuario.papel == Papel.SINDICO,
                Usuario.status != StatusUsuario.INATIVO, Usuario.id != usuario.id,
            )
        )
        if atual is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(f"{condominio.nome} já tem um síndico ativo ({atual.nome}). "
                        "Inative o atual antes de reativar este."),
            )
        if condominio.sindico_id is None:
            condominio.sindico_id = usuario.id


def criar_administrador(db: Session, dados) -> Usuario:
    """Um administrador cadastra outro: já nasce ativo e sem condomínio."""
    servico_auth.garantir_email_e_cpf_livres(db, dados.email, dados.cpf)
    usuario = Usuario(
        nome=dados.nome,
        email=dados.email.lower(),
        cpf=dados.cpf,
        telefone=dados.telefone,
        data_nascimento=dados.data_nascimento,
        senha_hash=gerar_hash_senha(dados.senha),
        papel=Papel.ADMIN,
        status=StatusUsuario.ATIVO,
    )
    db.add(usuario)
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

    garantir_outro_admin_ativo(db, usuario)
    _soltar_do_condominio_se_sindico(db, usuario)
    cancelar_reservas_futuras(db, usuario)
    usuario.status = StatusUsuario.INATIVO
    db.flush()

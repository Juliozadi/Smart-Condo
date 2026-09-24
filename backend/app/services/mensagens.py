"""Regras do chat: quem conversa com quem, e a leitura das mensagens.

A conversa é sempre entre duas pessoas ativas do mesmo condomínio. O
síndico fala com porteiros e moradores; o porteiro fala com o síndico,
com os outros porteiros e com os moradores; o morador fala com o síndico
e com a portaria — nunca com outro morador, cujo contato ele não tem
motivo para receber do sistema. O administrador da plataforma não
participa: ele não pertence a condomínio nenhum.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from app.models.enums import Papel, StatusUsuario
from app.models.mensagem import Mensagem
from app.models.usuario import Usuario

PODE_FALAR_COM: dict[Papel, set[Papel]] = {
    Papel.SINDICO: {Papel.PORTEIRO, Papel.MORADOR},
    Papel.PORTEIRO: {Papel.SINDICO, Papel.PORTEIRO, Papel.MORADOR},
    Papel.MORADOR: {Papel.SINDICO, Papel.PORTEIRO},
}
LIMITE_CONVERSA = 200


def _contatos_query(usuario: Usuario):
    return select(Usuario).where(
        Usuario.condominio_id == usuario.condominio_id,
        Usuario.id != usuario.id,
        Usuario.status == StatusUsuario.ATIVO,
        Usuario.papel.in_(PODE_FALAR_COM.get(usuario.papel, set())),
    )


def contato_permitido(db: Session, usuario: Usuario, outro_id: int) -> Usuario | None:
    """O outro usuário, se a conversa for permitida; None em qualquer outro caso.

    A rota responde 404 tanto para "não existe" quanto para "não pode": dizer
    a diferença revelaria quem está cadastrado em outro condomínio.
    """
    if usuario.condominio_id is None:
        return None
    return db.scalar(_contatos_query(usuario).where(Usuario.id == outro_id))


def _entre(a: int, b: int):
    return or_(
        and_(Mensagem.remetente_id == a, Mensagem.destinatario_id == b),
        and_(Mensagem.remetente_id == b, Mensagem.destinatario_id == a),
    )


def listar_contatos(db: Session, usuario: Usuario) -> list[dict]:
    pessoas = db.scalars(_contatos_query(usuario).options(selectinload(Usuario.unidade))).all()
    if not pessoas:
        return []

    nao_lidas = dict(db.execute(
        select(Mensagem.remetente_id, func.count())
        .where(Mensagem.destinatario_id == usuario.id, Mensagem.lida_em.is_(None))
        .group_by(Mensagem.remetente_id)
    ).all())

    # A última mensagem de cada conversa: o maior id entre as duas pessoas.
    outro = func.greatest(Mensagem.remetente_id, Mensagem.destinatario_id) + \
        func.least(Mensagem.remetente_id, Mensagem.destinatario_id) - usuario.id
    ultimas_ids = [
        linha[0] for linha in db.execute(
            select(func.max(Mensagem.id))
            .where(or_(Mensagem.remetente_id == usuario.id, Mensagem.destinatario_id == usuario.id))
            .group_by(outro)
        ).all()
    ]
    ultimas = {}
    if ultimas_ids:
        for m in db.scalars(select(Mensagem).where(Mensagem.id.in_(ultimas_ids))):
            par = m.destinatario_id if m.remetente_id == usuario.id else m.remetente_id
            ultimas[par] = m

    saida = []
    for p in pessoas:
        ultima = ultimas.get(p.id)
        saida.append({
            "id": p.id, "nome": p.nome, "papel": p.papel, "telefone": p.telefone,
            "foto_url": p.foto_url,
            # Com o bloco: em condomínio de vários blocos há mais de um "101".
            "unidade": p.unidade.identificacao if p.unidade else None,
            "nao_lidas": nao_lidas.get(p.id, 0),
            "ultima_mensagem": ultima.texto[:120] if ultima else None,
            "ultima_em": ultima.enviada_em if ultima else None,
        })
    # Conversas com movimento primeiro, das mais recentes; depois por nome.
    saida.sort(key=lambda c: (c["ultima_em"] is None,
                              -(c["ultima_em"].timestamp()) if c["ultima_em"] else 0,
                              c["nome"].lower()))
    return saida


def conversa(db: Session, usuario: Usuario, outro: Usuario, depois_de: int | None) -> list[Mensagem]:
    """As mensagens das duas pessoas, e marca como lidas as recebidas."""
    consulta = select(Mensagem).where(_entre(usuario.id, outro.id))
    if depois_de:
        consulta = consulta.where(Mensagem.id > depois_de)
        mensagens = db.scalars(consulta.order_by(Mensagem.id).limit(LIMITE_CONVERSA)).all()
    else:
        mensagens = list(reversed(db.scalars(
            consulta.order_by(Mensagem.id.desc()).limit(LIMITE_CONVERSA)
        ).all()))

    db.execute(
        update(Mensagem)
        .where(Mensagem.remetente_id == outro.id, Mensagem.destinatario_id == usuario.id,
               Mensagem.lida_em.is_(None))
        .values(lida_em=datetime.now(timezone.utc))
    )
    db.commit()
    return mensagens


def enviar(db: Session, usuario: Usuario, outro: Usuario, texto: str) -> Mensagem:
    m = Mensagem(condominio_id=usuario.condominio_id, remetente_id=usuario.id,
                 destinatario_id=outro.id, texto=texto)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def total_nao_lidas(db: Session, usuario: Usuario) -> int:
    return db.scalar(
        select(func.count()).select_from(Mensagem)
        .where(Mensagem.destinatario_id == usuario.id, Mensagem.lida_em.is_(None))
    ) or 0

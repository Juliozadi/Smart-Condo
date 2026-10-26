"""Controle de chaves na portaria.

A portaria guarda a chave do salão, da piscina, da casa de máquinas — e a
do apartamento que o morador deixa para a diarista ou para o eletricista.
Ninguém sabia quem tinha levado a chave do salão, e a chave de um
apartamento entregue à pessoa errada é a porta aberta para um furto.
Cada retirada fica registrada; a chave do apartamento só sai para quem
mora lá ou para quem o morador autorizou (com o CPF conferido), e o
apartamento fica sabendo quando ela sai e quando volta.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import conferir_que_mora, exigir_papel
from app.core.database import get_db
from app.core.tempo import agora_local, hoje_local
from app.models.chave import Chave, MovimentacaoChave
from app.models.condominio import Unidade
from app.models.enums import CanalVerificacao, Papel, StatusUsuario
from app.models.portaria import AutorizacaoVisita
from app.models.usuario import Usuario
from app.schemas.chave import (
    ChaveAtualizacao, ChaveEntrada, ChaveSaida, MovimentacaoSaida, QuemPodeRetirar,
    RetiradaEntrada,
)
from app.schemas.comuns import Mensagem
from app.services import notificacao
from app.services.visitas import autorizador_mora_la, documento_mascarado, vale_no_dia

router = APIRouter(prefix="/chaves", tags=["Chaves"])

equipe = exigir_papel(Papel.PORTEIRO, Papel.SINDICO)
quem_ve = exigir_papel(Papel.PORTEIRO, Papel.SINDICO, Papel.MORADOR)

SO_QUEM_PODE = ("A chave do apartamento só sai para quem mora lá ou para quem o morador "
                "autorizou a retirá-la.")


def _hora(momento: datetime) -> str:
    return momento.astimezone(agora_local().tzinfo).strftime("%d/%m às %Hh%M")


def _fora(db: Session, chave_ids: list[int]) -> dict[int, MovimentacaoChave]:
    if not chave_ids:
        return {}
    abertas = db.scalars(select(MovimentacaoChave).where(
        MovimentacaoChave.chave_id.in_(chave_ids), MovimentacaoChave.devolvida_em.is_(None))).all()
    return {m.chave_id: m for m in abertas}


def _saida(c: Chave, aberta: MovimentacaoChave | None) -> ChaveSaida:
    return ChaveSaida(
        id=c.id, nome=c.nome, unidade_id=c.unidade_id,
        unidade=c.unidade.identificacao if c.unidade else None,
        posicao=c.posicao, observacao=c.observacao, na_portaria=aberta is None,
        com=aberta.retirada_por_nome if aberta else None,
        retirada_em=aberta.retirada_em if aberta else None,
    )


def _chave(db: Session, chave_id: int, usuario: Usuario, travar: bool = False) -> Chave:
    consulta = select(Chave).options(selectinload(Chave.unidade)).where(Chave.id == chave_id)
    if travar:
        # Duas portarias entregando a mesma chave ao mesmo tempo: a segunda
        # espera a primeira e encontra a chave fora.
        consulta = consulta.with_for_update(of=Chave)
    c = db.scalar(consulta)
    if c is None or c.condominio_id != usuario.condominio_id or c.inativo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chave não encontrada.")
    if usuario.papel == Papel.MORADOR and c.unidade_id != usuario.unidade_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chave não encontrada.")
    return c


def _conferir_nome(db: Session, condominio_id: int, nome: str, exceto: int | None = None) -> None:
    consulta = select(Chave.id).where(Chave.condominio_id == condominio_id,
                                      Chave.inativo_em.is_(None),
                                      func.lower(Chave.nome) == nome.lower())
    if exceto is not None:
        consulta = consulta.where(Chave.id != exceto)
    if db.scalar(consulta) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Já existe uma chave chamada \"{nome}\" no quadro.")


def _moradores(db: Session, unidade_id: int) -> list[Usuario]:
    """Quem mora no apartamento — o dono que não mora não leva a chave."""
    return list(db.scalars(select(Usuario).where(
        Usuario.unidade_id == unidade_id, Usuario.papel == Papel.MORADOR,
        Usuario.status == StatusUsuario.ATIVO, Usuario.reside.is_(True),
    ).order_by(Usuario.nome)).all())


def _avisar(db: Session, chave: Chave, titulo: str, mensagem: str) -> None:
    if chave.unidade_id is None:
        return
    for m in _moradores(db, chave.unidade_id):
        notificacao.notificar(m.email, CanalVerificacao.EMAIL, titulo, mensagem)


@router.get("", response_model=list[ChaveSaida], summary="O quadro de chaves")
def listar(usuario: Usuario = Depends(quem_ve), db: Session = Depends(get_db)) -> list[ChaveSaida]:
    consulta = (select(Chave).options(selectinload(Chave.unidade))
                .where(Chave.condominio_id == usuario.condominio_id, Chave.inativo_em.is_(None)))
    if usuario.papel == Papel.MORADOR:
        conferir_que_mora(usuario)
        consulta = consulta.where(Chave.unidade_id == usuario.unidade_id)
    chaves = db.scalars(consulta.order_by(Chave.unidade_id.is_not(None), Chave.nome)).all()
    fora = _fora(db, [c.id for c in chaves])
    return [_saida(c, fora.get(c.id)) for c in chaves]


@router.post("", response_model=ChaveSaida, status_code=status.HTTP_201_CREATED,
             summary="Põe uma chave no quadro")
def criar(dados: ChaveEntrada, usuario: Usuario = Depends(equipe),
          db: Session = Depends(get_db)) -> ChaveSaida:
    if dados.unidade_id is not None:
        unidade = db.get(Unidade, dados.unidade_id)
        if unidade is None or unidade.condominio_id != usuario.condominio_id or unidade.pendente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Apartamento não encontrado.")
    _conferir_nome(db, usuario.condominio_id, dados.nome)
    c = Chave(**dados.model_dump(), condominio_id=usuario.condominio_id)
    db.add(c)
    db.commit()
    c = _chave(db, c.id, usuario)
    return _saida(c, None)


@router.put("/{chave_id}", response_model=ChaveSaida, summary="Corrige o nome, a posição ou a observação")
def editar(chave_id: int, dados: ChaveAtualizacao, usuario: Usuario = Depends(equipe),
           db: Session = Depends(get_db)) -> ChaveSaida:
    c = _chave(db, chave_id, usuario, travar=True)
    novos = {campo: getattr(dados, campo) for campo in dados.model_fields_set}
    if "nome" in novos:
        if novos["nome"] is None:
            raise HTTPException(status_code=422, detail="Informe o nome da chave.")
        _conferir_nome(db, usuario.condominio_id, novos["nome"], exceto=c.id)
    for campo, valor in novos.items():
        setattr(c, campo, valor)
    db.commit()
    c = _chave(db, c.id, usuario)
    return _saida(c, _fora(db, [c.id]).get(c.id))


@router.delete("/{chave_id}", response_model=Mensagem, summary="Tira a chave do quadro (inativa)")
def remover(chave_id: int, usuario: Usuario = Depends(equipe),
            db: Session = Depends(get_db)) -> Mensagem:
    c = _chave(db, chave_id, usuario, travar=True)
    if _fora(db, [c.id]):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="A chave está fora: registre a devolução antes de removê-la.")
    c.inativo_em = datetime.now(timezone.utc)
    c.inativado_por_id = usuario.id
    db.commit()
    return Mensagem(detalhe=f"\"{c.nome}\" saiu do quadro; o histórico fica guardado.")


@router.get("/{chave_id}/quem-pode-retirar", response_model=list[QuemPodeRetirar],
            summary="Quem pode levar a chave do apartamento, hoje")
def quem_pode_retirar(chave_id: int, usuario: Usuario = Depends(equipe),
                      db: Session = Depends(get_db)) -> list[QuemPodeRetirar]:
    c = _chave(db, chave_id, usuario)
    if c.unidade_id is None:
        return []
    lista = [QuemPodeRetirar(tipo="morador", id=m.id, nome=m.nome)
             for m in _moradores(db, c.unidade_id)]
    hoje = hoje_local()
    autorizacoes = db.scalars(select(AutorizacaoVisita).where(
        AutorizacaoVisita.unidade_id == c.unidade_id, AutorizacaoVisita.pode_retirar_chave.is_(True),
        AutorizacaoVisita.inativo_em.is_(None), autorizador_mora_la(),
    ).order_by(AutorizacaoVisita.nome)).all()
    lista += [QuemPodeRetirar(tipo="autorizacao", id=a.id, nome=a.nome, detalhe=a.tipo,
                              documento=documento_mascarado(a.documento))
              for a in autorizacoes if vale_no_dia(a, hoje)]
    return lista


@router.post("/{chave_id}/retirada", response_model=MovimentacaoSaida,
             status_code=status.HTTP_201_CREATED, summary="Registra quem levou a chave")
def retirar(chave_id: int, dados: RetiradaEntrada, usuario: Usuario = Depends(equipe),
            db: Session = Depends(get_db)) -> MovimentacaoSaida:
    c = _chave(db, chave_id, usuario, travar=True)
    if _fora(db, [c.id]):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"A chave \"{c.nome}\" já está fora. Registre a devolução antes.")

    m = MovimentacaoChave(chave_id=c.id, retirada_registrada_por_id=usuario.id,
                          observacao=dados.observacao)
    if c.unidade_id is None:
        if not dados.nome:
            raise HTTPException(status_code=422, detail="Informe o nome de quem leva a chave.")
        m.retirada_por_nome, m.retirada_por_documento = dados.nome, dados.documento
    elif dados.morador_id is not None:
        morador = next((x for x in _moradores(db, c.unidade_id) if x.id == dados.morador_id), None)
        if morador is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=SO_QUEM_PODE)
        m.retirada_por_nome, m.morador_id = morador.nome, morador.id
    elif dados.autorizacao_id is not None:
        a = db.scalar(select(AutorizacaoVisita).where(
            AutorizacaoVisita.id == dados.autorizacao_id, autorizador_mora_la()))
        documento = re.sub(r"\D", "", dados.documento or "")
        if (a is None or a.unidade_id != c.unidade_id or not a.pode_retirar_chave
                or not vale_no_dia(a, hoje_local())):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=SO_QUEM_PODE)
        if not a.documento or documento != a.documento:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="O documento apresentado não confere com o da autorização.")
        m.retirada_por_nome, m.retirada_por_documento, m.autorizacao_id = a.nome, a.documento, a.id
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=SO_QUEM_PODE)

    db.add(m)
    db.commit()
    db.refresh(m)
    _avisar(db, c, "Chave do apartamento retirada",
            f"A chave \"{c.nome}\" foi retirada na portaria por {m.retirada_por_nome}, "
            f"em {_hora(m.retirada_em)}.")
    return _movimentacao_saida(db, m, usuario)


@router.post("/{chave_id}/devolucao", response_model=MovimentacaoSaida,
             summary="Registra que a chave voltou")
def devolver(chave_id: int, usuario: Usuario = Depends(equipe),
             db: Session = Depends(get_db)) -> MovimentacaoSaida:
    c = _chave(db, chave_id, usuario, travar=True)
    m = _fora(db, [c.id]).get(c.id)
    if m is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"A chave \"{c.nome}\" já está na portaria.")
    m.devolvida_em = datetime.now(timezone.utc)
    m.devolucao_registrada_por_id = usuario.id
    db.commit()
    db.refresh(m)
    _avisar(db, c, "Chave do apartamento devolvida",
            f"A chave \"{c.nome}\" voltou para a portaria em {_hora(m.devolvida_em)}.")
    return _movimentacao_saida(db, m, usuario)


def _movimentacao_saida(db: Session, m: MovimentacaoChave, usuario: Usuario) -> MovimentacaoSaida:
    registrou = db.get(Usuario, m.retirada_registrada_por_id) if m.retirada_registrada_por_id else None
    recebeu = (db.get(Usuario, m.devolucao_registrada_por_id)
               if m.devolucao_registrada_por_id else None)
    documento = m.retirada_por_documento
    if usuario.papel == Papel.MORADOR:
        # O morador reconhece quem levou pelo nome; o documento inteiro fica
        # com a portaria e o síndico.
        documento = documento_mascarado(documento) if documento and documento.isdigit() else None
    return MovimentacaoSaida(
        id=m.id, retirada_por_nome=m.retirada_por_nome, retirada_por_documento=documento,
        retirada_em=m.retirada_em,
        retirada_registrada_por_nome=registrou.nome if registrou else None,
        devolvida_em=m.devolvida_em,
        devolucao_registrada_por_nome=recebeu.nome if recebeu else None,
        observacao=m.observacao,
    )


@router.get("/{chave_id}/movimentacoes", response_model=list[MovimentacaoSaida],
            summary="Quem levou a chave, e quando")
def movimentacoes(chave_id: int, usuario: Usuario = Depends(quem_ve),
                  db: Session = Depends(get_db)) -> list[MovimentacaoSaida]:
    if usuario.papel == Papel.MORADOR:
        conferir_que_mora(usuario)
    c = _chave(db, chave_id, usuario)
    consulta = select(MovimentacaoChave).where(MovimentacaoChave.chave_id == c.id)
    if usuario.papel == Papel.MORADOR:
        # Quem chega ao apartamento não vê o histórico de antes dele.
        consulta = consulta.where(MovimentacaoChave.retirada_em >= usuario.unidade_desde)
    lista = db.scalars(consulta.order_by(MovimentacaoChave.retirada_em.desc(),
                                         MovimentacaoChave.id.desc()).limit(200)).all()
    return [_movimentacao_saida(db, m, usuario) for m in lista]

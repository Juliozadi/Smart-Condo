"""Chat entre síndico, porteiros e moradores.

Documentação, seção 13.5.2: o síndico pode contatar os porteiros "por
chat ou ligação de voz". A ligação é feita pelo telefone cadastrado, que
vem na lista de contatos; o chat é este.

A tela consulta as rotas a cada poucos segundos enquanto a conversa está
aberta. É mais simples que uma conexão permanente e basta para o volume
de mensagens de um condomínio.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import exigir_papel
from app.core.database import get_db
from app.models.enums import Papel
from app.models.usuario import Usuario
from app.schemas.mensagem import ContatoSaida, MensagemEntrada, MensagemSaida, NaoLidasSaida
from app.services import mensagens as servico

router = APIRouter(prefix="/mensagens", tags=["Mensagens"])

participante = exigir_papel(Papel.SINDICO, Papel.PORTEIRO, Papel.MORADOR)
NAO_ENCONTRADO = HTTPException(status_code=404, detail="Contato não encontrado.")


def _saida(m, usuario: Usuario) -> MensagemSaida:
    s = MensagemSaida.model_validate(m)
    s.minha = m.remetente_id == usuario.id
    return s


@router.get("/contatos", response_model=list[ContatoSaida], summary="Com quem posso conversar")
def contatos(usuario: Usuario = Depends(participante), db: Session = Depends(get_db)):
    return servico.listar_contatos(db, usuario)


@router.get("/nao-lidas", response_model=NaoLidasSaida, summary="Total de mensagens não lidas")
def nao_lidas(usuario: Usuario = Depends(participante), db: Session = Depends(get_db)):
    return {"total": servico.total_nao_lidas(db, usuario)}


@router.get("/com/{outro_id}", response_model=list[MensagemSaida], summary="Conversa com uma pessoa")
def conversa(
    outro_id: int,
    depois_de: int | None = Query(default=None, ge=1, description="Só as mensagens depois deste id"),
    usuario: Usuario = Depends(participante),
    db: Session = Depends(get_db),
):
    outro = servico.contato_permitido(db, usuario, outro_id)
    if outro is None:
        raise NAO_ENCONTRADO
    return [_saida(m, usuario) for m in servico.conversa(db, usuario, outro, depois_de)]


@router.post("/com/{outro_id}", response_model=MensagemSaida,
             status_code=status.HTTP_201_CREATED, summary="Envia uma mensagem")
def enviar(
    outro_id: int,
    dados: MensagemEntrada,
    usuario: Usuario = Depends(participante),
    db: Session = Depends(get_db),
):
    outro = servico.contato_permitido(db, usuario, outro_id)
    if outro is None:
        raise NAO_ENCONTRADO
    return _saida(servico.enviar(db, usuario, outro, dados.texto), usuario)

"""Achados e perdidos da portaria.

A portaria (com a permissão de registrar encomendas, que já cobre o que
fica guardado na portaria) e o síndico registram o que foi achado; os
moradores veem o que está guardado e dizem "é meu"; a entrega registra o
nome de quem retirou, e quem reclamou recebe o aviso — se não foi ele,
fica sabendo na hora. Passado o prazo de guarda, o que ninguém reclamou
o síndico doa ou descarta, com o destino anotado.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import exigir_papel, exigir_permissao_do_porteiro, exigir_permissao_porteiro
from app.core.database import get_db
from app.core.tempo import agora_utc, dia_e_hora, hoje_local
from app.models.achado import Achado
from app.models.enums import Papel, StatusAchado
from app.models.usuario import Usuario
from app.schemas.achado import AchadoEntrada, AchadoSaida, DescarteEntrada, DevolucaoEntrada
from app.services import destinatarios, registro

router = APIRouter(prefix="/achados", tags=["Achados e perdidos"])

PERMISSAO = "registrar_encomendas"
PRAZO_GUARDA_DIAS = 30
quem_ve = exigir_papel(Papel.PORTEIRO, Papel.SINDICO, Papel.MORADOR)
equipe = exigir_permissao_porteiro(PERMISSAO)
so_morador = exigir_papel(Papel.MORADOR)
so_sindico = exigir_papel(Papel.SINDICO)
_hoje = hoje_local
_agora = agora_utc


def _nome(u: Usuario | None) -> str | None:
    if u is None:
        return None
    if u.unidade is not None:
        return f"{u.nome} — apto {u.unidade.identificacao}"
    return u.nome


def _saida(a: Achado, usuario: Usuario) -> AchadoSaida:
    equipe_ve = usuario.papel != Papel.MORADOR
    meu = a.reclamado_por_id == usuario.id
    guardado = a.status == StatusAchado.GUARDADO
    dias = (_hoje() - a.encontrado_em).days
    saida = AchadoSaida(
        id=a.id, descricao=a.descricao, local=a.local, encontrado_em=a.encontrado_em,
        status=a.status, dias_guardado=dias, reclamado=a.reclamado_por_id is not None,
        reclamado_por_mim=meu, reclamado_em=a.reclamado_em if (equipe_ve or meu) else None,
        devolvido_em=a.devolvido_em if (equipe_ve or meu) else None,
        entregue_a=a.entregue_a if (equipe_ve or meu) else None,
    )
    if equipe_ve:
        saida.registrado_por = a.registrado_por.nome if a.registrado_por else None
        saida.reclamado_por = _nome(a.reclamado_por)
        saida.descartado_em = a.descartado_em
        saida.destino = a.destino
        saida.pode_devolver = guardado
        saida.pode_descartar = (guardado and usuario.papel == Papel.SINDICO
                                and a.reclamado_por_id is None and dias >= PRAZO_GUARDA_DIAS)
    else:
        saida.pode_reclamar = guardado and a.reclamado_por_id is None
        saida.pode_desistir = guardado and meu
    return saida


def _achado(db: Session, achado_id: int, usuario: Usuario, travar: bool = False) -> Achado:
    consulta = select(Achado).options(
        selectinload(Achado.registrado_por), selectinload(Achado.reclamado_por),
    ).where(Achado.id == achado_id)
    if travar:
        # Duas portarias entregando o mesmo objeto, ou dois moradores
        # dizendo "é meu" ao mesmo tempo: o segundo espera e vê o resultado.
        consulta = consulta.with_for_update(of=Achado)
    a = db.scalar(consulta)
    if a is None or a.condominio_id != usuario.condominio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objeto não encontrado.")
    if (usuario.papel == Papel.MORADOR and a.status != StatusAchado.GUARDADO
            and a.reclamado_por_id != usuario.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objeto não encontrado.")
    return a


def _guardado(a: Achado) -> None:
    if a.status != StatusAchado.GUARDADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este objeto já foi entregue." if a.status == StatusAchado.DEVOLVIDO
            else "Este objeto já foi doado ou descartado.")


@router.get("", response_model=list[AchadoSaida], summary="Lista os achados e perdidos")
def listar(
    situacao: StatusAchado | None = Query(default=None, alias="status"),
    usuario: Usuario = Depends(quem_ve),
    db: Session = Depends(get_db),
) -> list[AchadoSaida]:
    exigir_permissao_do_porteiro(db, usuario, PERMISSAO)
    consulta = select(Achado).options(
        selectinload(Achado.registrado_por),
        selectinload(Achado.reclamado_por).selectinload(Usuario.unidade),
    ).where(Achado.condominio_id == usuario.condominio_id)
    if usuario.papel == Papel.MORADOR:
        # O morador vê o que está guardado e o que ele mesmo reclamou.
        consulta = consulta.where((Achado.status == StatusAchado.GUARDADO)
                                  | (Achado.reclamado_por_id == usuario.id))
    if situacao is not None:
        consulta = consulta.where(Achado.status == situacao)
    primeiro_guardados = case((Achado.status == StatusAchado.GUARDADO, 0), else_=1)
    achados = db.scalars(consulta.order_by(
        primeiro_guardados, Achado.encontrado_em.desc(), Achado.id.desc())).all()
    return [_saida(a, usuario) for a in achados]


@router.post("", response_model=AchadoSaida, status_code=status.HTTP_201_CREATED,
             summary="Registra um objeto achado")
def registrar_achado(
    dados: AchadoEntrada,
    usuario: Usuario = Depends(equipe),
    db: Session = Depends(get_db),
) -> AchadoSaida:
    a = Achado(condominio_id=usuario.condominio_id, registrado_por_id=usuario.id,
               descricao=dados.descricao, local=dados.local, encontrado_em=dados.encontrado_em,
               status=StatusAchado.GUARDADO)
    db.add(a)
    db.flush()
    registro.registrar(db, usuario, registro.CRIOU, registro.ACHADO, a.id)
    db.commit()
    return _saida(_achado(db, a.id, usuario), usuario)


@router.post("/{achado_id}/reclamacao", response_model=AchadoSaida,
             summary="O morador diz que o objeto é dele")
def reclamar(
    achado_id: int,
    morador: Usuario = Depends(so_morador),
    db: Session = Depends(get_db),
) -> AchadoSaida:
    a = _achado(db, achado_id, morador, travar=True)
    _guardado(a)
    if a.reclamado_por_id not in (None, morador.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Outro morador já disse que este objeto é dele. Procure a portaria.")
    if a.reclamado_por_id is None:
        a.reclamado_por_id = morador.id
        a.reclamado_em = _agora()
        db.commit()
    return _saida(_achado(db, achado_id, morador), morador)


@router.delete("/{achado_id}/reclamacao", response_model=AchadoSaida,
               summary="O morador desfaz o \"é meu\"")
def desistir(
    achado_id: int,
    morador: Usuario = Depends(so_morador),
    db: Session = Depends(get_db),
) -> AchadoSaida:
    a = _achado(db, achado_id, morador, travar=True)
    _guardado(a)
    if a.reclamado_por_id != morador.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Você não disse que este objeto é seu.")
    a.reclamado_por_id = None
    a.reclamado_em = None
    db.commit()
    return _saida(_achado(db, achado_id, morador), morador)


@router.post("/{achado_id}/devolucao", response_model=AchadoSaida,
             summary="Entrega o objeto a quem é dono")
def devolver(
    achado_id: int,
    dados: DevolucaoEntrada,
    usuario: Usuario = Depends(equipe),
    db: Session = Depends(get_db),
) -> AchadoSaida:
    a = _achado(db, achado_id, usuario, travar=True)
    _guardado(a)
    a.status = StatusAchado.DEVOLVIDO
    a.devolvido_em = _agora()
    a.devolvido_por_id = usuario.id
    a.entregue_a = dados.entregue_a
    registro.registrar(db, usuario, registro.EDITOU, registro.ACHADO, a.id,
                       f"Entregue a {dados.entregue_a}")
    reclamou = a.reclamado_por
    texto = (f"{a.descricao} foi entregue a {dados.entregue_a} em {dia_e_hora(a.devolvido_em)}. "
             "Se não foi você quem retirou, avise a portaria.")
    db.commit()
    if reclamou is not None:
        # Quem disse "é meu" fica sabendo da entrega — inclusive se outra
        # pessoa retirou no lugar dele.
        destinatarios.avisar([reclamou], "Achados e perdidos", texto)
    return _saida(_achado(db, achado_id, usuario), usuario)


@router.post("/{achado_id}/descarte", response_model=AchadoSaida,
             summary="Doa ou descarta o que ninguém reclamou")
def descartar(
    achado_id: int,
    dados: DescarteEntrada,
    sindico: Usuario = Depends(so_sindico),
    db: Session = Depends(get_db),
) -> AchadoSaida:
    a = _achado(db, achado_id, sindico, travar=True)
    _guardado(a)
    if a.reclamado_por_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Um morador disse que este objeto é dele: entregue a ele antes de doar.")
    dias = (_hoje() - a.encontrado_em).days
    if dias < PRAZO_GUARDA_DIAS:
        faltam = PRAZO_GUARDA_DIAS - dias
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Guarde por {PRAZO_GUARDA_DIAS} dias antes de doar ou descartar: "
                   f"falta{'m' if faltam > 1 else ''} {faltam} dia{'s' if faltam > 1 else ''}.")
    a.status = StatusAchado.DESCARTADO
    a.descartado_em = _agora()
    a.descartado_por_id = sindico.id
    a.destino = dados.destino
    registro.registrar(db, sindico, registro.INATIVOU, registro.ACHADO, a.id, dados.destino)
    db.commit()
    return _saida(_achado(db, achado_id, sindico), sindico)

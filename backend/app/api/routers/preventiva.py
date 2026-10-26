"""Manutenção preventiva e obrigações com vencimento.

O AVCB vence e o seguro não cobre o incêndio; a recarga dos extintores
passa do prazo e a fiscalização multa; a caixa d'água fica um ano sem
limpeza. O síndico controlava numa planilha — ou na memória. Cada plano
tem a periodicidade e o próximo vencimento; o painel avisa o que venceu
ou está para vencer, e registrar a realização renova o prazo (e pode
lançar a despesa na prestação de contas).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import exigir_papel
from app.core.database import get_db
from app.core.tempo import hoje_local, somar_meses
from app.models.enums import CategoriaDespesa, Papel
from app.models.financeiro import Despesa
from app.models.preventiva import PlanoManutencao, RealizacaoManutencao
from app.models.usuario import Usuario
from app.schemas.comuns import Mensagem
from app.schemas.preventiva import (
    PlanoAtualizacao, PlanoEntrada, PlanoSaida, RealizacaoEntrada, RealizacaoSaida,
)
from app.services import registro

router = APIRouter(prefix="/manutencao-preventiva", tags=["Manutenção preventiva"])

sindico = exigir_papel(Papel.SINDICO)

ROTULOS = {
    "nome": "nome", "periodicidade_meses": "periodicidade",
    "proximo_vencimento": "próximo vencimento", "antecedencia_aviso_dias": "aviso",
    "fornecedor": "fornecedor", "observacao": "observação",
}


def _hoje() -> date:
    return hoje_local()


def _saida(p: PlanoManutencao, hoje: date) -> PlanoSaida:
    dias = (p.proximo_vencimento - hoje).days
    situacao = ("vencida" if dias < 0
                else "vence_em_breve" if dias <= p.antecedencia_aviso_dias else "em_dia")
    return PlanoSaida(
        id=p.id, nome=p.nome, periodicidade_meses=p.periodicidade_meses,
        proximo_vencimento=p.proximo_vencimento, antecedencia_aviso_dias=p.antecedencia_aviso_dias,
        fornecedor=p.fornecedor, observacao=p.observacao, ultima_realizacao=p.ultima_realizacao,
        situacao=situacao, dias_para_vencer=dias,
    )


def _realizacao_saida(r: RealizacaoManutencao) -> RealizacaoSaida:
    return RealizacaoSaida(
        id=r.id, data=r.data, custo=r.custo, observacao=r.observacao,
        registrada_por_nome=r.registrada_por.nome if r.registrada_por else None,
        despesa_id=r.despesa_id, criado_em=r.criado_em,
    )


def _plano(db: Session, plano_id: int, usuario: Usuario, travar: bool = False) -> PlanoManutencao:
    consulta = select(PlanoManutencao).where(PlanoManutencao.id == plano_id)
    if travar:
        consulta = consulta.with_for_update()
    p = db.scalar(consulta)
    if p is None or p.condominio_id != usuario.condominio_id or p.inativo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Plano de manutenção não encontrado.")
    return p


def _conferir_nome(db: Session, condominio_id: int, nome: str, exceto: int | None = None) -> None:
    consulta = select(PlanoManutencao.id).where(
        PlanoManutencao.condominio_id == condominio_id, PlanoManutencao.inativo_em.is_(None),
        func.lower(PlanoManutencao.nome) == nome.lower(),
    )
    if exceto is not None:
        consulta = consulta.where(PlanoManutencao.id != exceto)
    if db.scalar(consulta) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Já existe um plano chamado \"{nome}\".")


@router.get("", response_model=list[PlanoSaida],
            summary="Os planos, do que vence primeiro ao que vence por último")
def listar(usuario: Usuario = Depends(sindico), db: Session = Depends(get_db)) -> list[PlanoSaida]:
    planos = db.scalars(
        select(PlanoManutencao).where(PlanoManutencao.condominio_id == usuario.condominio_id,
                                      PlanoManutencao.inativo_em.is_(None))
        .order_by(PlanoManutencao.proximo_vencimento, PlanoManutencao.id)
    ).all()
    hoje = _hoje()
    return [_saida(p, hoje) for p in planos]


@router.post("", response_model=PlanoSaida, status_code=status.HTTP_201_CREATED,
             summary="Cadastra o que vence de tempos em tempos")
def criar(dados: PlanoEntrada, usuario: Usuario = Depends(sindico),
          db: Session = Depends(get_db)) -> PlanoSaida:
    _conferir_nome(db, usuario.condominio_id, dados.nome)
    p = PlanoManutencao(**dados.model_dump(), condominio_id=usuario.condominio_id)
    db.add(p)
    db.flush()
    registro.registrar(db, usuario, registro.CRIOU, registro.PLANO_MANUTENCAO, p.id, p.nome)
    db.commit()
    db.refresh(p)
    return _saida(p, _hoje())


@router.put("/{plano_id}", response_model=PlanoSaida, summary="Corrige um plano")
def editar(plano_id: int, dados: PlanoAtualizacao, usuario: Usuario = Depends(sindico),
           db: Session = Depends(get_db)) -> PlanoSaida:
    p = _plano(db, plano_id, usuario, travar=True)
    novos = {campo: getattr(dados, campo) for campo in dados.model_fields_set}
    # Só fornecedor e observação podem ficar vazios.
    for campo in ("nome", "periodicidade_meses", "proximo_vencimento", "antecedencia_aviso_dias"):
        if campo in novos and novos[campo] is None:
            raise HTTPException(status_code=422, detail=f"Informe o {ROTULOS[campo]}.")
    if "nome" in novos:
        _conferir_nome(db, usuario.condominio_id, novos["nome"], exceto=p.id)
    descricao = registro.campos_alterados(p, novos, ROTULOS)
    for campo, valor in novos.items():
        setattr(p, campo, valor)
    if descricao:
        registro.registrar(db, usuario, registro.EDITOU, registro.PLANO_MANUTENCAO, p.id, descricao)
    db.commit()
    db.refresh(p)
    return _saida(p, _hoje())


@router.delete("/{plano_id}", response_model=Mensagem, summary="Remove um plano (inativa)")
def remover(plano_id: int, usuario: Usuario = Depends(sindico),
            db: Session = Depends(get_db)) -> Mensagem:
    p = _plano(db, plano_id, usuario, travar=True)
    p.inativo_em = datetime.now(timezone.utc)
    p.inativado_por_id = usuario.id
    registro.registrar(db, usuario, registro.INATIVOU, registro.PLANO_MANUTENCAO, p.id, p.nome)
    db.commit()
    return Mensagem(detalhe=f"\"{p.nome}\" saiu da manutenção preventiva; o histórico fica guardado.")


@router.post("/{plano_id}/realizacoes", response_model=RealizacaoSaida,
             status_code=status.HTTP_201_CREATED,
             summary="Registra que foi feito; renova o vencimento")
def realizar(plano_id: int, dados: RealizacaoEntrada, usuario: Usuario = Depends(sindico),
             db: Session = Depends(get_db)) -> RealizacaoSaida:
    p = _plano(db, plano_id, usuario, travar=True)
    r = RealizacaoManutencao(plano_id=p.id, data=dados.data, custo=dados.custo,
                             observacao=dados.observacao, registrada_por_id=usuario.id)
    if dados.lancar_despesa:
        despesa = Despesa(
            condominio_id=usuario.condominio_id, lancada_por_id=usuario.id,
            categoria=CategoriaDespesa.MANUTENCAO, descricao=f"{p.nome} (manutenção preventiva)"[:180],
            valor=dados.custo, data=dados.data, fornecedor=p.fornecedor,
        )
        db.add(despesa)
        db.flush()
        registro.registrar(db, usuario, registro.CRIOU, registro.DESPESA, despesa.id,
                           f"Da manutenção preventiva: {p.nome}")
        r.despesa_id = despesa.id
    # Só a realização mais recente renova o prazo: lançar depois uma antiga
    # (esquecida) não faz o vencimento voltar.
    if p.ultima_realizacao is None or dados.data >= p.ultima_realizacao:
        p.ultima_realizacao = dados.data
        p.proximo_vencimento = somar_meses(dados.data, p.periodicidade_meses)
    db.add(r)
    db.flush()
    registro.registrar(db, usuario, registro.EDITOU, registro.PLANO_MANUTENCAO, p.id,
                       f"Realizado em {dados.data:%d/%m/%Y}")
    db.commit()
    db.refresh(r)
    return _realizacao_saida(r)


@router.get("/{plano_id}/realizacoes", response_model=list[RealizacaoSaida],
            summary="O histórico de um plano, da mais recente à mais antiga")
def historico(plano_id: int, usuario: Usuario = Depends(sindico),
              db: Session = Depends(get_db)) -> list[RealizacaoSaida]:
    p = _plano(db, plano_id, usuario)
    lista = db.scalars(
        select(RealizacaoManutencao).options(selectinload(RealizacaoManutencao.registrada_por))
        .where(RealizacaoManutencao.plano_id == p.id)
        .order_by(RealizacaoManutencao.data.desc(), RealizacaoManutencao.id.desc()).limit(200)
    ).all()
    return [_realizacao_saida(r) for r in lista]

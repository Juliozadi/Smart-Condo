"""Prestação de contas: despesas do condomínio e balancete do mês.

Código Civil, art. 1.348, VIII: compete ao síndico prestar contas. O
sistema registrava só o que entrava (os pagamentos); aqui o síndico lança
o que sai, e os moradores veem para onde vai o dinheiro — o balancete do
mês e cada despesa, com o comprovante. A portaria não entra.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import exigir_papel
from app.core.config import settings
from app.core.database import get_db
from app.core.tempo import hoje_local
from app.models.condominio import Unidade
from app.models.enums import Papel
from app.models.financeiro import Cobranca, Despesa, Pagamento
from app.models.usuario import Usuario
from app.schemas.financeiro import (
    Balancete, CancelamentoCobranca, DespesaAtualizacao, DespesaEntrada, DespesaSaida,
    TotalPorCategoria,
)
from app.services import arquivos, registro

router = APIRouter(prefix="/financeiro", tags=["Prestação de contas"])

CENTAVO = Decimal("0.01")
MES = r"^\d{4}-(0[1-9]|1[0-2])$"

ROTULOS_DESPESA = {
    "categoria": "a categoria", "descricao": "a descrição", "valor": "o valor",
    "data": "a data", "fornecedor": "o fornecedor",
}

# O financeiro é do síndico e dos moradores (a portaria não vê, como nas
# cobranças).
quem_ve = exigir_papel(Papel.SINDICO, Papel.MORADOR)


def _periodo(mes: str | None) -> tuple[date, date]:
    """Primeiro dia do mês pedido (ou do atual) e do mês seguinte."""
    if mes is None:
        inicio = hoje_local().replace(day=1)
    else:
        ano, numero = (int(p) for p in mes.split("-"))
        inicio = date(ano, numero, 1)
    fim = date(inicio.year + inicio.month // 12, inicio.month % 12 + 1, 1)
    return inicio, fim


def _saida(d: Despesa, ultima=None) -> DespesaSaida:
    return DespesaSaida(
        id=d.id, categoria=d.categoria, descricao=d.descricao, valor=d.valor, data=d.data,
        fornecedor=d.fornecedor,
        comprovante_url=(f"/financeiro/despesas/{d.id}/comprovante"
                         if d.comprovante_arquivo else None),
        lancada_por_nome=d.lancada_por.nome if d.lancada_por else None,
        cancelada=d.inativo, criado_em=d.criado_em, ultima_alteracao=ultima,
    )


def _com_autoria(db: Session, d: Despesa) -> DespesaSaida:
    return _saida(d, registro.ultimas(db, registro.DESPESA, [d.id]).get(d.id))


def _despesa_do_sindico(db: Session, sindico: Usuario, despesa_id: int) -> Despesa:
    # Travada: duas abas do síndico corrigindo e cancelando ao mesmo tempo.
    despesa = db.get(Despesa, despesa_id, with_for_update=True)
    if despesa is None or despesa.condominio_id != sindico.condominio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Despesa não encontrada.")
    if despesa.inativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Esta despesa foi cancelada.")
    return despesa


# ── Despesas ─────────────────────────────────────────────────────────
@router.post("/despesas", response_model=DespesaSaida, status_code=status.HTTP_201_CREATED,
             summary="Lança uma despesa do condomínio")
def lancar_despesa(
    dados: DespesaEntrada,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> DespesaSaida:
    despesa = Despesa(**dados.model_dump(), condominio_id=sindico.condominio_id,
                      lancada_por_id=sindico.id)
    db.add(despesa)
    db.flush()
    registro.registrar(db, sindico, registro.CRIOU, registro.DESPESA, despesa.id)
    db.commit()
    db.refresh(despesa)
    return _com_autoria(db, despesa)


@router.get("/despesas", response_model=list[DespesaSaida], summary="Lista as despesas")
def listar_despesas(
    mes: str | None = Query(default=None, pattern=MES, description="AAAA-MM; vazio: todas"),
    incluir_canceladas: bool = Query(default=False),
    usuario: Usuario = Depends(quem_ve),
    db: Session = Depends(get_db),
) -> list[DespesaSaida]:
    consulta = (
        select(Despesa).options(selectinload(Despesa.lancada_por))
        .where(Despesa.condominio_id == usuario.condominio_id)
    )
    if mes is not None:
        inicio, fim = _periodo(mes)
        consulta = consulta.where(Despesa.data >= inicio, Despesa.data < fim)
    # A cancelada (lançada errada) só o síndico pede para ver.
    if not (incluir_canceladas and usuario.papel == Papel.SINDICO):
        consulta = consulta.where(Despesa.inativo_em.is_(None))
    despesas = db.scalars(consulta.order_by(Despesa.data.desc(), Despesa.id.desc())).all()
    if usuario.papel != Papel.SINDICO:
        return [_saida(d) for d in despesas]
    ultimas = registro.ultimas(db, registro.DESPESA, (d.id for d in despesas))
    return [_saida(d, ultimas.get(d.id)) for d in despesas]


@router.put("/despesas/{despesa_id}", response_model=DespesaSaida,
            summary="Corrige uma despesa")
def corrigir_despesa(
    despesa_id: int,
    dados: DespesaAtualizacao,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> DespesaSaida:
    despesa = _despesa_do_sindico(db, sindico, despesa_id)
    novos = dados.model_dump(exclude_unset=True)
    descricao = registro.campos_alterados(despesa, novos, ROTULOS_DESPESA)
    for campo, valor in novos.items():
        setattr(despesa, campo, valor)
    if descricao:
        registro.registrar(db, sindico, registro.EDITOU, registro.DESPESA, despesa.id, descricao)
    db.commit()
    db.refresh(despesa)
    return _com_autoria(db, despesa)


@router.post("/despesas/{despesa_id}/cancelamento", response_model=DespesaSaida,
             summary="Cancela uma despesa lançada errada")
def cancelar_despesa(
    despesa_id: int,
    dados: CancelamentoCobranca,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> DespesaSaida:
    """Nada é apagado: a despesa sai das telas e do balancete, e fica
    guardada com o motivo, quem cancelou e quando."""
    despesa = _despesa_do_sindico(db, sindico, despesa_id)
    despesa.inativo_em = datetime.now(timezone.utc)
    despesa.inativado_por_id = sindico.id
    registro.registrar(db, sindico, registro.CANCELOU, registro.DESPESA, despesa.id,
                       dados.motivo)
    db.commit()
    db.refresh(despesa)
    return _com_autoria(db, despesa)


@router.put("/despesas/{despesa_id}/comprovante", response_model=DespesaSaida,
            summary="Envia a nota fiscal ou o recibo da despesa")
def enviar_comprovante(
    despesa_id: int,
    arquivo: UploadFile = File(..., description="PDF ou imagem JPG, PNG ou WebP"),
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> DespesaSaida:
    despesa = _despesa_do_sindico(db, sindico, despesa_id)
    conteudo = arquivo.file.read(settings.DOCUMENTO_MAX_KB * 1024 + 1)
    try:
        nome = arquivos.salvar_privado(arquivos.DESPESAS, conteudo, aceita_pdf=True,
                                       max_kb=settings.DOCUMENTO_MAX_KB)
    except arquivos.ArquivoRecusado as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro
    anterior = despesa.comprovante_arquivo
    despesa.comprovante_arquivo = nome
    registro.registrar(db, sindico, registro.EDITOU, registro.DESPESA, despesa.id,
                       "Trocou o comprovante" if anterior else "Anexou o comprovante")
    db.commit()
    arquivos.apagar_privado(arquivos.DESPESAS, anterior)
    db.refresh(despesa)
    return _com_autoria(db, despesa)


@router.get("/despesas/{despesa_id}/comprovante", summary="Abre o comprovante da despesa")
def abrir_comprovante(
    despesa_id: int,
    usuario: Usuario = Depends(quem_ve),
    db: Session = Depends(get_db),
) -> FileResponse:
    despesa = db.get(Despesa, despesa_id)
    caminho = (arquivos.caminho_privado(arquivos.DESPESAS, despesa.comprovante_arquivo)
               if despesa and despesa.condominio_id == usuario.condominio_id else None)
    if caminho is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Comprovante não encontrado.")
    return FileResponse(
        caminho, media_type=arquivos.tipo_de_conteudo(caminho.name),
        headers={"Cache-Control": "private, no-store", "Content-Disposition": "inline"},
    )


# ── Balancete ────────────────────────────────────────────────────────
def _receitas(db: Session, condominio_id: int, ate: date, desde: date | None = None) -> Decimal:
    """Todo o dinheiro recebido entre as datas, no dia do fuso do condomínio."""
    dia_local = func.date(func.timezone(settings.FUSO_HORARIO, Pagamento.pago_em))
    consulta = (
        select(func.coalesce(func.sum(Pagamento.valor), 0))
        .join(Cobranca, Cobranca.id == Pagamento.cobranca_id)
        .join(Unidade, Unidade.id == Cobranca.unidade_id)
        .where(Unidade.condominio_id == condominio_id, dia_local < ate)
    )
    if desde is not None:
        consulta = consulta.where(dia_local >= desde)
    return Decimal(db.scalar(consulta) or 0).quantize(CENTAVO)


def _despesas(db: Session, condominio_id: int, ate: date, desde: date | None = None) -> Decimal:
    consulta = select(func.coalesce(func.sum(Despesa.valor), 0)).where(
        Despesa.condominio_id == condominio_id, Despesa.inativo_em.is_(None), Despesa.data < ate)
    if desde is not None:
        consulta = consulta.where(Despesa.data >= desde)
    return Decimal(db.scalar(consulta) or 0).quantize(CENTAVO)


@router.get("/balancete", response_model=Balancete, summary="Balancete do mês")
def balancete(
    mes: str | None = Query(default=None, pattern=MES, description="AAAA-MM; vazio: mês atual"),
    usuario: Usuario = Depends(quem_ve),
    db: Session = Depends(get_db),
) -> Balancete:
    inicio, fim = _periodo(mes)
    cond = usuario.condominio_id
    receitas = _receitas(db, cond, fim, inicio)
    despesas = _despesas(db, cond, fim, inicio)
    anterior = _receitas(db, cond, inicio) - _despesas(db, cond, inicio)
    categorias = db.execute(
        select(Despesa.categoria, func.sum(Despesa.valor).label("total"))
        .where(Despesa.condominio_id == cond, Despesa.inativo_em.is_(None),
               Despesa.data >= inicio, Despesa.data < fim)
        .group_by(Despesa.categoria)
        .order_by(func.sum(Despesa.valor).desc())
    ).all()
    return Balancete(
        mes=inicio.strftime("%Y-%m"),
        receitas=receitas, despesas=despesas, saldo_do_mes=receitas - despesas,
        saldo_anterior=anterior, saldo_acumulado=anterior + receitas - despesas,
        por_categoria=[TotalPorCategoria(categoria=c, total=t) for c, t in categorias],
    )

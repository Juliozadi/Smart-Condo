"""Controle de veículos no estacionamento.

Documentação, seção 8: o porteiro registra entradas e saídas. O que ele
pode fazer aqui depende da permissão que o síndico definiu (seção 12).
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import exists, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.deps import (
    exigir_condominio, exigir_papel, exigir_permissao_do_porteiro, exigir_permissao_porteiro,
)
from app.core.database import get_db
from app.models.condominio import Unidade
from app.models.enums import CategoriaVeiculo, Papel, StatusUsuario, TipoMovimentacao
from app.models.operacao import MovimentacaoVeiculo, VeiculoUnidade
from app.models.usuario import Usuario
from app.schemas.comuns import Mensagem, limpar_placa, validar_placa
from app.schemas.operacao import (
    MovimentacaoEntrada, MovimentacaoSaida, OcupacaoEstacionamento, VeiculoCadastradoSaida,
    VeiculoCadastroEntrada, VeiculoNoPatio,
)

router = APIRouter(prefix="/veiculos", tags=["Veículos"])


def _saida(m: MovimentacaoVeiculo) -> MovimentacaoSaida:
    return MovimentacaoSaida(
        id=m.id, placa=m.placa, tipo=m.tipo, categoria=m.categoria,
        unidade_id=m.unidade_id,
        unidade=m.unidade.identificacao if m.unidade else None,
        modelo=m.modelo, cor=m.cor, observacao=m.observacao,
        registrada_em=m.registrada_em,
    )


# ── Veículos cadastrados do apartamento ──────────────────────────────
# A portaria só registrava as passagens: o carro do morador chegava e
# ninguém sabia de quem era. O morador cadastra as placas do apartamento,
# e a portaria reconhece a placa na entrada.

# Quantos veículos cada apartamento cadastra — mais do que as vagas, que a
# família pode estacionar fora; um limite contra erro e abuso.
LIMITE_VEICULOS = 10


def _dono_mora_la():
    """Condição SQL: o cadastro vale enquanto quem o fez mora no
    apartamento (desde antes de cadastrar), ou se foi o síndico. O carro de
    quem se mudou deixa de ser reconhecido sem ninguém precisar removê-lo."""
    return or_(
        exists().where(Usuario.id == VeiculoUnidade.cadastrado_por_id,
                       Usuario.papel == Papel.SINDICO),
        exists().where(
            Usuario.id == VeiculoUnidade.cadastrado_por_id,
            Usuario.unidade_id == VeiculoUnidade.unidade_id,
            Usuario.papel == Papel.MORADOR, Usuario.status == StatusUsuario.ATIVO,
            Usuario.unidade_desde <= VeiculoUnidade.criado_em,
        ),
    )


def _cadastrados(condominio_id: int):
    return (
        select(VeiculoUnidade)
        .options(selectinload(VeiculoUnidade.unidade), selectinload(VeiculoUnidade.cadastrado_por))
        .where(VeiculoUnidade.condominio_id == condominio_id,
               VeiculoUnidade.inativo_em.is_(None), _dono_mora_la())
    )


def _cadastro_saida(v: VeiculoUnidade) -> VeiculoCadastradoSaida:
    return VeiculoCadastradoSaida(
        id=v.id, placa=v.placa, modelo=v.modelo, cor=v.cor, unidade_id=v.unidade_id,
        unidade=v.unidade.identificacao,
        cadastrado_por_nome=v.cadastrado_por.nome if v.cadastrado_por else None,
        criado_em=v.criado_em,
    )


def _veiculo_da_placa(db: Session, condominio_id: int, placa: str) -> VeiculoUnidade | None:
    return db.scalar(_cadastrados(condominio_id).where(VeiculoUnidade.placa == placa))


def _travar_placa(db: Session, condominio_id: int, placa: str) -> None:
    """Dois pedidos com a mesma placa ao mesmo tempo esperam um pelo outro."""
    db.execute(select(func.pg_advisory_xact_lock(condominio_id, func.hashtext(placa))))


@router.get("/cadastrados", response_model=list[VeiculoCadastradoSaida],
            summary="Veículos cadastrados dos apartamentos")
def listar_cadastrados(
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> list[VeiculoCadastradoSaida]:
    """O morador vê os do apartamento; o síndico e a portaria (com a
    permissão de veículos), os de todos."""
    exigir_permissao_do_porteiro(db, usuario, "registrar_veiculos")
    consulta = _cadastrados(usuario.condominio_id)
    if usuario.papel == Papel.MORADOR:
        consulta = consulta.where(VeiculoUnidade.unidade_id == usuario.unidade_id)
    elif usuario.papel not in (Papel.SINDICO, Papel.PORTEIRO):
        return []
    return [_cadastro_saida(v) for v in db.scalars(
        consulta.order_by(VeiculoUnidade.unidade_id, VeiculoUnidade.placa)).all()]


@router.get("/cadastrados/placa/{placa}", response_model=VeiculoCadastradoSaida,
            summary="De que apartamento é esta placa")
def consultar_placa(
    placa: str,
    usuario: Usuario = Depends(exigir_permissao_porteiro("registrar_veiculos")),
    db: Session = Depends(get_db),
) -> VeiculoCadastradoSaida:
    try:
        placa = validar_placa(placa)
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro
    veiculo = _veiculo_da_placa(db, usuario.condominio_id, placa)
    if veiculo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Esta placa não está cadastrada.")
    return _cadastro_saida(veiculo)


@router.post("/cadastrados", response_model=VeiculoCadastradoSaida,
             status_code=status.HTTP_201_CREATED, summary="Cadastra um veículo do apartamento")
def cadastrar_veiculo(
    dados: VeiculoCadastroEntrada,
    usuario: Usuario = Depends(exigir_papel(Papel.MORADOR, Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> VeiculoCadastradoSaida:
    if usuario.papel == Papel.MORADOR:
        unidade_id = usuario.unidade_id
    else:
        if dados.unidade_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Informe o apartamento do veículo.")
        unidade = db.get(Unidade, dados.unidade_id)
        if (unidade is None or unidade.condominio_id != usuario.condominio_id
                or unidade.pendente):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Unidade não encontrada.")
        unidade_id = unidade.id

    _travar_placa(db, usuario.condominio_id, dados.placa)
    existente = db.scalar(select(VeiculoUnidade).where(
        VeiculoUnidade.condominio_id == usuario.condominio_id,
        VeiculoUnidade.placa == dados.placa, VeiculoUnidade.inativo_em.is_(None)))
    if existente is not None:
        if db.scalar(select(_dono_mora_la()).where(VeiculoUnidade.id == existente.id)):
            # Não diz de quem é: a placa do vizinho é dado dele.
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=("Esta placa já está cadastrada no seu apartamento."
                        if existente.unidade_id == unidade_id
                        else "Esta placa já está cadastrada em outro apartamento."),
            )
        # Cadastro de quem se mudou: deixa de valer de vez, e a placa fica livre.
        existente.inativo_em = datetime.now(timezone.utc)

    do_apartamento = db.scalar(select(func.count()).select_from(
        _cadastrados(usuario.condominio_id).where(VeiculoUnidade.unidade_id == unidade_id)
        .subquery()))
    if do_apartamento >= LIMITE_VEICULOS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O apartamento chegou ao limite de {LIMITE_VEICULOS} veículos cadastrados. "
                   "Remova os que não usa mais.",
        )

    veiculo = VeiculoUnidade(
        condominio_id=usuario.condominio_id, unidade_id=unidade_id, cadastrado_por_id=usuario.id,
        placa=dados.placa, modelo=dados.modelo, cor=dados.cor,
    )
    db.add(veiculo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Esta placa já está cadastrada.") from None
    db.refresh(veiculo)
    return _cadastro_saida(veiculo)


@router.delete("/cadastrados/{veiculo_id}", response_model=Mensagem,
               summary="Remove um veículo do apartamento")
def remover_veiculo(
    veiculo_id: int,
    usuario: Usuario = Depends(exigir_papel(Papel.MORADOR, Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> Mensagem:
    veiculo = db.scalar(_cadastrados(usuario.condominio_id)
                        .where(VeiculoUnidade.id == veiculo_id).with_for_update(of=VeiculoUnidade))
    if veiculo is None or (usuario.papel == Papel.MORADOR
                           and veiculo.unidade_id != usuario.unidade_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Veículo não encontrado.")
    # Nada é apagado: fica guardado, com quem removeu e quando.
    veiculo.inativo_em = datetime.now(timezone.utc)
    veiculo.inativado_por_id = usuario.id
    db.commit()
    return Mensagem(detalhe="Veículo removido do apartamento.")


def _ultima_por_placa(condominio_id: int):
    """Subconsulta com a movimentação mais recente de cada placa."""
    return (
        select(
            MovimentacaoVeiculo.placa.label("placa"),
            func.max(MovimentacaoVeiculo.id).label("ultimo_id"),
        )
        .where(MovimentacaoVeiculo.condominio_id == condominio_id)
        .group_by(MovimentacaoVeiculo.placa)
        .subquery()
    )


@router.post(
    "",
    response_model=MovimentacaoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Registra a entrada ou a saída de um veículo",
)
def registrar_movimentacao(
    dados: MovimentacaoEntrada,
    usuario: Usuario = Depends(exigir_permissao_porteiro("registrar_veiculos")),
    db: Session = Depends(get_db),
) -> MovimentacaoSaida:
    unidade = None
    unidade_id = dados.unidade_id
    modelo, cor = dados.modelo, dados.cor
    # Placa cadastrada: a portaria não precisa escolher o apartamento.
    if dados.categoria == CategoriaVeiculo.MORADOR and unidade_id is None:
        cadastrado = _veiculo_da_placa(db, usuario.condominio_id, dados.placa)
        if cadastrado is not None:
            unidade_id = cadastrado.unidade_id
            modelo, cor = modelo or cadastrado.modelo, cor or cadastrado.cor
    if unidade_id is not None:
        unidade = db.get(Unidade, unidade_id)
        if unidade is None or unidade.condominio_id != usuario.condominio_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada."
            )
    if dados.categoria == CategoriaVeiculo.MORADOR and unidade is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe a unidade do morador.",
        )

    # Trava a placa até o fim da transação: dois pedidos ao mesmo tempo
    # (clique duplo, dois porteiros) passavam juntos pela conferência
    # abaixo, e o carro entrava duas vezes. Não há linha para travar
    # antes da primeira entrada, por isso a trava é por chave.
    db.execute(
        select(func.pg_advisory_xact_lock(
            usuario.condominio_id, func.hashtext(dados.placa)
        ))
    )
    # Duas entradas seguidas (ou duas saídas) deixariam o pátio errado.
    ultima = db.scalar(
        select(MovimentacaoVeiculo)
        .where(
            MovimentacaoVeiculo.condominio_id == usuario.condominio_id,
            MovimentacaoVeiculo.placa == dados.placa,
        )
        .order_by(MovimentacaoVeiculo.id.desc())
        .limit(1)
    )
    if ultima is not None and ultima.tipo == dados.tipo:
        ja = "entrada" if dados.tipo == TipoMovimentacao.ENTRADA else "saída"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A última movimentação desta placa já foi uma {ja}.",
        )
    if ultima is None and dados.tipo == TipoMovimentacao.SAIDA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este veículo não tem entrada registrada.",
        )

    movimentacao = MovimentacaoVeiculo(
        condominio_id=usuario.condominio_id,
        placa=dados.placa,
        modelo=modelo,
        cor=cor,
        tipo=dados.tipo,
        categoria=dados.categoria,
        unidade_id=unidade_id,
        observacao=dados.observacao,
        registrada_por_id=usuario.id,
        registrada_em=datetime.now(timezone.utc),
    )
    db.add(movimentacao)
    db.commit()
    db.refresh(movimentacao)
    return _saida(movimentacao)


@router.get("/patio", response_model=list[VeiculoNoPatio], summary="Veículos no pátio agora")
def listar_no_patio(
    usuario: Usuario = Depends(exigir_permissao_porteiro("registrar_veiculos")),
    db: Session = Depends(get_db),
) -> list[VeiculoNoPatio]:
    """Quem está dentro sai da última movimentação de cada placa.

    Traz placa e unidade de todos os carros: é da portaria e do síndico. O
    morador vê só a ocupação, em números (GET /veiculos/ocupacao)."""
    ultimas = _ultima_por_placa(usuario.condominio_id)
    dentro = db.scalars(
        select(MovimentacaoVeiculo)
        .join(ultimas, MovimentacaoVeiculo.id == ultimas.c.ultimo_id)
        .where(MovimentacaoVeiculo.tipo == TipoMovimentacao.ENTRADA)
        .order_by(MovimentacaoVeiculo.registrada_em.desc())
    ).all()

    return [
        VeiculoNoPatio(
            placa=m.placa, categoria=m.categoria,
            unidade=m.unidade.identificacao if m.unidade else None,
            modelo=m.modelo, cor=m.cor, desde=m.registrada_em,
        )
        for m in dentro
    ]


@router.get(
    "/ocupacao",
    response_model=OcupacaoEstacionamento,
    summary="Ocupação do estacionamento",
)
def ocupacao(
    usuario: Usuario = Depends(exigir_condominio), db: Session = Depends(get_db)
) -> OcupacaoEstacionamento:
    """As vagas totais vêm da soma das vagas das unidades."""
    vagas = db.scalar(
        select(func.coalesce(func.sum(Unidade.vagas_garagem), 0)).where(
            Unidade.condominio_id == usuario.condominio_id
        )
    ) or 0

    ultimas = _ultima_por_placa(usuario.condominio_id)
    ocupadas = db.scalar(
        select(func.count())
        .select_from(MovimentacaoVeiculo)
        .join(ultimas, MovimentacaoVeiculo.id == ultimas.c.ultimo_id)
        .where(MovimentacaoVeiculo.tipo == TipoMovimentacao.ENTRADA)
    ) or 0

    percentual = round(ocupadas / vagas * 100) if vagas else 0
    return OcupacaoEstacionamento(
        vagas_totais=vagas,
        ocupadas=ocupadas,
        # Mais carros que vagas é possível (visitantes); não devolve negativo.
        livres=max(vagas - ocupadas, 0),
        percentual=min(percentual, 100),
    )


@router.get(
    "",
    response_model=list[MovimentacaoSaida],
    summary="Histórico de movimentações",
)
def listar_movimentacoes(
    placa: str | None = Query(default=None, description="Filtra por placa."),
    limite: int = Query(default=50, ge=1, le=200),
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> list[MovimentacaoSaida]:
    exigir_permissao_do_porteiro(db, usuario, "registrar_veiculos")
    consulta = select(MovimentacaoVeiculo).where(
        MovimentacaoVeiculo.condominio_id == usuario.condominio_id
    )
    # O morador acompanha apenas os veículos da própria unidade.
    if usuario.papel == Papel.MORADOR:
        consulta = consulta.where(MovimentacaoVeiculo.unidade_id == usuario.unidade_id)
    if placa:
        consulta = consulta.where(MovimentacaoVeiculo.placa == limpar_placa(placa))

    movimentacoes = db.scalars(
        consulta.order_by(MovimentacaoVeiculo.id.desc()).limit(limite)
    ).all()
    return [_saida(m) for m in movimentacoes]

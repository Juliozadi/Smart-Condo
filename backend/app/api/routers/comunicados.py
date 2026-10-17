"""Comunicados do síndico.

Documentação, seção 13.5.4: "o Síndico pode fazer comunicados sobre qualquer
assunto que lhe vê importância de repassar aos moradores".
Seção 11.6.4: o morador pode filtrar por categoria e marcar como lido.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session, selectinload

from app.api.deps import exigir_condominio, exigir_papel
from app.core.database import get_db
from app.models.comunicado import Comunicado, LeituraComunicado
from app.models.condominio import Unidade
from app.models.enums import CategoriaComunicado, CanalVerificacao, Papel, StatusUsuario
from app.models.usuario import Usuario
from app.schemas.comuns import Mensagem
from app.schemas.comunicado import ComunicadoEntrada, ComunicadoSaida
from app.services import notificacao, registro

router = APIRouter(prefix="/comunicados", tags=["Comunicados"])


def _destino(c: Comunicado) -> str:
    if c.unidade_id is not None:
        return f"Apto {c.unidade.identificacao}"
    if c.bloco is not None:
        return f"Bloco {c.bloco}"
    return "Todo o condomínio"


def _saida(c: Comunicado, autor_nome: str, lido: bool) -> ComunicadoSaida:
    return ComunicadoSaida(
        id=c.id, titulo=c.titulo, conteudo=c.conteudo, categoria=c.categoria,
        fixado=c.fixado, publicado_em=c.publicado_em, autor_nome=autor_nome, lido=lido,
        bloco=c.bloco, unidade_id=c.unidade_id, destino=_destino(c),
    )


def _visiveis(usuario: Usuario):
    """Condição SQL: os comunicados que este usuário pode ver.

    O síndico vê todos. A portaria vê os gerais e os de bloco (a falta de
    água no bloco B é da conta dela), nunca os de um apartamento. O morador
    vê os gerais, os do seu bloco e os do seu apartamento — estes, só os
    publicados desde que mora lá: a advertência do morador anterior não é
    da conta de quem chegou depois.
    """
    no_condominio = Comunicado.condominio_id == usuario.condominio_id
    if usuario.papel == Papel.SINDICO:
        return no_condominio
    gerais = and_(Comunicado.bloco.is_(None), Comunicado.unidade_id.is_(None))
    if usuario.papel == Papel.PORTEIRO:
        return and_(no_condominio, Comunicado.unidade_id.is_(None))
    if usuario.papel != Papel.MORADOR or usuario.unidade is None:
        return and_(no_condominio, gerais)
    return and_(no_condominio, or_(
        gerais,
        Comunicado.bloco == usuario.unidade.bloco,
        and_(Comunicado.unidade_id == usuario.unidade_id,
             Comunicado.publicado_em >= usuario.unidade_desde),
    ))


@router.post(
    "",
    response_model=ComunicadoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Publica um comunicado",
)
def publicar(
    dados: ComunicadoEntrada,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> ComunicadoSaida:
    if sindico.condominio_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Cadastre o condomínio primeiro."
        )
    # O destino é deste condomínio; a unidade do autocadastro ainda não
    # aprovada (pendente) não existe para o síndico.
    if dados.unidade_id is not None:
        unidade = db.get(Unidade, dados.unidade_id)
        if (unidade is None or unidade.condominio_id != sindico.condominio_id
                or unidade.pendente):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada."
            )
    if dados.bloco is not None and not db.scalar(
        select(Unidade.id).where(
            Unidade.condominio_id == sindico.condominio_id, Unidade.bloco == dados.bloco,
            Unidade.pendente.is_(False),
        ).limit(1)
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Não há unidades no bloco {dados.bloco}.",
        )

    comunicado = Comunicado(
        condominio_id=sindico.condominio_id,
        autor_id=sindico.id,
        publicado_em=datetime.now(timezone.utc),
        **dados.model_dump(),
    )
    db.add(comunicado)
    db.flush()
    registro.registrar(db, sindico, registro.CRIOU, registro.COMUNICADO, comunicado.id)
    db.commit()
    db.refresh(comunicado)

    # Só quem mora lá hoje: antes o aviso ia também para os inativados e
    # para cadastros recusados ou ainda pendentes. E só o destino: o bloco,
    # ou o apartamento.
    consulta = select(Usuario).where(
        Usuario.condominio_id == sindico.condominio_id, Usuario.papel == Papel.MORADOR,
        Usuario.status == StatusUsuario.ATIVO,
    )
    if comunicado.unidade_id is not None:
        consulta = consulta.where(Usuario.unidade_id == comunicado.unidade_id)
    elif comunicado.bloco is not None:
        consulta = consulta.join(Unidade, Unidade.id == Usuario.unidade_id).where(
            Unidade.bloco == comunicado.bloco)
    for morador in db.scalars(consulta).all():
        notificacao.notificar(
            morador.email, CanalVerificacao.EMAIL, "Novo comunicado", comunicado.titulo
        )

    return _saida(comunicado, sindico.nome, lido=False)


@router.get("", response_model=list[ComunicadoSaida], summary="Lista os comunicados")
def listar(
    categoria: CategoriaComunicado | None = Query(default=None),
    apenas_nao_lidos: bool = Query(default=False),
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> list[ComunicadoSaida]:
    consulta = (
        select(Comunicado)
        .options(selectinload(Comunicado.autor), selectinload(Comunicado.unidade))
        .where(_visiveis(usuario), Comunicado.inativo_em.is_(None))
        # Os fixados primeiro, depois do mais novo para o mais antigo.
        .order_by(Comunicado.fixado.desc(), Comunicado.publicado_em.desc())
    )
    if categoria is not None:
        consulta = consulta.where(Comunicado.categoria == categoria)

    comunicados = db.scalars(consulta).all()

    lidos = set(
        db.scalars(
            select(LeituraComunicado.comunicado_id).where(
                LeituraComunicado.usuario_id == usuario.id
            )
        ).all()
    )

    saida = [_saida(c, c.autor.nome, lido=c.id in lidos) for c in comunicados]
    if apenas_nao_lidos:
        saida = [c for c in saida if not c.lido]
    return saida


@router.post(
    "/{comunicado_id}/leitura", response_model=Mensagem, summary="Marca o comunicado como lido"
)
def marcar_como_lido(
    comunicado_id: int,
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> Mensagem:
    # Só o que ele pode ver: o 404 também não confirma que a advertência
    # do vizinho existe.
    comunicado = db.scalar(select(Comunicado).where(
        Comunicado.id == comunicado_id, _visiveis(usuario), Comunicado.inativo_em.is_(None)))
    if comunicado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comunicado não encontrado."
        )

    # Marcar de novo não é erro nem duplica a linha — nem quando as duas
    # marcações chegam ao mesmo tempo: quem decide é a restrição do banco.
    db.execute(
        pg_insert(LeituraComunicado)
        .values(comunicado_id=comunicado.id, usuario_id=usuario.id,
                lido_em=datetime.now(timezone.utc))
        .on_conflict_do_nothing(constraint="uq_leitura_por_usuario")
    )
    db.commit()

    return Mensagem(detalhe="Comunicado marcado como lido.")


@router.delete("/{comunicado_id}", response_model=Mensagem, summary="Remove (inativa) um comunicado")
def remover(
    comunicado_id: int,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> Mensagem:
    comunicado = db.get(Comunicado, comunicado_id, with_for_update=True)
    if (comunicado is None or comunicado.condominio_id != sindico.condominio_id
            or comunicado.inativo_em is not None):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comunicado não encontrado."
        )
    # Nada é apagado: o comunicado sai das telas, mas fica no banco com
    # quem o removeu e quando.
    comunicado.inativo_em = datetime.now(timezone.utc)
    comunicado.inativado_por_id = sindico.id
    registro.registrar(db, sindico, registro.INATIVOU, registro.COMUNICADO, comunicado.id)
    db.commit()
    return Mensagem(detalhe="Comunicado removido.")

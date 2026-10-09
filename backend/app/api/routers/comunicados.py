"""Comunicados do síndico.

Documentação, seção 13.5.4: "o Síndico pode fazer comunicados sobre qualquer
assunto que lhe vê importância de repassar aos moradores".
Seção 11.6.4: o morador pode filtrar por categoria e marcar como lido.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.api.deps import exigir_condominio, exigir_papel
from app.core.database import get_db
from app.models.comunicado import Comunicado, LeituraComunicado
from app.models.enums import CategoriaComunicado, CanalVerificacao, Papel, StatusUsuario
from app.models.usuario import Usuario
from app.schemas.comuns import Mensagem
from app.schemas.comunicado import ComunicadoEntrada, ComunicadoSaida
from app.services import notificacao, registro

router = APIRouter(prefix="/comunicados", tags=["Comunicados"])


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
    # para cadastros recusados ou ainda pendentes.
    moradores = db.scalars(
        select(Usuario).where(
            Usuario.condominio_id == sindico.condominio_id, Usuario.papel == Papel.MORADOR,
            Usuario.status == StatusUsuario.ATIVO,
        )
    ).all()
    for morador in moradores:
        notificacao.notificar(
            morador.email, CanalVerificacao.EMAIL, "Novo comunicado", comunicado.titulo
        )

    return ComunicadoSaida(
        id=comunicado.id, titulo=comunicado.titulo, conteudo=comunicado.conteudo,
        categoria=comunicado.categoria, fixado=comunicado.fixado,
        publicado_em=comunicado.publicado_em, autor_nome=sindico.nome, lido=False,
    )


@router.get("", response_model=list[ComunicadoSaida], summary="Lista os comunicados")
def listar(
    categoria: CategoriaComunicado | None = Query(default=None),
    apenas_nao_lidos: bool = Query(default=False),
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> list[ComunicadoSaida]:
    consulta = (
        select(Comunicado)
        .where(Comunicado.condominio_id == usuario.condominio_id, Comunicado.inativo_em.is_(None))
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

    saida = [
        ComunicadoSaida(
            id=c.id, titulo=c.titulo, conteudo=c.conteudo, categoria=c.categoria,
            fixado=c.fixado, publicado_em=c.publicado_em, autor_nome=c.autor.nome,
            lido=c.id in lidos,
        )
        for c in comunicados
    ]
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
    comunicado = db.get(Comunicado, comunicado_id)
    if (comunicado is None or comunicado.condominio_id != usuario.condominio_id
            or comunicado.inativo_em is not None):
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

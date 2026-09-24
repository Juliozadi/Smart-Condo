"""Portaria: visitantes, encomendas e ocorrências.

Documentação, seção 6 (História do Usuário):
  - porteiro: "gostaria que o sistema enviasse uma notificação de entrega
    para o cliente que realizou o pedido"
  - porteiro: "que uma notificação seja enviada para o cliente com a foto do
    indivíduo ou gravação em tempo real (vídeo porteiro)... e, assim, o
    cliente confirme se é ou não seu convidado"
  - morador: "o porteiro me envia pelo sistema uma foto ou vídeo para que eu
    confirmasse a minha entrega ou pedido"

O que o porteiro pode fazer aqui depende das permissões que o síndico
definiu (seção 12, caso de uso "Permissão do Porteiro").

As fotos de visitantes e encomendas são dado pessoal de terceiros
(LGPD). Não têm endereço público: são enviadas e lidas por rotas desta
área, que conferem o token e quem pode ver cada uma — a portaria com a
permissão correspondente, o síndico e o morador da unidade. Passado
FOTO_PORTARIA_DIAS, o arquivo é apagado.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    exigir_condominio, exigir_papel, exigir_permissao_do_porteiro, exigir_permissao_porteiro,
    porteiro_tem_permissao,
)
from app.core.config import settings
from app.core.database import get_db
from app.models.condominio import Unidade
from app.models.enums import (
    CanalVerificacao, Papel, StatusEncomenda, StatusOcorrencia, StatusVisitante,
)
from app.models.portaria import Encomenda, Ocorrencia, Visitante
from app.models.usuario import Usuario
from app.schemas.portaria import (
    ConfirmacaoVisitante, EncomendaEntrada, EncomendaSaida, OcorrenciaEntrada,
    OcorrenciaSaida, RespostaOcorrencia, RetiradaEncomenda, VisitanteEntrada,
    VisitanteSaida,
)
from app.services import arquivos, notificacao

router = APIRouter(prefix="/portaria", tags=["Portaria"])


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _unidade_do_condominio(db: Session, usuario: Usuario, unidade_id: int) -> Unidade:
    unidade = db.get(Unidade, unidade_id)
    if unidade is None or unidade.condominio_id != usuario.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada."
        )
    return unidade


def _avisar_moradores(db: Session, unidade: Unidade, titulo: str, mensagem: str) -> None:
    """Notifica quem mora na unidade."""
    moradores = db.scalars(
        select(Usuario).where(Usuario.unidade_id == unidade.id, Usuario.papel == Papel.MORADOR)
    ).all()
    for morador in moradores:
        notificacao.notificar(morador.email, CanalVerificacao.EMAIL, titulo, mensagem)


def _visitante_saida(v: Visitante, unidade: Unidade | None = None) -> VisitanteSaida:
    return VisitanteSaida(
        id=v.id, unidade_id=v.unidade_id,
        unidade=(unidade or v.unidade).identificacao,
        nome=v.nome, documento=v.documento, tipo_visita=v.tipo_visita,
        placa_veiculo=v.placa_veiculo,
        foto_url=f"/portaria/visitantes/{v.id}/foto" if v.foto_arquivo else None,
        status=v.status,
        entrada_em=v.entrada_em, saida_em=v.saida_em,
        confirmado_em=v.confirmado_em, criado_em=v.criado_em,
    )


def _encomenda_saida(e: Encomenda) -> EncomendaSaida:
    return EncomendaSaida(
        id=e.id, unidade_id=e.unidade_id, unidade=e.unidade.identificacao,
        remetente=e.remetente, tipo_volume=e.tipo_volume,
        codigo_rastreio=e.codigo_rastreio, observacoes=e.observacoes,
        foto_url=f"/portaria/encomendas/{e.id}/foto" if e.foto_arquivo else None,
        status=e.status, recebida_em=e.recebida_em,
        retirada_em=e.retirada_em, criado_em=e.criado_em,
    )


# ── Fotos (vídeo porteiro e encomendas) ─────────────────────────────
def _ler_foto_enviada(arquivo: UploadFile, pasta: str = arquivos.PORTARIA) -> str:
    """Grava a foto numa pasta privada e devolve o nome gravado."""
    # Lê só até um byte além do limite, como na foto de perfil.
    conteudo = arquivo.file.read(settings.FOTO_MAX_KB * 1024 + 1)
    try:
        return arquivos.salvar_privado(
            pasta, conteudo, aceita_pdf=False, max_kb=settings.FOTO_MAX_KB
        )
    except arquivos.ArquivoRecusado as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro


def _pode_ver_foto(db: Session, usuario: Usuario, unidade: Unidade, permissao: str) -> bool:
    if unidade.condominio_id != usuario.condominio_id:
        return False
    if usuario.papel == Papel.SINDICO:
        return True
    if usuario.papel == Papel.MORADOR:
        return unidade.id == usuario.unidade_id
    if usuario.papel == Papel.PORTEIRO:
        return porteiro_tem_permissao(db, usuario, permissao)
    return False


def _entregar_foto(nome: str | None, pasta: str = arquivos.PORTARIA) -> FileResponse:
    caminho = arquivos.caminho_privado(pasta, nome)
    if caminho is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto não encontrada.")
    return FileResponse(
        caminho,
        media_type=arquivos.tipo_de_conteudo(caminho.name),
        # Dado pessoal: nada de cópia em cache compartilhado nem no disco
        # do navegador.
        headers={"Cache-Control": "private, no-store"},
    )


def _expurgar_fotos_antigas(db: Session) -> None:
    """Apaga as fotos da portaria que passaram do prazo de guarda.

    Roda a cada novo registro, sem depender de tarefa agendada: o custo é
    uma consulta pelos poucos registros vencidos que ainda têm foto.
    """
    limite = _agora() - timedelta(days=settings.FOTO_PORTARIA_DIAS)
    vencidos = [
        *db.scalars(select(Visitante).where(
            Visitante.foto_arquivo.is_not(None), Visitante.criado_em < limite)),
        *db.scalars(select(Encomenda).where(
            Encomenda.foto_arquivo.is_not(None), Encomenda.criado_em < limite)),
    ]
    if not vencidos:
        return
    nomes = [registro.foto_arquivo for registro in vencidos]
    for registro in vencidos:
        registro.foto_arquivo = None
    db.commit()
    for nome in nomes:
        arquivos.apagar_privado(arquivos.PORTARIA, nome)


# ── Visitantes ───────────────────────────────────────────────────────
@router.post(
    "/visitantes",
    response_model=VisitanteSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Registra um visitante e notifica o morador",
)
def registrar_visitante(
    dados: VisitanteEntrada,
    usuario: Usuario = Depends(exigir_permissao_porteiro("registrar_visitantes")),
    db: Session = Depends(get_db),
) -> VisitanteSaida:
    unidade = _unidade_do_condominio(db, usuario, dados.unidade_id)
    _expurgar_fotos_antigas(db)

    visitante = Visitante(
        **dados.model_dump(),
        registrado_por_id=usuario.id,
        status=StatusVisitante.AGUARDANDO_CONFIRMACAO,
    )
    db.add(visitante)
    db.commit()
    db.refresh(visitante)

    # A notificação com a foto é o que permite o morador confirmar (seção 6).
    _avisar_moradores(
        db, unidade,
        "Visitante na portaria",
        f"{visitante.nome} diz ser seu convidado. Confirme ou recuse a entrada.",
    )
    return _visitante_saida(visitante, unidade)


@router.get(
    "/visitantes",
    response_model=list[VisitanteSaida],
    summary="Lista os visitantes",
)
def listar_visitantes(
    status_visitante: StatusVisitante | None = Query(default=None, alias="status"),
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> list[VisitanteSaida]:
    exigir_permissao_do_porteiro(db, usuario, "registrar_visitantes")
    consulta = select(Visitante).join(Unidade).where(
        Unidade.condominio_id == usuario.condominio_id
    )
    # O morador só enxerga os visitantes da própria unidade.
    if usuario.papel == Papel.MORADOR:
        consulta = consulta.where(Visitante.unidade_id == usuario.unidade_id)
    if status_visitante is not None:
        consulta = consulta.where(Visitante.status == status_visitante)

    visitantes = db.scalars(consulta.order_by(Visitante.id.desc())).all()
    return [_visitante_saida(v) for v in visitantes]


@router.post(
    "/visitantes/{visitante_id}/confirmacao",
    response_model=VisitanteSaida,
    summary="O morador confirma ou recusa o visitante",
)
def confirmar_visitante(
    visitante_id: int,
    dados: ConfirmacaoVisitante,
    morador: Usuario = Depends(exigir_papel(Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> VisitanteSaida:
    """"o cliente confirme se é ou não seu convidado" (seção 6)."""
    visitante = db.get(Visitante, visitante_id)
    # Quem responde é o morador da unidade visitada, ninguém mais.
    if visitante is None or visitante.unidade_id != morador.unidade_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visitante não encontrado."
        )
    if visitante.status != StatusVisitante.AGUARDANDO_CONFIRMACAO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este visitante já foi respondido.",
        )

    agora = _agora()
    visitante.confirmado_por_id = morador.id
    visitante.confirmado_em = agora
    if dados.confirmado:
        visitante.status = StatusVisitante.DENTRO
        visitante.entrada_em = agora
    else:
        visitante.status = StatusVisitante.RECUSADO

    db.commit()
    db.refresh(visitante)

    if visitante.registrado_por_id:
        porteiro = db.get(Usuario, visitante.registrado_por_id)
        if porteiro:
            notificacao.notificar(
                porteiro.email, CanalVerificacao.EMAIL,
                "Resposta do morador",
                f"{visitante.nome}: entrada "
                f"{'liberada' if dados.confirmado else 'recusada'}.",
            )
    return _visitante_saida(visitante)


@router.post(
    "/visitantes/{visitante_id}/saida",
    response_model=VisitanteSaida,
    summary="Registra a saída do visitante",
)
def registrar_saida(
    visitante_id: int,
    usuario: Usuario = Depends(exigir_permissao_porteiro("registrar_visitantes")),
    db: Session = Depends(get_db),
) -> VisitanteSaida:
    visitante = db.get(Visitante, visitante_id)
    if visitante is None or visitante.unidade.condominio_id != usuario.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visitante não encontrado."
        )
    if visitante.status != StatusVisitante.DENTRO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este visitante não está registrado como dentro do condomínio.",
        )

    visitante.status = StatusVisitante.SAIU
    visitante.saida_em = _agora()
    db.commit()
    db.refresh(visitante)
    return _visitante_saida(visitante)


@router.put(
    "/visitantes/{visitante_id}/foto",
    response_model=VisitanteSaida,
    summary="Envia a foto do visitante (vídeo porteiro)",
)
def enviar_foto_visitante(
    visitante_id: int,
    arquivo: UploadFile = File(..., description="Imagem JPG, PNG ou WebP"),
    usuario: Usuario = Depends(exigir_permissao_porteiro("registrar_visitantes")),
    db: Session = Depends(get_db),
) -> VisitanteSaida:
    visitante = db.get(Visitante, visitante_id)
    if visitante is None or visitante.unidade.condominio_id != usuario.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visitante não encontrado."
        )
    # A foto é para o morador reconhecer quem está na portaria. Depois
    # da resposta dele, trocá-la mudaria o que ele viu ao decidir.
    if visitante.status != StatusVisitante.AGUARDANDO_CONFIRMACAO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O morador já respondeu; a foto não pode mais ser trocada.",
        )

    nova = _ler_foto_enviada(arquivo)
    anterior = visitante.foto_arquivo
    visitante.foto_arquivo = nova
    db.commit()
    arquivos.apagar_privado(arquivos.PORTARIA, anterior)
    db.refresh(visitante)
    return _visitante_saida(visitante)


@router.get("/visitantes/{visitante_id}/foto", summary="Foto do visitante")
def foto_visitante(
    visitante_id: int,
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> FileResponse:
    visitante = db.get(Visitante, visitante_id)
    # 404 também para quem não pode ver: não confirma que o registro existe.
    if visitante is None or not _pode_ver_foto(
        db, usuario, visitante.unidade, "registrar_visitantes"
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto não encontrada.")
    return _entregar_foto(visitante.foto_arquivo)


# ── Encomendas ───────────────────────────────────────────────────────
@router.post(
    "/encomendas",
    response_model=EncomendaSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Registra uma encomenda e notifica o morador",
)
def registrar_encomenda(
    dados: EncomendaEntrada,
    usuario: Usuario = Depends(exigir_permissao_porteiro("registrar_encomendas")),
    db: Session = Depends(get_db),
) -> EncomendaSaida:
    unidade = _unidade_do_condominio(db, usuario, dados.unidade_id)
    _expurgar_fotos_antigas(db)

    encomenda = Encomenda(
        **dados.model_dump(),
        registrada_por_id=usuario.id,
        recebida_em=_agora(),
        status=StatusEncomenda.AGUARDANDO_RETIRADA,
    )
    db.add(encomenda)
    db.commit()
    db.refresh(encomenda)

    # "notificação de entrega para o cliente que realizou o pedido" (seção 6)
    rastreio = f" (rastreio {encomenda.codigo_rastreio})" if encomenda.codigo_rastreio else ""
    _avisar_moradores(
        db, unidade,
        "Encomenda na portaria",
        f"{encomenda.tipo_volume} de {encomenda.remetente}{rastreio} chegou para você.",
    )
    return _encomenda_saida(encomenda)


@router.get("/encomendas", response_model=list[EncomendaSaida], summary="Lista as encomendas")
def listar_encomendas(
    status_encomenda: StatusEncomenda | None = Query(default=None, alias="status"),
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> list[EncomendaSaida]:
    exigir_permissao_do_porteiro(db, usuario, "registrar_encomendas")
    consulta = select(Encomenda).join(Unidade).where(
        Unidade.condominio_id == usuario.condominio_id
    )
    if usuario.papel == Papel.MORADOR:
        consulta = consulta.where(Encomenda.unidade_id == usuario.unidade_id)
    if status_encomenda is not None:
        consulta = consulta.where(Encomenda.status == status_encomenda)

    return [_encomenda_saida(e) for e in db.scalars(consulta.order_by(Encomenda.id.desc())).all()]


@router.post(
    "/encomendas/{encomenda_id}/retirada",
    response_model=EncomendaSaida,
    summary="O morador confirma a retirada da encomenda",
)
def confirmar_retirada(
    encomenda_id: int,
    dados: RetiradaEncomenda,
    morador: Usuario = Depends(exigir_papel(Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> EncomendaSaida:
    """"o porteiro me envia... uma foto ou vídeo para que eu confirmasse a
    minha entrega ou pedido" (seção 6)."""
    encomenda = db.get(Encomenda, encomenda_id)
    if encomenda is None or encomenda.unidade_id != morador.unidade_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Encomenda não encontrada."
        )
    if encomenda.status != StatusEncomenda.AGUARDANDO_RETIRADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Esta encomenda já foi respondida."
        )

    if dados.confirmada:
        encomenda.status = StatusEncomenda.RETIRADA
        encomenda.retirada_em = _agora()
        encomenda.retirada_por_id = morador.id
    else:
        encomenda.status = StatusEncomenda.RECUSADA

    db.commit()
    db.refresh(encomenda)
    return _encomenda_saida(encomenda)


@router.put(
    "/encomendas/{encomenda_id}/foto",
    response_model=EncomendaSaida,
    summary="Envia a foto da encomenda",
)
def enviar_foto_encomenda(
    encomenda_id: int,
    arquivo: UploadFile = File(..., description="Imagem JPG, PNG ou WebP"),
    usuario: Usuario = Depends(exigir_permissao_porteiro("registrar_encomendas")),
    db: Session = Depends(get_db),
) -> EncomendaSaida:
    encomenda = db.get(Encomenda, encomenda_id)
    if encomenda is None or encomenda.unidade.condominio_id != usuario.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Encomenda não encontrada."
        )
    if encomenda.status != StatusEncomenda.AGUARDANDO_RETIRADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O morador já respondeu; a foto não pode mais ser trocada.",
        )

    nova = _ler_foto_enviada(arquivo)
    anterior = encomenda.foto_arquivo
    encomenda.foto_arquivo = nova
    db.commit()
    arquivos.apagar_privado(arquivos.PORTARIA, anterior)
    db.refresh(encomenda)
    return _encomenda_saida(encomenda)


@router.get("/encomendas/{encomenda_id}/foto", summary="Foto da encomenda")
def foto_encomenda(
    encomenda_id: int,
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> FileResponse:
    encomenda = db.get(Encomenda, encomenda_id)
    if encomenda is None or not _pode_ver_foto(
        db, usuario, encomenda.unidade, "registrar_encomendas"
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto não encontrada.")
    return _entregar_foto(encomenda.foto_arquivo)


# ── Ocorrências ──────────────────────────────────────────────────────
@router.post(
    "/ocorrencias",
    response_model=OcorrenciaSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Abre uma ocorrência",
)
def abrir_ocorrencia(
    dados: OcorrenciaEntrada,
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> OcorrenciaSaida:
    # O porteiro só registra ocorrência se o síndico liberou (seção 12).
    exigir_permissao_do_porteiro(db, usuario, "registrar_ocorrencias")

    ocorrencia = Ocorrencia(
        condominio_id=usuario.condominio_id,
        aberta_por_id=usuario.id,
        unidade_id=usuario.unidade_id,
        **dados.model_dump(),
    )
    db.add(ocorrencia)
    db.commit()
    db.refresh(ocorrencia)
    return _ocorrencia_saida(db, ocorrencia)


def _ocorrencia_saida(db: Session, o: Ocorrencia) -> OcorrenciaSaida:
    unidade = db.get(Unidade, o.unidade_id) if o.unidade_id else None
    return OcorrenciaSaida(
        id=o.id, titulo=o.titulo, descricao=o.descricao, categoria=o.categoria,
        local=o.local, prioridade=o.prioridade,
        foto_url=f"/portaria/ocorrencias/{o.id}/foto" if o.foto_arquivo else None,
        status=o.status, aberta_por_id=o.aberta_por_id,
        aberta_por_nome=o.aberta_por.nome,
        unidade=unidade.identificacao if unidade else None,
        resposta=o.resposta, respondida_em=o.respondida_em, criado_em=o.criado_em,
    )


@router.get("/ocorrencias", response_model=list[OcorrenciaSaida], summary="Lista as ocorrências")
def listar_ocorrencias(
    status_ocorrencia: StatusOcorrencia | None = Query(default=None, alias="status"),
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> list[OcorrenciaSaida]:
    exigir_permissao_do_porteiro(db, usuario, "registrar_ocorrencias")
    consulta = select(Ocorrencia).where(Ocorrencia.condominio_id == usuario.condominio_id)
    # O morador acompanha só o que ele mesmo abriu.
    if usuario.papel == Papel.MORADOR:
        consulta = consulta.where(Ocorrencia.aberta_por_id == usuario.id)
    if status_ocorrencia is not None:
        consulta = consulta.where(Ocorrencia.status == status_ocorrencia)

    return [
        _ocorrencia_saida(db, o)
        for o in db.scalars(consulta.order_by(Ocorrencia.id.desc())).all()
    ]


def _ocorrencia_visivel(db: Session, usuario: Usuario, ocorrencia_id: int) -> Ocorrencia:
    """A ocorrência, se quem pede pode vê-la — as mesmas regras da lista."""
    ocorrencia = db.get(Ocorrencia, ocorrencia_id)
    visivel = ocorrencia is not None and ocorrencia.condominio_id == usuario.condominio_id and (
        usuario.papel == Papel.SINDICO
        or ocorrencia.aberta_por_id == usuario.id
        or (usuario.papel == Papel.PORTEIRO
            and porteiro_tem_permissao(db, usuario, "registrar_ocorrencias"))
    )
    if not visivel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ocorrência não encontrada."
        )
    return ocorrencia


@router.put(
    "/ocorrencias/{ocorrencia_id}/foto",
    response_model=OcorrenciaSaida,
    summary="Anexa uma foto à ocorrência",
)
def enviar_foto_ocorrencia(
    ocorrencia_id: int,
    arquivo: UploadFile = File(..., description="Imagem JPG, PNG ou WebP"),
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> OcorrenciaSaida:
    ocorrencia = _ocorrencia_visivel(db, usuario, ocorrencia_id)
    # Só quem abriu anexa, e só enquanto ninguém respondeu: a foto é a
    # prova do que foi relatado, e o síndico decide olhando para ela.
    if ocorrencia.aberta_por_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só quem abriu a ocorrência pode anexar a foto.",
        )
    if ocorrencia.respondida_em is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A ocorrência já foi respondida; a foto não pode mais ser trocada.",
        )

    nova = _ler_foto_enviada(arquivo, arquivos.OCORRENCIAS)
    anterior = ocorrencia.foto_arquivo
    ocorrencia.foto_arquivo = nova
    db.commit()
    arquivos.apagar_privado(arquivos.OCORRENCIAS, anterior)
    db.refresh(ocorrencia)
    return _ocorrencia_saida(db, ocorrencia)


@router.get("/ocorrencias/{ocorrencia_id}/foto", summary="Foto da ocorrência")
def foto_ocorrencia(
    ocorrencia_id: int,
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> FileResponse:
    ocorrencia = _ocorrencia_visivel(db, usuario, ocorrencia_id)
    return _entregar_foto(ocorrencia.foto_arquivo, arquivos.OCORRENCIAS)


@router.post(
    "/ocorrencias/{ocorrencia_id}/resposta",
    response_model=OcorrenciaSaida,
    summary="O síndico responde uma ocorrência",
)
def responder_ocorrencia(
    ocorrencia_id: int,
    dados: RespostaOcorrencia,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> OcorrenciaSaida:
    ocorrencia = db.get(Ocorrencia, ocorrencia_id)
    if ocorrencia is None or ocorrencia.condominio_id != sindico.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ocorrência não encontrada."
        )

    ocorrencia.status = dados.status
    ocorrencia.resposta = dados.resposta
    ocorrencia.respondida_por_id = sindico.id
    ocorrencia.respondida_em = _agora()

    db.commit()
    db.refresh(ocorrencia)
    return _ocorrencia_saida(db, ocorrencia)

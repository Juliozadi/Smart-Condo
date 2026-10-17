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

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import exists, func, or_, select, update
from sqlalchemy.orm import Session, contains_eager, selectinload

from app.api.deps import (
    exigir_condominio, exigir_papel, exigir_permissao_do_porteiro, exigir_permissao_porteiro,
    porteiro_tem_permissao,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.tempo import hoje_local
from app.models.condominio import Unidade
from app.models.enums import (
    CanalVerificacao, Papel, StatusEncomenda, StatusOcorrencia, StatusUsuario, StatusVisitante,
)
from app.models.portaria import AutorizacaoVisita, Encomenda, Ocorrencia, Visitante
from app.models.usuario import Usuario
from app.schemas.portaria import (
    AutorizacaoEntrada, AutorizacaoSaida, ConfirmacaoVisitante, EncomendaEntrada, EncomendaSaida,
    EntregaEncomenda, OcorrenciaEntrada, OcorrenciaSaida, RespostaOcorrencia, RetiradaEncomenda,
    VisitanteEntrada, VisitanteSaida,
)
from app.services import arquivos, notificacao

router = APIRouter(prefix="/portaria", tags=["Portaria"])


def _agora() -> datetime:
    return datetime.now(timezone.utc)


# Quanto o visitante espera a resposta do morador. Depois disso ele vira
# "sem resposta": não fica aguardando para sempre no painel da portaria, e
# o morador não o confirma dias depois (a entrada seria registrada na hora).
PRAZO_RESPOSTA = timedelta(hours=2)


def _expirar_sem_resposta(db: Session, condominio_id: int) -> None:
    db.execute(
        update(Visitante)
        .where(
            Visitante.status == StatusVisitante.AGUARDANDO_CONFIRMACAO,
            Visitante.criado_em < _agora() - PRAZO_RESPOSTA,
            Visitante.unidade_id.in_(
                select(Unidade.id).where(Unidade.condominio_id == condominio_id)
            ),
        )
        .values(status=StatusVisitante.SEM_RESPOSTA)
        .execution_options(synchronize_session=False)
    )
    db.commit()


def _unidade_do_condominio(db: Session, usuario: Usuario, unidade_id: int) -> Unidade:
    unidade = db.get(Unidade, unidade_id)
    # A pendente (autocadastro ainda não aprovado) não existe para a portaria.
    if (unidade is None or unidade.condominio_id != usuario.condominio_id
            or unidade.pendente):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada."
        )
    return unidade


def _moradores(db: Session, unidade: Unidade) -> list[Usuario]:
    """Quem mora na unidade agora: o morador que se mudou (inativado) ou
    teve o cadastro recusado não recebe mais os visitantes e as encomendas
    do apartamento."""
    return list(db.scalars(
        select(Usuario).where(
            Usuario.unidade_id == unidade.id, Usuario.papel == Papel.MORADOR,
            Usuario.status == StatusUsuario.ATIVO,
        )
    ).all())


def _avisar_moradores(db: Session, unidade: Unidade, titulo: str, mensagem: str) -> None:
    for morador in _moradores(db, unidade):
        notificacao.notificar(morador.email, CanalVerificacao.EMAIL, titulo, mensagem)


def _avisar_sindico(db: Session, unidade: Unidade, titulo: str, mensagem: str) -> None:
    """O apartamento está vazio no sistema (à venda, ou o novo morador ainda
    não se cadastrou): quem fica sabendo é o síndico atual."""
    sindico = db.scalar(select(Usuario).where(
        Usuario.condominio_id == unidade.condominio_id, Usuario.papel == Papel.SINDICO,
        Usuario.status == StatusUsuario.ATIVO,
    ))
    if sindico is not None:
        notificacao.notificar(sindico.email, CanalVerificacao.EMAIL, titulo, mensagem)


def _visitante_saida(v: Visitante, unidade: Unidade | None = None) -> VisitanteSaida:
    return VisitanteSaida(
        id=v.id, unidade_id=v.unidade_id,
        unidade=(unidade or v.unidade).identificacao,
        nome=v.nome, documento=v.documento, tipo_visita=v.tipo_visita,
        placa_veiculo=v.placa_veiculo,
        foto_url=f"/portaria/visitantes/{v.id}/foto" if v.foto_arquivo else None,
        status=v.status,
        entrada_em=v.entrada_em, saida_em=v.saida_em,
        confirmado_em=v.confirmado_em, autorizacao_id=v.autorizacao_id,
        criado_em=v.criado_em,
    )


def _encomenda_saida(e: Encomenda) -> EncomendaSaida:
    return EncomendaSaida(
        id=e.id, unidade_id=e.unidade_id, unidade=e.unidade.identificacao,
        remetente=e.remetente, tipo_volume=e.tipo_volume,
        codigo_rastreio=e.codigo_rastreio, observacoes=e.observacoes,
        foto_url=f"/portaria/encomendas/{e.id}/foto" if e.foto_arquivo else None,
        status=e.status, recebida_em=e.recebida_em,
        retirada_em=e.retirada_em, retirado_por_nome=e.retirado_por_nome,
        entregue_por_nome=e.entregue_por.nome if e.entregue_por else None,
        criado_em=e.criado_em,
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


# O morador vê o que chegou para a unidade desde que passou a morar nela
# (usuarios.unidade_desde): o morador novo, o transferido e o que voltou não
# veem os visitantes (nome, CPF, foto) nem as encomendas de quem estava lá
# antes. A encomenda que ainda aguarda retirada aparece, porque o volume
# está na portaria e ele pode dizer que não é dele.
def _visitante_do_morador(v: Visitante, morador: Usuario) -> bool:
    return v.unidade_id == morador.unidade_id and v.criado_em >= morador.unidade_desde


def _encomenda_do_morador(e: Encomenda, morador: Usuario) -> bool:
    return e.unidade_id == morador.unidade_id and (
        e.criado_em >= morador.unidade_desde or e.status == StatusEncomenda.AGUARDANDO_RETIRADA
    )


def _pode_ver_foto(db: Session, usuario: Usuario, unidade: Unidade, permissao: str,
                   do_morador: bool) -> bool:
    if unidade.condominio_id != usuario.condominio_id:
        return False
    if usuario.papel == Papel.SINDICO:
        return True
    if usuario.papel == Papel.MORADOR:
        return do_morador
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
    # Ninguém mora lá pelo sistema: não há quem confirme, e o visitante
    # não fica duas horas esperando. O registro fica, como "sem resposta".
    sem_morador = not _moradores(db, unidade)

    visitante = Visitante(
        **dados.model_dump(exclude={"autorizacao_id"}),
        registrado_por_id=usuario.id,
        status=(StatusVisitante.SEM_RESPOSTA if sem_morador
                else StatusVisitante.AGUARDANDO_CONFIRMACAO),
    )
    autorizacao = None
    if dados.autorizacao_id is not None:
        # Depois do expurgo das fotos, que faz commit e soltaria a trava.
        autorizacao = _autorizacao_para_entrada(db, unidade, dados.autorizacao_id,
                                                dados.documento)
        agora = _agora()
        # Entra quem o morador autorizou, com o nome que ele deu; a
        # autorização é a resposta dele, dada antes.
        visitante.nome = autorizacao.nome
        visitante.autorizacao_id = autorizacao.id
        visitante.status = StatusVisitante.DENTRO
        visitante.entrada_em = agora
        visitante.confirmado_em = agora
        visitante.confirmado_por_id = autorizacao.autorizado_por_id
    db.add(visitante)
    db.commit()
    db.refresh(visitante)

    if autorizacao is not None:
        _avisar_moradores(
            db, unidade,
            "Visitante autorizado entrou",
            f"{visitante.nome} ({autorizacao.tipo}) entrou pela autorização deixada na portaria.",
        )
    elif sem_morador:
        _avisar_sindico(
            db, unidade,
            "Visitante para apartamento sem morador",
            f"{visitante.nome} chegou à portaria para o apto {unidade.identificacao}, que não "
            "tem morador ativo no sistema: não há quem confirme a entrada.",
        )
        return _visitante_saida(visitante, unidade).model_copy(update={"sem_morador": True})
    else:
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
    _expirar_sem_resposta(db, usuario.condominio_id)
    consulta = select(Visitante).join(Unidade).where(
        Unidade.condominio_id == usuario.condominio_id
    )
    # O morador só enxerga os visitantes da própria unidade, desde que mora nela.
    if usuario.papel == Papel.MORADOR:
        consulta = consulta.where(
            Visitante.unidade_id == usuario.unidade_id,
            Visitante.criado_em >= usuario.unidade_desde,
        )
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
    visitante = db.get(Visitante, visitante_id, with_for_update=True)
    # Quem responde é o morador da unidade visitada, ninguém mais.
    if visitante is None or not _visitante_do_morador(visitante, morador):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visitante não encontrado."
        )
    if (visitante.status == StatusVisitante.AGUARDANDO_CONFIRMACAO
            and visitante.criado_em < _agora() - PRAZO_RESPOSTA):
        visitante.status = StatusVisitante.SEM_RESPOSTA
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Passou o tempo de resposta: o visitante já não está esperando na portaria.",
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
    visitante = db.get(Visitante, visitante_id, with_for_update=True)
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
    visitante = db.get(Visitante, visitante_id, with_for_update=True)
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
        db, usuario, visitante.unidade, "registrar_visitantes",
        do_morador=_visitante_do_morador(visitante, usuario),
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto não encontrada.")
    return _entregar_foto(visitante.foto_arquivo)


# ── Autorização prévia de visita ─────────────────────────────────────
# A diarista de toda terça, o pedreiro da reforma, os convidados da festa:
# o morador deixa a entrada liberada e a portaria registra sem esperar a
# resposta dele. Quem autoriza é quem mora no apartamento agora: a
# autorização de quem se mudou deixa de valer, sem ninguém precisar
# lembrar de revogá-la.

# Quantas autorizações em vigor cada apartamento pode ter. A lista de
# convidados de uma festa cabe; milhares, por engano ou abuso, não.
LIMITE_AUTORIZACOES = 60


def _autorizador_mora_la():
    """Condição SQL: quem autorizou ainda mora no apartamento — ativo,
    na mesma unidade e desde antes de autorizar (o que se mudou e voltou
    não ressuscita as autorizações antigas)."""
    return exists().where(
        Usuario.id == AutorizacaoVisita.autorizado_por_id,
        Usuario.unidade_id == AutorizacaoVisita.unidade_id,
        Usuario.papel == Papel.MORADOR,
        Usuario.status == StatusUsuario.ATIVO,
        Usuario.unidade_desde <= AutorizacaoVisita.criado_em,
    )


def _vale_no_dia(a: AutorizacaoVisita, dia: date) -> bool:
    return (not a.inativo and a.valida_de <= dia <= a.valida_ate
            and (not a.dias_semana or str(dia.isoweekday()) in a.dias_semana))


def _documento_mascarado(documento: str | None) -> str | None:
    """A portaria vê só o meio do CPF: ela digita o do documento que a
    pessoa apresenta, e o sistema confere — copiar da tela não serve."""
    if not documento:
        return None
    return f"***.{documento[3:6]}.{documento[6:9]}-**"


def _autorizacao_saida(a: AutorizacaoVisita, hoje: date, *, para_morador: bool,
                       ja_dentro: bool = False) -> AutorizacaoSaida:
    return AutorizacaoSaida(
        id=a.id, unidade_id=a.unidade_id, unidade=a.unidade.identificacao,
        nome=a.nome,
        documento=a.documento if para_morador else _documento_mascarado(a.documento),
        tipo=a.tipo, valida_de=a.valida_de, valida_ate=a.valida_ate,
        dias_semana=[int(d) for d in a.dias_semana] if a.dias_semana else None,
        observacao=a.observacao,
        autorizado_por_nome=a.autorizado_por.nome if a.autorizado_por else None,
        vale_hoje=_vale_no_dia(a, hoje), ja_dentro=ja_dentro, criado_em=a.criado_em,
    )


def _autorizacao_para_entrada(db: Session, unidade: Unidade, autorizacao_id: int,
                              documento: str) -> AutorizacaoVisita:
    """Confere se a autorização libera esta entrada, agora.

    Trava a autorização: duas portarias registrando a mesma pessoa ao
    mesmo tempo não a colocam "dentro" duas vezes.
    """
    autorizacao = db.get(AutorizacaoVisita, autorizacao_id, with_for_update=True)
    if autorizacao is None or autorizacao.unidade_id != unidade.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Autorização não encontrada para esta unidade.")
    if autorizacao.inativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Esta autorização foi revogada pelo morador.")
    if not db.scalar(select(_autorizador_mora_la()).where(
            AutorizacaoVisita.id == autorizacao.id)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta autorização não vale mais: quem autorizou não mora mais na unidade.",
        )
    if not _vale_no_dia(autorizacao, hoje_local()):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Esta autorização não vale hoje.")
    if autorizacao.documento and autorizacao.documento != documento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O documento apresentado não confere com o da autorização.",
        )
    if db.scalar(select(Visitante.id).where(
            Visitante.autorizacao_id == autorizacao.id,
            Visitante.status == StatusVisitante.DENTRO).limit(1)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Esta pessoa já está dentro do condomínio.")
    return autorizacao


@router.post(
    "/autorizacoes",
    response_model=AutorizacaoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="O morador autoriza um visitante com antecedência",
)
def autorizar_visita(
    dados: AutorizacaoEntrada,
    morador: Usuario = Depends(exigir_papel(Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> AutorizacaoSaida:
    # Trava o apartamento: dois pedidos ao mesmo tempo não passam juntos
    # pelo limite.
    unidade = (db.get(Unidade, morador.unidade_id, with_for_update=True)
               if morador.unidade_id else None)
    if unidade is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Seu cadastro não está ligado a um apartamento.")
    hoje = hoje_local()
    em_vigor = db.scalar(
        select(func.count()).select_from(AutorizacaoVisita).where(
            AutorizacaoVisita.unidade_id == unidade.id,
            AutorizacaoVisita.inativo_em.is_(None),
            AutorizacaoVisita.valida_ate >= hoje,
            _autorizador_mora_la(),
        )
    )
    if em_vigor >= LIMITE_AUTORIZACOES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Seu apartamento chegou ao limite de {LIMITE_AUTORIZACOES} autorizações "
                   "em vigor. Revogue as que não são mais necessárias.",
        )

    autorizacao = AutorizacaoVisita(
        **dados.model_dump(exclude={"dias_semana"}),
        dias_semana="".join(str(d) for d in dados.dias_semana) if dados.dias_semana else None,
        unidade_id=unidade.id,
        autorizado_por_id=morador.id,
    )
    db.add(autorizacao)
    db.commit()
    db.refresh(autorizacao)
    return _autorizacao_saida(autorizacao, hoje, para_morador=True)


@router.get(
    "/autorizacoes",
    response_model=list[AutorizacaoSaida],
    summary="Lista as autorizações de visita",
)
def listar_autorizacoes(
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> list[AutorizacaoSaida]:
    """O morador vê as do apartamento que ainda vão valer; a portaria e o
    síndico, as que valem hoje no condomínio."""
    exigir_permissao_do_porteiro(db, usuario, "registrar_visitantes")
    hoje = hoje_local()
    consulta = (
        select(AutorizacaoVisita).join(AutorizacaoVisita.unidade)
        .options(contains_eager(AutorizacaoVisita.unidade),
                 selectinload(AutorizacaoVisita.autorizado_por))
        .where(
            Unidade.condominio_id == usuario.condominio_id,
            AutorizacaoVisita.inativo_em.is_(None),
            AutorizacaoVisita.valida_ate >= hoje,
            _autorizador_mora_la(),
        )
    )
    para_morador = usuario.papel == Papel.MORADOR
    if para_morador:
        consulta = consulta.where(AutorizacaoVisita.unidade_id == usuario.unidade_id)
        ordem = (AutorizacaoVisita.valida_de, AutorizacaoVisita.id)
    else:
        consulta = consulta.where(
            AutorizacaoVisita.valida_de <= hoje,
            or_(AutorizacaoVisita.dias_semana.is_(None),
                AutorizacaoVisita.dias_semana.contains(str(hoje.isoweekday()))),
        )
        ordem = (Unidade.bloco, Unidade.numero, AutorizacaoVisita.nome)
    autorizacoes = db.scalars(consulta.order_by(*ordem)).all()

    dentro = set(db.scalars(select(Visitante.autorizacao_id).where(
        Visitante.autorizacao_id.in_([a.id for a in autorizacoes]),
        Visitante.status == StatusVisitante.DENTRO,
    ))) if autorizacoes else set()
    return [_autorizacao_saida(a, hoje, para_morador=para_morador, ja_dentro=a.id in dentro)
            for a in autorizacoes]


@router.delete(
    "/autorizacoes/{autorizacao_id}",
    response_model=AutorizacaoSaida,
    summary="O morador revoga uma autorização de visita",
)
def revogar_autorizacao(
    autorizacao_id: int,
    morador: Usuario = Depends(exigir_papel(Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> AutorizacaoSaida:
    autorizacao = db.get(AutorizacaoVisita, autorizacao_id, with_for_update=True)
    # Qualquer morador do apartamento revoga (a diarista foi dispensada);
    # a de quem morava lá antes não aparece para ninguém, nem aqui.
    if (autorizacao is None or autorizacao.unidade_id != morador.unidade_id
            or not db.scalar(select(_autorizador_mora_la()).where(
                AutorizacaoVisita.id == autorizacao.id))):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Autorização não encontrada.")
    if autorizacao.inativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Esta autorização já foi revogada.")
    autorizacao.inativo_em = _agora()
    autorizacao.inativado_por_id = morador.id
    db.commit()
    db.refresh(autorizacao)
    return _autorizacao_saida(autorizacao, hoje_local(), para_morador=True)


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
    if not _moradores(db, unidade):
        # A encomenda do morador que se mudou fica na portaria: sem ninguém
        # para retirá-la, o síndico precisa saber.
        _avisar_sindico(
            db, unidade,
            "Encomenda para apartamento sem morador",
            f"{encomenda.tipo_volume} de {encomenda.remetente}{rastreio} chegou para o apto "
            f"{unidade.identificacao}, que não tem morador ativo no sistema.",
        )
        return _encomenda_saida(encomenda).model_copy(update={"sem_morador": True})
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
        consulta = consulta.where(
            Encomenda.unidade_id == usuario.unidade_id,
            (Encomenda.criado_em >= usuario.unidade_desde)
            | (Encomenda.status == StatusEncomenda.AGUARDANDO_RETIRADA),
        )
    if status_encomenda is not None:
        consulta = consulta.where(Encomenda.status == status_encomenda)

    consulta = consulta.options(
        contains_eager(Encomenda.unidade), selectinload(Encomenda.entregue_por)
    )
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
    encomenda = db.get(Encomenda, encomenda_id, with_for_update=True)
    if encomenda is None or not _encomenda_do_morador(encomenda, morador):
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


@router.post(
    "/encomendas/{encomenda_id}/entrega",
    response_model=EncomendaSaida,
    summary="A portaria entrega a encomenda em mãos",
)
def entregar_encomenda(
    encomenda_id: int,
    dados: EntregaEncomenda,
    usuario: Usuario = Depends(exigir_permissao_porteiro("registrar_encomendas")),
    db: Session = Depends(get_db),
) -> EncomendaSaida:
    """Só o morador, pelo app, dava baixa: entregue em mãos, a encomenda
    ficava "aguardando retirada" para sempre no painel da portaria. Os
    moradores da unidade são avisados de quem levou."""
    encomenda = db.get(Encomenda, encomenda_id, with_for_update=True)
    if encomenda is None or encomenda.unidade.condominio_id != usuario.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Encomenda não encontrada."
        )
    if encomenda.status != StatusEncomenda.AGUARDANDO_RETIRADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Esta encomenda já foi respondida."
        )
    encomenda.status = StatusEncomenda.RETIRADA
    encomenda.retirada_em = _agora()
    encomenda.entregue_por_id = usuario.id
    encomenda.retirado_por_nome = dados.retirado_por_nome
    db.commit()
    db.refresh(encomenda)
    _avisar_moradores(
        db, encomenda.unidade, "Encomenda retirada na portaria",
        f"{encomenda.tipo_volume} de {encomenda.remetente}: entregue a "
        f"{dados.retirado_por_nome} por {usuario.nome}.",
    )
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
    encomenda = db.get(Encomenda, encomenda_id, with_for_update=True)
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
        db, usuario, encomenda.unidade, "registrar_encomendas",
        do_morador=_encomenda_do_morador(encomenda, usuario),
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
    # Relê travada: a resposta do síndico pode estar chegando agora.
    db.refresh(ocorrencia, with_for_update=True)
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
    ocorrencia = db.get(Ocorrencia, ocorrencia_id, with_for_update=True)
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

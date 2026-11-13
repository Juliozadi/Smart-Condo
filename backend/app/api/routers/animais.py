"""Animais de estimação dos apartamentos.

O morador que mora no apartamento cadastra os animais dele; o síndico vê
todos, cadastra por qualquer apartamento e lembra quem está com a vacina
antirrábica vencida ou sem registro; a portaria consulta, para saber de
quem é o cachorro solto na garagem. Como os carros, o cadastro vale
enquanto quem o fez mora no apartamento: quem se muda leva os animais
da lista sem ninguém precisar removê-los.
"""
from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import conferir_que_mora, exigir_papel
from app.core.database import get_db
from app.core.tempo import agora_utc, hoje_local
from app.models.animal import Animal
from app.models.condominio import Unidade
from app.models.enums import Papel, StatusUsuario
from app.models.usuario import Usuario
from app.schemas.animal import AnimalAtualizacao, AnimalEntrada, AnimalSaida, LembreteSaida
from app.schemas.comuns import Mensagem
from app.services import destinatarios

router = APIRouter(prefix="/animais", tags=["Animais de estimação"])

quem_ve = exigir_papel(Papel.MORADOR, Papel.SINDICO, Papel.PORTEIRO)
quem_cadastra = exigir_papel(Papel.MORADOR, Papel.SINDICO)
so_sindico = exigir_papel(Papel.SINDICO)
# Um limite contra erro e abuso, não contra famílias grandes.
LIMITE_ANIMAIS = 10
# Um lembrete por animal por semana, no máximo.
INTERVALO_LEMBRETE = timedelta(days=7)
_hoje = hoje_local
_agora = agora_utc

ESPECIES = {"cao": "cachorro", "gato": "gato", "ave": "ave", "outro": "animal"}


def _dono_mora_la():
    """O cadastro vale enquanto quem o fez mora no apartamento (desde antes
    de cadastrar), ou se foi o síndico."""
    return or_(
        exists().where(Usuario.id == Animal.cadastrado_por_id, Usuario.papel == Papel.SINDICO),
        exists().where(
            Usuario.id == Animal.cadastrado_por_id, Usuario.unidade_id == Animal.unidade_id,
            Usuario.papel == Papel.MORADOR, Usuario.status == StatusUsuario.ATIVO,
            Usuario.reside.is_(True), Usuario.unidade_desde <= Animal.criado_em,
        ),
    )


def _cadastrados(condominio_id: int):
    return (
        select(Animal)
        .options(selectinload(Animal.unidade), selectinload(Animal.cadastrado_por))
        .where(Animal.condominio_id == condominio_id, Animal.inativo_em.is_(None),
               _dono_mora_la())
    )


def _situacao_vacina(a: Animal) -> str:
    if a.vacina_antirrabica_ate is None:
        return "sem_registro"
    return "vencida" if a.vacina_antirrabica_ate < _hoje() else "em_dia"


def _saida(a: Animal, usuario: Usuario) -> AnimalSaida:
    return AnimalSaida(
        id=a.id, unidade_id=a.unidade_id, unidade=a.unidade.identificacao, nome=a.nome,
        especie=a.especie, raca=a.raca, porte=a.porte, cor=a.cor,
        vacina_antirrabica_ate=a.vacina_antirrabica_ate, vacina=_situacao_vacina(a),
        observacao=a.observacao,
        cadastrado_por_nome=a.cadastrado_por.nome if a.cadastrado_por else None,
        lembrete_vacina_em=a.lembrete_vacina_em if usuario.papel == Papel.SINDICO else None,
        pode_editar=usuario.papel == Papel.SINDICO or (
            usuario.papel == Papel.MORADOR and a.unidade_id == usuario.unidade_id),
    )


def _animal(db: Session, animal_id: int, usuario: Usuario) -> Animal:
    a = db.scalar(_cadastrados(usuario.condominio_id).where(Animal.id == animal_id)
                  .with_for_update(of=Animal))
    if a is None or (usuario.papel == Papel.MORADOR and a.unidade_id != usuario.unidade_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Animal não encontrado.")
    return a


@router.get("", response_model=list[AnimalSaida], summary="Lista os animais")
def listar(
    unidade_id: int | None = Query(default=None),
    vacina: str | None = Query(default=None, pattern="^(pendente)$",
                               description="pendente: vencida ou sem registro"),
    usuario: Usuario = Depends(quem_ve),
    db: Session = Depends(get_db),
) -> list[AnimalSaida]:
    """O morador vê os do apartamento dele; o síndico e a portaria, os de
    todos."""
    consulta = _cadastrados(usuario.condominio_id)
    if usuario.papel == Papel.MORADOR:
        conferir_que_mora(usuario)
        consulta = consulta.where(Animal.unidade_id == usuario.unidade_id)
    elif unidade_id is not None:
        consulta = consulta.where(Animal.unidade_id == unidade_id)
    if vacina == "pendente":
        consulta = consulta.where(or_(Animal.vacina_antirrabica_ate.is_(None),
                                      Animal.vacina_antirrabica_ate < _hoje()))
    animais = db.scalars(consulta.join(Unidade, Unidade.id == Animal.unidade_id)
                         .order_by(Unidade.bloco, Unidade.numero, Animal.nome)).all()
    return [_saida(a, usuario) for a in animais]


@router.post("", response_model=AnimalSaida, status_code=status.HTTP_201_CREATED,
             summary="Cadastra um animal do apartamento")
def cadastrar(
    dados: AnimalEntrada,
    usuario: Usuario = Depends(quem_cadastra),
    db: Session = Depends(get_db),
) -> AnimalSaida:
    if usuario.papel == Papel.MORADOR:
        conferir_que_mora(usuario)
        unidade_id = usuario.unidade_id
    else:
        if dados.unidade_id is None:
            raise HTTPException(status_code=422, detail="Informe o apartamento do animal.")
        unidade = db.get(Unidade, dados.unidade_id)
        if (unidade is None or unidade.condominio_id != usuario.condominio_id
                or unidade.pendente):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Unidade não encontrada.")
        unidade_id = unidade.id
    # Dois cadastros ao mesmo tempo no mesmo apartamento contam um depois
    # do outro, e o limite vale.
    db.execute(select(func.pg_advisory_xact_lock(usuario.condominio_id, unidade_id)))
    do_apartamento = db.scalar(select(func.count()).select_from(
        _cadastrados(usuario.condominio_id).where(Animal.unidade_id == unidade_id).subquery()))
    if do_apartamento >= LIMITE_ANIMAIS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O apartamento chegou ao limite de {LIMITE_ANIMAIS} animais cadastrados. "
                   "Remova os que não estão mais com vocês.")
    a = Animal(condominio_id=usuario.condominio_id, unidade_id=unidade_id,
               cadastrado_por_id=usuario.id,
               **dados.model_dump(exclude={"unidade_id"}))
    db.add(a)
    db.commit()
    return _saida(_animal(db, a.id, usuario), usuario)


@router.put("/{animal_id}", response_model=AnimalSaida, summary="Corrige o cadastro do animal")
def atualizar(
    animal_id: int,
    dados: AnimalAtualizacao,
    usuario: Usuario = Depends(quem_cadastra),
    db: Session = Depends(get_db),
) -> AnimalSaida:
    conferir_que_mora(usuario)
    a = _animal(db, animal_id, usuario)
    novos = dados.model_dump(exclude_unset=True)
    if "vacina_antirrabica_ate" in novos and novos["vacina_antirrabica_ate"] != a.vacina_antirrabica_ate:
        # Vacina nova: um próximo lembrete vale quando ela vencer.
        a.lembrete_vacina_em = None
    for campo, valor in novos.items():
        setattr(a, campo, valor)
    db.commit()
    return _saida(_animal(db, animal_id, usuario), usuario)


@router.delete("/{animal_id}", response_model=Mensagem, summary="Remove o animal da lista")
def remover(
    animal_id: int,
    usuario: Usuario = Depends(quem_cadastra),
    db: Session = Depends(get_db),
) -> Mensagem:
    conferir_que_mora(usuario)
    a = _animal(db, animal_id, usuario)
    # Nada é apagado: fica guardado, com quem removeu e quando.
    a.inativo_em = _agora()
    a.inativado_por_id = usuario.id
    db.commit()
    return Mensagem(detalhe="Animal removido da lista do apartamento.")


@router.post("/lembrete-vacina", response_model=LembreteSaida,
             summary="Lembra os apartamentos da vacina antirrábica vencida")
def lembrar_vacina(
    sindico: Usuario = Depends(so_sindico),
    db: Session = Depends(get_db),
) -> LembreteSaida:
    agora = _agora()
    pendentes = db.scalars(
        _cadastrados(sindico.condominio_id)
        .where(or_(Animal.vacina_antirrabica_ate.is_(None),
                   Animal.vacina_antirrabica_ate < _hoje()),
               or_(Animal.lembrete_vacina_em.is_(None),
                   Animal.lembrete_vacina_em < agora - INTERVALO_LEMBRETE))
        .with_for_update(of=Animal)).all()
    por_unidade: dict[int, list[Animal]] = {}
    for a in pendentes:
        por_unidade.setdefault(a.unidade_id, []).append(a)
        a.lembrete_vacina_em = agora
    avisos = []
    for unidade_id, animais in por_unidade.items():
        nomes = ", ".join(f"{a.nome} ({ESPECIES[a.especie.value]})" for a in animais)
        texto = (f"O regimento pede a vacina antirrábica em dia. Atualize no SmartCondo a "
                 f"validade da vacina de: {nomes}.")
        avisos.append((unidade_id, texto))
    db.commit()
    for unidade_id, texto in avisos:
        destinatarios.avisar(destinatarios.moradores_da_unidade(db, unidade_id),
                             "Vacina dos animais", texto)
    return LembreteSaida(animais=len(pendentes), apartamentos=len(por_unidade))

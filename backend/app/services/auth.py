"""Regras de cadastro, confirmação, login e recuperação de senha.

Documentação, seção 12 — casos de uso "Cadastro", "Login do usuário" e
"Esqueci minha senha".
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    conferir_codigo, conferir_senha, gerar_codigo_verificacao, gerar_hash_codigo,
    gerar_hash_senha,
)
from app.models.enums import CanalVerificacao, FinalidadeCodigo, Papel, StatusUsuario
from app.models.usuario import CodigoVerificacao, Usuario
from app.services import notificacao

MAX_TENTATIVAS_CODIGO = 5


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def buscar_por_email(db: Session, email: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(Usuario.email == email.lower()))


def buscar_por_cpf(db: Session, cpf: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(Usuario.cpf == cpf))


def garantir_email_e_cpf_livres(db: Session, email: str, cpf: str) -> None:
    if buscar_por_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um cadastro com este e-mail.",
        )
    if buscar_por_cpf(db, cpf):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um cadastro com este CPF.",
        )


class CodigoMuitoFrequente(Exception):
    """Pediu código novo antes do intervalo mínimo ou além do limite da hora."""


def _pode_emitir(db: Session, usuario: Usuario, finalidade: FinalidadeCodigo) -> bool:
    agora = _agora()
    validade = timedelta(minutes=settings.CODIGO_VERIFICACAO_EXPIRA_MIN)
    # A tabela guarda só a validade; a emissão é a validade menos o prazo.
    emissoes = [
        c.expira_em - validade
        for c in db.scalars(
            select(CodigoVerificacao).where(
                CodigoVerificacao.usuario_id == usuario.id,
                CodigoVerificacao.finalidade == finalidade,
                CodigoVerificacao.expira_em > agora - timedelta(hours=1) + validade,
            )
        )
    ]
    if len(emissoes) >= settings.CODIGO_MAX_POR_HORA:
        return False
    intervalo = timedelta(seconds=settings.CODIGO_INTERVALO_S)
    return not any(e > agora - intervalo for e in emissoes)


def emitir_codigo(
    db: Session,
    usuario: Usuario,
    finalidade: FinalidadeCodigo,
    canal: CanalVerificacao,
) -> str:
    """Gera, guarda (em hash) e envia um novo código.

    Qualquer código pendente da mesma finalidade é invalidado, para que só o
    mais recente valha. Levanta CodigoMuitoFrequente se o limite de
    frequência foi atingido; nesse caso o código anterior continua valendo.
    """
    # Trava o usuário até o commit. Pedidos simultâneos passavam todos pelo
    # limite de frequência — dezenas de e-mails ou SMS de uma vez — e cada
    # um deixava o seu código valendo, já que não via os dos outros.
    db.execute(select(Usuario.id).where(Usuario.id == usuario.id).with_for_update())
    if not _pode_emitir(db, usuario, finalidade):
        raise CodigoMuitoFrequente()
    pendentes = db.scalars(
        select(CodigoVerificacao).where(
            CodigoVerificacao.usuario_id == usuario.id,
            CodigoVerificacao.finalidade == finalidade,
            CodigoVerificacao.consumido_em.is_(None),
        )
    ).all()
    for pendente in pendentes:
        pendente.consumido_em = _agora()

    destino = usuario.email if canal == CanalVerificacao.EMAIL else usuario.telefone
    codigo = gerar_codigo_verificacao()

    registro = CodigoVerificacao(
        usuario_id=usuario.id,
        codigo_hash=gerar_hash_codigo(codigo),
        finalidade=finalidade,
        canal=canal,
        expira_em=_agora() + timedelta(minutes=settings.CODIGO_VERIFICACAO_EXPIRA_MIN),
        destino=destino,
    )
    db.add(registro)
    db.flush()

    notificacao.enviar_codigo(destino, canal, codigo, finalidade.value)
    return codigo


def validar_codigo(
    db: Session,
    usuario: Usuario,
    codigo_informado: str,
    finalidade: FinalidadeCodigo,
) -> CodigoVerificacao:
    """Confere o código e o marca como consumido. Erra alto se não servir."""
    registro = db.scalar(
        select(CodigoVerificacao)
        .where(
            CodigoVerificacao.usuario_id == usuario.id,
            CodigoVerificacao.finalidade == finalidade,
            CodigoVerificacao.consumido_em.is_(None),
        )
        .order_by(CodigoVerificacao.id.desc())
        # Travado até o commit: palpites enviados ao mesmo tempo liam todos
        # a mesma contagem e passavam juntos — num teste, 33 palpites
        # conferidos contra um limite de 5. Assim eles entram um por vez.
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if registro is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não há código pendente. Solicite um novo.",
        )

    expira_em = registro.expira_em
    if expira_em.tzinfo is None:
        expira_em = expira_em.replace(tzinfo=timezone.utc)
    # Os três casos abaixo gravam ANTES de levantar a exceção. Sem o
    # commit, a requisição falha, o SQLAlchemy desfaz a sessão e a
    # contagem volta a zero — o limite de tentativas nunca fecharia e
    # o código de seis dígitos poderia ser descoberto por força bruta.
    # Quem chama só commita no caminho de sucesso.
    if expira_em < _agora():
        registro.consumido_em = _agora()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O código expirou. Solicite um novo.",
        )

    if registro.tentativas >= MAX_TENTATIVAS_CODIGO:
        registro.consumido_em = _agora()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas. Solicite um novo código.",
        )

    if not conferir_codigo(codigo_informado, registro.codigo_hash):
        registro.tentativas += 1
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código incorreto.",
        )

    registro.consumido_em = _agora()
    return registro


def status_apos_confirmacao(papel: Papel) -> StatusUsuario:
    """Depois de confirmar o código, o cadastro ainda espera o síndico.

    Só o morador se cadastra sozinho, e a tela "aguardando aprovação" do
    front-end existe para esse intervalo. Quem é criado por dentro do
    sistema (pelo administrador ou pelo síndico) já nasce ativo e nem passa
    por aqui.
    """
    return StatusUsuario.AGUARDANDO_APROVACAO


def _minutos_de_bloqueio_restantes(usuario: Usuario) -> int:
    """Quanto falta do bloqueio, arredondado para cima."""
    if usuario.bloqueado_ate is None:
        return 0
    # Mesma defesa que validar_codigo faz com expira_em: dependendo do
    # driver, o timestamp pode voltar sem fuso e a subtração estoura.
    bloqueado_ate = usuario.bloqueado_ate
    if bloqueado_ate.tzinfo is None:
        bloqueado_ate = bloqueado_ate.replace(tzinfo=timezone.utc)
    restante = bloqueado_ate - _agora()
    if restante.total_seconds() <= 0:
        return 0
    return max(1, -(-int(restante.total_seconds()) // 60))


def _contar_senha_errada(db: Session, usuario: Usuario) -> None:
    """Soma uma tentativa e tranca a conta ao estourar o limite."""
    usuario.tentativas_login += 1
    if usuario.tentativas_login >= settings.MAX_TENTATIVAS_LOGIN:
        usuario.bloqueado_ate = _agora() + timedelta(minutes=settings.BLOQUEIO_LOGIN_MIN)
        usuario.tentativas_login = 0
    # Precisa gravar aqui: quem chamou vai receber exceção e não commita.
    db.commit()


def autenticar(db: Session, email: str, senha: str) -> Usuario:
    """Valida as credenciais do login (seção 12).

    Sem limite de tentativas, adivinhar a senha é só questão de tempo.
    O bloqueio conta por conta, é temporário e some no primeiro acerto.

    Ele não esconde quais e-mails existem — o 429 só aparece para conta
    cadastrada. Mas isso não abre nada novo: o cadastro já responde "Já
    existe um cadastro com este e-mail". Limitar por IP, que resolveria
    os dois, depende de saber o IP real atrás do proxy.
    """
    # Travado até o commit, pelo mesmo motivo do código: senhas enviadas
    # ao mesmo tempo liam todas a mesma contagem, e o bloqueio nunca
    # disparava (40 senhas conferidas em paralelo, contra um limite de 5).
    usuario = db.scalar(
        select(Usuario)
        .where(Usuario.email == email.lower())
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    bloqueio_venceu = False

    if usuario is not None:
        faltam = _minutos_de_bloqueio_restantes(usuario)
        if faltam:
            # Antes de conferir a senha: conta trancada não gasta bcrypt.
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Muitas tentativas de login. Tente novamente em "
                    f"{faltam} minuto{'s' if faltam > 1 else ''}."
                ),
            )
        # O bloqueio venceu: marca para limpar, senão o carimbo vencido
        # fica no cadastro para sempre. A flag é necessária porque zerar
        # o campo aqui esconderia a mudança da condição lá embaixo.
        bloqueio_venceu = usuario.bloqueado_ate is not None

    # A mensagem é a mesma para e-mail inexistente e senha errada, para não
    # revelar quais e-mails estão cadastrados.
    if usuario is None or not conferir_senha(senha, usuario.senha_hash):
        if usuario is not None:
            _contar_senha_errada(db, usuario)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
        )

    if usuario.tentativas_login or bloqueio_venceu:
        usuario.tentativas_login = 0
        usuario.bloqueado_ate = None
        db.commit()
    return usuario


def encerrar_sessoes(usuario: Usuario) -> None:
    """Invalida todos os tokens já emitidos para o usuário."""
    usuario.versao_sessao = (usuario.versao_sessao or 0) + 1


def trocar_senha(db: Session, usuario: Usuario, senha_atual: str, nova_senha: str) -> None:
    """Exige a senha atual, e os erros contam para o mesmo bloqueio do
    login: sem isso, quem pegasse uma sessão aberta poderia testar senhas
    aqui à vontade."""
    # Relê travado: o usuário veio do token, lido antes, sem trava.
    db.refresh(usuario, with_for_update=True)
    faltam = _minutos_de_bloqueio_restantes(usuario)
    if faltam:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Muitas tentativas com a senha errada. Tente novamente em "
                f"{faltam} minuto{'s' if faltam > 1 else ''}."
            ),
        )
    if not conferir_senha(senha_atual, usuario.senha_hash):
        _contar_senha_errada(db, usuario)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha atual está incorreta.",
        )
    usuario.senha_hash = gerar_hash_senha(nova_senha)
    usuario.tentativas_login = 0
    usuario.bloqueado_ate = None
    encerrar_sessoes(usuario)
    db.flush()

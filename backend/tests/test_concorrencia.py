"""Requisições que chegam ao mesmo tempo.

A conferência ("o horário está livre?", "quanto falta pagar?") e a
gravação não são um passo só. Sem trava, duas requisições simultâneas
passam juntas pela conferência: o mesmo espaço ficava reservado duas
vezes no mesmo horário, e a mesma cobrança podia ser paga a mais. Estes
testes disparam as requisições em paralelo, contra o banco de verdade.
"""
from __future__ import annotations

import threading
from datetime import timedelta

from app.core.tempo import hoje_local
from tests.fixtures import cab, cadastrar_morador, CPFS
from tests.test_financeiro import gerar_cobranca
from tests.test_reservas import cenario, reservar  # noqa: F401


def ao_mesmo_tempo(n, acao):
    """Roda acao(i) em n threads, soltas juntas por uma barreira."""
    barreira = threading.Barrier(n)
    respostas = [None] * n

    def rodar(i):
        barreira.wait()
        respostas[i] = acao(i)

    threads = [threading.Thread(target=rodar, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return respostas


def test_mesmo_horario_so_uma_reserva_passa(cliente, cenario):
    _, tok_carla = cadastrar_morador(
        cliente, cenario["sindico"], cenario["cond"],
        email="carla@exemplo.com", cpf=CPFS[4], unidade="402",
    )
    _, tok_davi = cadastrar_morador(
        cliente, cenario["sindico"], cenario["cond"],
        email="davi@exemplo.com", cpf=CPFS[5], unidade="503",
    )
    moradores = [cenario["ana"], cenario["bruno"], tok_carla, tok_davi]
    salao = cenario["salao"]["id"]

    for dias in range(10, 16):
        dia = (hoje_local() + timedelta(days=dias)).isoformat()
        codigos = ao_mesmo_tempo(4, lambda i: reservar(
            cliente, moradores[i], salao, data=dia).status_code)
        assert sorted(codigos) == [201, 409, 409, 409], (dia, codigos)


def test_mesma_cobranca_nao_e_paga_a_mais(cliente, cenario):
    unidade = cliente.get(
        "/api/v1/condominios/meu/unidades", headers=cab(cenario["sindico"])
    ).json()[0]["id"]
    cobranca = gerar_cobranca(cliente, cenario["sindico"], unidade, valor="320.00").json()

    codigos = ao_mesmo_tempo(6, lambda i: cliente.post(
        f"/api/v1/financeiro/cobrancas/{cobranca['id']}/pagamentos",
        json={"valor": "200.00", "forma": "pix"}, headers=cab(cenario["sindico"]),
    ).status_code)
    # O primeiro paga 200; dos 120 que faltam, nenhum outro de 200 cabe.
    assert codigos.count(201) == 1, codigos

    pagamentos = cliente.get(
        f"/api/v1/financeiro/cobrancas/{cobranca['id']}/pagamentos",
        headers=cab(cenario["sindico"]),
    ).json()
    assert sum(float(p["valor"]) for p in pagamentos) == 200.0


def test_marcar_como_lido_ao_mesmo_tempo(cliente, cenario):
    comunicado = cliente.post(
        "/api/v1/comunicados",
        json={"titulo": "Aviso geral", "conteudo": "Conteúdo do aviso", "categoria": "geral"},
        headers=cab(cenario["sindico"]),
    ).json()
    codigos = ao_mesmo_tempo(6, lambda i: cliente.post(
        f"/api/v1/comunicados/{comunicado['id']}/leitura", headers=cab(cenario["ana"]),
    ).status_code)
    assert codigos == [200] * 6


def test_registro_duplicado_ao_mesmo_tempo_e_conflito(cliente, cenario):
    """A restrição de unicidade do banco barra o segundo; a resposta é 409,
    e não um erro do servidor."""
    unidade = cliente.get(
        "/api/v1/condominios/meu/unidades", headers=cab(cenario["sindico"])
    ).json()[0]["id"]
    codigos = ao_mesmo_tempo(6, lambda i: gerar_cobranca(
        cliente, cenario["sindico"], unidade).status_code)
    assert codigos.count(201) == 1, codigos
    assert set(codigos) <= {201, 409}, codigos


# ── Força bruta em paralelo ──────────────────────────────────────────
def test_senhas_em_paralelo_respeitam_o_limite(cliente, cenario):
    """Antes, 40 senhas enviadas juntas eram todas conferidas: cada uma
    lia a mesma contagem de erros, e o bloqueio nunca disparava."""
    from app.core.config import settings

    codigos = ao_mesmo_tempo(15, lambda i: cliente.post(
        "/api/v1/auth/login", json={"email": "ana@exemplo.com", "senha": f"errada{i:03d}"},
    ).status_code)
    assert codigos.count(401) == settings.MAX_TENTATIVAS_LOGIN, codigos
    assert codigos.count(429) == 15 - settings.MAX_TENTATIVAS_LOGIN


def test_palpites_do_codigo_em_paralelo_respeitam_o_limite(cliente, cenario):
    """O código de seis dígitos da recuperação de senha aceita cinco erros.
    Em paralelo, antes, passavam mais de trinta palpites."""
    from app.services.auth import MAX_TENTATIVAS_CODIGO

    r = cliente.post("/api/v1/auth/senha/recuperar", json={"email": "ana@exemplo.com"})
    assert r.status_code == 200, r.text

    respostas = ao_mesmo_tempo(15, lambda i: cliente.post(
        "/api/v1/auth/senha/redefinir",
        json={"email": "ana@exemplo.com", "codigo": f"{100000 + i}",
              "nova_senha": "novasenha123", "confirmacao_senha": "novasenha123"},
    ).json()["detalhe"])
    assert respostas.count("Código incorreto.") == MAX_TENTATIVAS_CODIGO, respostas


def test_pedidos_de_codigo_em_paralelo_geram_um_so(cliente, db, cenario):
    """O limite é de um código por minuto. Em paralelo, antes, cada pedido
    gerava e enviava o seu, e todos ficavam valendo."""
    from sqlalchemy import func, select

    from app.models.enums import FinalidadeCodigo
    from app.models.usuario import CodigoVerificacao, Usuario

    codigos = ao_mesmo_tempo(10, lambda i: cliente.post(
        "/api/v1/auth/senha/recuperar", json={"email": "ana@exemplo.com"},
    ).status_code)
    # A resposta é sempre a mesma, para não revelar nada a quem pede.
    assert codigos == [200] * 10

    ana = db.scalar(select(Usuario).where(Usuario.email == "ana@exemplo.com"))
    emitidos = db.scalar(
        select(func.count()).select_from(CodigoVerificacao)
        .where(CodigoVerificacao.usuario_id == ana.id)
        .where(CodigoVerificacao.finalidade == FinalidadeCodigo.RECUPERACAO_SENHA)
    )
    assert emitidos == 1


# ── Decisões que só podem ser tomadas uma vez ────────────────────────
def test_aprovar_e_recusar_ao_mesmo_tempo(cliente, cenario, monkeypatch):
    """Duas abas do síndico: uma aprova, a outra recusa. Antes, as duas
    passavam; o morador recebia os dois e-mails e o cadastro podia ficar
    ativo com os documentos já apagados pela recusa."""
    from app.services import notificacao

    enviados = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: enviados.append(titulo))
    uid, _ = cadastrar_morador(
        cliente, cenario["sindico"], cenario["cond"],
        email="pendente@exemplo.com", cpf=CPFS[4], unidade="402", aprovar=False,
    )
    codigos = ao_mesmo_tempo(6, lambda i: cliente.post(
        f"/api/v1/usuarios/{uid}/aprovacao",
        json={"aprovado": i % 2 == 0, "motivo": "Documento ilegível"},
        headers=cab(cenario["sindico"]),
    ).status_code)
    assert sorted(codigos) == [200, 409, 409, 409, 409, 409], codigos
    assert len(enviados) == 1, enviados


def test_aprovar_e_cancelar_a_reserva_ao_mesmo_tempo(cliente, cenario):
    """O síndico aprova enquanto o morador cancela: só um dos dois vale."""
    salao = cenario["salao"]["id"]
    for dias in range(20, 25):
        dia = (hoje_local() + timedelta(days=dias)).isoformat()
        reserva = reservar(cliente, cenario["ana"], salao, data=dia).json()

        def agir(i, rid=reserva["id"]):
            if i % 2:
                return cliente.delete(f"/api/v1/espacos/reservas/{rid}",
                                      headers=cab(cenario["ana"])).status_code
            return cliente.post(f"/api/v1/espacos/reservas/{rid}/avaliacao",
                                json={"aprovada": True}, headers=cab(cenario["sindico"])).status_code

        codigos = ao_mesmo_tempo(4, agir)
        aprovacoes = [c for i, c in enumerate(codigos) if i % 2 == 0]
        cancelamentos = [c for i, c in enumerate(codigos) if i % 2]
        # Aprovar e depois cancelar é válido; aprovar ou cancelar duas
        # vezes, não. Antes, as quatro ações respondiam 200.
        assert aprovacoes.count(200) <= 1 and cancelamentos.count(200) == 1, (dia, codigos)
        final = next(r for r in cliente.get("/api/v1/espacos/reservas/minhas",
                                            headers=cab(cenario["ana"])).json()
                     if r["id"] == reserva["id"])
        assert final["status"] == "cancelada"


def test_mesma_placa_nao_entra_duas_vezes_ao_mesmo_tempo(cliente, cenario, monkeypatch):
    """Clique duplo em Entrada, ou dois porteiros: os dois pedidos passavam
    juntos pela conferência da última movimentação, e o pátio ficava com
    o carro duas vezes. Uma pausa depois da conferência garante que os
    pedidos se sobreponham."""
    import time
    from datetime import datetime as _datetime

    from app.api.routers import veiculos

    class Lento(_datetime):
        @classmethod
        def now(cls, tz=None):
            time.sleep(0.3)
            return _datetime.now(tz)

    monkeypatch.setattr(veiculos, "datetime", Lento)
    corpo = {"placa": "ABC1D23", "tipo": "entrada", "categoria": "visitante"}
    respostas = ao_mesmo_tempo(4, lambda i: cliente.post(
        "/api/v1/veiculos", json=corpo, headers=cab(cenario["sindico"])).status_code)
    assert sorted(respostas) == [201, 409, 409, 409]
    patio = cliente.get("/api/v1/veiculos/patio", headers=cab(cenario["sindico"])).json()
    assert [v["placa"] for v in patio] == ["ABC1D23"]


def test_dois_sindicos_ao_mesmo_tempo_so_um_passa(cliente, db):
    """Um síndico por condomínio. A conferência ("já tem síndico?") e a
    gravação não eram um passo só: dois cadastros juntos passavam os dois."""
    from tests.fixtures import criar_condominio_como_admin, token_admin

    tok = token_admin(cliente, db)
    cond = criar_condominio_como_admin(cliente, tok)

    def criar(i):
        return cliente.post(
            f"/api/v1/admin/condominios/{cond['id']}/usuarios",
            json={
                "nome": "Síndico Concorrente", "email": f"sindico{i}@exemplo.com",
                "cpf": CPFS[i], "telefone": "(67) 99999-0001",
                "senha": "senhaforte123", "papel": "sindico",
            },
            headers=cab(tok),
        ).status_code

    codigos = ao_mesmo_tempo(4, criar)
    assert sorted(codigos) == [201, 409, 409, 409], codigos


def test_reativar_dois_sindicos_ao_mesmo_tempo_so_um_passa(cliente, db, monkeypatch):
    """Sem trava no condomínio, cada reativação conferia "já tem síndico?"
    antes de a outra gravar. A janela é curta; o atraso logo depois da
    conferência a deixa larga, para o teste não depender da sorte."""
    import time

    from app.services import usuarios as servico_usuarios
    from tests.fixtures import criar_condominio_como_admin, criar_sindico, token_admin

    original = servico_usuarios._conferir_reativacao

    def conferir_devagar(db_, usuario):
        original(db_, usuario)
        time.sleep(0.3)

    monkeypatch.setattr(servico_usuarios, "_conferir_reativacao", conferir_devagar)

    tok = token_admin(cliente, db)
    cond = criar_condominio_como_admin(cliente, tok)
    ids = []
    for i in range(4):
        id_, _ = criar_sindico(cliente, tok, cond["id"], email=f"s{i}@exemplo.com", cpf=CPFS[i])
        r = cliente.delete(f"/api/v1/admin/usuarios/{id_}", headers=cab(tok))
        assert r.status_code == 200, r.text
        ids.append(id_)

    codigos = ao_mesmo_tempo(4, lambda i: cliente.put(
        f"/api/v1/admin/usuarios/{ids[i]}", json={"status": "ativo"}, headers=cab(tok),
    ).status_code)
    assert sorted(codigos) == [200, 409, 409, 409], codigos

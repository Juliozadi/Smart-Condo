"""Assembleia virtual com votação.

Situação real: a assembleia é marcada no salão numa noite de semana, vai
meia dúzia de pessoas e as decisões valem para todos. Desde a Lei
14.309/2022 (Código Civil, art. 1.354-A) ela pode ser eletrônica. O
sistema não tinha assembleia nenhuma: a convocação ia como comunicado e
a votação acontecia fora dele.

Regras do Código Civil seguidas aqui:
  - art. 1.335, III: vota o condômino que está quite;
  - art. 1.352: as deliberações são por maioria dos votos; um voto por
    apartamento (a convenção pode dar outro peso, o sistema não);
  - art. 1.351 e 1.341: algumas matérias pedem 2/3 dos condôminos.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.api.routers import assembleias as rota
from app.core.tempo import hoje_local
from app.services import notificacao
from tests.fixtures import CPFS, cab, cadastrar_morador, token
from tests.test_financeiro import cenario, gerar_cobranca  # noqa: F401

URL = "/api/v1/assembleias"


def _agora():
    return datetime.now(timezone.utc)


def convocar(cliente, tok, abre=None, encerra=None, **extra):
    abre = abre or _agora() + timedelta(minutes=1)
    corpo = {
        "titulo": "Assembleia geral ordinária",
        "descricao": "Prestação de contas e obras do ano.",
        "abre_em": abre.isoformat(),
        "encerra_em": (encerra or abre + timedelta(days=2)).isoformat(),
        "itens": [
            {"titulo": "Aprovar as contas de 2026", "maioria": "simples"},
            {"titulo": "Trocar o portão da garagem", "descricao": "Orçamento de R$ 18 mil.",
             "maioria": "dois_tercos"},
        ],
    }
    corpo.update(extra)
    return cliente.post(URL, json=corpo, headers=cab(tok))


@pytest.fixture
def aberta(cliente, cenario, monkeypatch):
    """Uma assembleia já na votação: o relógio da rota anda 2 minutos."""
    a = convocar(cliente, cenario["sindico"]).json()
    monkeypatch.setattr(rota, "_agora", lambda: _agora() + timedelta(minutes=2))
    return a


def depois_de_encerrar(monkeypatch):
    monkeypatch.setattr(rota, "_agora", lambda: _agora() + timedelta(days=3))


def votar(cliente, tok, assembleia, *escolhas):
    votos = [{"item_id": item["id"], "escolha": e}
             for item, e in zip(assembleia["itens"], escolhas)]
    return cliente.post(f"{URL}/{assembleia['id']}/votos", json={"votos": votos},
                        headers=cab(tok))


def morador_inquilino(cliente, cenario, email, cpf, unidade):
    r = cliente.post("/api/v1/auth/cadastro/morador", json={
        "nome": "Inquilino Teste", "email": email, "cpf": cpf, "telefone": "(67) 99999-0002",
        "senha": "senhaforte123", "codigo_condominio": cenario["cond"]["codigo_acesso"],
        "unidade_numero": unidade, "tipo_ocupacao": "inquilino"})
    assert r.status_code == 201, r.text
    corpo = r.json()
    cliente.post("/api/v1/auth/confirmar", json={"email": email, "codigo": corpo["codigo_debug"]})
    cliente.post(f"/api/v1/usuarios/{corpo['usuario']['id']}/aprovacao",
                 json={"aprovado": True}, headers=cab(cenario["sindico"]))
    return token(cliente, email, "senhaforte123")


def test_convocacao_avisa_todos_os_moradores(cliente, cenario, monkeypatch):
    avisos = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: avisos.append(destino))
    r = convocar(cliente, cenario["sindico"])
    assert r.status_code == 201, r.text
    a = r.json()
    assert a["situacao"] == "agendada" and len(a["itens"]) == 2
    assert sorted(avisos) == ["ana@exemplo.com", "bruno@exemplo.com"]
    lista = cliente.get(URL, headers=cab(cenario["ana"])).json()
    assert [x["titulo"] for x in lista] == ["Assembleia geral ordinária"]
    # Antes de abrir não se vota.
    r = votar(cliente, cenario["ana"], a, "a_favor", "a_favor")
    assert r.status_code == 409 and "ainda não abriu" in r.json()["detalhe"]


def test_quem_pode_convocar_e_ver(cliente, cenario):
    assert convocar(cliente, cenario["ana"]).status_code == 403
    assert cliente.get(URL, headers=cab(cenario["porteiro"])).status_code == 403


def test_um_voto_por_apartamento(cliente, cenario, aberta):
    r = votar(cliente, cenario["ana"], aberta, "a_favor", "contra")
    assert r.status_code == 201, r.text
    # A outra moradora do 204 (também proprietária) não vota de novo.
    tok = cadastrar_morador(cliente, cenario["sindico"], cenario["cond"],
                            email="filha@exemplo.com", cpf=CPFS[4], unidade="204")[1]
    r = votar(cliente, tok, aberta, "contra", "contra")
    assert r.status_code == 409 and "já votou" in r.json()["detalhe"]
    assert votar(cliente, cenario["bruno"], aberta, "a_favor", "a_favor").status_code == 201
    a = cliente.get(f"{URL}/{aberta['id']}", headers=cab(cenario["ana"])).json()
    assert a["unidades_que_votaram"] == 2 and a["meu_apartamento_votou"] is True
    # Enquanto a votação está aberta, ninguém vê o placar — nem o síndico.
    assert a["itens"][0]["resultado"] is None
    s = cliente.get(f"{URL}/{aberta['id']}", headers=cab(cenario["sindico"])).json()
    assert s["itens"][0]["resultado"] is None


def test_votar_em_todos_os_itens(cliente, cenario, aberta):
    votos = [{"item_id": aberta["itens"][0]["id"], "escolha": "a_favor"}]
    r = cliente.post(f"{URL}/{aberta['id']}/votos", json={"votos": votos},
                     headers=cab(cenario["ana"]))
    assert r.status_code == 422
    assert votar(cliente, cenario["ana"], aberta, "a_favor", "talvez").status_code == 422


def test_inquilino_so_vota_sem_proprietario(cliente, cenario, aberta):
    inquilino_204 = morador_inquilino(cliente, cenario, "inq204@exemplo.com", CPFS[4], "204")
    r = votar(cliente, inquilino_204, aberta, "a_favor", "a_favor")
    assert r.status_code == 403 and "proprietário" in r.json()["detalhe"]
    # No 410 não mora proprietário: o inquilino vota.
    inquilino_410 = morador_inquilino(cliente, cenario, "inq410@exemplo.com", CPFS[5], "410")
    assert votar(cliente, inquilino_410, aberta, "a_favor", "a_favor").status_code == 201


def test_quem_esta_em_atraso_nao_vota(cliente, cenario, aberta):
    vencida = (hoje_local() - timedelta(days=5))
    gerar_cobranca(cliente, cenario["sindico"], cenario["u301"],
                   competencia=vencida.replace(day=1).isoformat(),
                   vencimento=vencida.isoformat())
    r = votar(cliente, cenario["bruno"], aberta, "a_favor", "a_favor")
    assert r.status_code == 403 and "1.335" in r.json()["detalhe"]
    a = cliente.get(f"{URL}/{aberta['id']}", headers=cab(cenario["bruno"])).json()
    assert a["posso_votar"] is False and "quite" in a["motivo_sem_voto"]


def test_resultado_depois_de_encerrar(cliente, cenario, aberta, monkeypatch):
    assert votar(cliente, cenario["ana"], aberta, "a_favor", "a_favor").status_code == 201
    assert votar(cliente, cenario["bruno"], aberta, "contra", "a_favor").status_code == 201
    depois_de_encerrar(monkeypatch)
    a = cliente.get(f"{URL}/{aberta['id']}", headers=cab(cenario["ana"])).json()
    assert a["situacao"] == "encerrada"
    contas, portao = a["itens"]
    # Maioria simples: 1 a 1 empata, e empate não aprova.
    assert contas["resultado"] == {"a_favor": 1, "contra": 1, "abstencao": 0, "aprovado": False}
    # 2/3 das unidades: 2 de 2 aprovam.
    assert portao["resultado"]["aprovado"] is True
    assert votar(cliente, cenario["ana"], aberta, "a_favor", "a_favor").status_code == 409


def test_dois_tercos_conta_todas_as_unidades(cliente, cenario, aberta, monkeypatch):
    """Dois apartamentos a favor não são 2/3 de um prédio de quatro: o
    quórum qualificado conta todas as unidades, não só as que votaram."""
    for email, cpf, unidade in (("c@exemplo.com", CPFS[4], "102"),
                                ("d@exemplo.com", CPFS[5], "410")):
        cadastrar_morador(cliente, cenario["sindico"], cenario["cond"], email=email, cpf=cpf,
                          unidade=unidade)
    assert votar(cliente, cenario["ana"], aberta, "a_favor", "a_favor").status_code == 201
    assert votar(cliente, cenario["bruno"], aberta, "a_favor", "a_favor").status_code == 201
    depois_de_encerrar(monkeypatch)
    a = cliente.get(f"{URL}/{aberta['id']}", headers=cab(cenario["sindico"])).json()
    assert a["total_unidades"] == 4
    assert a["itens"][0]["resultado"]["aprovado"] is True     # maioria simples: 2 a 0
    assert a["itens"][1]["resultado"]["aprovado"] is False    # 2 < 2/3 de 4


def test_sindico_cancela_com_motivo(cliente, cenario, aberta, monkeypatch):
    avisos = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: avisos.append(mensagem))
    r = cliente.post(f"{URL}/{aberta['id']}/cancelamento", headers=cab(cenario["sindico"]),
                     json={"motivo": "Pauta incompleta"})
    assert r.status_code == 200, r.text
    assert r.json()["situacao"] == "cancelada"
    assert len(avisos) == 2 and "Pauta incompleta" in avisos[0]
    assert votar(cliente, cenario["ana"], aberta, "a_favor", "a_favor").status_code == 409
    assert cliente.post(f"{URL}/{aberta['id']}/cancelamento", headers=cab(cenario["ana"]),
                        json={"motivo": "Não quero"}).status_code == 403


def test_outro_condominio_nao_ve(cliente, cenario, aberta, db):
    from tests.fixtures import criar_condominio_como_admin, criar_sindico, token_admin
    admin2 = token_admin(cliente, db, email="adm2@exemplo.com", cpf="111.444.777-35")
    outro = criar_condominio_como_admin(cliente, admin2, nome="Aurora", cnpj="45.997.418/0001-53")
    _, sindico2 = criar_sindico(cliente, admin2, outro["id"], email="s2@exemplo.com",
                                cpf="529.982.247-25")
    assert cliente.get(f"{URL}/{aberta['id']}", headers=cab(sindico2)).status_code == 404
    assert cliente.get(URL, headers=cab(sindico2)).json() == []


@pytest.mark.parametrize("ajuste", [
    {"itens": []},
    {"titulo": "ab"},
    {"abre": -60},              # abre no passado
    {"encerra": -10},           # encerra antes de abrir
    {"encerra": 60 * 24 * 31},  # mais de 30 dias de votação
])
def test_convocacao_invalida(cliente, cenario, ajuste):
    abre = _agora() + timedelta(minutes=ajuste.pop("abre", 1))
    encerra = (abre + timedelta(minutes=ajuste.pop("encerra")) if "encerra" in ajuste else None)
    r = convocar(cliente, cenario["sindico"], abre=abre, encerra=encerra, **ajuste)
    assert r.status_code == 422, (ajuste, r.text)


def test_item_com_maioria_invalida(cliente, cenario):
    r = convocar(cliente, cenario["sindico"],
                 itens=[{"titulo": "Mudar a convenção", "maioria": "metade"}])
    assert r.status_code == 422


def test_dois_moradores_do_apartamento_votam_ao_mesmo_tempo(cliente, cenario, aberta,
                                                            monkeypatch):
    """As duas cédulas chegam juntas e passam juntas pelas conferências (a
    pausa deixa a janela larga): só uma vale, e a outra recebe 409 — pela
    trava do apartamento ou, na falta dela, pela restrição do banco."""
    import time
    from tests.test_concorrencia import ao_mesmo_tempo
    tok = cadastrar_morador(cliente, cenario["sindico"], cenario["cond"],
                            email="filha@exemplo.com", cpf=CPFS[4], unidade="204")[1]
    original = rota._motivo_sem_voto

    def conferir_devagar(*args, **kwargs):
        motivo = original(*args, **kwargs)
        time.sleep(0.3)
        return motivo

    monkeypatch.setattr(rota, "_motivo_sem_voto", conferir_devagar)
    codigos = ao_mesmo_tempo(2, lambda i: votar(
        cliente, [cenario["ana"], tok][i], aberta, "a_favor", "contra").status_code)
    assert sorted(codigos) == [201, 409], codigos

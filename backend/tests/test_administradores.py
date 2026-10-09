"""Vários administradores, histórico de quem fez cada coisa e nada apagado.

Pedidos do grupo:
- um administrador cadastra outro;
- toda criação, edição e inativação mostra quem a fez ("editado por fulano");
- nada é excluído: "excluir" inativa, e o registro pode ser reativado.
"""
from __future__ import annotations

import pytest

from tests.fixtures import (
    CPFS, cab, criar_condominio_como_admin, criar_sindico, montar_condominio, token,
    token_admin,
)
from tests.test_concorrencia import ao_mesmo_tempo


@pytest.fixture
def admin(cliente, db):
    return token_admin(cliente, db)


def cadastrar_admin(cliente, tok, email="segundo@exemplo.com", cpf=CPFS[7]):
    return cliente.post("/api/v1/admin/administradores", headers=cab(tok), json={
        "nome": "Beatriz Segunda", "email": email, "cpf": cpf,
        "telefone": "(67) 99999-2222", "senha": "senhaforte123",
    })


def id_de(cliente, tok):
    return cliente.get("/api/v1/auth/eu", headers=cab(tok)).json()["id"]


# ── Mais de um administrador ─────────────────────────────────────────
def test_admin_cadastra_outro_admin(cliente, admin):
    r = cadastrar_admin(cliente, admin)
    assert r.status_code == 201, r.text
    novo = r.json()
    assert novo["papel"] == "admin" and novo["condominio_id"] is None
    assert novo["criado_por"] == "Administrador"
    # O novo administrador entra e usa o painel.
    tok = token(cliente, "segundo@exemplo.com", "senhaforte123")
    assert cliente.get("/api/v1/admin/resumo", headers=cab(tok)).status_code == 200


def test_so_admin_cadastra_admin(cliente, db):
    base = montar_condominio(cliente, db)
    assert cadastrar_admin(cliente, base["sindico"]).status_code == 403


def test_admin_nao_e_criado_pela_rota_do_condominio(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    r = cliente.post(f"/api/v1/admin/condominios/{cond['id']}/usuarios", headers=cab(admin), json={
        "nome": "Outro Admin", "email": "x@exemplo.com", "cpf": CPFS[7],
        "telefone": "(67) 99999-2222", "senha": "senhaforte123", "papel": "admin",
    })
    assert r.status_code == 400


def test_admin_inativa_outro_mas_nao_a_si_mesmo(cliente, admin):
    segundo = cadastrar_admin(cliente, admin).json()
    tok2 = token(cliente, "segundo@exemplo.com", "senhaforte123")
    eu = id_de(cliente, admin)
    assert cliente.delete(f"/api/v1/admin/usuarios/{eu}", headers=cab(admin)).status_code == 400
    r = cliente.put(f"/api/v1/admin/usuarios/{eu}", json={"status": "inativo"}, headers=cab(admin))
    assert r.status_code == 400
    # O segundo inativa o primeiro, e o histórico diz quem fez.
    assert cliente.delete(f"/api/v1/admin/usuarios/{eu}", headers=cab(tok2)).status_code == 200
    historico = cliente.get("/api/v1/admin/historico", params={
        "entidade": "usuario", "entidade_id": eu}, headers=cab(tok2)).json()
    assert historico[0]["acao"] == "inativou"
    assert historico[0]["autor_nome"] == segundo["nome"]


def test_dois_admins_inativando_um_ao_outro_nao_deixam_a_plataforma_sem_admin(
        cliente, admin, monkeypatch):
    """Cada um via o outro ainda ativo; sem a trava, sobravam zero. Uma
    pausa no meio da inativação garante que as duas se sobreponham."""
    import time

    from app.services import usuarios as servico_usuarios
    original = servico_usuarios.cancelar_reservas_futuras

    def devagar(db, usuario):
        time.sleep(0.4)
        return original(db, usuario)

    monkeypatch.setattr(servico_usuarios, "cancelar_reservas_futuras", devagar)
    cadastrar_admin(cliente, admin)
    tok2 = token(cliente, "segundo@exemplo.com", "senhaforte123")
    ids = [id_de(cliente, admin), id_de(cliente, tok2)]
    toks = [tok2, admin]   # cada um inativa o outro
    codigos = ao_mesmo_tempo(2, lambda i: cliente.delete(
        f"/api/v1/admin/usuarios/{ids[i]}", headers=cab(toks[i])).status_code)
    assert sorted(codigos) == [200, 409], codigos
    ativos = [u for u in cliente.get("/api/v1/admin/usuarios", params={"papel": "admin"},
                                     headers=cab(toks[codigos.index(200)] if 200 in codigos else admin)).json()
              if u["status"] == "ativo"]
    assert len(ativos) == 1


# ── Quem fez cada alteração ──────────────────────────────────────────
def test_edicao_mostra_quem_editou_e_o_que(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    assert cond["criado_por"] == "Administrador"
    assert cond["ultima_alteracao"]["acao"] == "criou"

    cadastrar_admin(cliente, admin)
    tok2 = token(cliente, "segundo@exemplo.com", "senhaforte123")
    corpo = {k: cond[k] for k in ("nome", "cnpj", "cep", "logradouro", "numero",
                                  "bairro", "cidade", "uf", "telefone")}
    corpo.update(nome="Residencial Renomeado", telefone="(67) 3333-4444")
    r = cliente.put(f"/api/v1/admin/condominios/{cond['id']}", json=corpo, headers=cab(tok2))
    assert r.status_code == 200, r.text
    ultima = r.json()["ultima_alteracao"]
    assert ultima["acao"] == "editou" and ultima["autor_nome"] == "Beatriz Segunda"
    assert ultima["descricao"] == "Alterou o nome e o telefone"
    # A lista mostra o mesmo, e o criador continua sendo o primeiro.
    linha = next(c for c in cliente.get("/api/v1/admin/condominios", headers=cab(admin)).json()
                 if c["id"] == cond["id"])
    assert linha["ultima_alteracao"]["autor_nome"] == "Beatriz Segunda"
    assert linha["criado_por"] == "Administrador"


def test_salvar_sem_mudar_nada_nao_vira_edicao(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    corpo = {k: cond[k] for k in ("nome", "cnpj", "cep", "logradouro", "numero",
                                  "bairro", "cidade", "uf", "telefone")}
    r = cliente.put(f"/api/v1/admin/condominios/{cond['id']}", json=corpo, headers=cab(admin))
    assert r.json()["ultima_alteracao"]["acao"] == "criou"


def test_senha_trocada_pelo_admin_encerra_as_sessoes_do_usuario(cliente, db, admin):
    base = montar_condominio(cliente, db, email_admin="admin2@exemplo.com", cpf_admin=CPFS[5])
    sindico_id = id_de(cliente, base["sindico"])
    r = cliente.put(f"/api/v1/admin/usuarios/{sindico_id}",
                    json={"senha": "novasenha456"}, headers=cab(admin))
    assert r.status_code == 200
    assert r.json()["ultima_alteracao"]["descricao"] == "Alterou a senha"
    # A sessão aberta com a senha antiga cai.
    assert cliente.get("/api/v1/auth/eu", headers=cab(base["sindico"])).status_code == 401


# ── Nada é apagado ───────────────────────────────────────────────────
def test_condominio_inativo_nao_recebe_cadastro(cliente, admin):
    cond = criar_condominio_como_admin(cliente, admin)
    cliente.delete(f"/api/v1/admin/condominios/{cond['id']}", headers=cab(admin))
    assert cliente.get(f"/api/v1/condominios/por-codigo/{cond['codigo_acesso']}").status_code == 404
    r = cliente.post(f"/api/v1/admin/condominios/{cond['id']}/usuarios", headers=cab(admin), json={
        "nome": "Fulano de Tal", "email": "s@exemplo.com", "cpf": CPFS[2],
        "telefone": "(67) 99999-1111", "senha": "senhaforte123", "papel": "sindico",
    })
    assert r.status_code == 409
    # Os indicadores não contam o inativo; a lista o mostra, por último.
    assert cliente.get("/api/v1/admin/resumo", headers=cab(admin)).json()["condominios"] == 0
    assert cliente.get("/api/v1/admin/condominios", headers=cab(admin)).json()[0]["inativo"]


def test_reativar_sindico_nao_deixa_dois_sindicos(cliente, admin):
    """Antes, reativar pela edição deixava o condomínio com dois síndicos."""
    cond = criar_condominio_como_admin(cliente, admin)
    primeiro, _ = criar_sindico(cliente, admin, cond["id"], cpf=CPFS[0])
    cliente.delete(f"/api/v1/admin/usuarios/{primeiro}", headers=cab(admin))
    criar_sindico(cliente, admin, cond["id"], email="novo.sindico@exemplo.com", cpf=CPFS[1])
    r = cliente.put(f"/api/v1/admin/usuarios/{primeiro}",
                    json={"status": "ativo"}, headers=cab(admin))
    assert r.status_code == 409
    assert "já tem um síndico ativo" in r.json()["detalhe"]


def test_comunicado_removido_fica_guardado(cliente, db, admin):
    from app.models.comunicado import Comunicado
    base = montar_condominio(cliente, db, email_admin="admin2@exemplo.com", cpf_admin=CPFS[5])
    c = cliente.post("/api/v1/comunicados", headers=cab(base["sindico"]), json={
        "titulo": "Aviso geral", "conteudo": "Conteúdo do aviso", "categoria": "geral"}).json()
    r = cliente.delete(f"/api/v1/comunicados/{c['id']}", headers=cab(base["sindico"]))
    assert r.status_code == 200
    assert cliente.get("/api/v1/comunicados", headers=cab(base["sindico"])).json() == []
    guardado = db.get(Comunicado, c["id"])
    assert guardado is not None and guardado.inativo_em is not None
    assert cliente.post(f"/api/v1/comunicados/{c['id']}/leitura",
                        headers=cab(base["sindico"])).status_code == 404
    historico = cliente.get("/api/v1/admin/historico", params={
        "entidade": "comunicado", "entidade_id": c["id"]}, headers=cab(admin)).json()
    assert [h["acao"] for h in historico] == ["inativou", "criou"]


def test_comunicado_nao_vai_para_morador_inativo(cliente, db, monkeypatch):
    from app.services import notificacao
    from tests.fixtures import cadastrar_morador
    enviados = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: enviados.append(destino))
    base = montar_condominio(cliente, db)
    ativo_id, _ = cadastrar_morador(cliente, base["sindico"], base["cond"],
                                    email="ativo@exemplo.com", cpf=CPFS[1], unidade="101")
    saiu_id, _ = cadastrar_morador(cliente, base["sindico"], base["cond"],
                                   email="saiu@exemplo.com", cpf=CPFS[3], unidade="102")
    cliente.delete(f"/api/v1/usuarios/{saiu_id}", headers=cab(base["sindico"]))
    enviados.clear()
    cliente.post("/api/v1/comunicados", headers=cab(base["sindico"]), json={
        "titulo": "Aviso geral", "conteudo": "Conteúdo do aviso", "categoria": "geral"})
    assert enviados == ["ativo@exemplo.com"]


def test_salvar_morador_sem_mudar_nada_nao_registra_alteracao(cliente, db, admin):
    """A tela manda sempre todos os campos, inclusive a unidade: salvar
    sem mexer em nada não pode aparecer como "Alterou a unidade"."""
    from tests.fixtures import cadastrar_morador
    base = montar_condominio(cliente, db, email_admin="admin2@exemplo.com", cpf_admin=CPFS[5])
    uid, _ = cadastrar_morador(cliente, base["sindico"], base["cond"], unidade="204")
    u = cliente.get(f"/api/v1/admin/usuarios/{uid}", headers=cab(admin)).json()
    antes = u["ultima_alteracao"]
    r = cliente.put(f"/api/v1/admin/usuarios/{uid}", headers=cab(admin), json={
        "nome": u["nome"], "email": u["email"], "telefone": u["telefone"], "status": "ativo",
        "unidade_numero": "204", "unidade_bloco": "unico", "tipo_ocupacao": u["tipo_ocupacao"],
    })
    assert r.status_code == 200, r.text
    assert r.json()["ultima_alteracao"] == antes
    # Mudando de fato a unidade, aparece.
    r = cliente.put(f"/api/v1/admin/usuarios/{uid}", headers=cab(admin),
                    json={"unidade_numero": "305"})
    assert r.json()["ultima_alteracao"]["descricao"] == "Alterou a unidade"

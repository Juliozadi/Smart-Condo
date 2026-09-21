"""Atalhos para montar um condomínio completo nos testes."""
from __future__ import annotations

# CPFs válidos distintos, para não esbarrar na checagem de duplicidade.
CPFS = [
    "010.000.000-28", "011.234.567-04", "012.469.134-02", "013.703.701-56",
    "014.938.268-59", "016.172.835-92", "017.407.402-62", "018.641.969-47",
]


def criar_admin(db, email="admin@exemplo.com", cpf=CPFS[6], senha="senhaforte123"):
    """O primeiro administrador nasce fora da API (app/criar_admin.py);
    nos testes ele é inserido direto, do mesmo jeito."""
    from app.core.security import gerar_hash_senha
    from app.models.enums import Papel, StatusUsuario
    from app.models.usuario import Usuario

    admin = Usuario(
        nome="Administrador", email=email, cpf=cpf.replace(".", "").replace("-", ""),
        telefone="67999990000", senha_hash=gerar_hash_senha(senha),
        papel=Papel.ADMIN, status=StatusUsuario.ATIVO,
    )
    db.add(admin)
    db.commit()
    return admin


def token_admin(cliente, db, **extra):
    admin = criar_admin(db, **extra)
    return token(cliente, admin.email, extra.get("senha", "senhaforte123"))


def criar_condominio_como_admin(cliente, tok_admin, nome="Residencial das Palmeiras",
                                cnpj="11.222.333/0001-81"):
    r = cliente.post(
        "/api/v1/admin/condominios",
        json={
            "nome": nome, "cnpj": cnpj, "cep": "79000-000",
            "logradouro": "Rua das Flores", "numero": "100", "bairro": "Centro",
            "cidade": "Campo Grande", "uf": "MS",
        },
        headers=cab(tok_admin),
    )
    assert r.status_code == 201, r.text
    return r.json()


def criar_sindico(cliente, tok_admin, condominio_id, email="sindico@exemplo.com",
                  cpf=CPFS[0], senha="senhaforte123"):
    """Síndico é criado pelo administrador — ele não se cadastra sozinho."""
    r = cliente.post(
        f"/api/v1/admin/condominios/{condominio_id}/usuarios",
        json={
            "nome": "Roberto Nascimento", "email": email, "cpf": cpf,
            "telefone": "(67) 99999-0001", "senha": senha, "papel": "sindico",
        },
        headers=cab(tok_admin),
    )
    assert r.status_code == 201, r.text
    return r.json()["id"], token(cliente, email, senha)


def token(cliente, email, senha):
    r = cliente.post("/api/v1/auth/login", json={"email": email, "senha": senha})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def cab(tok):
    return {"Authorization": f"Bearer {tok}"}


def montar_condominio(cliente, db, nome="Residencial das Palmeiras",
                      cnpj="11.222.333/0001-81", email_sindico="sindico@exemplo.com",
                      cpf_sindico=CPFS[0], email_admin="admin@exemplo.com",
                      cpf_admin=CPFS[6]):
    """Monta a cadeia completa: administrador, condomínio e síndico.

    É a ordem real do sistema — o administrador cria o condomínio e nomeia
    o síndico; o síndico não se cadastra sozinho.
    """
    tok_admin = token_admin(cliente, db, email=email_admin, cpf=cpf_admin)
    cond = criar_condominio_como_admin(cliente, tok_admin, nome=nome, cnpj=cnpj)
    sindico_id, tok_sindico = criar_sindico(
        cliente, tok_admin, cond["id"], email=email_sindico, cpf=cpf_sindico
    )
    return {"admin": tok_admin, "cond": cond, "sindico": tok_sindico, "sindico_id": sindico_id}


def cadastrar_morador(
    cliente, tok_sindico, condominio, email="morador@exemplo.com", cpf=CPFS[1],
    unidade="204", senha="senhaforte123", aprovar=True,
):
    r = cliente.post(
        "/api/v1/auth/cadastro/morador",
        json={
            "nome": "João Silva", "email": email, "cpf": cpf,
            "telefone": "(67) 99999-0002", "senha": senha,
            # O morador entra pelo código que recebeu do síndico.
            "codigo_condominio": condominio["codigo_acesso"],
            "unidade_numero": unidade, "tipo_ocupacao": "proprietario",
        },
    )
    assert r.status_code == 201, r.text
    corpo = r.json()
    usuario_id = corpo["usuario"]["id"]

    cliente.post("/api/v1/auth/confirmar", json={"email": email, "codigo": corpo["codigo_debug"]})
    if aprovar:
        ap = cliente.post(
            f"/api/v1/usuarios/{usuario_id}/aprovacao",
            json={"aprovado": True},
            headers=cab(tok_sindico),
        )
        assert ap.status_code == 200, ap.text
        return usuario_id, token(cliente, email, senha)
    return usuario_id, None


def cadastrar_porteiro(
    cliente, tok_sindico, condominio, email="porteiro@exemplo.com", cpf=CPFS[2],
    senha="senhaforte123", permissoes=None, aprovar=True,
):
    corpo_envio = {
        "nome": "Carlos Pereira", "email": email, "cpf": cpf,
        "telefone": "(67) 99999-0003", "senha": senha, "condominio_id": condominio["id"],
    }
    if permissoes is not None:
        corpo_envio["permissoes"] = permissoes

    r = cliente.post("/api/v1/usuarios/porteiros", json=corpo_envio, headers=cab(tok_sindico))
    assert r.status_code == 201, r.text
    corpo = r.json()
    usuario_id = corpo["usuario"]["id"]

    cliente.post("/api/v1/auth/confirmar", json={"email": email, "codigo": corpo["codigo_debug"]})
    if aprovar:
        cliente.post(
            f"/api/v1/usuarios/{usuario_id}/aprovacao",
            json={"aprovado": True},
            headers=cab(tok_sindico),
        )
        return usuario_id, token(cliente, email, senha)
    return usuario_id, None


def criar_espaco(cliente, tok_sindico, **extra):
    corpo = {
        "nome": "Salão de Festas", "capacidade": 80,
        "reservavel": True, "uso_livre": False,
    }
    corpo.update(extra)
    r = cliente.post("/api/v1/espacos", json=corpo, headers=cab(tok_sindico))
    assert r.status_code == 201, r.text
    return r.json()

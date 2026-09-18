"""Atalhos para montar um condomínio completo nos testes."""
from __future__ import annotations

# CPFs válidos distintos, para não esbarrar na checagem de duplicidade.
CPFS = [
    "010.000.000-28", "011.234.567-04", "012.469.134-02", "013.703.701-56",
    "014.938.268-59", "016.172.835-92", "017.407.402-62", "018.641.969-47",
]


def cadastrar_sindico(cliente, email="sindico@exemplo.com", cpf=CPFS[0], senha="senhaforte123"):
    r = cliente.post(
        "/api/v1/auth/cadastro/sindico",
        json={
            "nome": "Roberto Nascimento", "email": email, "cpf": cpf,
            "telefone": "(67) 99999-0001", "senha": senha,
        },
    )
    assert r.status_code == 201, r.text
    corpo = r.json()
    cliente.post(
        "/api/v1/auth/confirmar", json={"email": email, "codigo": corpo["codigo_debug"]}
    )
    return token(cliente, email, senha)


def token(cliente, email, senha):
    r = cliente.post("/api/v1/auth/login", json={"email": email, "senha": senha})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def cab(tok):
    return {"Authorization": f"Bearer {tok}"}


def criar_condominio(cliente, tok_sindico, nome="Residencial das Palmeiras"):
    r = cliente.post(
        "/api/v1/condominios",
        json={
            "nome": nome, "cnpj": "11.222.333/0001-81", "cep": "79000-000",
            "logradouro": "Rua das Flores", "numero": "100", "bairro": "Centro",
            "cidade": "Campo Grande", "uf": "MS",
        },
        headers=cab(tok_sindico),
    )
    assert r.status_code == 201, r.text
    return r.json()


def cadastrar_morador(
    cliente, tok_sindico, condominio_id, email="morador@exemplo.com", cpf=CPFS[1],
    unidade="204", senha="senhaforte123", aprovar=True,
):
    r = cliente.post(
        "/api/v1/auth/cadastro/morador",
        json={
            "nome": "João Silva", "email": email, "cpf": cpf,
            "telefone": "(67) 99999-0002", "senha": senha,
            "condominio_id": condominio_id, "unidade_numero": unidade,
            "tipo_ocupacao": "proprietario",
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
    cliente, tok_sindico, condominio_id, email="porteiro@exemplo.com", cpf=CPFS[2],
    senha="senhaforte123", permissoes=None, aprovar=True,
):
    corpo_envio = {
        "nome": "Carlos Pereira", "email": email, "cpf": cpf,
        "telefone": "(67) 99999-0003", "senha": senha, "condominio_id": condominio_id,
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

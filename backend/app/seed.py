"""Popula o banco com um condomínio completo para demonstração.

    python -m app.seed            # cria os dados
    python -m app.seed --limpar   # apaga tudo antes de criar

Serve para apresentar o sistema sem cadastrar nada na mão. Todas as contas
saem com a mesma senha, impressa no fim.

Nunca rode isto num banco de produção: com --limpar ele esvazia as tabelas.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, text

from app.core.database import Base, SessionLocal, engine
from app.core.security import gerar_hash_senha
from app.models.comunicado import Comunicado
from app.models.condominio import Condominio, Unidade
from app.models.enums import (
    CanalVerificacao, CategoriaComunicado, CategoriaDocumento, CategoriaVeiculo,
    FormaPagamento, Papel, PrioridadeOcorrencia, PrioridadeOrdemServico, StatusCobranca,
    StatusEncomenda, StatusOcorrencia, StatusOrdemServico, StatusReserva, StatusUsuario,
    StatusVisitante,
    TipoMovimentacao, TipoOcupacao,
)
from app.models.espaco import EspacoComum, RegistroOcupacao, Reserva
from app.models.operacao import Documento, MovimentacaoVeiculo, OrdemServico
from app.models.financeiro import Cobranca, Pagamento, PreferenciaCobranca
from app.models.portaria import Encomenda, Ocorrencia, Visitante
from app.models.usuario import PermissaoPorteiro, Usuario
from app.services import arquivos

SENHA = "smartcondo123"
HOJE = date.today()
AGORA = datetime.now(timezone.utc)


def _hora(h: int, m: int = 0) -> time:
    return time(hour=h, minute=m)


def limpar(db) -> None:
    nomes = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables
                      if t.name != "alembic_version")
    db.execute(text(f"TRUNCATE {nomes} RESTART IDENTITY CASCADE"))
    db.commit()
    # O TRUNCATE reinicia os IDs, mas a sessão ainda guarda os objetos
    # antigos; sem soltar o identity map, o SQLAlchemy avisa de colisão.
    db.expunge_all()
    # Os arquivos enviados (fotos e documentos) ficam fora do banco; sem
    # os registros que apontavam para eles, só ocupariam espaço — e são
    # dados pessoais sem finalidade.
    for pasta in ("fotos", arquivos.PORTARIA, arquivos.OCORRENCIAS, arquivos.DOCUMENTOS):
        for arquivo in arquivos._pasta(pasta).iterdir():
            if arquivo.is_file():
                arquivo.unlink()


def criar(db) -> dict:
    senha_hash = gerar_hash_senha(SENHA)

    def usuario(nome, email, cpf, telefone, papel, **extra) -> Usuario:
        u = Usuario(
            nome=nome, email=email, cpf=cpf, telefone=telefone,
            senha_hash=senha_hash, papel=papel,
            status=extra.pop("status", StatusUsuario.ATIVO), **extra,
        )
        db.add(u)
        return u

    # ── Administrador da plataforma ───────────────────────────────────
    usuario(
        "Administrador SmartCondo", "admin@smartcondo.com", "01740740262",
        "67999990000", Papel.ADMIN,
    )

    # ── Síndico e condomínio ──────────────────────────────────────────
    sindico = usuario(
        "Roberto Nascimento", "sindico@smartcondo.com", "01000000028",
        "67999990001", Papel.SINDICO,
    )
    db.flush()

    condominio = Condominio(
        nome="Residencial das Palmeiras", cnpj="11222333000181", cep="79000000",
        # Fixo aqui de propósito: a demonstração precisa de um código estável.
        codigo_acesso="PALM-2025",
        logradouro="Rua das Flores", numero="100", bairro="Centro",
        cidade="Campo Grande", uf="MS", telefone="6733330000", sindico_id=sindico.id,
    )
    db.add(condominio)
    db.flush()
    sindico.condominio_id = condominio.id

    # ── Unidades ──────────────────────────────────────────────────────
    unidades: dict[str, Unidade] = {}
    for numero, andar, vagas in [
        ("101", 1, 1), ("102", 1, 1), ("204", 2, 2), ("301", 3, 1),
        ("302", 3, 1), ("410", 4, 2), ("502", 5, 2),
    ]:
        u = Unidade(
            condominio_id=condominio.id, numero=numero, bloco="unico",
            andar=andar, vagas_garagem=vagas,
        )
        db.add(u)
        unidades[numero] = u
    db.flush()

    # ── Porteiros ─────────────────────────────────────────────────────
    carlos = usuario(
        "Carlos Pereira", "porteiro@smartcondo.com", "01246913402",
        "67999990003", Papel.PORTEIRO, condominio_id=condominio.id,
    )
    renata = usuario(
        "Renata Moura", "renata@smartcondo.com", "01493826859",
        "67999990004", Papel.PORTEIRO, condominio_id=condominio.id,
    )
    db.flush()

    # O Carlos tem tudo liberado; a Renata não registra veículos nem
    # ocorrências — assim dá para mostrar a tela de permissões fazendo efeito.
    db.add(PermissaoPorteiro(
        porteiro_id=carlos.id, definidas_por_id=sindico.id,
        registrar_visitantes=True, registrar_encomendas=True,
        registrar_veiculos=True, registrar_ocorrencias=True, acessar_financeiro=False,
    ))
    db.add(PermissaoPorteiro(
        porteiro_id=renata.id, definidas_por_id=sindico.id,
        registrar_visitantes=True, registrar_encomendas=True,
        registrar_veiculos=False, registrar_ocorrencias=False, acessar_financeiro=False,
    ))

    # ── Moradores ─────────────────────────────────────────────────────
    moradores: dict[str, Usuario] = {}
    for nome, email, cpf, tel, unidade, ocupacao in [
        ("João Silva", "morador@smartcondo.com", "01123456704", "67988880001", "204", TipoOcupacao.PROPRIETARIO),
        ("Ana Beatriz Rocha", "ana@smartcondo.com", "01370370156", "67988880002", "301", TipoOcupacao.PROPRIETARIO),
        ("Bruno Cardoso", "bruno@smartcondo.com", "01617283592", "67988880003", "102", TipoOcupacao.INQUILINO),
        ("Marina Duarte", "marina@smartcondo.com", "01864196947", "67988880004", "410", TipoOcupacao.PROPRIETARIO),
    ]:
        m = usuario(
            nome, email, cpf, tel, Papel.MORADOR,
            condominio_id=condominio.id, unidade_id=unidades[unidade].id,
            tipo_ocupacao=ocupacao,
        )
        moradores[unidade] = m

    # Um cadastro parado na fila, para a tela de aprovação do síndico ter o que mostrar.
    usuario(
        "Pedro Henrique Lima", "pedro@smartcondo.com", "02000000045", "67988880005",
        Papel.MORADOR, condominio_id=condominio.id, unidade_id=unidades["502"].id,
        tipo_ocupacao=TipoOcupacao.INQUILINO, status=StatusUsuario.AGUARDANDO_APROVACAO,
    )
    db.flush()

    # ── Espaços comuns ────────────────────────────────────────────────
    espacos: dict[str, EspacoComum] = {}
    for nome, capacidade, reservavel, uso_livre, manutencao, descricao in [
        ("Salão de Festas", 80, True, False, False, "Com cozinha de apoio e som"),
        ("Churrasqueira 1", 20, True, False, False, "Área descoberta"),
        ("Churrasqueira 2", 20, True, False, False, "Área coberta"),
        ("Salão de Jogos", 25, True, False, False, "Sinuca, ping-pong e mesas"),
        ("Piscina", 60, False, True, False, "Adulto e infantil"),
        ("Academia", 12, False, True, False, "Equipamentos completos"),
        ("Playground", 20, False, True, False, "Área infantil coberta"),
        ("Coworking", 10, True, False, True, "Em reforma até o fim do mês"),
    ]:
        e = EspacoComum(
            condominio_id=condominio.id, nome=nome, descricao=descricao,
            capacidade=capacidade, reservavel=reservavel, uso_livre=uso_livre,
            em_manutencao=manutencao,
        )
        db.add(e)
        espacos[nome] = e
    db.flush()

    # ── Ocupação atual das áreas de uso livre ─────────────────────────
    for nome, pessoas in [("Piscina", 23), ("Academia", 11), ("Playground", 0)]:
        db.add(RegistroOcupacao(
            espaco_id=espacos[nome].id, pessoas=pessoas,
            registrado_em=AGORA - timedelta(minutes=3), registrado_por_id=carlos.id,
        ))

    # ── Reservas ──────────────────────────────────────────────────────
    db.add(Reserva(
        espaco_id=espacos["Salão de Festas"].id, morador_id=moradores["204"].id,
        data=HOJE + timedelta(days=4), hora_inicio=_hora(14), hora_fim=_hora(22),
        pessoas_estimadas=50, observacoes="Aniversário de 15 anos",
        status=StatusReserva.APROVADA, avaliada_por_id=sindico.id, avaliada_em=AGORA,
    ))
    db.add(Reserva(
        espaco_id=espacos["Churrasqueira 2"].id, morador_id=moradores["301"].id,
        data=HOJE + timedelta(days=11), hora_inicio=_hora(11), hora_fim=_hora(18),
        pessoas_estimadas=20, status=StatusReserva.PENDENTE,
    ))
    db.add(Reserva(
        espaco_id=espacos["Salão de Jogos"].id, morador_id=moradores["102"].id,
        data=HOJE + timedelta(days=2), hora_inicio=_hora(19), hora_fim=_hora(23),
        pessoas_estimadas=12, status=StatusReserva.PENDENTE,
    ))
    db.add(Reserva(
        espaco_id=espacos["Salão de Festas"].id, morador_id=moradores["410"].id,
        data=HOJE - timedelta(days=25), hora_inicio=_hora(18), hora_fim=_hora(23),
        pessoas_estimadas=60, status=StatusReserva.CONCLUIDA,
    ))

    # ── Preferências de cobrança ──────────────────────────────────────
    for unidade, dia, forma in [
        ("204", 20, FormaPagamento.PIX),
        ("301", 10, FormaPagamento.BOLETO),
        ("102", 5, FormaPagamento.DEBITO_AUTOMATICO),
    ]:
        db.add(PreferenciaCobranca(
            morador_id=moradores[unidade].id, dia_vencimento=dia, forma_preferida=forma
        ))

    # ── Financeiro: três competências ─────────────────────────────────
    primeiro_dia = HOJE.replace(day=1)
    for atras in (2, 1, 0):
        mes = primeiro_dia
        for _ in range(atras):
            mes = (mes - timedelta(days=1)).replace(day=1)

        for unidade in ("101", "102", "204", "301", "302", "410"):
            valor = Decimal("320.00") if unidade != "410" else Decimal("410.00")
            vencimento = mes.replace(day=10)
            # A competência mais antiga já está quitada; a do meio tem um
            # inadimplente; a atual está toda em aberto.
            if atras == 2:
                situacao = StatusCobranca.PAGA
            elif atras == 1:
                situacao = StatusCobranca.VENCIDA if unidade == "302" else StatusCobranca.PAGA
            else:
                situacao = StatusCobranca.VENCIDA if vencimento < HOJE else StatusCobranca.ABERTA

            cobranca = Cobranca(
                unidade_id=unidades[unidade].id, competencia=mes,
                descricao=f"Taxa de condomínio {mes:%m/%Y}", valor=valor,
                vencimento=vencimento, status=situacao,
            )
            db.add(cobranca)
            db.flush()

            if situacao == StatusCobranca.PAGA:
                pagador = moradores.get(unidade)
                db.add(Pagamento(
                    cobranca_id=cobranca.id,
                    pago_por_id=pagador.id if pagador else None,
                    valor=valor, forma=FormaPagamento.PIX,
                    pago_em=datetime.combine(vencimento, time(10, 30), tzinfo=timezone.utc),
                ))

    # ── Comunicados ───────────────────────────────────────────────────
    for titulo, conteudo, categoria, fixado, dias in [
        ("Manutenção da piscina",
         "A piscina ficará fechada no dia 20 para limpeza e troca da bomba. "
         "A reabertura está prevista para as 8h do dia seguinte.",
         CategoriaComunicado.MANUTENCAO, False, 1),
        ("Assembleia geral ordinária",
         "Convocamos todos os condôminos para a assembleia no salão de festas, "
         "às 19h30. A pauta inclui a prestação de contas e o orçamento do ano.",
         CategoriaComunicado.URGENTE, True, 3),
        ("Nova regra para a churrasqueira",
         "As reservas passam a ser liberadas com até 30 dias de antecedência, "
         "por ordem de chegada.",
         CategoriaComunicado.GERAL, False, 8),
        ("Reforço na portaria",
         "A partir deste mês teremos um porteiro adicional no turno da noite.",
         CategoriaComunicado.SEGURANCA, False, 15),
        ("Reajuste da taxa condominial",
         "A taxa passa a R$ 320,00 a partir da próxima competência, conforme "
         "aprovado em assembleia.",
         CategoriaComunicado.FINANCEIRO, False, 22),
    ]:
        db.add(Comunicado(
            condominio_id=condominio.id, autor_id=sindico.id, titulo=titulo,
            conteudo=conteudo, categoria=categoria, fixado=fixado,
            publicado_em=AGORA - timedelta(days=dias),
        ))

    # ── Portaria ──────────────────────────────────────────────────────
    db.add(Visitante(
        unidade_id=unidades["204"].id, registrado_por_id=carlos.id,
        nome="Marcos Alves", documento="01864196947", tipo_visita="Visita pessoal",
        status=StatusVisitante.AGUARDANDO_CONFIRMACAO,
    ))
    db.add(Visitante(
        unidade_id=unidades["301"].id, registrado_por_id=carlos.id,
        nome="Fernanda Souza", documento="01617283592", tipo_visita="Visita pessoal",
        status=StatusVisitante.DENTRO, entrada_em=AGORA - timedelta(hours=2),
        confirmado_por_id=moradores["301"].id, confirmado_em=AGORA - timedelta(hours=2),
    ))
    db.add(Visitante(
        unidade_id=unidades["102"].id, registrado_por_id=renata.id,
        nome="Lucas Oliveira", documento="01493826859", tipo_visita="Prestador de serviço",
        placa_veiculo="ABC1D23", status=StatusVisitante.SAIU,
        entrada_em=AGORA - timedelta(hours=6), saida_em=AGORA - timedelta(hours=1),
        confirmado_por_id=moradores["102"].id, confirmado_em=AGORA - timedelta(hours=6),
    ))

    db.add(Encomenda(
        unidade_id=unidades["204"].id, registrada_por_id=carlos.id,
        remetente="Correios", tipo_volume="Caixa média", codigo_rastreio="BR987654321",
        status=StatusEncomenda.AGUARDANDO_RETIRADA, recebida_em=AGORA - timedelta(hours=3),
    ))
    db.add(Encomenda(
        unidade_id=unidades["301"].id, registrada_por_id=renata.id,
        remetente="Mercado Livre", tipo_volume="Envelope / documento",
        status=StatusEncomenda.RETIRADA, recebida_em=AGORA - timedelta(days=2),
        retirada_em=AGORA - timedelta(days=1), retirada_por_id=moradores["301"].id,
    ))

    db.add(Ocorrencia(
        condominio_id=condominio.id, aberta_por_id=moradores["204"].id,
        unidade_id=unidades["204"].id, titulo="Barulho no apartamento vizinho",
        descricao="Som alto depois das 23h em dias de semana, por três noites seguidas.",
        categoria="convivencia", local="Apto 205", prioridade=PrioridadeOcorrencia.ALTA,
        status=StatusOcorrencia.ABERTA,
    ))
    db.add(Ocorrencia(
        condominio_id=condominio.id, aberta_por_id=moradores["102"].id,
        unidade_id=unidades["102"].id, titulo="Lâmpada queimada na garagem",
        descricao="A lâmpada da vaga 12 está queimada há uma semana.",
        categoria="manutencao", local="Estacionamento", prioridade=PrioridadeOcorrencia.BAIXA,
        status=StatusOcorrencia.RESOLVIDA,
        resposta="Lâmpada trocada pela manutenção.", respondida_por_id=sindico.id,
        respondida_em=AGORA - timedelta(days=1),
    ))

    # ── Veículos ──────────────────────────────────────────────────────
    # Três carros no pátio (última movimentação é entrada) e um que já saiu.
    for placa, modelo, cor, categoria, unidade, tipos in [
        ("ABC1D23", "Fiat Argo", "Prata", CategoriaVeiculo.MORADOR, "204", ["entrada"]),
        ("DEF2G45", "Honda Civic", "Preto", CategoriaVeiculo.MORADOR, "301", ["entrada"]),
        ("GHI3J67", "VW Saveiro", "Branco", CategoriaVeiculo.PRESTADOR, None, ["entrada"]),
        ("JKL4M89", "Chevrolet Onix", "Vermelho", CategoriaVeiculo.VISITANTE, None,
         ["entrada", "saida"]),
    ]:
        for indice, tipo in enumerate(tipos):
            db.add(MovimentacaoVeiculo(
                condominio_id=condominio.id,
                placa=placa, modelo=modelo, cor=cor,
                tipo=TipoMovimentacao.ENTRADA if tipo == "entrada" else TipoMovimentacao.SAIDA,
                categoria=categoria,
                unidade_id=unidades[unidade].id if unidade else None,
                registrada_por_id=carlos.id,
                registrada_em=AGORA - timedelta(hours=5 - indice * 2),
            ))

    # ── Ordens de serviço ─────────────────────────────────────────────
    for tipo, descricao, local, prioridade, situacao, fornecedor, estimado, real, dias in [
        ("Elétrica", "Lâmpadas queimadas na garagem do subsolo.", "Garagem",
         PrioridadeOrdemServico.MEDIA, StatusOrdemServico.ABERTA, "Elétrica Silva",
         Decimal("450.00"), None, 0),
        ("Hidráulica", "Vazamento na tubulação da churrasqueira.", "Área de lazer",
         PrioridadeOrdemServico.URGENTE, StatusOrdemServico.EM_ANDAMENTO, "HidroMS",
         Decimal("1200.00"), None, 3),
        ("Pintura", "Repintura do hall de entrada.", "Hall",
         PrioridadeOrdemServico.BAIXA, StatusOrdemServico.CONCLUIDA, "Pinturas Aurora",
         Decimal("2800.00"), Decimal("2650.00"), 30),
        ("Elevador", "Manutenção preventiva semestral.", "Torre A",
         PrioridadeOrdemServico.ALTA, StatusOrdemServico.CONCLUIDA, "ElevaSul",
         Decimal("900.00"), Decimal("900.00"), 45),
    ]:
        db.add(OrdemServico(
            condominio_id=condominio.id, tipo=tipo, descricao=descricao, local=local,
            prioridade=prioridade, status=situacao, fornecedor=fornecedor,
            data_prevista=HOJE + timedelta(days=7) if situacao != StatusOrdemServico.CONCLUIDA else None,
            custo_estimado=estimado, custo_real=real,
            aberta_por_id=sindico.id,
            concluida_em=(AGORA - timedelta(days=dias)
                          if situacao == StatusOrdemServico.CONCLUIDA else None),
        ))

    # ── Documentos ────────────────────────────────────────────────────
    for titulo, categoria, descricao, tamanho, unidade in [
        ("Convenção do Condomínio", CategoriaDocumento.CONVENCAO,
         "Documento registrado em cartório.", 820, None),
        ("Regimento Interno", CategoriaDocumento.REGIMENTO,
         "Regras de convivência e uso das áreas comuns.", 410, None),
        ("Ata da Assembleia de Março", CategoriaDocumento.ATA,
         "Prestação de contas e eleição do conselho.", 180, None),
        ("Ata da Assembleia de Janeiro", CategoriaDocumento.ATA,
         "Aprovação do orçamento anual.", 165, None),
        ("Prestação de Contas 2024", CategoriaDocumento.PRESTACAO_CONTAS,
         "Balanço completo do exercício.", 1240, None),
        ("Planta Baixa — Apto 204", CategoriaDocumento.PLANTA,
         "Planta da unidade.", 2100, "204"),
    ]:
        db.add(Documento(
            condominio_id=condominio.id, titulo=titulo, categoria=categoria,
            descricao=descricao,
            arquivo_url=f"https://cdn.smartcondo.com/docs/{categoria.value}.pdf",
            tamanho_kb=tamanho,
            unidade_id=unidades[unidade].id if unidade else None,
            publicado_por_id=sindico.id,
            publicado_em=AGORA - timedelta(days=10),
        ))

    db.commit()
    return {"condominio": condominio.nome}


def main() -> int:
    parser = argparse.ArgumentParser(description="Popula o banco para demonstração.")
    parser.add_argument(
        "--limpar", action="store_true",
        help="Apaga todos os dados antes de criar. Nunca use em produção.",
    )
    args = parser.parse_args()

    with SessionLocal() as db:
        ja_tem = db.scalar(select(Usuario).limit(1))
        if ja_tem is not None and not args.limpar:
            print(
                "O banco já tem dados. Rode com --limpar para apagar e recriar:\n"
                "    python -m app.seed --limpar",
                file=sys.stderr,
            )
            return 1

        if args.limpar:
            print("Apagando os dados existentes…")
            limpar(db)

        print("Criando o condomínio de demonstração…")
        criar(db)

    print(f"""
Pronto. Contas criadas (todas com a senha "{SENHA}"):

  Admin     admin@smartcondo.com        (gerencia condomínios e síndicos)
  Síndico   sindico@smartcondo.com
  Porteiro  porteiro@smartcondo.com     (todas as permissões)
            renata@smartcondo.com       (sem veículos nem ocorrências)
  Morador   morador@smartcondo.com      (Apto 204)
            ana@smartcondo.com          (Apto 301)
            bruno@smartcondo.com        (Apto 102)
            marina@smartcondo.com       (Apto 410)

  pedro@smartcondo.com está aguardando aprovação do síndico — use para
  demonstrar a tela de aprovação de cadastros.

  Código de acesso do condomínio: PALM-2025
  (é o que o morador informa ao se cadastrar)
""")
    # Fecha o pool antes de sair, senão o Python avisa de conexão aberta.
    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Gera o Diagrama Entidade-Relacionamento do SmartCondo.

O desenho é lido do banco em funcionamento, não escrito à mão: colunas,
tipos, chaves primárias e estrangeiras saem do catálogo do PostgreSQL.
Assim o diagrama nunca fica defasado em relação ao banco — se alguém
acrescentar uma coluna e esquecer da figura, basta rodar este script.

São quatro figuras. Uma visão de conjunto, só com os nomes das entidades
e as ligações, e três recortes por assunto com todos os atributos. Vinte e uma
entidades com duzentos e tantos atributos não cabem legíveis numa página
só; a visão de conjunto mostra o todo, os recortes mostram o detalhe.

    python3 der.py
"""
import os
import subprocess
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

BANCO = os.environ.get("DATABASE_URL_PSQL", "postgresql://smartcondo:smartcondo@127.0.0.1:5432/smartcondo")

VERDE = "#0b6d66"
VERDE_CLARO = "#e8f6f5"
CINZA = "#41565c"
TEXTO = "#0a2f2c"

# Os três recortes por assunto, e o que entra em cada um.
RECORTES = [
    ("Núcleo — condomínio, unidades e usuários", [
        "condominios", "unidades", "usuarios", "permissoes_porteiro", "codigos_verificacao",
        "documentos_cadastro",
    ]),
    ("Convivência — espaços, comunicados, documentos, ocorrências e mensagens", [
        "espacos_comuns", "reservas", "registros_ocupacao", "comunicados",
        "leituras_comunicado", "documentos", "ocorrencias", "ordens_servico", "mensagens",
    ]),
    ("Financeiro e portaria", [
        "cobrancas", "pagamentos", "preferencias_cobranca",
        "visitantes", "encomendas", "movimentacoes_veiculo",
    ]),
]


def consultar(sql):
    saida = subprocess.run(
        ["psql", BANCO, "-tAF|", "-c", sql],
        capture_output=True, text=True, check=True).stdout
    return [l.split("|") for l in saida.strip().split("\n") if l]


def ler_esquema():
    colunas = consultar("""
        SELECT c.table_name, c.column_name,
               CASE WHEN c.data_type='character varying' THEN 'varchar('||c.character_maximum_length||')'
                    WHEN c.data_type='numeric' THEN 'numeric('||c.numeric_precision||','||c.numeric_scale||')'
                    WHEN c.data_type='timestamp with time zone' THEN 'timestamptz'
                    WHEN c.data_type='timestamp without time zone' THEN 'timestamp'
                    WHEN c.data_type='USER-DEFINED' THEN c.udt_name
                    WHEN c.data_type='time without time zone' THEN 'time'
                    ELSE c.data_type END
        FROM information_schema.columns c
        JOIN information_schema.tables t
          ON t.table_name=c.table_name AND t.table_schema=c.table_schema
        WHERE c.table_schema='public' AND t.table_type='BASE TABLE'
          AND c.table_name<>'alembic_version'
        ORDER BY c.table_name, c.ordinal_position""")
    chaves = consultar("""
        SELECT tc.table_name, tc.constraint_type, kcu.column_name,
               coalesce(ccu.table_name,'')
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON kcu.constraint_name=tc.constraint_name AND kcu.table_schema=tc.table_schema
        LEFT JOIN information_schema.constraint_column_usage ccu
          ON ccu.constraint_name=tc.constraint_name AND tc.constraint_type='FOREIGN KEY'
        WHERE tc.table_schema='public' AND tc.table_name<>'alembic_version'
          AND tc.constraint_type IN ('PRIMARY KEY','FOREIGN KEY')""")

    tabelas = {}
    for tab, col, tipo in colunas:
        tabelas.setdefault(tab, []).append([col, tipo, ""])
    ligacoes = []
    for tab, tipo, col, destino in chaves:
        marca = "PK" if tipo == "PRIMARY KEY" else "FK"
        for linha in tabelas.get(tab, []):
            if linha[0] == col:
                linha[2] = (linha[2] + " " + marca).strip()
        if tipo == "FOREIGN KEY":
            ligacoes.append((tab, col, destino))
    return tabelas, ligacoes


def caixa(ax, x, y, nome, atributos, largura, altura_linha, fonte):
    """Desenha uma entidade: cabeçalho com o nome, corpo com os atributos."""
    altura = altura_linha * (len(atributos) + 1.25)
    ax.add_patch(FancyBboxPatch(
        (x, y - altura), largura, altura,
        boxstyle="round,pad=0.0006,rounding_size=0.004",
        facecolor="white", edgecolor=VERDE, lw=1.1, zorder=2))
    ax.add_patch(plt.Rectangle((x, y - altura_linha * 1.25), largura, altura_linha * 1.25,
                               facecolor=VERDE, edgecolor=VERDE, lw=1.1, zorder=3))
    ax.text(x + largura / 2, y - altura_linha * 0.63, nome, ha="center", va="center",
            fontsize=fonte + 0.6, weight="bold", color="white", zorder=4)
    for i, (col, tipo, marca) in enumerate(atributos):
        ly = y - altura_linha * (1.25 + i + 0.5)
        rotulo = f"{col}  {tipo}"
        negrito = "PK" in marca
        ax.text(x + largura * 0.045, ly, ("• " if marca else "") + rotulo,
                ha="left", va="center", fontsize=fonte, color=TEXTO,
                weight="bold" if negrito else "normal", zorder=4)
        if marca:
            ax.text(x + largura * 0.955, ly, marca, ha="right", va="center",
                    fontsize=fonte - 0.4, color=VERDE, weight="bold", zorder=4)
    return altura


def figura_recorte(titulo, nomes, tabelas, ligacoes, arquivo):
    """Uma figura com as entidades de um assunto e todos os seus atributos."""
    n = len(nomes)
    colunas = 3 if n > 4 else 2
    largura_caixa = 1.0 / colunas * 0.86
    fonte = 6.0 if n > 6 else 6.6
    altura_linha = 0.020 if n > 6 else 0.023

    # Cada coluna recebe as entidades na ordem, empilhadas de cima para baixo.
    fig, ax = plt.subplots(figsize=(13.8, 9.0))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.5, 0.99, titulo, ha="center", va="top", fontsize=11,
            weight="bold", color=CINZA)

    topo = [0.945] * colunas
    caixas = {}
    for i, nome in enumerate(nomes):
        c = i % colunas
        x = c * (1.0 / colunas) + (1.0 / colunas - largura_caixa) / 2
        atributos = tabelas[nome]
        alt = caixa(ax, x, topo[c], nome, atributos, largura_caixa, altura_linha, fonte)
        caixas[nome] = (x, topo[c], largura_caixa, alt)
        topo[c] -= alt + 0.035

    # Sem isto sobra uma faixa branca embaixo, do tamanho da coluna mais
    # curta: as colunas raramente terminam na mesma altura.
    fundo = min(y - alt for _, y, _, alt in caixas.values())
    ax.set_ylim(fundo - 0.03, 1)

    # Ligações entre entidades que estão nesta figura.
    for origem, coluna, destino in ligacoes:
        if origem not in caixas or destino not in caixas or origem == destino:
            continue
        xo, yo, wo, ho = caixas[origem]
        xd, yd, wd, hd = caixas[destino]
        ax.annotate("", xy=(xd + wd / 2, yd - hd / 2), xytext=(xo + wo / 2, yo - ho / 2),
                    arrowprops=dict(arrowstyle="-|>", color="#7f9ba1", lw=0.9,
                                    connectionstyle="arc3,rad=0.16",
                                    shrinkA=6, shrinkB=6), zorder=1)

    fig.savefig(arquivo, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"{arquivo} — {n} entidades")


def figura_geral(tabelas, ligacoes, arquivo):
    """Visão de conjunto: só os nomes das entidades e as ligações."""
    fig, ax = plt.subplots(figsize=(13.8, 8.4))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.5, 0.985, "Visão de conjunto — as 21 entidades e suas ligações",
            ha="center", va="top", fontsize=11, weight="bold", color=CINZA)

    # Posições escolhidas à mão: o núcleo no centro, cada assunto de um lado.
    pos = {
        "condominios": (0.50, 0.86), "unidades": (0.50, 0.66), "usuarios": (0.50, 0.44),
        "codigos_verificacao": (0.50, 0.22), "permissoes_porteiro": (0.50, 0.07),
        "espacos_comuns": (0.17, 0.86), "reservas": (0.17, 0.70),
        "registros_ocupacao": (0.17, 0.54), "comunicados": (0.17, 0.38),
        "leituras_comunicado": (0.17, 0.22), "documentos": (0.17, 0.07),
        "ocorrencias": (0.83, 0.86), "ordens_servico": (0.83, 0.70),
        "cobrancas": (0.83, 0.54), "pagamentos": (0.83, 0.38),
        "preferencias_cobranca": (0.83, 0.22), "visitantes": (0.83, 0.07),
        "encomendas": (0.335, 0.30), "movimentacoes_veiculo": (0.665, 0.30),
        "mensagens": (0.335, 0.56), "documentos_cadastro": (0.665, 0.56),
    }
    for origem, _, destino in ligacoes:
        if origem == destino or origem not in pos or destino not in pos:
            continue
        xo, yo = pos[origem]; xd, yd = pos[destino]
        ax.annotate("", xy=(xd, yd), xytext=(xo, yo),
                    arrowprops=dict(arrowstyle="-|>", color="#9bb3b8", lw=0.8,
                                    connectionstyle="arc3,rad=0.12",
                                    shrinkA=26, shrinkB=26), zorder=1)
    for nome, (x, y) in pos.items():
        largura = 0.008 * len(nome) + 0.03
        ax.add_patch(FancyBboxPatch((x - largura / 2, y - 0.024), largura, 0.048,
                                    boxstyle="round,pad=0.002,rounding_size=0.008",
                                    facecolor=VERDE_CLARO, edgecolor=VERDE, lw=1.1, zorder=2))
        ax.text(x, y, nome, ha="center", va="center", fontsize=7.4,
                weight="bold", color=TEXTO, zorder=3)
    fig.savefig(arquivo, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"{arquivo} — visão de conjunto")


if __name__ == "__main__":
    tabelas, ligacoes = ler_esquema()
    print(f"lidas {len(tabelas)} entidades e {len(ligacoes)} chaves estrangeiras do banco")
    figura_geral(tabelas, ligacoes, "der_geral.png")
    for i, (titulo, nomes) in enumerate(RECORTES, 1):
        faltando = [n for n in nomes if n not in tabelas]
        if faltando:
            raise SystemExit(f"entidades do recorte {i} que não existem no banco: {faltando}")
        figura_recorte(titulo, nomes, tabelas, ligacoes, f"der_{i}.png")
    cobertas = {n for _, nomes in RECORTES for n in nomes}
    sobrando = set(tabelas) - cobertas
    if sobrando:
        raise SystemExit(f"entidades fora de todos os recortes: {sorted(sobrando)}")
    print("todas as entidades do banco aparecem em algum recorte")

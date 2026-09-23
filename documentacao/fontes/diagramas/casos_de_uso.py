"""Gera o diagrama de casos de uso (UML) do SmartCondo.

O desenho é feito por script, e não à mão numa ferramenta, para que uma
correção no conjunto de casos de uso se reflita na figura sem que alguém
precise redesenhá-la. Saída: casos_de_uso.png, na própria pasta.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch

# Cada caso de uso, com os atores que o alcançam e a coluna em que fica.
# A coluna não é enfeite: com os casos do administrador e do síndico à
# esquerda e os do porteiro e do morador à direita, as linhas de
# associação quase não se cruzam, e o diagrama fica legível.
ESQ, DIR = 0, 1
CASOS = [
    ("Autenticar-se",                   ["ADM", "SIN", "POR", "MOR"], ESQ),
    ("Recuperar senha",                 ["ADM", "SIN", "POR", "MOR"], ESQ),
    ("Cadastrar condomínio",            ["ADM"],                      ESQ),
    ("Gerar código de acesso",          ["ADM", "SIN"],               ESQ),
    ("Manter usuários",                 ["ADM", "SIN"],               ESQ),
    ("Aprovar cadastro de morador",     ["SIN"],                      ESQ),
    ("Definir permissões do porteiro",  ["SIN"],                      ESQ),
    ("Publicar comunicado",             ["SIN"],                      ESQ),
    ("Publicar documento",              ["SIN"],                      ESQ),
    ("Gerar cobrança",                  ["SIN"],                      ESQ),
    ("Abrir ordem de serviço",          ["SIN"],                      ESQ),
    ("Avaliar reserva",                 ["SIN"],                      ESQ),
    ("Responder ocorrência",            ["SIN"],                      ESQ),
    ("Registrar pagamento",             ["SIN", "MOR"],               ESQ),
    ("Registrar visitante",             ["POR"],                      DIR),
    ("Registrar encomenda",             ["POR"],                      DIR),
    ("Registrar veículo",               ["POR"],                      DIR),
    ("Registrar ocupação de espaço",    ["POR"],                      DIR),
    ("Abrir ocorrência",                ["POR", "MOR"],               DIR),
    ("Solicitar reserva",               ["MOR"],                      DIR),
    ("Confirmar visitante",             ["MOR"],                      DIR),
    ("Confirmar retirada de encomenda", ["MOR"],                      DIR),
    ("Consultar cobranças",             ["MOR"],                      DIR),
    ("Escolher forma de pagamento",     ["MOR"],                      DIR),
    ("Consultar comunicados",           ["MOR"],                      DIR),
]

ATORES = {
    "ADM": ("Administrador", 0.06, 0.86),
    "SIN": ("Síndico",       0.06, 0.30),
    "POR": ("Porteiro",      0.94, 0.78),
    "MOR": ("Morador",       0.94, 0.24),
}

VERDE = "#0b6d66"
CINZA = "#4a5c62"


def ator(ax, x, y, nome):
    """Desenha o boneco palito da UML, com o nome embaixo."""
    e = 0.021
    ax.add_patch(plt.Circle((x, y + 4.4 * e), e, fill=False, lw=1.4, color=VERDE))
    ax.plot([x, x], [y + 3.4 * e, y + 0.9 * e], lw=1.4, color=VERDE)
    ax.plot([x - 1.7 * e, x + 1.7 * e], [y + 2.6 * e, y + 2.6 * e], lw=1.4, color=VERDE)
    ax.plot([x, x - 1.5 * e], [y + 0.9 * e, y - 1.4 * e], lw=1.4, color=VERDE)
    ax.plot([x, x + 1.5 * e], [y + 0.9 * e, y - 1.4 * e], lw=1.4, color=VERDE)
    ax.text(x, y - 2.6 * e, nome, ha="center", va="top", fontsize=8.5,
            weight="bold", color=VERDE)


def desenhar():
    fig, ax = plt.subplots(figsize=(13.6, 9.6))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    # A fronteira do sistema: tudo o que está dentro é responsabilidade
    # do SmartCondo; os atores ficam de fora.
    ax.add_patch(FancyBboxPatch((0.20, 0.035), 0.60, 0.925,
                                boxstyle="round,pad=0.004,rounding_size=0.012",
                                fill=False, lw=1.3, color=CINZA))
    ax.text(0.50, 0.975, "SmartCondo", ha="center", va="center",
            fontsize=12, weight="bold", color=CINZA)

    # Os casos ficam em duas colunas dentro da fronteira.
    pos = {}
    quantos = [sum(1 for c in CASOS if c[2] == k) for k in (ESQ, DIR)]
    proxima = [0, 0]
    for nome, _, coluna in CASOS:
        linha = proxima[coluna]
        proxima[coluna] += 1
        x = 0.355 if coluna == ESQ else 0.645
        y = 0.925 - linha * (0.86 / max(quantos[coluna] - 1, 1))
        pos[nome] = (x, y)
        ax.add_patch(Ellipse((x, y), 0.245, 0.052, fill=True,
                             facecolor="#e8f6f5", edgecolor=VERDE, lw=1.1))
        ax.text(x, y, nome, ha="center", va="center", fontsize=7.6, color="#0a2f2c")

    # As associações ator — caso de uso.
    for nome, atores, _ in CASOS:
        cx, cy = pos[nome]
        for sigla in atores:
            _, ax_x, ax_y = ATORES[sigla]
            esquerda = ax_x < 0.5
            borda_x = cx - 0.1225 if esquerda else cx + 0.1225
            ax.plot([ax_x + (0.035 if esquerda else -0.035), borda_x],
                    [ax_y, cy], lw=0.55, color="#9bb3b8", zorder=0)

    for sigla, (nome, x, y) in ATORES.items():
        ator(ax, x, y, nome)

    fig.savefig("casos_de_uso.png", dpi=200, bbox_inches="tight",
                facecolor="white")
    print("casos_de_uso.png gerado —", len(CASOS), "casos de uso,", len(ATORES), "atores")


if __name__ == "__main__":
    desenhar()

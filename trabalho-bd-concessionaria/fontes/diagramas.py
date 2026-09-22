"""Gera os diagramas do trabalho em SVG: o MER (conceitual, notação de
Chen com cardinalidades mín-máx) e o DER (lógico, notação pé de galinha).

    python diagramas.py            # grava ../diagramas/mer.svg e der.svg

O render.js converte os SVGs em PNG para o documento e a apresentação.
"""
import math
import os
from xml.sax.saxutils import escape

SAIDA = os.path.join(os.path.dirname(__file__), '..', 'diagramas')
FONTE = "Arial, 'Liberation Sans', Helvetica, sans-serif"
TINTA = '#1F2A37'
AZUL = '#1F3A5F'
AZUL_CLARO = '#E6EDF5'
LARANJA = '#A8481A'
LARANJA_CLARO = '#FBEADC'
CINZA = '#5B6B7C'
FUNDO = '#FFFFFF'


def largura_texto(texto, tamanho):
    """Estimativa da largura de um texto em Arial (média de 0,55 em)."""
    return len(texto) * tamanho * 0.55


def svg(largura, altura, corpo):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" '
            f'height="{altura}" viewBox="0 0 {largura} {altura}">\n'
            f'<rect width="{largura}" height="{altura}" fill="{FUNDO}"/>\n'
            + '\n'.join(corpo) + '\n</svg>\n')


def texto(x, y, conteudo, tamanho=20, peso='normal', cor=TINTA,
          ancora='middle', sublinhado=False, italico=False):
    extra = ' text-decoration="underline"' if sublinhado else ''
    if italico:
        extra += ' font-style="italic"'
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONTE}" '
            f'font-size="{tamanho}" font-weight="{peso}" fill="{cor}" '
            f'text-anchor="{ancora}" dominant-baseline="central"{extra}>'
            f'{escape(conteudo)}</text>')


def linha(x1, y1, x2, y2, cor=TINTA, espessura=2):
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{cor}" stroke-width="{espessura}"/>')


# ── MER ─────────────────────────────────────────────────────────────
def mer():
    ENT_L, ENT_A = 200, 64
    entidades = {
        'FORNECEDOR': (250, 360),
        'VEÍCULO': (770, 360),
        'CLIENTE': (250, 690),
        'VENDA': (770, 690),
        'FUNCIONÁRIO': (1260, 690),
    }
    # Relacionamento: nome, entidade A, cardinalidade junto de A,
    # entidade B, cardinalidade junto de B, posição do losango
    relacionamentos = [
        ('fornece', 'FORNECEDOR', '(0,1)', 'VEÍCULO', '(0,n)', (510, 360)),
        ('é vendido em', 'VEÍCULO', '(1,1)', 'VENDA', '(0,1)', (770, 525)),
        ('realiza', 'CLIENTE', '(1,1)', 'VENDA', '(0,n)', (510, 690)),
        ('registra', 'FUNCIONÁRIO', '(1,1)', 'VENDA', '(0,n)', (1015, 690)),
    ]
    # Atributos: lista, ângulo inicial e final (graus), raios da elipse
    # imaginária em que ficam distribuídos
    atributos = {
        'FORNECEDOR': (['id', 'nome', 'cnpj', 'telefone'], 150, 30, 190, 150),
        'VEÍCULO': (['id', 'marca', 'modelo', 'ano', 'cor', 'placa',
                     'preço', 'status'], 152, -12, 300, 190),
        'CLIENTE': (['id', 'nome', 'cpf', 'telefone', 'e-mail', 'endereço'],
                    212, 334, 245, 180),
        'VENDA': (['id', 'data da venda', 'valor da venda'], 230, 310, 170, 165),
        'FUNCIONÁRIO': (['id', 'nome', 'cargo', 'salário', 'telefone'],
                        248, 395, 180, 165),
    }

    camada_linhas, camada_formas, camada_textos = [], [], []

    # Atributos (linhas primeiro, para ficarem por baixo das formas)
    for ent, (nomes, a0, a1, rx, ry) in atributos.items():
        cx, cy = entidades[ent]
        n = len(nomes)
        for i, nome in enumerate(nomes):
            ang = math.radians(a0 + (a1 - a0) * (i / (n - 1) if n > 1 else 0))
            ax = cx + rx * math.cos(ang)
            ay = cy - ry * math.sin(ang)
            erx = largura_texto(nome, 19) / 2 + 16
            camada_linhas.append(linha(cx, cy, ax, ay, CINZA, 1.6))
            camada_formas.append(
                f'<ellipse cx="{ax:.1f}" cy="{ay:.1f}" rx="{erx:.1f}" ry="21" '
                f'fill="#FFFFFF" stroke="{CINZA}" stroke-width="1.6"/>')
            camada_textos.append(texto(ax, ay, nome, 19,
                                       sublinhado=(nome == 'id')))

    # Relacionamentos
    for nome, ea, ca, eb, cb, (rx_, ry_) in relacionamentos:
        for ent, card in ((ea, ca), (eb, cb)):
            ex, ey = entidades[ent]
            camada_linhas.append(linha(ex, ey, rx_, ry_, TINTA, 2.2))
            # Cardinalidade junto da entidade, deslocada da linha
            if ey == ry_:  # linha horizontal
                borda = ex + (ENT_L / 2 + 34) * (1 if rx_ > ex else -1)
                camada_textos.append(texto(borda, ey - 20, card, 19, 'bold',
                                           LARANJA))
            else:  # linha vertical
                borda = ey + (ENT_A / 2 + 22) * (1 if ry_ > ey else -1)
                camada_textos.append(texto(ex + 36, borda, card, 19, 'bold',
                                           LARANJA))
        dl, da = 180, 96
        pontos = (f'{rx_},{ry_ - da / 2} {rx_ + dl / 2},{ry_} '
                  f'{rx_},{ry_ + da / 2} {rx_ - dl / 2},{ry_}')
        camada_formas.append(f'<polygon points="{pontos}" fill="{LARANJA_CLARO}" '
                             f'stroke="{LARANJA}" stroke-width="2.2"/>')
        camada_textos.append(texto(rx_, ry_, nome, 19, 'bold', LARANJA))

    # Entidades
    for nome, (cx, cy) in entidades.items():
        camada_formas.append(
            f'<rect x="{cx - ENT_L / 2}" y="{cy - ENT_A / 2}" width="{ENT_L}" '
            f'height="{ENT_A}" rx="4" fill="{AZUL_CLARO}" stroke="{AZUL}" '
            f'stroke-width="2.6"/>')
        camada_textos.append(texto(cx, cy, nome, 22, 'bold', AZUL))

    # Legenda (canto superior direito)
    lx, ly = 1170, 50
    leg = [f'<rect x="{lx}" y="{ly}" width="340" height="284" rx="6" '
           f'fill="#FAFBFC" stroke="#C9D2DC" stroke-width="1.4"/>',
           texto(lx + 20, ly + 30, 'Legenda', 19, 'bold', TINTA, 'start')]
    y = ly + 72
    leg.append(f'<rect x="{lx + 20}" y="{y - 16}" width="70" height="32" '
               f'rx="3" fill="{AZUL_CLARO}" stroke="{AZUL}" stroke-width="2"/>')
    leg.append(texto(lx + 108, y, 'Entidade', 18, ancora='start'))
    y += 48
    leg.append(f'<polygon points="{lx + 55},{y - 19} {lx + 92},{y} '
               f'{lx + 55},{y + 19} {lx + 18},{y}" fill="{LARANJA_CLARO}" '
               f'stroke="{LARANJA}" stroke-width="2"/>')
    leg.append(texto(lx + 108, y, 'Relacionamento', 18, ancora='start'))
    y += 46
    leg.append(f'<ellipse cx="{lx + 55}" cy="{y}" rx="35" ry="16" fill="#FFFFFF" '
               f'stroke="{CINZA}" stroke-width="1.6"/>')
    leg.append(texto(lx + 108, y, 'Atributo', 18, ancora='start'))
    y += 44
    leg.append(f'<ellipse cx="{lx + 55}" cy="{y}" rx="35" ry="16" fill="#FFFFFF" '
               f'stroke="{CINZA}" stroke-width="1.6"/>')
    leg.append(texto(lx + 55, y, 'id', 17, sublinhado=True))
    leg.append(texto(lx + 108, y, 'Identificador', 18, ancora='start'))
    y += 44
    leg.append(texto(lx + 55, y, '(0,n)', 18, 'bold', LARANJA))
    leg.append(texto(lx + 108, y, 'Cardinalidade (mín,máx)', 18, ancora='start'))

    corpo = camada_linhas + camada_formas + camada_textos + leg
    return svg(1520, 920, corpo)


# ── DER ─────────────────────────────────────────────────────────────
TABELAS = {
    'fornecedores': [('PK', 'id', 'INT'), ('', 'nome', 'VARCHAR(100)'),
                     ('UK', 'cnpj', 'VARCHAR(18)'), ('', 'telefone', 'VARCHAR(15)')],
    'veiculos': [('PK', 'id', 'INT'), ('', 'marca', 'VARCHAR(50)'),
                 ('', 'modelo', 'VARCHAR(50)'), ('', 'ano', 'YEAR'),
                 ('', 'cor', 'VARCHAR(30)'), ('UK', 'placa', 'VARCHAR(8)'),
                 ('', 'preco', 'DECIMAL(10,2)'), ('', 'status', 'VARCHAR(20)'),
                 ('FK', 'fornecedor_id', 'INT')],
    'clientes': [('PK', 'id', 'INT'), ('', 'nome', 'VARCHAR(100)'),
                 ('UK', 'cpf', 'VARCHAR(14)'), ('', 'telefone', 'VARCHAR(15)'),
                 ('', 'email', 'VARCHAR(100)'), ('', 'endereco', 'VARCHAR(150)')],
    'vendas': [('PK', 'id', 'INT'), ('FK', 'cliente_id', 'INT'),
               ('FK', 'funcionario_id', 'INT'), ('FK UK', 'veiculo_id', 'INT'),
               ('', 'data_venda', 'DATE'), ('', 'valor_venda', 'DECIMAL(10,2)')],
    'funcionarios': [('PK', 'id', 'INT'), ('', 'nome', 'VARCHAR(100)'),
                     ('', 'cargo', 'VARCHAR(50)'), ('', 'salario', 'DECIMAL(10,2)'),
                     ('', 'telefone', 'VARCHAR(15)')],
}
TAB_L, CAB, LIN = 400, 50, 36
POSICOES = {
    'fornecedores': (60, 70),
    'veiculos': (560, 70),
    'clientes': (60, 560),
    'vendas': (560, 560),
    'funcionarios': (1060, 560),
}


def y_coluna(tabela, coluna):
    x, y = POSICOES[tabela]
    for i, (_, nome, _) in enumerate(TABELAS[tabela]):
        if nome == coluna:
            return y + CAB + i * LIN + LIN / 2
    raise KeyError(coluna)


def tabela_svg(nome):
    x, y = POSICOES[nome]
    cols = TABELAS[nome]
    altura = CAB + len(cols) * LIN
    partes = [
        f'<rect x="{x}" y="{y}" width="{TAB_L}" height="{altura}" rx="6" '
        f'fill="#FFFFFF" stroke="{AZUL}" stroke-width="2.4"/>',
        f'<path d="M{x},{y + CAB} v{-CAB + 6} a6,6 0 0 1 6,-6 h{TAB_L - 12} '
        f'a6,6 0 0 1 6,6 v{CAB - 6} z" fill="{AZUL}"/>',
        texto(x + TAB_L / 2, y + CAB / 2, nome, 22, 'bold', '#FFFFFF'),
    ]
    for i, (chave, col, tipo) in enumerate(cols):
        cy = y + CAB + i * LIN + LIN / 2
        if i % 2 == 1:
            partes.append(f'<rect x="{x + 1.2}" y="{cy - LIN / 2}" '
                          f'width="{TAB_L - 2.4}" height="{LIN}" fill="#F3F6F9"/>')
        if i > 0:
            partes.append(linha(x, cy - LIN / 2, x + TAB_L, cy - LIN / 2,
                                '#DCE3EA', 1))
        bx = x + 12
        for k in chave.split():
            cor = {'PK': '#B8860B', 'FK': LARANJA, 'UK': '#4B6F8F'}[k]
            partes.append(f'<rect x="{bx}" y="{cy - 12}" width="36" height="24" '
                          f'rx="4" fill="{cor}"/>')
            partes.append(texto(bx + 18, cy, k, 14, 'bold', '#FFFFFF'))
            bx += 40
        negrito = 'bold' if chave.startswith('PK') else 'normal'
        partes.append(texto(x + 98, cy, col, 19, negrito, TINTA, 'start'))
        partes.append(texto(x + TAB_L - 14, cy, tipo, 16, cor=CINZA,
                            ancora='end'))
    return partes


def pe_de_galinha(x, y, direcao, tipo):
    """Símbolos na ponta de uma ligação que encosta na borda de uma tabela
    em (x, y). direcao = vetor unitário que aponta da tabela para fora.
    tipo: 'um' (||), 'zero_um' (o|), 'zero_muitos' (o<)."""
    dx, dy = direcao
    px, py = -dy, dx  # perpendicular
    partes = []

    def ponto(d, lateral=0):
        return x + dx * d + px * lateral, y + dy * d + py * lateral

    def barra(d):
        (x1, y1), (x2, y2) = ponto(d, -11), ponto(d, 11)
        partes.append(linha(x1, y1, x2, y2, TINTA, 2.4))

    def circulo(d):
        cx, cy = ponto(d)
        partes.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="7.5" '
                      f'fill="#FFFFFF" stroke="{TINTA}" stroke-width="2.2"/>')

    if tipo == 'um':
        barra(10)
        barra(18)
    elif tipo == 'zero_um':
        barra(12)
        circulo(28)
    elif tipo == 'zero_muitos':
        vx, vy = ponto(18)
        for lateral in (-12, 0, 12):
            bx, by = ponto(0, lateral)
            partes.append(linha(vx, vy, bx, by, TINTA, 2.2))
        circulo(30)
    return partes


def der():
    ligacoes = []
    # fornecedores.id (0..1) -> veiculos.fornecedor_id (0..n)
    y1 = y_coluna('fornecedores', 'id')
    y2 = y_coluna('veiculos', 'fornecedor_id')
    ligacoes.append(f'<polyline points="460,{y1} 510,{y1} 510,{y2} 560,{y2}" '
                    f'fill="none" stroke="{TINTA}" stroke-width="2.2"/>')
    ligacoes += pe_de_galinha(460, y1, (1, 0), 'zero_um')
    ligacoes += pe_de_galinha(560, y2, (-1, 0), 'zero_muitos')
    # veiculos (1) -> vendas.veiculo_id (0..1): vertical
    base_veic = POSICOES['veiculos'][1] + CAB + len(TABELAS['veiculos']) * LIN
    topo_vendas = POSICOES['vendas'][1]
    xv = 560 + TAB_L / 2
    ligacoes.append(linha(xv, base_veic, xv, topo_vendas, TINTA, 2.2))
    ligacoes += pe_de_galinha(xv, base_veic, (0, 1), 'um')
    ligacoes += pe_de_galinha(xv, topo_vendas, (0, -1), 'zero_um')
    # clientes.id (1) -> vendas.cliente_id (0..n)
    y1 = y_coluna('clientes', 'id')
    y2 = y_coluna('vendas', 'cliente_id')
    ligacoes.append(f'<polyline points="460,{y1} 510,{y1} 510,{y2} 560,{y2}" '
                    f'fill="none" stroke="{TINTA}" stroke-width="2.2"/>')
    ligacoes += pe_de_galinha(460, y1, (1, 0), 'um')
    ligacoes += pe_de_galinha(560, y2, (-1, 0), 'zero_muitos')
    # funcionarios.id (1) -> vendas.funcionario_id (0..n)
    y1 = y_coluna('funcionarios', 'id')
    y2 = y_coluna('vendas', 'funcionario_id')
    ligacoes.append(f'<polyline points="1060,{y1} 1010,{y1} 1010,{y2} 960,{y2}" '
                    f'fill="none" stroke="{TINTA}" stroke-width="2.2"/>')
    ligacoes += pe_de_galinha(1060, y1, (-1, 0), 'um')
    ligacoes += pe_de_galinha(960, y2, (1, 0), 'zero_muitos')

    tabelas = []
    for nome in TABELAS:
        tabelas += tabela_svg(nome)

    # Rótulos das ligações
    rotulos = [
        texto(498, 340, 'fornece', 17, 'normal', CINZA, 'end', italico=True),
        texto(xv + 16, (base_veic + topo_vendas) / 2, 'é vendido em', 17,
              'normal', CINZA, 'start', italico=True),
    ]

    # Legenda (canto superior direito)
    lx, ly = 1060, 70
    leg = [f'<rect x="{lx}" y="{ly}" width="400" height="330" rx="6" '
           f'fill="#FAFBFC" stroke="#C9D2DC" stroke-width="1.4"/>',
           texto(lx + 22, ly + 32, 'Legenda', 20, 'bold', TINTA, 'start')]
    y = ly + 76
    for k, cor, desc in (('PK', '#B8860B', 'Chave primária'),
                         ('FK', LARANJA, 'Chave estrangeira'),
                         ('UK', '#4B6F8F', 'Valor único (UNIQUE)')):
        leg.append(f'<rect x="{lx + 22}" y="{y - 12}" width="36" height="24" '
                   f'rx="4" fill="{cor}"/>')
        leg.append(texto(lx + 40, y, k, 14, 'bold', '#FFFFFF'))
        leg.append(texto(lx + 120, y, desc, 18, ancora='start'))
        y += 42
    y += 6
    for tipo, desc in (('um', 'Exatamente um'),
                       ('zero_um', 'Zero ou um'),
                       ('zero_muitos', 'Zero ou muitos')):
        leg.append(linha(lx + 22, y, lx + 98, y, TINTA, 2.2))
        leg += pe_de_galinha(lx + 98, y, (-1, 0), tipo)
        leg.append(texto(lx + 120, y, desc, 18, ancora='start'))
        y += 44
    corpo = ligacoes + tabelas + rotulos + leg
    return svg(1520, 880, corpo)


if __name__ == '__main__':
    os.makedirs(SAIDA, exist_ok=True)
    for nome, conteudo in (('mer', mer()), ('der', der())):
        caminho = os.path.join(SAIDA, nome + '.svg')
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print('gerado', os.path.normpath(caminho))

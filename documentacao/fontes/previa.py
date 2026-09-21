"""Gera uma pré-visualização fiel do .docx a partir do XML.

O LibreOffice não funciona neste ambiente e o mammoth descarta
alinhamento, recuo e bordas. Este script lê as propriedades reais de
cada parágrafo (alinhamento, recuo, negrito, estilo) e monta um HTML
paginado em A4 com as margens do documento, para conferir o resultado.
"""
import base64
import sys
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

ALINHAMENTO = {
    WD_ALIGN_PARAGRAPH.LEFT: 'left',
    WD_ALIGN_PARAGRAPH.CENTER: 'center',
    WD_ALIGN_PARAGRAPH.RIGHT: 'right',
    WD_ALIGN_PARAGRAPH.JUSTIFY: 'justify',
}


def escapar(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def paragrafo_html(p, dentro_tabela=False):
    partes = []
    for r in p.runs:
        txt = escapar(r.text)
        if r.font.bold:
            txt = f'<b>{txt}</b>'
        partes.append(txt)
    texto = ''.join(partes)

    pf = p.paragraph_format
    estilo = []
    al = ALINHAMENTO.get(p.alignment)
    if al:
        estilo.append(f'text-align:{al}')
    if pf.first_line_indent and not dentro_tabela:
        estilo.append(f'text-indent:{pf.first_line_indent.cm:.2f}cm')
    else:
        estilo.append('text-indent:0')
    if pf.line_spacing:
        estilo.append(f'line-height:{pf.line_spacing}')
    tamanho = 12
    if p.runs and p.runs[0].font.size:
        tamanho = p.runs[0].font.size.pt
    estilo.append(f'font-size:{tamanho}pt')

    nome = p.style.name if p.style is not None else ''
    if nome.startswith('Heading'):
        estilo.append('font-weight:700' if nome != 'Heading 3' else 'font-weight:400')
        estilo.append('margin:14pt 0 8pt')
    else:
        estilo.append('margin:0 0 6pt')

    if not texto.strip():
        # parágrafo vazio ou com imagem
        imgs = p._p.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
        if imgs:
            return None  # a imagem é tratada fora
        return '<p style="margin:0 0 6pt">&nbsp;</p>'
    return f'<p style="{";".join(estilo)}">{texto}</p>'


def main(caminho, saida):
    doc = Document(caminho)
    partes = []
    # larguras de folha por secao, para a previa mostrar a pagina deitada
    folhas = [(sec.page_width.cm, sec.page_height.cm, sec.left_margin.cm,
               sec.right_margin.cm, sec.top_margin.cm, sec.bottom_margin.cm)
              for sec in doc.sections]
    s = doc.sections[0]

    # mapeia as imagens por rId
    imagens = {}
    for rid, rel in doc.part.rels.items():
        if 'image' in rel.reltype:
            dados = base64.b64encode(rel.target_part.blob).decode()
            imagens[rid] = f'data:image/png;base64,{dados}'

    corpo = doc.element.body
    ns = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    }
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    for filho in corpo.iterchildren():
        tag = filho.tag.split('}')[-1]
        if tag == 'p':
            p = Paragraph(filho, doc)
            blip = filho.find('.//a:blip', ns)
            if blip is not None:
                rid = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                ext = filho.find('.//wp:extent', {'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'})
                larg_cm = int(ext.get('cx')) / 360000 if ext is not None else 15
                partes.append(
                    f'<div style="text-align:center;margin:8pt 0">'
                    f'<img src="{imagens.get(rid, "")}" style="width:{larg_cm:.2f}cm;border:1px solid #ccc"></div>')
                continue
            html = paragrafo_html(p)
            if html:
                partes.append(html)
        elif tag == 'tbl':
            t = Table(filho, doc)
            linhas = []
            for i, row in enumerate(t.rows):
                celulas = []
                for c in row.cells:
                    conteudo = ''.join(
                        paragrafo_html(cp, dentro_tabela=True) or '' for cp in c.paragraphs)
                    fundo = 'background:#E8EEF0;' if i == 0 else ''
                    celulas.append(
                        f'<td style="{fundo}border:1px solid #666;padding:4px 7px;'
                        f'vertical-align:middle">{conteudo}</td>')
                linhas.append('<tr>' + ''.join(celulas) + '</tr>')
            colgroup = '<colgroup>' + ''.join(
                f'<col style="width:{c.width.cm:.2f}cm">' for c in t.columns) + '</colgroup>'
            partes.append(
                '<table style="border-collapse:collapse;width:16cm;margin:8pt 0;'
                'table-layout:fixed">' + colgroup + ''.join(linhas) + '</table>')

    html = f"""<!doctype html><meta charset="utf-8">
<style>
 body{{background:#9aa;margin:0;padding:20px;font-family:Arial,sans-serif}}
 .folha{{background:#fff;width:21cm;min-height:29.7cm;margin:0 auto 18px;
        padding:{s.top_margin.cm}cm {s.right_margin.cm}cm {s.bottom_margin.cm}cm {s.left_margin.cm}cm;
        box-sizing:border-box;box-shadow:0 2px 10px rgba(0,0,0,.3)}}
 p{{color:#000}}
</style>
<div class="folha">{''.join(partes)}</div>"""
    open(saida, 'w', encoding='utf-8').write(html)
    print('gerado:', saida, '|', len(partes), 'blocos')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

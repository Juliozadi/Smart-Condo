"""Gera o .docx e o .pdf finais com o sumário e as listas paginados.

    python paginar.py

1. roda o montar.js;
2. converte o .docx em PDF com o LibreOffice;
3. procura no PDF a página de cada título e de cada legenda (alvos.json);
4. grava paginas.json e repete até os números se estabilizarem.

A numeração segue a ABNT: a capa não é contada, a folha de rosto é a
página 1, e o número aparece a partir da introdução.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.normpath(os.path.join(AQUI, '..'))
NOME = 'Documentacao_Concessionaria_ABNT'
DOCX = os.path.join(RAIZ, NOME + '.docx')
PDF = os.path.join(RAIZ, NOME + '.pdf')


def normalizar(texto):
    return re.sub(r'\s+', ' ', texto).strip()


def gerar_pdf():
    subprocess.run(['node', 'montar.js'], cwd=AQUI, check=True,
                   stdout=subprocess.DEVNULL)
    tmp = tempfile.mkdtemp()
    subprocess.run(['soffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', tmp, DOCX], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return os.path.join(tmp, NOME + '.pdf')


def localizar(pdf):
    texto = subprocess.run(['pdftotext', pdf, '-'], capture_output=True,
                           text=True, check=True).stdout
    paginas = [normalizar(p) for p in texto.split('\f')]
    alvos = json.load(open(os.path.join(AQUI, 'alvos.json'), encoding='utf-8'))
    # O texto começa depois da página do SUMÁRIO
    inicio = next(i for i, p in enumerate(paginas) if p.startswith('SUMÁRIO')) + 1
    resultado = {}
    atual = inicio
    for alvo in alvos:
        chave = normalizar(alvo)
        while atual < len(paginas) and chave not in paginas[atual]:
            atual += 1
        if atual == len(paginas):
            raise SystemExit(f'não encontrado no PDF: {alvo}')
        resultado[alvo] = atual  # índice 0 = capa; folha de rosto = 1
    return resultado, len(paginas)


def main():
    arq = os.path.join(AQUI, 'paginas.json')
    anterior = None
    for rodada in range(1, 5):
        pdf = gerar_pdf()
        paginas, total = localizar(pdf)
        with open(arq, 'w', encoding='utf-8') as f:
            json.dump(paginas, f, ensure_ascii=False, indent=1)
        print(f'rodada {rodada}: {total} páginas no PDF')
        if paginas == anterior:
            break
        anterior = paginas
    shutil.copy(pdf, PDF)
    print('gerados:', os.path.relpath(DOCX), 'e', os.path.relpath(PDF))


if __name__ == '__main__':
    main()

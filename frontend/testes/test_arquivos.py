"""Fluxos com arquivo, de ponta a ponta no navegador.

- A foto que a portaria tira chega ao morador da unidade — e só com o
  token, porque a API não serve essas fotos por endereço aberto.
- Os documentos escolhidos no cadastro do morador são enviados e o
  síndico os abre na fila de aprovação.

Os testes criam registros novos (visitante, cadastro) a cada execução;
o e-mail e o CPF do cadastro são gerados na hora para não colidir.
"""
from __future__ import annotations

import random
import struct
import zlib

from conftest import FRONT, abrir, ir


def png(largura=48, altura=48, cor=(16, 182, 168)) -> bytes:
    """Um PNG de verdade, que o navegador consegue abrir."""
    def bloco(tipo, dados):
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(
            ">I", zlib.crc32(tipo + dados) & 0xFFFFFFFF)
    linha = b"\x00" + bytes(cor) * largura
    return (b"\x89PNG\r\n\x1a\n"
            + bloco(b"IHDR", struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0))
            + bloco(b"IDAT", zlib.compress(linha * altura))
            + bloco(b"IEND", b""))


PDF = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
       b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
       b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
       b"trailer<</Root 1 0 R>>\n%%EOF")


def cpf_valido() -> str:
    base = [random.randint(0, 9) for _ in range(9)]
    for _ in range(2):
        soma = sum(d * p for d, p in zip(base, range(len(base) + 1, 1, -1)))
        base.append(0 if soma % 11 < 2 else 11 - soma % 11)
    return "".join(map(str, base))


def test_foto_do_visitante_chega_ao_morador_so_com_o_token(navegador):
    ctx, pg = abrir(navegador, papel="porteiro")
    ir(pg, "pages/porteiro/visitantes.html", 1200)
    nome = f"Visitante Foto {random.randint(1000, 9999)}"
    pg.fill("#nome-visitante", nome)
    pg.fill("#doc-visitante", cpf_valido())
    pg.select_option("#apto-visitante", label="204")
    pg.select_option("#tipo-visita", index=1)
    pg.set_input_files(".captura-foto input[type=file]", files=[
        {"name": "visitante.png", "mimeType": "image/png", "buffer": png()}])
    pg.wait_for_selector(".captura-imagem", timeout=5000)
    pg.click("#formVisitante button[type=submit]")
    pg.wait_for_selector("#erroVisitante.sucesso", timeout=10000)
    # O formulário limpo também tira a prévia da foto.
    assert pg.locator(".captura-imagem").count() == 0

    # No cartão do porteiro, a foto entra no lugar das iniciais.
    cartao = pg.locator("#listaPresentes .list-item", has_text=nome)
    cartao.locator("img.foto-registro").wait_for(timeout=5000)
    assert cartao.locator("img.foto-registro").get_attribute("src").startswith("blob:")
    assert pg.erros == []
    ctx.close()

    ctx, pg = abrir(navegador, papel="morador")
    item = pg.locator(".portaria-item", has_text=nome)
    item.locator("img.retrato").wait_for(timeout=8000)
    retrato = item.locator("img.retrato")
    assert retrato.get_attribute("src").startswith("blob:")
    assert retrato.evaluate("i => i.naturalWidth") > 0
    # O caminho da foto, aberto sem o token, não entrega nada.
    status = pg.evaluate("""async () => {
        const api = window.SmartCondo.api;
        const lista = await api.get('/portaria/visitantes');
        const r = await fetch(api.url + lista[0].foto_url);
        return r.status;
    }""")
    assert status == 401
    assert pg.erros == []
    ctx.close()


def test_camera_mostra_uma_coisa_por_vez(navegador):
    """Aviso, câmera e foto dividem o mesmo espaço: nunca dois ao mesmo tempo."""
    ctx, pg = abrir(navegador, papel="porteiro")
    ctx.grant_permissions(["camera"], origin=FRONT)
    ir(pg, "pages/porteiro/visitantes.html", 1000)
    visiveis = """() => [...document.querySelectorAll('.captura-palco > *')]
        .filter(e => getComputedStyle(e).display !== 'none').map(e => e.className)"""
    assert pg.evaluate(visiveis) == ["captura-vazio"]

    pg.click(".captura-btn.abrir")
    pg.wait_for_function("document.querySelector('.captura-video').readyState >= 2", timeout=8000)
    assert pg.evaluate(visiveis) == ["captura-video"]

    pg.click(".captura-btn.tirar")
    assert pg.evaluate(visiveis) == ["captura-imagem"]
    assert pg.input_value(".captura-valor").startswith("data:image/jpeg")

    pg.click(".captura-btn.refazer")
    assert pg.evaluate(visiveis) == ["captura-vazio"]
    assert pg.erros == []
    ctx.close()


def test_documentos_do_cadastro_chegam_ao_sindico(navegador):
    ctx, pg = abrir(navegador)
    ir(pg, "pages/cadastro/morador.html", 1000)
    sufixo = random.randint(10000, 99999)
    nome = f"Paula Documentos {sufixo}"

    # Etapa 1 — dados pessoais e a foto de perfil
    pg.fill("#mNome", nome)
    pg.fill("#mCpf", cpf_valido())
    pg.fill("#mNascimento", "1990-05-10")
    pg.fill("#mEmail", f"paula{sufixo}@exemplo.com")
    pg.fill("#mTelefone", "(67) 99999-1234")
    pg.set_input_files("#foto-m", files=[
        {"name": "eu.png", "mimeType": "image/png", "buffer": png()}])
    assert "eu.png" in pg.inner_text("label[for=foto-m]")
    pg.evaluate("mostrarStep(2)")
    pg.wait_for_selector("#step2", state="visible")

    # Etapa 2 — unidade
    pg.fill("#mCodigoCondominio", "PALM-2025")
    pg.fill("#mApartamento", "505")
    pg.select_option("#mOcupacao", "proprietario")
    pg.evaluate("mostrarStep(3)")
    pg.wait_for_selector("#step3", state="visible")

    # Etapa 3 — um arquivo recusado antes de sair do navegador...
    pg.set_input_files("#doc-rg-m", files=[
        {"name": "rg.exe", "mimeType": "application/octet-stream", "buffer": b"MZ"}])
    assert "PDF, JPG, PNG ou WebP" in pg.inner_text("label[for=doc-rg-m]")
    # ...e os de verdade.
    pg.set_input_files("#doc-rg-m", files=[
        {"name": "rg.pdf", "mimeType": "application/pdf", "buffer": PDF}])
    pg.set_input_files("#doc-res-m", files=[
        {"name": "conta.png", "mimeType": "image/png", "buffer": png(cor=(230, 162, 60))}])
    assert "rg.pdf" in pg.inner_text("label[for=doc-rg-m]")
    pg.fill("#mSenha", "senhaforte123")
    pg.fill("#mConfirmarSenha", "senhaforte123")
    for caixa in pg.locator("#step3 .terms-check input[type=checkbox]").all():
        caixa.check()
    pg.click("#btnFinalizarMorador")
    pg.wait_for_url("**/confirmar_codigo.html", timeout=15000)
    assert pg.erros == []

    # Confirma o código (em DEBUG ele volta na resposta do cadastro).
    dados = pg.evaluate("JSON.parse(sessionStorage.getItem('smartcondo_cadastro'))")
    r = pg.request.post(f"{FRONT.rsplit(':', 1)[0]}:8000/api/v1/auth/confirmar",
                        data={"email": dados["email"], "codigo": dados["codigo_debug"]})
    assert r.ok, r.text()
    ctx.close()

    # O síndico vê os documentos no cartão do cadastro pendente e abre.
    ctx, pg = abrir(navegador, papel="sindico")
    ir(pg, "pages/sindico/moradores.html", 1200)
    cartao = pg.locator("#listaPendentes .list-item", has_text=nome)
    cartao.locator(".doc-chip").first.wait_for(timeout=8000)
    chips = cartao.locator("button.doc-chip").all_inner_texts()
    assert chips == ["RG ou CNH", "Comprovante de residência"]
    # A escritura é opcional: não aparece como falta.
    assert cartao.locator(".doc-chip.falta").count() == 0

    cartao.locator("button.doc-chip", has_text="Comprovante").click()
    img = pg.locator("#visorConteudo img")
    img.wait_for(timeout=5000)
    assert img.get_attribute("src").startswith("blob:")
    assert img.evaluate("i => i.naturalWidth") > 0
    pg.keyboard.press("Escape")
    assert not pg.locator("#visorDocumento").is_visible()

    cartao.locator("button.doc-chip", has_text="RG").click()
    pg.locator("#visorConteudo iframe").wait_for(timeout=5000)
    pg.click("#visorFechar")
    assert pg.erros == []
    ctx.close()


def test_foto_da_ocorrencia_do_morador_chega_ao_sindico(navegador):
    ctx, pg = abrir(navegador, papel="morador")
    ir(pg, "pages/morador/ocorrencias.html", 1000)
    assunto = f"Lâmpada queimada {random.randint(1000, 9999)}"
    pg.select_option("#ocorre_tipoDeOcorrencia", index=1)
    pg.select_option("#ocorre_prioridade", index=1)
    pg.select_option("#ocorre_localDaOcorrencia", index=1)
    pg.fill("#ocorre_assunto", assunto)
    pg.fill("#ocorre_descricaoDetalhada", "A lâmpada do corredor está queimada há dias.")
    pg.set_input_files(".captura-foto input[type=file]", files=[
        {"name": "lampada.png", "mimeType": "image/png", "buffer": png(cor=(250, 200, 40))}])
    pg.wait_for_selector(".captura-imagem", timeout=5000)
    pg.click("#formOcorrencia button[type=submit]")
    pg.wait_for_selector("#erroOcorrencia.sucesso", timeout=10000)
    # Na lista do próprio morador, com a miniatura.
    pg.locator(".list-item", has_text=assunto).locator(".miniatura-foto img").wait_for(timeout=8000)
    assert pg.erros == []
    ctx.close()

    ctx, pg = abrir(navegador, papel="sindico")
    ir(pg, "pages/sindico/ocorrencias.html", 1200)
    mini = pg.locator(".list-item", has_text=assunto).locator(".miniatura-foto img")
    mini.wait_for(timeout=8000)
    assert mini.get_attribute("src").startswith("blob:")
    assert mini.evaluate("i => i.naturalWidth") > 0
    assert pg.erros == []
    ctx.close()


def test_documento_do_sindico_chega_ao_morador(navegador):
    """O síndico envia o PDF; o morador abre com o token, numa aba nova."""
    ctx, pg = abrir(navegador, papel="sindico")
    ir(pg, "pages/sindico/documentos.html", 1200)
    titulo = f"Ata de teste {random.randint(1000, 9999)}"
    pg.fill("#doc_titulo", titulo)
    pg.select_option("#doc_categoria", "ata")
    # Arquivo de outro tipo não chega a sair do navegador.
    pg.set_input_files("#doc_arquivo", files=[
        {"name": "ata.exe", "mimeType": "application/octet-stream", "buffer": b"MZ"}])
    pg.click("#formDocumento button[type=submit]")
    assert "PDF, JPG, PNG ou WebP" in pg.inner_text("#erroDocumento")
    pg.set_input_files("#doc_arquivo", files=[
        {"name": "ata.pdf", "mimeType": "application/pdf", "buffer": PDF}])
    pg.click("#formDocumento button[type=submit]")
    pg.wait_for_selector("#erroDocumento.sucesso", timeout=10000)
    pg.locator("#tabelaDocumentos .table-row", has_text=titulo).wait_for(timeout=5000)
    assert pg.erros == []
    ctx.close()

    ctx, pg = abrir(navegador, papel="morador")
    ir(pg, "pages/morador/documentos.html", 1200)
    cartao = pg.locator(".dash-card", has_text=titulo)
    cartao.wait_for(timeout=8000)
    with pg.expect_popup() as aba:
        cartao.locator("button.link-baixar").click()
    nova = aba.value
    nova.wait_for_url("blob:**", timeout=8000)
    # Sem o token, o mesmo caminho não entrega o arquivo.
    status = pg.evaluate("""async (t) => {
        const api = window.SmartCondo.api;
        const doc = (await api.get('/documentos')).find(d => d.titulo === t);
        return (await fetch(api.url + doc.url)).status;
    }""", titulo)
    assert status == 401
    assert pg.erros == []
    ctx.close()


def test_planilha_exportada_nao_vira_formula(navegador):
    """Nome digitado como =HYPERLINK(...) não pode virar fórmula no Excel."""
    ctx, pg = abrir(navegador, papel="sindico")
    ir(pg, "pages/sindico/moradores.html", 1200)
    with pg.expect_download() as baixado:
        pg.evaluate("""() => window.SmartCondo.api.baixarCsv('teste.csv', [
            ['Nome', 'Valor'], ['=HYPERLINK("http://x")', 450], ['-2+3', -5], ['Ana', '1.200,00']])""")
    texto = open(baixado.value.path(), encoding="utf-8-sig", newline="").read()
    assert texto.split("\r\n") == [
        '"Nome";"Valor"', '"\'=HYPERLINK(""http://x"")";"450"', '"\'-2+3";"-5"', '"Ana";"1.200,00"']

    # O botão da própria tela continua gerando a planilha.
    with pg.expect_download() as baixado:
        pg.get_by_role("button", name="Exportar").first.click()
    assert baixado.value.suggested_filename == "moradores.csv"
    assert open(baixado.value.path(), encoding="utf-8-sig", newline="").read().startswith('"Nome";"E-mail"')
    assert pg.erros == []
    ctx.close()

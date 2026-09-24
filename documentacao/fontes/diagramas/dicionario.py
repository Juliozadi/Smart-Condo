# -*- coding: utf-8 -*-
"""Gera o dicionário de dados e a lista de relacionamentos, em JS.

Tipo, obrigatoriedade, valor padrão, chaves e valores dos tipos
enumerados são lidos do banco em funcionamento — nunca copiados à mão,
que é como um dicionário de dados envelhece sem ninguém perceber. O que
o script não consegue deduzir é o significado de cada coluna em
português; isso está no dicionário DESCRICOES abaixo, e a geração falha
se alguma coluna ficar sem descrição.

    python3 dicionario.py     # escreve ../banco_gerado.js
"""
import subprocess
import json
import os

BANCO = os.environ.get("DATABASE_URL_PSQL",
                       "postgresql://smartcondo:smartcondo@127.0.0.1:5432/smartcondo")

# O que cada tabela é, em uma frase.
TABELAS = {
    "condominios": "Os condomínios atendidos pela plataforma. É o cadastro raiz: tudo o mais pertence, direta ou indiretamente, a um condomínio.",
    "unidades": "Os apartamentos ou casas de cada condomínio. A unidade é o que liga o morador às cobranças, encomendas, visitantes e ocorrências.",
    "usuarios": "Todas as pessoas que acessam o sistema, em qualquer papel: administrador, síndico, porteiro e morador.",
    "codigos_verificacao": "Os códigos enviados para confirmar um cadastro ou recuperar uma senha, com prazo de validade e contagem de tentativas.",
    "permissoes_porteiro": "O que cada porteiro pode fazer no sistema, definido pelo síndico porteiro a porteiro.",
    "espacos_comuns": "As áreas comuns do condomínio: salão de festas, churrasqueira, academia, piscina.",
    "reservas": "As reservas de espaços feitas pelos moradores, com a avaliação do síndico quando o espaço exige aprovação.",
    "registros_ocupacao": "A contagem de pessoas nas áreas de uso livre, registrada pela portaria, para que o morador saiba se o espaço está cheio.",
    "comunicados": "Os avisos publicados pelo síndico para o condomínio.",
    "leituras_comunicado": "Quem leu qual comunicado, para que o síndico saiba o alcance do aviso.",
    "documentos": "Os documentos do condomínio disponibilizados aos moradores: convenção, regimento, atas, plantas e prestações de contas.",
    "ocorrencias": "Os problemas e reclamações registrados por moradores e porteiros, e a resposta do síndico.",
    "ordens_servico": "As ordens de serviço de manutenção abertas pelo síndico, com prioridade, custo e acompanhamento.",
    "cobrancas": "As cobranças emitidas para cada unidade, por competência.",
    "pagamentos": "Os pagamentos registrados para cada cobrança. Uma cobrança pode receber mais de um pagamento.",
    "preferencias_cobranca": "O dia do mês e a forma de pagamento que cada morador prefere.",
    "visitantes": "Os visitantes anunciados pela portaria e a confirmação do morador.",
    "encomendas": "As encomendas recebidas na portaria e a retirada pelo morador.",
    "movimentacoes_veiculo": "As entradas e saídas de veículos registradas na portaria.",
    "mensagens": "As mensagens do chat entre síndico, porteiros e moradores do mesmo condomínio.",
    "documentos_cadastro": "Os documentos que o morador envia ao se cadastrar, para o síndico conferir antes de aprovar.",
}

# O significado de cada coluna que não é identificador, vínculo ou carimbo
# de tempo automático — essas são descritas pelo próprio script.
DESCRICOES = {
    "condominios.nome": "Razão social ou nome pelo qual o condomínio é conhecido",
    "condominios.cnpj": "CNPJ do condomínio, conferido pelos dígitos verificadores e único na plataforma",
    "documentos_cadastro.tipo": "RG ou CNH, comprovante de residência ou escritura; um arquivo por tipo",
    "documentos_cadastro.arquivo": "Nome aleatório do arquivo gravado pela API, nunca o nome original",
    "documentos_cadastro.tipo_conteudo": "Tipo do arquivo conferido pelo conteúdo: PDF, JPEG, PNG ou WebP",
    "documentos_cadastro.tamanho_bytes": "Tamanho do arquivo enviado",
    "documentos_cadastro.enviado_em": "Momento do envio",
    "condominios.cep": "CEP do endereço",
    "condominios.logradouro": "Rua, avenida ou praça",
    "condominios.numero": "Número do imóvel no logradouro",
    "condominios.complemento": "Complemento do endereço, quando houver",
    "condominios.bairro": "Bairro",
    "condominios.cidade": "Cidade",
    "condominios.uf": "Sigla da unidade federativa",
    "condominios.telefone": "Telefone de contato da administração",
    "condominios.codigo_acesso": "Código que o morador informa para se cadastrar no condomínio certo; pode ser trocado a qualquer momento",

    "unidades.numero": "Número do apartamento ou da casa",
    "unidades.bloco": "Bloco ou torre, quando o condomínio tiver mais de um",
    "unidades.andar": "Andar em que a unidade fica",
    "unidades.vagas_garagem": "Quantidade de vagas de garagem da unidade; a soma das vagas alimenta o cálculo de ocupação do estacionamento",

    "usuarios.nome": "Nome completo",
    "usuarios.email": "E-mail, usado para entrar no sistema e para receber os códigos; único na plataforma",
    "usuarios.cpf": "CPF, conferido pelos dígitos verificadores e único na plataforma",
    "usuarios.telefone": "Telefone de contato",
    "usuarios.data_nascimento": "Data de nascimento",
    "usuarios.senha_hash": "Resumo criptográfico da senha. A senha em si não é guardada em lugar nenhum",
    "usuarios.papel": "Papel do usuário, que determina o que ele enxerga e pode fazer",
    "usuarios.status": "Situação do cadastro ao longo do fluxo de entrada, da confirmação do código até a liberação do acesso",
    "usuarios.tipo_ocupacao": "Relação do morador com a unidade: proprietário, inquilino ou coabitante",
    "usuarios.foto_url": "Endereço da foto de perfil, quando houver",
    "usuarios.avaliado_em": "Data e hora em que o síndico aprovou ou recusou o cadastro",
    "usuarios.motivo_recusa": "Justificativa registrada pelo síndico ao recusar o cadastro; é o que o morador vê na tela de espera",
    "usuarios.tentativas_login": "Senhas erradas seguidas; zera no primeiro acesso bem-sucedido",
    "usuarios.bloqueado_ate": "Momento até o qual a conta fica bloqueada depois de sucessivas senhas erradas",
    "usuarios.versao_sessao": "Versão da sessão, gravada em cada token; sobe quando a senha é trocada ou redefinida, e os tokens antigos deixam de valer",

    "codigos_verificacao.codigo_hash": "Resumo criptográfico do código enviado. O código em si não é guardado",
    "codigos_verificacao.finalidade": "Para que o código serve: confirmar o cadastro ou recuperar a senha",
    "codigos_verificacao.canal": "Meio pelo qual o código foi enviado",
    "codigos_verificacao.expira_em": "Momento a partir do qual o código deixa de ser aceito",
    "codigos_verificacao.consumido_em": "Momento em que o código foi usado; depois disso ele não vale mais",
    "codigos_verificacao.tentativas": "Quantas vezes o código foi informado errado; esgotado o limite, o código é invalidado",
    "codigos_verificacao.destino": "Endereço para onde o código foi enviado",

    "permissoes_porteiro.registrar_visitantes": "Se o porteiro pode anunciar visitantes",
    "permissoes_porteiro.registrar_encomendas": "Se o porteiro pode registrar encomendas",
    "permissoes_porteiro.registrar_veiculos": "Se o porteiro pode registrar entrada e saída de veículos",
    "permissoes_porteiro.registrar_ocorrencias": "Se o porteiro pode abrir ocorrências",
    "permissoes_porteiro.acessar_financeiro": "Se o porteiro pode consultar a área financeira",

    "espacos_comuns.nome": "Nome do espaço",
    "espacos_comuns.descricao": "Descrição e regras de uso",
    "espacos_comuns.capacidade": "Quantas pessoas o espaço comporta",
    "espacos_comuns.reservavel": "Se o espaço precisa ser reservado antes do uso",
    "espacos_comuns.uso_livre": "Se o espaço pode ser usado sem reserva; nesse caso a ocupação é acompanhada pela contagem da portaria",
    "espacos_comuns.em_manutencao": "Se o espaço está temporariamente indisponível",

    "reservas.data": "Dia da reserva",
    "reservas.hora_inicio": "Hora de início",
    "reservas.hora_fim": "Hora de término; precisa ser posterior à de início",
    "reservas.pessoas_estimadas": "Quantas pessoas o morador espera receber",
    "reservas.observacoes": "Observações do morador ao solicitar",
    "reservas.status": "Situação da reserva, da solicitação até a conclusão ou o cancelamento",
    "reservas.avaliada_em": "Data e hora em que o síndico aprovou ou recusou",
    "reservas.motivo_recusa": "Justificativa registrada pelo síndico ao recusar",

    "registros_ocupacao.pessoas": "Quantas pessoas estavam no espaço no momento da contagem; não pode ser negativo",
    "registros_ocupacao.registrado_em": "Momento da contagem",

    "comunicados.titulo": "Título do aviso",
    "comunicados.conteudo": "Texto do aviso",
    "comunicados.categoria": "Assunto do aviso, usado para filtrar e destacar na tela",
    "comunicados.fixado": "Se o aviso deve permanecer no topo da lista",
    "comunicados.publicado_em": "Momento da publicação; é por ele que a lista é ordenada",

    "leituras_comunicado.lido_em": "Momento em que o usuário abriu o comunicado",

    "documentos.titulo": "Título do documento",
    "documentos.descricao": "Breve explicação do conteúdo",
    "documentos.categoria": "Tipo do documento",
    "documentos.arquivo": "Nome do arquivo (PDF ou imagem) enviado pelo síndico, gravado pela API sem endereço público",
    "documentos.tipo_conteudo": "Tipo do arquivo conferido pelo conteúdo (application/pdf, image/png...)",
    "documentos.tamanho_kb": "Tamanho do arquivo em kilobytes, exibido antes do download",
    "documentos.publicado_em": "Momento da publicação",

    "ocorrencias.titulo": "Resumo do problema",
    "ocorrencias.descricao": "Relato completo",
    "ocorrencias.categoria": "Assunto da ocorrência",
    "ocorrencias.local": "Onde o problema foi observado",
    "ocorrencias.prioridade": "Urgência atribuída no registro",
    "ocorrencias.foto_arquivo": "Nome do arquivo da foto anexada por quem abriu, gravado pela API sem endereço público",
    "ocorrencias.status": "Situação do atendimento, da abertura ao arquivamento",
    "ocorrencias.resposta": "Resposta do síndico a quem abriu a ocorrência",
    "ocorrencias.respondida_em": "Momento da resposta",

    "ordens_servico.tipo": "Natureza do serviço a executar",
    "ordens_servico.descricao": "O que precisa ser feito",
    "ordens_servico.local": "Onde o serviço será executado",
    "ordens_servico.prioridade": "Urgência do serviço",
    "ordens_servico.status": "Andamento da ordem, da abertura à conclusão ou ao cancelamento",
    "ordens_servico.fornecedor": "Empresa ou profissional responsável",
    "ordens_servico.data_prevista": "Data prevista para a execução",
    "ordens_servico.custo_estimado": "Valor orçado; quando informado, não pode ser negativo",
    "ordens_servico.custo_real": "Valor efetivamente gasto; quando informado, não pode ser negativo",
    "ordens_servico.concluida_em": "Momento da conclusão",
    "ordens_servico.observacoes": "Anotações de acompanhamento",

    "cobrancas.competencia": "Mês a que a cobrança se refere; não pode haver duas cobranças da mesma unidade na mesma competência",
    "cobrancas.descricao": "O que está sendo cobrado",
    "cobrancas.valor": "Valor devido; precisa ser maior que zero",
    "cobrancas.vencimento": "Data de vencimento",
    "cobrancas.status": "Situação da cobrança, que acompanha os pagamentos registrados",

    "pagamentos.valor": "Valor pago; precisa ser maior que zero",
    "pagamentos.forma": "Forma utilizada no pagamento",
    "pagamentos.pago_em": "Momento do pagamento",
    "pagamentos.comprovante_url": "Endereço do comprovante, quando houver",
    "pagamentos.observacao": "Anotação sobre o pagamento",

    "preferencias_cobranca.dia_vencimento": "Dia do mês escolhido pelo morador; limitado a 28 para existir em todos os meses",
    "preferencias_cobranca.forma_preferida": "Forma de pagamento preferida",

    "visitantes.nome": "Nome do visitante",
    "visitantes.documento": "Documento apresentado na portaria",
    "visitantes.tipo_visita": "Natureza da visita",
    "visitantes.placa_veiculo": "Placa do veículo, quando o visitante chega de carro",
    "visitantes.foto_arquivo": "Nome do arquivo da foto tirada na portaria, gravado pela API sem endereço público; apagado após o prazo de guarda",
    "visitantes.status": "Situação da visita, do anúncio à saída",
    "visitantes.entrada_em": "Momento da entrada",
    "visitantes.saida_em": "Momento da saída",
    "visitantes.confirmado_em": "Momento em que o morador autorizou ou recusou",

    "encomendas.remetente": "Quem enviou, ou a transportadora",
    "encomendas.tipo_volume": "Tipo do volume recebido",
    "encomendas.codigo_rastreio": "Código de rastreio, quando houver",
    "encomendas.observacoes": "Anotações da portaria",
    "encomendas.foto_arquivo": "Nome do arquivo da foto do volume, gravado pela API sem endereço público; apagado após o prazo de guarda",
    "encomendas.status": "Situação da encomenda, do recebimento à retirada",
    "encomendas.recebida_em": "Momento em que a portaria recebeu",
    "encomendas.retirada_em": "Momento em que o morador retirou",

    "movimentacoes_veiculo.placa": "Placa do veículo",
    "movimentacoes_veiculo.modelo": "Modelo do veículo",
    "movimentacoes_veiculo.cor": "Cor do veículo",
    "movimentacoes_veiculo.tipo": "Se o registro é de entrada ou de saída",
    "movimentacoes_veiculo.categoria": "A quem o veículo pertence",
    "movimentacoes_veiculo.registrada_em": "Momento do registro",
    "movimentacoes_veiculo.observacao": "Anotação da portaria",

    "mensagens.texto": "Conteúdo da mensagem, de 1 a 2.000 caracteres",
    "mensagens.enviada_em": "Momento do envio, preenchido pelo banco",
    "mensagens.lida_em": "Momento em que o destinatário abriu a conversa; vazio enquanto não lida",
}

# O que cada vínculo significa, quando o nome da coluna não basta.
VINCULOS = {
    "condominios.sindico_id": "Síndico responsável pelo condomínio",
    "usuarios.avaliado_por_id": "Síndico que aprovou ou recusou este cadastro",
    "reservas.avaliada_por_id": "Síndico que aprovou ou recusou a reserva",
    "ocorrencias.aberta_por_id": "Quem registrou a ocorrência",
    "ocorrencias.respondida_por_id": "Síndico que respondeu",
    "ordens_servico.aberta_por_id": "Síndico que abriu a ordem",
    "encomendas.registrada_por_id": "Porteiro que recebeu a encomenda",
    "encomendas.retirada_por_id": "Morador que retirou",
    "visitantes.registrado_por_id": "Porteiro que anunciou a visita",
    "visitantes.confirmado_por_id": "Morador que autorizou ou recusou",
    "movimentacoes_veiculo.registrada_por_id": "Porteiro que registrou a movimentação",
    "registros_ocupacao.registrado_por_id": "Porteiro que fez a contagem",
    "permissoes_porteiro.porteiro_id": "Porteiro a quem as permissões pertencem",
    "permissoes_porteiro.definidas_por_id": "Síndico que definiu as permissões",
    "documentos.publicado_por_id": "Síndico que publicou o documento",
    "comunicados.autor_id": "Síndico que publicou o comunicado",
    "pagamentos.pago_por_id": "Quem registrou o pagamento",
    "preferencias_cobranca.morador_id": "Morador dono da preferência",
    "reservas.morador_id": "Morador que solicitou a reserva",
    "cobrancas.unidade_id": "Unidade cobrada",
    "codigos_verificacao.usuario_id": "Usuário a quem o código foi enviado",
    "comunicados.condominio_id": "Condomínio para o qual o aviso foi publicado",
    "documentos.condominio_id": "Condomínio a que o documento pertence",
    "documentos.unidade_id": "Unidade destinatária, quando o documento não é para todo o condomínio",
    "encomendas.unidade_id": "Unidade destinatária da encomenda",
    "espacos_comuns.condominio_id": "Condomínio a que o espaço pertence",
    "leituras_comunicado.comunicado_id": "Comunicado que foi lido",
    "leituras_comunicado.usuario_id": "Usuário que leu",
    "movimentacoes_veiculo.condominio_id": "Condomínio onde a movimentação ocorreu",
    "movimentacoes_veiculo.unidade_id": "Unidade à qual o veículo está ligado, quando houver",
    "ocorrencias.condominio_id": "Condomínio onde o problema ocorreu",
    "ocorrencias.unidade_id": "Unidade envolvida, quando a ocorrência não é de área comum",
    "ordens_servico.condominio_id": "Condomínio onde o serviço será executado",
    "pagamentos.cobranca_id": "Cobrança que está sendo paga",
    "registros_ocupacao.espaco_id": "Espaço em que a contagem foi feita",
    "reservas.espaco_id": "Espaço reservado",
    "unidades.condominio_id": "Condomínio a que a unidade pertence",
    "usuarios.condominio_id": "Condomínio em que o usuário atua; vazio apenas para o administrador da plataforma",
    "usuarios.unidade_id": "Unidade em que o morador vive; vazio para síndico, porteiro e administrador",
    "visitantes.unidade_id": "Unidade visitada",
    "mensagens.condominio_id": "Condomínio onde a conversa acontece",
    "mensagens.remetente_id": "Quem enviou a mensagem",
    "mensagens.destinatario_id": "Quem recebe a mensagem; não pode ser o próprio remetente",
    "documentos_cadastro.usuario_id": "Morador que enviou o documento",
}


def consultar(sql):
    saida = subprocess.run([
        "psql", BANCO, "-tAF|", "-c", sql
    ], capture_output=True, text=True, check=True).stdout
    return [l.split("|") for l in saida.strip().split("\n") if l]


def ler():
    colunas = consultar("""
        SELECT c.table_name, c.column_name,
               CASE WHEN c.data_type='character varying' THEN 'VARCHAR('||c.character_maximum_length||')'
                    WHEN c.data_type='numeric' THEN 'NUMERIC('||c.numeric_precision||','||c.numeric_scale||')'
                    WHEN c.data_type='timestamp with time zone' THEN 'TIMESTAMPTZ'
                    WHEN c.data_type='USER-DEFINED' THEN upper(c.udt_name)
                    WHEN c.data_type='time without time zone' THEN 'TIME'
                    ELSE upper(c.data_type) END,
               c.is_nullable
        FROM information_schema.columns c
        JOIN information_schema.tables t
          ON t.table_name=c.table_name AND t.table_schema=c.table_schema
        WHERE c.table_schema='public' AND t.table_type='BASE TABLE'
          AND c.table_name<>'alembic_version'
        ORDER BY c.table_name, c.ordinal_position""")
    chaves = consultar("""
        SELECT tc.table_name, tc.constraint_type, kcu.column_name, coalesce(ccu.table_name,'')
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON kcu.constraint_name=tc.constraint_name AND kcu.table_schema=tc.table_schema
        LEFT JOIN information_schema.constraint_column_usage ccu
          ON ccu.constraint_name=tc.constraint_name AND tc.constraint_type='FOREIGN KEY'
        WHERE tc.table_schema='public' AND tc.table_name<>'alembic_version'
          AND tc.constraint_type IN ('PRIMARY KEY','FOREIGN KEY')""")
    enums = {t: v for t, v in consultar("""
        SELECT t.typname, string_agg(e.enumlabel, ', ' ORDER BY e.enumsortorder)
        FROM pg_type t JOIN pg_enum e ON e.enumtypid=t.oid GROUP BY t.typname""")}
    unicos = consultar("""
        SELECT rel.relname, con.conname, pg_get_constraintdef(con.oid)
        FROM pg_constraint con JOIN pg_class rel ON rel.oid=con.conrelid
        JOIN pg_namespace n ON n.oid=rel.relnamespace
        WHERE n.nspname='public' AND con.contype IN ('u','c')
          AND rel.relname<>'alembic_version'
        ORDER BY rel.relname, con.conname""")
    return colunas, chaves, enums, unicos


def montar():
    colunas, chaves, enums, unicos = ler()
    pk = {(t, c) for t, tipo, c, _ in chaves if tipo == 'PRIMARY KEY'}
    fk = {(t, c): d for t, tipo, c, d in chaves if tipo == 'FOREIGN KEY'}

    faltando = []
    tabelas = []
    for nome in sorted({t for t, *_ in colunas}):
        linhas = []
        for t, col, tipo, nulo in colunas:
            if t != nome:
                continue
            marca = []
            if (t, col) in pk:
                marca.append('PK')
            if (t, col) in fk:
                marca.append('FK')
            chave = f"{t}.{col}"
            if (t, col) in pk:
                desc = 'Identificador da tabela, gerado pelo banco'
            elif (t, col) in fk:
                desc = VINCULOS.get(chave, f"Vínculo com {fk[(t, col)]}")
            elif col == 'criado_em':
                desc = 'Momento em que o registro foi criado, preenchido pelo banco'
            elif col == 'atualizado_em':
                desc = 'Momento da última alteração do registro'
            else:
                desc = DESCRICOES.get(chave)
                if desc is None:
                    faltando.append(chave)
                    desc = ''
            if tipo.lower() in enums:
                desc += f" — tipo enumerado {tipo.lower()}, valores: {enums[tipo.lower()]}"
                tipo = 'ENUM'

            linhas.append({
                'coluna': col, 'tipo': tipo,
                'obrigatorio': 'Não' if nulo == 'YES' else 'Sim',
                'chave': '/'.join(marca), 'descricao': desc,
            })
        regras = [f"{c[2]}" for c in unicos if c[0] == nome]
        tabelas.append({'nome': nome, 'resumo': TABELAS[nome],
                        'colunas': linhas, 'regras': regras})

    if faltando:
        raise SystemExit("colunas sem descrição: " + ', '.join(faltando))

    sem_texto = [f"{t}.{c}" for t, tipo, c, _ in chaves
                 if tipo == 'FOREIGN KEY' and f"{t}.{c}" not in VINCULOS]
    if sem_texto:
        raise SystemExit("chaves estrangeiras sem descrição: " + ', '.join(sem_texto))

    relacoes = []
    for t, tipo, c, destino in sorted(chaves):
        if tipo != 'FOREIGN KEY':
            continue
        relacoes.append({'origem': t, 'coluna': c, 'destino': destino,
                         'texto': VINCULOS.get(f"{t}.{c}", '')})

    destino = os.path.join(os.path.dirname(__file__), '..', 'banco_gerado.js')
    with open(destino, 'w', encoding='utf-8') as f:
        f.write("/* GERADO POR diagramas/dicionario.py — não edite à mão.\n"
                " * Tipos, obrigatoriedade e chaves vêm do banco em funcionamento;\n"
                " * as descrições estão no próprio script que gera este arquivo.\n"
                " */\n")
        f.write("const dicionario = " + json.dumps(tabelas, ensure_ascii=False, indent=2) + ";\n\n")
        f.write("const relacoes = " + json.dumps(relacoes, ensure_ascii=False, indent=2) + ";\n\n")
        f.write("const enumerados = " + json.dumps(
            [{'nome': k, 'valores': v} for k, v in sorted(enums.items())],
            ensure_ascii=False, indent=2) + ";\n\n")
        f.write("module.exports = { dicionario, relacoes, enumerados };\n")

    total = sum(len(t['colunas']) for t in tabelas)
    print(f"banco_gerado.js — {len(tabelas)} tabelas, {total} colunas, "
          f"{len(relacoes)} relacionamentos, {len(enums)} tipos enumerados")


if __name__ == '__main__':
    montar()

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
    "usuarios": "Todas as pessoas que acessam o sistema, em qualquer papel: administrador, síndico, porteiro e morador. Quem tem mais de um papel ou apartamento (o síndico que também mora, o dono de dois apartamentos) tem um cadastro por perfil, todos ligados ao cadastro com o login.",
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
    "assembleias": "As assembleias virtuais convocadas pelo síndico (Código Civil, art. 1.354-A): o período de votação e, se cancelada, o motivo.",
    "itens_pauta": "Os itens da pauta de cada assembleia, com a maioria que cada um exige para ser aprovado.",
    "votos": "O voto de cada apartamento em cada item da pauta: um por apartamento, garantido pelo banco.",
    "despesas": "O que o condomínio gastou, com o comprovante: a outra metade da prestação de contas, que os moradores veem no balancete do mês.",
    "preferencias_cobranca": "O dia do mês e a forma de pagamento que cada morador prefere.",
    "visitantes": "Os visitantes anunciados pela portaria e a confirmação do morador.",
    "autorizacoes_visita": "As entradas liberadas pelo morador antes de o visitante chegar — a diarista, o prestador da reforma, os convidados da festa —, que a portaria registra sem esperar a resposta dele.",
    "encomendas": "As encomendas recebidas na portaria e a retirada pelo morador.",
    "movimentacoes_veiculo": "As entradas e saídas de veículos registradas na portaria.",
    "infracoes": "As advertências e multas do síndico a um apartamento, com o prazo e a defesa do morador e a decisão do síndico; a multa mantida vira cobrança (Código Civil, art. 1.336, § 2º).",
    "horarios_mudanca": "Os dias da semana e os horários em que o regimento de cada condomínio permite mudança; o dia sem linha não tem mudança.",
    "anotacoes_portaria": "O livro da portaria: o que o porteiro que sai, ou o síndico, anota para o próximo turno. Não se apaga nem se edita — corrige-se com outra anotação.",
    "ciencias_anotacao": "Quem leu cada anotação importante do livro da portaria, e quando — uma vez por pessoa.",
    "planos_manutencao": "O que vence de tempos em tempos e não pode passar (AVCB, extintores, caixa d'água, elevadores, para-raios), com a periodicidade e o próximo vencimento. Remover é inativar.",
    "realizacoes_manutencao": "Cada vez que uma manutenção preventiva foi feita: o dia, o custo e a despesa lançada com ele.",
    "declaracoes_quitacao": "As declarações de que o apartamento não tinha débito vencido, com o código que qualquer um confere e o que diziam no dia em que foram emitidas. Não se apagam; o síndico revoga com motivo.",
    "mudancas": "As mudanças pedidas pelos moradores — dia, horário e empresa — com a avaliação do síndico; a portaria vê as aprovadas.",
    "veiculos_unidade": "As placas que cada apartamento cadastrou, para a portaria reconhecer o carro do morador na chegada. Deixam de valer sozinhas quando quem cadastrou se muda.",
    "mensagens": "As mensagens do chat entre síndico, porteiros e moradores do mesmo condomínio.",
    "documentos_cadastro": "Os documentos que o morador envia ao se cadastrar, para o síndico conferir antes de aprovar.",
    "registros_alteracao": "Quem criou, editou, inativou ou reativou cada registro, e quando — o \"editado por fulano\" das telas do administrador.",
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
    "condominios.complemento": "Complemento do endereço dos cadastros antigos; não é mais pedido",
    "condominios.bairro": "Bairro",
    "condominios.cidade": "Cidade",
    "condominios.uf": "Sigla da unidade federativa",
    "condominios.telefone": "Telefone de contato da administração",
    "condominios.multa_atraso": "Multa, em %, da cobrança paga depois do vencimento; de 0 a 2 (Código Civil, art. 1.336, § 1º)",
    "condominios.juros_mensais": "Juros ao mês, em %, contados por dia de atraso; de 0 a 1 (Código Civil, art. 1.336, § 1º)",
    "condominios.mudanca_antecedencia_dias": "Com quantos dias de aviso o morador agenda a mudança, pelo regimento; de 0 a 60",
    "cobrancas.origem": "De onde vem a cobrança: a taxa do mês (uma por apartamento e mês), uma multa ou o uso de um espaço",
    "infracoes.tipo": "Advertência (sem valor) ou multa",
    "infracoes.descricao": "O que aconteceu, como o síndico descreveu na notificação",
    "infracoes.artigo": "O artigo do regimento ou da convenção descumprido",
    "infracoes.ocorrida_em": "Dia da infração, no último ano",
    "infracoes.valor": "Valor da multa, até 5 vezes a contribuição mensal; vazio na advertência",
    "infracoes.prazo_defesa": "Último dia para o apartamento apresentar a defesa (de 5 a 30 dias depois da notificação)",
    "infracoes.status": "Notificada, com defesa apresentada, mantida ou anulada",
    "infracoes.defesa": "A defesa do morador, como ele escreveu",
    "infracoes.defesa_em": "Momento em que a defesa foi apresentada",
    "infracoes.decisao_motivo": "Por que o síndico manteve ou anulou; o apartamento recebe",
    "infracoes.decidida_em": "Momento da decisão",
    "horarios_mudanca.dia_semana": "Dia da semana, de 1 (segunda) a 7 (domingo); um horário por dia",
    "horarios_mudanca.hora_inicio": "A partir de que horas a mudança pode começar nesse dia",
    "horarios_mudanca.hora_fim": "Até que horas a mudança precisa terminar nesse dia",
    "anotacoes_portaria.texto": "A anotação, como o autor escreveu (de 3 a 2.000 caracteres)",
    "anotacoes_portaria.importante": "Importante: quem chegar precisa ler e dar ciência",
    "ciencias_anotacao.ciente_em": "Momento em que a pessoa deu ciência",
    "planos_manutencao.nome": "O que precisa ser feito; único entre os planos ativos do condomínio",
    "planos_manutencao.periodicidade_meses": "De quantos em quantos meses (1 a 120)",
    "planos_manutencao.proximo_vencimento": "Até quando precisa ser feito de novo; a realização mais recente o renova",
    "planos_manutencao.antecedencia_aviso_dias": "Quantos dias antes do vencimento o painel começa a avisar (0 a 180)",
    "planos_manutencao.fornecedor": "Empresa que costuma fazer o serviço",
    "planos_manutencao.observacao": "Anotação do síndico sobre o plano",
    "planos_manutencao.ultima_realizacao": "Dia da realização mais recente; vazia, ainda sem registro",
    "realizacoes_manutencao.data": "Dia em que foi feita (nunca no futuro)",
    "realizacoes_manutencao.custo": "Quanto custou; vazio, sem custo informado",
    "realizacoes_manutencao.observacao": "O que foi feito, como o síndico anotou",
    "declaracoes_quitacao.codigo": "Código de verificação, 16 letras e números sorteados (sem 0, O, 1 e I); único",
    "declaracoes_quitacao.referencia_ate": "Dia até o qual o apartamento não tinha cobrança vencida em aberto (o da emissão)",
    "declaracoes_quitacao.valida_ate": "Até quando quem recebe pode confiar na declaração (30 dias)",
    "declaracoes_quitacao.condominio_nome": "Nome do condomínio no dia da emissão, como está na declaração",
    "declaracoes_quitacao.condominio_cnpj": "CNPJ do condomínio no dia da emissão",
    "declaracoes_quitacao.identificacao_unidade": "O apartamento (e o bloco), como está na declaração",
    "declaracoes_quitacao.sindico_nome": "O síndico no dia da emissão",
    "declaracoes_quitacao.emitida_em": "Momento da emissão",
    "declaracoes_quitacao.revogada_em": "Quando o síndico revogou; vazia, a declaração não foi revogada",
    "declaracoes_quitacao.motivo_revogacao": "Por que foi revogada; o apartamento recebe, quem confere o código não vê",
    "condominios.codigo_acesso": "Código que o morador informa para se cadastrar no condomínio certo; pode ser trocado a qualquer momento",

    "unidades.numero": "Número do apartamento ou da casa",
    "unidades.bloco": "Bloco ou torre, quando o condomínio tiver mais de um",
    "unidades.andar": "Andar em que a unidade fica",
    "unidades.vagas_garagem": "Quantidade de vagas de garagem da unidade; a soma das vagas alimenta o cálculo de ocupação do estacionamento",
    "unidades.pendente": "Verdadeiro quando a unidade foi criada pelo autocadastro de um morador e ainda não foi confirmada pelo síndico; não aparece nas listas da portaria e do síndico até a aprovação",

    "usuarios.nome": "Nome completo",
    "usuarios.email": "E-mail, usado para entrar no sistema e para receber os códigos; único na plataforma",
    "usuarios.cpf": "CPF, conferido pelos dígitos verificadores e único na plataforma",
    "usuarios.telefone": "Telefone de contato",
    "usuarios.data_nascimento": "Data de nascimento",
    "usuarios.senha_hash": "Resumo criptográfico da senha. A senha em si não é guardada em lugar nenhum",
    "usuarios.papel": "Papel do usuário, que determina o que ele enxerga e pode fazer",
    "usuarios.status": "Situação do cadastro ao longo do fluxo de entrada, da confirmação do código até a liberação do acesso",
    "usuarios.tipo_ocupacao": "Relação do morador com a unidade: proprietário, inquilino ou coabitante",
    "usuarios.reside": "Se o morador mora na unidade; falso no proprietário que alugou: ele paga e vota, mas visitas, encomendas, reservas, carros e mudanças são de quem mora lá",
    "usuarios.foto_url": "Endereço da foto de perfil, quando houver",
    "usuarios.avaliado_em": "Data e hora em que o síndico aprovou ou recusou o cadastro",
    "usuarios.motivo_recusa": "Justificativa registrada pelo síndico ao recusar o cadastro; é o que o morador vê na tela de espera",
    "usuarios.tentativas_login": "Senhas erradas seguidas; zera no primeiro acesso bem-sucedido",
    "usuarios.bloqueado_ate": "Momento até o qual a conta fica bloqueada depois de sucessivas senhas erradas",
    "usuarios.unidade_desde": "Desde quando mora na unidade atual; renovado na transferência e na reativação. O morador só vê os visitantes e as encomendas a partir daqui",
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
    "permissoes_porteiro.acessar_financeiro": "Sem uso: a permissão saiu do sistema, e o financeiro é sempre recusado ao porteiro",

    "espacos_comuns.nome": "Nome do espaço",
    "espacos_comuns.descricao": "Descrição e regras de uso",
    "espacos_comuns.capacidade": "Quantas pessoas o espaço comporta",
    "espacos_comuns.reservavel": "Se o espaço precisa ser reservado antes do uso",
    "espacos_comuns.uso_livre": "Se o espaço pode ser usado sem reserva; nesse caso a ocupação é acompanhada pela contagem da portaria",
    "espacos_comuns.em_manutencao": "Se o espaço está temporariamente indisponível",
    "espacos_comuns.horario_abertura": "Regra de uso: a partir de que horas o espaço pode ser reservado; vazio = sem regra",
    "espacos_comuns.horario_fechamento": "Regra de uso: até que horas o espaço pode ser usado (ex.: 22h, pela lei do silêncio); posterior à abertura",
    "espacos_comuns.antecedencia_minima_dias": "Regra de uso: com quantos dias de antecedência, no mínimo, a reserva precisa ser feita",
    "espacos_comuns.duracao_maxima_horas": "Regra de uso: quantas horas cada reserva pode durar, no máximo",
    "espacos_comuns.limite_por_unidade": "Regra de uso: quantas reservas futuras deste espaço cada apartamento pode ter ao mesmo tempo",
    "espacos_comuns.taxa_uso": "Taxa de uso (limpeza, gás, desgaste), cobrada do apartamento quando o síndico aprova a reserva; vazia, sem taxa",

    "reservas.data": "Dia da reserva",
    "reservas.hora_inicio": "Hora de início",
    "reservas.hora_fim": "Hora de término; precisa ser posterior à de início",
    "reservas.pessoas_estimadas": "Quantas pessoas o morador espera receber",
    "reservas.observacoes": "Observações do morador ao solicitar",
    "reservas.status": "Situação da reserva, da solicitação até a conclusão ou o cancelamento",
    "reservas.avaliada_em": "Data e hora em que o síndico aprovou ou recusou",
    "reservas.motivo_recusa": "Justificativa registrada pelo síndico ao recusar",
    "reservas.cancelada_em": "Data e hora do cancelamento, pelo morador ou pelo síndico",
    "reservas.motivo_cancelamento": "Por que a reserva foi cancelada (síndico, espaço inativado ou cadastro inativado); o morador vê este texto",

    "registros_ocupacao.pessoas": "Quantas pessoas estavam no espaço no momento da contagem; não pode ser negativo",
    "registros_ocupacao.registrado_em": "Momento da contagem",

    "comunicados.titulo": "Título do aviso",
    "comunicados.conteudo": "Texto do aviso",
    "comunicados.categoria": "Assunto do aviso, usado para filtrar e destacar na tela",
    "comunicados.fixado": "Se o aviso deve permanecer no topo da lista",
    "comunicados.publicado_em": "Momento da publicação; é por ele que a lista é ordenada",
    "comunicados.bloco": "Bloco de destino, quando o aviso é só para ele (ex.: falta de água no bloco B); vazio com a unidade vazia = todo o condomínio",

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
    "pagamentos.encargos": "Parte do valor que pagou multa e juros do atraso; o resto abate a cobrança",
    "pagamentos.forma": "Forma utilizada no pagamento",
    "pagamentos.pago_em": "Momento do pagamento",
    "pagamentos.comprovante_url": "Endereço do comprovante, quando houver",
    "pagamentos.observacao": "Anotação sobre o pagamento",

    "assembleias.titulo": "Nome da assembleia",
    "assembleias.descricao": "Texto da convocação",
    "assembleias.abre_em": "Momento em que a votação abre; antes disso, só a convocação",
    "assembleias.encerra_em": "Momento em que a votação encerra; depois dele aparece o resultado. No máximo 30 dias depois da abertura",
    "assembleias.motivo_cancelamento": "Por que o síndico cancelou a assembleia; os moradores recebem",
    "assembleias.inativo_em": "Quando a assembleia foi cancelada; vazio enquanto vale",
    "itens_pauta.ordem": "Posição do item na pauta",
    "itens_pauta.titulo": "O que está sendo votado",
    "itens_pauta.descricao": "Detalhes do item, como o orçamento",
    "itens_pauta.maioria": "Quantos votos aprovam: maioria simples (mais a favor que contra), 2/3 de todos os apartamentos ou unanimidade",
    "votos.escolha": "A favor, contra ou abstenção",
    "votos.votado_em": "Momento do voto; o voto não pode ser mudado depois",
    "despesas.categoria": "Para onde foi o dinheiro: água, energia, limpeza, manutenção, segurança, pessoal, administração, obras ou outros",
    "despesas.descricao": "O que foi pago",
    "despesas.valor": "Valor pago; precisa ser maior que zero",
    "despesas.data": "Dia do pagamento; é por ele que a despesa entra no balancete do mês. Não pode ser futuro",
    "despesas.fornecedor": "Quem recebeu, quando houver",
    "despesas.comprovante_arquivo": "Nome do arquivo da nota fiscal ou do recibo, gravado pela API sem endereço público",
    "despesas.inativo_em": "Quando a despesa foi cancelada por ter sido lançada errada; ela sai do balancete, e o motivo fica no registro",

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

    "autorizacoes_visita.nome": "Nome de quem pode entrar; é o nome registrado na entrada",
    "autorizacoes_visita.documento": "CPF da pessoa, opcional; quando informado, a portaria só libera quem apresentar o mesmo documento",
    "autorizacoes_visita.tipo": "Diarista, prestador de serviço, familiar, convidado…",
    "autorizacoes_visita.valida_de": "Primeiro dia em que a entrada está liberada; não pode ser passado",
    "autorizacoes_visita.valida_ate": "Último dia em que a entrada está liberada; no máximo um ano depois do primeiro",
    "autorizacoes_visita.dias_semana": "Dias da semana em que vale (1 = segunda … 7 = domingo), como 25 para terça e sexta; vazio = todos os dias do período",
    "autorizacoes_visita.observacao": "Recado do morador para a portaria",
    "autorizacoes_visita.inativo_em": "Quando o morador revogou a autorização; vazio enquanto vale. O registro fica guardado",

    "encomendas.remetente": "Quem enviou, ou a transportadora",
    "encomendas.tipo_volume": "Tipo do volume recebido",
    "encomendas.codigo_rastreio": "Código de rastreio, quando houver",
    "encomendas.observacoes": "Anotações da portaria",
    "encomendas.foto_arquivo": "Nome do arquivo da foto do volume, gravado pela API sem endereço público; apagado após o prazo de guarda",
    "encomendas.status": "Situação da encomenda, do recebimento à retirada",
    "encomendas.recebida_em": "Momento em que a portaria recebeu",
    "encomendas.retirada_em": "Momento da retirada, pelo app ou em mãos na portaria",
    "encomendas.retirado_por_nome": "Nome de quem levou a encomenda entregue em mãos (pode não ter cadastro)",

    "movimentacoes_veiculo.placa": "Placa do veículo",
    "movimentacoes_veiculo.modelo": "Modelo do veículo",
    "movimentacoes_veiculo.cor": "Cor do veículo",
    "movimentacoes_veiculo.tipo": "Se o registro é de entrada ou de saída",
    "movimentacoes_veiculo.categoria": "A quem o veículo pertence",
    "movimentacoes_veiculo.registrada_em": "Momento do registro",
    "movimentacoes_veiculo.observacao": "Anotação da portaria",
    "mudancas.tipo": "Se é a chegada de quem vai morar no apartamento ou a saída de quem vai embora",
    "mudancas.data": "Dia da mudança, dentro do regimento: com antecedência mínima e nunca no domingo",
    "mudancas.hora_inicio": "Início do horário reservado para a mudança",
    "mudancas.hora_fim": "Fim do horário; uma mudança de cada vez em cada bloco",
    "mudancas.empresa": "Empresa que faz a mudança, quando informada",
    "mudancas.observacao": "Recado do morador para o síndico e a portaria",
    "mudancas.status": "Pendente, aprovada, recusada, cancelada ou realizada",
    "mudancas.avaliada_em": "Momento em que o síndico aprovou ou recusou",
    "mudancas.motivo_recusa": "Por que o síndico recusou; o morador recebe",
    "mudancas.cancelada_em": "Momento do cancelamento",
    "mudancas.motivo_cancelamento": "Por que foi cancelada; obrigatório quando é o síndico quem cancela",
    "veiculos_unidade.placa": "Placa do veículo, só letras e números; uma placa ativa por condomínio",
    "veiculos_unidade.modelo": "Modelo do veículo, quando informado",
    "veiculos_unidade.cor": "Cor do veículo, quando informada",
    "veiculos_unidade.inativo_em": "Quando o veículo foi removido do apartamento; vazio enquanto vale. A placa fica livre para outro cadastro",

    "mensagens.texto": "Conteúdo da mensagem, de 1 a 2.000 caracteres",
    "mensagens.enviada_em": "Momento do envio, preenchido pelo banco",
    "mensagens.lida_em": "Momento em que o destinatário abriu a conversa; vazio enquanto não lida",
    "condominios.inativo_em": "Quando o condomínio foi inativado; vazio enquanto ativo. Nada é apagado: \"excluir\" inativa",
    "comunicados.inativo_em": "Quando o comunicado foi removido das telas; vazio enquanto publicado. O registro fica guardado",
    "documentos.inativo_em": "Quando o documento foi removido das telas; vazio enquanto disponível. Registro e arquivo ficam guardados",
    "espacos_comuns.inativo_em": "Quando o espaço foi inativado; vazio enquanto ativo. As reservas passadas ficam no histórico",
    "planos_manutencao.inativo_em": "Quando o plano foi removido; vazio enquanto ativo. O histórico de realizações fica guardado",
    "registros_alteracao.acao": "O que foi feito: criou, editou, inativou, reativou, aprovou, recusou, cancelou ou gerou novo código",
    "registros_alteracao.entidade": "Tipo do registro alterado: condominio, usuario, comunicado, documento, espaco, unidade ou cobranca",
    "registros_alteracao.entidade_id": "Identificador do registro alterado, na tabela indicada em entidade",
    "registros_alteracao.descricao": "O que mudou, quando cabe (\"Alterou o nome e o telefone\"); a senha aparece pelo nome, nunca pelo valor",
    "registros_alteracao.feito_em": "Momento da alteração, preenchido pelo banco",
}

# O que cada vínculo significa, quando o nome da coluna não basta.
VINCULOS = {
    "assembleias.condominio_id": "Condomínio que realiza a assembleia",
    "assembleias.convocada_por_id": "Síndico que convocou",
    "assembleias.inativado_por_id": "Síndico que cancelou",
    "itens_pauta.assembleia_id": "Assembleia a que o item pertence",
    "votos.item_id": "Item da pauta votado",
    "votos.unidade_id": "Apartamento que votou; um voto por apartamento em cada item",
    "votos.usuario_id": "Morador que votou pelo apartamento",
    "despesas.condominio_id": "Condomínio que pagou",
    "despesas.lancada_por_id": "Síndico que lançou a despesa",
    "despesas.inativado_por_id": "Síndico que cancelou a despesa",
    "condominios.sindico_id": "Síndico responsável pelo condomínio",
    "condominios.inativado_por_id": "Administrador que inativou o condomínio",
    "comunicados.inativado_por_id": "Síndico que removeu o comunicado",
    "documentos.inativado_por_id": "Síndico que removeu o documento",
    "espacos_comuns.inativado_por_id": "Síndico que inativou o espaço",
    "registros_alteracao.autor_id": "Quem fez a alteração",
    "usuarios.avaliado_por_id": "Síndico que aprovou ou recusou este cadastro",
    "usuarios.conta_principal_id": "No perfil vinculado, o cadastro com login da mesma pessoa; vazio no cadastro principal. E-mail e CPF são únicos entre os principais",
    "reservas.avaliada_por_id": "Síndico que aprovou ou recusou a reserva",
    "reservas.cancelada_por_id": "Quem cancelou a reserva: o próprio morador ou o síndico",
    "reservas.cobranca_id": "A cobrança da taxa de uso, gerada quando o síndico aprovou; cancelada a reserva antes de paga, a cobrança também é",
    "ocorrencias.aberta_por_id": "Quem registrou a ocorrência",
    "ocorrencias.respondida_por_id": "Síndico que respondeu",
    "ordens_servico.aberta_por_id": "Síndico que abriu a ordem",
    "encomendas.registrada_por_id": "Porteiro que recebeu a encomenda",
    "encomendas.retirada_por_id": "Morador que confirmou a retirada pelo app",
    "encomendas.entregue_por_id": "Porteiro que entregou em mãos na portaria",
    "visitantes.registrado_por_id": "Porteiro que anunciou a visita",
    "visitantes.confirmado_por_id": "Morador que autorizou ou recusou (na entrada pela autorização prévia, quem a deixou)",
    "visitantes.autorizacao_id": "Autorização prévia pela qual a pessoa entrou, sem esperar resposta; vazio no anúncio comum",
    "autorizacoes_visita.unidade_id": "Apartamento para o qual a entrada está liberada",
    "autorizacoes_visita.autorizado_por_id": "Morador que deixou a autorização; ela deixa de valer se ele não morar mais lá",
    "autorizacoes_visita.inativado_por_id": "Morador que revogou a autorização",
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
    "comunicados.unidade_id": "Apartamento de destino, quando o aviso é só para ele (ex.: uma advertência); nunca junto com o bloco",
    "documentos.condominio_id": "Condomínio a que o documento pertence",
    "documentos.unidade_id": "Unidade destinatária, quando o documento não é para todo o condomínio",
    "encomendas.unidade_id": "Unidade destinatária da encomenda",
    "espacos_comuns.condominio_id": "Condomínio a que o espaço pertence",
    "leituras_comunicado.comunicado_id": "Comunicado que foi lido",
    "leituras_comunicado.usuario_id": "Usuário que leu",
    "movimentacoes_veiculo.condominio_id": "Condomínio onde a movimentação ocorreu",
    "movimentacoes_veiculo.unidade_id": "Unidade à qual o veículo está ligado, quando houver",
    "mudancas.condominio_id": "Condomínio da mudança",
    "infracoes.condominio_id": "Condomínio da notificação",
    "planos_manutencao.condominio_id": "Condomínio do plano",
    "planos_manutencao.inativado_por_id": "Quem removeu o plano",
    "realizacoes_manutencao.plano_id": "O plano que foi cumprido",
    "realizacoes_manutencao.registrada_por_id": "Quem registrou a realização",
    "realizacoes_manutencao.despesa_id": "A despesa de manutenção lançada com o custo, na prestação de contas",
    "declaracoes_quitacao.condominio_id": "Condomínio que declara",
    "declaracoes_quitacao.unidade_id": "Apartamento declarado em dia",
    "declaracoes_quitacao.emitida_por_id": "Morador ou síndico que pediu",
    "declaracoes_quitacao.revogada_por_id": "Síndico que revogou",
    "infracoes.unidade_id": "Apartamento notificado",
    "infracoes.aplicada_por_id": "Síndico que notificou",
    "infracoes.defesa_por_id": "Morador que apresentou a defesa",
    "infracoes.decidida_por_id": "Síndico que decidiu",
    "infracoes.cobranca_id": "A cobrança gerada pela multa mantida",
    "horarios_mudanca.condominio_id": "Condomínio cujo regimento define o horário",
    "anotacoes_portaria.condominio_id": "Condomínio do livro",
    "anotacoes_portaria.autor_id": "Porteiro ou síndico que anotou; removido o cadastro, a anotação fica",
    "ciencias_anotacao.anotacao_id": "A anotação lida",
    "ciencias_anotacao.usuario_id": "Quem deu ciência",
    "mudancas.unidade_id": "Apartamento que muda",
    "mudancas.solicitada_por_id": "Morador que pediu a mudança",
    "mudancas.avaliada_por_id": "Síndico que aprovou ou recusou",
    "mudancas.cancelada_por_id": "Quem cancelou: um morador do apartamento ou o síndico",
    "veiculos_unidade.condominio_id": "Condomínio onde o veículo está cadastrado",
    "veiculos_unidade.unidade_id": "Apartamento dono do veículo",
    "veiculos_unidade.cadastrado_por_id": "Morador (ou síndico) que cadastrou a placa",
    "veiculos_unidade.inativado_por_id": "Quem removeu o veículo do apartamento",
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

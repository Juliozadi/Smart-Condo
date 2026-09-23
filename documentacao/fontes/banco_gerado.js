/* GERADO POR diagramas/dicionario.py — não edite à mão.
 * Tipos, obrigatoriedade e chaves vêm do banco em funcionamento;
 * as descrições estão no próprio script que gera este arquivo.
 */
const dicionario = [
  {
    "nome": "cobrancas",
    "resumo": "As cobranças emitidas para cada unidade, por competência.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "unidade_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Unidade cobrada"
      },
      {
        "coluna": "competencia",
        "tipo": "DATE",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Mês a que a cobrança se refere; não pode haver duas cobranças da mesma unidade na mesma competência"
      },
      {
        "coluna": "descricao",
        "tipo": "VARCHAR(180)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "O que está sendo cobrado"
      },
      {
        "coluna": "valor",
        "tipo": "NUMERIC(10,2)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Valor devido; precisa ser maior que zero"
      },
      {
        "coluna": "vencimento",
        "tipo": "DATE",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Data de vencimento"
      },
      {
        "coluna": "status",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Situação da cobrança, que acompanha os pagamentos registrados — tipo enumerado status_cobranca, valores: ABERTA, PAGA, VENCIDA, CANCELADA"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      }
    ],
    "regras": [
      "CHECK ((valor > (0)::numeric))",
      "UNIQUE (unidade_id, competencia)"
    ]
  },
  {
    "nome": "codigos_verificacao",
    "resumo": "Os códigos enviados para confirmar um cadastro ou recuperar uma senha, com prazo de validade e contagem de tentativas.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "usuario_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Usuário a quem o código foi enviado"
      },
      {
        "coluna": "codigo_hash",
        "tipo": "VARCHAR(64)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Resumo criptográfico do código enviado. O código em si não é guardado"
      },
      {
        "coluna": "finalidade",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Para que o código serve: confirmar o cadastro ou recuperar a senha — tipo enumerado finalidade_codigo, valores: CONFIRMACAO_CADASTRO, RECUPERACAO_SENHA"
      },
      {
        "coluna": "canal",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Meio pelo qual o código foi enviado — tipo enumerado canal_verificacao, valores: EMAIL, SMS"
      },
      {
        "coluna": "expira_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento a partir do qual o código deixa de ser aceito"
      },
      {
        "coluna": "consumido_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Momento em que o código foi usado; depois disso ele não vale mais"
      },
      {
        "coluna": "tentativas",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Quantas vezes o código foi informado errado; esgotado o limite, o código é invalidado"
      },
      {
        "coluna": "destino",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Endereço para onde o código foi enviado"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      }
    ],
    "regras": []
  },
  {
    "nome": "comunicados",
    "resumo": "Os avisos publicados pelo síndico para o condomínio.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "condominio_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Condomínio para o qual o aviso foi publicado"
      },
      {
        "coluna": "autor_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Síndico que publicou o comunicado"
      },
      {
        "coluna": "titulo",
        "tipo": "VARCHAR(180)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Título do aviso"
      },
      {
        "coluna": "conteudo",
        "tipo": "TEXT",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Texto do aviso"
      },
      {
        "coluna": "categoria",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Assunto do aviso, usado para filtrar e destacar na tela — tipo enumerado categoria_comunicado, valores: GERAL, MANUTENCAO, FINANCEIRO, SEGURANCA, EVENTO, URGENTE"
      },
      {
        "coluna": "fixado",
        "tipo": "BOOLEAN",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Se o aviso deve permanecer no topo da lista"
      },
      {
        "coluna": "publicado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da publicação; é por ele que a lista é ordenada"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      }
    ],
    "regras": []
  },
  {
    "nome": "condominios",
    "resumo": "Os condomínios atendidos pela plataforma. É o cadastro raiz: tudo o mais pertence, direta ou indiretamente, a um condomínio.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "nome",
        "tipo": "VARCHAR(160)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Razão social ou nome pelo qual o condomínio é conhecido"
      },
      {
        "coluna": "cnpj",
        "tipo": "VARCHAR(18)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "CNPJ do condomínio, conferido pelos dígitos verificadores e único na plataforma"
      },
      {
        "coluna": "cep",
        "tipo": "VARCHAR(9)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "CEP do endereço"
      },
      {
        "coluna": "logradouro",
        "tipo": "VARCHAR(180)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Rua, avenida ou praça"
      },
      {
        "coluna": "numero",
        "tipo": "VARCHAR(20)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Número do imóvel no logradouro"
      },
      {
        "coluna": "complemento",
        "tipo": "VARCHAR(80)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Complemento do endereço, quando houver"
      },
      {
        "coluna": "bairro",
        "tipo": "VARCHAR(100)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Bairro"
      },
      {
        "coluna": "cidade",
        "tipo": "VARCHAR(100)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Cidade"
      },
      {
        "coluna": "uf",
        "tipo": "VARCHAR(2)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Sigla da unidade federativa"
      },
      {
        "coluna": "telefone",
        "tipo": "VARCHAR(20)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Telefone de contato da administração"
      },
      {
        "coluna": "sindico_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico responsável pelo condomínio"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      },
      {
        "coluna": "codigo_acesso",
        "tipo": "VARCHAR(20)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Código que o morador informa para se cadastrar no condomínio certo; pode ser trocado a qualquer momento"
      }
    ],
    "regras": []
  },
  {
    "nome": "documentos",
    "resumo": "Os documentos do condomínio disponibilizados aos moradores: convenção, regimento, atas, plantas e prestações de contas.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "condominio_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Condomínio a que o documento pertence"
      },
      {
        "coluna": "titulo",
        "tipo": "VARCHAR(180)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Título do documento"
      },
      {
        "coluna": "descricao",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Breve explicação do conteúdo"
      },
      {
        "coluna": "categoria",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Tipo do documento — tipo enumerado categoria_documento, valores: CONVENCAO, REGIMENTO, ATA, PLANTA, PRESTACAO_CONTAS, OUTRO"
      },
      {
        "coluna": "arquivo_url",
        "tipo": "VARCHAR(500)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Endereço do arquivo"
      },
      {
        "coluna": "tamanho_kb",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Tamanho do arquivo em kilobytes, exibido antes do download"
      },
      {
        "coluna": "unidade_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Unidade destinatária, quando o documento não é para todo o condomínio"
      },
      {
        "coluna": "publicado_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico que publicou o documento"
      },
      {
        "coluna": "publicado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da publicação"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      }
    ],
    "regras": []
  },
  {
    "nome": "encomendas",
    "resumo": "As encomendas recebidas na portaria e a retirada pelo morador.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "unidade_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Unidade destinatária da encomenda"
      },
      {
        "coluna": "registrada_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Porteiro que recebeu a encomenda"
      },
      {
        "coluna": "remetente",
        "tipo": "VARCHAR(120)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Quem enviou, ou a transportadora"
      },
      {
        "coluna": "tipo_volume",
        "tipo": "VARCHAR(60)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Tipo do volume recebido"
      },
      {
        "coluna": "codigo_rastreio",
        "tipo": "VARCHAR(60)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Código de rastreio, quando houver"
      },
      {
        "coluna": "observacoes",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Anotações da portaria"
      },
      {
        "coluna": "foto_url",
        "tipo": "VARCHAR(500)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Endereço da foto do volume, quando houver"
      },
      {
        "coluna": "status",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Situação da encomenda, do recebimento à retirada — tipo enumerado status_encomenda, valores: AGUARDANDO_RETIRADA, RETIRADA, RECUSADA"
      },
      {
        "coluna": "recebida_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que a portaria recebeu"
      },
      {
        "coluna": "retirada_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Momento em que o morador retirou"
      },
      {
        "coluna": "retirada_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Morador que retirou"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      }
    ],
    "regras": []
  },
  {
    "nome": "espacos_comuns",
    "resumo": "As áreas comuns do condomínio: salão de festas, churrasqueira, academia, piscina.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "condominio_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Condomínio a que o espaço pertence"
      },
      {
        "coluna": "nome",
        "tipo": "VARCHAR(120)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Nome do espaço"
      },
      {
        "coluna": "descricao",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Descrição e regras de uso"
      },
      {
        "coluna": "capacidade",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Quantas pessoas o espaço comporta"
      },
      {
        "coluna": "reservavel",
        "tipo": "BOOLEAN",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Se o espaço precisa ser reservado antes do uso"
      },
      {
        "coluna": "uso_livre",
        "tipo": "BOOLEAN",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Se o espaço pode ser usado sem reserva; nesse caso a ocupação é acompanhada pela contagem da portaria"
      },
      {
        "coluna": "em_manutencao",
        "tipo": "BOOLEAN",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Se o espaço está temporariamente indisponível"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      }
    ],
    "regras": []
  },
  {
    "nome": "leituras_comunicado",
    "resumo": "Quem leu qual comunicado, para que o síndico saiba o alcance do aviso.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "comunicado_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Comunicado que foi lido"
      },
      {
        "coluna": "usuario_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Usuário que leu"
      },
      {
        "coluna": "lido_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o usuário abriu o comunicado"
      }
    ],
    "regras": [
      "UNIQUE (comunicado_id, usuario_id)"
    ]
  },
  {
    "nome": "mensagens",
    "resumo": "As mensagens do chat entre síndico, porteiros e moradores do mesmo condomínio.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "condominio_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Condomínio onde a conversa acontece"
      },
      {
        "coluna": "remetente_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Quem enviou a mensagem"
      },
      {
        "coluna": "destinatario_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Quem recebe a mensagem; não pode ser o próprio remetente"
      },
      {
        "coluna": "texto",
        "tipo": "TEXT",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Conteúdo da mensagem, de 1 a 2.000 caracteres"
      },
      {
        "coluna": "enviada_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento do envio, preenchido pelo banco"
      },
      {
        "coluna": "lida_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Momento em que o destinatário abriu a conversa; vazio enquanto não lida"
      }
    ],
    "regras": [
      "CHECK ((remetente_id <> destinatario_id))",
      "CHECK (((char_length(texto) >= 1) AND (char_length(texto) <= 2000)))"
    ]
  },
  {
    "nome": "movimentacoes_veiculo",
    "resumo": "As entradas e saídas de veículos registradas na portaria.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "condominio_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Condomínio onde a movimentação ocorreu"
      },
      {
        "coluna": "placa",
        "tipo": "VARCHAR(10)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Placa do veículo"
      },
      {
        "coluna": "modelo",
        "tipo": "VARCHAR(60)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Modelo do veículo"
      },
      {
        "coluna": "cor",
        "tipo": "VARCHAR(30)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Cor do veículo"
      },
      {
        "coluna": "tipo",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Se o registro é de entrada ou de saída — tipo enumerado tipo_movimentacao, valores: ENTRADA, SAIDA"
      },
      {
        "coluna": "categoria",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "A quem o veículo pertence — tipo enumerado categoria_veiculo, valores: MORADOR, VISITANTE, PRESTADOR"
      },
      {
        "coluna": "unidade_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Unidade à qual o veículo está ligado, quando houver"
      },
      {
        "coluna": "registrada_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Porteiro que registrou a movimentação"
      },
      {
        "coluna": "registrada_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento do registro"
      },
      {
        "coluna": "observacao",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Anotação da portaria"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      }
    ],
    "regras": []
  },
  {
    "nome": "ocorrencias",
    "resumo": "Os problemas e reclamações registrados por moradores e porteiros, e a resposta do síndico.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "condominio_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Condomínio onde o problema ocorreu"
      },
      {
        "coluna": "aberta_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Quem registrou a ocorrência"
      },
      {
        "coluna": "unidade_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Unidade envolvida, quando a ocorrência não é de área comum"
      },
      {
        "coluna": "titulo",
        "tipo": "VARCHAR(180)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Resumo do problema"
      },
      {
        "coluna": "descricao",
        "tipo": "TEXT",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Relato completo"
      },
      {
        "coluna": "categoria",
        "tipo": "VARCHAR(60)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Assunto da ocorrência"
      },
      {
        "coluna": "foto_url",
        "tipo": "VARCHAR(500)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Endereço da foto anexada, quando houver"
      },
      {
        "coluna": "status",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Situação do atendimento, da abertura ao arquivamento — tipo enumerado status_ocorrencia, valores: ABERTA, EM_ANALISE, RESOLVIDA, ARQUIVADA"
      },
      {
        "coluna": "resposta",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Resposta do síndico a quem abriu a ocorrência"
      },
      {
        "coluna": "respondida_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico que respondeu"
      },
      {
        "coluna": "respondida_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Momento da resposta"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      },
      {
        "coluna": "local",
        "tipo": "VARCHAR(120)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Onde o problema foi observado"
      },
      {
        "coluna": "prioridade",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Urgência atribuída no registro — tipo enumerado prioridade_ocorrencia, valores: BAIXA, NORMAL, ALTA, URGENTE"
      }
    ],
    "regras": []
  },
  {
    "nome": "ordens_servico",
    "resumo": "As ordens de serviço de manutenção abertas pelo síndico, com prioridade, custo e acompanhamento.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "condominio_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Condomínio onde o serviço será executado"
      },
      {
        "coluna": "tipo",
        "tipo": "VARCHAR(60)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Natureza do serviço a executar"
      },
      {
        "coluna": "descricao",
        "tipo": "TEXT",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "O que precisa ser feito"
      },
      {
        "coluna": "local",
        "tipo": "VARCHAR(120)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Onde o serviço será executado"
      },
      {
        "coluna": "prioridade",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Urgência do serviço — tipo enumerado prioridade_ordem_servico, valores: BAIXA, MEDIA, ALTA, URGENTE"
      },
      {
        "coluna": "status",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Andamento da ordem, da abertura à conclusão ou ao cancelamento — tipo enumerado status_ordem_servico, valores: ABERTA, EM_ANDAMENTO, CONCLUIDA, CANCELADA"
      },
      {
        "coluna": "fornecedor",
        "tipo": "VARCHAR(120)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Empresa ou profissional responsável"
      },
      {
        "coluna": "data_prevista",
        "tipo": "DATE",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Data prevista para a execução"
      },
      {
        "coluna": "custo_estimado",
        "tipo": "NUMERIC(10,2)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Valor orçado; quando informado, não pode ser negativo"
      },
      {
        "coluna": "custo_real",
        "tipo": "NUMERIC(10,2)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Valor efetivamente gasto; quando informado, não pode ser negativo"
      },
      {
        "coluna": "aberta_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico que abriu a ordem"
      },
      {
        "coluna": "concluida_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Momento da conclusão"
      },
      {
        "coluna": "observacoes",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Anotações de acompanhamento"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      }
    ],
    "regras": [
      "CHECK (((custo_estimado IS NULL) OR (custo_estimado >= (0)::numeric)))",
      "CHECK (((custo_real IS NULL) OR (custo_real >= (0)::numeric)))"
    ]
  },
  {
    "nome": "pagamentos",
    "resumo": "Os pagamentos registrados para cada cobrança. Uma cobrança pode receber mais de um pagamento.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "cobranca_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Cobrança que está sendo paga"
      },
      {
        "coluna": "pago_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Quem registrou o pagamento"
      },
      {
        "coluna": "valor",
        "tipo": "NUMERIC(10,2)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Valor pago; precisa ser maior que zero"
      },
      {
        "coluna": "forma",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Forma utilizada no pagamento — tipo enumerado forma_pagamento, valores: PIX, BOLETO, DEBITO_AUTOMATICO, CARTAO"
      },
      {
        "coluna": "pago_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento do pagamento"
      },
      {
        "coluna": "comprovante_url",
        "tipo": "VARCHAR(500)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Endereço do comprovante, quando houver"
      },
      {
        "coluna": "observacao",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Anotação sobre o pagamento"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      }
    ],
    "regras": [
      "CHECK ((valor > (0)::numeric))"
    ]
  },
  {
    "nome": "permissoes_porteiro",
    "resumo": "O que cada porteiro pode fazer no sistema, definido pelo síndico porteiro a porteiro.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "porteiro_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Porteiro a quem as permissões pertencem"
      },
      {
        "coluna": "registrar_visitantes",
        "tipo": "BOOLEAN",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Se o porteiro pode anunciar visitantes"
      },
      {
        "coluna": "registrar_encomendas",
        "tipo": "BOOLEAN",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Se o porteiro pode registrar encomendas"
      },
      {
        "coluna": "registrar_veiculos",
        "tipo": "BOOLEAN",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Se o porteiro pode registrar entrada e saída de veículos"
      },
      {
        "coluna": "registrar_ocorrencias",
        "tipo": "BOOLEAN",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Se o porteiro pode abrir ocorrências"
      },
      {
        "coluna": "acessar_financeiro",
        "tipo": "BOOLEAN",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Se o porteiro pode consultar a área financeira"
      },
      {
        "coluna": "definidas_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico que definiu as permissões"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      }
    ],
    "regras": []
  },
  {
    "nome": "preferencias_cobranca",
    "resumo": "O dia do mês e a forma de pagamento que cada morador prefere.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "morador_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Morador dono da preferência"
      },
      {
        "coluna": "dia_vencimento",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Dia do mês escolhido pelo morador; limitado a 28 para existir em todos os meses"
      },
      {
        "coluna": "forma_preferida",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Forma de pagamento preferida — tipo enumerado forma_pagamento, valores: PIX, BOLETO, DEBITO_AUTOMATICO, CARTAO"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      }
    ],
    "regras": [
      "CHECK (((dia_vencimento >= 1) AND (dia_vencimento <= 28)))"
    ]
  },
  {
    "nome": "registros_ocupacao",
    "resumo": "A contagem de pessoas nas áreas de uso livre, registrada pela portaria, para que o morador saiba se o espaço está cheio.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "espaco_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Espaço em que a contagem foi feita"
      },
      {
        "coluna": "pessoas",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Quantas pessoas estavam no espaço no momento da contagem; não pode ser negativo"
      },
      {
        "coluna": "registrado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da contagem"
      },
      {
        "coluna": "registrado_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Porteiro que fez a contagem"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      }
    ],
    "regras": [
      "CHECK ((pessoas >= 0))"
    ]
  },
  {
    "nome": "reservas",
    "resumo": "As reservas de espaços feitas pelos moradores, com a avaliação do síndico quando o espaço exige aprovação.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "espaco_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Espaço reservado"
      },
      {
        "coluna": "morador_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Morador que solicitou a reserva"
      },
      {
        "coluna": "data",
        "tipo": "DATE",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Dia da reserva"
      },
      {
        "coluna": "hora_inicio",
        "tipo": "TIME",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Hora de início"
      },
      {
        "coluna": "hora_fim",
        "tipo": "TIME",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Hora de término; precisa ser posterior à de início"
      },
      {
        "coluna": "pessoas_estimadas",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Quantas pessoas o morador espera receber"
      },
      {
        "coluna": "observacoes",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Observações do morador ao solicitar"
      },
      {
        "coluna": "status",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Situação da reserva, da solicitação até a conclusão ou o cancelamento — tipo enumerado status_reserva, valores: PENDENTE, APROVADA, RECUSADA, CANCELADA, CONCLUIDA"
      },
      {
        "coluna": "avaliada_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico que aprovou ou recusou a reserva"
      },
      {
        "coluna": "avaliada_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Data e hora em que o síndico aprovou ou recusou"
      },
      {
        "coluna": "motivo_recusa",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Justificativa registrada pelo síndico ao recusar"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      }
    ],
    "regras": [
      "CHECK ((hora_fim > hora_inicio))"
    ]
  },
  {
    "nome": "unidades",
    "resumo": "Os apartamentos ou casas de cada condomínio. A unidade é o que liga o morador às cobranças, encomendas, visitantes e ocorrências.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "condominio_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Condomínio a que a unidade pertence"
      },
      {
        "coluna": "numero",
        "tipo": "VARCHAR(20)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Número do apartamento ou da casa"
      },
      {
        "coluna": "bloco",
        "tipo": "VARCHAR(20)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Bloco ou torre, quando o condomínio tiver mais de um"
      },
      {
        "coluna": "andar",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Andar em que a unidade fica"
      },
      {
        "coluna": "vagas_garagem",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Quantidade de vagas de garagem da unidade; a soma das vagas alimenta o cálculo de ocupação do estacionamento"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      }
    ],
    "regras": [
      "UNIQUE (condominio_id, bloco, numero)"
    ]
  },
  {
    "nome": "usuarios",
    "resumo": "Todas as pessoas que acessam o sistema, em qualquer papel: administrador, síndico, porteiro e morador.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "nome",
        "tipo": "VARCHAR(160)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Nome completo"
      },
      {
        "coluna": "email",
        "tipo": "VARCHAR(180)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "E-mail, usado para entrar no sistema e para receber os códigos; único na plataforma"
      },
      {
        "coluna": "cpf",
        "tipo": "VARCHAR(14)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "CPF, conferido pelos dígitos verificadores e único na plataforma"
      },
      {
        "coluna": "telefone",
        "tipo": "VARCHAR(20)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Telefone de contato"
      },
      {
        "coluna": "data_nascimento",
        "tipo": "DATE",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Data de nascimento"
      },
      {
        "coluna": "senha_hash",
        "tipo": "VARCHAR(120)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Resumo criptográfico da senha. A senha em si não é guardada em lugar nenhum"
      },
      {
        "coluna": "papel",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Papel do usuário, que determina o que ele enxerga e pode fazer — tipo enumerado papel_usuario, valores: SINDICO, PORTEIRO, MORADOR, ADMIN"
      },
      {
        "coluna": "status",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Situação do cadastro ao longo do fluxo de entrada, da confirmação do código até a liberação do acesso — tipo enumerado status_usuario, valores: AGUARDANDO_CODIGO, AGUARDANDO_APROVACAO, ATIVO, RECUSADO, INATIVO"
      },
      {
        "coluna": "condominio_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Condomínio em que o usuário atua; vazio apenas para o administrador da plataforma"
      },
      {
        "coluna": "unidade_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Unidade em que o morador vive; vazio para síndico, porteiro e administrador"
      },
      {
        "coluna": "tipo_ocupacao",
        "tipo": "ENUM",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Relação do morador com a unidade: proprietário, inquilino ou coabitante — tipo enumerado tipo_ocupacao, valores: PROPRIETARIO, INQUILINO, COABITANTE"
      },
      {
        "coluna": "foto_url",
        "tipo": "VARCHAR(500)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Endereço da foto de perfil, quando houver"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      },
      {
        "coluna": "avaliado_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico que aprovou ou recusou este cadastro"
      },
      {
        "coluna": "avaliado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Data e hora em que o síndico aprovou ou recusou o cadastro"
      },
      {
        "coluna": "motivo_recusa",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Justificativa registrada pelo síndico ao recusar o cadastro; é o que o morador vê na tela de espera"
      },
      {
        "coluna": "tentativas_login",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Senhas erradas seguidas; zera no primeiro acesso bem-sucedido"
      },
      {
        "coluna": "bloqueado_ate",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Momento até o qual a conta fica bloqueada depois de sucessivas senhas erradas"
      }
    ],
    "regras": []
  },
  {
    "nome": "visitantes",
    "resumo": "Os visitantes anunciados pela portaria e a confirmação do morador.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "unidade_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Unidade visitada"
      },
      {
        "coluna": "registrado_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Porteiro que anunciou a visita"
      },
      {
        "coluna": "nome",
        "tipo": "VARCHAR(160)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Nome do visitante"
      },
      {
        "coluna": "documento",
        "tipo": "VARCHAR(20)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Documento apresentado na portaria"
      },
      {
        "coluna": "tipo_visita",
        "tipo": "VARCHAR(60)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Natureza da visita"
      },
      {
        "coluna": "placa_veiculo",
        "tipo": "VARCHAR(10)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Placa do veículo, quando o visitante chega de carro"
      },
      {
        "coluna": "foto_url",
        "tipo": "VARCHAR(500)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Endereço da foto tirada na portaria, quando houver"
      },
      {
        "coluna": "status",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Situação da visita, do anúncio à saída — tipo enumerado status_visitante, valores: AGUARDANDO_CONFIRMACAO, CONFIRMADO, RECUSADO, DENTRO, SAIU"
      },
      {
        "coluna": "entrada_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Momento da entrada"
      },
      {
        "coluna": "saida_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Momento da saída"
      },
      {
        "coluna": "confirmado_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Morador que autorizou ou recusou"
      },
      {
        "coluna": "confirmado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Momento em que o morador autorizou ou recusou"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      },
      {
        "coluna": "atualizado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da última alteração do registro"
      }
    ],
    "regras": []
  }
];

const relacoes = [
  {
    "origem": "cobrancas",
    "coluna": "unidade_id",
    "destino": "unidades",
    "texto": "Unidade cobrada"
  },
  {
    "origem": "codigos_verificacao",
    "coluna": "usuario_id",
    "destino": "usuarios",
    "texto": "Usuário a quem o código foi enviado"
  },
  {
    "origem": "comunicados",
    "coluna": "autor_id",
    "destino": "usuarios",
    "texto": "Síndico que publicou o comunicado"
  },
  {
    "origem": "comunicados",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio para o qual o aviso foi publicado"
  },
  {
    "origem": "condominios",
    "coluna": "sindico_id",
    "destino": "usuarios",
    "texto": "Síndico responsável pelo condomínio"
  },
  {
    "origem": "documentos",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio a que o documento pertence"
  },
  {
    "origem": "documentos",
    "coluna": "publicado_por_id",
    "destino": "usuarios",
    "texto": "Síndico que publicou o documento"
  },
  {
    "origem": "documentos",
    "coluna": "unidade_id",
    "destino": "unidades",
    "texto": "Unidade destinatária, quando o documento não é para todo o condomínio"
  },
  {
    "origem": "encomendas",
    "coluna": "registrada_por_id",
    "destino": "usuarios",
    "texto": "Porteiro que recebeu a encomenda"
  },
  {
    "origem": "encomendas",
    "coluna": "retirada_por_id",
    "destino": "usuarios",
    "texto": "Morador que retirou"
  },
  {
    "origem": "encomendas",
    "coluna": "unidade_id",
    "destino": "unidades",
    "texto": "Unidade destinatária da encomenda"
  },
  {
    "origem": "espacos_comuns",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio a que o espaço pertence"
  },
  {
    "origem": "leituras_comunicado",
    "coluna": "comunicado_id",
    "destino": "comunicados",
    "texto": "Comunicado que foi lido"
  },
  {
    "origem": "leituras_comunicado",
    "coluna": "usuario_id",
    "destino": "usuarios",
    "texto": "Usuário que leu"
  },
  {
    "origem": "mensagens",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio onde a conversa acontece"
  },
  {
    "origem": "mensagens",
    "coluna": "destinatario_id",
    "destino": "usuarios",
    "texto": "Quem recebe a mensagem; não pode ser o próprio remetente"
  },
  {
    "origem": "mensagens",
    "coluna": "remetente_id",
    "destino": "usuarios",
    "texto": "Quem enviou a mensagem"
  },
  {
    "origem": "movimentacoes_veiculo",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio onde a movimentação ocorreu"
  },
  {
    "origem": "movimentacoes_veiculo",
    "coluna": "registrada_por_id",
    "destino": "usuarios",
    "texto": "Porteiro que registrou a movimentação"
  },
  {
    "origem": "movimentacoes_veiculo",
    "coluna": "unidade_id",
    "destino": "unidades",
    "texto": "Unidade à qual o veículo está ligado, quando houver"
  },
  {
    "origem": "ocorrencias",
    "coluna": "aberta_por_id",
    "destino": "usuarios",
    "texto": "Quem registrou a ocorrência"
  },
  {
    "origem": "ocorrencias",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio onde o problema ocorreu"
  },
  {
    "origem": "ocorrencias",
    "coluna": "respondida_por_id",
    "destino": "usuarios",
    "texto": "Síndico que respondeu"
  },
  {
    "origem": "ocorrencias",
    "coluna": "unidade_id",
    "destino": "unidades",
    "texto": "Unidade envolvida, quando a ocorrência não é de área comum"
  },
  {
    "origem": "ordens_servico",
    "coluna": "aberta_por_id",
    "destino": "usuarios",
    "texto": "Síndico que abriu a ordem"
  },
  {
    "origem": "ordens_servico",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio onde o serviço será executado"
  },
  {
    "origem": "pagamentos",
    "coluna": "cobranca_id",
    "destino": "cobrancas",
    "texto": "Cobrança que está sendo paga"
  },
  {
    "origem": "pagamentos",
    "coluna": "pago_por_id",
    "destino": "usuarios",
    "texto": "Quem registrou o pagamento"
  },
  {
    "origem": "permissoes_porteiro",
    "coluna": "definidas_por_id",
    "destino": "usuarios",
    "texto": "Síndico que definiu as permissões"
  },
  {
    "origem": "permissoes_porteiro",
    "coluna": "porteiro_id",
    "destino": "usuarios",
    "texto": "Porteiro a quem as permissões pertencem"
  },
  {
    "origem": "preferencias_cobranca",
    "coluna": "morador_id",
    "destino": "usuarios",
    "texto": "Morador dono da preferência"
  },
  {
    "origem": "registros_ocupacao",
    "coluna": "espaco_id",
    "destino": "espacos_comuns",
    "texto": "Espaço em que a contagem foi feita"
  },
  {
    "origem": "registros_ocupacao",
    "coluna": "registrado_por_id",
    "destino": "usuarios",
    "texto": "Porteiro que fez a contagem"
  },
  {
    "origem": "reservas",
    "coluna": "avaliada_por_id",
    "destino": "usuarios",
    "texto": "Síndico que aprovou ou recusou a reserva"
  },
  {
    "origem": "reservas",
    "coluna": "espaco_id",
    "destino": "espacos_comuns",
    "texto": "Espaço reservado"
  },
  {
    "origem": "reservas",
    "coluna": "morador_id",
    "destino": "usuarios",
    "texto": "Morador que solicitou a reserva"
  },
  {
    "origem": "unidades",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio a que a unidade pertence"
  },
  {
    "origem": "usuarios",
    "coluna": "avaliado_por_id",
    "destino": "usuarios",
    "texto": "Síndico que aprovou ou recusou este cadastro"
  },
  {
    "origem": "usuarios",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio em que o usuário atua; vazio apenas para o administrador da plataforma"
  },
  {
    "origem": "usuarios",
    "coluna": "unidade_id",
    "destino": "unidades",
    "texto": "Unidade em que o morador vive; vazio para síndico, porteiro e administrador"
  },
  {
    "origem": "visitantes",
    "coluna": "confirmado_por_id",
    "destino": "usuarios",
    "texto": "Morador que autorizou ou recusou"
  },
  {
    "origem": "visitantes",
    "coluna": "registrado_por_id",
    "destino": "usuarios",
    "texto": "Porteiro que anunciou a visita"
  },
  {
    "origem": "visitantes",
    "coluna": "unidade_id",
    "destino": "unidades",
    "texto": "Unidade visitada"
  }
];

const enumerados = [
  {
    "nome": "canal_verificacao",
    "valores": "EMAIL, SMS"
  },
  {
    "nome": "categoria_comunicado",
    "valores": "GERAL, MANUTENCAO, FINANCEIRO, SEGURANCA, EVENTO, URGENTE"
  },
  {
    "nome": "categoria_documento",
    "valores": "CONVENCAO, REGIMENTO, ATA, PLANTA, PRESTACAO_CONTAS, OUTRO"
  },
  {
    "nome": "categoria_veiculo",
    "valores": "MORADOR, VISITANTE, PRESTADOR"
  },
  {
    "nome": "finalidade_codigo",
    "valores": "CONFIRMACAO_CADASTRO, RECUPERACAO_SENHA"
  },
  {
    "nome": "forma_pagamento",
    "valores": "PIX, BOLETO, DEBITO_AUTOMATICO, CARTAO"
  },
  {
    "nome": "papel_usuario",
    "valores": "SINDICO, PORTEIRO, MORADOR, ADMIN"
  },
  {
    "nome": "prioridade_ocorrencia",
    "valores": "BAIXA, NORMAL, ALTA, URGENTE"
  },
  {
    "nome": "prioridade_ordem_servico",
    "valores": "BAIXA, MEDIA, ALTA, URGENTE"
  },
  {
    "nome": "status_cobranca",
    "valores": "ABERTA, PAGA, VENCIDA, CANCELADA"
  },
  {
    "nome": "status_encomenda",
    "valores": "AGUARDANDO_RETIRADA, RETIRADA, RECUSADA"
  },
  {
    "nome": "status_ocorrencia",
    "valores": "ABERTA, EM_ANALISE, RESOLVIDA, ARQUIVADA"
  },
  {
    "nome": "status_ordem_servico",
    "valores": "ABERTA, EM_ANDAMENTO, CONCLUIDA, CANCELADA"
  },
  {
    "nome": "status_reserva",
    "valores": "PENDENTE, APROVADA, RECUSADA, CANCELADA, CONCLUIDA"
  },
  {
    "nome": "status_usuario",
    "valores": "AGUARDANDO_CODIGO, AGUARDANDO_APROVACAO, ATIVO, RECUSADO, INATIVO"
  },
  {
    "nome": "status_visitante",
    "valores": "AGUARDANDO_CONFIRMACAO, CONFIRMADO, RECUSADO, DENTRO, SAIU"
  },
  {
    "nome": "tipo_movimentacao",
    "valores": "ENTRADA, SAIDA"
  },
  {
    "nome": "tipo_ocupacao",
    "valores": "PROPRIETARIO, INQUILINO, COABITANTE"
  }
];

module.exports = { dicionario, relacoes, enumerados };

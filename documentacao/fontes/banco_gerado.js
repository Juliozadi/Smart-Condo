/* GERADO POR diagramas/dicionario.py — não edite à mão.
 * Tipos, obrigatoriedade e chaves vêm do banco em funcionamento;
 * as descrições estão no próprio script que gera este arquivo.
 */
const dicionario = [
  {
    "nome": "anotacoes_portaria",
    "resumo": "O livro da portaria: o que o porteiro que sai, ou o síndico, anota para o próximo turno. Não se apaga nem se edita — corrige-se com outra anotação.",
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
        "descricao": "Condomínio do livro"
      },
      {
        "coluna": "autor_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Porteiro ou síndico que anotou; removido o cadastro, a anotação fica"
      },
      {
        "coluna": "texto",
        "tipo": "TEXT",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "A anotação, como o autor escreveu (de 3 a 2.000 caracteres)"
      },
      {
        "coluna": "importante",
        "tipo": "BOOLEAN",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Importante: quem chegar precisa ler e dar ciência"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      }
    ],
    "regras": []
  },
  {
    "nome": "assembleias",
    "resumo": "As assembleias virtuais convocadas pelo síndico (Código Civil, art. 1.354-A): o período de votação e, se cancelada, o motivo.",
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
        "descricao": "Condomínio que realiza a assembleia"
      },
      {
        "coluna": "convocada_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico que convocou"
      },
      {
        "coluna": "titulo",
        "tipo": "VARCHAR(180)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Nome da assembleia"
      },
      {
        "coluna": "descricao",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Texto da convocação"
      },
      {
        "coluna": "abre_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que a votação abre; antes disso, só a convocação"
      },
      {
        "coluna": "encerra_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que a votação encerra; depois dele aparece o resultado. No máximo 30 dias depois da abertura"
      },
      {
        "coluna": "motivo_cancelamento",
        "tipo": "VARCHAR(300)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Por que o síndico cancelou a assembleia; os moradores recebem"
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
        "coluna": "inativo_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Quando a assembleia foi cancelada; vazio enquanto vale"
      },
      {
        "coluna": "inativado_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico que cancelou"
      }
    ],
    "regras": [
      "CHECK ((encerra_em > abre_em))"
    ]
  },
  {
    "nome": "autorizacoes_visita",
    "resumo": "As entradas liberadas pelo morador antes de o visitante chegar — a diarista, o prestador da reforma, os convidados da festa —, que a portaria registra sem esperar a resposta dele.",
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
        "descricao": "Apartamento para o qual a entrada está liberada"
      },
      {
        "coluna": "autorizado_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Morador que deixou a autorização; ela deixa de valer se ele não morar mais lá"
      },
      {
        "coluna": "nome",
        "tipo": "VARCHAR(160)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Nome de quem pode entrar; é o nome registrado na entrada"
      },
      {
        "coluna": "documento",
        "tipo": "VARCHAR(20)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "CPF da pessoa, opcional; quando informado, a portaria só libera quem apresentar o mesmo documento"
      },
      {
        "coluna": "tipo",
        "tipo": "VARCHAR(60)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Diarista, prestador de serviço, familiar, convidado…"
      },
      {
        "coluna": "valida_de",
        "tipo": "DATE",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Primeiro dia em que a entrada está liberada; não pode ser passado"
      },
      {
        "coluna": "valida_ate",
        "tipo": "DATE",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Último dia em que a entrada está liberada; no máximo um ano depois do primeiro"
      },
      {
        "coluna": "dias_semana",
        "tipo": "VARCHAR(7)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Dias da semana em que vale (1 = segunda … 7 = domingo), como 25 para terça e sexta; vazio = todos os dias do período"
      },
      {
        "coluna": "observacao",
        "tipo": "VARCHAR(300)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Recado do morador para a portaria"
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
        "coluna": "inativo_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Quando o morador revogou a autorização; vazio enquanto vale. O registro fica guardado"
      },
      {
        "coluna": "inativado_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Morador que revogou a autorização"
      },
      {
        "coluna": "pode_retirar_chave",
        "tipo": "BOOLEAN",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Se a pessoa pode levar a chave do apartamento deixada na portaria; exige o CPF, que a portaria confere"
      }
    ],
    "regras": [
      "CHECK ((valida_ate >= valida_de))"
    ]
  },
  {
    "nome": "chaves",
    "resumo": "O quadro de chaves da portaria: as das áreas comuns e as dos apartamentos que os moradores deixam, que só saem para quem mora lá ou para quem o morador autorizou. Remover é inativar.",
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
        "descricao": "Condomínio da portaria que guarda a chave"
      },
      {
        "coluna": "unidade_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Apartamento dono da chave; vazio, chave de área comum"
      },
      {
        "coluna": "nome",
        "tipo": "VARCHAR(80)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Como a portaria chama a chave; único entre as chaves do quadro"
      },
      {
        "coluna": "posicao",
        "tipo": "VARCHAR(20)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Onde fica no quadro de chaves, como A3"
      },
      {
        "coluna": "observacao",
        "tipo": "VARCHAR(300)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Recado sobre a chave (para quem ela sai, de onde é)"
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
        "coluna": "inativo_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Quando a chave saiu do quadro; vazio enquanto está nele. O histórico fica guardado"
      },
      {
        "coluna": "inativado_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Quem tirou a chave do quadro"
      }
    ],
    "regras": []
  },
  {
    "nome": "ciencias_anotacao",
    "resumo": "Quem leu cada anotação importante do livro da portaria, e quando — uma vez por pessoa.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "anotacao_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "A anotação lida"
      },
      {
        "coluna": "usuario_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Quem deu ciência"
      },
      {
        "coluna": "ciente_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que a pessoa deu ciência"
      }
    ],
    "regras": [
      "UNIQUE (anotacao_id, usuario_id)"
    ]
  },
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
      },
      {
        "coluna": "origem",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "De onde vem a cobrança: a taxa do mês (uma por apartamento e mês), uma multa ou o uso de um espaço — tipo enumerado origem_cobranca, valores: TAXA, MULTA, USO_ESPACO"
      }
    ],
    "regras": [
      "CHECK ((valor > (0)::numeric))"
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
      },
      {
        "coluna": "inativo_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Quando o comunicado foi removido das telas; vazio enquanto publicado. O registro fica guardado"
      },
      {
        "coluna": "inativado_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico que removeu o comunicado"
      },
      {
        "coluna": "bloco",
        "tipo": "VARCHAR(20)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Bloco de destino, quando o aviso é só para ele (ex.: falta de água no bloco B); vazio com a unidade vazia = todo o condomínio"
      },
      {
        "coluna": "unidade_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Apartamento de destino, quando o aviso é só para ele (ex.: uma advertência); nunca junto com o bloco"
      }
    ],
    "regras": [
      "CHECK (((bloco IS NULL) OR (unidade_id IS NULL)))"
    ]
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
        "descricao": "Complemento do endereço dos cadastros antigos; não é mais pedido"
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
      },
      {
        "coluna": "inativo_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Quando o condomínio foi inativado; vazio enquanto ativo. Nada é apagado: \"excluir\" inativa"
      },
      {
        "coluna": "inativado_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Administrador que inativou o condomínio"
      },
      {
        "coluna": "multa_atraso",
        "tipo": "NUMERIC(4,2)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Multa, em %, da cobrança paga depois do vencimento; de 0 a 2 (Código Civil, art. 1.336, § 1º)"
      },
      {
        "coluna": "juros_mensais",
        "tipo": "NUMERIC(4,2)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Juros ao mês, em %, contados por dia de atraso; de 0 a 1 (Código Civil, art. 1.336, § 1º)"
      },
      {
        "coluna": "mudanca_antecedencia_dias",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Com quantos dias de aviso o morador agenda a mudança, pelo regimento; de 0 a 60"
      }
    ],
    "regras": [
      "CHECK (((juros_mensais >= (0)::numeric) AND (juros_mensais <= (1)::numeric)))",
      "CHECK (((mudanca_antecedencia_dias >= 0) AND (mudanca_antecedencia_dias <= 60)))",
      "CHECK (((multa_atraso >= (0)::numeric) AND (multa_atraso <= (2)::numeric)))"
    ]
  },
  {
    "nome": "declaracoes_quitacao",
    "resumo": "As declarações de que o apartamento não tinha débito vencido, com o código que qualquer um confere e o que diziam no dia em que foram emitidas. Não se apagam; o síndico revoga com motivo.",
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
        "descricao": "Condomínio que declara"
      },
      {
        "coluna": "unidade_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Apartamento declarado em dia"
      },
      {
        "coluna": "emitida_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Morador ou síndico que pediu"
      },
      {
        "coluna": "codigo",
        "tipo": "VARCHAR(16)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Código de verificação, 16 letras e números sorteados (sem 0, O, 1 e I); único"
      },
      {
        "coluna": "referencia_ate",
        "tipo": "DATE",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Dia até o qual o apartamento não tinha cobrança vencida em aberto (o da emissão)"
      },
      {
        "coluna": "valida_ate",
        "tipo": "DATE",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Até quando quem recebe pode confiar na declaração (30 dias)"
      },
      {
        "coluna": "condominio_nome",
        "tipo": "VARCHAR(160)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Nome do condomínio no dia da emissão, como está na declaração"
      },
      {
        "coluna": "condominio_cnpj",
        "tipo": "VARCHAR(18)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "CNPJ do condomínio no dia da emissão"
      },
      {
        "coluna": "identificacao_unidade",
        "tipo": "VARCHAR(45)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "O apartamento (e o bloco), como está na declaração"
      },
      {
        "coluna": "sindico_nome",
        "tipo": "VARCHAR(160)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "O síndico no dia da emissão"
      },
      {
        "coluna": "emitida_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da emissão"
      },
      {
        "coluna": "revogada_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Quando o síndico revogou; vazia, a declaração não foi revogada"
      },
      {
        "coluna": "revogada_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico que revogou"
      },
      {
        "coluna": "motivo_revogacao",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Por que foi revogada; o apartamento recebe, quem confere o código não vê"
      }
    ],
    "regras": [
      "CHECK (((revogada_em IS NULL) = (motivo_revogacao IS NULL)))",
      "CHECK ((valida_ate >= referencia_ate))",
      "UNIQUE (codigo)"
    ]
  },
  {
    "nome": "despesas",
    "resumo": "O que o condomínio gastou, com o comprovante: a outra metade da prestação de contas, que os moradores veem no balancete do mês.",
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
        "descricao": "Condomínio que pagou"
      },
      {
        "coluna": "lancada_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico que lançou a despesa"
      },
      {
        "coluna": "categoria",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Para onde foi o dinheiro: água, energia, limpeza, manutenção, segurança, pessoal, administração, obras ou outros — tipo enumerado categoria_despesa, valores: AGUA, ENERGIA, LIMPEZA, MANUTENCAO, SEGURANCA, PESSOAL, ADMINISTRACAO, OBRAS, OUTROS"
      },
      {
        "coluna": "descricao",
        "tipo": "VARCHAR(180)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "O que foi pago"
      },
      {
        "coluna": "valor",
        "tipo": "NUMERIC(10,2)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Valor pago; precisa ser maior que zero"
      },
      {
        "coluna": "data",
        "tipo": "DATE",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Dia do pagamento; é por ele que a despesa entra no balancete do mês. Não pode ser futuro"
      },
      {
        "coluna": "fornecedor",
        "tipo": "VARCHAR(120)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Quem recebeu, quando houver"
      },
      {
        "coluna": "comprovante_arquivo",
        "tipo": "VARCHAR(100)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Nome do arquivo da nota fiscal ou do recibo, gravado pela API sem endereço público"
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
        "coluna": "inativo_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Quando a despesa foi cancelada por ter sido lançada errada; ela sai do balancete, e o motivo fica no registro"
      },
      {
        "coluna": "inativado_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico que cancelou a despesa"
      }
    ],
    "regras": [
      "CHECK ((valor > (0)::numeric))"
    ]
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
        "coluna": "arquivo",
        "tipo": "VARCHAR(100)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Nome do arquivo (PDF ou imagem) enviado pelo síndico, gravado pela API sem endereço público"
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
      },
      {
        "coluna": "tipo_conteudo",
        "tipo": "VARCHAR(40)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Tipo do arquivo conferido pelo conteúdo (application/pdf, image/png...)"
      },
      {
        "coluna": "inativo_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Quando o documento foi removido das telas; vazio enquanto disponível. Registro e arquivo ficam guardados"
      },
      {
        "coluna": "inativado_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico que removeu o documento"
      }
    ],
    "regras": []
  },
  {
    "nome": "documentos_cadastro",
    "resumo": "Os documentos que o morador envia ao se cadastrar, para o síndico conferir antes de aprovar.",
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
        "descricao": "Morador que enviou o documento"
      },
      {
        "coluna": "tipo",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "RG ou CNH, comprovante de residência ou escritura; um arquivo por tipo — tipo enumerado tipo_documento_cadastro, valores: IDENTIDADE, COMPROVANTE_RESIDENCIA, ESCRITURA"
      },
      {
        "coluna": "arquivo",
        "tipo": "VARCHAR(100)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Nome aleatório do arquivo gravado pela API, nunca o nome original"
      },
      {
        "coluna": "tipo_conteudo",
        "tipo": "VARCHAR(40)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Tipo do arquivo conferido pelo conteúdo: PDF, JPEG, PNG ou WebP"
      },
      {
        "coluna": "tamanho_bytes",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Tamanho do arquivo enviado"
      },
      {
        "coluna": "enviado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento do envio"
      }
    ],
    "regras": [
      "UNIQUE (usuario_id, tipo)"
    ]
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
        "coluna": "foto_arquivo",
        "tipo": "VARCHAR(100)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Nome do arquivo da foto do volume, gravado pela API sem endereço público; apagado após o prazo de guarda"
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
        "descricao": "Momento da retirada, pelo app ou em mãos na portaria"
      },
      {
        "coluna": "retirada_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Morador que confirmou a retirada pelo app"
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
        "coluna": "entregue_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Porteiro que entregou em mãos na portaria"
      },
      {
        "coluna": "retirado_por_nome",
        "tipo": "VARCHAR(120)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Nome de quem levou a encomenda entregue em mãos (pode não ter cadastro)"
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
      },
      {
        "coluna": "inativo_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Quando o espaço foi inativado; vazio enquanto ativo. As reservas passadas ficam no histórico"
      },
      {
        "coluna": "inativado_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico que inativou o espaço"
      },
      {
        "coluna": "horario_abertura",
        "tipo": "TIME",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Regra de uso: a partir de que horas o espaço pode ser reservado; vazio = sem regra"
      },
      {
        "coluna": "horario_fechamento",
        "tipo": "TIME",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Regra de uso: até que horas o espaço pode ser usado (ex.: 22h, pela lei do silêncio); posterior à abertura"
      },
      {
        "coluna": "antecedencia_minima_dias",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Regra de uso: com quantos dias de antecedência, no mínimo, a reserva precisa ser feita"
      },
      {
        "coluna": "duracao_maxima_horas",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Regra de uso: quantas horas cada reserva pode durar, no máximo"
      },
      {
        "coluna": "limite_por_unidade",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Regra de uso: quantas reservas futuras deste espaço cada apartamento pode ter ao mesmo tempo"
      },
      {
        "coluna": "taxa_uso",
        "tipo": "NUMERIC(10,2)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Taxa de uso (limpeza, gás, desgaste), cobrada do apartamento quando o síndico aprova a reserva; vazia, sem taxa"
      }
    ],
    "regras": [
      "CHECK ((horario_fechamento > horario_abertura))",
      "CHECK (((taxa_uso IS NULL) OR (taxa_uso > (0)::numeric)))"
    ]
  },
  {
    "nome": "horarios_mudanca",
    "resumo": "Os dias da semana e os horários em que o regimento de cada condomínio permite mudança; o dia sem linha não tem mudança.",
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
        "descricao": "Condomínio cujo regimento define o horário"
      },
      {
        "coluna": "dia_semana",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Dia da semana, de 1 (segunda) a 7 (domingo); um horário por dia"
      },
      {
        "coluna": "hora_inicio",
        "tipo": "TIME",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "A partir de que horas a mudança pode começar nesse dia"
      },
      {
        "coluna": "hora_fim",
        "tipo": "TIME",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Até que horas a mudança precisa terminar nesse dia"
      }
    ],
    "regras": [
      "CHECK (((dia_semana >= 1) AND (dia_semana <= 7)))",
      "CHECK ((hora_fim > hora_inicio))",
      "UNIQUE (condominio_id, dia_semana)"
    ]
  },
  {
    "nome": "infracoes",
    "resumo": "As advertências e multas do síndico a um apartamento, com o prazo e a defesa do morador e a decisão do síndico; a multa mantida vira cobrança (Código Civil, art. 1.336, § 2º).",
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
        "descricao": "Condomínio da notificação"
      },
      {
        "coluna": "unidade_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Apartamento notificado"
      },
      {
        "coluna": "aplicada_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico que notificou"
      },
      {
        "coluna": "tipo",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Advertência (sem valor) ou multa — tipo enumerado tipo_infracao, valores: ADVERTENCIA, MULTA"
      },
      {
        "coluna": "descricao",
        "tipo": "TEXT",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "O que aconteceu, como o síndico descreveu na notificação"
      },
      {
        "coluna": "artigo",
        "tipo": "VARCHAR(120)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "O artigo do regimento ou da convenção descumprido"
      },
      {
        "coluna": "ocorrida_em",
        "tipo": "DATE",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Dia da infração, no último ano"
      },
      {
        "coluna": "valor",
        "tipo": "NUMERIC(10,2)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Valor da multa, até 5 vezes a contribuição mensal; vazio na advertência"
      },
      {
        "coluna": "prazo_defesa",
        "tipo": "DATE",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Último dia para o apartamento apresentar a defesa (de 5 a 30 dias depois da notificação)"
      },
      {
        "coluna": "status",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Notificada, com defesa apresentada, mantida ou anulada — tipo enumerado status_infracao, valores: NOTIFICADA, DEFESA_APRESENTADA, CONFIRMADA, ANULADA"
      },
      {
        "coluna": "defesa",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "A defesa do morador, como ele escreveu"
      },
      {
        "coluna": "defesa_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Momento em que a defesa foi apresentada"
      },
      {
        "coluna": "defesa_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Morador que apresentou a defesa"
      },
      {
        "coluna": "decisao_motivo",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Por que o síndico manteve ou anulou; o apartamento recebe"
      },
      {
        "coluna": "decidida_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Momento da decisão"
      },
      {
        "coluna": "decidida_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico que decidiu"
      },
      {
        "coluna": "cobranca_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "A cobrança gerada pela multa mantida"
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
      "CHECK ((((tipo = 'MULTA'::tipo_infracao) AND (valor > (0)::numeric)) OR ((tipo = 'ADVERTENCIA'::tipo_infracao) AND (valor IS NULL))))"
    ]
  },
  {
    "nome": "itens_pauta",
    "resumo": "Os itens da pauta de cada assembleia, com a maioria que cada um exige para ser aprovado.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "assembleia_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Assembleia a que o item pertence"
      },
      {
        "coluna": "ordem",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Posição do item na pauta"
      },
      {
        "coluna": "titulo",
        "tipo": "VARCHAR(180)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "O que está sendo votado"
      },
      {
        "coluna": "descricao",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Detalhes do item, como o orçamento"
      },
      {
        "coluna": "maioria",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Quantos votos aprovam: maioria simples (mais a favor que contra), 2/3 de todos os apartamentos ou unanimidade — tipo enumerado maioria_exigida, valores: SIMPLES, DOIS_TERCOS, UNANIMIDADE"
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
    "nome": "movimentacoes_chave",
    "resumo": "Cada retirada de uma chave e a devolução dela: quem levou, quem entregou e quem recebeu de volta. Uma chave só está fora uma vez.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "chave_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "A chave que saiu"
      },
      {
        "coluna": "retirada_por_nome",
        "tipo": "VARCHAR(160)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Quem levou a chave, como estava no momento"
      },
      {
        "coluna": "retirada_por_documento",
        "tipo": "VARCHAR(20)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Documento de quem levou: o informado na chave de área comum, ou o CPF conferido da pessoa autorizada"
      },
      {
        "coluna": "morador_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Morador do apartamento que levou a chave dele"
      },
      {
        "coluna": "autorizacao_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "A autorização do morador com que a pessoa levou a chave do apartamento"
      },
      {
        "coluna": "retirada_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Quando a chave saiu"
      },
      {
        "coluna": "retirada_registrada_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Porteiro ou síndico que entregou a chave"
      },
      {
        "coluna": "devolvida_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Quando voltou; vazio enquanto está fora"
      },
      {
        "coluna": "devolucao_registrada_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Porteiro ou síndico que recebeu a chave de volta"
      },
      {
        "coluna": "observacao",
        "tipo": "VARCHAR(300)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Recado da portaria sobre a retirada"
      }
    ],
    "regras": []
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
    "nome": "mudancas",
    "resumo": "As mudanças pedidas pelos moradores — dia, horário e empresa — com a avaliação do síndico; a portaria vê as aprovadas.",
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
        "descricao": "Condomínio da mudança"
      },
      {
        "coluna": "unidade_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Apartamento que muda"
      },
      {
        "coluna": "solicitada_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Morador que pediu a mudança"
      },
      {
        "coluna": "tipo",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Se é a chegada de quem vai morar no apartamento ou a saída de quem vai embora — tipo enumerado tipo_mudanca, valores: CHEGADA, SAIDA"
      },
      {
        "coluna": "data",
        "tipo": "DATE",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Dia da mudança, dentro do regimento: com antecedência mínima e nunca no domingo"
      },
      {
        "coluna": "hora_inicio",
        "tipo": "TIME",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Início do horário reservado para a mudança"
      },
      {
        "coluna": "hora_fim",
        "tipo": "TIME",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Fim do horário; uma mudança de cada vez em cada bloco"
      },
      {
        "coluna": "empresa",
        "tipo": "VARCHAR(120)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Empresa que faz a mudança, quando informada"
      },
      {
        "coluna": "observacao",
        "tipo": "VARCHAR(300)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Recado do morador para o síndico e a portaria"
      },
      {
        "coluna": "status",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Pendente, aprovada, recusada, cancelada ou realizada — tipo enumerado status_mudanca, valores: PENDENTE, APROVADA, RECUSADA, CANCELADA, CONCLUIDA"
      },
      {
        "coluna": "avaliada_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Síndico que aprovou ou recusou"
      },
      {
        "coluna": "avaliada_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Momento em que o síndico aprovou ou recusou"
      },
      {
        "coluna": "motivo_recusa",
        "tipo": "VARCHAR(300)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Por que o síndico recusou; o morador recebe"
      },
      {
        "coluna": "cancelada_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Quem cancelou: um morador do apartamento ou o síndico"
      },
      {
        "coluna": "cancelada_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Momento do cancelamento"
      },
      {
        "coluna": "motivo_cancelamento",
        "tipo": "VARCHAR(300)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Por que foi cancelada; obrigatório quando é o síndico quem cancela"
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
        "coluna": "foto_arquivo",
        "tipo": "VARCHAR(100)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Nome do arquivo da foto anexada por quem abriu, gravado pela API sem endereço público"
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
      },
      {
        "coluna": "encargos",
        "tipo": "NUMERIC(10,2)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Parte do valor que pagou multa e juros do atraso; o resto abate a cobrança"
      }
    ],
    "regras": [
      "CHECK (((encargos >= (0)::numeric) AND (encargos <= valor)))",
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
        "descricao": "Sem uso: a permissão saiu do sistema, e o financeiro é sempre recusado ao porteiro"
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
    "nome": "planos_manutencao",
    "resumo": "O que vence de tempos em tempos e não pode passar (AVCB, extintores, caixa d'água, elevadores, para-raios), com a periodicidade e o próximo vencimento. Remover é inativar.",
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
        "descricao": "Condomínio do plano"
      },
      {
        "coluna": "nome",
        "tipo": "VARCHAR(120)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "O que precisa ser feito; único entre os planos ativos do condomínio"
      },
      {
        "coluna": "periodicidade_meses",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "De quantos em quantos meses (1 a 120)"
      },
      {
        "coluna": "proximo_vencimento",
        "tipo": "DATE",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Até quando precisa ser feito de novo; a realização mais recente o renova"
      },
      {
        "coluna": "antecedencia_aviso_dias",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Quantos dias antes do vencimento o painel começa a avisar (0 a 180)"
      },
      {
        "coluna": "fornecedor",
        "tipo": "VARCHAR(120)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Empresa que costuma fazer o serviço"
      },
      {
        "coluna": "observacao",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Anotação do síndico sobre o plano"
      },
      {
        "coluna": "ultima_realizacao",
        "tipo": "DATE",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Dia da realização mais recente; vazia, ainda sem registro"
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
        "coluna": "inativo_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Quando o plano foi removido; vazio enquanto ativo. O histórico de realizações fica guardado"
      },
      {
        "coluna": "inativado_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Quem removeu o plano"
      }
    ],
    "regras": [
      "CHECK (((antecedencia_aviso_dias >= 0) AND (antecedencia_aviso_dias <= 180)))",
      "CHECK (((periodicidade_meses >= 1) AND (periodicidade_meses <= 120)))"
    ]
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
    "nome": "realizacoes_manutencao",
    "resumo": "Cada vez que uma manutenção preventiva foi feita: o dia, o custo e a despesa lançada com ele.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "plano_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "O plano que foi cumprido"
      },
      {
        "coluna": "data",
        "tipo": "DATE",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Dia em que foi feita (nunca no futuro)"
      },
      {
        "coluna": "custo",
        "tipo": "NUMERIC(10,2)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Quanto custou; vazio, sem custo informado"
      },
      {
        "coluna": "observacao",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "O que foi feito, como o síndico anotou"
      },
      {
        "coluna": "registrada_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Quem registrou a realização"
      },
      {
        "coluna": "despesa_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "A despesa de manutenção lançada com o custo, na prestação de contas"
      },
      {
        "coluna": "criado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento em que o registro foi criado, preenchido pelo banco"
      }
    ],
    "regras": [
      "CHECK (((custo IS NULL) OR (custo > (0)::numeric)))"
    ]
  },
  {
    "nome": "registros_alteracao",
    "resumo": "Quem criou, editou, inativou ou reativou cada registro, e quando — o \"editado por fulano\" das telas do administrador.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "autor_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Quem fez a alteração"
      },
      {
        "coluna": "acao",
        "tipo": "VARCHAR(20)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "O que foi feito: criou, editou, inativou, reativou, aprovou, recusou, cancelou ou gerou novo código"
      },
      {
        "coluna": "entidade",
        "tipo": "VARCHAR(30)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Tipo do registro alterado: condominio, usuario, comunicado, documento, espaco, unidade ou cobranca"
      },
      {
        "coluna": "entidade_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Identificador do registro alterado, na tabela indicada em entidade"
      },
      {
        "coluna": "descricao",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "O que mudou, quando cabe (\"Alterou o nome e o telefone\"); a senha aparece pelo nome, nunca pelo valor"
      },
      {
        "coluna": "feito_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento da alteração, preenchido pelo banco"
      }
    ],
    "regras": []
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
      },
      {
        "coluna": "cancelada_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Quem cancelou a reserva: o próprio morador ou o síndico"
      },
      {
        "coluna": "cancelada_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Data e hora do cancelamento, pelo morador ou pelo síndico"
      },
      {
        "coluna": "motivo_cancelamento",
        "tipo": "TEXT",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Por que a reserva foi cancelada (síndico, espaço inativado ou cadastro inativado); o morador vê este texto"
      },
      {
        "coluna": "cobranca_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "A cobrança da taxa de uso, gerada quando o síndico aprovou; cancelada a reserva antes de paga, a cobrança também é"
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
      },
      {
        "coluna": "pendente",
        "tipo": "BOOLEAN",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Verdadeiro quando a unidade foi criada pelo autocadastro de um morador e ainda não foi confirmada pelo síndico; não aparece nas listas da portaria e do síndico até a aprovação"
      }
    ],
    "regras": [
      "UNIQUE (condominio_id, bloco, numero)"
    ]
  },
  {
    "nome": "usuarios",
    "resumo": "Todas as pessoas que acessam o sistema, em qualquer papel: administrador, síndico, porteiro e morador. Quem tem mais de um papel ou apartamento (o síndico que também mora, o dono de dois apartamentos) tem um cadastro por perfil, todos ligados ao cadastro com o login.",
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
      },
      {
        "coluna": "versao_sessao",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Versão da sessão, gravada em cada token; sobe quando a senha é trocada ou redefinida, e os tokens antigos deixam de valer"
      },
      {
        "coluna": "unidade_desde",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Desde quando mora na unidade atual; renovado na transferência e na reativação. O morador só vê os visitantes e as encomendas a partir daqui"
      },
      {
        "coluna": "reside",
        "tipo": "BOOLEAN",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Se o morador mora na unidade; falso no proprietário que alugou: ele paga e vota, mas visitas, encomendas, reservas, carros e mudanças são de quem mora lá"
      },
      {
        "coluna": "conta_principal_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "No perfil vinculado, o cadastro com login da mesma pessoa; vazio no cadastro principal. E-mail e CPF são únicos entre os principais"
      }
    ],
    "regras": []
  },
  {
    "nome": "veiculos_unidade",
    "resumo": "As placas que cada apartamento cadastrou, para a portaria reconhecer o carro do morador na chegada. Deixam de valer sozinhas quando quem cadastrou se muda.",
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
        "descricao": "Condomínio onde o veículo está cadastrado"
      },
      {
        "coluna": "unidade_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Apartamento dono do veículo"
      },
      {
        "coluna": "cadastrado_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Morador (ou síndico) que cadastrou a placa"
      },
      {
        "coluna": "placa",
        "tipo": "VARCHAR(10)",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Placa do veículo, só letras e números; uma placa ativa por condomínio"
      },
      {
        "coluna": "modelo",
        "tipo": "VARCHAR(60)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Modelo do veículo, quando informado"
      },
      {
        "coluna": "cor",
        "tipo": "VARCHAR(30)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Cor do veículo, quando informada"
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
        "coluna": "inativo_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Quando o veículo foi removido do apartamento; vazio enquanto vale. A placa fica livre para outro cadastro"
      },
      {
        "coluna": "inativado_por_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Quem removeu o veículo do apartamento"
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
        "coluna": "foto_arquivo",
        "tipo": "VARCHAR(100)",
        "obrigatorio": "Não",
        "chave": "",
        "descricao": "Nome do arquivo da foto tirada na portaria, gravado pela API sem endereço público; apagado após o prazo de guarda"
      },
      {
        "coluna": "status",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Situação da visita, do anúncio à saída — tipo enumerado status_visitante, valores: AGUARDANDO_CONFIRMACAO, CONFIRMADO, RECUSADO, DENTRO, SAIU, SEM_RESPOSTA"
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
        "descricao": "Morador que autorizou ou recusou (na entrada pela autorização prévia, quem a deixou)"
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
      },
      {
        "coluna": "autorizacao_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Autorização prévia pela qual a pessoa entrou, sem esperar resposta; vazio no anúncio comum"
      }
    ],
    "regras": []
  },
  {
    "nome": "votos",
    "resumo": "O voto de cada apartamento em cada item da pauta: um por apartamento, garantido pelo banco.",
    "colunas": [
      {
        "coluna": "id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "PK",
        "descricao": "Identificador da tabela, gerado pelo banco"
      },
      {
        "coluna": "item_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Item da pauta votado"
      },
      {
        "coluna": "unidade_id",
        "tipo": "INTEGER",
        "obrigatorio": "Sim",
        "chave": "FK",
        "descricao": "Apartamento que votou; um voto por apartamento em cada item"
      },
      {
        "coluna": "usuario_id",
        "tipo": "INTEGER",
        "obrigatorio": "Não",
        "chave": "FK",
        "descricao": "Morador que votou pelo apartamento"
      },
      {
        "coluna": "escolha",
        "tipo": "ENUM",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "A favor, contra ou abstenção — tipo enumerado escolha_voto, valores: A_FAVOR, CONTRA, ABSTENCAO"
      },
      {
        "coluna": "votado_em",
        "tipo": "TIMESTAMPTZ",
        "obrigatorio": "Sim",
        "chave": "",
        "descricao": "Momento do voto; o voto não pode ser mudado depois"
      }
    ],
    "regras": [
      "UNIQUE (item_id, unidade_id)"
    ]
  }
];

const relacoes = [
  {
    "origem": "anotacoes_portaria",
    "coluna": "autor_id",
    "destino": "usuarios",
    "texto": "Porteiro ou síndico que anotou; removido o cadastro, a anotação fica"
  },
  {
    "origem": "anotacoes_portaria",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio do livro"
  },
  {
    "origem": "assembleias",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio que realiza a assembleia"
  },
  {
    "origem": "assembleias",
    "coluna": "convocada_por_id",
    "destino": "usuarios",
    "texto": "Síndico que convocou"
  },
  {
    "origem": "assembleias",
    "coluna": "inativado_por_id",
    "destino": "usuarios",
    "texto": "Síndico que cancelou"
  },
  {
    "origem": "autorizacoes_visita",
    "coluna": "autorizado_por_id",
    "destino": "usuarios",
    "texto": "Morador que deixou a autorização; ela deixa de valer se ele não morar mais lá"
  },
  {
    "origem": "autorizacoes_visita",
    "coluna": "inativado_por_id",
    "destino": "usuarios",
    "texto": "Morador que revogou a autorização"
  },
  {
    "origem": "autorizacoes_visita",
    "coluna": "unidade_id",
    "destino": "unidades",
    "texto": "Apartamento para o qual a entrada está liberada"
  },
  {
    "origem": "chaves",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio da portaria que guarda a chave"
  },
  {
    "origem": "chaves",
    "coluna": "inativado_por_id",
    "destino": "usuarios",
    "texto": "Quem tirou a chave do quadro"
  },
  {
    "origem": "chaves",
    "coluna": "unidade_id",
    "destino": "unidades",
    "texto": "Apartamento dono da chave; vazio, chave de área comum"
  },
  {
    "origem": "ciencias_anotacao",
    "coluna": "anotacao_id",
    "destino": "anotacoes_portaria",
    "texto": "A anotação lida"
  },
  {
    "origem": "ciencias_anotacao",
    "coluna": "usuario_id",
    "destino": "usuarios",
    "texto": "Quem deu ciência"
  },
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
    "origem": "comunicados",
    "coluna": "inativado_por_id",
    "destino": "usuarios",
    "texto": "Síndico que removeu o comunicado"
  },
  {
    "origem": "comunicados",
    "coluna": "unidade_id",
    "destino": "unidades",
    "texto": "Apartamento de destino, quando o aviso é só para ele (ex.: uma advertência); nunca junto com o bloco"
  },
  {
    "origem": "condominios",
    "coluna": "inativado_por_id",
    "destino": "usuarios",
    "texto": "Administrador que inativou o condomínio"
  },
  {
    "origem": "condominios",
    "coluna": "sindico_id",
    "destino": "usuarios",
    "texto": "Síndico responsável pelo condomínio"
  },
  {
    "origem": "declaracoes_quitacao",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio que declara"
  },
  {
    "origem": "declaracoes_quitacao",
    "coluna": "emitida_por_id",
    "destino": "usuarios",
    "texto": "Morador ou síndico que pediu"
  },
  {
    "origem": "declaracoes_quitacao",
    "coluna": "revogada_por_id",
    "destino": "usuarios",
    "texto": "Síndico que revogou"
  },
  {
    "origem": "declaracoes_quitacao",
    "coluna": "unidade_id",
    "destino": "unidades",
    "texto": "Apartamento declarado em dia"
  },
  {
    "origem": "despesas",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio que pagou"
  },
  {
    "origem": "despesas",
    "coluna": "inativado_por_id",
    "destino": "usuarios",
    "texto": "Síndico que cancelou a despesa"
  },
  {
    "origem": "despesas",
    "coluna": "lancada_por_id",
    "destino": "usuarios",
    "texto": "Síndico que lançou a despesa"
  },
  {
    "origem": "documentos",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio a que o documento pertence"
  },
  {
    "origem": "documentos",
    "coluna": "inativado_por_id",
    "destino": "usuarios",
    "texto": "Síndico que removeu o documento"
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
    "origem": "documentos_cadastro",
    "coluna": "usuario_id",
    "destino": "usuarios",
    "texto": "Morador que enviou o documento"
  },
  {
    "origem": "encomendas",
    "coluna": "entregue_por_id",
    "destino": "usuarios",
    "texto": "Porteiro que entregou em mãos na portaria"
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
    "texto": "Morador que confirmou a retirada pelo app"
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
    "origem": "espacos_comuns",
    "coluna": "inativado_por_id",
    "destino": "usuarios",
    "texto": "Síndico que inativou o espaço"
  },
  {
    "origem": "horarios_mudanca",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio cujo regimento define o horário"
  },
  {
    "origem": "infracoes",
    "coluna": "aplicada_por_id",
    "destino": "usuarios",
    "texto": "Síndico que notificou"
  },
  {
    "origem": "infracoes",
    "coluna": "cobranca_id",
    "destino": "cobrancas",
    "texto": "A cobrança gerada pela multa mantida"
  },
  {
    "origem": "infracoes",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio da notificação"
  },
  {
    "origem": "infracoes",
    "coluna": "decidida_por_id",
    "destino": "usuarios",
    "texto": "Síndico que decidiu"
  },
  {
    "origem": "infracoes",
    "coluna": "defesa_por_id",
    "destino": "usuarios",
    "texto": "Morador que apresentou a defesa"
  },
  {
    "origem": "infracoes",
    "coluna": "unidade_id",
    "destino": "unidades",
    "texto": "Apartamento notificado"
  },
  {
    "origem": "itens_pauta",
    "coluna": "assembleia_id",
    "destino": "assembleias",
    "texto": "Assembleia a que o item pertence"
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
    "origem": "movimentacoes_chave",
    "coluna": "autorizacao_id",
    "destino": "autorizacoes_visita",
    "texto": "A autorização do morador com que a pessoa levou a chave do apartamento"
  },
  {
    "origem": "movimentacoes_chave",
    "coluna": "chave_id",
    "destino": "chaves",
    "texto": "A chave que saiu"
  },
  {
    "origem": "movimentacoes_chave",
    "coluna": "devolucao_registrada_por_id",
    "destino": "usuarios",
    "texto": "Porteiro ou síndico que recebeu a chave de volta"
  },
  {
    "origem": "movimentacoes_chave",
    "coluna": "morador_id",
    "destino": "usuarios",
    "texto": "Morador do apartamento que levou a chave dele"
  },
  {
    "origem": "movimentacoes_chave",
    "coluna": "retirada_registrada_por_id",
    "destino": "usuarios",
    "texto": "Porteiro ou síndico que entregou a chave"
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
    "origem": "mudancas",
    "coluna": "avaliada_por_id",
    "destino": "usuarios",
    "texto": "Síndico que aprovou ou recusou"
  },
  {
    "origem": "mudancas",
    "coluna": "cancelada_por_id",
    "destino": "usuarios",
    "texto": "Quem cancelou: um morador do apartamento ou o síndico"
  },
  {
    "origem": "mudancas",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio da mudança"
  },
  {
    "origem": "mudancas",
    "coluna": "solicitada_por_id",
    "destino": "usuarios",
    "texto": "Morador que pediu a mudança"
  },
  {
    "origem": "mudancas",
    "coluna": "unidade_id",
    "destino": "unidades",
    "texto": "Apartamento que muda"
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
    "origem": "planos_manutencao",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio do plano"
  },
  {
    "origem": "planos_manutencao",
    "coluna": "inativado_por_id",
    "destino": "usuarios",
    "texto": "Quem removeu o plano"
  },
  {
    "origem": "preferencias_cobranca",
    "coluna": "morador_id",
    "destino": "usuarios",
    "texto": "Morador dono da preferência"
  },
  {
    "origem": "realizacoes_manutencao",
    "coluna": "despesa_id",
    "destino": "despesas",
    "texto": "A despesa de manutenção lançada com o custo, na prestação de contas"
  },
  {
    "origem": "realizacoes_manutencao",
    "coluna": "plano_id",
    "destino": "planos_manutencao",
    "texto": "O plano que foi cumprido"
  },
  {
    "origem": "realizacoes_manutencao",
    "coluna": "registrada_por_id",
    "destino": "usuarios",
    "texto": "Quem registrou a realização"
  },
  {
    "origem": "registros_alteracao",
    "coluna": "autor_id",
    "destino": "usuarios",
    "texto": "Quem fez a alteração"
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
    "coluna": "cancelada_por_id",
    "destino": "usuarios",
    "texto": "Quem cancelou a reserva: o próprio morador ou o síndico"
  },
  {
    "origem": "reservas",
    "coluna": "cobranca_id",
    "destino": "cobrancas",
    "texto": "A cobrança da taxa de uso, gerada quando o síndico aprovou; cancelada a reserva antes de paga, a cobrança também é"
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
    "coluna": "conta_principal_id",
    "destino": "usuarios",
    "texto": "No perfil vinculado, o cadastro com login da mesma pessoa; vazio no cadastro principal. E-mail e CPF são únicos entre os principais"
  },
  {
    "origem": "usuarios",
    "coluna": "unidade_id",
    "destino": "unidades",
    "texto": "Unidade em que o morador vive; vazio para síndico, porteiro e administrador"
  },
  {
    "origem": "veiculos_unidade",
    "coluna": "cadastrado_por_id",
    "destino": "usuarios",
    "texto": "Morador (ou síndico) que cadastrou a placa"
  },
  {
    "origem": "veiculos_unidade",
    "coluna": "condominio_id",
    "destino": "condominios",
    "texto": "Condomínio onde o veículo está cadastrado"
  },
  {
    "origem": "veiculos_unidade",
    "coluna": "inativado_por_id",
    "destino": "usuarios",
    "texto": "Quem removeu o veículo do apartamento"
  },
  {
    "origem": "veiculos_unidade",
    "coluna": "unidade_id",
    "destino": "unidades",
    "texto": "Apartamento dono do veículo"
  },
  {
    "origem": "visitantes",
    "coluna": "autorizacao_id",
    "destino": "autorizacoes_visita",
    "texto": "Autorização prévia pela qual a pessoa entrou, sem esperar resposta; vazio no anúncio comum"
  },
  {
    "origem": "visitantes",
    "coluna": "confirmado_por_id",
    "destino": "usuarios",
    "texto": "Morador que autorizou ou recusou (na entrada pela autorização prévia, quem a deixou)"
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
  },
  {
    "origem": "votos",
    "coluna": "item_id",
    "destino": "itens_pauta",
    "texto": "Item da pauta votado"
  },
  {
    "origem": "votos",
    "coluna": "unidade_id",
    "destino": "unidades",
    "texto": "Apartamento que votou; um voto por apartamento em cada item"
  },
  {
    "origem": "votos",
    "coluna": "usuario_id",
    "destino": "usuarios",
    "texto": "Morador que votou pelo apartamento"
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
    "nome": "categoria_despesa",
    "valores": "AGUA, ENERGIA, LIMPEZA, MANUTENCAO, SEGURANCA, PESSOAL, ADMINISTRACAO, OBRAS, OUTROS"
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
    "nome": "escolha_voto",
    "valores": "A_FAVOR, CONTRA, ABSTENCAO"
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
    "nome": "maioria_exigida",
    "valores": "SIMPLES, DOIS_TERCOS, UNANIMIDADE"
  },
  {
    "nome": "origem_cobranca",
    "valores": "TAXA, MULTA, USO_ESPACO"
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
    "nome": "status_infracao",
    "valores": "NOTIFICADA, DEFESA_APRESENTADA, CONFIRMADA, ANULADA"
  },
  {
    "nome": "status_mudanca",
    "valores": "PENDENTE, APROVADA, RECUSADA, CANCELADA, CONCLUIDA"
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
    "valores": "AGUARDANDO_CONFIRMACAO, CONFIRMADO, RECUSADO, DENTRO, SAIU, SEM_RESPOSTA"
  },
  {
    "nome": "tipo_documento_cadastro",
    "valores": "IDENTIDADE, COMPROVANTE_RESIDENCIA, ESCRITURA"
  },
  {
    "nome": "tipo_infracao",
    "valores": "ADVERTENCIA, MULTA"
  },
  {
    "nome": "tipo_movimentacao",
    "valores": "ENTRADA, SAIDA"
  },
  {
    "nome": "tipo_mudanca",
    "valores": "CHEGADA, SAIDA"
  },
  {
    "nome": "tipo_ocupacao",
    "valores": "PROPRIETARIO, INQUILINO, COABITANTE"
  }
];

module.exports = { dicionario, relacoes, enumerados };

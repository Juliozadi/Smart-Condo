"""Executa o script no MySQL e guarda, em resultados.json, o que o
documento mostra: o estado das tabelas depois de cada etapa da carga, as
consultas de verificação e as mensagens de erro dos testes de integridade.

    python coletar_resultados.py      # precisa de um MySQL 8 local (root)

Assim, toda saída reproduzida no documento veio de uma execução real.
"""
import json
import os
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, '..', 'script_concessionaria.sql')
MYSQL = ['mysql', '-uroot', '--default-character-set=utf8mb4']


def executar(sql, banco=None, lote=False):
    cmd = MYSQL + (['--batch'] if lote else []) + ([banco] if banco else [])
    r = subprocess.run(cmd, input=sql, capture_output=True, text=True)
    return r.stdout, r.stderr.strip()


def consulta(sql):
    saida, erro = executar(sql, 'concessionaria_db', lote=True)
    if erro:
        raise RuntimeError(erro)
    linhas = [l.split('\t') for l in saida.rstrip('\n').split('\n')]
    return {'colunas': linhas[0], 'linhas': linhas[1:]}


def ate(marcador):
    """Trecho do script do início até a linha do marcador (exclusive)."""
    texto = open(SCRIPT, encoding='utf-8').read()
    return texto[:texto.index(marcador)]


resultados = {}

# Etapa 1: estrutura + cadastros
executar(ate('-- 3.2)'))
resultados['apos_insert_veiculos'] = consulta('SELECT * FROM veiculos')
resultados['apos_insert_contagem'] = consulta(
    "SELECT 'fornecedores' AS tabela, COUNT(*) AS registros FROM fornecedores "
    "UNION ALL SELECT 'veiculos', COUNT(*) FROM veiculos "
    "UNION ALL SELECT 'clientes', COUNT(*) FROM clientes "
    "UNION ALL SELECT 'funcionarios', COUNT(*) FROM funcionarios")
resultados['antes_update'] = consulta(
    "SELECT 'Onix' AS item, preco AS valor FROM veiculos WHERE modelo = 'Onix' "
    "UNION ALL SELECT 'Compass', status FROM veiculos WHERE placa = 'PQR6I78' "
    "UNION ALL SELECT 'Mariana', telefone FROM clientes "
    "WHERE cpf = '123.456.789-00' "
    "UNION ALL SELECT nome, salario FROM funcionarios WHERE cargo = 'Vendedor'")

# Etapa 2: vendas
executar(ate('-- 3.3)'))
resultados['apos_vendas'] = consulta('SELECT * FROM vendas')
resultados['apos_vendas_status'] = consulta(
    'SELECT id, marca, modelo, status FROM veiculos ORDER BY id')

# Etapa 3: atualizações
executar(ate('-- 3.4)'))
resultados['depois_update'] = consulta(
    "SELECT 'Onix' AS item, preco AS valor FROM veiculos WHERE modelo = 'Onix' "
    "UNION ALL SELECT 'Compass', status FROM veiculos WHERE placa = 'PQR6I78' "
    "UNION ALL SELECT 'Mariana', telefone FROM clientes "
    "WHERE cpf = '123.456.789-00' "
    "UNION ALL SELECT nome, salario FROM funcionarios WHERE cargo = 'Vendedor'")

# Script completo
saida, erro = executar(open(SCRIPT, encoding='utf-8').read())
if erro:
    raise RuntimeError(erro)
# Mesma consulta do Código 7 do documento
resultados['restricoes'] = consulta(
    "SELECT TABLE_NAME AS tabela, CONSTRAINT_NAME AS restricao,\n"
    "       CONSTRAINT_TYPE AS tipo\n"
    "FROM information_schema.TABLE_CONSTRAINTS\n"
    "WHERE TABLE_SCHEMA = 'concessionaria_db'\n"
    "ORDER BY TABLE_NAME, CONSTRAINT_TYPE, CONSTRAINT_NAME;")

# As quatro consultas de verificação, exatamente como estão no script
texto = open(SCRIPT, encoding='utf-8').read()
bloco = texto[texto.index('-- 5) CONSULTAS'):]
comandos = [c.strip() for c in bloco.split(';') if 'SELECT' in c]
nomes = ['final_contagem', 'final_estoque', 'final_vendas', 'final_por_funcionario']
for nome, cmd in zip(nomes, comandos):
    sql = '\n'.join(l for l in cmd.split('\n') if not l.startswith('--'))
    resultados[nome] = consulta(sql)

# Testes de integridade: cada um deve falhar
testes = {
    'teste_fk': "DELETE FROM clientes WHERE cpf = '123.456.789-00';",
    'teste_unique': "INSERT INTO vendas (cliente_id, funcionario_id, veiculo_id, "
                    "data_venda, valor_venda) VALUES (3, 3, 1, '2026-09-21', 70000.00);",
    'teste_check': "UPDATE veiculos SET status = 'Vendida' WHERE id = 6;",
}
for nome, sql in testes.items():
    _, erro = executar(sql, 'concessionaria_db')
    assert erro.startswith('ERROR'), (nome, erro)
    resultados[nome] = erro.replace(' at line 1', '')

resultados['versao'] = consulta('SELECT VERSION() AS v')['linhas'][0][0]

with open(os.path.join(AQUI, 'resultados.json'), 'w', encoding='utf-8') as f:
    json.dump(resultados, f, ensure_ascii=False, indent=1)
print('resultados.json gravado |', resultados['versao'])
for k in ('antes_update', 'depois_update', 'teste_fk', 'teste_unique', 'teste_check'):
    print(k, resultados[k])

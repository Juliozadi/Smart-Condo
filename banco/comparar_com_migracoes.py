"""Confere que banco/01_criar_tabelas.sql cria o mesmo banco que as migrações.

O script SQL é mantido à mão, para quem prefere criar o banco pelo
pgAdmin, e é fácil esquecer de acompanhar uma migração nova. Este
programa compara dois bancos — um criado pelo Alembic, outro pelo
script — e lista toda diferença de tabela, coluna, restrição ou índice.

    python banco/comparar_com_migracoes.py URL_DO_BANCO_ALEMBIC URL_DO_BANCO_SCRIPT

As URLs no formato postgresql://usuario:senha@host:porta/banco. Sai com
código 1 se houver diferença, para o CI falhar.
"""
import subprocess
import sys

CONSULTAS = {
    "colunas": """
        SELECT table_name||'.'||column_name||' '||data_type||
               coalesce('('||character_maximum_length||')','')||
               ' nulo='||is_nullable||' padrao='||coalesce(column_default,'-')
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name<>'alembic_version'""",
    "restricoes": """
        SELECT rel.relname||' '||con.conname||' '||pg_get_constraintdef(con.oid)
        FROM pg_constraint con JOIN pg_class rel ON rel.oid=con.conrelid
        JOIN pg_namespace n ON n.oid=rel.relnamespace
        WHERE n.nspname='public' AND rel.relname<>'alembic_version'""",
    "indices": """
        SELECT indexdef FROM pg_indexes
        WHERE schemaname='public' AND tablename<>'alembic_version'""",
    "tipos": """
        SELECT t.typname||' '||string_agg(e.enumlabel, ',' ORDER BY e.enumsortorder)
        FROM pg_type t JOIN pg_enum e ON e.enumtypid=t.oid GROUP BY t.typname""",
}


def ler(url: str, sql: str) -> set[str]:
    saida = subprocess.run(["psql", url, "-tA", "-c", sql],
                           capture_output=True, text=True, check=True).stdout
    return {linha for linha in saida.splitlines() if linha.strip()}


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    alembic, script = sys.argv[1], sys.argv[2]
    diferencas = 0
    for nome, sql in CONSULTAS.items():
        a, s = ler(alembic, sql), ler(script, sql)
        for linha in sorted(a - s):
            print(f"[{nome}] só nas migrações: {linha}")
            diferencas += 1
        for linha in sorted(s - a):
            print(f"[{nome}] só no script SQL: {linha}")
            diferencas += 1
    if diferencas:
        print(f"\n{diferencas} diferença(s). Atualize banco/01_criar_tabelas.sql.")
        return 1
    print("O script SQL cria o mesmo banco que as migrações.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

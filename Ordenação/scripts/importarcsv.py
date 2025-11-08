import sqlite3
import pandas as pd

DB_NAME = "dados_desmatamentoAM.db"
TABELA = "desmatamento"   # coloque o nome da sua tabela aqui
CSV_SAIDA = "dados_exportados.csv"

con = sqlite3.connect(DB_NAME)

df = pd.read_sql_query(f"SELECT * FROM {TABELA}", con)

df.to_csv(CSV_SAIDA, index=False, encoding="utf-8")

con.close()

print("CSV gerado:", CSV_SAIDA)

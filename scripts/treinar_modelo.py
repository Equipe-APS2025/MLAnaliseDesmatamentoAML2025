import mysql.connector
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "81218515",
    "database": "desmatamentoaml"
}

con = mysql.connector.connect(**DB_CONFIG)
cur = con.cursor()
cur.execute("SELECT ano, uf , area_km FROM desmatamento")
dados = cur.fetchall()
con.close()

df = pd.DataFrame(dados, columns=["ano", "uf", "area_km"])
df = pd.get_dummies(df, columns=["uf"])

X = df.drop("area_km", axis=1)
y = df["area_km"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

modelo = RandomForestRegressor()
modelo.fit(X_train, y_train)

joblib.dump(modelo, "modelo_rf.pkl")

print("Modelo treinado. Score:", modelo.score(X_test, y_test))

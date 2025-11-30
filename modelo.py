import pandas as pd
import sqlite3
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor


def carregar_dados_para_modelo(db_name, estado=None):
    conn = sqlite3.connect(db_name)

    if estado:
        query = "SELECT * FROM desmatamento_por_ano_estado WHERE state = ? ORDER BY year"
        df = pd.read_sql_query(query, conn, params=(estado,))
    else:
        query = "SELECT * FROM desmatamento_por_ano_estado ORDER BY year"
        df = pd.read_sql_query(query, conn)

    conn.close()
    return df


def treinar_modelo(df):
    df["year"] = df["year"].astype(int)

    df_ano = df.groupby("year")["total_area_km"].sum().reset_index()

    X = df_ano[["year"]]
    y = df_ano["total_area_km"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"MAE: {mae:.2f}, R²: {r2:.2f}")

    return model, df_ano


def prever_futuro(model, ano_inicial, anos_a_frente=5):
    futuros = pd.DataFrame({
        "year": range(ano_inicial + 1, ano_inicial + anos_a_frente + 1)
    })

    futuros["previsto_km2"] = model.predict(futuros[["year"]])
    futuros["previsto_km2"] = futuros["previsto_km2"].clip(lower=0)

    return futuros


def previsao_estado(db_name, estado_selecionado, anos_futuros=5):
    conn = sqlite3.connect(db_name)
    df = pd.read_sql_query(
        """
        SELECT year, SUM(area_km) AS total_area_km
        FROM desmatamento
        WHERE state = ?
        GROUP BY year
        ORDER BY year
        """,
        conn, params=(estado_selecionado,)
    )
    conn.close()

    if df.empty:
        return [], []

    X = df[["year"]]
    y = df["total_area_km"]

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    ultimo_ano = df["year"].max()

    futuros = pd.DataFrame({
        "year": range(ultimo_ano + 1, ultimo_ano + anos_futuros + 1)
    })

    previsao = model.predict(futuros[["year"]])
    futuros["previsto_km2"] = previsao.clip(min=0)

    return df.to_dict(orient="records"), futuros.to_dict(orient="records")

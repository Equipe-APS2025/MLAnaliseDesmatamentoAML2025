from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from shapely import wkt
import folium
import uuid
import pandas as pd
import geopandas as gpd
import os
import joblib

app = Flask(__name__)

# Banco para tabela + gráfico
DB_TABELA = {
    "host": "localhost",
    "user": "root",
    "password": "81218515",
    "database": "desmatamentoaml"
}

# Banco para mapa (possui a coluna geometry)
DB_MAPA = {
    "host": "localhost",
    "user": "root",
    "password": "81218515",
    "database": "desmatamento_db"
}

MAPA_ESTADOS = {
    "Acre": "AC",
    "Amazonas": "AM",
    "Rondônia": "RO",
    "Roraima": "RR",
    "Pará": "PA",
    "Amapá": "AP",
    "Tocantins": "TO",
    "Mato Grosso": "MT",
    "Maranhão": "MA"
}

def conectar_tabela():
    return mysql.connector.connect(**DB_TABELA)

def conectar_mapa():
    return mysql.connector.connect(**DB_MAPA)

modelo = joblib.load(r"C:\Users\arian\Ordenação\data\modelo_rf.pkl")

def prever_area(ano, estado):
    # Converte nome para sigla se vier em formato textual
    estado = MAPA_ESTADOS.get(estado, estado)  # Mantém se já for sigla
    estado = estado.strip().upper()

    df = pd.DataFrame([[ano, estado]], columns=["year", "state"])
    df = pd.get_dummies(df, columns=["state"])

    # Adiciona colunas que o modelo espera e não vieram
    for col in modelo.feature_names_in_:
        if col not in df.columns:
            df[col] = 0

    # Reordena exatamente como no treino
    df = df[modelo.feature_names_in_]

    return float(modelo.predict(df)[0])

@app.route("/", methods=["GET", "POST"])
def index():
    con = conectar_tabela()
    cur = con.cursor()

    cur.execute("SELECT DISTINCT ano FROM desmatamento ORDER BY ano")
    anos = [str(r[0]) for r in cur.fetchall()]

    cur.execute("SELECT DISTINCT uf FROM desmatamento ORDER BY uf")
    estados = [r[0] for r in cur.fetchall()]
    con.close()

    if request.method == "POST":
        anos_sel = request.form.getlist("ano")
        estados_sel = request.form.getlist("estado")

        return redirect(url_for("resultado",
                                anos=",".join(anos_sel),
                                estados=",".join(estados_sel)))
    return render_template("index.html", anos=anos, estados=estados)

@app.route("/resultado")
def resultado():
    anos = [a for a in request.args.get("anos", "").split(",") if a]
    estados = [e for e in request.args.get("estados", "").split(",") if e]

    # ------- DADOS PARA TABELA E GRÁFICO -------
    con_tabela = conectar_tabela()
    cur_tabela = con_tabela.cursor()

    query = """
        SELECT ano, uf, SUM(area_km) AS total_area_km
        FROM desmatamento
        WHERE 1=1
    """
    params = []

    if anos:
        query += f" AND ano IN ({','.join(['%s']*len(anos))})"
        params.extend(anos)
    if estados:
        query += f" AND uf IN ({','.join(['%s']*len(estados))})"
        params.extend(estados)

    query += " GROUP BY ano, uf"
    cur_tabela.execute(query, params)

    dados = [{"ano": r[0], "uf": r[1], "total_area_km": float(r[2])} for r in cur_tabela.fetchall()]
    con_tabela.close()

    # ------- DADOS PARA MAPA -------
    con_mapa = conectar_mapa()
    cur_mapa = con_mapa.cursor()

    query_map = """
        SELECT year, state, area_km, geometry
        FROM desmatamento
        WHERE 1=1
    """
    params_map = []

    if anos:
        query_map += f" AND year IN ({','.join(['%s']*len(anos))})"
        params_map.extend(anos)
    if estados:
        query_map += f" AND state IN ({','.join(['%s']*len(estados))})"
        params_map.extend(estados)

    cur_mapa.execute(query_map, params_map)
    mapas = cur_mapa.fetchall()
    con_mapa.close()

    # ------- MÉDIA -------
    media = round(sum(d["total_area_km"] for d in dados) / len(dados), 2) if dados else 0

    # ------- ORDENAÇÃO -------
    ordem = request.args.get("ordem", "ano")
    if ordem == "valor":
        dados = sorted(dados, key=lambda x: x["total_area_km"], reverse=True)
    else:
        dados = sorted(dados, key=lambda x: x["ano"])

    grafico_anos = [f"{d['ano']} - {d['uf']}" for d in dados]
    grafico_valores = [round(d["total_area_km"], 2) for d in dados]

    # ------- MAPA -------
    mapa_html = None
    if mapas:
        df_map = pd.DataFrame(mapas, columns=["year", "state", "area_km", "geometry"])
        df_map["geometry"] = df_map["geometry"].apply(wkt.loads)
        gdf_map = gpd.GeoDataFrame(df_map, geometry="geometry", crs="EPSG:4326").simplify(0.01)

        m = folium.Map(location=[-4.5, -63], zoom_start=5, tiles="CartoDBPositron")
        folium.GeoJson(gdf_map).add_to(m)

        if not os.path.exists("static"):
            os.makedirs("static")

        mapa_html = f"mapa_{uuid.uuid4().hex}.html"
        m.save(f"static/{mapa_html}")

    # ------- PREVISÕES -------
    previsoes = [
        {"ano": ano, "estado": estado, "previsto": round(prever_area(int(ano), estado), 2)}
        for estado in estados for ano in anos
    ]

    return render_template("resultado.html",
                           dados=dados,
                           media=media,
                           grafico_anos=grafico_anos,
                           grafico_valores=grafico_valores,
                           mapa_html=mapa_html,
                           anos=anos,
                           estados=estados,
                           previsoes=previsoes)

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
import geopandas as gpd
from shapely import wkt
import folium
import uuid
import pandas as pd
import modelo   # ✔ Importação correta, sem import circular

app = Flask(__name__)

DB_NAME = "dados_desmatamentoAM.db"
SHP_FILE = r"C:\Users\arian\Downloads\yearly_deforestation_biome\yearly_deforestation_biome.shp"


def inicializar_banco():
    if not os.path.exists(DB_NAME):
        print("⏳ Criando banco de dados...")
        df = gpd.read_file(SHP_FILE)

        df.columns = [
            c.strip().replace(" ", "_")
             .replace("²", "2").replace("á", "a").replace("é", "e")
             .replace("í", "i").replace("ó", "o").replace("ú", "u")
             .replace("ã", "a").replace("ç", "c")
             .lower()
            for c in df.columns
        ]

        df = df[df["geometry"].notna()]

        conn = sqlite3.connect(DB_NAME)
        df.to_sql("desmatamento", conn, if_exists="replace", index=False)
        conn.close()
        print("log Banco criado com sucesso!")
    else:
        print("log Banco já existe.")

    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
        CREATE VIEW IF NOT EXISTS desmatamento_por_ano_estado AS
        SELECT year, state, SUM(area_km) AS total_area_km
        FROM desmatamento
        GROUP BY year, state
        ORDER BY year, state
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Erro ao criar view: {e}")


@app.route("/", methods=["GET", "POST"])
def index():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT year FROM desmatamento ORDER BY year")
    anos = [str(int(row[0])) for row in cur.fetchall()]

    cur.execute("SELECT DISTINCT state FROM desmatamento ORDER BY state")
    estados = [row[0] for row in cur.fetchall()]
    conn.close()

    if request.method == "POST":
        anos_sel = request.form.getlist("ano")
        estados_sel = request.form.getlist("estado")

        return redirect(url_for(
            "resultado",
            anos=",".join(anos_sel) if anos_sel else "",
            estados=",".join(estados_sel) if estados_sel else ""
        ))

    return render_template("index.html", anos=anos, estados=estados)


@app.route("/previsao", methods=["GET", "POST"])
def previsao():
    conn = sqlite3.connect(DB_NAME)
    estados = pd.read_sql_query(
        "SELECT DISTINCT state FROM desmatamento ORDER BY state", conn
    )["state"].tolist()
    conn.close()

    estado_sel = request.form.get("estado") if request.method == "POST" else request.args.get("estado")

    if not estado_sel:
        return render_template("previsao_estado.html", estados=estados, previsoes=None)

    df = modelo.carregar_dados_para_modelo(DB_NAME, estado_sel)
    if df.empty:
        return f"⚠️ Não há dados disponíveis para o estado {estado_sel}.", 400

    model, df_ano = modelo.treinar_modelo(df)

    ultimo_ano = int(df_ano["year"].max())
    previsoes = modelo.prever_futuro(model, ultimo_ano, anos_a_frente=5)

    return render_template(
        "previsao_estado.html",
        estados=estados,
        estado_sel=estado_sel,
        previsoes=previsoes.to_dict(orient="records"),
        historico=df_ano.to_dict(orient="records"),
        ultimo_ano=ultimo_ano
    )


@app.route("/previsao_estado/<estado>")
def mostrar_previsao(estado):
    historico, previsoes = modelo.previsao_estado(DB_NAME, estado)
    return render_template(
        "previsao_estado.html",
        historico=historico,
        previsoes=previsoes,
        estado=estado
    )


@app.route("/resultado")
def resultado():
    anos = request.args.get("anos", "")
    estados = request.args.get("estados", "")

    anos_list = [a for a in anos.split(",") if a]
    estados_list = [e for e in estados.split(",") if e]

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    query_view = "SELECT * FROM desmatamento_por_ano_estado WHERE 1=1"
    params = []

    if anos_list:
        query_view += f" AND year IN ({','.join(['?'] * len(anos_list))})"
        params.extend(anos_list)

    if estados_list:
        query_view += f" AND state IN ({','.join(['?'] * len(estados_list))})"
        params.extend(estados_list)

    cur.execute(query_view, params)
    dados = [
        dict(year=row[0], state=row[1], total_area_km=row[2])
        for row in cur.fetchall()
    ]

    query_map = "SELECT year, state, area_km, geometry FROM desmatamento WHERE 1=1"
    params_map = []

    if anos_list:
        query_map += f" AND year IN ({','.join(['?'] * len(anos_list))})"
        params_map.extend(anos_list)

    if estados_list:
        query_map += f" AND state IN ({','.join(['?'] * len(estados_list))})"
        params_map.extend(estados_list)

    cur.execute(query_map, params_map)
    mapas = [
        dict(year=row[0], state=row[1], area_km=row[2], geometry=row[3])
        for row in cur.fetchall()
    ]
    conn.close()

    media = round(sum(d["total_area_km"] for d in dados) / len(dados), 2) if dados else 0

    grafico_anos = [f"{d['year']} - {d['state']}" for d in dados]
    grafico_valores = [round(d["total_area_km"], 2) for d in dados]

    mapa_html = None

    if mapas:
        df_map = pd.DataFrame(mapas)
        df_map["geometry"] = df_map["geometry"].apply(lambda x: wkt.loads(x) if x else None)
        df_map = df_map[df_map["geometry"].notna()]

        gdf_map = gpd.GeoDataFrame(df_map, geometry="geometry", crs="EPSG:4326")
        gdf_map["geometry"] = gdf_map["geometry"].simplify(tolerance=0.01, preserve_topology=True)

        m = folium.Map(location=[-4.5, -63], zoom_start=5, tiles="CartoDBPositron")

        folium.GeoJson(
            gdf_map,
            style_function=lambda x: {
                "fillColor": "#cc0000",
                "color": "#660000",
                "weight": 1,
                "fillOpacity": 0.45
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["year", "state", "area_km"],
                aliases=["Ano", "Estado", "Área (km²)"],
                localize=True
            )
        ).add_to(m)

        if not os.path.exists("static"):
            os.makedirs("static")

        mapa_html = f"mapa_{uuid.uuid4().hex}.html"
        m.save(f"static/{mapa_html}")

    return render_template(
        "resultado.html",
        dados=dados,
        media=media,
        grafico_anos=grafico_anos,
        grafico_valores=grafico_valores,
        mapa_html=mapa_html,
        anos=anos_list,
        estados=estados_list
    )


if __name__ == "__main__":
    inicializar_banco()
    app.run(debug=True)

# 🌳 ML Análise de Desmatamento na Amazônia Legal🌳

## 📄 Sobre o Projeto
Este projeto usa **Machine Learning** para analisar e prever o desmatamento na Amazônia Legal.  
Inclui **mapas interativos**, gráficos e uma aplicação web em **Flask**.

---

## ⚡ Funcionalidades
- 📊 Visualização de dados históricos por **estado** e **ano**  
- 🗺️ Mapas interativos com **Folium**  
- 🤖 Previsão de desmatamento usando modelos ML  

---

## 🛠️ Tecnologias
- Python 3.13 🐍  
- Flask 🌐  
- MySQL / SQLite 🗄️  
- Pandas & GeoPandas 📈  
- Folium 🗺️  
- Joblib 💽  

---

##Estrutura do projeto

MLAnaliseDesmatamentoAML2025/
│
├── app.py                      # Arquivo principal Flask
├── requirements.txt            # Bibliotecas necessárias
│
├── data/                       # Dados para análise / modelo
│   ├── dados.csv
│   ├── dadosanual.csv
│   └── modelo_rf.pkl
│
├── scripts/                    # Scripts Python auxiliares
│   ├── importarcsv.py
│   └── treinar_modelo.py
│
├── templates/                  # Arquivos HTML
│   └── index.html              # Página principal
│   └── resultado.html          # Página de resultados
│
└── static/                     # Arquivos front-end (CSS, JS, imagens)
    ├── css/
    │   └── style.css
    ├── js/
    │   └── script.js
    └── img/
        └── (imagens do layout)


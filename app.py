import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import numpy as np

st.set_page_config(layout="wide", page_title="Carte Bio Hauts-de-France")
st.title("🚜 Outil d'aide à l'installation pour les exploitations en agriculture biologique - Hauts-de-France")

@st.cache_data
def load_data():
    df = pd.read_csv('data.csv', sep=';', encoding='utf-8-sig', dtype=str)

    cols_num = [
        'prct_SAU_normalise', 'prct_gdculture',
        'prct_elevage', 'nb_exploit_normalise',
        'score_global_elevage', 'score_global_gdculture'
    ]

    for col in cols_num:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['canton_raw'] = df['Étiquettes de lignes'].astype(str).str.split('.').str[0].str.strip()
    df['dept'] = df['canton_raw'].str[:-2]
    df['cant'] = df['canton_raw'].str[-2:].str.zfill(3)
    df['canton'] = (df['dept'] + df['cant']).str.zfill(5)

    url_geojson = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"
    gdf_geo = gpd.read_file(url_geojson)
    gdf_geo['code'] = gdf_geo['code'].astype(str).str.strip()
    gdf_geo = gdf_geo[gdf_geo['code'].str[:2].isin(['02', '59', '60', '62', '80'])].copy()

    return df, gdf_geo, cols_num

# Récupération des données
df_csv, gdf_geo, cols_num = load_data()

# --- JOINTURES ---
gdf_final = gdf_geo.merge(df_csv, left_on='code', right_on='canton', how='left')
for col in cols_num:
    gdf_final[col] = gdf_final[col].fillna(0)

# --- INTERFACE UTILISATEUR ---
st.subheader("🌱 Vos préférences")
col1, col2, col3 = st.columns(3)

with col1:
    type_exploit = st.radio("Type d'activité ?", ["Élevage", "Grande culture"], horizontal=True, key="q3")

with col2:
    entraide = st.radio("Besoin d'entraide ?", ["Oui", "Non"], horizontal=True, key="q2")

with col3:
    reprise = st.radio("Terres déjà converties ?", ["Oui", "Non"], horizontal=True, key="q1")

# --- CALCULS ---

# Alpha : intensité de l'effet progressif (ajustable)
alpha = 1.0

# 1. Score de base selon le type d'activité
if type_exploit == "Élevage":
    score_base = gdf_final['prct_elevage'].copy().values
else:
    score_base = gdf_final['prct_gdculture'].copy().values

# 2. Effet progressif "Terres déjà converties"
# Score_final = Score_base × (1 + α × (prct_SAU_normalise − 0.5))
# > 0.5 → bonus, < 0.5 → malus, = 0.5 → neutre
if reprise == "Oui":
    E_terres = gdf_final['prct_SAU_normalise'].values
    score_base = score_base * (1 + alpha * (E_terres - 0.5))

# 3. Effet progressif "Besoin d'entraide"
# Score_final = Score_précédent × (1 + α × (nb_exploit_normalise − 0.5))
# > 0.5 → bonus, < 0.5 → malus, = 0.5 → neutre
if entraide == "Oui":
    E_entraide = gdf_final['nb_exploit_normalise'].values
    score_base = score_base * (1 + alpha * (E_entraide - 0.5))

# Plafonnement entre 0 et 1
gdf_final['score_final'] = np.clip(score_base, 0, 1)

# --- CARTE ---
st.markdown(f"### 🗺️ Cantons favorables — {type_exploit}")

custom_scale = [
    [0.0,  "#d73027"],
    [0.25, "#f46d43"],
    [0.5,  "#fee08b"],
    [0.75, "#a6d96a"],
    [1.0,  "#1a9850"]
]

fig = px.choropleth_mapbox(
    gdf_final,
    geojson=gdf_final.__geo_interface__,
    locations=gdf_final.index,
    color='score_final',
    color_continuous_scale=custom_scale,
    range_color=[0, 1],
    hover_name="nom",
    hover_data={
        "code": True,
        "prct_SAU_normalise": ":.2f",
        "nb_exploit_normalise": ":.2f",
        "prct_elevage": ":.2f",
        "prct_gdculture": ":.2f",
        "score_global_elevage": ":.2f",
        "score_global_gdculture": ":.2f",
        "score_final": ":.2f"
    },
    mapbox_style="carto-positron",
    opacity=0.7
)

fig.update_layout(
    mapbox_zoom=7,
    mapbox_center={"lat": 49.9, "lon": 2.8},
    margin={"r":0,"t":0,"l":0,"b":0},
    height=700
)

st.plotly_chart(fig, use_container_width=True, key="carte_principale")

# --- DEBUG ---
with st.expander("Voir les données brutes"):
    cols_to_show = ['nom', 'code', 'score_final', 'prct_SAU_normalise', 'nb_exploit_normalise',
                    'prct_elevage', 'prct_gdculture', 'score_global_elevage', 'score_global_gdculture']
    st.dataframe(gdf_final[cols_to_show].head(10))

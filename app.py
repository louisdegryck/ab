import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

# Configuration de la page
st.set_page_config(layout="wide", page_title="Carte Bio Hauts-de-France")
st.title("🚜 Outil d'aide à l'installation pour les exploitation en agriculture biologique - Hauts-de-France")

@st.cache_data
def load_data():
    # 1. Chargement du CSV Agricole
    df = pd.read_csv('cartetest.csv', sep=';', encoding='utf-8-sig', dtype=str)
    df = df.iloc[:, :6] 
    df.columns = ['canton', 'surfab', 'terres_ab', 'nb_exploit', 'score_exploit','prct_bio']

    for col in ['surfab', 'terres_ab', 'nb_exploit', 'score_exploit','prct_bio']:
        df[col] = df[col].astype(str).str.replace(',', '.')
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['canton_raw'] = df['canton'].astype(str).str.split('.').str[0].str.strip()
    df['dept'] = df['canton_raw'].str[:-2]
    df['cant'] = df['canton_raw'].str[-2:].str.zfill(3)
    df['canton'] = (df['dept'] + df['cant']).str.zfill(5)

    # 2. Chargement du CSV Industries
    df_ind = pd.read_csv('industries_cantons.csv', sep=';', encoding='utf-8-sig', dtype=str)
    df_ind = df_ind.iloc[:, :6]
    df_ind.columns = ['canton_ind', 'nb_silos', 'nb_transfo_gc', 'nb_abattoirs', 'nb_laiteries', 'nb_transfo_viande']

    for col in ['nb_silos', 'nb_transfo_gc', 'nb_abattoirs', 'nb_laiteries', 'nb_transfo_viande']:
        df_ind[col] = df_ind[col].astype(str).str.replace(',', '.')
        df_ind[col] = pd.to_numeric(df_ind[col], errors='coerce').fillna(0)

    df_ind['canton_raw'] = df_ind['canton_ind'].astype(str).str.split('.').str[0].str.strip()
    df_ind['dept'] = df_ind['canton_raw'].str[:-2]
    df_ind['cant'] = df_ind['canton_raw'].str[-2:].str.zfill(3)
    df_ind['canton_ind'] = (df_ind['dept'] + df_ind['cant']).str.zfill(5)

    # 3. Chargement Géo
    url_geojson = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"
    gdf_geo = gpd.read_file(url_geojson)
    gdf_geo['code'] = gdf_geo['code'].astype(str).str.strip()
    gdf_geo = gdf_geo[gdf_geo['code'].str[:2].isin(['02', '59', '60', '62', '80'])].copy()

    return df, df_ind, gdf_geo

# Récupération des données
df_csv, df_ind, gdf_geo = load_data()

# --- JOINTURES ET NETTOYAGE ---
gdf_final = gdf_geo.merge(df_csv, left_on='code', right_on='canton', how='left')
for col in ['terres_ab', 'score_exploit', 'surfab', 'nb_exploit']:
    gdf_final[col] = pd.to_numeric(gdf_final[col], errors='coerce').fillna(0)

gdf_final = gdf_final.merge(df_ind, left_on='code', right_on='canton_ind', how='left')
for col in ['nb_silos', 'nb_transfo_gc', 'nb_abattoirs', 'nb_laiteries', 'nb_transfo_viande']:
    gdf_final[col] = pd.to_numeric(gdf_final[col], errors='coerce').fillna(0)

# --- INTERFACE UTILISATEUR ---
st.subheader("🌱 Vos préférences")
col1, col2, col3 = st.columns(3)

with col1:
    reprise = st.radio("Terres déjà converties ?", ["Oui", "Non"], horizontal=True, key="q1")

with col2:
    entraide = st.radio("Besoin d'entraide ?", ["Oui", "Non"], horizontal=True, key="q2")

with col3:
    type_exploit = st.radio("Type d'activité ?", ["Élevage", "Grande culture"], horizontal=True, key="q3")

# --- CALCULS ---
# Score Industrie
if type_exploit == "Élevage":
    raw_ind = gdf_final['nb_abattoirs'] + gdf_final['nb_laiteries'] + gdf_final['nb_transfo_viande']
else:
    raw_ind = gdf_final['nb_silos'] + gdf_final['nb_transfo_gc']

i_min, i_max = raw_ind.min(), raw_ind.max()
gdf_final['score_ind'] = (raw_ind - i_min) / (i_max - i_min) if i_max > i_min else 0

# Score Final
veut_terres = (reprise == "Oui")
veut_entraide = (entraide == "Oui")

base = gdf_final['prct_bio'] if veut_terres else (1 - gdf_final['prct_bio'])

if veut_entraide:
    base = base * (1 + gdf_final['score_exploit']) / 2

gdf_final['score'] = base * (1 + gdf_final['score_ind']) / 2

# --- CARTE ---
st.markdown(f"### 🗺️ Cantons favorables")

# --- CARTE ---
st.markdown(f"### 🗺️ Cantons selon la part de bio")

# --- CARTE ---
st.markdown("### 🗺️ Cantons selon la part de bio")

# Création d'une palette séquentielle custom
# 0 → couleur claire, 0.1 → couleur jaune, 1 → couleur verte
custom_scale = [
    [0.0, "lightgray"],  # très faible
    [0.1, "yellow"],     # pivot à 10%
    [1.0, "green"]       # max
]

fig = px.choropleth_mapbox(
    gdf_final,
    geojson=gdf_final.__geo_interface__,
    locations=gdf_final.index,
    color='prct_bio',
    color_continuous_scale=custom_scale,
    range_color=[0, 1],
    hover_name="nom",
    hover_data={
        "code": True,
        "prct_bio": ":.2f",
        "terres_ab": ":.2f",
        "surfab": ":.2f",
        "nb_exploit": ":.0f"
    },
    mapbox_style="carto-positron",
    zoom=7,
    center={"lat": 49.9, "lon": 2.8},
    opacity=0.7
)

fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=700)
st.plotly_chart(fig, use_container_width=True)

# --- DEBUG ---
with st.expander("Voir les données brutes"):
    st.write(gdf_final[['nom', 'code', 'score', 'score_ind']].head())

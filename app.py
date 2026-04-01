import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import numpy as np

st.set_page_config(layout="wide", page_title="Carte Bio Hauts-de-France")
st.title("🚜 Outil d'aide à l'installation pour les exploitations en agriculture biologique - Hauts-de-France")

@st.cache_data
def load_data():
    # 1. Chargement du CSV Unique
    # Assurez-vous que le fichier s'appelle bien data.csv
    df = pd.read_csv('data.csv', sep=';', encoding='utf-8-sig', dtype=str)

    # Liste des colonnes numériques à traiter
    cols_num = [
        'score_nb_exploit', 'prct_SAU_bio', 'prct_gdculture', 
        'prct_elevage', 'score_global_elevage', 'score_global_gdculture'
    ]

    # Remplacement des virgules par des points et conversion en numérique
    for col in cols_num:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Reconstruction du code INSEE canton sur 5 caractères
    # Ex: '5919' -> '59' (département) + '019' (canton formaté sur 3 chiffres) -> '59019'
    df['canton_raw'] = df['Étiquettes de lignes'].astype(str).str.split('.').str[0].str.strip()
    df['dept'] = df['canton_raw'].str[:-2] # Récupère tout sauf les 2 derniers chiffres
    df['cant'] = df['canton_raw'].str[-2:].str.zfill(3) # Transforme les 2 derniers chiffres en 3 chiffres (ex: "14" -> "014")
    df['canton'] = (df['dept'] + df['cant']).str.zfill(5) # Rajoute le zéro devant si besoin (ex: "2014" -> "02014")

    # 2. Chargement Géo
    url_geojson = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"
    gdf_geo = gpd.read_file(url_geojson)
    gdf_geo['code'] = gdf_geo['code'].astype(str).str.strip()
    
    # Filtrer uniquement sur les Hauts-de-France
    gdf_geo = gdf_geo[gdf_geo['code'].str[:2].isin(['02', '59', '60', '62', '80'])].copy()

    return df, gdf_geo, cols_num

# Récupération des données
df_csv, gdf_geo, cols_num = load_data()

# --- JOINTURES ---
gdf_final = gdf_geo.merge(df_csv, left_on='code', right_on='canton', how='left')

# Remplir les valeurs manquantes (cantons sans données) par 0
for col in cols_num:
    gdf_final[col] = gdf_final[col].fillna(0)

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

# 1. Choix du score de base selon le type d'activité
if type_exploit == "Élevage":
    score_temp = gdf_final['score_global_elevage'].copy()
else:
    score_temp = gdf_final['score_global_gdculture'].copy()

# 2. Règle : Terres déjà converties ?
# "si oui : score_global... * 0.5 si prct_SAU_bio > 0.05"
if reprise == "Oui":
    masque_terres = gdf_final['prct_SAU_bio'] > 0.05
    # np.where(condition, valeur_si_vrai, valeur_si_faux)
    score_temp = np.where(masque_terres, score_temp * 0.5, score_temp)

# 3. Règle : Besoin d'entraide ?
# "si oui : résultat précédent * 0,5 si score_nb_exploit < 0,5"
if entraide == "Oui":
    masque_entraide = gdf_final['score_nb_exploit'] < 0.5
    score_temp = np.where(masque_entraide, score_temp * 0.5, score_temp)

# On plafonne à 1 et on empêche de descendre sous 0 pour l'affichage
gdf_final['score_final'] = np.clip(score_temp, 0, 1)


# --- CARTE ---
st.markdown(f"### 🗺️ Cantons favorables — {type_exploit}")

# Échelle de couleur personnalisée
custom_scale = [
    [0.0, "white"],
    [0.5, "yellow"],
    [1.0, "green"]
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
        "prct_SAU_bio": ":.2f",
        "score_nb_exploit": ":.2f",
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
    cols_to_show = ['nom', 'code', 'score_final', 'prct_SAU_bio', 'score_nb_exploit', 
                    'score_global_elevage', 'score_global_gdculture']
    st.dataframe(gdf_final[cols_to_show].head(10))

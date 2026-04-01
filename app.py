import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

st.set_page_config(page_title="Carte Surface AB", layout="wide")
st.title("🚜 Surface Agricole Biologique par Canton (Hauts-de-France)")

@st.cache_data
def load_data():
    # 1. CHARGEMENT DU CSV
    # On force le type 'str' pour ne pas perdre le 0 au début des codes
    df = pd.read_csv('cartetest.csv', sep=';', dtype={'canton': str})
    
    # Nettoyage des noms de colonnes (enlève espaces invisibles)
    df.columns = df.columns.str.strip()
    
    # Harmonisation : on renomme terre_ab en terres_ab si nécessaire
    if 'terre_ab' in df.columns:
        df = df.rename(columns={'terre_ab': 'terres_ab'})

    # Nettoyage des chiffres (remplace virgule par point)
    for col in ['surfab', 'terres_ab']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # CORRECTION CRUCIALE DU CODE CANTON : 
    # Le GeoJSON attend 4 chiffres (ex: 0219 pour Aisne, canton 19)
    df['canton'] = df['canton'].str.zfill(4)

    # 2. CHARGEMENT DU GÉOJSON DES CANTONS
    url_geojson = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"
    gdf_cantons = gpd.read_file(url_geojson)
    
    # Filtrage sur les départements des Hauts-de-France (02, 59, 60, 62, 80)
    gdf_cantons = gdf_cantons[gdf_cantons['code'].str[:2].isin(['02', '59', '60', '62', '80'])].copy()
    
    return df, gdf_cantons

with st.spinner("Génération de la carte..."):
    df_csv, gdf_geo = load_data()

# --- JOINTURE ---
# On fusionne le GeoJSON avec vos données CSV sur la base du code canton
gdf_final = gdf_geo.merge(df_csv, left_on='code', right_on='canton', how='left')
gdf_final['terres_ab'] = gdf_final['terres_ab'].fillna(0)
gdf_final['surfab'] = gdf_final['surfab'].fillna(0)

# --- CARTE PLOTLY ---
fig = px.choropleth_mapbox(
    gdf_final,
    geojson=gdf_final.__geo_interface__,
    locations=gdf_final.index,
    color='terres_ab',
    color_continuous_scale=["#ffffff", "#99d98c", "#1a7431"],
    hover_name="nom", # Nom du canton venant du GeoJSON
    hover_data={"canton": True, "terres_ab": True, "surfab": True},
    mapbox_style="carto-positron",
    zoom=7.5,
    center={"lat": 49.9, "lon": 2.8},
    opacity=0.8
)

fig.update_traces(marker_line_width=0.2, marker_line_color="gray")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=800)

st.plotly_chart(fig, use_container_width=True)

# Diagnostic en cas de besoin
if st.checkbox("Vérifier les données chargées"):
    st.write("Exemple de codes cantons après correction (doit être 0219, 5919...) :")
    st.write(df_csv['canton'].head())
    st.dataframe(df_csv)

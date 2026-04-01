import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

st.set_page_config(page_title="Carte AB", layout="wide")
st.title("🚜 Surface Agricole Biologique par Canton")

@st.cache_data
def load_data():
    # --- A. CHARGEMENT DU CSV ---
    # On lit le fichier sans imposer de séparateur (détection auto)
    df = pd.read_csv('cartetest.csv', sep=None, engine='python')
    
    # Nettoyage des noms de colonnes
    df.columns = df.columns.str.strip().str.lower()
    
    # On renomme 'terre_ab' (vu sur votre image) en 'terres_ab' (utilisé dans le code)
    if 'terre_ab' in df.columns:
        df = df.rename(columns={'terre_ab': 'terres_ab'})

    # NETTOYAGE DES CODES CANTONS (C'est ici que ça échouait)
    # On enlève les espaces, les ".0" et on rajoute le "0" devant si nécessaire (ex: 219 -> 0219)
    df['canton'] = df['canton'].astype(str).str.split('.').str[0].str.strip().str.zfill(4)

    # NETTOYAGE DES CHIFFRES
    for col in ['surfab', 'terres_ab']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # --- B. CHARGEMENT DU GEOJSON ---
    url_geojson = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"
    gdf_geo = gpd.read_file(url_geojson)
    
    # On nettoie aussi le code du GeoJSON pour être sûr du match
    gdf_geo['code'] = gdf_geo['code'].astype(str).str.strip().str.zfill(4)
    
    # Filtrage Hauts-de-France
    gdf_geo = gdf_geo[gdf_geo['code'].str[:2].isin(['02', '59', '60', '62', '80'])].copy()
    
    return df, gdf_geo

df_csv, gdf_geo = load_data()

# --- C. JOINTURE ---
# On fusionne le GeoJSON avec le CSV
gdf_final = gdf_geo.merge(df_csv, left_on='code', right_on='canton', how='left')

# On remplit les zones sans données par 0 pour éviter le "null"
gdf_final['terres_ab'] = gdf_final['terres_ab'].fillna(0)
gdf_final['surfab'] = gdf_final['surfab'].fillna(0)

# --- D. CARTE ---
fig = px.choropleth_mapbox(
    gdf_final,
    geojson=gdf_final.__geo_interface__,
    locations=gdf_final.index,
    color='terres_ab',
    color_continuous_scale="YlGn", # Dégradé Jaune -> Vert
    hover_name="nom", # Nom du canton (venant du GeoJSON)
    hover_data={
        "canton": True, 
        "terres_ab": ":.2f", # 2 chiffres après la virgule
        "surfab": ":.2f"
    },
    mapbox_style="carto-positron",
    zoom=7.5,
    center={"lat": 49.9, "lon": 2.8},
    opacity=0.8
)

fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=800)
st.plotly_chart(fig, use_container_width=True)

# --- E. DEBUG (Pour vous aider à vérifier) ---
if st.checkbox("Vérifier la correspondance des codes"):
    col1, col2 = st.columns(2)
    with col1:
        st.write("Codes dans votre CSV (5 premiers) :")
        st.write(df_csv['canton'].head().tolist())
    with col2:
        st.write("Codes dans le GeoJSON (5 premiers) :")
        st.write(gdf_geo['code'].head().tolist())

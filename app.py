import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

st.set_page_config(page_title="Carte Terres AB", layout="wide")
st.title("🚜 Surface des Terres en Agriculture Biologique par Canton")

@st.cache_data
def load_all_data():
    # --- 1. CHARGEMENT DES DONNÉES AGRICOLES ---
    # Ton nouveau fichier : canton;surfab;terres_ab
    df_csv = pd.read_csv('cartetest.csv', sep=';')
    # On s'assure que terres_ab est numérique
    df_csv['terres_ab'] = pd.to_numeric(df_csv['terres_ab'].astype(str).str.replace(',', '.'), errors='coerce')
    # On nettoie la colonne canton pour la jointure
    df_csv['canton'] = df_csv['canton'].astype(str).str.strip()

    # --- 2. CHARGEMENT DES LIMITES GÉOGRAPHIQUES (COMMUNES) ---
    url_geojson = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes-version-simplifiee.geojson"
    gdf_com = gpd.read_file(url_geojson)
    
    # Filtrage Hauts-de-France (Départements 60, 80, 02, 59, 62)
    gdf_com = gdf_com[gdf_com['code'].str[:2].isin(['60', '80', '02', '59', '62'])].copy()
    gdf_com['geometry'] = gdf_com.geometry.simplify(tolerance=0.002)

    # --- 3. MAPPING COMMUNES -> CANTONS (INSEE) ---
    url_insee = "https://www.insee.fr/fr/statistiques/fichier/7766585/v_commune_2024.csv"
    try:
        df_insee = pd.read_csv(url_insee)
        # Création du canton_id pour matcher avec ton CSV (ex: "Canton 60-1")
        # Ajuste ce format si tes cantons dans le CSV sont écrits différemment
        df_insee['canton_id'] = "Canton " + df_insee['DEP'].astype(str) + "-" + df_insee['CAN'].astype(str)
        df_map = df_insee[['COM', 'canton_id']].copy()
        df_map.columns = ['codeinseecommune', 'canton']
    except:
        # Solution de secours si l'INSEE est injoignable
        df_map = pd.DataFrame({'codeinseecommune': gdf_com['code'].unique()})
        df_map['canton'] = "Secteur " + df_map['codeinseecommune'].str[:3]

    # --- 4. CRÉATION DU FOND DE CARTE DES CANTONS (DISSOLVE) ---
    gdf_com_mapped = gdf_com.merge(df_map, left_on='code', right_on='codeinseecommune', how='inner')
    gdf_cantons = gdf_com_mapped.dissolve(by='canton').reset_index()

    return df_csv, gdf_cantons

with st.spinner("Chargement de la carte des cantons..."):
    df_agri, gdf_cantons = load_all_data()

# --- JOINTURE ET PRÉPARATION ---
# On fusionne tes données CSV avec les géométries des cantons
gdf_final = gdf_cantons.merge(df_agri, on='canton', how='left')
gdf_final['terres_ab'] = gdf_final['terres_ab'].fillna(0)
gdf_final = gdf_final.reset_index(drop=True)

# --- AFFICHAGE DE LA CARTE ---
fig = px.choropleth_mapbox(
    gdf_final,
    geojson=gdf_final.__geo_interface__, 
    locations=gdf_final.index,
    color='terres_ab', # On utilise terres_ab pour le dégradé
    color_continuous_scale=["#ffffff", "#99d98c", "#1a7431"], # Corrigé (plus de saut de ligne)
    hover_name="canton",
    hover_data={"terres_ab": True, "surfab": True},
    mapbox_style="carto-positron",
    zoom=7,
    center={"lat": 49.9, "lon": 2.8},
    opacity=0.7
)

fig.update_traces(marker_line_width=0.5, marker_line_color="white")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=700)

st.plotly_chart(fig, use_container_width=True)

# Optionnel : afficher les données
if st.checkbox("Afficher le tableau des données"):
    st.dataframe(df_agri)

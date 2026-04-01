import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
st.set_page_config(page_title="Carte Surface AB", layout="wide")
st.title("🌾 Évolution de la Surface Agricole Biologique (Hauts-de-France)")
@st.cache_data
def load_data():
    # --- 1. CHARGEMENT DES DONNÉES AGRICOLES (VOTRE CSV) ---
    df_csv = pd.read_csv('test_carte.csv', sep=';')
    df_csv['codeinseecommune'] = df_csv['codeinseecommune'].astype(str).str.zfill(5)

    # --- 2. CHARGEMENT DU FOND DE CARTE DES COMMUNES ---
    url_geojson = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes-version-simplifiee.geojson"
    gdf_com = gpd.read_file(url_geojson)
    # Filtrage Hauts-de-France et on réinitialise l'index immédiatement
    gdf_com = gdf_com[gdf_com['code'].str[:2].isin(['60', '80', '02', '59', '62'])].copy()
    gdf_com = gdf_com.reset_index(drop=True)
    gdf_com['geometry'] = gdf_com.geometry.simplify(tolerance=0.002)
    # --- 3. CHARGEMENT DES CORRESPONDANCES CANTONS (INSEE) ---
    url_insee = "https://www.insee.fr/fr/statistiques/fichier/7766585/v_commune_2024.csv"
    try:
        df_insee = pd.read_csv(url_insee)
        # Création d'un identifiant de canton unique (DEP + CAN)
        df_insee['canton_id'] = "Canton " + df_insee['DEP'].astype(str) + "-" + df_insee['CAN'].astype(str)
        df_map = df_insee[['COM', 'canton_id']].copy()
        df_map.columns = ['codeinseecommune', 'canton']
        df_map['codeinseecommune'] = df_map['codeinseecommune'].astype(str).str.zfill(5)
    except:
        df_map = pd.DataFrame({'codeinseecommune': gdf_com['code'].unique()})
        df_map['canton'] = "Secteur " + df_map['codeinseecommune'].str[:3]
    # --- 4. CRÉATION DU FOND DE CARTE DES CANTONS ---
    gdf_com_mapped = gdf_com.merge(df_map, left_on='code', right_on='codeinseecommune', how='inner')
    gdf_cantons = gdf_com_mapped.dissolve(by='canton').reset_index()
    return df_csv, gdf_com, gdf_cantons, df_map
with st.spinner("Initialisation des données..."):
    df_agri, gdf_communes, gdf_cantons, df_mapping = load_data()
# --- INTERFACE ---
st.sidebar.header("Paramètres")
annees_dispos = sorted(df_agri['annee'].dropna().unique().astype(int))
annee_choisie = st.sidebar.selectbox("Sélectionnez l'année :", annees_dispos)
echelle = st.sidebar.radio("Échelle :", ["Communes", "Cantons"])
# --- CALCULS ET JOINTURES ---
df_filtre = df_agri[df_agri['annee'] == annee_choisie].copy()
if echelle == "Communes":
    # On repart du fond de carte communes propre
    gdf_final = gdf_communes.merge(df_filtre, left_on='code', right_on='codeinseecommune', how='left')
    hover_name_col = "nom"
    hover_data_dict = {"code": True, "surfab": True}
else:
    # On repart du fond de carte cantons propre
    df_agri_cantons = df_filtre.merge(df_mapping, on='codeinseecommune', how='left')
    df_grouped = df_agri_cantons.groupby('canton', as_index=False)['surfab'].sum()
    gdf_final = gdf_cantons.merge(df_grouped, on='canton', how='left')
    hover_name_col = "canton"
    hover_data_dict = {"canton": False, "surfab": True}
# REMPLISSAGE DES VIDES ET RÉINITIALISATION CRUCIALE DE L'INDEX
gdf_final['surfab'] = gdf_final['surfab'].fillna(0)
gdf_final = gdf_final.reset_index(drop=True)
# --- CARTE ---
# On utilise gdf_final.__geo_interface__ pour être certain que Plotly voit les géométries
fig = px.choropleth_mapbox(
    gdf_final,
    geojson=gdf_final.__geo_interface__, 
    locations=gdf_final.index,
    color='surfab',
    color_continuous_scale=["white", "
#99d98c", "
#1a7431"],
    hover_name=hover_name_col,
    hover_data=hover_data_dict,
    mapbox_style="carto-positron",
    zoom=7,
    center={"lat": 49.9, "lon": 2.8},
    opacity=0.7
)
# Amélioration du tracé : on ajoute une bordure grise très fine pour voir les communes à 0
fig.update_traces(marker_line_width=0.1, marker_line_color="gray")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig, use_container_width=True)

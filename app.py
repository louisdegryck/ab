import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

# Configuration de la page Streamlit
st.set_page_config(page_title="Carte Surface AB", layout="wide")
st.title("🌾 Évolution de la Surface Agricole Biologique (Hauts-de-France)")

# 1. Fonction en cache pour ne charger les données lourdes qu'UNE SEULE FOIS
@st.cache_data
def load_data():
    # Chargement CSV
    df = pd.read_csv('test_carte.csv', sep=';')
    df['codeinseecommune'] = df['codeinseecommune'].astype(str).str.zfill(5)
    
    # Chargement GeoJSON
    url_geojson = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes-version-simplifiee.geojson"
    gdf = gpd.read_file(url_geojson)
    
    # Filtrage HDF et simplification (pour la rapidité d'affichage)
    departements_hdf = ['60', '80', '02', '59', '62']
    gdf_hdf = gdf[gdf['code'].str[:2].isin(departements_hdf)].copy()
    gdf_hdf = gdf_hdf.dropna(subset=['geometry'])
    gdf_hdf['geometry'] = gdf_hdf.geometry.simplify(tolerance=0.002, preserve_topology=True)
    
    return df, gdf_hdf

# On affiche un petit message de chargement pendant la lecture des données
with st.spinner("Chargement des données géographiques en cours..."):
    df_csv, gdf_communes = load_data()

# 2. Barre latérale (Sidebar) pour les interactions utilisateur
st.sidebar.header("Paramètres")
annees_dispos = sorted(df_csv['annee'].dropna().unique().astype(int))

# Remplacement du 'input()' par un menu déroulant très propre
annee_choisie = st.sidebar.selectbox("Sélectionnez l'année à afficher :", annees_dispos)

st.sidebar.markdown("---")
st.sidebar.info("Cette carte affiche la surface agricole utile en agriculture biologique par commune.")

# 3. Traitement des données selon l'année choisie
df_filtre = df_csv[df_csv['annee'] == annee_choisie]

# Jointure
gdf_merged = gdf_communes.merge(df_filtre, left_on='code', right_on='codeinseecommune', how='left')

# Gestion des NaN (vides) pour l'affichage en blanc
gdf_merged['surfab'] = gdf_merged['surfab'].fillna(0)
gdf_merged['annee'] = gdf_merged['annee'].fillna(annee_choisie)
gdf_merged = gdf_merged.reset_index(drop=True)

# Calcul du centre
bounds = gdf_merged.total_bounds
center_lon = (bounds[0] + bounds[2]) / 2
center_lat = (bounds[1] + bounds[3]) / 2

# 4. Création de la carte
with st.spinner(f"Génération de la carte pour {annee_choisie}..."):
    fig = px.choropleth_mapbox(
        gdf_merged,
        geojson=gdf_merged.geometry,
        locations=gdf_merged.index,
        color='surfab',               
        color_continuous_scale=["white", "#ffea00", "#7cb518", "#008000"], 
        hover_name="nom",
        hover_data={
            "code": True,
            "surfab": True, 
            "annee": True,
            "codeinseecommune": False    
        },
        mapbox_style="carto-positron",
        zoom=7.2,
        center={"lat": center_lat, "lon": center_lon},
        opacity=0.7                      
    )

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    # ---> NOUVEAUTÉ : Affichage spécifique pour Streamlit
    st.plotly_chart(fig, use_container_width=True)
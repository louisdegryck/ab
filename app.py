import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Carte Surface AB", layout="wide")
st.title("🌾 Surface Agricole Bio (Hauts-de-France)")

@st.cache_data
def load_data():
    # 1. DONNÉES AGRICOLES
    df_csv = pd.read_csv('test_carte.csv', sep=';')
    df_csv['codeinseecommune'] = df_csv['codeinseecommune'].astype(str).str.zfill(5)
    
    # 2. CARTE COMMUNES
    url_geojson = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes-version-simplifiee.geojson"
    gdf_com = gpd.read_file(url_geojson)
    gdf_com = gdf_com[gdf_com['code'].str[:2].isin(['60', '80', '02', '59', '62'])].copy()
    gdf_com['geometry'] = gdf_com.geometry.simplify(tolerance=0.002)

    # 3. CORRESPONDANCES CANTONS (INSEE)
    url_insee = "https://www.insee.fr/fr/statistiques/fichier/7766585/v_commune_2024.csv"
    try:
        df_insee = pd.read_csv(url_insee)
        # Création d'un nom de canton unique
        df_insee['canton_name'] = df_insee['LIBELLE'].astype(str)
        df_map = df_insee[['COM', 'canton_name']].copy()
        df_map.columns = ['codeinseecommune', 'canton']
        df_map['codeinseecommune'] = df_map['codeinseecommune'].astype(str).str.zfill(5)
    except:
        df_map = pd.DataFrame({'codeinseecommune': gdf_com['code'].unique()})
        df_map['canton'] = "Secteur " + df_map['codeinseecommune'].str[:3]

    # 4. CARTE CANTONS
    gdf_com_mapped = gdf_com.merge(df_map, left_on='code', right_on='codeinseecommune', how='inner')
    gdf_cantons = gdf_com_mapped.dissolve(by='canton').reset_index()

    return df_csv, gdf_com, gdf_cantons, df_map

with st.spinner("Chargement des données..."):
    df_agri, gdf_communes, gdf_cantons, df_mapping = load_data()

# --- SIDEBAR ---
st.sidebar.header("Paramètres")
annees_dispos = sorted(df_agri['annee'].dropna().unique().astype(int))
annee_choisie = st.sidebar.selectbox("Année :", annees_dispos)
echelle = st.sidebar.radio("Échelle :", ["Communes", "Cantons"])

# --- PRÉPARATION DES DONNÉES ---
df_filtre = df_agri[df_agri['annee'] == annee_choisie].copy()

if echelle == "Communes":
    gdf_final = gdf_communes.merge(df_filtre, left_on='code', right_on='codeinseecommune', how='left')
    location_col = "code" # On lie par le code INSEE
    feature_id = "properties.code"
    hover_name_col = "nom"
    line_w = 0.1
else:
    # Agrégation par canton
    df_agri_cantons = df_filtre.merge(df_mapping, on='codeinseecommune', how='left')
    df_grouped = df_agri_cantons.groupby('canton', as_index=False)['surfab'].sum()
    gdf_final = gdf_cantons.merge(df_grouped, on='canton', how='left')
    location_col = "canton" # On lie par le nom du canton
    feature_id = "properties.canton"
    hover_name_col = "canton"
    line_w = 1.5

gdf_final['surfab'] = gdf_final['surfab'].fillna(0)

# --- GÉNÉRATION DE LA CARTE ---
fig = px.choropleth_mapbox(
    gdf_final,
    geojson=gdf_final.__geo_interface__,
    locations=location_col,      # La colonne dans le tableau
    featureidkey=feature_id,     # Le chemin dans le GeoJSON
    color='surfab',
    color_continuous_scale="YlGn",
    hover_name=hover_name_col,
    mapbox_style="carto-positron",
    zoom=7,
    center={"lat": 49.9, "lon": 2.8},
    opacity=0.7
)

fig.update_traces(marker_line_width=line_w, marker_line_color="black")

# --- AJOUT DU TEXTE (Uniquement pour les Cantons) ---
if echelle == "Cantons":
    # On utilise representative_point pour être sûr que le texte est DANS la forme
    # et on extrait proprement les coordonnées
    points = gdf_final.geometry.representative_point()
    fig.add_trace(go.Scattermapbox(
        lat=points.y,
        lon=points.x,
        mode='text',
        text=gdf_final['canton'],
        textfont={"size": 10, "color": "black", "family": "Arial Black"},
        hoverinfo='none'
    ))

fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=700)
st.plotly_chart(fig, use_container_width=True)

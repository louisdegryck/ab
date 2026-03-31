import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Carte Bio HDF", layout="wide")

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data
def load_all_data():
    # 1. Votre CSV
    df = pd.read_csv('test_carte.csv', sep=';')
    df['codeinseecommune'] = df['codeinseecommune'].astype(str).str.zfill(5)
    
    # 2. Géo communes
    url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes-version-simplifiee.geojson"
    gdf = gpd.read_file(url)
    gdf = gdf[gdf['code'].str[:2].isin(['02', '59', '60', '62', '80'])].copy()
    gdf = gdf.reset_index(drop=True)
    
    # 3. Correspondance Cantons (INSEE)
    url_insee = "https://www.insee.fr/fr/statistiques/fichier/7766585/v_commune_2024.csv"
    try:
        df_insee = pd.read_csv(url_insee)
        df_insee['canton_name'] = df_insee['LIBELLE'].astype(str)
        df_map = df_insee[['COM', 'canton_name']].copy()
        df_map.columns = ['codeinseecommune', 'canton']
        df_map['codeinseecommune'] = df_map['codeinseecommune'].astype(str).str.zfill(5)
    except:
        df_map = pd.DataFrame({'codeinseecommune': gdf['code'].unique(), 'canton': 'Secteur Inconnu'})

    # 4. Fond de carte Cantons
    gdf_mapped = gdf.merge(df_map, left_on='code', right_on='codeinseecommune', how='left')
    gdf_can = gdf_mapped.dissolve(by='canton').reset_index()
    
    return df, gdf, gdf_can, df_map

df_agri, gdf_com, gdf_can, mapping = load_all_data()

# --- SIDEBAR ---
st.sidebar.title("Configuration")
annees = sorted(df_agri['annee'].unique())
annee = st.sidebar.selectbox("Année", annees)
echelle = st.sidebar.radio("Échelle", ["Communes", "Cantons"])

# --- PRÉPARATION ---
df_yr = df_agri[df_agri['annee'] == annee].copy()

if echelle == "Communes":
    # On prépare le tableau final
    gdf_disp = gdf_com.merge(df_yr, left_on='code', right_on='codeinseecommune', how='left')
    gdf_disp['surfab'] = gdf_disp['surfab'].fillna(0)
    h_name = "nom"
    l_width = 0.1
else:
    # Agrégation par canton
    df_m = df_yr.merge(mapping, on='codeinseecommune', how='left')
    df_g = df_m.groupby('canton')['surfab'].sum().reset_index()
    gdf_disp = gdf_can.merge(df_g, on='canton', how='left')
    gdf_disp['surfab'] = gdf_disp['surfab'].fillna(0)
    h_name = "canton"
    l_width = 1.2

# --- LE SECRET DE L'AFFICHAGE : RESET INDEX ---
# Plotly va lier le rang 0 du tableau au rang 0 du GeoJSON
gdf_disp = gdf_disp.reset_index(drop=True)

# --- DESSIN DE LA CARTE ---
fig = px.choropleth_mapbox(
    gdf_disp,
    geojson=gdf_disp.geometry, # On passe directement la colonne geometry
    locations=gdf_disp.index,   # On utilise l'index (0, 1, 2...)
    color='surfab',
    color_continuous_scale="YlGn",
    range_color=[0, gdf_disp['surfab'].max() if gdf_disp['surfab'].max() > 0 else 100],
    hover_name=h_name,
    mapbox_style="carto-positron",
    zoom=7,
    center={"lat": 49.9, "lon": 2.8},
    opacity=0.8
)

fig.update_traces(marker_line_width=l_width, marker_line_color="black")

# --- AJOUT DU TEXTE (Optionnel et sécurisé) ---
if echelle == "Cantons":
    try:
        # On utilise representative_point pour placer les noms
        pts = gdf_disp.geometry.representative_point()
        fig.add_trace(go.Scattermapbox(
            lat=pts.y, lon=pts.x, mode='text',
            text=gdf_disp['canton'],
            textfont={"size": 10, "color": "black", "family": "Arial Black"},
            hoverinfo='none'
        ))
    except:
        pass

fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=800)

# AFFICHAGE
st.plotly_chart(fig, use_container_width=True)

# PETIT DEBUG (Affiche le tableau en bas pour vérifier que les données sont là)
if st.checkbox("Voir les données brutes"):
    st.write(gdf_disp.drop(columns='geometry').head())

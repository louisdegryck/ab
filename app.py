import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Carte Bio HDF", layout="wide")
st.set_page_config(page_title="Carte Surface AB", layout="wide")
st.title("🌾 Évolution de la Surface Agricole Biologique (Hauts-de-France)")

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data
def load_all_data():
    # 1. Votre CSV
    df = pd.read_csv('test_carte.csv', sep=';')
    df['codeinseecommune'] = df['codeinseecommune'].astype(str).str.zfill(5)
def load_data():
    # --- 1. CHARGEMENT DES DONNÉES AGRICOLES (VOTRE CSV) ---
    df_csv = pd.read_csv('test_carte.csv', sep=';')
    df_csv['codeinseecommune'] = df_csv['codeinseecommune'].astype(str).str.zfill(5)

    # 2. Géo communes
    url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes-version-simplifiee.geojson"
    gdf = gpd.read_file(url)
    gdf = gdf[gdf['code'].str[:2].isin(['02', '59', '60', '62', '80'])].copy()
    gdf = gdf.reset_index(drop=True)
    
    # 3. Correspondance Cantons (INSEE)
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
        df_insee['canton_name'] = df_insee['LIBELLE'].astype(str)
        df_map = df_insee[['COM', 'canton_name']].copy()
        # Création d'un identifiant de canton unique (DEP + CAN)
        df_insee['canton_id'] = "Canton " + df_insee['DEP'].astype(str) + "-" + df_insee['CAN'].astype(str)
        df_map = df_insee[['COM', 'canton_id']].copy()
        df_map.columns = ['codeinseecommune', 'canton']
        df_map['codeinseecommune'] = df_map['codeinseecommune'].astype(str).str.zfill(5)
    except:
        df_map = pd.DataFrame({'codeinseecommune': gdf['code'].unique(), 'canton': 'Secteur Inconnu'})
        df_map = pd.DataFrame({'codeinseecommune': gdf_com['code'].unique()})
        df_map['canton'] = "Secteur " + df_map['codeinseecommune'].str[:3]

    # 4. Fond de carte Cantons
    gdf_mapped = gdf.merge(df_map, left_on='code', right_on='codeinseecommune', how='left')
    gdf_can = gdf_mapped.dissolve(by='canton').reset_index()
    
    return df, gdf, gdf_can, df_map
    # --- 4. CRÉATION DU FOND DE CARTE DES CANTONS ---
    gdf_com_mapped = gdf_com.merge(df_map, left_on='code', right_on='codeinseecommune', how='inner')
    gdf_cantons = gdf_com_mapped.dissolve(by='canton').reset_index()

df_agri, gdf_com, gdf_can, mapping = load_all_data()
    return df_csv, gdf_com, gdf_cantons, df_map

# --- SIDEBAR ---
st.sidebar.title("Configuration")
annees = sorted(df_agri['annee'].unique())
annee = st.sidebar.selectbox("Année", annees)
echelle = st.sidebar.radio("Échelle", ["Communes", "Cantons"])
with st.spinner("Initialisation des données..."):
    df_agri, gdf_communes, gdf_cantons, df_mapping = load_data()

# --- PRÉPARATION ---
df_yr = df_agri[df_agri['annee'] == annee].copy()
# --- INTERFACE ---
st.sidebar.header("Paramètres")
annees_dispos = sorted(df_agri['annee'].dropna().unique().astype(int))
annee_choisie = st.sidebar.selectbox("Sélectionnez l'année :", annees_dispos)
echelle = st.sidebar.radio("Échelle :", ["Communes", "Cantons"])

# --- CALCULS ET JOINTURES ---
df_filtre = df_agri[df_agri['annee'] == annee_choisie].copy()

if echelle == "Communes":
    # On prépare le tableau final
    gdf_disp = gdf_com.merge(df_yr, left_on='code', right_on='codeinseecommune', how='left')
    gdf_disp['surfab'] = gdf_disp['surfab'].fillna(0)
    h_name = "nom"
    l_width = 0.1
    # On repart du fond de carte communes propre
    gdf_final = gdf_communes.merge(df_filtre, left_on='code', right_on='codeinseecommune', how='left')
    hover_name_col = "nom"
    hover_data_dict = {"code": True, "surfab": True}
else:
    # Agrégation par canton
    df_m = df_yr.merge(mapping, on='codeinseecommune', how='left')
    df_g = df_m.groupby('canton')['surfab'].sum().reset_index()
    gdf_disp = gdf_can.merge(df_g, on='canton', how='left')
    gdf_disp['surfab'] = gdf_disp['surfab'].fillna(0)
    h_name = "canton"
    l_width = 1.2
    # On repart du fond de carte cantons propre
    df_agri_cantons = df_filtre.merge(df_mapping, on='codeinseecommune', how='left')
    df_grouped = df_agri_cantons.groupby('canton', as_index=False)['surfab'].sum()
    gdf_final = gdf_cantons.merge(df_grouped, on='canton', how='left')
    hover_name_col = "canton"
    hover_data_dict = {"canton": False, "surfab": True}

# --- LE SECRET DE L'AFFICHAGE : RESET INDEX ---
# Plotly va lier le rang 0 du tableau au rang 0 du GeoJSON
gdf_disp = gdf_disp.reset_index(drop=True)
# REMPLISSAGE DES VIDES ET RÉINITIALISATION CRUCIALE DE L'INDEX
gdf_final['surfab'] = gdf_final['surfab'].fillna(0)
gdf_final = gdf_final.reset_index(drop=True)

# --- DESSIN DE LA CARTE ---
# --- CARTE ---
# On utilise gdf_final.__geo_interface__ pour être certain que Plotly voit les géométries
fig = px.choropleth_mapbox(
    gdf_disp,
    geojson=gdf_disp.geometry, # On passe directement la colonne geometry
    locations=gdf_disp.index,   # On utilise l'index (0, 1, 2...)
    gdf_final,
    geojson=gdf_final.__geo_interface__, 
    locations=gdf_final.index,
    color='surfab',
    color_continuous_scale="YlGn",
    range_color=[0, gdf_disp['surfab'].max() if gdf_disp['surfab'].max() > 0 else 100],
    hover_name=h_name,
    color_continuous_scale=["white", "#99d98c", "#1a7431"],
    hover_name=hover_name_col,
    hover_data=hover_data_dict,
    mapbox_style="carto-positron",
    zoom=7,
    center={"lat": 49.9, "lon": 2.8},
    opacity=0.8
    opacity=0.7
)

fig.update_traces(marker_line_width=l_width, marker_line_color="black")
# Amélioration du tracé : on ajoute une bordure grise très fine pour voir les communes à 0
fig.update_traces(marker_line_width=0.1, marker_line_color="gray")

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
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig, use_container_width=True)

# PETIT DEBUG (Affiche le tableau en bas pour vérifier que les données sont là)
if st.checkbox("Voir les données brutes"):
    st.write(gdf_disp.drop(columns='geometry').head())

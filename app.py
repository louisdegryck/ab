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
    # Filtrage Hauts-de-France
    gdf_com = gdf_com[gdf_com['code'].str[:2].isin(['60', '80', '02', '59', '62'])].copy()
    gdf_com['geometry'] = gdf_com.geometry.simplify(tolerance=0.002)

    # --- 3. CHARGEMENT DES CORRESPONDANCES CANTONS (OPEN DATA INSEE) ---
    # On télécharge directement la table officielle de l'INSEE (COG 2024)
    url_insee = "https://www.insee.fr/fr/statistiques/fichier/7766585/v_commune_2024.csv"
    try:
        df_insee = pd.read_csv(url_insee)
        # On garde le code commune (COM), le code département (DEP) et le code canton (CAN)
        # Note : Un canton n'est unique que si on combine son code avec celui du département
        df_insee['canton_id'] = "Canton " + df_insee['DEP'].astype(str) + "-" + df_insee['CAN'].astype(str)
        df_map = df_insee[['COM', 'canton_id']].copy()
        df_map.columns = ['codeinseecommune', 'canton']
        df_map['codeinseecommune'] = df_map['codeinseecommune'].astype(str).str.zfill(5)
    except:
        # En cas de problème de connexion au site INSEE
        st.error("Impossible de récupérer la liste officielle des cantons. Utilisation d'une fallback.")
        df_map = pd.DataFrame({'codeinseecommune': gdf_com['code'].unique()})
        df_map['canton'] = "Secteur " + df_map['codeinseecommune'].str[:3]

    # --- 4. CRÉATION DU FOND DE CARTE DES CANTONS (DISSOLVE) ---
    gdf_com_mapped = gdf_com.merge(df_map, left_on='code', right_on='codeinseecommune', how='inner')
    gdf_cantons = gdf_com_mapped.dissolve(by='canton').reset_index()

    return df_csv, gdf_com, gdf_cantons, df_map

with st.spinner("Initialisation des données (INSEE + Géo)..."):
    df_agri, gdf_communes, gdf_cantons, df_mapping = load_data()

# --- INTERFACE ---
st.sidebar.header("Paramètres")
annees_dispos = sorted(df_agri['annee'].dropna().unique().astype(int))
annee_choisie = st.sidebar.selectbox("Sélectionnez l'année :", annees_dispos)
echelle = st.sidebar.radio("Échelle :", ["Communes", "Cantons"])

# --- CALCULS ---
df_filtre = df_agri[df_agri['annee'] == annee_choisie].copy()

if echelle == "Communes":
    gdf_final = gdf_communes.merge(df_filtre, left_on='code', right_on='codeinseecommune', how='left')
    hover_name_col = "nom"
    hover_data_dict = {"code": True, "surfab": True}
else:
    # On ajoute les infos cantons aux données de surfab
    df_agri_cantons = df_filtre.merge(df_mapping, on='codeinseecommune', how='left')
    df_grouped = df_agri_cantons.groupby('canton', as_index=False)['surfab'].sum()
    gdf_final = gdf_cantons.merge(df_grouped, on='canton', how='left')
    hover_name_col = "canton"
    hover_data_dict = {"canton": False, "surfab": True}

gdf_final['surfab'] = gdf_final['surfab'].fillna(0)
gdf_final = gdf_final.reset_index(drop=True)

# --- CARTE ---
fig = px.choropleth_mapbox(
    gdf_final,
    geojson=gdf_final.geometry,
    locations=gdf_final.index,
    color='surfab',
    color_continuous_scale=["white", "#7cb518", "#008000"],
    hover_name=hover_name_col,
    hover_data=hover_data_dict,
    mapbox_style="carto-positron",
    zoom=7.2,
    center={"lat": 49.9, "lon": 2.8},
    opacity=0.7
)

fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig, use_container_width=True)

import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

st.set_page_config(page_title="Carte AB", layout="wide")
st.title("🚜 Surface Agricole Biologique par Canton")

@st.cache_data
def load_data():
    try:
        # 1. Lecture du CSV (Détection automatique du séparateur)
        df = pd.read_csv('cartetest.csv', sep=None, engine='python', dtype=str)
        
        # 2. NETTOYAGE RADICAL DES COLONNES
        # On enlève les espaces, on met en minuscule, on supprime les caractères invisibles (BOM)
        df.columns = [c.strip().lower().encode('ascii', 'ignore').decode('ascii') for c in df.columns]
        
        # 3. VERIFICATION DES COLONNES
        # Si 'canton' n'est pas trouvé, on prend la 1ère colonne du fichier par défaut
        if 'canton' not in df.columns:
            st.warning(f"Colonne 'canton' non trouvée. Colonnes détectées : {list(df.columns)}. Utilisation de la 1ère colonne.")
            df = df.rename(columns={df.columns[0]: 'canton'})
        
        # On cherche 'terres_ab' ou 'terre_ab'
        col_data = [c for c in df.columns if 'terre' in c]
        if col_data:
            df = df.rename(columns={col_data[0]: 'terres_ab'})
        else:
            st.error("Impossible de trouver une colonne contenant le mot 'terre'.")

        # 4. NETTOYAGE DES DONNÉES
        # Canton : on force 4 chiffres (ex: 219 -> 0219)
        df['canton'] = df['canton'].astype(str).str.split('.').str[0].str.strip().str.zfill(4)
        
        # Valeurs : on remplace virgule par point et on force en nombre
        df['terres_ab'] = df['terres_ab'].astype(str).str.replace(',', '.')
        df['terres_ab'] = pd.to_numeric(df['terres_ab'], errors='coerce').fillna(0)

        # 5. CHARGEMENT DU GEOJSON
        url_geojson = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"
        gdf_geo = gpd.read_file(url_geojson)
        gdf_geo['code'] = gdf_geo['code'].astype(str).str.zfill(4)
        
        # Filtrage Hauts-de-France
        gdf_geo = gdf_geo[gdf_geo['code'].str[:2].isin(['02', '59', '60', '62', '80'])].copy()
        
        return df, gdf_geo

    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")
        return None, None

df_csv, gdf_geo = load_data()

if df_csv is not None:
    # JOINTURE
    gdf_final = gdf_geo.merge(df_csv, left_on='code', right_on='canton', how='left')
    gdf_final['terres_ab'] = gdf_final['terres_ab'].fillna(0)

    # CARTE
    fig = px.choropleth_mapbox(
        gdf_final,
        geojson=gdf_final.__geo_interface__,
        locations=gdf_final.index,
        color='terres_ab',
        color_continuous_scale="YlGn",
        hover_name="nom",
        hover_data={"canton": True, "terres_ab": True},
        mapbox_style="carto-positron",
        zoom=7.5,
        center={"lat": 49.9, "lon": 2.8},
        opacity=0.8
    )

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=800)
    st.plotly_chart(fig, use_container_width=True)

    # Zone de Debug
    if st.checkbox("Afficher les données pour vérification"):
        st.write("Colonnes identifiées :", df_csv.columns.tolist())
        st.dataframe(df_csv.head())

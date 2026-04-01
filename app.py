import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🚜 Carte Surface Agricole Biologique - Hauts-de-France")

@st.cache_data
def load_data():
    # 1. LECTURE DU CSV
    df = pd.read_csv('cartetest.csv', sep=';', encoding='utf-8-sig', dtype=str)
    
    # 2. ON FORCE LES NOMS DE COLONNES PAR POSITION
    df = df.iloc[:, [0, 1, 2]] 
    df.columns = ['canton', 'surfab', 'terre_ab']
    
    # 3. NETTOYAGE DES CHIFFRES
    for col in ['surfab', 'terre_ab']:
        df[col] = df[col].astype(str).str.replace(',', '.')
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 4. RECONSTRUCTION DU CODE CANTON EN 5 CHIFFRES
    # Ex: "5919" → dept="59", cant="019" → "59019"
    # Ex: "219"  → dept="2",  cant="019" → "02019"
    df['canton_raw'] = df['canton'].astype(str).str.split('.').str[0].str.strip()
    df['dept'] = df['canton_raw'].str[:-2]           # Tout sauf les 2 derniers chiffres
    df['cant'] = df['canton_raw'].str[-2:].str.zfill(3)  # Les 2 derniers, paddés à 3
    df['canton'] = (df['dept'] + df['cant']).str.zfill(5) # Assemblage + zfill pour "02xxx"
    
    # 5. CHARGEMENT DU FOND DE CARTE
    url_geojson = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"
    gdf_geo = gpd.read_file(url_geojson)
    gdf_geo['code'] = gdf_geo['code'].astype(str).str.strip()
    
    # Filtrage Hauts-de-France (02, 59, 60, 62, 80)
    gdf_geo = gdf_geo[gdf_geo['code'].str[:2].isin(['02', '59', '60', '62', '80'])].copy()
    
    return df, gdf_geo

# Chargement
df_csv, gdf_geo = load_data()

# 6. JOINTURE (Merge)
gdf_final = gdf_geo.merge(df_csv, left_on='code', right_on='canton', how='left')
gdf_final['terre_ab'] = gdf_final['terre_ab'].fillna(0)
gdf_final['surfab'] = gdf_final['surfab'].fillna(0)

# 7. AFFICHAGE DE LA CARTE
fig = px.choropleth_mapbox(
    gdf_final,
    geojson=gdf_final.__geo_interface__,
    locations=gdf_final.index,
    color='terre_ab',
    color_continuous_scale="YlGn",
    hover_name="nom",
    hover_data={
        "code": True, 
        "terre_ab": ":.2f", 
        "surfab": ":.2f"
    },
    mapbox_style="carto-positron",
    zoom=7.5,
    center={"lat": 49.9, "lon": 2.8},
    opacity=0.8
)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=800)
st.plotly_chart(fig, use_container_width=True)

# 8. TABLEAU DE VÉRIFICATION
st.subheader("Données détectées")
st.write("Si la carte est blanche, compare les codes 'code' (GeoJSON) et 'canton' (Ton CSV) ci-dessous :")
c1, c2 = st.columns(2)
with c1:
    st.write("Ton CSV nettoyé :")
    st.dataframe(df_csv[['canton', 'surfab', 'terre_ab']].head(10))
with c2:
    st.write("Le GeoJSON (Attendu) :")
    st.dataframe(gdf_geo[['code', 'nom']].head(10))

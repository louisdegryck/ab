import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🚜 Carte Surface Agricole Biologique - Hauts-de-France")

@st.cache_data
def load_data():
    df = pd.read_csv('cartetest.csv', sep=';', encoding='utf-8-sig', dtype=str)
    df = df.iloc[:, [0, 1, 2]] 
    df.columns = ['canton', 'surfab', 'terre_ab']
    
    for col in ['surfab', 'terre_ab']:
        df[col] = df[col].astype(str).str.replace(',', '.')
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df['canton_raw'] = df['canton'].astype(str).str.split('.').str[0].str.strip()
    df['dept'] = df['canton_raw'].str[:-2]
    df['cant'] = df['canton_raw'].str[-2:].str.zfill(3)
    df['canton'] = (df['dept'] + df['cant']).str.zfill(5)
    
    url_geojson = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"
    gdf_geo = gpd.read_file(url_geojson)
    gdf_geo['code'] = gdf_geo['code'].astype(str).str.strip()
    gdf_geo = gdf_geo[gdf_geo['code'].str[:2].isin(['02', '59', '60', '62', '80'])].copy()
    
    return df, gdf_geo

# Chargement
df_csv, gdf_geo = load_data()

# JOINTURE
gdf_final = gdf_geo.merge(df_csv, left_on='code', right_on='canton', how='left')
gdf_final['terre_ab'] = gdf_final['terre_ab'].fillna(0)
gdf_final['surfab'] = gdf_final['surfab'].fillna(0)

# ─────────────────────────────────────────────
# CARTE 1 : carte originale (toujours visible)
# ─────────────────────────────────────────────
st.subheader("🗺️ Carte des surfaces agricoles biologiques")

fig1 = px.choropleth_mapbox(
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
fig1.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=800)
st.plotly_chart(fig1, use_container_width=True, key="carte1")

# ─────────────────────────────────────────────
# CARTE 2 : carte avec question reprise terres
# ─────────────────────────────────────────────
st.subheader("🌱 Souhaitez-vous reprendre des terres converties ?")

reprise = st.radio(
    "",
    options=["Oui", "Non"],
    horizontal=True
)

color_scale = "YlGn" if reprise == "Oui" else "YlGn_r"

fig2 = px.choropleth_mapbox(
    gdf_final,
    geojson=gdf_final.__geo_interface__,
    locations=gdf_final.index,
    color='terre_ab',
    color_continuous_scale=color_scale,
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
fig2.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=800)
st.plotly_chart(fig2, use_container_width=True, key="carte2")

# ─────────────────────────────────────────────
# TABLEAU DE VÉRIFICATION
# ─────────────────────────────────────────────
st.subheader("Données détectées")
c1, c2 = st.columns(2)
with c1:
    st.write("Ton CSV nettoyé :")
    st.dataframe(df_csv[['canton', 'surfab', 'terre_ab']].head(10))
with c2:
    st.write("Le GeoJSON (Attendu) :")
    st.dataframe(gdf_geo[['code', 'nom']].head(10))

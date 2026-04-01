import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🚜 Carte Surface Agricole Biologique - Hauts-de-France")

@st.cache_data
def load_data():
    # 1. LECTURE DU CSV (On force le séparateur ; et l'encodage Excel)
    # On utilise utf-8-sig pour ignorer les caractères invisibles en début de fichier
    df = pd.read_csv('cartetest.csv', sep=';', encoding='utf-8-sig', dtype=str)
    
    # 2. ON FORCE LES NOMS DE COLONNES PAR POSITION (pour éviter KeyError)
    # Peu importe comment elles s'appellent dans ton fichier :
    # La 1ère sera 'canton', la 2ème 'surfab', la 3ème 'terre_ab'
    df = df.iloc[:, [0, 1, 2]] 
    df.columns = ['canton', 'surfab', 'terre_ab']
    
    # 3. NETTOYAGE DES CHIFFRES
    for col in ['surfab', 'terre_ab']:
        df[col] = df[col].astype(str).str.replace(',', '.')
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
      # 4. NETTOYAGE ET RECONSTRUCTION DES CODES CANTONS
# Ton CSV : "5919" = dept "59" + canton "19" → on reconstruit "59019" (5 chiffres)
df['canton_raw'] = df['canton'].astype(str).str.split('.').str[0].str.strip()

# Le département = les 2 premiers chiffres, le canton = le reste, paddé à 3 chiffres
df['dept'] = df['canton_raw'].str[:-2]          # "59" depuis "5919"
df['cant'] = df['canton_raw'].str[-2:].str.zfill(3)  # "019" depuis "19"
df['canton'] = df['dept'] + df['cant']           # "59019"

# 5. CHARGEMENT DU FOND DE CARTE
url_geojson = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"
gdf_geo = gpd.read_file(url_geojson)
gdf_geo['code'] = gdf_geo['code'].astype(str).str.strip()  # déjà en 5 chiffres

# Filtrage Hauts-de-France (02, 59, 60, 62, 80)
gdf_geo = gdf_geo[gdf_geo['code'].str[:2].isin(['02', '59', '60', '62', '80'])].copy()
    
    # Filtrage Hauts-de-France (02, 59, 60, 62, 80)
    gdf_geo = gdf_geo[gdf_geo['code'].str[:2].isin(['02', '59', '60', '62', '80'])].copy()
    
    return df, gdf_geo

# Chargement
df_csv, gdf_geo = load_data()

# 6. JOINTURE (Merge)
gdf_final = gdf_geo.merge(df_csv, left_on='code', right_on='canton', how='left')

# On remplit les vides par 0 pour que la carte se colore
gdf_final['terre_ab'] = gdf_final['terre_ab'].fillna(0)
gdf_final['surfab'] = gdf_final['surfab'].fillna(0)

# 7. AFFICHAGE DE LA CARTE
fig = px.choropleth_mapbox(
    gdf_final,
    geojson=gdf_final.__geo_interface__,
    locations=gdf_final.index,
    color='terre_ab',
    color_continuous_scale="YlGn",
    hover_name="nom", # Nom du canton venant du GeoJSON (ex: Roye)
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

# 8. TABLEAU DE VERIFICATION (En bas de page)
st.subheader("Données détectées")
st.write("Si la carte est blanche, compare les codes 'code' (GeoJSON) et 'canton' (Ton CSV) ci-dessous :")
c1, c2 = st.columns(2)
with c1:
    st.write("Ton CSV nettoyé :")
    st.dataframe(df_csv.head(10))
with c2:
    st.write("Le GeoJSON (Attendu) :")
    st.dataframe(gdf_geo[['code', 'nom']].head(10))

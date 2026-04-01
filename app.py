pip install streamlit folium streamlit-folium pandas

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests

# Configuration de la page Streamlit
st.set_page_config(page_title="Carte Terres AB par Canton", layout="wide")

st.title("Répartition des Terres en Agriculture Biologique par Canton")

# 1. Chargement des données CSV
# On force le type 'str' pour la colonne canton pour garder les codes intacts (ex: 0101)
@st.cache_data
def load_data():
    df = pd.read_csv('cartetest.csv', dtype={'canton': str})
    return df

df = load_data()

# 2. Lien vers le GeoJSON des cantons (Source: France-GeoJSON / Grégoire David)
# Ce fichier contient la propriété 'code' pour chaque canton
geojson_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"

# 3. Création de la carte
m = folium.Map(location=[46.5, 2.5], zoom_start=6, tiles='CartoDB positron')

# 4. Ajout de la couche Choropleth (le dégradé)
choropleth = folium.Choropleth(
    geo_data=geojson_url,
    data=df,
    columns=['canton', 'terres_ab'],
    key_on='feature.properties.code',  # On se base sur le CODE du canton
    fill_color='YlGn',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Terres en Agriculture Biologique (ha)',
    nan_fill_color='white',
    highlight=True
).add_to(m)

# 5. Ajout d'une info-bulle interactive (Tooltip)
# On récupère le geojson pour pouvoir lier les données au survol
geojson_data = requests.get(geojson_url).json()

# On crée un dictionnaire pour mapper Code -> Valeur terres_ab afin de l'afficher au survol
ab_dict = df.set_index('canton')['terres_ab'].to_dict()

for feature in geojson_data['features']:
    code = feature['properties']['code']
    feature['properties']['valeur_ab'] = ab_dict.get(code, "Pas de donnée")

folium.GeoJson(
    geojson_data,
    style_function=lambda x: {'fillColor': 'transparent', 'color': 'transparent'},
    tooltip=folium.GeoJsonTooltip(
        fields=['code', 'nom', 'valeur_ab'],
        aliases=['Code Canton:', 'Nom:', 'Terres AB (ha):'],
        localize=True
    )
).add_to(m)

# 6. Affichage dans Streamlit
st_folium(m, width='100%', height=600)

# Affichage du tableau de données en dessous (optionnel)
if st.checkbox("Afficher le tableau des données"):
    st.write(df)

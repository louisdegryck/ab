import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests

st.set_page_config(page_title="Carte Terres AB", layout="wide")

@st.cache_data
def load_data():
    # Lecture robuste du CSV
    try:
        df = pd.read_csv('cartetest.csv', dtype={'canton': str}, sep=None, engine='python')
        if df['terres_ab'].dtype == object:
            df['terres_ab'] = df['terres_ab'].astype(str).str.replace(',', '.').astype(float)
        return df
    except Exception as e:
        st.error(f"Erreur lors de la lecture du CSV : {e}")
        return None

df = load_data()

if df is not None:
    st.title("🚜 Terres en Agriculture Biologique par Canton")

    # GeoJSON distant (Codes cantons français)
    geojson_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"

    # Création de la carte
    m = folium.Map(location=[46.5, 2.5], zoom_start=6, tiles='CartoDB positron')

    # Choropleth
    folium.Choropleth(
        geo_data=geojson_url,
        data=df,
        columns=['canton', 'terres_ab'],
        key_on='feature.properties.code', 
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Terres AB (ha)',
        nan_fill_color='white'
    ).add_to(m)

    st_folium(m, width=1000, height=600)
    
    if st.checkbox("Voir les données brutes"):
        st.dataframe(df)

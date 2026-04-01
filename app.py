import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Carte Terres AB", layout="wide")

@st.cache_data
def load_data():
    try:
        # Lecture du CSV
        df = pd.read_csv('cartetest.csv', sep=None, engine='python', dtype={'canton': str})
        
        # Nettoyage des noms de colonnes
        df.columns = df.columns.str.strip().str.lower()
        
        # On identifie les colonnes
        col_canton = [c for c in df.columns if 'canton' in c][0]
        col_data = [c for c in df.columns if 'terres' in c][0]
        
        df = df.rename(columns={col_canton: 'canton', col_data: 'terres_ab'})

        # --- CORRECTION DES CODES CANTONS ---
        # On s'assure que le code fait au moins 4 caractères (ex: 101 devient 0101)
        df['canton'] = df['canton'].astype(str).str.strip().str.zfill(4)
        
        # Nettoyage des données numériques
        if df['terres_ab'].dtype == object:
            df['terres_ab'] = df['terres_ab'].str.replace(',', '.').astype(float)
        
        return df
    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
        return None

df = load_data()

if df is not None:
    st.title("🚜 Carte des Terres AB par Canton")

    # GeoJSON des cantons
    geojson_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"

    # Création de la carte
    m = folium.Map(location=[46.5, 2.5], zoom_start=6, tiles='CartoDB positron')

    # Choropleth
    choropleth = folium.Choropleth(
        geo_data=geojson_url,
        data=df,
        columns=['canton', 'terres_ab'],
        key_on='feature.properties.code', # On lie sur le champ 'code' du GeoJSON
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.4,
        legend_name='Terres AB (ha)',
        nan_fill_color='white'
    ).add_to(m)

    # Affichage de la carte
    st_folium(m, width="100%", height=600)

    # --- ZONE DE DIAGNOSTIC (pour comprendre pourquoi ça ne s'affiche pas) ---
    with st.expander("Diagnostic des données"):
        st.write("Voici les 5 premiers codes cantons que Python lit dans votre CSV :")
        st.write(df['canton'].head().tolist())
        st.write("Si ces codes ne font pas 4 chiffres (ex: 0101) ou 5 chiffres (ex: 97101), la carte restera vide.")
        st.dataframe(df)

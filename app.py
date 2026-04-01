import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Carte Terres AB", layout="wide")

@st.cache_data
def load_data():
    try:
        # 1. Lecture flexible du CSV (détection automatique du séparateur)
        df = pd.read_csv('cartetest.csv', sep=None, engine='python', dtype=str)
        
        # 2. NETTOYAGE DES COLONNES : on enlève les espaces et on met tout en minuscule
        df.columns = df.columns.str.strip().str.lower()
        
        # 3. Vérification des colonnes nécessaires
        # On cherche une colonne qui contient 'canton' et une qui contient 'terres'
        col_canton = [c for c in df.columns if 'canton' in c]
        col_data = [c for c in df.columns if 'terres' in c]
        
        if not col_canton or not col_data:
            st.error(f"Colonnes introuvables. Colonnes détectées : {list(df.columns)}")
            return None
        
        # On renomme pour que le reste du code fonctionne
        df = df.rename(columns={col_canton[0]: 'canton', col_data[0]: 'terres_ab'})
        
        # 4. Conversion numérique propre
        df['terres_ab'] = df['terres_ab'].str.replace(',', '.').astype(float)
        
        return df
    except Exception as e:
        st.error(f"Erreur lors de la lecture : {e}")
        return None

df = load_data()

if df is not None:
    st.title("🚜 Terres en Agriculture Biologique par Canton")

    # Lien GeoJSON
    geojson_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"

    # Création de la carte
    m = folium.Map(location=[46.5, 2.5], zoom_start=6, tiles='CartoDB positron')

    # Choropleth
    folium.Choropleth(
        geo_data=geojson_url,
        data=df,
        columns=['canton', 'terres_ab'],
        key_on='feature.properties.code', # On utilise le code canton
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Terres AB (ha)',
        nan_fill_color='#f5f5f5' # Gris très clair pour les zones sans données
    ).add_to(m)

    st_folium(m, width="100%", height=600)
    
    # Debug pour t'aider à voir ce que Python lit
    if st.checkbox("Afficher les données lues par l'application"):
        st.write("Colonnes identifiées :", df.columns.tolist())
        st.dataframe(df)

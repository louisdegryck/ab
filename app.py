import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np

st.set_page_config(layout="wide", page_title="Carte Terres AB")

@st.cache_data
def load_data():
    try:
        # 1. Lecture avec le séparateur point-virgule
        df = pd.read_csv('cartetest.csv', sep=';', dtype={'canton': str})
        
        # 2. Nettoyage des noms de colonnes
        df.columns = df.columns.str.strip()
        
        # 3. NETTOYAGE FORCÉ de la colonne terres_ab
        # On convertit en texte, on remplace la virgule par le point
        df['terres_ab'] = df['terres_ab'].astype(str).str.replace(',', '.')
        
        # On transforme tout ce qui n'est pas un chiffre en NaN (Not a Number)
        df['terres_ab'] = pd.to_numeric(df['terres_ab'], errors='coerce')
        
        # On SUPPRIME les lignes où terres_ab est vide (NaN) 
        # C'est l'étape qui corrige ton erreur TypeError
        df = df.dropna(subset=['terres_ab'])
        
        # 4. Nettoyage de la colonne canton
        df['canton'] = df['canton'].astype(str).str.strip()
        
        return df
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {e}")
        return None

st.title("🚜 Surface des Terres en Agriculture Biologique par Canton")

df = load_data()

if df is not None and not df.empty:
    # URL GeoJSON officiel
    geojson_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"

    # Création de la carte
    m = folium.Map(location=[46.5, 2.5], zoom_start=6, tiles='CartoDB positron')

    # Choropleth (le dégradé)
    try:
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

        # Affichage
        st_folium(m, width="100%", height=600)
        
    except Exception as e:
        st.error(f"Erreur lors de la création du dégradé : {e}")
        st.info("Vérifiez que la colonne 'terres_ab' contient bien des chiffres.")

    # Tableau de contrôle
    with st.expander("Vérifier les données après nettoyage"):
        st.write(f"Nombre de lignes valides trouvées : {len(df)}")
        st.dataframe(df)
else:
    st.warning("Aucune donnée valide n'a pu être lue. Vérifiez le format de votre fichier CSV.")

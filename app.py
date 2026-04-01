import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests

st.set_page_config(layout="wide")

# 1. Chargement et nettoyage strict
@st.cache_data
def load_data():
    try:
        # Lecture du CSV (on force canton en texte)
        df = pd.read_csv('cartetest.csv', sep=None, engine='python', dtype={'canton': str})
        
        # On ne garde que les colonnes nécessaires pour éviter les erreurs
        # On s'assure que les noms sont exacts
        df.columns = df.columns.str.strip()
        
        # Conversion forcée de terres_ab en nombre (gestion des virgules)
        df['terres_ab'] = df['terres_ab'].astype(str).str.replace(',', '.')
        df['terres_ab'] = pd.to_numeric(df['terres_ab'], errors='coerce')
        
        # On supprime les lignes vides
        df = df.dropna(subset=['canton', 'terres_ab'])
        
        return df
    except Exception as e:
        st.error(f"Erreur lecture CSV : {e}")
        return None

df = load_data()

st.title("Carte des Terres AB par Canton")

if df is not None:
    # URL du GeoJSON (Source officielle simplifiée)
    geojson_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"
    
    # Création de la carte centrée sur la France
    m = folium.Map(location=[46.5, 2.5], zoom_start=6, tiles='CartoDB positron')

    # Création du calque de couleur
    choropleth = folium.Choropleth(
        geo_data=geojson_url,
        data=df,
        columns=['canton', 'terres_ab'],
        key_on='feature.properties.code',  # C'est ici que le lien se fait avec le JSON
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Terres AB (ha)',
        nan_fill_color='white' # Si le code ne correspond pas, la zone reste blanche
    ).add_to(m)

    # Affichage dans Streamlit
    st_folium(m, width=1200, height=600)

    # --- SECTION DE DÉBOGAGE (TRÈS IMPORTANTE) ---
    st.divider()
    st.subheader("Vérification de la correspondance (Debug)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Tes données (CSV)")
        st.write("Voici les codes 'canton' que tu fournis :")
        st.dataframe(df[['canton', 'terres_ab']].head(10))

    with col2:
        st.write("### Codes attendus (GeoJSON)")
        st.write("Pour que ça marche, tes codes doivent être comme ceux-là :")
        # On récupère juste un bout du JSON pour montrer les codes à l'utilisateur
        try:
            resp = requests.get(geojson_url).json()
            codes_exemple = [f["properties"]["code"] for f in resp["features"][:10]]
            st.write(codes_exemple)
        except:
            st.write("Impossible de charger l'exemple du JSON")

    st.info("💡 SI LES CODES NE SE RESSEMBLENT PAS : La carte ne peut pas faire le lien. "
            "Par exemple, si ton CSV dit '1' et le JSON dit '3001', la zone ne se colorera pas.")

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np

st.set_page_config(page_title="Carte Terres AB", layout="wide")

@st.cache_data
def load_data():
    try:
        # 1. Lecture brute
        df = pd.read_csv('cartetest.csv', sep=None, engine='python', dtype=str)
        
        # 2. Nettoyage noms de colonnes
        df.columns = df.columns.str.strip().str.lower()
        col_canton = [c for c in df.columns if 'canton' in c][0]
        col_data = [c for c in df.columns if 'terres' in c][0]
        df = df.rename(columns={col_canton: 'canton', col_data: 'terres_ab'})

        # 3. NETTOYAGE CRITIQUE DES DONNÉES NUMÉRIQUES
        # On remplace la virgule par le point, et on force en numérique
        # 'errors=coerce' transformera tout ce qui n'est pas un chiffre en NaN (vide)
        df['terres_ab'] = df['terres_ab'].astype(str).str.replace(',', '.')
        df['terres_ab'] = pd.to_numeric(df['terres_ab'], errors='coerce')

        # 4. Suppression des lignes où terres_ab est vide ou invalide
        df = df.dropna(subset=['terres_ab'])

        # 5. Formatage des codes cantons (ex: 101 -> 0101)
        df['canton'] = df['canton'].astype(str).str.strip().str.zfill(4)
        
        return df
    except Exception as e:
        st.error(f"Erreur lors de la préparation des données : {e}")
        return None

df = load_data()

if df is not None and not df.empty:
    st.title("🚜 Répartition des Terres en Agriculture Biologique")

    geojson_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"

    # Création de la carte
    m = folium.Map(location=[46.5, 2.5], zoom_start=6, tiles='CartoDB positron')

    # Choropleth
    try:
        folium.Choropleth(
            geo_data=geojson_url,
            data=df,
            columns=['canton', 'terres_ab'],
            key_on='feature.properties.code',
            fill_color='YlGn',
            fill_opacity=0.7,
            line_opacity=0.3,
            legend_name='Terres AB (ha)',
            nan_fill_color='white'
        ).add_to(m)

        st_folium(m, width="100%", height=600)
    except Exception as e:
        st.error(f"Erreur d'affichage de la carte : {e}")
        st.info("Cela arrive souvent si les valeurs numériques sont incorrectes.")

    # Tableau de vérification
    with st.expander("Vérifier les données nettoyées"):
        st.write(f"Nombre de lignes valides : {len(df)}")
        st.dataframe(df)
else:
    st.warning("Le fichier a été lu, mais aucune donnée numérique valide n'a été trouvée dans la colonne 'terres_ab'.")

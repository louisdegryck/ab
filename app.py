import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests

st.set_page_config(layout="wide")

@st.cache_data
def load_data():
    try:
        # 1. Lecture automatique du séparateur (sep=None)
        # On désactive l'indexation automatique pour éviter les décalages
        df = pd.read_csv('cartetest.csv', sep=None, engine='python')
        
        # 2. NETTOYAGE RADICAL des noms de colonnes
        # On enlève les espaces, on met en minuscule, on nettoie les caractères invisibles
        df.columns = [str(c).strip().lower().replace('ï»¿', '') for c in df.columns]
        
        # 3. VERIFICATION : Si 'canton' n'est toujours pas là, on cherche la colonne 0
        if 'canton' not in df.columns:
            st.error(f"Colonne 'canton' introuvable ! Colonnes détectées : {list(df.columns)}")
            # On essaie de forcer le nom de la première colonne
            df = df.rename(columns={df.columns[0]: 'canton'})
            st.warning(f"J'ai utilisé la colonne '{df.columns[0]}' comme colonne 'canton'")

        # 4. Idem pour terres_ab
        if 'terres_ab' not in df.columns:
             # On cherche une colonne qui contient le mot 'terres'
             cols_terres = [c for c in df.columns if 'terres' in c]
             if cols_terres:
                 df = df.rename(columns={cols_terres[0]: 'terres_ab'})

        # 5. Conversion des nombres (remplace la virgule par le point)
        df['terres_ab'] = df['terres_ab'].astype(str).str.replace(',', '.')
        df['terres_ab'] = pd.to_numeric(df['terres_ab'], errors='coerce')
        
        # 6. Suppression des lignes vides
        df = df.dropna(subset=['canton', 'terres_ab'])
        
        # 7. Forcer les codes cantons en TEXTE (important pour le lien avec le JSON)
        df['canton'] = df['canton'].astype(str).str.strip()
        
        return df
    except Exception as e:
        st.error(f"Erreur lors de l'ouverture du fichier : {e}")
        return None

st.title("🚜 Carte des Terres AB par Canton")

df = load_data()

if df is not None:
    # URL GeoJSON Cantons
    geojson_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"

    # Création de la carte
    m = folium.Map(location=[46.5, 2.5], zoom_start=6, tiles='CartoDB positron')

    # Choropleth
    folium.Choropleth(
        geo_data=geojson_url,
        data=df,
        columns=['canton', 'terres_ab'],
        key_on='feature.properties.code',  # Lien par CODE (ex: 3001)
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Surface Terres AB (ha)',
        nan_fill_color='white'
    ).add_to(m)

    st_folium(m, width="100%", height=600)

    # Aide au diagnostic si la carte reste blanche
    with st.expander("Diagnostic des données"):
        st.write("Colonnes lues :", list(df.columns))
        st.write("Aperçu des données :")
        st.dataframe(df.head())
        st.info("Note : Si les zones ne se colorent pas, vérifie si tes codes cantons (ex: 1) correspondent au format du GeoJSON (ex: 3001).")

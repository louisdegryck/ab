import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide", page_title="Carte Terres AB")

@st.cache_data
def load_data():
    # On lit le fichier avec le séparateur ';' spécifié
    # On force 'canton' en texte (string) pour ne pas perdre les zéros (ex: 0101)
    df = pd.read_csv('cartetest.csv', sep=';', dtype={'canton': str})
    
    # Nettoyage des noms de colonnes (au cas où il y aurait des espaces invisibles)
    df.columns = df.columns.str.strip()
    
    # Nettoyage de la colonne terres_ab (remplace la virgule par un point si besoin)
    if df['terres_ab'].dtype == object:
        df['terres_ab'] = df['terres_ab'].str.replace(',', '.').astype(float)
    
    # On s'assure que la colonne canton est bien propre
    df['canton'] = df['canton'].str.strip()
    
    return df

st.title("🚜 Surface des Terres en Agriculture Biologique par Canton")

df = load_data()

if df is not None:
    # URL GeoJSON officiel des cantons français
    geojson_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"

    # 1. Création de la carte de base
    m = folium.Map(location=[46.5, 2.5], zoom_start=6, tiles='CartoDB positron')

    # 2. Ajout du dégradé (Choropleth)
    folium.Choropleth(
        geo_data=geojson_url,
        data=df,
        columns=['canton', 'terres_ab'],
        key_on='feature.properties.code',  # Liaison par le CODE du canton (ex: 3001)
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Terres AB (ha)',
        nan_fill_color='white'
    ).add_to(m)

    # 3. Affichage de la carte
    st_folium(m, width="100%", height=600)

    # --- Zone de vérification (Debug) ---
    with st.expander("Vérifier les données lues dans le fichier"):
        st.write("Colonnes détectées :", df.columns.tolist())
        st.dataframe(df)
        st.info("💡 Si la carte reste blanche : vérifiez que vos codes dans la colonne 'canton' "
                "font 4 ou 5 chiffres (ex: 3001 pour le Gard). Si ce sont des noms, contactez-moi.")

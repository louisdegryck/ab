import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🚜 Carte Surface Agricole Biologique - Hauts-de-France")

@st.cache_data
def load_data():
    df = pd.read_csv('cartetest.csv', sep=';', encoding='utf-8-sig', dtype=str)
    df = df.iloc[:, [0, 1, 2, 3, 4]]
    df.columns = ['canton', 'surfab', 'terres_ab', 'nb_exploit', 'score_exploit']

    for col in ['surfab', 'terres_ab', 'nb_exploit', 'score_exploit']:
        df[col] = df[col].astype(str).str.replace(',', '.')
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['canton_raw'] = df['canton'].astype(str).str.split('.').str[0].str.strip()
    df['dept'] = df['canton_raw'].str[:-2]
    df['cant'] = df['canton_raw'].str[-2:].str.zfill(3)
    df['canton'] = (df['dept'] + df['cant']).str.zfill(5)

    url_geojson = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"
    gdf_geo = gpd.read_file(url_geojson)
    gdf_geo['code'] = gdf_geo['code'].astype(str).str.strip()
    gdf_geo = gdf_geo[gdf_geo['code'].str[:2].isin(['02', '59', '60', '62', '80'])].copy()

    return df, gdf_geo

# Chargement
df_csv, gdf_geo = load_data()

# JOINTURE
gdf_final = gdf_geo.merge(df_csv, left_on='code', right_on='canton', how='left')
gdf_final['terres_ab']    = gdf_final['terres_ab'].fillna(0)
gdf_final['score_exploit'] = gdf_final['score_exploit'].fillna(0)
gdf_final['surfab']       = gdf_final['surfab'].fillna(0)
gdf_final['nb_exploit']   = gdf_final['nb_exploit'].fillna(0)

# ─────────────────────────────────────────────
# QUESTIONS
# ─────────────────────────────────────────────
st.subheader("🌱 Vos préférences")
col1, col2 = st.columns(2)

with col1:
    reprise = st.radio(
        "Souhaitez-vous reprendre des terres déjà converties en agriculture biologique ?",
        options=["Oui", "Non"],
        horizontal=True,
        key="q1"
    )

with col2:
    entraide = st.radio(
        "Souhaitez-vous travailler en entraide ?",
        options=["Oui", "Non"],
        horizontal=True,
        key="q2"
    )

# ─────────────────────────────────────────────
# CALCUL DU SCORE COMPOSITE
# ─────────────────────────────────────────────
# terres_ab est toujours la base
# score_exploit amplifie si entraide=Oui, sinon aucun impact

if veut_terres and veut_entraide:
    # Entraide amplifie les terres converties
    gdf_final['score'] = gdf_final['terres_ab'] * (1 + gdf_final['score_exploit']) / 2

elif veut_terres and not veut_entraide:
    # Entraide n'a pas d'impact, on affiche juste terres_ab
    gdf_final['score'] = gdf_final['terres_ab']

elif not veut_terres and veut_entraide:
    # On inverse terres_ab, entraide amplifie
    gdf_final['score'] = (1 - gdf_final['terres_ab']) * (1 + gdf_final['score_exploit']) / 2

else:  # Les deux Non
    # On inverse terres_ab, entraide n'a pas d'impact
    gdf_final['score'] = 1 - gdf_final['terres_ab']
    
# ─────────────────────────────────────────────
# TITRE DYNAMIQUE selon les réponses
# ─────────────────────────────────────────────
labels = []
if reprise == "Oui":
    labels.append("terres converties disponibles")
else:
    labels.append("sans terres converties")
if entraide == "Oui":
    labels.append("avec entraide")
else:
    labels.append("sans entraide")

st.markdown(f"### 🗺️ Cantons favorables : {' · '.join(labels)}")

# ─────────────────────────────────────────────
# AFFICHAGE DE LA CARTE
# ─────────────────────────────────────────────
fig = px.choropleth_mapbox(
    gdf_final,
    geojson=gdf_final.__geo_interface__,
    locations=gdf_final.index,
    color='score',
    color_continuous_scale="YlGn",
    range_color=[0, 1],
    hover_name="nom",
    hover_data={
        "code": True,
        "terres_ab": ":.2f",
        "score_exploit": ":.2f",
        "surfab": ":.2f",
        "nb_exploit": ":.0f",
        "score": ":.2f"
    },
    mapbox_style="carto-positron",
    zoom=7.5,
    center={"lat": 49.9, "lon": 2.8},
    opacity=0.8
)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=800)
st.plotly_chart(fig, use_container_width=True, key="carte_principale")

# ─────────────────────────────────────────────
# TABLEAU DE VÉRIFICATION
# ─────────────────────────────────────────────
st.subheader("Données détectées")
c1, c2 = st.columns(2)
with c1:
    st.write("Ton CSV nettoyé :")
    st.dataframe(df_csv[['canton', 'surfab', 'terres_ab', 'score_exploit']].head(10))
with c2:
    st.write("Le GeoJSON (Attendu) :")
    st.dataframe(gdf_geo[['code', 'nom']].head(10))

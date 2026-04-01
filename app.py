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

    # CHARGEMENT DU 2e CSV
    df_ind = pd.read_csv('industries_cantons.csv', sep='\t', encoding='utf-8-sig', dtype=str)
    df_ind.columns = ['canton_ind', 'nb_silos', 'nb_transfo_gc', 'nb_abattoirs', 'nb_laiteries', 'nb_transfo_viande']

    for col in ['nb_silos', 'nb_transfo_gc', 'nb_abattoirs', 'nb_laiteries', 'nb_transfo_viande']:
        df_ind[col] = df_ind[col].astype(str).str.replace(',', '.')
        df_ind[col] = pd.to_numeric(df_ind[col], errors='coerce').fillna(0)

    df_ind['canton_raw'] = df_ind['canton_ind'].astype(str).str.split('.').str[0].str.strip()
    df_ind['dept'] = df_ind['canton_raw'].str[:-2]
    df_ind['cant'] = df_ind['canton_raw'].str[-2:].str.zfill(3)
    df_ind['canton_ind'] = (df_ind['dept'] + df_ind['cant']).str.zfill(5)

    url_geojson = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"
    gdf_geo = gpd.read_file(url_geojson)
    gdf_geo['code'] = gdf_geo['code'].astype(str).str.strip()
    gdf_geo = gdf_geo[gdf_geo['code'].str[:2].isin(['02', '59', '60', '62', '80'])].copy()

    return df, df_ind, gdf_geo

# Chargement
df_csv, df_ind, gdf_geo = load_data()

# JOINTURE principale
gdf_final = gdf_geo.merge(df_csv, left_on='code', right_on='canton', how='left')
gdf_final['terres_ab']     = gdf_final['terres_ab'].fillna(0)
gdf_final['score_exploit'] = gdf_final['score_exploit'].fillna(0)
gdf_final['surfab']        = gdf_final['surfab'].fillna(0)
gdf_final['nb_exploit']    = gdf_final['nb_exploit'].fillna(0)

# JOINTURE industries
gdf_final = gdf_final.merge(df_ind, left_on='code', right_on='canton_ind', how='left')
for col in ['nb_silos', 'nb_transfo_gc', 'nb_abattoirs', 'nb_laiteries', 'nb_transfo_viande']:
    gdf_final[col] = gdf_final[col].fillna(0)

# ─────────────────────────────────────────────
# QUESTIONS
# ─────────────────────────────────────────────
st.subheader("🌱 Vos préférences")
col1, col2, col3 = st.columns(3)

with col1:
    reprise = st.radio(
        "Souhaitez-vous reprendre des terres converties ?",
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

with col3:
    type_exploit = st.radio(
        "Quel type d'exploitation souhaitez-vous ?",
        options=["Élevage", "Grande culture"],
        horizontal=True,
        key="q3"
    )

# ─────────────────────────────────────────────
# SCORE INDUSTRIE (normalisé entre 0 et 1)
# ─────────────────────────────────────────────
if type_exploit == "Élevage":
    raw_ind = gdf_final['nb_abattoirs'] + gdf_final['nb_laiteries'] + gdf_final['nb_transfo_viande']
else:
    raw_ind = gdf_final['nb_silos'] + gdf_final['nb_transfo_gc']

# Normalisation min-max pour ramener entre 0 et 1
ind_min, ind_max = raw_ind.min(), raw_ind.max()
if ind_max > ind_min:
    gdf_final['score_ind'] = (raw_ind - ind_min) / (ind_max - ind_min)
else:
    gdf_final['score_ind'] = 0

# ─────────────────────────────────────────────
# CALCUL DU SCORE COMPOSITE
# ─────────────────────────────────────────────
veut_terres   = reprise   == "Oui"
veut_entraide = entraide  == "Oui"

# Base terres_ab selon reprise
if veut_terres:
    base = gdf_final['terres_ab']
else:
    base = 1 - gdf_final['terres_ab']

# Amplification entraide
if veut_entraide:
    base = base * (1 + gdf_final['score_exploit']) / 2

# Amplification industrie (toujours active, amplifie le gradient)
gdf_final['score'] = base * (1 + gdf_final['score_ind']) / 2

# ─────────────────────────────────────────────
# TITRE DYNAMIQUE
# ─────────────────────────────────────────────
labels = []
labels.append("terres converties" if veut_terres else "sans terres converties")
labels.append("avec entraide" if veut_entraide else "sans entraide")
labels.append("élevage" if type_exploit == "Élevage" else "grande culture")
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
        "score_ind": ":.2f",
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
c1, c2, c3 = st.columns(3)
with c1:
    st.write("CSV agricole :")
    st.dataframe(df_csv[['canton', 'surfab', 'terres_ab', 'score_exploit']].head(10))
with c2:
    st.write("CSV industries :")
    st.dataframe(df_ind[['canton_ind', 'nb_silos', 'nb_abattoirs', 'nb_laiteries']].head(10))
with c3:
    st.write("GeoJSON :")
    st.dataframe(gdf_geo[['code', 'nom']].head(10))

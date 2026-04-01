import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🚜 Carte Surface Agricole Biologique - Hauts-de-France")

@st.cache_data
def load_data():
    # ---------------------------------------------------------
    # CHARGEMENT DU 1er CSV (Agricole)
    # ---------------------------------------------------------
    df = pd.read_csv('cartetest.csv', sep=';', encoding='utf-8-sig', dtype=str)
    df = df.iloc[:, :5] # Sécurité : on garde uniquement les 5 premières colonnes
    df.columns = ['canton', 'surfab', 'terres_ab', 'nb_exploit', 'score_exploit']

    for col in ['surfab', 'terres_ab', 'nb_exploit', 'score_exploit']:
        df[col] = df[col].astype(str).str.replace(',', '.')
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['canton_raw'] = df['canton'].astype(str).str.split('.').str[0].str.strip()
    df['dept'] = df['canton_raw'].str[:-2]
    df['cant'] = df['canton_raw'].str[-2:].str.zfill(3)
    df['canton'] = (df['dept'] + df['cant']).str.zfill(5)

    # ---------------------------------------------------------
    # CHARGEMENT DU 2e CSV (Industries)
    # ---------------------------------------------------------
    # CORRECTION : On utilise sep=';' et on limite aux 6 premières colonnes
    df_ind = pd.read_csv('industries_cantons.csv', sep=';', encoding='utf-8-sig', dtype=str)
    df_ind = df_ind.iloc[:, :6]
    df_ind.columns = ['canton_ind', 'nb_silos', 'nb_transfo_gc', 'nb_abattoirs', 'nb_laiteries', 'nb_transfo_viande']

    for col in ['nb_silos', 'nb_transfo_gc', 'nb_abattoirs', 'nb_laiteries', 'nb_transfo_viande']:
        df_ind[col] = df_ind[col].astype(str).str.replace(',', '.')
        df_ind[col] = pd.to_numeric(df_ind[col], errors='coerce').fillna(0)

    df_ind['canton_raw'] = df_ind['canton_ind'].astype(str).str.split('.').str[0].str.strip()
    df_ind['dept'] = df_ind['canton_raw'].str[:-2]
    df_ind['cant'] = df_ind['canton_raw'].str[-2:].str.zfill(3)
    df_ind['canton_ind'] = (df_ind['dept'] + df_ind['cant']).str.zfill(5)

    # ---------------------------------------------------------
    # CHARGEMENT DU GEOJSON
    # ---------------------------------------------------------
    url_geojson = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"
    gdf_geo = gpd.read_file(url_geojson)
    gdf_geo['code'] = gdf_geo['code'].astype(str).str.strip()
    gdf_geo = gdf_geo[gdf_geo['code'].str[:2].isin(['02', '59', '60', '62', '80'])].copy()

    return df, df_ind, gdf_geo

# Exécution du chargement
df_csv, df_ind, gdf_geo = load_data()

# =============================================================
# JOINTURES ET NETTOYAGE DES DONNÉES
# =============================================================

# JOINTURE principale
gdf_final = gdf_geo.merge(df_csv, left_on='code', right_on='canton', how='left')
# CORRECTION : On force la conversion en nombres mathématiques pour éviter l'erreur TypeError
for col in ['terres_ab', 'score_exploit', 'surfab', 'nb_exploit']:
    gdf_final[col] = pd.to_numeric(gdf_final[col], errors='coerce').fillna(0)

# JOINTURE industries
gdf_final = gdf_final.merge(df_ind, left_on='code', right_on='canton_ind', how='left')
# CORRECTION : Idem, on force les colonnes industrielles en nombres
for col in ['nb_silos', 'nb_transfo_gc', 'nb_abattoirs', 'nb_laiteries', 'nb_transfo_viande']:
    gdf_final[col] = pd.to_numeric(gdf_final[col], errors='coerce').fillna(0)


# =============================================================
# QUESTIONS UTILISATEUR (INTERFACE)
# =============================================================
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

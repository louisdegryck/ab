import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import numpy as np

# --- CONFIG PAGE ---
st.set_page_config(layout="wide", page_title="BioStart – Hauts-de-France")

# --- CSS PERSONNALISÉ ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

/* Reset & fond général */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #f5f2eb;
    color: #1a2e1a;
}

/* Fond de l'app */
.stApp {
    background-color: #f5f2eb;
}

/* Header */
.main-header {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 2rem 0 1rem 0;
    border-bottom: 2px solid #2d5a1b;
    margin-bottom: 2rem;
}

.main-header img {
    height: 64px;
    width: auto;
}

.main-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    color: #1a2e1a;
    line-height: 1.2;
    margin: 0;
}

.main-subtitle {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    color: #4a7a2e;
    font-weight: 400;
    margin: 0;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* Bloc préférences */
.preferences-block {
    background: #ffffff;
    border-radius: 16px;
    padding: 1.8rem 2rem;
    margin-bottom: 2rem;
    border: 1px solid #d4e8c2;
    box-shadow: 0 2px 12px rgba(45,90,27,0.06);
}

.preferences-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.2rem;
    color: #2d5a1b;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Labels des radios */
.stRadio > label {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    color: #1a2e1a !important;
    margin-bottom: 0.4rem !important;
}

/* Boutons radio */
.stRadio > div {
    gap: 8px;
}

.stRadio > div > label {
    background: #f0f7e8;
    border: 1.5px solid #c2dba8;
    border-radius: 8px;
    padding: 6px 16px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: #2d5a1b !important;
    transition: all 0.2s ease;
    cursor: pointer;
}

.stRadio > div > label:hover {
    background: #ddf0c4;
    border-color: #2d5a1b;
}

/* Titre carte */
.map-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.4rem;
    color: #1a2e1a;
    margin: 1.5rem 0 0.8rem 0;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid #c2dba8;
}

/* Badge activité */
.badge {
    display: inline-block;
    background: #2d5a1b;
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 3px 12px;
    border-radius: 20px;
    margin-left: 10px;
    vertical-align: middle;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* Légende active */
.legend-pills {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}
.pill {
    font-size: 0.78rem;
    font-weight: 500;
    padding: 4px 12px;
    border-radius: 20px;
    border: 1.5px solid;
}
.pill-active {
    background: #e8f5d8;
    border-color: #2d5a1b;
    color: #2d5a1b;
}
.pill-inactive {
    background: #f5f2eb;
    border-color: #c2dba8;
    color: #7a9a6a;
}

/* Expander debug */
.streamlit-expanderHeader {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    color: #4a7a2e !important;
}

/* Séparateur */
hr {
    border: none;
    border-top: 1px solid #d4e8c2;
    margin: 1.5rem 0;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #f5f2eb; }
::-webkit-scrollbar-thumb { background: #c2dba8; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# --- CHARGEMENT DONNÉES ---
@st.cache_data
def load_data():
    df = pd.read_csv('data.csv', sep=';', encoding='utf-8-sig', dtype=str)

    cols_num = [
        'prct_SAU_normalise', 'prct_gdculture',
        'prct_elevage', 'nb_exploit_normalise',
        'score_global_elevage', 'score_global_gdculture'
    ]

    for col in cols_num:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['canton_raw'] = df['Étiquettes de lignes'].astype(str).str.split('.').str[0].str.strip()
    df['dept'] = df['canton_raw'].str[:-2]
    df['cant'] = df['canton_raw'].str[-2:].str.zfill(3)
    df['canton'] = (df['dept'] + df['cant']).str.zfill(5)

    url_geojson = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/cantons-version-simplifiee.geojson"
    gdf_geo = gpd.read_file(url_geojson)
    gdf_geo['code'] = gdf_geo['code'].astype(str).str.strip()
    gdf_geo = gdf_geo[gdf_geo['code'].str[:2].isin(['02', '59', '60', '62', '80'])].copy()

    return df, gdf_geo, cols_num

df_csv, gdf_geo, cols_num = load_data()

# --- JOINTURES ---
gdf_final = gdf_geo.merge(df_csv, left_on='code', right_on='canton', how='left')
for col in cols_num:
    gdf_final[col] = gdf_final[col].fillna(0)


# --- HEADER AVEC LOGO ---
try:
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        st.image("logo_biostart.png", width=90)
    with col_title:
        st.markdown("""
            <p class="main-subtitle">Outil d'aide à l'installation · Agriculture Biologique</p>
            <p class="main-title">Hauts-de-France — Cartographie des opportunités</p>
        """, unsafe_allow_html=True)
except:
    st.markdown("""
        <p class="main-subtitle">Outil d'aide à l'installation · Agriculture Biologique</p>
        <p class="main-title">Hauts-de-France — Cartographie des opportunités</p>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)


# --- INTERFACE UTILISATEUR ---
st.markdown("""
<div class="preferences-title">🌿 Définissez vos critères</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    type_exploit = st.radio(
        "🌾 Type d'activité",
        ["Élevage", "Grande culture"],
        index=None,  # Aucun coché par défaut
        key="q3"
    )

with col2:
    entraide = st.radio(
        "🤝 Besoin d'entraide ?",
        ["Oui", "Non"],
        index=None,  # Aucun coché par défaut
        key="q2"
    )

with col3:
    reprise = st.radio(
        "🌱 Terres déjà converties ?",
        ["Oui", "Non"],
        index=None,  # Aucun coché par défaut
        key="q1"
    )

st.markdown("<hr>", unsafe_allow_html=True)

# --- CALCULS (uniquement si type_exploit sélectionné) ---
if type_exploit is None:
    st.markdown("""
    <div style="
        text-align: center;
        padding: 4rem 2rem;
        color: #7a9a6a;
        font-family: 'DM Serif Display', serif;
        font-size: 1.3rem;
        font-style: italic;
    ">
        Sélectionnez un type d'activité pour afficher la carte
    </div>
    """, unsafe_allow_html=True)

else:
    alpha = 1.0

    # Score de base
    if type_exploit == "Élevage":
        score_base = gdf_final['prct_elevage'].copy().values
    else:
        score_base = gdf_final['prct_gdculture'].copy().values

    # Effet progressif Terres converties
    if reprise == "Oui":
        E_terres = gdf_final['prct_SAU_normalise'].values
        score_base = score_base * (1 + alpha * (E_terres - 0.5))

    # Effet progressif Entraide
    if entraide == "Oui":
        E_entraide = gdf_final['nb_exploit_normalise'].values
        score_base = score_base * (1 + alpha * (E_entraide - 0.5))

    gdf_final['score_final'] = np.clip(score_base, 0, 1)

    # --- TITRE + PILLS ACTIVES ---
    pills_html = f'<span class="pill pill-active">📍 {type_exploit}</span>'
    if entraide == "Oui":
        pills_html += '<span class="pill pill-active">🤝 Entraide activée</span>'
    elif entraide == "Non":
        pills_html += '<span class="pill pill-inactive">🤝 Entraide non requise</span>'
    if reprise == "Oui":
        pills_html += '<span class="pill pill-active">🌱 Terres converties</span>'
    elif reprise == "Non":
        pills_html += '<span class="pill pill-inactive">🌱 Terres non converties</span>'

    st.markdown(f"""
    <p class="map-title">Cantons favorables <span class="badge">{type_exploit}</span></p>
    <div class="legend-pills">{pills_html}</div>
    """, unsafe_allow_html=True)

    # --- CARTE ---
    custom_scale = [
        [0.0,  "#d73027"],
        [0.25, "#f46d43"],
        [0.5,  "#fee08b"],
        [0.75, "#a6d96a"],
        [1.0,  "#1a9850"]
    ]

    fig = px.choropleth_mapbox(
        gdf_final,
        geojson=gdf_final.__geo_interface__,
        locations=gdf_final.index,
        color='score_final',
        color_continuous_scale=custom_scale,
        range_color=[0, 1],
        hover_name="nom",
        hover_data={
            "code": True,
            "prct_SAU_normalise": ":.2f",
            "nb_exploit_normalise": ":.2f",
            "prct_elevage": ":.2f",
            "prct_gdculture": ":.2f",
            "score_global_elevage": ":.2f",
            "score_global_gdculture": ":.2f",
            "score_final": ":.2f"
        },
        mapbox_style="carto-positron",
        opacity=0.75
    )

    fig.update_layout(
        mapbox_zoom=7,
        mapbox_center={"lat": 49.9, "lon": 2.8},
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=680,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar=dict(
            title="Score",
            thickness=14,
            len=0.6,
            tickfont=dict(family="DM Sans", size=11, color="#1a2e1a"),
            title_font=dict(family="DM Sans", size=12, color="#1a2e1a"),
        )
    )

    st.plotly_chart(fig, use_container_width=True, key="carte_principale")

    # --- DEBUG ---
    with st.expander("📋 Voir les données brutes"):
        cols_to_show = ['nom', 'code', 'score_final', 'prct_SAU_normalise', 'nb_exploit_normalise',
                        'prct_elevage', 'prct_gdculture', 'score_global_elevage', 'score_global_gdculture']
        st.dataframe(
            gdf_final[cols_to_show].sort_values('score_final', ascending=False).head(20),
            use_container_width=True
        )

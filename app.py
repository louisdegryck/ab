import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import requests
import zipfile
import io
import json

st.set_page_config(layout="wide", page_title="BioStart – Hauts-de-France")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap');

html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif;
    background-color: #f4f1e8;
    color: #1a2e1a;
}
.stApp { background-color: #f4f1e8; }

.main-subtitle {
    font-size: 0.85rem;
    color: #4a7a2e;
    font-weight: 600;
    margin: 0 0 6px 0;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}
.main-title {
    font-size: 2.2rem;
    font-weight: 800;
    color: #1a2e1a;
    line-height: 1.15;
    margin: 0;
}
.section-label {
    font-size: 1.1rem;
    font-weight: 700;
    color: #2d5a1b;
    margin-bottom: 1.2rem;
    letter-spacing: 0.03em;
}
.stRadio > label {
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    color: #1a2e1a !important;
    margin-bottom: 0.6rem !important;
}
.stRadio > div > label {
    background: #eef7e4 !important;
    border: 2px solid #b8d89a !important;
    border-radius: 10px !important;
    padding: 8px 20px !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: #2d5a1b !important;
    transition: all 0.2s ease;
}
.stRadio > div > label:hover {
    background: #d4edba !important;
    border-color: #2d5a1b !important;
}
.stButton > button {
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    color: #c0392b !important;
    background: #fff5f5 !important;
    border: 2px solid #e74c3c !important;
    border-radius: 10px !important;
    padding: 8px 20px !important;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background: #fde8e8 !important;
    border-color: #c0392b !important;
}
.map-title {
    font-size: 1.6rem;
    font-weight: 800;
    color: #1a2e1a;
    margin: 1.5rem 0 0.6rem 0;
    padding-bottom: 0.6rem;
    border-bottom: 2px solid #b8d89a;
}
.badge {
    display: inline-block;
    background: #2d5a1b;
    color: white;
    font-size: 0.8rem;
    font-weight: 700;
    padding: 4px 14px;
    border-radius: 20px;
    margin-left: 10px;
    vertical-align: middle;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.legend-pills { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 1.2rem; }
.pill {
    font-size: 0.82rem;
    font-weight: 600;
    padding: 5px 14px;
    border-radius: 20px;
    border: 2px solid;
    font-family: 'Montserrat', sans-serif;
}
.pill-active   { background: #e0f2c8; border-color: #2d5a1b; color: #2d5a1b; }
.pill-inactive { background: #f4f1e8; border-color: #b8d89a; color: #7a9a6a; }
.invite-msg {
    text-align: center;
    padding: 5rem 2rem;
    color: #7a9a6a;
    font-size: 1.3rem;
    font-weight: 600;
    font-style: italic;
}
.pra-info {
    font-size: 0.8rem;
    color: #7a9a6a;
    font-weight: 500;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
hr { border: none; border-top: 2px solid #d4e8c2; margin: 1.5rem 0; }
.streamlit-expanderHeader {
    font-family: 'Montserrat', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: #2d5a1b !important;
}
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #f4f1e8; }
::-webkit-scrollbar-thumb { background: #b8d89a; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# --- CHARGEMENT PRA ---
@st.cache_data
def load_pra():
    """
    Télécharge le shapefile PRA depuis data.gouv.fr et le convertit en GeoDataFrame.
    Source : https://www.data.gouv.fr/datasets/petites-regions-agricoles-1
    """
    url_zip = "https://www.data.gouv.fr/api/1/datasets/r/4bf242e5-1497-4161-b124-0c0e5b766a3d"
    try:
        r = requests.get(url_zip, timeout=30)
        r.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(r.content))
        # On cherche le .shp dans le zip
        shp_files = [f for f in z.namelist() if f.endswith('.shp')]
        if not shp_files:
            return None
        # Extraction dans un buffer mémoire via fiona/geopandas
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            z.extractall(tmpdir)
            shp_path = os.path.join(tmpdir, shp_files[0])
            gdf_pra = gpd.read_file(shp_path)
        # Reprojection en WGS84
        gdf_pra = gdf_pra.to_crs(epsg=4326)
        # Filtrage Hauts-de-France : codes département 02, 59, 60, 62, 80
        # La colonne de code département dans ce fichier est souvent 'DEP' ou dans le code PRA
        # On tente plusieurs noms de colonnes possibles
        col_dept = None
        for c in ['DEP', 'dep', 'INSEE_DEP', 'code_dep', 'DEPT']:
            if c in gdf_pra.columns:
                col_dept = c
                break
        if col_dept:
            gdf_pra = gdf_pra[gdf_pra[col_dept].astype(str).str.zfill(2).isin(['02', '59', '60', '62', '80'])].copy()
        else:
            # Fallback : filtre spatial par bounding box Hauts-de-France
            gdf_pra = gdf_pra.cx[1.4:4.3, 49.0:51.2].copy()
        return gdf_pra
    except Exception as e:
        st.warning(f"Impossible de charger les PRA : {e}")
        return None


# --- CHARGEMENT DONNÉES AGRICOLES ---
@st.cache_data
def load_data():
    df = pd.read_csv('data.csv', sep=';', encoding='utf-8-sig', dtype=str)

    cols_num = [
        'prct_SAU_normalise', 'prct_gdculture', 'prct_elevage',
        'nb_exploit_normalise', 'score_global_elevage', 'score_global_gdculture',
        'Nb_industries_gdculture', 'Nb_industries_elevage', 'Prct_SAU_bio', 'nb_exploit'
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
gdf_pra = load_pra()

# --- JOINTURES ---
gdf_final = gdf_geo.merge(df_csv, left_on='code', right_on='canton', how='left')
for col in cols_num:
    gdf_final[col] = gdf_final[col].fillna(0)


# --- RESET ---
def reset_filtres():
    st.session_state["q1"] = None
    st.session_state["q2"] = None
    st.session_state["q3"] = None

for key in ["q1", "q2", "q3"]:
    if key not in st.session_state:
        st.session_state[key] = None


# --- HEADER ---
try:
    col_logo, col_title = st.columns([1, 9])
    with col_logo:
        st.image("logo_biostart.png", width=100)
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

# --- CRITÈRES ---
col_titre, col_reset = st.columns([6, 1])
with col_titre:
    st.markdown('<p class="section-label">🌿 Définissez vos critères</p>', unsafe_allow_html=True)
with col_reset:
    st.button("🗑️ Effacer les filtres", on_click=reset_filtres)

col1, col2, col3 = st.columns(3)
with col1:
    type_exploit = st.radio("🌾 Type d'activité", ["Élevage", "Grande culture"], index=None, key="q3")
with col2:
    entraide = st.radio("🤝 Besoin d'entraide ?", ["Oui", "Non"], index=None, key="q2")
with col3:
    reprise = st.radio("🌱 Terres déjà converties ?", ["Oui", "Non"], index=None, key="q1")

st.markdown("<hr>", unsafe_allow_html=True)


# --- CARTE ---
if type_exploit is None:
    st.markdown('<div class="invite-msg">Sélectionnez un type d\'activité pour afficher la carte 🗺️</div>', unsafe_allow_html=True)

else:
    alpha = 1.0

    if type_exploit == "Élevage":
        score_base = gdf_final['prct_elevage'].copy().values
    else:
        score_base = gdf_final['prct_gdculture'].copy().values

    if reprise == "Oui":
        E_terres = gdf_final['prct_SAU_normalise'].values
        score_base = score_base * (1 + alpha * (E_terres - 0.5))

    if entraide == "Oui":
        E_entraide = gdf_final['nb_exploit_normalise'].values
        score_base = score_base * (1 + alpha * (E_entraide - 0.5))

    gdf_final['score_final'] = np.clip(score_base, 0, 1)

    # Pills
    pills_html = f'<span class="pill pill-active">📍 {type_exploit}</span>'
    if entraide == "Oui":
        pills_html += '<span class="pill pill-active">🤝 Entraide activée</span>'
    elif entraide == "Non":
        pills_html += '<span class="pill pill-inactive">🤝 Entraide non requise</span>'
    if reprise == "Oui":
        pills_html += '<span class="pill pill-active">🌱 Terres converties</span>'
    elif reprise == "Non":
        pills_html += '<span class="pill pill-inactive">🌱 Terres non converties</span>'
    if gdf_pra is not None:
        pills_html += '<span class="pill pill-active">🗂️ Contours PRA activés</span>'

    st.markdown(f"""
    <p class="map-title">Cantons favorables <span class="badge">{type_exploit}</span></p>
    <div class="legend-pills">{pills_html}</div>
    """, unsafe_allow_html=True)

    # Hover selon activité
    if type_exploit == "Élevage":
        hover_data = {
            "code": True,
            "Nb_industries_elevage": ":.0f",
            "Prct_SAU_bio": ":.2f",
            "nb_exploit": ":.0f",
            "score_final": ":.2f"
        }
    else:
        hover_data = {
            "code": True,
            "Nb_industries_gdculture": ":.0f",
            "Prct_SAU_bio": ":.2f",
            "nb_exploit": ":.0f",
            "score_final": ":.2f"
        }

    custom_scale = [
        [0.0,  "#d73027"],
        [0.25, "#f46d43"],
        [0.5,  "#fee08b"],
        [0.75, "#a6d96a"],
        [1.0,  "#1a9850"]
    ]

    # Carte de base (choropleth cantons)
    fig = px.choropleth_mapbox(
        gdf_final,
        geojson=gdf_final.__geo_interface__,
        locations=gdf_final.index,
        color='score_final',
        color_continuous_scale=custom_scale,
        range_color=[0, 1],
        hover_name="nom",
        hover_data=hover_data,
        mapbox_style="carto-positron",
        opacity=0.75,
        zoom=7,
        center={"lat": 49.9, "lon": 2.8}
    )

    # --- COUCHE PRA : contours + labels ---
    if gdf_pra is not None:
        # Détection du nom de la colonne PRA
        nom_col = None
        for c in ['NOM_PRA', 'nom_pra', 'NAME_PRA', 'name_pra', 'LIBELLE', 'libelle', 'NOM', 'nom', 'LIB_PRA']:
            if c in gdf_pra.columns:
                nom_col = c
                break
        if nom_col is None:
            nom_col = gdf_pra.columns[1]  # fallback : 2e colonne

        # Contours PRA via Scattermapbox (lignes)
        for _, row in gdf_pra.iterrows():
            geom = row.geometry
            nom_pra = str(row[nom_col])
            # Extraction des coordonnées selon le type de géométrie
            coords_list = []
            if geom.geom_type == 'Polygon':
                coords_list = [list(geom.exterior.coords)]
            elif geom.geom_type == 'MultiPolygon':
                coords_list = [list(poly.exterior.coords) for poly in geom.geoms]

            for coords in coords_list:
                lons = [c[0] for c in coords]
                lats = [c[1] for c in coords]
                fig.add_trace(go.Scattermapbox(
                    lon=lons,
                    lat=lats,
                    mode='lines',
                    line=dict(color='#1a3a6b', width=2),
                    hoverinfo='skip',
                    showlegend=False,
                    name=''
                ))

        # Labels PRA (centroïde de chaque PRA)
        pra_lons, pra_lats, pra_noms = [], [], []
        for _, row in gdf_pra.iterrows():
            centroid = row.geometry.centroid
            pra_lons.append(centroid.x)
            pra_lats.append(centroid.y)
            pra_noms.append(str(row[nom_col]))

        fig.add_trace(go.Scattermapbox(
            lon=pra_lons,
            lat=pra_lats,
            mode='text',
            text=pra_noms,
            textfont=dict(
                size=11,
                color='#1a3a6b',
                family='Montserrat'
            ),
            hoverinfo='skip',
            showlegend=False,
            name=''
        ))

    fig.update_layout(
        mapbox_zoom=7,
        mapbox_center={"lat": 49.9, "lon": 2.8},
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=700,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar=dict(
            title="Score",
            thickness=16,
            len=0.65,
            tickfont=dict(family="Montserrat", size=12, color="#1a2e1a"),
            title_font=dict(family="Montserrat", size=13, color="#1a2e1a"),
        )
    )

    st.plotly_chart(fig, use_container_width=True, key="carte_principale")

    with st.expander("📋 Voir les données brutes"):
        cols_to_show = [
            'nom', 'code', 'score_final', 'prct_SAU_normalise', 'nb_exploit_normalise',
            'prct_elevage', 'prct_gdculture', 'score_global_elevage', 'score_global_gdculture',
            'Nb_industries_gdculture', 'Nb_industries_elevage', 'Prct_SAU_bio', 'nb_exploit'
        ]
        st.dataframe(
            gdf_final[cols_to_show].sort_values('score_final', ascending=False).head(20),
            use_container_width=True
        )

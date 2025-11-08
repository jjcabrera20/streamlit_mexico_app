# -*- coding: utf-8 -*-


import streamlit as st
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import json
from pathlib import Path
from html import escape


# ---------------------------------------------------------
# 0. Language configuration
# ---------------------------------------------------------
TRANSLATIONS = {
    'en': {
        'title': '📍 Schools México - Interactive Map',
        'subtitle': 'Explore **{:,}** school points with filtering and sorting.',
        'map_filters': '🎛️ Map Filters',
        'centro_trabajo_codigo': 'Working center code',
        'departamento': 'State',
        'municipio': 'Municipality',
        'select_first': 'Select State first',
        'points_on_map': '🗺️ **{:,}** points on map',
        'map_view': '📍 Map View',
        'map_info': 'ℹ️ Displaying {:,} points. Click on a marker to copy the code to clipboard.',
        'data_table': '📊 Data Table - Filtered Records',
        'table_subtitle': 'Showing data based on map filters. Use search and column sorting to explore.',
        'search_placeholder': '🔍 Search in table (name, locality, etc.)',
        'total_records': '**Total: {:,} records**',
        'found_records': 'Found {:,} matching records',
        'showing_records': 'Showing {:,} of {:,} records',
        'page': 'Page',
        'rows_per_page': 'Rows per page',
        'download_all': '💾 Download All Data',
        'download_filtered': '💾 Download Filtered',
        'download_visible': '💾 Download Current Page',
        'download_disabled_help': 'Use search to filter data first',
        'language': 'Language',
        'name': 'School Name',
        'locality': 'Locality',
        'description': 'Description',
        'click_to_copy': 'Click to copy code'
    },
    'es': {
        'title': '📍 Escuelas México - Mapa Interactivo',
        'subtitle': 'Explora **{:,}** puntos de escuelas con filtrado y ordenamiento.',
        'map_filters': '🎛️ Filtros de Mapa',
        'centro_trabajo_codigo': 'Código centro de trabajo',
        'departamento': 'Entidad',
        'municipio': 'Municipio',
        'select_first': 'Selecciona Entidad primero',
        'points_on_map': '🗺️ **{:,}** puntos en el mapa',
        'map_view': '📍 Vista de Mapa',
        'map_info': 'ℹ️ Mostrando {:,} puntos. Haz clic en un marcador para copiar el código.',
        'data_table': '📊 Tabla de Datos - Registros Filtrados',
        'table_subtitle': 'Mostrando datos basados en filtros del mapa. Usa búsqueda y ordenamiento de columnas.',
        'search_placeholder': '🔍 Buscar en tabla (nombre, localidad, etc.)',
        'total_records': '**Total: {:,} registros**',
        'found_records': 'Se encontraron {:,} registros coincidentes',
        'showing_records': 'Mostrando {:,} de {:,} registros',
        'page': 'Página',
        'rows_per_page': 'Filas por página',
        'download_all': '💾 Descargar Todo',
        'download_filtered': '💾 Descargar Filtrado',
        'download_visible': '💾 Descargar Página Actual',
        'download_disabled_help': 'Usa búsqueda para filtrar datos primero',
        'language': 'Idioma',
        'name': 'Nombre de Escuela',
        'locality': 'Localidad',
        'description': 'Descripción',
        'click_to_copy': 'Clic para copiar código'
    }
}


# Language selector in sidebar
lang = st.sidebar.selectbox(
    "🌐 Language / Idioma",
    options=['en', 'es'],
    format_func=lambda x: 'English' if x == 'en' else 'Español',
    index=1  # Default to Spanish
)

t = TRANSLATIONS[lang]


# ---------------------------------------------------------
# 1. Load and cache data
# ---------------------------------------------------------
@st.cache_data
def load_data():
    path = "qutf_gpd_combined_escuelas_mexico.parquet"

    try:
        gdf = gpd.read_parquet(path)
    except Exception as e:
        st.warning(f"⚠️ Could not read parquet directly ({e}), trying fallback...")
        with open(path, "r", encoding="latin1", errors="ignore") as f:
            data = json.load(f)
        gdf = gpd.GeoDataFrame.from_features(data["features"], crs="EPSG:4326")

    return gdf


# ---------------------------------------------------------
# 2. Create map with click-to-copy functionality
# ---------------------------------------------------------
@st.cache_data
def create_map(_gdf, center_lat, center_lon, click_to_copy_text):
    """Create folium map optimized for performance with click-to-copy"""
    m = folium.Map(location=[center_lat, center_lon], zoom_start=8)

    # Add custom CSS and JavaScript for tooltips and click-to-copy
    custom_js = f"""
    <style>
    .leaflet-tooltip {{
        font-size: 11px !important;
        max-width: 300px !important;
        line-height: 1.3 !important;
    }}
    .leaflet-tooltip * {{
        font-size: 11px !important;
    }}
    </style>
    <script>
    function copyToClipboard(text) {{
        if (navigator.clipboard) {{
            navigator.clipboard.writeText(text).then(function() {{
                alert('📋 {click_to_copy_text}: ' + text);
            }}).catch(function(err) {{
                console.error('Error copying: ', err);
            }});
        }} else {{
            var textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";
            textArea.style.top = 0;
            textArea.style.left = 0;
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {{
                document.execCommand('copy');
                alert('📋 {click_to_copy_text}: ' + text);
            }} catch (err) {{
                console.error('Fallback: Could not copy', err);
            }}
            document.body.removeChild(textArea);
        }}
    }}
    </script>
    """
    m.get_root().html.add_child(folium.Element(custom_js))

    cluster = MarkerCluster(
        name="Schools",
        overlay=True,
        control=False,
        maxClusterRadius=50
    ).add_to(m)

    for _, row in _gdf.iterrows():
        lat, lon = row.geometry.y, row.geometry.x

        # Get code and school name
        code = str(row.get("name", "N/A"))
        school_name = str(row.get("nombre_de_centro_de_trabajo", "Sin nombre"))

        # Escape code for safe HTML/JS embedding
        code_escaped = escape(code)
        school_name_escaped = escape(school_name)

        # Create popup with click-to-copy button
        popup_html = f"""
        <div style="font-size: 12px; min-width: 200px;">
            <b style="font-size: 13px;">{code_escaped}</b><br>
            {school_name_escaped}<br>
            <button onclick="copyToClipboard('{code_escaped}')" 
                    style="margin-top: 8px; padding: 5px 10px; cursor: pointer; 
                           background-color: #4CAF50; color: white; border: none; 
                           border-radius: 3px;">
                📋 {click_to_copy_text}
            </button>
        </div>
        """

        # Simplified tooltip (hover)
        tooltip_html = f'<div style="font-size: 11px;"><b>{code_escaped}</b></div>'

        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=folium.Tooltip(tooltip_html),
            color='blue',
            fill=True,
            fillColor='blue',
            fillOpacity=0.7,
            weight=2
        ).add_to(cluster)

    return m


# ---------------------------------------------------------
# Initialize UI
# ---------------------------------------------------------
gdf = load_data()

st.title(t['title'])
st.markdown(t['subtitle'].format(len(gdf)))


# ---------------------------------------------------------
# 3. Sidebar filters (reordered to reduce data early)
# ---------------------------------------------------------
st.sidebar.header(t['map_filters'])

CENTRO_DE_TRABAJO_FIELD = "name"
DEPARTAMENTO_FIELD = "nombre_entidad"
MUNICIPIO_FIELD = "nombre_municipio"
NOMBRE_DE_CENTRO_DE_TRABAJO = "nombre_de_centro_de_trabajo"
NOMBRE_LOCALIDAD = "nombre_localidad"

# Departamento options
departamentos = sorted(gdf[DEPARTAMENTO_FIELD].dropna().unique().tolist())
admin1 = st.sidebar.selectbox(t['departamento'], departamentos, index=0)

if admin1:
    municipios = "" + sorted(gdf[gdf[DEPARTAMENTO_FIELD] == admin1][MUNICIPIO_FIELD].dropna().unique().tolist())
    admin2 = st.sidebar.selectbox(t['municipio'], municipios, index=0)

    if admin2:
        filtered_for_map = gdf[
            (gdf[MUNICIPIO_FIELD] == admin2) & (gdf[DEPARTAMENTO_FIELD] == admin1)
        ]
    else:
        filtered_for_map = gdf[gdf[DEPARTAMENTO_FIELD] == admin1]
else:
    filtered_for_map = gdf
    st.sidebar.selectbox(t['municipio'], [t['select_first']], index=0, disabled=True)


st.sidebar.write(t['points_on_map'].format(len(filtered_for_map)))

# Performance warning and limit points
if len(filtered_for_map) > 10000:
    st.sidebar.warning(f"⚠️ {len(filtered_for_map):,} points. Consider filtering by Municipio for better performance.")
    filtered_for_map = filtered_for_map.head(10000)


# ---------------------------------------------------------
# 4. Create and display map
# ---------------------------------------------------------
st.subheader(t['map_view'])

if not filtered_for_map.empty:
    center_lat = filtered_for_map.geometry.y.mean()
    center_lon = filtered_for_map.geometry.x.mean()
else:
    center_lat, center_lon = 23.6345, -102.5528

st.info(t['map_info'].format(len(filtered_for_map)))

with st.spinner('Loading map...'):
    m = create_map(filtered_for_map, center_lat, center_lon, t['click_to_copy'])
    st_folium(m, width=900, height=600, returned_objects=[])


# ---------------------------------------------------------
# 5. Data table with pagination
# ---------------------------------------------------------
st.subheader(t['data_table'])
st.markdown(t['table_subtitle'])

table_df = filtered_for_map.copy()

column_display_names = {
    CENTRO_DE_TRABAJO_FIELD: t['centro_trabajo_codigo'],
    DEPARTAMENTO_FIELD: t['departamento'],
    MUNICIPIO_FIELD: t['municipio'],
    NOMBRE_LOCALIDAD: t['locality'],
    NOMBRE_DE_CENTRO_DE_TRABAJO: t['name']
}

display_columns = [CENTRO_DE_TRABAJO_FIELD, DEPARTAMENTO_FIELD, MUNICIPIO_FIELD, NOMBRE_LOCALIDAD, NOMBRE_DE_CENTRO_DE_TRABAJO]

table_df = table_df[display_columns].copy()
table_df = table_df.rename(columns=column_display_names)

col1, col2 = st.columns([2, 1])
with col1:
    search_term = st.text_input(t['search_placeholder'], "")
with col2:
    st.write("")
    st.write(t['total_records'].format(len(table_df)))

if search_term:
    mask = table_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
    table_df = table_df[mask]
    st.info(t['found_records'].format(len(table_df)))

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    rows_per_page = st.selectbox(
        t['rows_per_page'],
        options=[50, 100, 200, 500],
        index=1
    )
with col2:
    total_pages = max(1, (len(table_df) - 1) // rows_per_page + 1)
    page = st.number_input(
        t['page'],
        min_value=1,
        max_value=total_pages,
        value=1,
        step=1
    )

start_idx = (page - 1) * rows_per_page
end_idx = min(start_idx + rows_per_page, len(table_df))
paginated_df = table_df.iloc[start_idx:end_idx]

st.caption(t['showing_records'].format(len(paginated_df), len(table_df)))

st.dataframe(
    paginated_df,
    width='stretch',
    height=400
)


# Download buttons
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    csv_filtered = table_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=t['download_all'],
        data=csv_filtered,
        file_name="filtered_schools.csv",
        mime="text/csv",
    )

with col2:
    csv_page = paginated_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=t['download_visible'],
        data=csv_page,
        file_name=f"schools_page_{page}.csv",
        mime="text/csv",
    )

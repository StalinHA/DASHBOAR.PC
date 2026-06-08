import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import re
from collections import defaultdict
from io import BytesIO
from datetime import datetime
import os
import zipfile

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Perú Compras - Análisis de Fichas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Lista completa de marcas
MARCAS_COMPLETAS = [
    'TRIUMPH BOARD', 'VASTEC', 'RHINOBOX', 'LENOVO', 'EXIN', 'M4X', 'KENYA TECHNOLOGY', 
    'HP', 'MADI-TEK', 'INVESTMENT & BUSINESS SMART SBI', 'ADVANCE', 'QUI-TECH', 'TEXCOPER', 
    'WIDETEK', 'IQTOUCH', 'LG', 'ONESCREEN', 'HUAWEI', 'INOTEC', 'DELL', 'I3', 'ASUS', 
    'QUAMTU', 'KODAK', 'RICOH', 'SHARP', 'CIBER', 'HAO TECH', 'BROTHER', 'VIEWSONIC', 
    'AVISION', 'SAMSUNG', 'ALLWIYA', 'GAMEMAX', 'DYNABOOK', 'HIPPOBOX', 'CONTEX', 'INNEX', 
    'CTOUCH', 'HIKVISION', 'ZKT ECO', 'YEALINK', 'TEROS', 'SILVER VOLT', 'QOSOFT', 
    'MIMIO', 'HAITECH', 'OPTOMA TECHNOLOGY INC', 'GROWTH HACK', 'MSI', 'XEROX', 'QOMO', 
    'EPSON', 'CLEVERTOUCH', 'I2S INNOVATIVE IMAGING SOLUTIONS', 'IQ BOARD', 'GCS', 'COLORTRAC', 
    'CANON', 'BOOKEYE', 'JFA TECHNOLOGY', 'AMC', 'MAXTIC', 'SANDISK', 'KINGSTON', 'ADATA', 'NEW KRAL'
]

# Archivos para guardar el progreso
PROGRESS_FILE = "progreso_marcas.json"
SERIES_PROCESSED_FILE = "series_procesadas.json"

# CSS personalizado - Fondo oscuro elegante con buen contraste
st.markdown("""
<style>
    /* Fondo principal - Azul noche */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    }
    
    /* Header - Gradiente azul brillante */
    .main-header {
        background: linear-gradient(90deg, #2563eb, #1e40af);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
        color: white;
    }
    
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.95;
        color: #e2e8f0;
    }
    
    /* Tarjetas de estadísticas */
    .stat-card {
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        text-align: center;
        transition: transform 0.3s;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        background: rgba(30, 41, 59, 0.9);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #60a5fa, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .stat-label {
        color: #cbd5e1;
        margin-top: 0.5rem;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a, #020617);
        border-right: 1px solid #334155;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #f1f5f9;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #1e293b;
        border-radius: 12px;
        padding: 6px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        color: #cbd5e1;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #3b82f6, #2563eb);
        color: white;
    }
    
    /* Texto general */
    .stMarkdown, .stText, .stMetric label {
        color: #f1f5f9;
    }
    
    /* Botones */
    .stButton button {
        background: linear-gradient(90deg, #3b82f6, #2563eb);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(59,130,246,0.4);
    }
    
    /* Info boxes */
    .stAlert {
        background-color: #1e293b;
        border-left: 4px solid #3b82f6;
        color: #e2e8f0;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1e293b;
        border-radius: 8px;
        color: #f1f5f9;
        font-weight: 600;
    }
    
    /* Badges */
    .no-data-badge {
        background-color: #ef4444;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #60a5fa;
    }
    
    [data-testid="stMetricLabel"] {
        color: #cbd5e1;
    }
    
    /* Dataframe */
    .stDataFrame {
        background: #1e293b;
        border-radius: 12px;
        border: 1px solid #334155;
    }
    
    /* Checkboxes */
    .stCheckbox label {
        color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

def extraer_marca(producto):
    if not producto:
        return "SIN MARCA"
    
    producto_upper = producto.upper()
    
    for marca in sorted(MARCAS_COMPLETAS, key=len, reverse=True):
        if marca.upper() in producto_upper:
            return marca
    
    patron_unidad = re.search(r'UNIDAD\s+([A-Z\s]+?)(?:\s+|$)', producto_upper)
    if patron_unidad:
        posible = patron_unidad.group(1).strip()
        if len(posible) < 20 and posible not in ['DE', 'LA', 'EL', 'LOS', 'LAS']:
            return posible
    
    return "OTRA MARCA"

def extraer_numero_parte(producto):
    if not producto:
        return "N/D"
    
    patrones = [
        r'UNIDAD\s+(?:[A-Z]+\s+)?([A-Z0-9]+(?:[-#][A-Z0-9]+)+)',
        r'([A-Z0-9]{4,}(?:[-#][A-Z0-9]{3,}))',
        r'([A-Z0-9]{8,})'
    ]
    
    for patron in patrones:
        match = re.search(patron, producto, re.IGNORECASE)
        if match:
            return match.group(1)[:30]
    
    return "N/D"

def procesar_json(archivo):
    try:
        datos = json.load(archivo)
        fichas = []
        
        if 'catalogos' in datos:
            for catalogo in datos['catalogos']:
                nombre_catalogo = catalogo.get('nombre', 'SIN CATÁLOGO')
                for categoria in catalogo.get('categorias', []):
                    nombre_categoria = categoria.get('nombre', 'SIN CATEGORÍA')
                    for ficha in categoria.get('fichas', []):
                        producto = ficha.get('producto', '')
                        ficha_id = f"{nombre_catalogo}_{nombre_categoria}_{producto[:50]}"
                        fichas.append({
                            'ID': ficha_id,
                            'Catálogo': nombre_catalogo,
                            'Categoría': nombre_categoria,
                            'Producto': producto,
                            'Marca': extraer_marca(producto),
                            'Número de Parte': extraer_numero_parte(producto),
                            'Estado': ficha.get('estado', 'SIN ESTADO'),
                            'Moneda': ficha.get('moneda', ''),
                            'Precio': ficha.get('precio_base', '0'),
                            'PDF': ficha.get('ficha_tecnica_pdf', ''),
                            'Imagen': ficha.get('imagen', '')
                        })
        
        return pd.DataFrame(fichas)
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        return pd.DataFrame()

def cargar_progreso():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def guardar_progreso(progreso):
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progreso, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def cargar_series_procesadas():
    if os.path.exists(SERIES_PROCESSED_FILE):
        try:
            with open(SERIES_PROCESSED_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def guardar_series_procesadas(series):
    try:
        with open(SERIES_PROCESSED_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(series), f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def exportar_progreso():
    progreso = cargar_progreso()
    return json.dumps(progreso, ensure_ascii=False, indent=2)

def importar_progreso(archivo_json):
    try:
        progreso = json.load(archivo_json)
        guardar_progreso(progreso)
        return True
    except:
        return False

def buscar_y_marcar_series(nuevas_series, df, series_procesadas):
    """Busca NUEVAS series con coincidencia EXACTA (no parcial) en la descripción del producto"""
    nuevas_series_unicas = [s for s in nuevas_series if s not in series_procesadas]
    duplicados = [s for s in nuevas_series if s in series_procesadas]
    
    encontradas = []
    no_encontradas = []
    
    # Diccionario para rastrear qué series ya asignamos a qué fichas
    series_asignadas = {}
    
    # Crear conjunto de series a buscar
    series_a_buscar = set(nuevas_series_unicas)
    
    for serie in series_a_buscar:
        serie_limpia = serie.strip()
        if not serie_limpia:
            continue
            
        # Buscar coincidencia EXACTA (con límites de palabra)
        encontrada = False
        for _, row in df.iterrows():
            producto = str(row['Producto'])
            # Usar expresión regular para coincidencia exacta de palabra completa
            patron = r'(?<![a-zA-Z0-9])' + re.escape(serie_limpia) + r'(?![a-zA-Z0-9-])'
            if re.search(patron, producto, re.IGNORECASE):
                # Verificar si esta serie ya fue asignada
                if serie_limpia not in series_asignadas:
                    series_asignadas[serie_limpia] = row['ID']
                    st.session_state.progreso[row['ID']] = True
                    encontradas.append({
                        'Serie': serie_limpia,
                        'Producto': row['Producto'][:200],
                        'Marca': row['Marca'],
                        'Categoría': row['Categoría'],
                        'ID_Ficha': row['ID']
                    })
                    encontrada = True
                    break
                else:
                    encontrada = True
                    break
        
        if not encontrada:
            no_encontradas.append(serie_limpia)
    
    # Actualizar series procesadas
    series_procesadas.update(series_a_buscar)
    guardar_series_procesadas(series_procesadas)
    guardar_progreso(st.session_state.progreso)
    
    return encontradas, no_encontradas, duplicados

def exportar_excel_progreso(df, series_encontradas, series_no_encontradas):
    """Exporta a Excel REAL con todas las hojas requeridas"""
    output = BytesIO()
    
    try:
        # Usar openpyxl como engine
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja 1: Series encontradas
            if series_encontradas:
                df_encontradas = pd.DataFrame(series_encontradas)
                df_encontradas.to_excel(writer, sheet_name='Series Encontradas', index=False)
            else:
                pd.DataFrame({'Mensaje': ['No hay series encontradas para esta carga']}).to_excel(
                    writer, sheet_name='Series Encontradas', index=False
                )
            
            # Hoja 2: Series no encontradas
            if series_no_encontradas:
                df_no_encontradas = pd.DataFrame({'Serie': series_no_encontradas})
                df_no_encontradas.to_excel(writer, sheet_name='Series No Encontradas', index=False)
            else:
                pd.DataFrame({'Mensaje': ['Todas las series fueron encontradas']}).to_excel(
                    writer, sheet_name='Series No Encontradas', index=False
                )
            
            # Hoja 3: Resumen de fichas por marca
            resumen_marcas = []
            for marca in df['Marca'].unique():
                df_marca = df[df['Marca'] == marca]
                total = len(df_marca)
                completadas = sum(1 for _, row in df_marca.iterrows() if st.session_state.progreso.get(row['ID'], False))
                pendientes = total - completadas
                porcentaje = (completadas / total * 100) if total > 0 else 0
                resumen_marcas.append({
                    'Marca': marca,
                    'Total Fichas': total,
                    'Completadas': completadas,
                    'Pendientes': pendientes,
                    'Porcentaje Completado': round(porcentaje, 1)
                })
            
            df_resumen = pd.DataFrame(resumen_marcas).sort_values('Marca')
            df_resumen.to_excel(writer, sheet_name='Resumen por Marca', index=False)
            
            # Hoja 4: Detalle por categoría de cada marca
            detalle_categorias = []
            for marca in sorted(df['Marca'].unique()):
                df_marca = df[df['Marca'] == marca]
                for categoria in sorted(df_marca['Categoría'].unique()):
                    df_cat = df_marca[df_marca['Categoría'] == categoria]
                    total = len(df_cat)
                    completadas = sum(1 for _, row in df_cat.iterrows() if st.session_state.progreso.get(row['ID'], False))
                    pendientes = total - completadas
                    porcentaje = (completadas / total * 100) if total > 0 else 0
                    detalle_categorias.append({
                        'Marca': marca,
                        'Categoría': categoria,
                        'Total Fichas': total,
                        'Completadas': completadas,
                        'Pendientes': pendientes,
                        'Porcentaje Completado': round(porcentaje, 1)
                    })
            
            df_detalle = pd.DataFrame(detalle_categorias)
            df_detalle.to_excel(writer, sheet_name='Detalle por Categoría', index=False)
            
            # Hoja 5: Todas las fichas con estado de revisión
            df_con_estado = df.copy()
            df_con_estado['Estado Revision'] = df_con_estado['ID'].apply(
                lambda x: 'COMPLETADA' if st.session_state.progreso.get(x, False) else 'PENDIENTE'
            )
            df_con_estado['Producto_Resumido'] = df_con_estado['Producto'].str[:150]
            df_export = df_con_estado[['Marca', 'Categoría', 'Estado', 'Estado Revision', 'Número de Parte', 'Producto_Resumido']]
            df_export.to_excel(writer, sheet_name='Todas las Fichas', index=False)
            
            # Hoja 6: Progreso General
            total_fichas = len(df)
            total_completadas = sum(1 for _, row in df.iterrows() if st.session_state.progreso.get(row['ID'], False))
            df_progreso_general = pd.DataFrame({
                'Metrica': ['Total Fichas', 'Fichas Completadas', 'Fichas Pendientes', 'Porcentaje Completado'],
                'Valor': [total_fichas, total_completadas, total_fichas - total_completadas, 
                          round(total_completadas / total_fichas * 100, 1) if total_fichas > 0 else 0]
            })
            df_progreso_general.to_excel(writer, sheet_name='Progreso General', index=False)
            
    except Exception as e:
        st.error(f"Error al exportar Excel: {e}")
        return None
    
    output.seek(0)
    return output

def limpiar_progreso_por_marca(marca, df):
    """Limpia el progreso de todas las fichas de una marca específica"""
    fichas_marca = df[df['Marca'] == marca]['ID'].tolist()
    for ficha_id in fichas_marca:
        st.session_state.progreso.pop(ficha_id, None)
    guardar_progreso(st.session_state.progreso)

# Inicializar estado de sesión
if 'progreso' not in st.session_state:
    st.session_state.progreso = cargar_progreso()
if 'df_actual' not in st.session_state:
    st.session_state.df_actual = None
if 'series_procesadas' not in st.session_state:
    st.session_state.series_procesadas = cargar_series_procesadas()
if 'ultimas_encontradas' not in st.session_state:
    st.session_state.ultimas_encontradas = []
if 'ultimas_no_encontradas' not in st.session_state:
    st.session_state.ultimas_no_encontradas = []

# Título principal
st.markdown("""
<div class="main-header">
    <h1>📊 Dashboard Perú Compras</h1>
    <p>Analizador profesional de fichas técnicas - Sistema de seguimiento de progreso</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📁 Carga tu archivo")
    archivo = st.file_uploader("Selecciona tu archivo JSON", type=['json'])
    
    st.markdown("---")
    st.markdown("### 📊 Sistema de Progreso")
    
    col1, col2 = st.columns(2)
    with col1:
        progreso_json = exportar_progreso()
        st.download_button(
            label="📤 Exportar progreso",
            data=progreso_json,
            file_name=f"progreso_marcas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    with col2:
        archivo_progreso = st.file_uploader("📥 Importar progreso", type=['json'], key="progress_uploader")
        if archivo_progreso is not None:
            if importar_progreso(archivo_progreso):
                st.success("✅ Progreso importado!")
                st.session_state.progreso = cargar_progreso()
                st.rerun()
    
    st.markdown("---")
    st.markdown("### 🗑️ Limpiar Progreso")
    
    if st.session_state.df_actual is not None:
        marcas_disponibles = [''] + sorted(st.session_state.df_actual['Marca'].unique().tolist())
        marca_limpiar = st.selectbox("Selecciona marca para limpiar", marcas_disponibles)
        
        col3, col4 = st.columns(2)
        with col3:
            if marca_limpiar and st.button(f"🗑️ Limpiar {marca_limpiar}"):
                limpiar_progreso_por_marca(marca_limpiar, st.session_state.df_actual)
                st.success(f"✅ Progreso de {marca_limpiar} limpiado!")
                st.rerun()
        
        with col4:
            if st.button("⚠️ RESET TOTAL", type="primary"):
                st.session_state.progreso = {}
                st.session_state.series_procesadas = set()
                guardar_progreso({})
                guardar_series_procesadas(set())
                st.success("✅ PROGRESO TOTAL RESETEADO!")
                st.rerun()
    
    st.markdown("---")
    st.markdown("### 🏭 Marcas Reconocidas")
    st.markdown(f"**{len(MARCAS_COMPLETAS)} marcas** cargadas en el sistema")
    
    st.markdown("---")
    st.markdown(f"### 📊 Series Procesadas")
    st.metric("Total series únicas procesadas", len(st.session_state.series_procesadas))

# Procesar archivo
if archivo is not None:
    with st.spinner('🔄 Procesando archivo...'):
        df = procesar_json(archivo)
        st.session_state.df_actual = df
    
    if len(df) > 0:
        st.success(f"✅ ¡Éxito! Se cargaron **{len(df):,}** fichas técnicas")
        
        # Métricas principales
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric("📦 Total Fichas", f"{len(df):,}")
        with col2:
            marcas_con_fichas = df['Marca'].nunique()
            st.metric("🏭 Marcas con Fichas", marcas_con_fichas)
        with col3:
            marcas_sin_fichas = len([m for m in MARCAS_COMPLETAS if m not in df['Marca'].values])
            st.metric("⚠️ Marcas sin Fichas", marcas_sin_fichas)
        with col4:
            propuestas = len(df[df['Estado'] == 'PROPUESTA'])
            st.metric("📌 En PROPUESTA", f"{propuestas:,}")
        with col5:
            ofertadas = len(df[df['Estado'] == 'OFERTADA SIN OFERTA'])
            st.metric("⚠️ Sin Oferta", f"{ofertadas:,}")
        with col6:
            fichas_completadas = sum(st.session_state.progreso.get(fila['ID'], False) for _, fila in df.iterrows())
            porcentaje = (fichas_completadas / len(df)) * 100 if len(df) > 0 else 0
            st.metric("✅ Progreso", f"{porcentaje:.1f}%")
        
        # Filtros
        st.markdown("---")
        st.markdown("### 🔍 Filtros Inteligentes")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            marcas_lista = ['Todas'] + sorted(df['Marca'].unique().tolist())
            marca_filter = st.selectbox("🏭 Marca", marcas_lista)
        with col2:
            estados_lista = ['Todos'] + sorted(df['Estado'].unique().tolist())
            estado_filter = st.selectbox("📌 Estado", estados_lista)
        with col3:
            categorias_lista = ['Todas'] + sorted(df['Categoría'].unique().tolist())
            categoria_filter = st.selectbox("📂 Categoría", categorias_lista)
        with col4:
            completado_filter = st.selectbox("✅ Estado revisión", ["Todos", "Completados", "Pendientes"])
        with col5:
            busqueda_texto = st.text_input("🔎 Búsqueda libre", placeholder="Producto o número de parte...")
        
        # Aplicar filtros
        df_filtrado = df.copy()
        if marca_filter != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['Marca'] == marca_filter]
        if estado_filter != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Estado'] == estado_filter]
        if categoria_filter != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['Categoría'] == categoria_filter]
        if completado_filter != "Todos":
            if completado_filter == "Completados":
                df_filtrado = df_filtrado[df_filtrado['ID'].apply(lambda x: st.session_state.progreso.get(x, False))]
            else:
                df_filtrado = df_filtrado[df_filtrado['ID'].apply(lambda x: not st.session_state.progreso.get(x, False))]
        if busqueda_texto:
            df_filtrado = df_filtrado[
                df_filtrado['Producto'].str.contains(busqueda_texto, case=False, na=False) |
                df_filtrado['Número de Parte'].str.contains(busqueda_texto, case=False, na=False)
            ]
        
        st.info(f"📊 Mostrando **{len(df_filtrado):,}** de **{len(df):,}** fichas")
        
        # Panel de marcas sin fichas
        st.markdown("---")
        st.markdown("### ⚠️ Marcas Sin Fichas en el Sistema")
        
        marcas_con_datos = set(df['Marca'].unique())
        marcas_sin_datos = [m for m in MARCAS_COMPLETAS if m not in marcas_con_datos]
        
        if marcas_sin_datos:
            cols = st.columns(5)
            for i, marca in enumerate(marcas_sin_datos[:20]):
                with cols[i % 5]:
                    st.markdown(f"<span class='no-data-badge'>⚠️ {marca}</span>", unsafe_allow_html=True)
            if len(marcas_sin_datos) > 20:
                st.caption(f"... y {len(marcas_sin_datos) - 20} marcas más sin fichas")
        else:
            st.success("✅ ¡Todas las marcas tienen fichas cargadas!")
        
        # Panel de progreso por marca CON EXPANDER PARA CATEGORÍAS
        st.markdown("---")
        st.markdown("### 📈 Panel de Progreso por Marca")
        
        for marca in sorted(df['Marca'].unique()):
            df_marca = df[df['Marca'] == marca]
            total_marca = len(df_marca)
            completadas_marca = sum(st.session_state.progreso.get(fila['ID'], False) for _, fila in df_marca.iterrows())
            porcentaje_marca = (completadas_marca / total_marca) * 100 if total_marca > 0 else 0
            
            # Barra de progreso de la marca
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{marca}** - {completadas_marca}/{total_marca} fichas")
                st.progress(porcentaje_marca / 100)
            with col2:
                st.markdown(f"`{porcentaje_marca:.1f}%`")
            
            # Expander con detalle por categoría
            with st.expander(f"Ver detalle por categoría - {marca}"):
                for categoria in sorted(df_marca['Categoría'].unique()):
                    df_categoria = df_marca[df_marca['Categoría'] == categoria]
                    total_cat = len(df_categoria)
                    completadas_cat = sum(st.session_state.progreso.get(fila['ID'], False) for _, fila in df_categoria.iterrows())
                    porcentaje_cat = (completadas_cat / total_cat) * 100 if total_cat > 0 else 0
                    
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.markdown(f"📁 **{categoria}**")
                    with col2:
                        st.markdown(f"{completadas_cat}/{total_cat} fichas")
                    with col3:
                        st.markdown(f"`{porcentaje_cat:.1f}%`")
                    
                    # Mini barra de progreso por categoría
                    st.progress(porcentaje_cat / 100)
                    st.markdown("---")
        
        # Tabs
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📈 Resumen General", 
            "🏭 Análisis por Marca", 
            "📂 Análisis por Categoría",
            "🔍 Análisis Marca-Categoría",
            "📦 Carga Masiva de Series",
            "✅ Revisión de Fichas",
            "📋 Tabla Detallada"
        ])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                estados_counts = df_filtrado['Estado'].value_counts().reset_index()
                estados_counts.columns = ['Estado', 'Cantidad']
                fig_estados = px.pie(estados_counts, values='Cantidad', names='Estado', 
                                     title='📌 Distribución por Estado', hole=0.4)
                fig_estados.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_estados, use_container_width=True)
            
            with col2:
                top_marcas = df_filtrado['Marca'].value_counts().head(10).reset_index()
                top_marcas.columns = ['Marca', 'Cantidad']
                fig_marcas = px.bar(top_marcas, x='Cantidad', y='Marca', orientation='h',
                                    title='🏭 Top 10 Marcas', text='Cantidad')
                fig_marcas.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_marcas, use_container_width=True)
        
        with tab2:
            marca_analisis = st.selectbox("Selecciona una marca", sorted(df['Marca'].unique()))
            
            if marca_analisis:
                df_marca = df[df['Marca'] == marca_analisis]
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Fichas", f"{len(df_marca):,}")
                with col2:
                    st.metric("Categorías", df_marca['Categoría'].nunique())
                with col3:
                    propuestas_marca = len(df_marca[df_marca['Estado'] == 'PROPUESTA'])
                    st.metric("En PROPUESTA", f"{propuestas_marca:,}")
                with col4:
                    completadas_marca = sum(st.session_state.progreso.get(fila['ID'], False) for _, fila in df_marca.iterrows())
                    porcentaje = (completadas_marca / len(df_marca)) * 100 if len(df_marca) > 0 else 0
                    st.metric("✅ Completado", f"{porcentaje:.1f}%")
                
                estados_marca = df_marca['Estado'].value_counts().reset_index()
                estados_marca.columns = ['Estado', 'Cantidad']
                fig_marca_estados = px.bar(estados_marca, x='Estado', y='Cantidad',
                                           title=f'📌 Estados - {marca_analisis}', text='Cantidad')
                fig_marca_estados.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_marca_estados, use_container_width=True)
        
        with tab3:
            categoria_analisis = st.selectbox("Selecciona una categoría", sorted(df['Categoría'].unique()))
            
            if categoria_analisis:
                df_categoria = df[df['Categoría'] == categoria_analisis]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Fichas", f"{len(df_categoria):,}")
                with col2:
                    st.metric("Marcas", df_categoria['Marca'].nunique())
                with col3:
                    completadas_cat = sum(st.session_state.progreso.get(fila['ID'], False) for _, fila in df_categoria.iterrows())
                    porcentaje = (completadas_cat / len(df_categoria)) * 100 if len(df_categoria) > 0 else 0
                    st.metric("✅ Completado", f"{porcentaje:.1f}%")
        
        with tab4:
            st.markdown("### 🔍 Análisis Detallado: Marca vs Categoría")
            
            marca_seleccionada = st.selectbox("🏭 Selecciona una marca", sorted(df['Marca'].unique()), key="marca_categoria_analysis")
            
            if marca_seleccionada:
                df_marca = df[df['Marca'] == marca_seleccionada]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📦 Total Fichas", len(df_marca))
                with col2:
                    st.metric("📁 Categorías", df_marca['Categoría'].nunique())
                with col3:
                    st.metric("📌 Estados distintos", df_marca['Estado'].nunique())
                
                st.markdown("---")
                st.markdown("#### 📂 Categorías donde aparece la marca")
                
                for categoria in df_marca['Categoría'].unique():
                    df_categoria_marca = df_marca[df_marca['Categoría'] == categoria]
                    
                    with st.expander(f"📁 {categoria} - Total: {len(df_categoria_marca)} fichas"):
                        estados_cat = df_categoria_marca['Estado'].value_counts().reset_index()
                        estados_cat.columns = ['Estado', 'Cantidad']
                        
                        fig_estados_cat = px.bar(estados_cat, x='Estado', y='Cantidad',
                                                  title=f'Distribución por Estado en {categoria}',
                                                  text='Cantidad', color='Estado')
                        fig_estados_cat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_estados_cat, use_container_width=True)
        
        # PESTAÑA: Carga Masiva de Series MEJORADA
        with tab5:
            st.markdown("### 📦 Carga Masiva de Números de Serie")
            st.markdown("Pega una lista de números de serie (uno por línea) para buscar coincidencias exactas en las descripciones de los productos.")
            st.info("💡 **Características:**\n- ✅ Detecta series duplicadas automáticamente\n- ✅ Acumula series nuevas sin perder el progreso anterior\n- ✅ Coincidencia EXACTA (no parcial)\n- ✅ Cada serie se asigna a UNA SOLA ficha")
            
            # Mostrar series ya procesadas
            with st.expander(f"📊 Ver series ya procesadas ({len(st.session_state.series_procesadas)} únicas)"):
                if st.session_state.series_procesadas:
                    series_list = list(st.session_state.series_procesadas)
                    st.write(series_list[:100])
                    if len(series_list) > 100:
                        st.caption(f"... y {len(series_list) - 100} más")
                else:
                    st.info("Aún no has procesado ninguna serie")
            
            series_input = st.text_area(
                "📝 Ingresa NUEVOS números de serie (uno por línea):",
                height=200,
                placeholder="Ejemplo:\nLH75WAFWLGCXZX\nLH75WAFWLGCXZX-RM\nLH86WAFPLGCXZX"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔍 Buscar y Marcar NUEVAS Series", type="primary"):
                    if series_input.strip():
                        nuevas_series = [s.strip() for s in series_input.strip().split('\n') if s.strip()]
                        
                        with st.spinner(f'Buscando {len(nuevas_series)} series nuevas...'):
                            encontradas, no_encontradas, duplicados = buscar_y_marcar_series(
                                nuevas_series, df, st.session_state.series_procesadas
                            )
                            
                            st.session_state.ultimas_encontradas = encontradas
                            st.session_state.ultimas_no_encontradas = no_encontradas
                            
                            st.success(f"✅ Búsqueda completada!")
                            
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("✅ Nuevas encontradas", len(encontradas))
                            with col_b:
                                st.metric("❌ Nuevas NO encontradas", len(no_encontradas))
                            with col_c:
                                st.metric("🔄 Duplicados (omitidos)", len(duplicados))
                            
                            if duplicados:
                                st.warning(f"⚠️ Series duplicadas omitidas: {', '.join(duplicados[:10])}")
                                if len(duplicados) > 10:
                                    st.caption(f"... y {len(duplicados) - 10} más")
                            
                            if encontradas:
                                st.markdown("#### ✅ Series encontradas y marcadas:")
                                st.dataframe(pd.DataFrame(encontradas), use_container_width=True)
                                
                                # Resumen por marca
                                st.markdown("#### 📊 Resumen por Marca de las series encontradas:")
                                df_resumen = pd.DataFrame(encontradas)
                                resumen_marcas_series = df_resumen.groupby('Marca').size().reset_index(name='Series Encontradas')
                                st.dataframe(resumen_marcas_series, use_container_width=True)
                            
                            if no_encontradas:
                                st.markdown("#### ❌ Series NO encontradas:")
                                st.write(no_encontradas[:50])
                                if len(no_encontradas) > 50:
                                    st.caption(f"... y {len(no_encontradas) - 50} más")
                            
                            # Mostrar progreso actualizado
                            fichas_completadas = sum(st.session_state.progreso.get(fila['ID'], False) for _, fila in df.iterrows())
                            porcentaje_total = (fichas_completadas / len(df)) * 100 if len(df) > 0 else 0
                            st.info(f"📊 Progreso total actual: **{porcentaje_total:.1f}%** ({fichas_completadas}/{len(df)} fichas completadas)")
                    else:
                        st.warning("⚠️ Por favor ingresa al menos un número de serie")
            
            with col2:
                # Botón para exportar Excel
                if st.button("📊 Exportar a Excel (Progreso Actual)"):
                    excel_file = exportar_excel_progreso(
                        df, 
                        st.session_state.ultimas_encontradas, 
                        st.session_state.ultimas_no_encontradas
                    )
                    
                    if excel_file:
                        st.download_button(
                            label="📥 Descargar Excel",
                            data=excel_file,
                            file_name=f"progreso_perucompras_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
        
        with tab6:
            st.markdown("### ✅ Revisión de Fichas")
            st.markdown("Marca las fichas que ya has revisado/completado. ¡El progreso se guarda automáticamente!")
            
            col1, col2 = st.columns(2)
            with col1:
                marca_revision = st.selectbox("Filtrar por marca", ["Todas"] + sorted(df['Marca'].unique()), key="revision_marca")
            with col2:
                categoria_revision = st.selectbox("Filtrar por categoría", ["Todas"] + sorted(df['Categoría'].unique()), key="revision_categoria")
            
            df_revision = df.copy()
            if marca_revision != "Todas":
                df_revision = df_revision[df_revision['Marca'] == marca_revision]
            if categoria_revision != "Todas":
                df_revision = df_revision[df_revision['Categoría'] == categoria_revision]
            
            rows_per_page_review = st.selectbox("Filas por página", [10, 25, 50, 100], index=1, key="review_rows")
            page_review = st.number_input("Página", min_value=1, value=1, step=1, key="review_page")
            
            start_idx_review = (page_review - 1) * rows_per_page_review
            end_idx_review = start_idx_review + rows_per_page_review
            
            st.markdown("#### Marca las fichas revisadas:")
            
            for idx, (_, row) in enumerate(df_revision.iloc[start_idx_review:end_idx_review].iterrows()):
                col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 3, 1])
                ficha_id = row['ID']
                is_checked = st.session_state.progreso.get(ficha_id, False)
                
                with col1:
                    nuevo_estado = st.checkbox("✅", value=is_checked, key=f"check_{ficha_id}_{idx}")
                    if nuevo_estado != is_checked:
                        if nuevo_estado:
                            st.session_state.progreso[ficha_id] = True
                        else:
                            st.session_state.progreso.pop(ficha_id, None)
                        guardar_progreso(st.session_state.progreso)
                        st.rerun()
                
                with col2:
                    st.markdown(f"**{row['Marca']}**")
                with col3:
                    st.markdown(row['Categoría'])
                with col4:
                    st.markdown(row['Producto'][:80] + "...")
                with col5:
                    if row['Número de Parte'] != 'N/D':
                        st.markdown(f"Parte: {row['Número de Parte']}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✅ Marcar todas las fichas filtradas"):
                    for _, row in df_revision.iterrows():
                        st.session_state.progreso[row['ID']] = True
                    guardar_progreso(st.session_state.progreso)
                    st.rerun()
            
            with col2:
                if st.button("🔄 Resetear todas las fichas filtradas"):
                    for _, row in df_revision.iterrows():
                        st.session_state.progreso.pop(row['ID'], None)
                    guardar_progreso(st.session_state.progreso)
                    st.rerun()
            
            with col3:
                total_revision = len(df_revision)
                completadas_revision = sum(st.session_state.progreso.get(row['ID'], False) for _, row in df_revision.iterrows())
                st.metric("Progreso", f"{completadas_revision}/{total_revision}")
        
        with tab7:
            st.markdown("### 📋 Listado Detallado")
            
            rows_per_page = st.selectbox("Filas por página", [10, 25, 50, 100], index=2, key="detail_rows")
            page_number = st.number_input("Página", min_value=1, value=1, step=1, key="detail_page")
            
            start_idx = (page_number - 1) * rows_per_page
            end_idx = start_idx + rows_per_page
            
            df_display = df_filtrado[['Marca', 'Categoría', 'Estado', 'Número de Parte', 'Producto']].copy()
            df_display['Revisado'] = df_filtrado['ID'].apply(lambda x: "✅" if st.session_state.progreso.get(x, False) else "⏳")
            df_display['Producto'] = df_display['Producto'].str[:100] + '...'
            
            st.dataframe(df_display.iloc[start_idx:end_idx], use_container_width=True)
            
            csv = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar resultados como CSV",
                data=csv,
                file_name="perucompras_resultados.csv",
                mime="text/csv"
            )
    else:
        st.error("❌ No se encontraron datos en el archivo")
else:
    st.info("👈 **Sube un archivo JSON** en el panel lateral para comenzar")

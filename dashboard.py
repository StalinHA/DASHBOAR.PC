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

# Archivo para guardar el progreso
PROGRESS_FILE = "progreso_marcas.json"

# CSS personalizado - Mejor contraste y legibilidad
st.markdown("""
<style>
    /* Fondo principal */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e9edf2 100%);
    }
    
    /* Header */
    .main-header {
        background: linear-gradient(90deg, #1a365d, #2c5282);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.95;
    }
    
    /* Tarjetas de estadísticas */
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        text-align: center;
        transition: transform 0.3s;
        border: 1px solid #e2e8f0;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.12);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #2c5282, #1a365d);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .stat-label {
        color: #4a5568;
        margin-top: 0.5rem;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2d3748, #1a202c);
        border-right: 1px solid #4a5568;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #f7fafc;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #edf2f7;
        border-radius: 12px;
        padding: 6px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        color: #2d3748;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #2c5282, #1a365d);
        color: white;
    }
    
    /* Texto general */
    .stMarkdown, .stText, .stMetric label {
        color: #2d3748;
    }
    
    /* Dataframe */
    .stDataFrame {
        background: white;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }
    
    /* Inputs */
    .stSelectbox, .stTextInput, .stNumberInput, .stTextArea {
        background-color: white;
        border-radius: 8px;
    }
    
    /* Botones */
    .stButton button {
        background: linear-gradient(90deg, #2c5282, #1a365d);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(44,82,130,0.3);
    }
    
    /* Info/Success/Warning boxes */
    .stAlert {
        background-color: #edf2f7;
        border-left: 4px solid #2c5282;
        color: #2d3748;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #edf2f7;
        border-radius: 8px;
        color: #2d3748;
        font-weight: 600;
    }
    
    /* Badges para marcas sin fichas */
    .no-data-badge {
        background-color: #e53e3e;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
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

def buscar_y_marcar_series(series_list, df):
    """Busca cada serie en la descripción del producto y la marca como completada"""
    encontradas = []
    no_encontradas = []
    
    for serie in series_list:
        serie_limpia = serie.strip()
        if not serie_limpia:
            continue
            
        # Buscar coincidencia exacta en el producto
        encontrada = False
        for _, row in df.iterrows():
            if serie_limpia in row['Producto']:
                encontrada = True
                # Marcar como completada
                st.session_state.progreso[row['ID']] = True
                encontradas.append({
                    'Serie': serie_limpia,
                    'Producto': row['Producto'][:200],
                    'Marca': row['Marca'],
                    'Categoría': row['Categoría']
                })
                break
        
        if not encontrada:
            no_encontradas.append(serie_limpia)
    
    guardar_progreso(st.session_state.progreso)
    return encontradas, no_encontradas

def exportar_excel_progreso(df, series_encontradas, series_no_encontradas):
    """Exporta a Excel el progreso con series encontradas y no encontradas"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Hoja 1: Series encontradas (completadas)
        if series_encontradas:
            df_encontradas = pd.DataFrame(series_encontradas)
            df_encontradas.to_excel(writer, sheet_name='Series Encontradas', index=False)
        
        # Hoja 2: Series no encontradas (pendientes)
        if series_no_encontradas:
            df_no_encontradas = pd.DataFrame({'Serie': series_no_encontradas})
            df_no_encontradas.to_excel(writer, sheet_name='Series No Encontradas', index=False)
        
        # Hoja 3: Resumen de fichas por marca
        resumen_marcas = df.groupby('Marca').size().reset_index(name='Total Fichas')
        resumen_marcas['Completadas'] = resumen_marcas['Marca'].apply(
            lambda x: sum(st.session_state.progreso.get(fila['ID'], False) for _, fila in df[df['Marca'] == x].iterrows())
        )
        resumen_marcas['Pendientes'] = resumen_marcas['Total Fichas'] - resumen_marcas['Completadas']
        resumen_marcas.to_excel(writer, sheet_name='Resumen por Marca', index=False)
        
        # Hoja 4: Todas las fichas con estado
        df_con_estado = df.copy()
        df_con_estado['Revisado'] = df_con_estado['ID'].apply(lambda x: 'COMPLETADA' if st.session_state.progreso.get(x, False) else 'PENDIENTE')
        df_con_estado[['Marca', 'Categoría', 'Producto', 'Estado', 'Revisado']].to_excel(writer, sheet_name='Todas las Fichas', index=False)
    
    output.seek(0)
    return output

# Inicializar estado de sesión
if 'progreso' not in st.session_state:
    st.session_state.progreso = cargar_progreso()
if 'df_actual' not in st.session_state:
    st.session_state.df_actual = None

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
    st.markdown("### 🏭 Marcas Reconocidas")
    st.markdown(f"**{len(MARCAS_COMPLETAS)} marcas** cargadas en el sistema")

# Procesar archivo
if archivo is not None:
    with st.spinner('🔄 Procesando archivo... Esto puede tomar unos segundos'):
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
        
        # Panel de progreso por marca
        st.markdown("---")
        st.markdown("### 📈 Panel de Progreso por Marca")
        
        progreso_marcas = []
        for marca in df['Marca'].unique():
            df_marca = df[df['Marca'] == marca]
            total_marca = len(df_marca)
            completadas_marca = sum(st.session_state.progreso.get(fila['ID'], False) for _, fila in df_marca.iterrows())
            porcentaje_marca = (completadas_marca / total_marca) * 100 if total_marca > 0 else 0
            progreso_marcas.append({
                'Marca': marca,
                'Total': total_marca,
                'Completadas': completadas_marca,
                'Porcentaje': porcentaje_marca
            })
        
        df_progreso_marcas = pd.DataFrame(progreso_marcas).sort_values('Porcentaje', ascending=False)
        
        fig_progreso = px.bar(df_progreso_marcas.head(15), 
                              x='Porcentaje', y='Marca', orientation='h',
                              title='Progreso por Marca (% Completado)',
                              text='Porcentaje',
                              color='Porcentaje',
                              color_continuous_scale='RdYlGn',
                              range_color=[0, 100])
        fig_progreso.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_progreso.update_layout(height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_progreso, use_container_width=True)
        
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
        
        # NUEVA PESTAÑA: Carga Masiva de Series
        with tab5:
            st.markdown("### 📦 Carga Masiva de Números de Serie")
            st.markdown("Pega una lista de números de serie (uno por línea) para buscar coincidencias exactas en las descripciones de los productos.")
            st.info("💡 **Formato aceptado:**\n- Un número de serie por línea\n- Hasta 10,000 series\n- Busca coincidencia EXACTA en la descripción del producto")
            
            series_input = st.text_area(
                "📝 Ingresa los números de serie (uno por línea):",
                height=200,
                placeholder="Ejemplo:\nM70SG51016201\nM70SG51016201SI\nM70SG51016211\nN50S67161F*\nNEO55SR716100"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔍 Buscar y Marcar Series", type="primary"):
                    if series_input.strip():
                        series_list = [s.strip() for s in series_input.strip().split('\n') if s.strip()]
                        
                        with st.spinner(f'Buscando {len(series_list)} series...'):
                            encontradas, no_encontradas = buscar_y_marcar_series(series_list, df)
                            
                            st.success(f"✅ Búsqueda completada!")
                            st.metric("Series encontradas", len(encontradas))
                            st.metric("Series NO encontradas", len(no_encontradas))
                            
                            if encontradas:
                                st.markdown("#### ✅ Series encontradas:")
                                st.dataframe(pd.DataFrame(encontradas), use_container_width=True)
                            
                            if no_encontradas:
                                st.markdown("#### ❌ Series NO encontradas:")
                                st.write(no_encontradas[:50])
                                if len(no_encontradas) > 50:
                                    st.caption(f"... y {len(no_encontradas) - 50} más")
                    else:
                        st.warning("⚠️ Por favor ingresa al menos un número de serie")
            
            with col2:
                # Botón para exportar Excel con el progreso actual
                if st.button("📊 Exportar a Excel (Progreso Actual)"):
                    series_encontradas = []
                    series_no_encontradas = []
                    
                    # Generar Excel con el progreso actual
                    excel_file = exportar_excel_progreso(df, series_encontradas, series_no_encontradas)
                    
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

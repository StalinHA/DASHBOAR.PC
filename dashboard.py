import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import re
from collections import defaultdict
from io import BytesIO

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

# CSS personalizado
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .main-header {
        background: linear-gradient(90deg, #667eea, #764ba2);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .main-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.3s;
    }
    .stat-card:hover {
        transform: translateY(-5px);
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .stat-label {
        color: #666;
        margin-top: 0.5rem;
        font-size: 0.9rem;
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
                        fichas.append({
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

# Título principal
st.markdown("""
<div class="main-header">
    <h1>📊 Dashboard Perú Compras</h1>
    <p>Analizador profesional de fichas técnicas - 66 marcas reconocidas</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📁 Carga tu archivo")
    archivo = st.file_uploader("Selecciona tu archivo JSON", type=['json'])
    
    st.markdown("---")
    st.markdown("### 🏭 Marcas Reconocidas")
    st.markdown(f"**{len(MARCAS_COMPLETAS)} marcas** cargadas en el sistema")

# Procesar archivo
if archivo is not None:
    with st.spinner('🔄 Procesando archivo... Esto puede tomar unos segundos'):
        df = procesar_json(archivo)
    
    if len(df) > 0:
        st.success(f"✅ ¡Éxito! Se cargaron **{len(df):,}** fichas técnicas")
        
        # Métricas principales
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📦 Total Fichas", f"{len(df):,}")
        with col2:
            marcas_detectadas = df[df['Marca'] != 'SIN MARCA']['Marca'].nunique()
            st.metric("🏭 Marcas Detectadas", marcas_detectadas)
        with col3:
            st.metric("📁 Categorías", df['Categoría'].nunique())
        with col4:
            propuestas = len(df[df['Estado'] == 'PROPUESTA'])
            st.metric("📌 En PROPUESTA", f"{propuestas:,}")
        with col5:
            ofertadas = len(df[df['Estado'] == 'OFERTADA SIN OFERTA'])
            st.metric("⚠️ Sin Oferta", f"{ofertadas:,}")
        
        # Filtros
        st.markdown("---")
        st.markdown("### 🔍 Filtros Inteligentes")
        
        col1, col2, col3, col4 = st.columns(4)
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
            busqueda_texto = st.text_input("🔎 Búsqueda libre", placeholder="Producto o número de parte...")
        
        # Aplicar filtros
        df_filtrado = df.copy()
        if marca_filter != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['Marca'] == marca_filter]
        if estado_filter != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Estado'] == estado_filter]
        if categoria_filter != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['Categoría'] == categoria_filter]
        if busqueda_texto:
            df_filtrado = df_filtrado[
                df_filtrado['Producto'].str.contains(busqueda_texto, case=False, na=False) |
                df_filtrado['Número de Parte'].str.contains(busqueda_texto, case=False, na=False)
            ]
        
        st.info(f"📊 Mostrando **{len(df_filtrado):,}** de **{len(df):,}** fichas")
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Resumen General", 
            "🏭 Análisis por Marca", 
            "📂 Análisis por Categoría", 
            "📋 Tabla Detallada"
        ])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                estados_counts = df_filtrado['Estado'].value_counts().reset_index()
                estados_counts.columns = ['Estado', 'Cantidad']
                fig_estados = px.pie(estados_counts, values='Cantidad', names='Estado', 
                                     title='📌 Distribución por Estado', hole=0.4)
                st.plotly_chart(fig_estados, use_container_width=True)
            
            with col2:
                top_marcas = df_filtrado['Marca'].value_counts().head(10).reset_index()
                top_marcas.columns = ['Marca', 'Cantidad']
                fig_marcas = px.bar(top_marcas, x='Cantidad', y='Marca', orientation='h',
                                    title='🏭 Top 10 Marcas', text='Cantidad')
                st.plotly_chart(fig_marcas, use_container_width=True)
            
            top_categorias = df_filtrado['Categoría'].value_counts().head(10).reset_index()
            top_categorias.columns = ['Categoría', 'Cantidad']
            fig_cat = px.bar(top_categorias, x='Categoría', y='Cantidad',
                             title='📁 Top 10 Categorías', text='Cantidad')
            fig_cat.update_xaxes(tickangle=45)
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with tab2:
            marca_analisis = st.selectbox("Selecciona una marca", sorted(df['Marca'].unique()))
            
            if marca_analisis:
                df_marca = df[df['Marca'] == marca_analisis]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Fichas", f"{len(df_marca):,}")
                with col2:
                    st.metric("Categorías", df_marca['Categoría'].nunique())
                with col3:
                    propuestas_marca = len(df_marca[df_marca['Estado'] == 'PROPUESTA'])
                    st.metric("En PROPUESTA", f"{propuestas_marca:,}")
                
                estados_marca = df_marca['Estado'].value_counts().reset_index()
                estados_marca.columns = ['Estado', 'Cantidad']
                fig_marca_estados = px.bar(estados_marca, x='Estado', y='Cantidad',
                                           title=f'📌 Estados - {marca_analisis}', text='Cantidad')
                st.plotly_chart(fig_marca_estados, use_container_width=True)
        
        with tab3:
            categoria_analisis = st.selectbox("Selecciona una categoría", sorted(df['Categoría'].unique()))
            
            if categoria_analisis:
                df_categoria = df[df['Categoría'] == categoria_analisis]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Fichas", f"{len(df_categoria):,}")
                with col2:
                    st.metric("Marcas", df_categoria['Marca'].nunique())
                
                marcas_categoria = df_categoria['Marca'].value_counts().reset_index()
                marcas_categoria.columns = ['Marca', 'Cantidad']
                fig_cat_marcas = px.bar(marcas_categoria, x='Cantidad', y='Marca', orientation='h',
                                        title=f'🏭 Marcas en {categoria_analisis}', text='Cantidad')
                st.plotly_chart(fig_cat_marcas, use_container_width=True)
        
        with tab4:
            st.markdown("### 📋 Listado Detallado")
            
            rows_per_page = st.selectbox("Filas por página", [10, 25, 50, 100], index=2)
            page_number = st.number_input("Página", min_value=1, value=1, step=1)
            
            start_idx = (page_number - 1) * rows_per_page
            end_idx = start_idx + rows_per_page
            
            df_display = df_filtrado[['Marca', 'Categoría', 'Estado', 'Número de Parte', 'Producto']].copy()
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
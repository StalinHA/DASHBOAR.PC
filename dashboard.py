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
    .completed-card {
        background: linear-gradient(135deg, #10b981, #059669);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .pending-card {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
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
                        # Crear un ID único para cada ficha
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
    """Carga el progreso guardado"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def guardar_progreso(progreso):
    """Guarda el progreso"""
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progreso, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def exportar_progreso():
    """Exporta el progreso como JSON descargable"""
    progreso = cargar_progreso()
    return json.dumps(progreso, ensure_ascii=False, indent=2)

def importar_progreso(archivo_json):
    """Importa progreso desde un archivo JSON"""
    try:
        progreso = json.load(archivo_json)
        guardar_progreso(progreso)
        return True
    except:
        return False

# Inicializar estado de sesión
if 'progreso' not in st.session_state:
    st.session_state.progreso = cargar_progreso()
if 'df_actual' not in st.session_state:
    st.session_state.df_actual = None
if 'marcas_completadas_actualizadas' not in st.session_state:
    st.session_state.marcas_completadas_actualizadas = False

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
    
    # Botones para compartir progreso
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
        with col6:
            # Calcular progreso general
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
            # Filtro por estado de completado
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
            else:  # Pendientes
                df_filtrado = df_filtrado[df_filtrado['ID'].apply(lambda x: not st.session_state.progreso.get(x, False))]
        if busqueda_texto:
            df_filtrado = df_filtrado[
                df_filtrado['Producto'].str.contains(busqueda_texto, case=False, na=False) |
                df_filtrado['Número de Parte'].str.contains(busqueda_texto, case=False, na=False)
            ]
        
        st.info(f"📊 Mostrando **{len(df_filtrado):,}** de **{len(df):,}** fichas")
        
        # Panel de progreso por marca y categoría
        st.markdown("---")
        st.markdown("### 📈 Panel de Progreso")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏭 Progreso por Marca")
            # Calcular progreso por marca
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
            
            # Mostrar top 10 marcas por progreso
            fig_progreso = px.bar(df_progreso_marcas.head(10), 
                                  x='Porcentaje', y='Marca', orientation='h',
                                  title='Top 10 Marcas por % Completado',
                                  text='Porcentaje',
                                  color='Porcentaje',
                                  color_continuous_scale='RdYlGn',
                                  range_color=[0, 100])
            fig_progreso.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            st.plotly_chart(fig_progreso, use_container_width=True)
        
        with col2:
            st.markdown("#### 📂 Progreso por Categoría")
            # Calcular progreso por categoría
            progreso_categorias = []
            for categoria in df['Categoría'].unique():
                df_cat = df[df['Categoría'] == categoria]
                total_cat = len(df_cat)
                completadas_cat = sum(st.session_state.progreso.get(fila['ID'], False) for _, fila in df_cat.iterrows())
                porcentaje_cat = (completadas_cat / total_cat) * 100 if total_cat > 0 else 0
                progreso_categorias.append({
                    'Categoría': categoria[:30],  # Limitar longitud
                    'Total': total_cat,
                    'Completadas': completadas_cat,
                    'Porcentaje': porcentaje_cat
                })
            
            df_progreso_categorias = pd.DataFrame(progreso_categorias).sort_values('Porcentaje', ascending=False)
            
            # Mostrar top 10 categorías por progreso
            fig_progreso_cat = px.bar(df_progreso_categorias.head(10), 
                                      x='Porcentaje', y='Categoría', orientation='h',
                                      title='Top 10 Categorías por % Completado',
                                      text='Porcentaje',
                                      color='Porcentaje',
                                      color_continuous_scale='RdYlGn',
                                      range_color=[0, 100])
            fig_progreso_cat.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            st.plotly_chart(fig_progreso_cat, use_container_width=True)
        
        # Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Resumen General", 
            "🏭 Análisis por Marca", 
            "📂 Análisis por Categoría",
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
                
                marcas_categoria = df_categoria['Marca'].value_counts().reset_index()
                marcas_categoria.columns = ['Marca', 'Cantidad']
                fig_cat_marcas = px.bar(marcas_categoria, x='Cantidad', y='Marca', orientation='h',
                                        title=f'🏭 Marcas en {categoria_analisis}', text='Cantidad')
                st.plotly_chart(fig_cat_marcas, use_container_width=True)
        
        with tab4:
            st.markdown("### ✅ Revisión de Fichas")
            st.markdown("Marca las fichas que ya has revisado/completado. ¡El progreso se guarda automáticamente!")
            
            # Selector para navegar por marca/categoría
            col1, col2 = st.columns(2)
            with col1:
                marca_revision = st.selectbox("Filtrar por marca", ["Todas"] + sorted(df['Marca'].unique()), key="revision_marca")
            with col2:
                categoria_revision = st.selectbox("Filtrar por categoría", ["Todas"] + sorted(df['Categoría'].unique()), key="revision_categoria")
            
            # Aplicar filtros para la tabla de revisión
            df_revision = df.copy()
            if marca_revision != "Todas":
                df_revision = df_revision[df_revision['Marca'] == marca_revision]
            if categoria_revision != "Todas":
                df_revision = df_revision[df_revision['Categoría'] == categoria_revision]
            
            # Paginación para la tabla de revisión
            rows_per_page_review = st.selectbox("Filas por página", [10, 25, 50, 100], index=1, key="review_rows")
            page_review = st.number_input("Página", min_value=1, value=1, step=1, key="review_page")
            
            start_idx_review = (page_review - 1) * rows_per_page_review
            end_idx_review = start_idx_review + rows_per_page_review
            
            # Mostrar tabla con checkboxes
            st.markdown("#### Marca las fichas revisadas:")
            
            for idx, (_, row) in enumerate(df_revision.iloc[start_idx_review:end_idx_review].iterrows()):
                col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 1])
                ficha_id = row['ID']
                is_checked = st.session_state.progreso.get(ficha_id, False)
                
                with col1:
                    nuevo_estado = st.checkbox("✅", value=is_checked, key=f"check_{ficha_id}")
                    if nuevo_estado != is_checked:
                        if nuevo_estado:
                            st.session_state.progreso[ficha_id] = True
                        else:
                            st.session_state.progreso.pop(ficha_id, None)
                        guardar_progreso(st.session_state.progreso)
                        st.rerun()
                
                with col2:
                    st.markdown(f"**Marca:** {row['Marca']}")
                with col3:
                    st.markdown(f"**Categoría:** {row['Categoría']}")
                with col4:
                    st.markdown(f"**Producto:** {row['Producto'][:80]}...")
                with col5:
                    if row['Número de Parte'] != 'N/D':
                        st.markdown(f"**Parte:** {row['Número de Parte']}")
            
            # Botones de acción rápida
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✅ Marcar todas las fichas filtradas como completadas"):
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
                st.metric("Progreso en este filtro", f"{completadas_revision}/{total_revision}")
        
        with tab5:
            st.markdown("### 📋 Listado Detallado")
            
            rows_per_page = st.selectbox("Filas por página", [10, 25, 50, 100], index=2, key="detail_rows")
            page_number = st.number_input("Página", min_value=1, value=1, step=1, key="detail_page")
            
            start_idx = (page_number - 1) * rows_per_page
            end_idx = start_idx + rows_per_page
            
            # Agregar columna de estado de revisión
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

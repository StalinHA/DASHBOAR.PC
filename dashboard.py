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

# CSS personalizado
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%); }
    .main-header {
        background: linear-gradient(90deg, #2563eb, #1e40af);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .main-header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; font-weight: 700; color: white; }
    .main-header p { font-size: 1.1rem; opacity: 0.95; color: #e2e8f0; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a, #020617); border-right: 1px solid #334155; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #1e293b; border-radius: 12px; padding: 6px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 8px 20px; color: #cbd5e1; font-weight: 600; }
    .stTabs [aria-selected="true"] { background: linear-gradient(90deg, #3b82f6, #2563eb); color: white; }
    .stMarkdown, .stText, .stMetric label { color: #f1f5f9; }
    .stButton button { background: linear-gradient(90deg, #3b82f6, #2563eb); color: white; border: none; border-radius: 8px; }
    .stButton button:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(59,130,246,0.4); }
    .stAlert { background-color: #1e293b; border-left: 4px solid #3b82f6; color: #e2e8f0; }
    .no-data-badge { background-color: #ef4444; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; display: inline-block; }
    [data-testid="stMetricValue"] { color: #60a5fa; }
    [data-testid="stMetricLabel"] { color: #cbd5e1; }
    .stDataFrame { background: #1e293b; border-radius: 12px; border: 1px solid #334155; }
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

def buscar_y_marcar_series_con_filtro(nuevas_series, df, series_procesadas, marca_filtro=None, categoria_filtro=None):
    """Busca series con coincidencia EXACTA y filtro opcional por marca/categoría"""
    nuevas = [s for s in nuevas_series if s not in series_procesadas]
    duplicados = [s for s in nuevas_series if s in series_procesadas]
    
    encontradas = []
    no_encontradas = []
    ids_marcados = set()
    
    # Filtrar dataframe si se especifica marca o categoría
    df_busqueda = df.copy()
    if marca_filtro and marca_filtro != "Todas":
        df_busqueda = df_busqueda[df_busqueda['Marca'] == marca_filtro]
    if categoria_filtro and categoria_filtro != "Todas":
        df_busqueda = df_busqueda[df_busqueda['Categoría'] == categoria_filtro]
    
    for serie in nuevas:
        serie_limpia = serie.strip()
        if not serie_limpia:
            continue
        
        # Buscar coincidencia EXACTA (caracter a caracter completo)
        ficha_encontrada = None
        for _, row in df_busqueda.iterrows():
            producto = str(row['Producto'])
            # Coincidencia exacta - la serie debe aparecer como palabra completa
            if serie_limpia in producto.split() or \
               producto.startswith(serie_limpia + ' ') or \
               producto.endswith(' ' + serie_limpia) or \
               f' {serie_limpia} ' in f' {producto} ':
                ficha_encontrada = row
                break
        
        if ficha_encontrada is not None and ficha_encontrada['ID'] not in ids_marcados:
            st.session_state.progreso[ficha_encontrada['ID']] = True
            ids_marcados.add(ficha_encontrada['ID'])
            encontradas.append({
                'Serie': serie_limpia,
                'Producto': ficha_encontrada['Producto'][:200],
                'Marca': ficha_encontrada['Marca'],
                'Categoría': ficha_encontrada['Categoría'],
                'ID_Ficha': ficha_encontrada['ID']
            })
        elif ficha_encontrada is None:
            no_encontradas.append(serie_limpia)
    
    series_procesadas.update(nuevas)
    guardar_series_procesadas(series_procesadas)
    guardar_progreso(st.session_state.progreso)
    
    return encontradas, no_encontradas, duplicados

def exportar_excel_progreso(df, series_encontradas, series_no_encontradas):
    output = BytesIO()
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if series_encontradas:
                pd.DataFrame(series_encontradas).to_excel(writer, sheet_name='Series Encontradas', index=False)
            else:
                pd.DataFrame({'Mensaje': ['No hay series encontradas']}).to_excel(writer, sheet_name='Series Encontradas', index=False)
            
            if series_no_encontradas:
                pd.DataFrame({'Serie': series_no_encontradas}).to_excel(writer, sheet_name='Series No Encontradas', index=False)
            else:
                pd.DataFrame({'Mensaje': ['Todas las series fueron encontradas']}).to_excel(writer, sheet_name='Series No Encontradas', index=False)
            
            resumen_marcas = df.groupby('Marca').size().reset_index(name='Total Fichas')
            resumen_marcas['Completadas'] = resumen_marcas['Marca'].apply(
                lambda x: sum(1 for _, row in df[df['Marca'] == x].iterrows() if st.session_state.progreso.get(row['ID'], False))
            )
            resumen_marcas['Porcentaje'] = (resumen_marcas['Completadas'] / resumen_marcas['Total Fichas'] * 100).round(1)
            resumen_marcas.to_excel(writer, sheet_name='Resumen por Marca', index=False)
            
            df_con_estado = df.copy()
            df_con_estado['Revisado'] = df_con_estado['ID'].apply(lambda x: 'COMPLETADA' if st.session_state.progreso.get(x, False) else 'PENDIENTE')
            df_con_estado[['Marca', 'Categoría', 'Producto', 'Estado', 'Revisado']].to_excel(writer, sheet_name='Todas las Fichas', index=False)
    except Exception as e:
        st.error(f"Error al exportar: {e}")
        return None
    output.seek(0)
    return output

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
if 'limpiar_textarea' not in st.session_state:
    st.session_state.limpiar_textarea = False

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
        st.download_button(
            label="📤 Exportar progreso",
            data=exportar_progreso(),
            file_name=f"progreso_marcas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    with col2:
        archivo_progreso = st.file_uploader("📥 Importar", type=['json'], key="progress_uploader")
        if archivo_progreso is not None:
            if importar_progreso(archivo_progreso):
                st.success("✅ Importado!")
                st.session_state.progreso = cargar_progreso()
                st.rerun()
    
    st.markdown("---")
    st.markdown("### 🗑️ Limpiar")
    
    if st.button("⚠️ RESET TOTAL", type="primary", use_container_width=True):
        st.session_state.progreso = {}
        st.session_state.series_procesadas = set()
        guardar_progreso({})
        guardar_series_procesadas(set())
        st.success("✅ Reseteado!")
        st.rerun()
    
    st.markdown("---")
    st.markdown(f"**🏭 {len(MARCAS_COMPLETAS)} marcas**")
    st.markdown(f"**📊 {len(st.session_state.series_procesadas)} series** procesadas")

# Procesar archivo
if archivo is not None:
    with st.spinner('🔄 Procesando archivo...'):
        df = procesar_json(archivo)
        st.session_state.df_actual = df
    
    if len(df) > 0:
        st.success(f"✅ Se cargaron **{len(df):,}** fichas técnicas")
        
        # Métricas
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        fichas_completadas = sum(st.session_state.progreso.get(fila['ID'], False) for _, fila in df.iterrows())
        
        with col1:
            st.metric("📦 Total Fichas", f"{len(df):,}")
        with col2:
            st.metric("🏭 Marcas", df['Marca'].nunique())
        with col3:
            st.metric("⚠️ Sin Fichas", len([m for m in MARCAS_COMPLETAS if m not in df['Marca'].values]))
        with col4:
            st.metric("📌 En PROPUESTA", f"{len(df[df['Estado'] == 'PROPUESTA']):,}")
        with col5:
            st.metric("⚠️ Sin Oferta", f"{len(df[df['Estado'] == 'OFERTADA SIN OFERTA']):,}")
        with col6:
            st.metric("✅ Progreso", f"{(fichas_completadas/len(df)*100):.1f}%")
        
        st.progress(fichas_completadas/len(df) if len(df)>0 else 0)
        
        # Panel de marcas sin fichas
        marcas_sin_datos = [m for m in MARCAS_COMPLETAS if m not in set(df['Marca'].unique())]
        if marcas_sin_datos:
            st.markdown("### ⚠️ Marcas sin fichas")
            cols = st.columns(8)
            for i, marca in enumerate(marcas_sin_datos[:16]):
                with cols[i % 8]:
                    st.markdown(f"<span class='no-data-badge'>⚠️ {marca}</span>", unsafe_allow_html=True)
        
        # Progreso por marca (diseño compacto)
        st.markdown("---")
        st.markdown("### 📈 Progreso por Marca")
        
        datos_marcas = []
        for marca in sorted(df['Marca'].unique()):
            df_marca = df[df['Marca'] == marca]
            total = len(df_marca)
            comp = sum(st.session_state.progreso.get(fila['ID'], False) for _, fila in df_marca.iterrows())
            pct = (comp/total*100) if total>0 else 0
            datos_marcas.append({'Marca': marca, 'Total': total, 'Completadas': comp, 'Porcentaje': pct})
        
        df_marcas = pd.DataFrame(datos_marcas).sort_values('Porcentaje', ascending=False)
        
        for _, row in df_marcas.head(8).iterrows():
            col1, col2, col3 = st.columns([2, 3, 1])
            with col1:
                st.markdown(f"**{row['Marca']}**")
            with col2:
                st.progress(row['Porcentaje']/100)
            with col3:
                st.markdown(f"`{row['Completadas']}/{row['Total']} ({row['Porcentaje']:.0f}%)`")
        
        if len(df_marcas) > 8:
            with st.expander(f"Ver otras {len(df_marcas)-8} marcas"):
                for _, row in df_marcas.iloc[8:].iterrows():
                    col1, col2, col3 = st.columns([2, 3, 1])
                    with col1:
                        st.markdown(row['Marca'])
                    with col2:
                        st.progress(row['Porcentaje']/100)
                    with col3:
                        st.markdown(f"`{row['Completadas']}/{row['Total']}`")
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📦 Carga Masiva de Series", 
            "✅ Revisión de Fichas", 
            "📋 Tabla Detallada",
            "📊 Análisis"
        ])
        
        # TAB 1: Carga de Series con filtro
        with tab1:
            st.markdown("### 📦 Carga Masiva de Números de Serie")
            st.markdown("Cada serie se compara caracter por caracter (coincidencia EXACTA)")
            
            # Selectores de filtro
            col_filtro1, col_filtro2 = st.columns(2)
            with col_filtro1:
                marcas_lista = ['Todas'] + sorted(df['Marca'].unique().tolist())
                marca_busqueda = st.selectbox("🔍 Filtrar por marca (opcional)", marcas_lista, key="filtro_marca")
            with col_filtro2:
                categorias_lista = ['Todas'] + sorted(df['Categoría'].unique().tolist())
                categoria_busqueda = st.selectbox("📂 Filtrar por categoría (opcional)", categorias_lista, key="filtro_categoria")
            
            # Textarea con key dinámica para limpiar
            textarea_key = "series_input"
            if st.session_state.get('limpiar_textarea', False):
                textarea_key = f"series_input_{datetime.now().timestamp()}"
                st.session_state.limpiar_textarea = False
            
            series_input = st.text_area(
                "📝 Ingresa números de serie (uno por línea):",
                height=150,
                key=textarea_key,
                placeholder="Ejemplo:\nLH75WAFWLGCXZX\nLH75WAFWLGCXZX-RM\nLH86WAFPLGCXZX"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔍 Buscar y Marcar", type="primary", use_container_width=True):
                    if series_input.strip():
                        nuevas_series = [s.strip() for s in series_input.strip().split('\n') if s.strip()]
                        
                        filtro_marca = None if marca_busqueda == "Todas" else marca_busqueda
                        filtro_categoria = None if categoria_busqueda == "Todas" else categoria_busqueda
                        
                        with st.spinner(f'Buscando {len(nuevas_series)} series...'):
                            encontradas, no_encontradas, duplicados = buscar_y_marcar_series_con_filtro(
                                nuevas_series, df, st.session_state.series_procesadas,
                                filtro_marca, filtro_categoria
                            )
                            
                            st.session_state.ultimas_encontradas = encontradas
                            st.session_state.ultimas_no_encontradas = no_encontradas
                            
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("✅ Encontradas", len(encontradas))
                            with col_b:
                                st.metric("❌ No encontradas", len(no_encontradas))
                            with col_c:
                                st.metric("🔄 Duplicadas", len(duplicados))
                            
                            if encontradas:
                                st.markdown("#### ✅ Series encontradas:")
                                st.dataframe(pd.DataFrame(encontradas), use_container_width=True)
                                
                                # Resumen por marca
                                df_resumen = pd.DataFrame(encontradas)
                                if len(df_resumen) > 0:
                                    st.markdown("#### 📊 Resumen por marca:")
                                    st.dataframe(df_resumen.groupby('Marca').size().reset_index(name='Encontradas'), use_container_width=True)
                            
                            if no_encontradas:
                                st.markdown("#### ❌ Series NO encontradas:")
                                st.write(no_encontradas[:30])
                            
                            # Actualizar progreso
                            fichas_comp = sum(st.session_state.progreso.get(fila['ID'], False) for _, fila in df.iterrows())
                            st.info(f"📊 Progreso total: **{(fichas_comp/len(df)*100):.1f}%** ({fichas_comp}/{len(df)})")
                    else:
                        st.warning("⚠️ Ingresa al menos un número de serie")
            
            with col2:
                if st.button("💾 Guardar y Limpiar", use_container_width=True):
                    if series_input.strip():
                        nuevas_series = [s.strip() for s in series_input.strip().split('\n') if s.strip()]
                        filtro_marca = None if marca_busqueda == "Todas" else marca_busqueda
                        filtro_categoria = None if categoria_busqueda == "Todas" else categoria_busqueda
                        
                        with st.spinner(f'Procesando {len(nuevas_series)} series...'):
                            encontradas, no_encontradas, duplicados = buscar_y_marcar_series_con_filtro(
                                nuevas_series, df, st.session_state.series_procesadas,
                                filtro_marca, filtro_categoria
                            )
                            st.session_state.ultimas_encontradas = encontradas
                            st.session_state.ultimas_no_encontradas = no_encontradas
                            st.session_state.limpiar_textarea = True
                            st.success(f"✅ Guardado: {len(encontradas)} encontradas, {len(no_encontradas)} no encontradas")
                            st.rerun()
                    else:
                        st.warning("⚠️ Ingresa series antes de guardar")
            
            # Botón de exportar Excel
            if st.button("📊 Exportar a Excel", use_container_width=True):
                excel_file = exportar_excel_progreso(df, st.session_state.ultimas_encontradas, st.session_state.ultimas_no_encontradas)
                if excel_file:
                    st.download_button(
                        label="📥 Descargar Excel",
                        data=excel_file,
                        file_name=f"progreso_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        
        # TAB 2: Revisión Manual
        with tab2:
            st.markdown("### ✅ Revisión Manual de Fichas")
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                marca_revision = st.selectbox("Filtrar por marca", ["Todas"] + sorted(df['Marca'].unique()), key="rev_marca")
            with col_f2:
                categoria_revision = st.selectbox("Filtrar por categoría", ["Todas"] + sorted(df['Categoría'].unique()), key="rev_categoria")
            
            df_revision = df.copy()
            if marca_revision != "Todas":
                df_revision = df_revision[df_revision['Marca'] == marca_revision]
            if categoria_revision != "Todas":
                df_revision = df_revision[df_revision['Categoría'] == categoria_revision]
            
            # Paginación
            items_por_pagina = 10
            total_paginas = max(1, (len(df_revision) + items_por_pagina - 1) // items_por_pagina)
            pagina = st.number_input("Página", min_value=1, max_value=total_paginas, value=1, step=1)
            
            inicio = (pagina - 1) * items_por_pagina
            fin = inicio + items_por_pagina
            
            for idx, (_, row) in enumerate(df_revision.iloc[inicio:fin].iterrows()):
                cols = st.columns([1, 2, 2, 3, 1])
                is_checked = st.session_state.progreso.get(row['ID'], False)
                checkbox_key = f"rev_{row['ID']}_{idx}_{pagina}"
                
                with cols[0]:
                    nuevo_estado = st.checkbox("✅", value=is_checked, key=checkbox_key)
                    if nuevo_estado != is_checked:
                        if nuevo_estado:
                            st.session_state.progreso[row['ID']] = True
                        else:
                            st.session_state.progreso.pop(row['ID'], None)
                        guardar_progreso(st.session_state.progreso)
                        st.rerun()
                
                with cols[1]:
                    st.markdown(f"**{row['Marca']}**")
                with cols[2]:
                    st.markdown(row['Categoría'])
                with cols[3]:
                    st.caption(row['Producto'][:80])
                with cols[4]:
                    if row['Número de Parte'] != 'N/D':
                        st.code(row['Número de Parte'], language="text")
            
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                if st.button("✅ Marcar todas visibles", use_container_width=True):
                    for _, row in df_revision.iloc[inicio:fin].iterrows():
                        st.session_state.progreso[row['ID']] = True
                    guardar_progreso(st.session_state.progreso)
                    st.rerun()
            with col_b2:
                if st.button("🔄 Resetear visibles", use_container_width=True):
                    for _, row in df_revision.iloc[inicio:fin].iterrows():
                        st.session_state.progreso.pop(row['ID'], None)
                    guardar_progreso(st.session_state.progreso)
                    st.rerun()
            with col_b3:
                comp_actual = sum(1 for _, row in df_revision.iterrows() if st.session_state.progreso.get(row['ID'], False))
                st.metric("Progreso filtro", f"{comp_actual}/{len(df_revision)}")
        
        # TAB 3: Tabla Detallada
        with tab3:
            st.markdown("### 📋 Listado Detallado")
            
            df_display = df[['Marca', 'Categoría', 'Estado', 'Número de Parte', 'Producto']].copy()
            df_display['Revisado'] = df['ID'].apply(lambda x: "✅" if st.session_state.progreso.get(x, False) else "⏳")
            df_display['Producto'] = df_display['Producto'].str[:100] + '...'
            st.dataframe(df_display, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 CSV", csv, "datos.csv", "text/csv")
        
        # TAB 4: Análisis
        with tab4:
            st.markdown("### 📊 Análisis de Datos")
            
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                estados_counts = df['Estado'].value_counts().reset_index()
                estados_counts.columns = ['Estado', 'Cantidad']
                fig_estados = px.pie(estados_counts, values='Cantidad', names='Estado', title='Distribución por Estado', hole=0.4)
                fig_estados.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_estados, use_container_width=True)
            
            with col_a2:
                top_marcas = df['Marca'].value_counts().head(10).reset_index()
                top_marcas.columns = ['Marca', 'Cantidad']
                fig_marcas = px.bar(top_marcas, x='Cantidad', y='Marca', orientation='h', title='Top 10 Marcas', text='Cantidad')
                fig_marcas.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_marcas, use_container_width=True)
    else:
        st.error("❌ No se encontraron datos")
else:
    st.info("👈 **Sube un archivo JSON** para comenzar")

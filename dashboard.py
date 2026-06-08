import streamlit as st
import pandas as pd
import plotly.express as px
import json
import re
from io import BytesIO
from datetime import datetime
import os

# Configuración
st.set_page_config(page_title="Dashboard Perú Compras", page_icon="📊", layout="wide")

# ==================== CONSTANTES ====================
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

PROGRESS_FILE = "progreso_marcas.json"
SERIES_PROCESSED_FILE = "series_procesadas.json"

# ==================== CSS MEJORADO ====================
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
    .main-header {
        background: linear-gradient(90deg, #2563eb, #1e40af);
        padding: 1.5rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { color: white; margin: 0; font-size: 1.8rem; }
    .main-header p { color: #e2e8f0; margin: 0.5rem 0 0 0; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a, #020617); }
    .stMetric label { color: #cbd5e1 !important; }
    .stMetric value { color: #60a5fa !important; }
    .stButton button { background: #3b82f6; color: white; border-radius: 8px; }
    .stButton button:hover { background: #2563eb; }
    .stAlert { background-color: #1e293b; border-left-color: #3b82f6; }
</style>
""", unsafe_allow_html=True)

# ==================== FUNCIONES PRINCIPALES ====================
def extraer_marca(producto):
    if not producto:
        return "SIN MARCA"
    producto_upper = producto.upper()
    for marca in sorted(MARCAS_COMPLETAS, key=len, reverse=True):
        if marca.upper() in producto_upper:
            return marca
    return "OTRA MARCA"

def procesar_json(archivo):
    try:
        datos = json.load(archivo)
        fichas = []
        for catalogo in datos.get('catalogos', []):
            for categoria in catalogo.get('categorias', []):
                for ficha in categoria.get('fichas', []):
                    producto = ficha.get('producto', '')
                    fichas.append({
                        'ID': f"{catalogo.get('nombre')}_{categoria.get('nombre')}_{producto[:50]}",
                        'Categoría': categoria.get('nombre', 'SIN CATEGORÍA'),
                        'Producto': producto,
                        'Marca': extraer_marca(producto),
                        'Estado': ficha.get('estado', 'SIN ESTADO'),
                        'Número de Parte': re.search(r'([A-Z0-9]{4,}(?:[-#][A-Z0-9]{3,}))', producto.upper()) or ['N/D']
                    })
                    fichas[-1]['Número de Parte'] = fichas[-1]['Número de Parte'][0][:30] if isinstance(fichas[-1]['Número de Parte'], tuple) else "N/D"
        return pd.DataFrame(fichas)
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

def cargar_progreso():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def guardar_progreso(progreso):
    try:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progreso, f)
        return True
    except:
        return False

def buscar_y_marcar_series(nuevas_series, df, series_procesadas):
    """CADA SERIE MARCA UNA SOLA FICHA - Coincidencia exacta"""
    nuevas = [s for s in nuevas_series if s not in series_procesadas]
    duplicados = [s for s in nuevas_series if s in series_procesadas]
    
    encontradas = []
    no_encontradas = []
    ids_marcados = set()
    
    for serie in nuevas:
        serie = serie.strip()
        if not serie:
            continue
        
        # Buscar coincidencia exacta
        ficha = None
        for _, row in df.iterrows():
            producto = str(row['Producto'])
            if f' {serie} ' in f' {producto} ' or producto.startswith(serie) or producto.endswith(serie):
                ficha = row
                break
        
        if ficha is not None and ficha['ID'] not in ids_marcados:
            st.session_state.progreso[ficha['ID']] = True
            ids_marcados.add(ficha['ID'])
            encontradas.append({
                'Serie': serie, 'Producto': ficha['Producto'][:150],
                'Marca': ficha['Marca'], 'Categoría': ficha['Categoría']
            })
        elif ficha is None:
            no_encontradas.append(serie)
    
    series_procesadas.update(nuevas)
    guardar_progreso(st.session_state.progreso)
    return encontradas, no_encontradas, duplicados

# ==================== INICIALIZACIÓN ====================
if 'progreso' not in st.session_state:
    st.session_state.progreso = cargar_progreso()
if 'series_procesadas' not in st.session_state:
    st.session_state.series_procesadas = set()

# ==================== HEADER ====================
st.markdown('<div class="main-header"><h1>📊 Dashboard Perú Compras</h1><p>Seguimiento de progreso por marca</p></div>', unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### 📁 Cargar JSON")
    archivo = st.file_uploader("Selecciona archivo", type=['json'])
    
    st.markdown("---")
    st.markdown("### 🗑️ Limpiar")
    if st.button("⚠️ RESET TOTAL", use_container_width=True):
        st.session_state.progreso = {}
        st.session_state.series_procesadas = set()
        guardar_progreso({})
        st.rerun()
    
    st.markdown("---")
    st.markdown(f"**🏭 {len(MARCAS_COMPLETAS)} marcas**")
    st.markdown(f"**📊 {len(st.session_state.series_procesadas)} series** procesadas")

# ==================== PROCESAR JSON ====================
if archivo is not None:
    with st.spinner('Procesando...'):
        df = procesar_json(archivo)
    
    if len(df) > 0:
        # Métricas
        col1, col2, col3, col4, col5 = st.columns(5)
        completadas = sum(st.session_state.progreso.get(fila['ID'], False) for _, fila in df.iterrows())
        
        col1.metric("📦 Total Fichas", f"{len(df):,}")
        col2.metric("🏭 Marcas", f"{df['Marca'].nunique()}")
        col3.metric("✅ Completadas", f"{completadas}")
        col4.metric("📊 Progreso", f"{(completadas/len(df)*100):.1f}%")
        col5.metric("⚠️ Sin Oferta", f"{len(df[df['Estado'] == 'OFERTADA SIN OFERTA']):,}")
        
        st.progress(completadas/len(df) if len(df)>0 else 0)
        
        # ==================== PROGRESO POR MARCA (DISEÑO COMPACTO) ====================
        st.markdown("---")
        st.markdown("### 📈 Progreso por Marca")
        
        # Calcular datos
        datos_marcas = []
        for marca in sorted(df['Marca'].unique()):
            df_marca = df[df['Marca'] == marca]
            total = len(df_marca)
            comp = sum(st.session_state.progreso.get(fila['ID'], False) for _, fila in df_marca.iterrows())
            pct = (comp/total*100) if total>0 else 0
            datos_marcas.append({'Marca': marca, 'Total': total, 'Completadas': comp, 'Porcentaje': pct})
        
        df_marcas = pd.DataFrame(datos_marcas).sort_values('Porcentaje', ascending=False)
        
        # Mostrar top 10 con barras
        for _, row in df_marcas.head(10).iterrows():
            col1, col2, col3 = st.columns([2, 3, 1])
            with col1:
                st.markdown(f"**{row['Marca']}**")
            with col2:
                st.progress(row['Porcentaje']/100)
            with col3:
                st.markdown(f"`{row['Completadas']}/{row['Total']} ({row['Porcentaje']:.0f}%)`")
        
        if len(df_marcas) > 10:
            with st.expander(f"Ver otras {len(df_marcas)-10} marcas"):
                for _, row in df_marcas.iloc[10:].iterrows():
                    col1, col2, col3 = st.columns([2, 3, 1])
                    with col1:
                        st.markdown(f"{row['Marca']}")
                    with col2:
                        st.progress(row['Porcentaje']/100)
                    with col3:
                        st.markdown(f"`{row['Completadas']}/{row['Total']}`")
        
        # ==================== TABS ====================
        tab1, tab2, tab3 = st.tabs(["📦 Carga de Series", "✅ Revisión Manual", "📋 Datos"])
        
        # TAB 1: Carga de Series
        with tab1:
            st.markdown("### Carga números de serie")
            st.caption("Cada serie marcará UNA sola ficha (coincidencia exacta)")
            
            series_input = st.text_area("Pega tus series (una por línea):", height=150)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔍 Buscar y Marcar", type="primary", use_container_width=True):
                    if series_input.strip():
                        nuevas = [s.strip() for s in series_input.strip().split('\n') if s.strip()]
                        with st.spinner(f'Buscando {len(nuevas)} series...'):
                            encontradas, no_encontradas, duplicados = buscar_y_marcar_series(nuevas, df, st.session_state.series_procesadas)
                            
                            st.success(f"✅ Encontradas: {len(encontradas)} | ❌ No encontradas: {len(no_encontradas)} | 🔄 Duplicadas: {len(duplicados)}")
                            
                            if encontradas:
                                st.markdown("#### ✅ Encontradas:")
                                st.dataframe(pd.DataFrame(encontradas), use_container_width=True)
                            
                            if no_encontradas:
                                st.markdown("#### ❌ No encontradas:")
                                st.write(no_encontradas[:20])
                            
                            st.rerun()
            
            with col2:
                if st.button("📊 Exportar Excel", use_container_width=True):
                    from openpyxl import Workbook
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        pd.DataFrame(datos_marcas).to_excel(writer, sheet_name='Resumen', index=False)
                        df[['Marca', 'Categoría', 'Producto', 'Estado']].to_excel(writer, sheet_name='Fichas', index=False)
                    output.seek(0)
                    st.download_button("📥 Descargar", output, f"reporte_{datetime.now():%Y%m%d}.xlsx", use_container_width=True)
        
        # TAB 2: Revisión Manual
        with tab2:
            st.markdown("### Revisión manual de fichas")
            
            col1, col2 = st.columns(2)
            with col1:
                marca_filtro = st.selectbox("Marca", ["Todas"] + sorted(df['Marca'].unique()))
            with col2:
                estado_filtro = st.selectbox("Estado", ["Todos"] + sorted(df['Estado'].unique()))
            
            df_revision = df.copy()
            if marca_filtro != "Todas":
                df_revision = df_revision[df_revision['Marca'] == marca_filtro]
            if estado_filtro != "Todos":
                df_revision = df_revision[df_revision['Estado'] == estado_filtro]
            
            # Paginación
            items_por_pagina = 10
            total_paginas = max(1, (len(df_revision) + items_por_pagina - 1) // items_por_pagina)
            pagina = st.number_input("Página", 1, total_paginas, 1)
            
            inicio = (pagina - 1) * items_por_pagina
            fin = inicio + items_por_pagina
            
            for idx, (_, row) in enumerate(df_revision.iloc[inicio:fin].iterrows()):
                col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                is_checked = st.session_state.progreso.get(row['ID'], False)
                
                with col1:
                    if st.checkbox("✅", value=is_checked, key=f"chk_{row['ID']}"):
                        if not is_checked:
                            st.session_state.progreso[row['ID']] = True
                            guardar_progreso(st.session_state.progreso)
                            st.rerun()
                    else:
                        if is_checked:
                            st.session_state.progreso.pop(row['ID'], None)
                            guardar_progreso(st.session_state.progreso)
                            st.rerun()
                
                with col2:
                    st.markdown(f"**{row['Marca']}**")
                with col3:
                    st.markdown(f"*{row['Categoría']}*")
                with col4:
                    st.caption(row['Producto'][:50])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Marcar todas", use_container_width=True):
                    for _, row in df_revision.iterrows():
                        st.session_state.progreso[row['ID']] = True
                    guardar_progreso(st.session_state.progreso)
                    st.rerun()
            with col2:
                if st.button("🔄 Resetear todas", use_container_width=True):
                    for _, row in df_revision.iterrows():
                        st.session_state.progreso.pop(row['ID'], None)
                    guardar_progreso(st.session_state.progreso)
                    st.rerun()
            with col3:
                comp_actual = sum(1 for _, row in df_revision.iterrows() if st.session_state.progreso.get(row['ID'], False))
                st.metric("Progreso filtro", f"{comp_actual}/{len(df_revision)}")
        
        # TAB 3: Datos
        with tab3:
            st.markdown("### Listado de fichas")
            df_display = df[['Marca', 'Categoría', 'Estado', 'Producto']].copy()
            df_display['Revisado'] = df['ID'].apply(lambda x: "✅" if st.session_state.progreso.get(x, False) else "⏳")
            df_display['Producto'] = df_display['Producto'].str[:80] + "..."
            st.dataframe(df_display, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 CSV", csv, "datos.csv", "text/csv")
    
    else:
        st.error("No se encontraron datos")
else:
    st.info("👈 Sube un archivo JSON para comenzar")

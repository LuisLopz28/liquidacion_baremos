"""
Aplicación Streamlit para Procesamiento de Liquidaciones de Técnicos
Desarrollado para análisis de baremos y facturación
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import os
import sys
from datetime import datetime

# Agregar directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from processor import LiquidacionProcessor
from visualizer import LiquidacionVisualizer

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Liquidación de Técnicos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f2f6, #ffffff);
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .sidebar .sidebar-content {
        background-color: #f1f3f4;
    }
    
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #666;
        font-size: 0.9rem;
        border-top: 1px solid #eee;
        margin-top: 3rem;
    }
    
    .info-box {
        background-color: #e7f3ff;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Inicializa las variables de sesión."""
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'final_df' not in st.session_state:
        st.session_state.final_df = None
    if 'segment_dfs' not in st.session_state:
        st.session_state.segment_dfs = []
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'show_help' not in st.session_state:
        st.session_state.show_help = False

def validate_files():
    """Valida que los archivos de referencia existan."""
    required_files = {
        "data/BaremoOrden.xlsx": "Archivo de Baremo",
        "data/Homologado.xlsx": "Archivo de Homologación"
    }
    
    missing_files = []
    for file_path, description in required_files.items():
        if not os.path.exists(file_path):
            missing_files.append(f"{description} ({file_path})")
    
    return missing_files

def create_download_button(df: pd.DataFrame, filename: str, button_text: str):
    """Crea un botón de descarga para Excel."""
    if df.empty:
        st.warning("No hay datos para descargar.")
        return
    
    # Crear buffer en memoria
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
        
        # Formatear el Excel
        workbook = writer.book
        worksheet = writer.sheets['Datos']
        
        # Formato para headers
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Aplicar formato a headers
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Ajustar ancho de columnas
        for i, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(str(col))
            ) + 2
            worksheet.set_column(i, i, min(max_length, 50))
    
    buffer.seek(0)
    
    st.download_button(
        label=button_text,
        data=buffer,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"download_{filename}_{datetime.now().strftime('%H%M%S')}"
    )

def show_help_section():
    """Muestra la sección de ayuda."""
    st.markdown("### ❓ Ayuda y Documentación")
    
    with st.expander("📋 Formato de Archivos Requeridos"):
        st.markdown("""
        **Archivo de Cierres (.xlsx)**
        - Debe contener columnas: Orden, Técnico, Ciudad, Fecha, Estado, etc.
        - Los datos deben estar en la primera hoja del Excel
        
        **Archivo de Consumo (.xlsx)**
        - Debe contener información de materiales utilizados
        - Columnas típicas: Material, Cantidad, Costo, Orden
        
        **Archivos de Referencia (carpeta data/)**
        - `BaremoOrden.xlsx`: Tarifas y baremos por tipo de trabajo
        - `Homologado.xlsx`: Códigos homologados para materiales
        """)
    
    with st.expander("🔄 Proceso de Liquidación"):
        st.markdown("""
        1. **Carga de Datos**: Se cargan los archivos de cierres y consumo
        2. **Validación**: Se verifican formatos y datos faltantes
        3. **Segmentación**: Los datos se dividen según reglas de negocio
        4. **Aplicación de Baremos**: Se calculan las liquidaciones según tarifas
        5. **Consolidación**: Se genera el reporte final con métricas
        """)
    
    with st.expander("📊 Interpretación de Resultados"):
        st.markdown("""
        - **Dashboard**: Métricas principales y gráficos resumen
        - **Análisis Detallado**: Comparaciones por segmento y concepto
        - **Rankings**: Top técnicos y performance
        - **Datos**: Exploración detallada de todos los datasets
        """)

def reset_processing():
    """Reinicia el estado de procesamiento."""
    st.session_state.processed_data = None
    st.session_state.final_df = None
    st.session_state.segment_dfs = []
    st.session_state.processing_complete = False

def main():
    # Inicializar sesión
    initialize_session_state()
    
    # Header principal
    st.markdown('<div class="main-header">📊 Sistema de Liquidación de Técnicos</div>', 
                unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Botón de ayuda
        if st.button("❓ Ayuda", use_container_width=True):
            st.session_state.show_help = not st.session_state.show_help
        
        # Botón de reset si hay datos procesados
        if st.session_state.processing_complete:
            if st.button("🔄 Nuevo Procesamiento", use_container_width=True):
                reset_processing()
                st.rerun()
        
        st.markdown("---")
        
        # Validar archivos de referencia
        missing_files = validate_files()
        if missing_files:
            st.error("❌ **Archivos Faltantes:**")
            for file in missing_files:
                st.error(f"• {file}")
            st.markdown("""
            <div class="warning-box">
                <strong>📋 Instrucciones:</strong><br>
                1. Crea la carpeta 'data' en la raíz del proyecto<br>
                2. Coloca los archivos BaremoOrden.xlsx y Homologado.xlsx en esa carpeta
            </div>
            """, unsafe_allow_html=True)
            st.stop()
        else:
            st.success("✅ Archivos de referencia encontrados")
        
        st.markdown("---")
        
        # Upload de archivos
        st.subheader("📁 Cargar Archivos")
        
        cierres_file = st.file_uploader(
            "Archivo de Cierres (Excel)",
            type=['xlsx', 'xls'],
            help="Archivo con datos de órdenes cerradas",
            key="cierres_uploader"
        )
        
        consumo_file = st.file_uploader(
            "Archivo de Consumo (Excel)",
            type=['xlsx', 'xls'],
            help="Archivo con datos de consumo de materiales",
            key="consumo_uploader"
        )
        
        # Botón de procesamiento
        process_button = st.button(
            "🚀 Procesar Liquidación",
            type="primary",
            disabled=not (cierres_file and consumo_file),
            use_container_width=True
        )
        
        # Información del proceso
        if cierres_file and consumo_file:
            st.markdown(f"""
            <div class="info-box">
                <strong>📄 Archivos Cargados:</strong><br>
                • Cierres: {cierres_file.name}<br>
                • Consumo: {consumo_file.name}
            </div>
            """, unsafe_allow_html=True)
    
    # Mostrar ayuda si está activada
    if st.session_state.show_help:
        show_help_section()
        st.markdown("---")
    
    # Contenido principal
    if process_button and cierres_file and consumo_file:
        with st.spinner("🔄 Procesando liquidación... Esto puede tomar unos momentos."):
            try:
                # Inicializar procesador
                processor = LiquidacionProcessor()
                
                # Procesar datos
                progress_bar = st.progress(0)
                status_placeholder = st.empty()
                
                status_placeholder.write("📊 Cargando y validando datos...")
                progress_bar.progress(20)
                
                data = processor.load_data(cierres_file, consumo_file)
                progress_bar.progress(50)
                
                status_placeholder.write("⚡ Aplicando reglas de segmentación...")
                final_df, segment_dfs = processor.process_all_segments(data)
                progress_bar.progress(80)
                
                if final_df.empty:
                    progress_bar.progress(100)
                    status_placeholder.empty()
                    st.error("❌ No se generaron datos después del procesamiento. Verifica los archivos de entrada.")
                    st.stop()
                
                # Guardar en sesión
                st.session_state.processed_data = data
                st.session_state.final_df = final_df
                st.session_state.segment_dfs = segment_dfs
                st.session_state.processing_complete = True
                
                progress_bar.progress(100)
                status_placeholder.empty()
                
                st.markdown("""
                <div class="success-message">
                    <strong>✅ Procesamiento Completado Exitosamente!</strong><br>
                    Los datos han sido procesados y están listos para análisis.
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ **Error durante el procesamiento:** {str(e)}")
                with st.expander("🔍 Detalles del Error"):
                    st.code(str(e))
                st.stop()
    
    # Mostrar resultados si el procesamiento está completo
    if st.session_state.processing_complete and st.session_state.final_df is not None:
        
        final_df = st.session_state.final_df
        visualizer = LiquidacionVisualizer()
        
        # Tabs para organizar el contenido
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Dashboard", "📊 Análisis Detallado", "🏆 Rankings", "📋 Datos"])
        
        with tab1:
            st.header("📈 Dashboard Ejecutivo")
            
            # Métricas principales
            try:
                metrics = visualizer.create_summary_metrics(final_df)
                visualizer.display_metrics_cards(metrics)
            except Exception as e:
                st.error(f"Error al crear métricas: {e}")
            
            st.markdown("---")
            
            # Gráficos principales
            col1, col2 = st.columns(2)
            
            with col1:
                try:
                    fig_segments = visualizer.create_baremos_by_segment(final_df)
                    st.plotly_chart(fig_segments, use_container_width=True)
                except Exception as e:
                    st.error(f"Error en gráfico de segmentos: {e}")
            
            with col2:
                try:
                    fig_cities = visualizer.create_city_distribution(final_df)
                    st.plotly_chart(fig_cities, use_container_width=True)
                except Exception as e:
                    st.error(f"Error en gráfico de ciudades: {e}")
            
            # Serie temporal
            try:
                fig_time = visualizer.create_time_series(final_df)
                st.plotly_chart(fig_time, use_container_width=True)
            except Exception as e:
                st.error(f"Error en serie temporal: {e}")
        
        with tab2:
            st.header("📊 Análisis Detallado")
            
            # Comparación de segmentos
            try:
                fig_comparison = visualizer.create_segment_comparison(final_df)
                st.plotly_chart(fig_comparison, use_container_width=True)
            except Exception as e:
                st.error(f"Error en comparación de segmentos: {e}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Análisis de conceptos
                try:
                    fig_concepts = visualizer.create_concept_analysis(final_df)
                    st.plotly_chart(fig_concepts, use_container_width=True)
                except Exception as e:
                    st.error(f"Error en análisis de conceptos: {e}")
            
            with col2:
                # Heatmap
                try:
                    fig_heatmap = visualizer.create_heatmap_city_segment(final_df)
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                except Exception as e:
                    st.error(f"Error en heatmap: {e}")
        
        with tab3:
            st.header("🏆 Rankings y Performance")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Top técnicos
                top_n = st.slider("Número de técnicos a mostrar", 5, 20, 10)
                try:
                    fig_top_tech = visualizer.create_top_technicians(final_df, top_n)
                    st.plotly_chart(fig_top_tech, use_container_width=True)
                except Exception as e:
                    st.error(f"Error en ranking de técnicos: {e}")
            
            with col2:
                # Tabla resumen de performance
                st.subheader("📋 Resumen Performance")
                try:
                    performance_table = visualizer.create_performance_summary_table(final_df)
                    if not performance_table.empty:
                        st.dataframe(
                            performance_table.head(10), 
                            use_container_width=True,
                            height=400
                        )
                        
                        # Botón de descarga para la tabla de performance
                        create_download_button(
                            performance_table,
                            f"performance_tecnicos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            "⬇️ Descargar Performance"
                        )
                    else:
                        st.info("No hay datos de performance disponibles.")
                except Exception as e:
                    st.error(f"Error en tabla de performance: {e}")
        
        with tab4:
            st.header("📋 Explorador de Datos")
            
            # Selector de vista
            data_view = st.selectbox(
                "Seleccionar Vista de Datos",
                ["Liquidación Final", "Datos por Segmento", "Datos Base"],
                help="Elige qué conjunto de datos explorar"
            )
            
            if data_view == "Liquidación Final":
                visualizer.display_data_table(final_df, "Datos de Liquidación Final")
                
                # Botón de descarga principal
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    create_download_button(
                        final_df,
                        f"liquidacion_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        "📥 Descargar Liquidación Completa"
                    )
            
            elif data_view == "Datos por Segmento":
                if st.session_state.segment_dfs:
                    segment_names = [name for name, _ in st.session_state.segment_dfs]
                    selected_segment = st.selectbox("Seleccionar Segmento", segment_names)
                    segment_df = next((df for name, df in st.session_state.segment_dfs if name == selected_segment), pd.DataFrame())
                    
                    if not segment_df.empty:
                        visualizer.display_data_table(segment_df, f"Datos del Segmento: {selected_segment}")
                        
                        create_download_button(
                            segment_df,
                            f"segmento_{selected_segment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            f"⬇️ Descargar {selected_segment}"
                        )
                    else:
                        st.warning(f"No hay datos disponibles para el segmento {selected_segment}.")
                else:
                    st.warning("No hay datos de segmentos disponibles.")
            
            else:  # Datos Base
                if st.session_state.processed_data:
                    base_data_view = st.selectbox(
                        "Seleccionar Datos Base",
                        ["Cierres Procesados", "Consumo Pivot", "Baremo", "Homologado"]
                    )
                    
                    data_map = {
                        "Cierres Procesados": "cierres",
                        "Consumo Pivot": "consumo", 
                        "Baremo": "baremo",
                        "Homologado": "homologado"
                    }
                    
                    try:
                        selected_data = st.session_state.processed_data[data_map[base_data_view]]
                        visualizer.display_data_table(selected_data, f"Datos Base: {base_data_view}")
                        
                        # Botón de descarga para datos base
                        create_download_button(
                            selected_data,
                            f"datos_base_{base_data_view.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            f"⬇️ Descargar {base_data_view}"
                        )
                    except KeyError:
                        st.error(f"No se encontraron los datos base para: {base_data_view}")
                else:
                    st.warning("No hay datos base disponibles. Procesa primero los archivos.")
    
    elif not st.session_state.processing_complete:
        # Pantalla de bienvenida
        st.markdown("""
        <div class="info-box">
            <h3>👋 Bienvenido al Sistema de Liquidación de Técnicos</h3>
            <p>Esta aplicación te permite procesar y analizar liquidaciones de técnicos de manera automatizada.</p>
            <p><strong>Para comenzar:</strong></p>
            <ol>
                <li>Asegúrate de que los archivos de referencia estén en la carpeta 'data'</li>
                <li>Carga los archivos de Cierres y Consumo en la barra lateral</li>
                <li>Haz clic en "Procesar Liquidación"</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar información adicional
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 📊 Dashboard
            Visualiza métricas principales, distribuciones por ciudad y segmento, y tendencias temporales.
            """)
        
        with col2:
            st.markdown("""
            ### 📈 Análisis
            Compara segmentos, analiza conceptos y explora correlaciones en los datos.
            """)
        
        with col3:
            st.markdown("""
            ### 🏆 Rankings
            Identifica los técnicos top performers y analiza métricas de rendimiento.
            """)
    
    # Footer
    st.markdown("""
    <div class="footer">
        <strong>Sistema de Liquidación de Técnicos</strong><br>
        Desarrollado con ❤️ usando Streamlit • Versión 2.0<br>
        <small>Para soporte técnico o consultas, contacta al equipo de desarrollo</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
"""
Módulo de visualización para la aplicación de liquidaciones
Contiene todas las funciones de gráficos y análisis visual
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import streamlit as st
from typing import Dict, List, Tuple

class LiquidacionVisualizer:
    def __init__(self):
        self.color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                             '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    def create_summary_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Crea métricas resumen del dataset."""
        if df.empty:
            return {
                "total_ordenes": 0,
                "total_baremos": 0.0,
                "total_factura": 0.0,
                "promedio_baremos": 0.0,
                "tecnicos_unicos": 0
            }
        
        return {
            "total_ordenes": len(df),
            "total_baremos": df["BAREMOS"].sum(),
            "total_factura": df["FACTURA"].sum() if "FACTURA" in df.columns else 0.0,
            "promedio_baremos": df["BAREMOS"].mean(),
            "tecnicos_unicos": df["NOMBRE_TECNICO"].nunique() if "NOMBRE_TECNICO" in df.columns else 0
        }
    
    def display_metrics_cards(self, metrics: Dict[str, float]):
        """Muestra las métricas en tarjetas de Streamlit."""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Órdenes", f"{metrics['total_ordenes']:,}")
        
        with col2:
            st.metric("Total Baremos", f"{metrics['total_baremos']:,.2f}")
        
        with col3:
            st.metric("Total Factura", f"${metrics['total_factura']:,.2f}")
        
        with col4:
            st.metric("Promedio Baremos", f"{metrics['promedio_baremos']:.2f}")
        
        with col5:
            st.metric("Técnicos Únicos", f"{metrics['tecnicos_unicos']:,}")
    
    def create_baremos_by_segment(self, df: pd.DataFrame) -> go.Figure:
        """Gráfico de baremos por segmento."""
        if df.empty:
            return go.Figure().add_annotation(text="No hay datos disponibles", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        # Determinar segmento basado en MEDIO_DE_ACCESO y TIPO_DE_ORDEN
        df_temp = df.copy()
        df_temp['SEGMENTO'] = df_temp['MEDIO_DE_ACCESO'] + '_' + df_temp['TIPO_DE_ORDEN']
        
        segment_data = df_temp.groupby('SEGMENTO')['BAREMOS'].sum().reset_index()
        
        fig = px.bar(
            segment_data, 
            x='SEGMENTO', 
            y='BAREMOS',
            title='Baremos por Segmento',
            color='BAREMOS',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            xaxis_title="Segmento",
            yaxis_title="Total Baremos",
            height=400,
            font=dict(size=12)
        )
        
        return fig
    
    def create_top_technicians(self, df: pd.DataFrame, top_n: int = 10) -> go.Figure:
        """Gráfico de top técnicos por baremos."""
        if df.empty or "NOMBRE_TECNICO" not in df.columns:
            return go.Figure().add_annotation(text="No hay datos de técnicos disponibles", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        tech_data = df.groupby('NOMBRE_TECNICO').agg({
            'BAREMOS': 'sum',
            'FACTURA': 'sum' if 'FACTURA' in df.columns else 'count'
        }).reset_index()
        
        tech_data = tech_data.nlargest(top_n, 'BAREMOS')
        
        fig = px.bar(
            tech_data,
            x='BAREMOS',
            y='NOMBRE_TECNICO',
            orientation='h',
            title=f'Top {top_n} Técnicos por Baremos',
            color='BAREMOS',
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            xaxis_title="Total Baremos",
            yaxis_title="Técnico",
            height=500,
            font=dict(size=12)
        )
        
        return fig
    
    def create_city_distribution(self, df: pd.DataFrame) -> go.Figure:
        """Gráfico de distribución por ciudad."""
        if df.empty or "CIUDAD" not in df.columns:
            return go.Figure().add_annotation(text="No hay datos de ciudad disponibles", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        city_data = df.groupby('CIUDAD')['BAREMOS'].sum().reset_index()
        city_data = city_data.nlargest(15, 'BAREMOS')
        
        fig = px.pie(
            city_data,
            values='BAREMOS',
            names='CIUDAD',
            title='Distribución de Baremos por Ciudad (Top 15)'
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=500, font=dict(size=12))
        
        return fig
    
    def create_time_series(self, df: pd.DataFrame) -> go.Figure:
        """Gráfico de serie temporal por fecha de cierre."""
        if df.empty or "FECHA_DE_CIERRE_FINAL" not in df.columns:
            return go.Figure().add_annotation(text="No hay datos de fecha disponibles", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        df_temp = df.copy()
        df_temp['FECHA_DE_CIERRE_FINAL'] = pd.to_datetime(df_temp['FECHA_DE_CIERRE_FINAL'])
        
        daily_data = df_temp.groupby(df_temp['FECHA_DE_CIERRE_FINAL'].dt.date).agg({
            'BAREMOS': 'sum',
            'PET_ATIS': 'count'
        }).reset_index()
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Scatter(
                x=daily_data['FECHA_DE_CIERRE_FINAL'],
                y=daily_data['BAREMOS'],
                mode='lines+markers',
                name='Baremos Diarios',
                line=dict(color='#1f77b4', width=3)
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=daily_data['FECHA_DE_CIERRE_FINAL'],
                y=daily_data['PET_ATIS'],
                mode='lines+markers',
                name='Órdenes Diarias',
                line=dict(color='#ff7f0e', width=2)
            ),
            secondary_y=True
        )
        
        fig.update_xaxes(title_text="Fecha")
        fig.update_yaxes(title_text="Total Baremos", secondary_y=False)
        fig.update_yaxes(title_text="Número de Órdenes", secondary_y=True)
        
        fig.update_layout(
            title_text="Evolución Temporal de Baremos y Órdenes",
            height=400,
            font=dict(size=12)
        )
        
        return fig
    
    def create_concept_analysis(self, df: pd.DataFrame) -> go.Figure:
        """Análisis de conceptos más utilizados."""
        if df.empty or "ATRIBUTO" not in df.columns:
            return go.Figure().add_annotation(text="No hay datos de atributos disponibles", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        concept_data = df.groupby('ATRIBUTO').agg({
            'CANTIDAD': 'sum',
            'BAREMOS': 'sum'
        }).reset_index()
        
        concept_data = concept_data.nlargest(15, 'BAREMOS')
        
        fig = px.scatter(
            concept_data,
            x='CANTIDAD',
            y='BAREMOS',
            size='BAREMOS',
            color='ATRIBUTO',
            title='Análisis de Conceptos: Cantidad vs Baremos',
            hover_data=['ATRIBUTO']
        )
        
        fig.update_layout(
            xaxis_title="Cantidad Total",
            yaxis_title="Baremos Total",
            height=500,
            font=dict(size=12),
            showlegend=False
        )
        
        return fig
    
    def create_heatmap_city_segment(self, df: pd.DataFrame) -> go.Figure:
        """Heatmap de baremos por ciudad y segmento."""
        if df.empty or "CIUDAD" not in df.columns:
            return go.Figure().add_annotation(text="No hay datos suficientes para el heatmap", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        df_temp = df.copy()
        df_temp['SEGMENTO'] = df_temp['MEDIO_DE_ACCESO'] + '_' + df_temp['TIPO_DE_ORDEN']
        
        heatmap_data = df_temp.pivot_table(
            index='CIUDAD',
            columns='SEGMENTO',
            values='BAREMOS',
            aggfunc='sum',
            fill_value=0
        )
        
        # Limitar a top 10 ciudades por baremos
        city_totals = heatmap_data.sum(axis=1).nlargest(10)
        heatmap_data = heatmap_data.loc[city_totals.index]
        
        fig = px.imshow(
            heatmap_data.values,
            labels=dict(x="Segmento", y="Ciudad", color="Baremos"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            title="Heatmap: Baremos por Ciudad y Segmento",
            color_continuous_scale="Viridis"
        )
        
        fig.update_layout(height=500, font=dict(size=10))
        
        return fig
    
    def create_performance_summary_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Crea tabla resumen de performance por técnico."""
        if df.empty or "NOMBRE_TECNICO" not in df.columns:
            return pd.DataFrame()
        
        summary = df.groupby('NOMBRE_TECNICO').agg({
            'BAREMOS': ['sum', 'mean', 'count'],
            'FACTURA': 'sum' if 'FACTURA' in df.columns else 'count',
            'CIUDAD': 'nunique'
        }).round(2)
        
        # Aplanar columnas multi-nivel
        summary.columns = ['Total_Baremos', 'Promedio_Baremos', 'Num_Ordenes', 'Total_Factura', 'Ciudades_Atendidas']
        summary = summary.reset_index()
        
        # Calcular eficiencia (baremos por orden)
        summary['Eficiencia'] = (summary['Total_Baremos'] / summary['Num_Ordenes']).round(2)
        
        return summary.sort_values('Total_Baremos', ascending=False)
    
    def create_segment_comparison(self, df: pd.DataFrame) -> go.Figure:
        """Comparación detallada entre segmentos."""
        if df.empty:
            return go.Figure().add_annotation(text="No hay datos para comparar segmentos", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        df_temp = df.copy()
        df_temp['SEGMENTO'] = df_temp['MEDIO_DE_ACCESO'] + '_' + df_temp['TIPO_DE_ORDEN']
        
        segment_stats = df_temp.groupby('SEGMENTO').agg({
            'BAREMOS': ['sum', 'mean', 'count'],
            'FACTURA': 'sum' if 'FACTURA' in df_temp.columns else 'count'
        }).round(2)
        
        segment_stats.columns = ['Total_Baremos', 'Promedio_Baremos', 'Num_Ordenes', 'Total_Factura']
        segment_stats = segment_stats.reset_index()
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Total Baremos', 'Promedio Baremos', 'Número Órdenes', 'Total Factura'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        fig.add_trace(
            go.Bar(x=segment_stats['SEGMENTO'], y=segment_stats['Total_Baremos'], 
                   name='Total Baremos', marker_color='#1f77b4'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(x=segment_stats['SEGMENTO'], y=segment_stats['Promedio_Baremos'], 
                   name='Promedio Baremos', marker_color='#ff7f0e'),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Bar(x=segment_stats['SEGMENTO'], y=segment_stats['Num_Ordenes'], 
                   name='Número Órdenes', marker_color='#2ca02c'),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Bar(x=segment_stats['SEGMENTO'], y=segment_stats['Total_Factura'], 
                   name='Total Factura', marker_color='#d62728'),
            row=2, col=2
        )
        
        fig.update_layout(
            title_text="Comparación Detallada por Segmentos",
            height=600,
            showlegend=False,
            font=dict(size=10)
        )
        
        return fig
    
    def display_data_table(self, df: pd.DataFrame, title: str = "Datos Detallados", max_rows: int = 1000):
        """Muestra tabla de datos con filtros."""
        st.subheader(title)
        
        if df.empty:
            st.warning("No hay datos disponibles para mostrar.")
            return
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if "NOMBRE_TECNICO" in df.columns:
                tecnicos = st.multiselect(
                    "Filtrar por Técnico",
                    options=df["NOMBRE_TECNICO"].unique(),
                    default=[]
                )
                if tecnicos:
                    df = df[df["NOMBRE_TECNICO"].isin(tecnicos)]
        
        with col2:
            if "CIUDAD" in df.columns:
                ciudades = st.multiselect(
                    "Filtrar por Ciudad",
                    options=df["CIUDAD"].unique(),
                    default=[]
                )
                if ciudades:
                    df = df[df["CIUDAD"].isin(ciudades)]
        
        with col3:
            if "MEDIO_DE_ACCESO" in df.columns:
                medios = st.multiselect(
                    "Filtrar por Medio de Acceso",
                    options=df["MEDIO_DE_ACCESO"].unique(),
                    default=[]
                )
                if medios:
                    df = df[df["MEDIO_DE_ACCESO"].isin(medios)]
        
        # Mostrar datos limitados
        if len(df) > max_rows:
            st.warning(f"Mostrando solo los primeros {max_rows} registros de {len(df)} total.")
            df_display = df.head(max_rows)
        else:
            df_display = df
        
        st.dataframe(df_display, use_container_width=True, height=400)
        
        # Estadísticas rápidas
        if not df.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Registros Filtrados", len(df))
            
            with col2:
                if "BAREMOS" in df.columns:
                    st.metric("Baremos Totales", f"{df['BAREMOS'].sum():,.2f}")
            
            with col3:
                if "FACTURA" in df.columns:
                    st.metric("Factura Total", f"${df['FACTURA'].sum():,.2f}")
            
            with col4:
                if "NOMBRE_TECNICO" in df.columns:
                    st.metric("Técnicos Únicos", df["NOMBRE_TECNICO"].nunique())
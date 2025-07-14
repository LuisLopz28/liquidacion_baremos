import streamlit as st
import pandas as pd
from funciones_procesamiento import (
    procesar_datos,
    cargar_homologado,
    cargar_baremo
)

st.set_page_config(page_title="Liquidación Final", layout="wide")

st.title("📊 Aplicación de Liquidación Final")

st.markdown("""
Esta aplicación permite cargar los archivos **Cierres** y **Consumo** para procesar automáticamente la liquidación de órdenes con base en los contratos.
""")

st.sidebar.header("📂 Cargar archivos")
archivo_cierres = st.sidebar.file_uploader("Sube el archivo de **Cierres** (.xlsx)", type=["xlsx"])
archivo_consumo = st.sidebar.file_uploader("Sube el archivo de **Consumo** (.xlsx)", type=["xlsx"])

if archivo_cierres and archivo_consumo:
    with st.spinner("Procesando archivos..."):
        try:
            # Carga bases integradas en el proyecto
            df_homologado = cargar_homologado("data/Homologado.xlsx")
            df_baremo = cargar_baremo("data/BaremoOrden.xlsx")
            
            # Procesa toda la lógica
            df_resultado = procesar_datos(archivo_cierres, archivo_consumo, df_homologado, df_baremo)

            st.success("✅ Procesamiento completado")
            st.dataframe(df_resultado)

            st.download_button(
                label="⬇️ Descargar resultado en Excel",
                data=df_resultado.to_excel(index=False, engine="openpyxl"),
                file_name="liquidacion_final.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"❌ Error durante el procesamiento: {str(e)}")
else:
    st.info("📌 Por favor, carga ambos archivos para continuar.")

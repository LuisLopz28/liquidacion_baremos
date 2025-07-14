import streamlit as st
import pandas as pd

st.set_page_config(page_title="Liquidación Final", layout="wide")

# --- FUNCIONES DE PROCESAMIENTO --- #

@st.cache_data
def cargar_homologado(path):
    df = pd.read_excel(path)
    df = df.astype(str)
    return df

@st.cache_data
def cargar_baremo(path):
    df = pd.read_excel(path)
    df = df.astype({'Medio de acceso': str, 'TipoOrdenFinal': str, 'SubTipoOrdenFinal': str, 'Concepto': str})
    return df

def procesar_datos(file_cierres, file_consumo, df_homologado, df_baremo):
    df_cierres = pd.read_excel(file_cierres)
    df_consumo = pd.read_excel(file_consumo)

    df_consumo = df_consumo[df_consumo["TIPO_DE_ORDEN"] != "AVERIA"].copy()
    df_consumo["Personalizado"] = df_consumo.apply(
        lambda x: 1 if x["TIPO_TRANSACCION"] == "customer" and x["SUBTIPO_DE_ORDEN"] in ["TRASLADOBA", "TRASLADOVOIBA", "TRASLADOVOIBATV"] or x["TIPO_TRANSACCION"] == "install" else None,
        axis=1
    )
    df_consumo = df_consumo[df_consumo["Personalizado"].notnull()]
    df_consumo = df_consumo.merge(df_homologado, how="left", on=["DESCRIPCION", "DESC_TIPO_EQUIPO"])
    df_consumo = df_consumo[df_consumo["HOMOLOGADO"].notnull() & (df_consumo["HOMOLOGADO"] != "NA")]

    df_consumo["Combinada"] = df_consumo["HOMOLOGADO"] + "_"
    df_pivot = pd.pivot_table(
        df_consumo,
        values="CANTIDAD",
        index=["PET_ATIS", "TIPO_DE_ORDEN", "SUBTIPO_DE_ORDEN", "XA_ACCESS_TECHNOLOGY"],
        columns="Combinada",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    df_pivot.columns = [col.replace("_", "") for col in df_pivot.columns]
    df_cierres = df_cierres.merge(df_pivot, how="left", left_on="Pet_atis", right_on="PET_ATIS")
    df_cierres.fillna(0, inplace=True)

    df_result = df_cierres.merge(
        df_baremo,
        how="left",
        left_on=["Tipo_de_orden", "Subtipo_de_orden", "Medio de acceso"],
        right_on=["TipoOrdenFinal", "SubTipoOrdenFinal", "Medio de acceso"]
    )

    columnas_relevantes = [
        "Pet_atis", "Tipo_de_orden", "Subtipo_de_orden", "Departamento", "Ciudad",
        "Medio de acceso", "Actuacion", "external_id", "Nombre_Tecnico", "Fecha_de_cierre_final",
        "ANTENA", "DECO_HD", "DECO_IPTV", "MODEM", "BASEPORT", "CABLE_UTP_W",
        "Item", "Concepto", "Clase", "Descripcion", "Puntos", "Valor Clase"
    ]
    for col in columnas_relevantes:
        if col not in df_result.columns:
            df_result[col] = 0

    df_result["Baremos"] = df_result["Puntos"] * 1
    df_result["Factura"] = df_result["Baremos"] * df_result["Valor Clase"]

    return df_result[columnas_relevantes + ["Baremos", "Factura"]]


# --- INTERFAZ --- #

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
            df_homologado = cargar_homologado("data/Homologado.xlsx")
            df_baremo = cargar_baremo("data/BaremoOrden.xlsx")
            
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

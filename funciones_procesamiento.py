# funciones_procesamiento.py

import pandas as pd

def limpiar_columnas(df):
    """Estandariza los nombres de las columnas: mayúsculas, sin espacios, sin tildes"""
    df.columns = df.columns.str.strip().str.upper().str.replace(" ", "_")
    return df

def procesar_homologado(path):
    df = pd.read_excel(path)
    df = limpiar_columnas(df)
    df = df.astype({"DESC_TIPO_EQUIPO": str, "DESCRIPCION": str, "HOMOLOGADO": str})
    return df

def procesar_baremo_orden(path):
    df = pd.read_excel(path)
    df = limpiar_columnas(df)
    df = df.astype({
        "MEDIO_DE_ACCESO": str,
        "TIPOORDENFINAL": str,
        "SUBTIPOORDENFINAL": str,
        "ITEM": str,
        "CONCEPTO": str,
        "CLASE": str,
        "DESCRIPCION": str,
        "PUNTOS": float,
        "VALOR_CLASE": float,
        "CASA/EDIFICIO": str
    })
    return df

def procesar_consumo(path, homologado_df):
    df = pd.read_excel(path)
    df = limpiar_columnas(df)
    df = df[df["TIPO_DE_ORDEN"] != "AVERIA"]
    df = df[
        ((df["TIPO_TRANSACCION"] == "customer") &
         (df["SUBTIPO_DE_ORDEN"].isin(["TRASLADOBA", "TRASLADOVOIBA", "TRASLADOVOIBATV"]))) |
        (df["TIPO_TRANSACCION"] == "install")
    ]

    columnas_necesarias = [
        "ACTUACION", "PET_ATIS", "CODIGO", "DESCRIPCION", "SERIAL", "FECHA_DE_CIERRE_FINAL",
        "EXTERNAL_ID", "CANTIDAD", "FAMILIA", "TIPO_DE_ORDEN", "DEPARTAMENTO", "SUBTIPO_DE_ORDEN",
        "TIPO", "MODELO", "TIPO_INGRESO_SAP", "DESC_TIPO_EQUIPO", "XA_ACCESS_TECHNOLOGY"
    ]

    df = df[columnas_necesarias]
    df = df.astype({
        "ACTUACION": str, "PET_ATIS": str, "CODIGO": str, "DESCRIPCION": str, "SERIAL": str,
        "FECHA_DE_CIERRE_FINAL": 'datetime64[ns]', "EXTERNAL_ID": 'Int64', "CANTIDAD": 'Int64',
        "FAMILIA": str, "TIPO_DE_ORDEN": str, "DEPARTAMENTO": str, "SUBTIPO_DE_ORDEN": str,
        "TIPO": str, "MODELO": str, "TIPO_INGRESO_SAP": str, "XA_ACCESS_TECHNOLOGY": str, "DESC_TIPO_EQUIPO": str
    })

    homologado_df = limpiar_columnas(homologado_df)
    df = df.merge(homologado_df, on=["DESCRIPCION", "DESC_TIPO_EQUIPO"], how="left")

    df = df[df["HOMOLOGADO"].notna() & (df["HOMOLOGADO"] != "NA") & (df["HOMOLOGADO"] != "")]
    df["COMBINADA"] = df["HOMOLOGADO"] + "_"

    pivot = df.pivot_table(
        index=["PET_ATIS", "TIPO_DE_ORDEN", "SUBTIPO_DE_ORDEN", "XA_ACCESS_TECHNOLOGY"],
        columns="COMBINADA", values="CANTIDAD", aggfunc="sum", fill_value=0
    ).reset_index()

    rename_cols = {
        'ANTENA_': 'ANTENA', 'DECO_HD_': 'DECO_HD', 'DECO_IPTV_': 'DECO_IPTV',
        'MODEM_': 'MODEM', 'BASEPORT_': 'BASEPORT', 'CABLE_UTP_W_': 'CABLE_UTP_W'
    }

    for col in rename_cols:
        if col in pivot.columns:
            pivot[rename_cols[col]] = pivot[col].fillna(0)

    final_cols = ["PET_ATIS", "TIPO_DE_ORDEN", "SUBTIPO_DE_ORDEN", "XA_ACCESS_TECHNOLOGY",
                  "ANTENA", "DECO_HD", "DECO_IPTV", "MODEM", "BASEPORT", "CABLE_UTP_W"]

    for col in final_cols[4:]:
        if col not in pivot.columns:
            pivot[col] = 0

    return pivot[final_cols]

def procesar_cierres(path, consumo_df, baremo_df):
    df = pd.read_excel(path)
    df = limpiar_columnas(df)

    columnas_cierre = [
        "TIPO_DE_ORDEN", "SUBTIPO_DE_ORDEN", "PET_ATIS", "RESUMEN_DE_PCS_Y_PSS_DE_LA_SOLICITUD",
        "CIUDAD", "DEPARTAMENTO", "XA_ACTUACION", "XA_ACCESS_TECHNOLOGY", "EXTERNAL_ID",
        "FECHA_DE_CIERRE_FINAL", "NOMBRE_TECNICO", "A_SMART_TV_CABLEADO"
    ]

    df = df[columnas_cierre]
    df = df.rename(columns={
        "XA_ACCESS_TECHNOLOGY": "MEDIO_DE_ACCESO",
        "XA_ACTUACION": "ACTUACION"
    })

    df = df.astype({
        "TIPO_DE_ORDEN": str, "SUBTIPO_DE_ORDEN": str, "PET_ATIS": str, "DEPARTAMENTO": str,
        "CIUDAD": str, "MEDIO_DE_ACCESO": str, "EXTERNAL_ID": str, "NOMBRE_TECNICO": str,
        "A_SMART_TV_CABLEADO": str, "RESUMEN_DE_PCS_Y_PSS_DE_LA_SOLICITUD": str,
        "FECHA_DE_CIERRE_FINAL": 'datetime64[ns]', "ACTUACION": str
    })

    consumo_df = limpiar_columnas(consumo_df)
    df = df.merge(consumo_df, left_on="PET_ATIS", right_on="PET_ATIS", how="left")

    for col in ["ANTENA", "DECO_HD", "DECO_IPTV", "MODEM", "BASEPORT", "CABLE_UTP_W"]:
        if col not in df.columns:
            df[col] = 0
    df = df.fillna(0)

    baremo_df = limpiar_columnas(baremo_df)
    return df

def calcular_liquidacion(df):
    df = df.copy()
    if "PUNTOS" in df.columns and "VALOR_CLASE" in df.columns and "CANTIDAD" in df.columns:
        df["BAREMOS"] = df["PUNTOS"] * df["CANTIDAD"]
        df["FACTURA"] = df["BAREMOS"] * df["VALOR_CLASE"]
        return df[df["CANTIDAD"] > 0]
    else:
        raise ValueError("Faltan columnas necesarias para el cálculo.")

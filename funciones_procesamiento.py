# funciones_procesamiento.py

import pandas as pd

def procesar_homologado(path):
    df = pd.read_excel(path)
    df = df.astype({"DESC_TIPO_EQUIPO": str, "DESCRIPCION": str, "HOMOLOGADO": str})
    return df

def procesar_baremo_orden(path):
    df = pd.read_excel(path)
    df = df.astype({
        "Medio de acceso": str,
        "TipoOrdenFinal": str,
        "SubTipoOrdenFinal": str,
        "Item": str,
        "Concepto": str,
        "Clase": str,
        "Descripcion": str,
        "Puntos": float,
        "Valor Clase": float,
        "CASA/EDIFICIO": str
    })
    return df

def procesar_consumo(path, homologado_df):
    df = pd.read_excel(path)
    df = df[df["TIPO_DE_ORDEN"] != "AVERIA"]
    df = df[((df["TIPO_TRANSACCION"] == "customer") & (df["SUBTIPO_DE_ORDEN"].isin(["TRASLADOBA", "TRASLADOVOIBA", "TRASLADOVOIBATV"]))) | (df["TIPO_TRANSACCION"] == "install")]
    df = df[["ACTUACION", "PET_ATIS", "CODIGO", "DESCRIPCION", "SERIAL", "Fecha_de_cierre_final", "external_id", "CANTIDAD", "FAMILIA", "TIPO_DE_ORDEN", "DEPARTAMENTO", "SUBTIPO_DE_ORDEN", "TIPO", "MODELO", "TIPO_INGRESO_SAP", "DESC_TIPO_EQUIPO", "XA_ACCESS_TECHNOLOGY"]]
    df = df.astype({
        "ACTUACION": str, "PET_ATIS": str, "CODIGO": str, "DESCRIPCION": str, "SERIAL": str,
        "Fecha_de_cierre_final": 'datetime64[ns]', "external_id": 'Int64', "CANTIDAD": 'Int64',
        "FAMILIA": str, "TIPO_DE_ORDEN": str, "DEPARTAMENTO": str, "SUBTIPO_DE_ORDEN": str,
        "TIPO": str, "MODELO": str, "TIPO_INGRESO_SAP": str, "XA_ACCESS_TECHNOLOGY": str, "DESC_TIPO_EQUIPO": str
    })
    df = df.merge(homologado_df, on=["DESCRIPCION", "DESC_TIPO_EQUIPO"], how="left")
    df = df[df["HOMOLOGADO"].notna() & (df["HOMOLOGADO"] != "NA") & (df["HOMOLOGADO"] != "")]
    df["Combinada"] = df["HOMOLOGADO"] + "_"
    pivot = df.pivot_table(index=["PET_ATIS", "TIPO_DE_ORDEN", "SUBTIPO_DE_ORDEN", "XA_ACCESS_TECHNOLOGY"],
                           columns="Combinada", values="CANTIDAD", aggfunc="sum", fill_value=0).reset_index()
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
    df = df[["Tipo_de_orden", "Subtipo_de_orden", "Pet_atis", "resumen_de_PCs_y_PSs_de_la_solicitud", "Ciudad", "Departamento", "XA_ACTUACION", "XA_ACCESS_TECHNOLOGY", "external_id", "Fecha_de_cierre_final", "Nombre_Tecnico", "A_Smart_TV_cableado"]]
    df = df.rename(columns={"XA_ACCESS_TECHNOLOGY": "Medio de acceso", "XA_ACTUACION": "Actuacion"})
    df = df.astype({
        "Tipo_de_orden": str, "Subtipo_de_orden": str, "Pet_atis": str, "Departamento": str,
        "Ciudad": str, "Medio de acceso": str, "external_id": str, "Nombre_Tecnico": str,
        "A_Smart_TV_cableado": str, "resumen_de_PCs_y_PSs_de_la_solicitud": str, "Fecha_de_cierre_final": 'datetime64[ns]', "Actuacion": str
    })
    df = df.merge(consumo_df, left_on="Pet_atis", right_on="PET_ATIS", how="left")
    df = df.fillna({"ALAMBRE_EXT": 0, "ANTENA": 0, "ALAMBRE_INT": 0, "DECO_HD": 0, "DECO_IPTV": 0, "MODEM": 0, "BASEPORT": 0, "CABLE_UTP_W": 0})
    df = df.merge(baremo_df, how="left", left_on=["Tipo_de_orden", "Subtipo_de_orden", "Medio de acceso"], right_on=["TipoOrdenFinal", "SubTipoOrdenFinal", "Medio de acceso"])
    return df

def calcular_liquidacion(df):
    df = df.copy()
    df["Baremos"] = df["Puntos"] * df["Cantidad"]
    df["Factura"] = df["Baremos"] * df["Valor Clase"]
    return df[df["Cantidad"] > 0]
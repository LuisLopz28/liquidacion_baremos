"""
Módulo de procesamiento de liquidaciones
Basado en el código original de liquidación de técnicos
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import os

# Diccionario de reglas por segmento
SEGMENT_RULES = {
    "ALTAS_FIBRA": [
        {"col": "%CASA/EDIFICIO", "formula": lambda r: 1 if r.get("CASA/EDIFICIO", 0) == 1 else 0},
        {"col": "%SMARTTV_CONECT", "formula": lambda r: 1 if r.get("SMARTTV_CONECT", 0) == 1 and r.get("A_Smart_TV_cableado") == "Si" and r.get("CABLE_UTP_W", 0) > 0 else 0},
        {"col": "%BASEPORTADD WIRELESS", "formula": lambda r: r.get("BASEPORT", 0) if r.get("BASEPORTADD WIRELESS", 0) == 1 and r.get("CABLE_UTP_W", 0)/max(r.get("DECO_IPTV", 1), 1) <= 20.9 else 0},
        {"col": "%BASEPORTADD CONNECT", "formula": lambda r: r.get("BASEPORT", 0) if r.get("BASEPORTADD CONNECT", 0) == 1 and r.get("CABLE_UTP_W", 0)/max(r.get("DECO_IPTV", 1), 1) > 20.9 else 0},
        {"col": "%CONNECT", "formula": lambda r: 1 if r.get("CONNECT", 0) == 1 and r.get("CABLE_UTP_W", 0) > 0 else 0},
        {"col": "%WIRELESS", "formula": lambda r: 1 if r.get("WIRELESS", 0) == 1 and r.get("CABLE_UTP_W", 0) == 0 and r.get("MODEM", 0) == 0 and (r.get("DECO_IPTV", 0) >= 1 or r.get("DECO_HD", 0) >= 1) else 0},
        {"col": "%DECOADD", "formula": lambda r: (r.get("DECO_HD", 0) - r.get("WIRELESS", 0)) if r.get("DECOADD", 0) == 1 and r.get("DECO_HD", 0) > 0 else 0},
        {"col": "%DECOIPTVADD_INAL", "formula": lambda r: (r.get("DECO_IPTV", 0) - r.get("%WIRELESS", 0)) if r.get("DECOIPTVADD_INAL", 0) == 1 and r.get("CABLE_UTP_W", 0) == 0 and r.get("DECO_IPTV", 0) > 0 else 0},
        {"col": "%DECOIPTVADD_CONECT", "formula": lambda r: (r.get("DECO_HD", 0)+r.get("DECO_IPTV", 0)-r.get("%CONNECT", 0)-r.get("%WIRELESS", 0)-r.get("%DECOIPTVADD_INAL", 0)-r.get("%DECOADD", 0)) if r.get("DECOIPTVADD_CONECT", 0) == 1 and r.get("CABLE_UTP_W", 0) > 0 else 0},
        {"col": "%CONFIG_MODEM", "formula": lambda r: 1 if r.get("CONFIG_MODEM", 0) == 1 and r.get("MODEM", 0) == 0 else 0},
    ],
    "POSVENTAS_FIBRA": [
        {"col": "%CASA/EDIFICIO", "formula": lambda r: 1 if r.get("CASA/EDIFICIO", 0) == 1 else 0},
        {"col": "%BASEPORTADD WIRELESS", "formula": lambda r: r.get("BASEPORT", 0) if r.get("BASEPORTADD WIRELESS", 0) == 1 and r.get("CABLE_UTP_W", 0)/max(r.get("DECO_IPTV", 1), 1) <= 20.9 else 0},
        {"col": "%BASEPORTADD CONNECT", "formula": lambda r: r.get("BASEPORT", 0) if r.get("BASEPORTADD CONNECT", 0) == 1 and r.get("CABLE_UTP_W", 0)/max(r.get("DECO_IPTV", 1), 1) > 20.9 else 0},
        {"col": "%DECOIPTVADD_INAL", "formula": lambda r: r.get("DECO_IPTV", 0) if r.get("DECOIPTVADD_INAL", 0) == 1 and r.get("CABLE_UTP_W", 0) == 0 else 0},
        {"col": "%DECOIPTVADD_CONECT", "formula": lambda r: (r.get("DECO_IPTV", 0)-r.get("%DECOIPTVADD_INAL", 0)) if r.get("DECOIPTVADD_CONECT", 0) == 1 and r.get("CABLE_UTP_W", 0) > 0 else 0},
        {"col": "%FIRSTDECODTH_FO_VERTICAL", "formula": lambda r: 1 if r.get("FIRSTDECODTH_FO_VERTICAL", 0) == 1 and r.get("ANTENA", 0) == 0 and r.get("DECO_HD", 0) >= 1 and r.get("CASA/EDIFICIO", 0) == 0 else 0},
        {"col": "%TRASLADO INTERNO", "formula": lambda r: 1 if r.get("TRASLADO INTERNO", 0) == 1 and r.get("MODEM", 0) == 0 else 0},
        {"col": "%REPOSICION MODEM BA", "formula": lambda r: 1 if r.get("REPOSICION MODEM BA", 0) == 1 and r.get("MODEM", 0) == 1 else 0},
        {"col": "%REPONER CTROL REMOTO", "formula": lambda r: 1 if r.get("REPONER CTROL REMOTO", 0) == 1 and sum([r.get(k, 0) for k in ["ALAMBRE_EXT","ANTENA","ALAMBRE_INT","DECO_HD","DECO_IPTV","MODEM","BASEPORT","CABLE_UTP_W"]]) == 0 else 0},
        {"col": "%REUBICAR DECO IPTV CONNECT", "formula": lambda r: 1 if r.get("REUBICAR DECO IPTV CONNECT", 0) == 1 and (r.get("BASEPORT", 0)+r.get("MODEM", 0)+r.get("DECO_IPTV", 0)) == 0 and r.get("CABLE_UTP_W", 0) > 0 else 0},
        {"col": "%REPARACION INTERNA", "formula": lambda r: 1 if r.get("REPARACION INTERNA", 0) == 1 else 0},
        {"col": "%REPONER DECO IPTV WIRELESS", "formula": lambda r: 1 if r.get("REPONER DECO IPTV WIRELESS", 0) == 1 and r.get("DECO_IPTV", 0) > 0 else 0},
    ],
    "ALTAS_COBRE": [
        {"col": "%ACOMETIDA", "formula": lambda r: 1 if r.get("ACOMETIDA", 0) == 1 and r.get("ALAMBRE_EXT", 0) >= 150 else 0},
        {"col": "%CAJA", "formula": lambda r: 1 if r.get("CAJA", 0) == 1 and r.get("ALAMBRE_EXT", 0) > 0 else 0},
        {"col": "%DECOADD", "formula": lambda r: r.get("DECO_HD", 0)-1 if r.get("DECOADD", 0) == 1 else 0},
        {"col": "%NA", "formula": lambda r: (r.get("DECO_HD", 0)-r.get("%DECOADD", 0)) if r.get("NA", 0) == 1 else 0},
        {"col": "%STRIP", "formula": lambda r: 1 if r.get("STRIP", 0) == 1 and r.get("ALAMBRE_EXT", 0) == 0 else 0},
    ],
    "POSVENTAS_COBRE": [
        {"col": "%CAJA", "formula": lambda r: 1 if r.get("CAJA", 0) == 1 and r.get("ALAMBRE_EXT", 0) > 0 else 0},
        {"col": "%DECOADD", "formula": lambda r: r.get("DECO_HD", 0)-1 if r.get("DECOADD", 0) == 1 else 0},
        {"col": "%STRIP", "formula": lambda r: 1 if r.get("STRIP", 0) == 1 and r.get("ALAMBRE_EXT", 0) == 0 else 0},
        {"col": "%IP_D", "formula": lambda r: 2 if r.get("IP_D", 0) == 1 else 0},
        {"col": "%IP_T", "formula": lambda r: 2 if r.get("IP_T", 0) == 1 else 0},
        {"col": "%STRIP VERTICAL", "formula": lambda r: 1 if r.get("STRIP VERTICAL", 0) == 1 and r.get("ANTENA", 0) == 0 else 0},
        {"col": "%TRASLADO INTERNO BA", "formula": lambda r: 1 if r.get("TRASLADO INTERNO BA", 0) == 1 and r.get("MODEM", 0) == 0 else 0},
        {"col": "%TRASLADO INTERNO TV", "formula": lambda r: 1 if r.get("TRASLADO INTERNO TV", 0) == 1 and r.get("DECO_HD", 0) > 0 else 0},
        {"col": "%REPOSICION MODEM BA", "formula": lambda r: 1 if r.get("REPOSICION MODEM BA", 0) == 1 and r.get("MODEM", 0) == 1 else 0},
        {"col": "%REPONER CTROL REMOTO", "formula": lambda r: 1 if r.get("REPONER CTROL REMOTO", 0) == 1 and sum([r.get(k, 0) for k in ["ALAMBRE_EXT","DECO_HD","MODEM","CABLE_UTP_W"]]) == 0 else 0},
    ]
}

class LiquidacionProcessor:
    def __init__(self):
        self.segment_rules = SEGMENT_RULES
        
    def clean_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia nombres de columnas: quita espacios y convierte a mayúsculas."""
        df.columns = df.columns.str.strip().str.upper()
        return df
    
    def validate_columns(self, df: pd.DataFrame, required: List[str], df_name: str):
        """Valida que existan columnas críticas."""
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise KeyError(f"❌ Faltan columnas en {df_name}: {missing}")
    
    def load_data(self, cierres_file, consumo_file, baremo_path: str = "data/BaremoOrden.xlsx", 
                  homologado_path: str = "data/Homologado.xlsx") -> Dict[str, pd.DataFrame]:
        """Carga y procesa todos los archivos necesarios."""
        
        # Leer archivos
        cierres = pd.read_excel(cierres_file)
        consumo = pd.read_excel(consumo_file)
        baremo = pd.read_excel(baremo_path)
        homologado = pd.read_excel(homologado_path)
        
        # Limpiar nombres de columnas
        for df in [cierres, consumo, baremo, homologado]:
            self.clean_columns(df)
        
        # Procesar cierres
        cierres = self._process_cierres(cierres)
        
        # Procesar consumo
        consumo_final = self._process_consumo(consumo, homologado)
        
        # Merge datos
        cierres = self._merge_data(cierres, consumo_final, baremo)
        
        return {
            "cierres": cierres,
            "consumo": consumo_final,
            "baremo": baremo,
            "homologado": homologado
        }
    
    def _process_cierres(self, cierres: pd.DataFrame) -> pd.DataFrame:
        """Procesa el DataFrame de cierres."""
        
        # Filtrar columnas
        keep_cols = [
            "TIPO_DE_ORDEN", "SUBTIPO_DE_ORDEN", "PET_ATIS",
            "CIUDAD", "DEPARTAMENTO", "XA_ACTUACION", "XA_ACCESS_TECHNOLOGY",
            "EXTERNAL_ID", "FECHA_DE_CIERRE_FINAL", "NOMBRE_TECNICO", "A_SMART_TV_CABLEADO"
        ]
        cierres = cierres[[c for c in keep_cols if c in cierres.columns]]
        
        # Renombrar columnas
        cierres.rename(columns={
            "XA_ACCESS_TECHNOLOGY": "MEDIO_DE_ACCESO",
            "XA_ACTUACION": "ACTUACION"
        }, inplace=True)
        
        # Asegurar columna A_SMART_TV_CABLEADO
        if "A_SMART_TV_CABLEADO" not in cierres.columns:
            cierres["A_SMART_TV_CABLEADO"] = "No"
        else:
            cierres["A_SMART_TV_CABLEADO"] = cierres["A_SMART_TV_CABLEADO"].fillna("No")
        
        # Validar columnas críticas
        self.validate_columns(cierres, ["MEDIO_DE_ACCESO", "PET_ATIS", "TIPO_DE_ORDEN", "SUBTIPO_DE_ORDEN"], "cierres")
        
        return cierres
    
    def _process_consumo(self, consumo: pd.DataFrame, homologado: pd.DataFrame) -> pd.DataFrame:
        """Procesa el DataFrame de consumo."""
        
        # Filtrar consumo válido
        consumo = consumo[(consumo["TIPO_DE_ORDEN"] != "AVERIA") & (
            ((consumo["TIPO_TRANSACCION"] == "customer") &
             (consumo["SUBTIPO_DE_ORDEN"].isin(["TRASLADOBA", "TRASLADOVOIBA", "TRASLADOVOIBATV"]))) |
            (consumo["TIPO_TRANSACCION"] == "install")
        )]
        
        # Filtrar columnas
        keep_cols = [
            "ACTUACION", "PET_ATIS", "CODIGO", "DESCRIPCION", "SERIAL", "FECHA_DE_CIERRE_FINAL",
            "EXTERNAL_ID", "CANTIDAD", "FAMILIA", "TIPO_DE_ORDEN", "DEPARTAMENTO", "SUBTIPO_DE_ORDEN",
            "TIPO", "MODELO", "TIPO_INGRESO_SAP", "DESC_TIPO_EQUIPO", "XA_ACCESS_TECHNOLOGY"
        ]
        consumo = consumo[[c for c in keep_cols if c in consumo.columns]]
        
        # Merge con homologado
        consumo = consumo.merge(homologado, on=["DESCRIPCION", "DESC_TIPO_EQUIPO"], how="left")
        consumo = consumo[consumo["HOMOLOGADO"].notna() & (consumo["HOMOLOGADO"] != "NA")]
        
        # Crear pivot
        consumo["Combinada"] = consumo["HOMOLOGADO"] + "_"
        pivot = consumo.pivot_table(
            index=["PET_ATIS", "TIPO_DE_ORDEN", "SUBTIPO_DE_ORDEN", "XA_ACCESS_TECHNOLOGY"],
            columns="Combinada",
            values="CANTIDAD",
            aggfunc="sum",
            fill_value=0
        ).reset_index()
        
        # Agregar columnas faltantes
        expected_cols = ["ANTENA_", "DECO_HD_", "DECO_IPTV_", "MODEM_", "BASEPORT_", "CABLE_UTP_W_"]
        for col in expected_cols:
            if col not in pivot.columns:
                pivot[col] = 0
        
        # Renombrar columnas
        rename_map = {col: col.rstrip("_") for col in expected_cols}
        pivot.rename(columns=rename_map, inplace=True)
        
        # Selección final
        final_cols = ["PET_ATIS", "TIPO_DE_ORDEN", "SUBTIPO_DE_ORDEN", "XA_ACCESS_TECHNOLOGY"] + list(rename_map.values())
        return pivot[final_cols]
    
    def _merge_data(self, cierres: pd.DataFrame, consumo_final: pd.DataFrame, baremo: pd.DataFrame) -> pd.DataFrame:
        """Combina todos los DataFrames."""
        
        # Asegurar tipo string para PET_ATIS
        cierres["PET_ATIS"] = cierres["PET_ATIS"].astype(str).str.strip()
        consumo_final["PET_ATIS"] = consumo_final["PET_ATIS"].astype(str).str.strip()
        
        # Merge con consumo
        cols_to_add = ["PET_ATIS"] + [c for c in consumo_final.columns if c not in [
            "TIPO_DE_ORDEN", "SUBTIPO_DE_ORDEN", "PET_ATIS", "CIUDAD", "DEPARTAMENTO",
            "ACTUACION", "MEDIO_DE_ACCESO", "EXTERNAL_ID", "FECHA_DE_CIERRE_FINAL", 
            "NOMBRE_TECNICO", "A_SMART_TV_CABLEADO"
        ]]
        cierres = cierres.merge(consumo_final[cols_to_add], on="PET_ATIS", how="left")
        
        # Merge con baremo
        cierres = cierres.merge(baremo, left_on=["TIPO_DE_ORDEN", "SUBTIPO_DE_ORDEN", "MEDIO_DE_ACCESO"],
                               right_on=["TIPOORDENFINAL", "SUBTIPOORDENFINAL", "MEDIO DE ACCESO"], how="left")
        
        # Pivot final
        cierres = cierres.pivot_table(
            index=["TIPO_DE_ORDEN", "SUBTIPO_DE_ORDEN", "PET_ATIS", "CIUDAD", "DEPARTAMENTO",
                   "ACTUACION", "MEDIO_DE_ACCESO", "EXTERNAL_ID", "FECHA_DE_CIERRE_FINAL", 
                   "NOMBRE_TECNICO", "A_SMART_TV_CABLEADO", "ANTENA", "DECO_HD", "DECO_IPTV", 
                   "MODEM", "BASEPORT", "CABLE_UTP_W"],
            columns="CONCEPTO",
            aggfunc="size",
            fill_value=0
        ).reset_index()
        
        return cierres
    
    def apply_segment_rules(self, df: pd.DataFrame, rules: List[Dict]) -> pd.DataFrame:
        """Aplica las reglas de segmento a un DataFrame."""
        df = df.copy()
        for rule in rules:
            col = rule["col"]
            df[col] = df.apply(rule["formula"], axis=1)
        return df
    
    def process_segment(self, cierres: pd.DataFrame, segment_name: str, rules: List[Dict], 
                       baremo: pd.DataFrame) -> pd.DataFrame:
        """Procesa un segmento específico."""
        
        # Determinar medio y tipo
        medio = "FIBRA" if "FIBRA" in segment_name else "COBRE"
        tipo = "ALTA" if "ALTAS" in segment_name else "POSVENTA"
        
        # Filtrar
        seg_df = cierres[(cierres["MEDIO_DE_ACCESO"] == medio) & (cierres["TIPO_DE_ORDEN"] == tipo)].copy()
        if seg_df.empty:
            return seg_df
        
        # Aplicar reglas
        seg_df = self.apply_segment_rules(seg_df, rules)
        
        # Unpivot columnas con %
        cols_unpivot = [c for c in seg_df.columns if c.startswith("%")]
        melted = seg_df.melt(
            id_vars=[c for c in seg_df.columns if c not in cols_unpivot],
            value_vars=cols_unpivot,
            var_name="ATRIBUTO", 
            value_name="CANTIDAD"
        )
        melted["ATRIBUTO"] = melted["ATRIBUTO"].str.replace("%", "")
        
        # Join con baremo
        merged = melted.merge(
            baremo,
            left_on=["MEDIO_DE_ACCESO", "TIPO_DE_ORDEN", "SUBTIPO_DE_ORDEN", "ATRIBUTO"],
            right_on=["MEDIO DE ACCESO", "TIPOORDENFINAL", "SUBTIPOORDENFINAL", "CONCEPTO"],
            how="left"
        )
        merged["BAREMOS"] = merged["PUNTOS"].fillna(0) * merged["CANTIDAD"]
        
        return merged[merged["CANTIDAD"] > 0]
    
    def process_all_segments(self, data: Dict[str, pd.DataFrame]) -> Tuple[pd.DataFrame, List[pd.DataFrame]]:
        """Procesa todos los segmentos y retorna el resultado final."""
        
        cierres = data["cierres"]
        baremo = data["baremo"]
        
        segments = []
        segment_dfs = []
        
        for seg_name, rules in self.segment_rules.items():
            df_segment = self.process_segment(cierres, seg_name, rules, baremo)
            if not df_segment.empty:
                segments.append(df_segment)
                segment_dfs.append((seg_name, df_segment))
        
        if segments:
            final_df = pd.concat(segments, ignore_index=True)
            final_df["FACTURA"] = final_df["BAREMOS"] * final_df["VALOR CLASE"]
            return final_df, segment_dfs
        else:
            return pd.DataFrame(), []
    
    def export_to_excel(self, final_df: pd.DataFrame, segment_dfs: List[Tuple[str, pd.DataFrame]], 
                       additional_dfs: Dict[str, pd.DataFrame], filename: str = "Liquidacion.xlsx") -> str:
        """Exporta todos los DataFrames a Excel."""
        
        with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
            # Hoja principal
            final_df.to_excel(writer, sheet_name="Liquidacion Final", index=False)
            
            # Hojas adicionales
            for name, df in additional_dfs.items():
                df.to_excel(writer, sheet_name=name, index=False)
            
            # Segmentos
            for seg_name, df in segment_dfs:
                df.to_excel(writer, sheet_name=seg_name, index=False)
        
        return filename
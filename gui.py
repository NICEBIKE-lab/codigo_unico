"""
Aplicación Streamlit — Generador de Código Unificado
=====================================================
Carga un archivo CSV o Excel con las columnas:
  • code
  • items_log_description
  • parent_description

Normaliza el texto de las tres columnas, genera el campo
``codigo_unificado`` y detecta duplicados exactos.

El código unificado puede ser:
  • SHA1 (12 caracteres hexadecimales) de la concatenación normalizada
  • ID incremental por grupo único (CU-000001, CU-000002, …)
"""

from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from processor import REQUIRED_COLUMNS, process, validate_columns

# ---------------------------------------------------------------------------
# Configuración de página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Código Unificado",
    page_icon="🔗",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Helpers de UI
# ---------------------------------------------------------------------------

def load_file(uploaded) -> pd.DataFrame:
    """Lee un CSV o Excel subido por el usuario."""
    name = uploaded.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded, dtype=object)
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded, dtype=object)
    raise ValueError(
        f"Formato no soportado: '{uploaded.name}'. "
        "Se aceptan archivos .csv, .xlsx y .xls."
    )


# ---------------------------------------------------------------------------
# UI principal
# ---------------------------------------------------------------------------

st.title("🔗 Generador de Código Unificado")
st.caption(
    "Carga un archivo CSV o Excel, normaliza las columnas y genera un "
    "``codigo_unificado`` único por combinación."
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Opciones")
    method = st.radio(
        "Tipo de código unificado",
        options=["incremental", "sha1"],
        format_func=lambda x: (
            "ID incremental  (CU-000001, CU-000002, …)"
            if x == "incremental"
            else "Hash SHA1  (12 caracteres hex)"
        ),
        help=(
            "Incremental: legible y ordenado. "
            "SHA1: basado en el contenido, reproducible entre ejecuciones."
        ),
    )
    show_norm = st.checkbox(
        "Mostrar columnas normalizadas",
        value=False,
        help="Incluye _norm_code, _norm_desc, _norm_parent en la vista.",
    )
    only_dups = st.checkbox(
        "Mostrar solo duplicados",
        value=False,
        help="Filtra la tabla para ver únicamente las filas duplicadas.",
    )

# ── Carga de archivo ──────────────────────────────────────────────────────────
st.subheader("1 · Cargar archivo")
uploaded = st.file_uploader(
    "Selecciona un archivo CSV o Excel (.xlsx / .xls)",
    type=["csv", "xlsx", "xls"],
    help="Debe contener las columnas: code, items_log_description, parent_description",
)

if uploaded is None:
    st.info("Sube un archivo para comenzar.")
    st.stop()

# ── Preview de datos crudos ────────────────────────────────────────────────────
try:
    df_raw = load_file(uploaded)
except Exception as exc:
    st.error(f"No se pudo leer el archivo: {exc}")
    st.stop()

missing = validate_columns(df_raw)
if missing:
    st.error(
        f"El archivo no contiene las columnas requeridas: **{', '.join(missing)}**\n\n"
        f"Columnas encontradas: {', '.join(df_raw.columns.tolist())}"
    )
    st.stop()

with st.expander("📄 Vista previa del archivo cargado", expanded=True):
    st.caption(f"{len(df_raw):,} filas · {len(df_raw.columns)} columnas")
    st.dataframe(df_raw.head(50), use_container_width=True, height=250)

# ── Procesamiento ────────────────────────────────────────────────────────────
st.subheader("2 · Procesar")

if st.button("▶ Generar código unificado", type="primary", use_container_width=True):
    with st.spinner("Procesando…"):
        df_result = process(df_raw, method)
    st.session_state["result"] = df_result
    st.session_state["method"] = method
    st.success("✅ Procesamiento completado.")

if "result" not in st.session_state:
    st.stop()

df_result: pd.DataFrame = st.session_state["result"]

# ── Métricas de resumen ────────────────────────────────────────────────────────
st.subheader("3 · Resumen")

total = len(df_result)
unique_codes = df_result["codigo_unificado"].nunique()
dup_rows = int(df_result["es_duplicado"].sum())
unique_rows = total - dup_rows  # filas sin duplicado

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de filas", f"{total:,}")
col2.metric("Códigos únicos", f"{unique_codes:,}")
col3.metric("Filas duplicadas", f"{dup_rows:,}")
col4.metric("Filas sin duplicado", f"{unique_rows:,}")

# ── Tabla de resultados ────────────────────────────────────────────────────────
st.subheader("4 · Código unificado")

# Columnas a mostrar
norm_cols = ["_norm_code", "_norm_desc", "_norm_parent"]
base_cols = REQUIRED_COLUMNS + ["codigo_unificado", "es_duplicado", "conteo_duplicados"]
display_cols = base_cols + (norm_cols if show_norm else [])

if only_dups:
    df_view = df_result[df_result["es_duplicado"]][display_cols]
    st.caption(f"Mostrando {len(df_view):,} filas duplicadas de {total:,}")
else:
    df_view = df_result[display_cols]
    st.caption(f"Mostrando {len(df_view):,} filas")

# Resalta duplicados con color de fondo
def _highlight_dup(row: pd.Series):
    if row.get("es_duplicado", False):
        return ["background-color: #fff3cd"] * len(row)
    return [""] * len(row)

st.dataframe(
    df_view.style.apply(_highlight_dup, axis=1),
    use_container_width=True,
    height=420,
)

# ── Descarga ──────────────────────────────────────────────────────────────────
st.subheader("5 · Descargar resultado")

export_cols = REQUIRED_COLUMNS + ["codigo_unificado", "es_duplicado", "conteo_duplicados"]
if show_norm:
    export_cols += norm_cols

df_export = df_result[export_cols]

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    df_export.to_excel(writer, index=False, sheet_name="resultado")
    # Hoja adicional con solo los duplicados
    df_dups_export = df_export[df_export["es_duplicado"]]
    if not df_dups_export.empty:
        df_dups_export.to_excel(writer, index=False, sheet_name="duplicados")

st.download_button(
    label="⬇ Descargar Excel (resultado completo)",
    data=buffer.getvalue(),
    file_name="codigo_unificado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
    type="primary",
)

st.caption(
    "El archivo contiene dos hojas: **resultado** (todos los datos) y "
    "**duplicados** (solo filas duplicadas)."
)

"""
Lógica de procesamiento para el generador de Código Unificado.

Este módulo puede importarse de forma independiente sin inicializar Streamlit,
lo que permite su uso en tests y en scripts de línea de comandos.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

import pandas as pd

REQUIRED_COLUMNS = ["code", "items_log_description", "parent_description"]


def normalize(value: object) -> str:
    """Convierte un valor a texto normalizado: UPPERCASE, sin tildes, sin
    espacios múltiples, sin espacios al inicio/fin.

    Retorna una cadena vacía para valores ``None``, ``NaN`` o ``pd.NA``.
    """
    if pd.isna(value):
        return ""
    s = str(value).strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.upper()
    s = re.sub(r"\s+", " ", s)
    return s


def sha1_code(key: str) -> str:
    """Devuelve los primeros 12 caracteres del hash SHA1 en mayúsculas."""
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12].upper()


def validate_columns(df: pd.DataFrame) -> list[str]:
    """Retorna la lista de columnas requeridas que faltan en *df*."""
    return [c for c in REQUIRED_COLUMNS if c not in df.columns]


def process(df: pd.DataFrame, method: str) -> pd.DataFrame:
    """
    Aplica normalización y genera ``codigo_unificado``.

    Parameters
    ----------
    df:
        DataFrame con al menos las columnas ``REQUIRED_COLUMNS``.
    method:
        ``"sha1"`` o ``"incremental"``.

    Returns
    -------
    DataFrame con las columnas originales más:

    * ``_norm_code``, ``_norm_desc``, ``_norm_parent`` — texto normalizado
    * ``codigo_unificado`` — código único por combinación normalizada
    * ``es_duplicado`` — ``True`` si la combinación ya apareció antes en el
      archivo
    * ``conteo_duplicados`` — número de veces que aparece esa combinación
    """
    out = df.copy()

    out["_norm_code"] = out["code"].apply(normalize)
    out["_norm_desc"] = out["items_log_description"].apply(normalize)
    out["_norm_parent"] = out["parent_description"].apply(normalize)

    # Clave de agrupación (separador improbable en datos reales)
    out["_clave"] = (
        out["_norm_code"] + "\x00" + out["_norm_desc"] + "\x00" + out["_norm_parent"]
    )

    if method == "sha1":
        out["codigo_unificado"] = out["_clave"].apply(sha1_code)
    else:
        # Incremental: asigna un ID a cada combinación única en el orden en
        # que aparece por primera vez
        unique_keys = list(dict.fromkeys(out["_clave"]))  # preserva orden
        key_to_id = {k: f"CU-{i:06d}" for i, k in enumerate(unique_keys, 1)}
        out["codigo_unificado"] = out["_clave"].map(key_to_id)

    # Detección de duplicados
    counts = out["_clave"].map(out["_clave"].value_counts())
    out["conteo_duplicados"] = counts
    out["es_duplicado"] = counts > 1

    out = out.drop(columns=["_clave"])
    return out

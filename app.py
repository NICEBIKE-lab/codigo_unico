from pathlib import Path
import re
import unicodedata
import pandas as pd

COL_NOMBRE = "NombreSucursal"
OUTPUT_FILE = "archivo_unificado.xlsx"
INPUT_CANDIDATES = (
    "archivo_entrada.xlsx",
    "input.xlsx",
    "data.xlsx",
)

def _norm_text(value: object) -> str:
    if pd.isna(value):
        return ""
    s = str(value)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.upper().strip()
    s = re.sub(r"\s+", " ", s)
    return s

def _norm_header(value: object) -> str:
    s = _norm_text(value)
    s = re.sub(r"[^A-Z0-9]+", "", s)  # quita espacios, _, -, etc.
    return s

def _find_nombre_column(df: pd.DataFrame, expected: str = COL_NOMBRE) -> str:
    expected_norm = _norm_header(expected)

    # Match exacto normalizado
    for c in df.columns:
        if _norm_header(c) == expected_norm:
            return c

    # Alias comunes
    aliases = {"NOMBRESUCURSAL", "NOMBRESUC", "SUCURSAL", "NOMBRE"}
    for c in df.columns:
        if _norm_header(c) in aliases:
            return c

    # Fallback: primera columna
    return df.columns[0]

def _to_code(value: str) -> str:
    s = _norm_text(value)
    s = re.sub(r"[^A-Z0-9]+", "-", s).strip("-")
    return f"SUC-{s}" if s else "SUC-SIN-NOMBRE"


def _resolve_input_file(base_dir: Path) -> Path:
    for filename in INPUT_CANDIDATES:
        candidate = base_dir / filename
        if candidate.exists():
            return candidate

    available = ", ".join(INPUT_CANDIDATES)
    raise FileNotFoundError(
        f"No se encontró archivo de entrada. Crea uno de: {available}"
    )


def build_unification_key(row: pd.Series) -> str:
    code = _norm_text(row.get("codigo_unificado", ""))
    return code or "SUC-SIN-NOMBRE"

def main() -> None:
    base_dir = Path(__file__).resolve().parent
    input_file = _resolve_input_file(base_dir)
    output_file = base_dir / OUTPUT_FILE

    df = pd.read_excel(input_file, dtype=object)

    if df.empty:
        raise ValueError("El archivo no tiene filas.")
    if len(df.columns) == 0:
        raise ValueError("El archivo no tiene columnas.")

    col_nombre_real = _find_nombre_column(df, COL_NOMBRE)
    print(f"Usando columna para unificación: {col_nombre_real}")

    # Clave de unificación: NombreSucursal (o primera columna si no existe)
    df["criterio_unificacion"] = df[col_nombre_real].apply(_norm_text)
    df["codigo_unificado"] = df[col_nombre_real].apply(_to_code)

    # Unificación por familia de code
    df["criterio_unificacion"] = df.apply(build_unification_key, axis=1)

    unique_keys = pd.Index(df["criterio_unificacion"]).unique()
    key_to_variant = {k: f"VAR-{i:06d}" for i, k in enumerate(unique_keys, start=1)}
    df["codigo_variante"] = df["criterio_unificacion"].map(key_to_variant)

    df.to_excel(output_file, index=False)
    print(f"Proceso terminado. Archivo generado: {output_file}")


if __name__ == "__main__":
    main()
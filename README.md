# codigo_unico
Revisa código único en filas

## GUI — Aplicación Streamlit

Interfaz web interactiva para generar y visualizar el `codigo_unificado`.

### Uso

1. Instala dependencias:

	```bash
	pip install -r requirements.txt
	```

2. Ejecuta la aplicación:

	```bash
	streamlit run gui.py
	```

3. En el navegador:
   - Sube un archivo CSV o Excel con las columnas `code`, `items_log_description`, `parent_description`.
   - Elige el tipo de código unificado (ID incremental o hash SHA1).
   - Haz clic en **"Generar código unificado"**.
   - Visualiza el resultado y descarga el Excel con las hojas `resultado` y `duplicados`.

### Columnas requeridas en el archivo de entrada

| Columna                 | Descripción                          |
|-------------------------|--------------------------------------|
| `code`                  | Código del ítem                      |
| `items_log_description` | Descripción del ítem                 |
| `parent_description`    | Descripción del elemento padre/ruta  |

### Tipos de código unificado

| Tipo          | Ejemplo        | Descripción                                            |
|---------------|----------------|--------------------------------------------------------|
| Incremental   | `CU-000001`    | ID secuencial por grupo único, en orden de aparición   |
| SHA1          | `3A7F9C2B1E04` | Hash SHA1 (12 hex) de la concatenación normalizada     |

---

## Script de línea de comandos (`app.py`)

### Uso

1. Coloca un archivo Excel de entrada en la raíz con uno de estos nombres:
   - `archivo_entrada.xlsx`
   - `input.xlsx`
   - `data.xlsx`

2. Ejecuta:

	```bash
	python app.py
	```

El resultado se guarda como `archivo_unificado.xlsx`.


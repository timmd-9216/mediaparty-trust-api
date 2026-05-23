# Setup y Configuración del Proyecto

## Problema con UV en macOS ARM64

### Descripción del Problema

Al intentar ejecutar `uv sync` en este proyecto, se produce el siguiente error:

```
error: Distribution `torch==2.8.0 @ registry+https://pypi.org/simple` can't be installed because it doesn't have a source distribution or wheel for the current platform

hint: You're on macOS (`macosx_14_0_x86_64`), but `torch` (v2.8.0) only has wheels for the following platforms: `manylinux_2_28_aarch64`, `manylinux_2_28_x86_64`, `macosx_11_0_arm64`, `win_amd64`
```

### Causa Raíz

El problema ocurre porque:

1. **Detección incorrecta de plataforma**: `uv` detecta la plataforma como `macosx_14_0_x86_64` (arquitectura Intel x86_64) cuando el sistema real es ARM64 (Apple Silicon).

2. **Incompatibilidad de versiones de PyTorch**: Las versiones recientes de PyTorch (2.6.0+) tienen ruedas precompiladas para `macosx_11_0_arm64`, pero `uv` busca ruedas para `macosx_14_0_x86_64` que no existen.

3. **Ambiente en modo Rosetta**: Si Python se ejecuta bajo Rosetta (x86_64 emulado), `uv` puede detectar la plataforma incorrectamente como `macosx_14_0_x86_64`.

### Verificación del Problema

```bash
# El sistema es ARM64
$ uname -m
arm64

# Python es ARM64
$ file $(which python)
.../python: Mach-O 64-bit executable arm64

# UV es ARM64
$ file $(which uv)
.../uv: Mach-O 64-bit executable arm64

# Pero UV detecta la plataforma como x86_64
$ uv sync
# Error: macosx_14_0_x86_64
```

### Solución: Usar pip con venv

La solución es usar `pip` con un entorno virtual estándar de Python en lugar de `uv`:

```bash
# Crear y activar el entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias con pip
pip install -e .
```

**Por qué funciona con pip:**

1. **Detección correcta de plataforma**: `pip` detecta correctamente la arquitectura ARM64 del intérprete de Python.

2. **Sin dependencias externas**: `python -m venv` está incluido en la stdlib, sin necesidad de conda ni herramientas adicionales.

3. **Versiones de PyTorch disponibles**: `pip` encuentra las ruedas correctas de PyTorch para `macosx_11_0_arm64`.

## Ejecución del Proyecto

### Iniciar la API

```bash
# Opción 1: Usando el script
./run_api.sh

# Opción 2: Comando directo
source .venv/bin/activate && uvicorn mediaparty_trust_api.main:app --reload
```

### Ejecutar el Cliente de Prueba

```bash
source .venv/bin/activate && python test_api.py --input test/input_example.json
```

## Recomendaciones

1. **Para este proyecto**: Usar `pip` con `python -m venv` hasta que `uv` resuelva el problema de detección de plataforma en macOS ARM64.

2. **Actualizar UV**: Verificar si hay versiones más recientes de `uv` que solucionen este problema:
   ```bash
   uv self update
   ```

3. **Alternativa con UV forzando plataforma**: Si se quiere usar `uv`, forzar la plataforma manualmente:
   ```bash
   UV_PYTHON_PLATFORM=macosx_11_0_arm64 uv sync
   ```

## Dependencias del Proyecto

- `requests`: Cliente HTTP para llamar a la API
- `fastapi`: Framework web para la API
- `uvicorn`: Servidor ASGI
- `stanza`: Procesamiento de lenguaje natural (requiere PyTorch)
- `torch`: Framework de deep learning (dependencia transitiva de stanza)

## Estructura del Proyecto

```
mediaparty-trust-api/
├── src/mediaparty_trust_api/
│   ├── main.py              # Punto de entrada de la API
│   ├── api/v1/endpoints.py  # Endpoints de la API
│   └── services/            # Servicios de análisis
├── test/
│   ├── input.json           # Plantilla de entrada
│   └── input_example.json   # Ejemplo completo
├── test_api.py              # Cliente de prueba
├── run_api.sh               # Script para iniciar la API
└── pyproject.toml           # Configuración del proyecto
```

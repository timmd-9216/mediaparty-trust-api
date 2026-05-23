# Prompts

Este directorio contiene los prompts y criterios de cada métrica de análisis
de confianza, **desacoplados** del código Python. Permiten versionar el
texto del prompt independientemente del código y, para las métricas que usan
LLM, optimizarlo con DSPy.

## Convención de archivos

Para cada métrica hay dos archivos:

- `prompt-<metric>.txt` — Texto del prompt / descripción del criterio.
  Es el artefacto versionable. Para métricas LLM-driven es la `instructions`
  del `dspy.Signature`; para métricas estadísticas documenta el criterio,
  thresholds y rationale para que se puedan auditar y migrar a LLM más
  adelante.
- `prompt-<metric>.json` — Definición estructurada:
  - `name`     — nombre de la signature
  - `inputs`   — campos de entrada con `type` y `description`
  - `outputs`  — campos de salida (structured output) con `type` y `description`
  - `thresholds` *(opcional)* — bandas numéricas y sus `flag`/`score`
    asociados, para que los thresholds vivan junto al prompt.

### Esquema del JSON

```json
{
  "name": "NombreDeLaSignature",
  "inputs":  { "<campo>": {"type": "string", "description": "..."} },
  "outputs": { "<campo>": {"type": "string", "description": "..."} },
  "thresholds": { "...": {} }
}
```

`types` soportados por el loader: `string`, `integer`, `number`, `boolean`.

## Métricas implementadas

| Métrica | Archivos | Modo |
|---|---|---|
| Qualitative Adjectives | `prompt-adjectives.{txt,json}` | LLM (DSPy + OpenRouter) |
| Word Count | `prompt-word-count.{txt,json}` | Estadística (Stanza) |
| Sentence Complexity | `prompt-sentence-complexity.{txt,json}` | Estadística (Stanza) |
| Verb Tense | `prompt-verb-tense.{txt,json}` | Estadística (Stanza) |

### 1. Qualitative Adjectives (LLM-Enhanced)

- Filtra adjetivos calificativos (subjetivos) vs descriptivos (objetivos)
  usando un LLM vía OpenRouter + DSPy.
- Thresholds sobre el ratio `qualitative_count / total_words`:
  - `<= 5%`  excelente (objetivo)
  - `<= 10%` moderado
  - `> 10%`  alto (sesgado / sensacionalista)
- **Importa porque:** un exceso de adjetivos calificativos es señal de sesgo o
  sensacionalismo.

### 2. Word Count

- Evalúa la longitud total del artículo (palabras tokenizadas por Stanza).
- Thresholds: `>= 500` comprehensivo, `>= 300` adecuado, `< 300` muy breve.
- **Importa porque:** la profundidad de la cobertura correlaciona con la
  calidad de la investigación.

### 3. Sentence Complexity

- Promedio de palabras por oración.
- Rango óptimo: 15–25 palabras/oración.
- **Importa porque:** una complejidad adecuada asegura legibilidad sin
  oversimplificación.

### 4. Verb Tense

- Distribución de tiempos verbales (ratio `past / total_verbs`).
- Esperado en noticias: 40–70% en pasado.
- **Importa porque:** el uso correcto de tiempos verbales indica estilo
  profesional de reporting periodístico.

## Cómo se usan desde el código

El loader vive en
`src/mediaparty_trust_api/services/prompt_loader.py` y expone:

```python
from mediaparty_trust_api.services.prompt_loader import load_dspy_signature, load_thresholds

# Carga prompts/prompt-adjectives.{txt,json} y construye un dspy.Signature
QualitativeAdjectiveFilter = load_dspy_signature("adjectives")

# Carga thresholds desde prompts/prompt-word-count.json
th = load_thresholds("word-count")
```

### Consumo en runtime

Todas las métricas consumen sus **thresholds** desde los archivos JSON en
tiempo de ejecución (`services/metrics.py`):

- `get_adjective_count()` → `load_thresholds("adjectives")` + usa Signature DSPy
- `get_word_count()` → `load_thresholds("word-count")`
- `get_sentence_complexity()` → `load_thresholds("sentence-complexity")`
- `get_verb_tense_analysis()` → `load_thresholds("verb-tense")`

Esto permite ajustar bandas de puntuación (`flag`, `score`, rangos numéricos)
sin tocar el código Python — solo editando los archivos JSON en este
directorio.

# Prompts

Este directorio contiene los prompts usados por las métricas que apoyan su
análisis en un LLM (vía DSPy + OpenRouter).

Para cada métrica que use LLM hay dos archivos:

- `prompt-<metric>.txt` — Texto del prompt (instrucciones del `dspy.Signature`).
  Es el archivo versionable que luego puede optimizar DSPy (p.ej. con
  `BootstrapFewShot`, `MIPRO`, etc.).
- `prompt-<metric>.json` — Definición del *structured output*: nombre de la
  signature, campos de entrada (`inputs`) y campos de salida (`outputs`) con
  su `type` y `description`.

## Formato del JSON

```json
{
  "name": "NombreDeLaSignature",
  "inputs": {
    "<campo_input>": {
      "type": "string",
      "description": "..."
    }
  },
  "outputs": {
    "<campo_output>": {
      "type": "string",
      "description": "..."
    }
  }
}
```

En tiempo de ejecución, `services/metrics.py` lee ambos archivos y construye
dinámicamente un `dspy.Signature` equivalente mediante
`load_dspy_signature("adjectives")`.

## Prompts disponibles

- `prompt-adjectives.{txt,json}` — Filtrado de adjetivos calificativos
  (usado por `get_adjective_count`).

> Nota: Las otras métricas (`word_count`, `sentence_complexity`,
> `verb_tense_analysis`) son puramente estadísticas sobre el `Document` de
> Stanza y no usan prompts LLM, por lo que no tienen archivos aquí.

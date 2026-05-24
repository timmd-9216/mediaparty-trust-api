# Prompt Tester App

Aplicación web independiente para iterar y probar el desarrollo de prompts del MediaParty Trust API.

## Características

- **Extracción desde URL**: Ingresa una URL de noticia y el sistema extrae automáticamente:
  - Título
  - Cuerpo de la nota
  - Autor
  - Editor responsable (del footer)
  - Grupo de medios (del footer)

- **Ingreso manual**: También puedes ingresar el título y cuerpo directamente

- **Análisis de métricas**: Visualiza los resultados de las métricas de análisis:
  - Qualitative Adjectives
  - Word Count
  - Sentence Complexity
  - Verb Tense
  - Title-Content Relation

## Requisitos

- Node.js 18+
- La API de MediaParty Trust corriendo en `http://localhost:8000`

## Instalación

```bash
cd prompt-tester-app
npm install
```

## Uso

### 1. Iniciar la API

Primero asegúrate de que la API esté corriendo:

```bash
cd ..
python -m uvicorn mediaparty_trust_api.main:app --reload
```

### 2. Iniciar la app

En otra terminal:

```bash
cd prompt-tester-app
npm run dev
```

La app estará disponible en `http://localhost:3001`

### 3. Configurar URL de la API

Por defecto, la app asume que la API corre en `http://localhost:8000`. 
Puedes cambiar esto configurando la variable de entorno:

```bash
export NEXT_PUBLIC_API_URL=http://tu-api-url:8000
npm run dev
```

## Estructura

- `app/page.tsx`: Página principal con estado y lógica
- `app/components/ArticleAnalyzer.tsx`: Formulario de ingreso de URL/texto
- `app/components/ScrapeResults.tsx`: Visualización de datos extraídos
- `app/components/MetricsResults.tsx`: Visualización de métricas
- `app/components/icons.tsx`: Iconos SVG inline

## Desarrollo

Para modificar los prompts, edita los archivos en `/prompts/` de la API principal.
Esta app permite probar rápidamente cómo funcionan los cambios sin necesidad
de usar curl o herramientas externas.

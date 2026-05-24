"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

import os

from mediaparty_trust_api.api.v1 import router as api_v1_router
from mediaparty_trust_api.core.config import config  # Load .env variables
from mediaparty_trust_api.services.prompt_loader import list_prompts, validate_prompts
from mediaparty_trust_api.services.stanza_service import stanza_service

from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    Downloads and initializes the Stanza Spanish model on startup.
    """
    # Discover and validate every metric defined under prompts/
    prompts = list_prompts()
    print(f"Discovered {len(prompts)} prompt definition(s) in prompts/:")
    for p in prompts:
        kind = "LLM" if p["has_llm_signature"] else "stats-only"
        print(
            f"  - {p['name']:<28} signature={p['signature'] or '-':<32} "
            f"kind={kind:<10} thresholds={'yes' if p['has_thresholds'] else 'no'}"
        )

    validation = validate_prompts()
    print(
        f"Prompt validation: {len(validation['valid'])}/{validation['total']} OK, "
        f"{len(validation['errors'])} error(s), "
        f"{len(validation.get('skipped', []))} skipped"
    )
    for skip in validation.get("skipped", []):
        print(f"  [SKIPPED] {skip['name']}: {skip['reason']}")
    for err in validation["errors"]:
        print(f"  [INVALID] {err['name']}: {err['error']} (ignored)")

    # Report LLM configuration
    model = os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")
    has_key = bool(os.getenv("OPENROUTER_API_KEY"))
    print(
        f"LLM config: model={model} | OPENROUTER_API_KEY={'set' if has_key else 'NOT SET'}"
    )

    # Startup: Initialize Stanza Spanish model (optional)
    print("Initializing Stanza Spanish model...")
    stanza_service.initialize()
    if stanza_service.is_initialized:
        print("Stanza model initialized successfully!")
    else:
        print("Stanza unavailable; metrics will run in degraded (text-based) mode.")

    yield

    # Shutdown: cleanup if needed
    print("Shutting down...")


app = FastAPI(
    title="MediaParty Trust API",
    description="""
    ## Journalism Quality Analysis System

    An intelligent journalism quality analysis system that combines NLP with LLM-powered metrics
    to evaluate article credibility and objectivity.

    ### Features

    * **LLM-Powered Adjective Analysis**: Uses OpenRouter + DSPy to distinguish qualitative
      (opinionated) from descriptive (objective) adjectives
    * **Multi-Metric Evaluation**: 4 complementary metrics for comprehensive article assessment
    * **NLP Foundation**: Stanford Stanza for robust Spanish language processing

    ### Metrics Evaluated

    1. **Qualitative Adjectives**: Filters adjectives using LLM to identify opinion vs. objective language
    2. **Word Count**: Evaluates article length and coverage depth
    3. **Sentence Complexity**: Analyzes readability and writing sophistication
    4. **Verb Tense Analysis**: Evaluates professional news reporting style

    ### Getting Started

    1. Navigate to the `/api/v1/analyze` endpoint below
    2. Click "Try it out"
    3. Use the pre-filled example or paste your own article
    4. Click "Execute" to see the analysis results
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    contact={
        "name": "MediaParty Trust API",
        "url": "https://github.com/your-repo/mediaparty-trust-api",
    },
    license_info={
        "name": "License",
        "url": "https://github.com/your-repo/mediaparty-trust-api/blob/main/LICENSE",
    },
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to MediaParty Trust API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Include API v1 routes
app.include_router(api_v1_router, prefix="/api/v1")

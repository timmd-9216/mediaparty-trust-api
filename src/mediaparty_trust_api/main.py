"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from mediaparty_trust_api.api.v1 import router as api_v1_router
from mediaparty_trust_api.services.stanza_service import stanza_service

# from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    Downloads and initializes the Stanza Spanish model on startup.
    """
    # Startup: Initialize Stanza Spanish model
    print("Initializing Stanza Spanish model...")
    stanza_service.initialize()
    print("Stanza model initialized successfully!")

    yield

    # Shutdown: cleanup if needed
    print("Shutting down...")


app = FastAPI(
    title="MediaParty Trust API",
    description="API for analyzing article trust and credibility",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# # Configure CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Configure appropriately for production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


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

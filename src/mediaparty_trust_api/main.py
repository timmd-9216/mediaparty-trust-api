"""Main FastAPI application entry point."""

from fastapi import FastAPI

from mediaparty_trust_api.api.v1 import router as api_v1_router

# from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="MediaParty Trust API",
    description="API for analyzing article trust and credibility",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
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

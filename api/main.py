"""
FastAPI application main file
"""
from fastapi import FastAPI

import service
from api.routers.clients import router as clients_router

logger = service.logger

# Initialize FastAPI
app = FastAPI(
    title="OpenVPN Client Manager API",
    description="API for managing OpenVPN clients",
    version="1.0.0"
)

# Include routers
app.include_router(clients_router)


@app.get("/")
def read_root():
    """Health check endpoint"""
    return {"message": "OpenVPN Manager API is running"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "OpenVPN Manager API"}

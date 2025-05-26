#!/usr/bin/env python3
"""
Server runner for the OpenVPN Manager API
"""
import os
import uvicorn
from api.main import app
import service

logger = service.logger


def run_server():
    """Run the API server"""
    port = int(os.environ.get("OVPN_API_PORT", 8000))
    host = os.environ.get("OVPN_API_HOST", "127.0.0.1")
    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()

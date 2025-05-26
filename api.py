#!/usr/bin/env python3
"""
FastAPI interface for OpenVPN client management
"""
import os
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import APIKeyHeader
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import service

logger = service.logger

# Initialize FastAPI
app = FastAPI(
    title="OpenVPN Client Manager API",
    description="API for managing OpenVPN clients",
    version="1.0.0"
)

# Security - API key authentication
API_KEY = os.environ.get("OVPN_API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key")


def get_api_key(api_key: str = Security(api_key_header)):
    if not API_KEY:
        # Skip authentication (DEVELOPMENT ONLY!)
        logger.warning("No API_KEY set - running without authentication")
        return api_key
    if api_key != API_KEY:
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key

# Models


class ClientRequest(BaseModel):
    name: str
    use_password: bool = False


class ClientResponse(BaseModel):
    name: str
    message: str
    config_path: Optional[str] = None


class BlockedClientsResponse(BaseModel):
    blocked_clients: List[str]


# Routes
@app.post("/clients", response_model=ClientResponse)
def create_client(client: ClientRequest, api_key: str = Depends(get_api_key)):
    """Generate a new OpenVPN client configuration"""
    logger.info(f"API request: create client {client.name}")
    try:
        config_path = service.generate_client(client.name, client.use_password)
        return ClientResponse(
            name=client.name,
            message=f"Client {client.name} created successfully",
            config_path=str(config_path)
        )
    except Exception as e:
        logger.error(f"Failed to create client {client.name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/clients/{name}/config")
def download_client_config(name: str, api_key: str = Depends(get_api_key)):
    """Download a client's .ovpn configuration file"""
    logger.info(f"API request: download config for {name}")
    config_path = service.OUTPUT_DIR / f"{name}.ovpn"
    if not config_path.exists():
        logger.error(f"Config file for {name} not found")
        raise HTTPException(status_code=404,
                            detail=f"Config for {name} not found")
    return FileResponse(
        path=config_path,
        filename=f"{name}.ovpn",
        media_type="application/octet-stream"
    )


@app.delete("/clients/{name}", response_model=ClientResponse)
def revoke_client(name: str, api_key: str = Depends(get_api_key)):
    """Revoke a client certificate"""
    logger.info(f"API request: revoke client {name}")
    try:
        service.revoke_client(name)
        return ClientResponse(
            name=name,
            message=f"Client {name} revoked successfully"
        )
    except Exception as e:
        logger.error(f"Failed to revoke client {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clients/{name}/suspend", response_model=ClientResponse)
def suspend_client(name: str, api_key: str = Depends(get_api_key)):
    """Temporarily suspend a client"""
    logger.info(f"API request: suspend client {name}")
    try:
        service.suspend_client(name)
        return ClientResponse(
            name=name,
            message=f"Client {name} suspended successfully"
        )
    except Exception as e:
        logger.error(f"Failed to suspend client {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clients/{name}/unsuspend", response_model=ClientResponse)
def unsuspend_client(name: str, api_key: str = Depends(get_api_key)):
    """Unsuspend a client"""
    logger.info(f"API request: unsuspend client {name}")
    try:
        service.unsuspend_client(name)
        return ClientResponse(
            name=name,
            message=f"Client {name} unsuspended successfully"
        )
    except Exception as e:
        logger.error(f"Failed to unsuspend client {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/clients/blocked", response_model=BlockedClientsResponse)
def list_blocked_clients(api_key: str = Depends(get_api_key)):
    """List all blocked clients"""
    logger.info("API request: list blocked clients")
    try:
        blocked = []
        if service.BLOCKLIST_PATH.exists():
            blocked = [line for line in
                       service.BLOCKLIST_PATH.read_text().splitlines() if line]
        return BlockedClientsResponse(blocked_clients=blocked)
    except Exception as e:
        logger.error(f"Failed to list blocked clients: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run the API server when executed directly
    port = int(os.environ.get("OVPN_API_PORT", 8000))
    host = os.environ.get("OVPN_API_HOST", "127.0.0.1")
    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

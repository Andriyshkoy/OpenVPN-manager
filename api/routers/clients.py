"""
Client management routes
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

import service
from api.dependencies import get_api_key
from api.schemas.client import (BlockedClientsResponse, ClientRequest,
                                ClientResponse)

logger = service.logger

router = APIRouter(
    prefix="/clients",
    tags=["clients"],
    dependencies=[Depends(get_api_key)]
)


@router.post("", response_model=ClientResponse)
def create_client(client: ClientRequest):
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


@router.get("/{name}/config")
def download_client_config(name: str):
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


@router.delete("/{name}", response_model=ClientResponse)
def revoke_client(name: str):
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


@router.post("/{name}/suspend", response_model=ClientResponse)
def suspend_client(name: str):
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


@router.post("/{name}/unsuspend", response_model=ClientResponse)
def unsuspend_client(name: str):
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


@router.get("/blocked", response_model=BlockedClientsResponse)
def list_blocked_clients():
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

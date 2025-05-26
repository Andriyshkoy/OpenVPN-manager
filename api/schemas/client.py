"""
Client-related Pydantic models
"""
from typing import List, Optional

from pydantic import BaseModel


class ClientRequest(BaseModel):
    name: str
    use_password: bool = False


class ClientResponse(BaseModel):
    name: str
    message: str
    config_path: Optional[str] = None


class BlockedClientsResponse(BaseModel):
    blocked_clients: List[str]

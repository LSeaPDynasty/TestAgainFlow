"""
DataStore schemas
"""
from typing import Dict, Optional
from pydantic import BaseModel, Field, RootModel


class DataStoreResponse(RootModel[Dict[str, Dict[str, Optional[str]]]]):
    """DataStore response for all environments"""
    root: Dict[str, Dict[str, Optional[str]]] = Field(..., description="Environment -> key-value pairs")


class DataStoreEnvUpdate(BaseModel):
    """DataStore environment update"""
    data: Dict[str, Optional[str]] = Field(..., description="Key-value pairs, null value to delete key")

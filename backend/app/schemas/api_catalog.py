"""Pydantic models for API Catalog endpoints."""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class APIEndpoint(BaseModel):
    """Schema for individual API endpoint."""
    path: Optional[str] = None
    method: str = "GET"
    description: Optional[str] = None
    parameters: Optional[List[Dict[str, Any]]] = None  # Changed to List
    response_format: Optional[str] = None
    authentication_required: bool = False
    # Additional fields from actual data
    name: Optional[str] = None
    endpointId: Optional[str] = None
    baseUrl: Optional[str] = None
    fullUrl: Optional[str] = None
    primaryUseCase: Optional[str] = None


class APICatalogResponse(BaseModel):
    """Schema for API catalog response."""
    id: str
    catalog_type: str
    name: str
    description: Optional[str] = None
    base_url: str
    endpoints_count: int
    last_updated: Optional[str] = None
    version: str = "1.0"
    metadata: Optional[Dict[str, Any]] = None
    endpoints: List[APIEndpoint] = Field(default_factory=list, description="Preview of endpoints")


class APICatalogMetrics(BaseModel):
    """Schema for API catalog metrics."""
    total_catalogs: int
    total_endpoints: int
    catalog_types: Dict[str, int]
    endpoint_methods: Dict[str, int]
    avg_endpoints_per_catalog: float


class APICatalogFilter(BaseModel):
    """Schema for API catalog filtering."""
    catalog_type: Optional[str] = None
    method: Optional[str] = None
    has_authentication: Optional[bool] = None
    min_endpoints: Optional[int] = None
    max_endpoints: Optional[int] = None
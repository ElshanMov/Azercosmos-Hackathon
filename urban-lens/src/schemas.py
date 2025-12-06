"""
Urban Infrastructure Lens - Pydantic Schemas (STAC Compatible)
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class GeometryType(str, Enum):
    POINT = "Point"
    LINESTRING = "LineString"
    POLYGON = "Polygon"
    MULTIPOINT = "MultiPoint"
    MULTILINESTRING = "MultiLineString"
    MULTIPOLYGON = "MultiPolygon"


class Geometry(BaseModel):
    type: GeometryType
    coordinates: Any


class Link(BaseModel):
    rel: str
    href: str
    type: Optional[str] = None
    title: Optional[str] = None


class Asset(BaseModel):
    href: str
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    roles: Optional[List[str]] = None


# STAC Item
class StacItemProperties(BaseModel):
    datetime: Optional[Union[datetime, str]] = None
    operator: Optional[str] = None
    operator_code: Optional[str] = None
    operator_color: Optional[str] = None
    infrastructure_type: Optional[str] = None
    type_code: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    depth_meters: Optional[float] = None
    material: Optional[str] = None
    building_type: Optional[str] = None
    floors: Optional[int] = None
    year_built: Optional[int] = None
    name: Optional[str] = None
    model_config = {"extra": "allow"}


class StacItem(BaseModel):
    type: str = "Feature"
    stac_version: str = "1.0.0"
    stac_extensions: List[str] = []
    id: str
    geometry: Geometry
    bbox: List[float]
    properties: StacItemProperties
    links: List[Link] = []
    assets: Dict[str, Asset] = {}
    collection: Optional[str] = None


# STAC Collection
class SpatialExtent(BaseModel):
    bbox: List[List[float]]


class TemporalExtent(BaseModel):
    interval: List[List[Optional[str]]]


class Extent(BaseModel):
    spatial: SpatialExtent
    temporal: TemporalExtent


class Provider(BaseModel):
    name: str
    description: Optional[str] = None
    roles: Optional[List[str]] = None
    url: Optional[str] = None


class StacCollection(BaseModel):
    type: str = "Collection"
    stac_version: str = "1.0.0"
    stac_extensions: List[str] = []
    id: str
    title: Optional[str] = None
    description: str
    keywords: List[str] = []
    license: str = "proprietary"
    providers: List[Provider] = []
    extent: Extent
    summaries: Dict[str, Any] = {}
    links: List[Link] = []


# STAC Catalog
class StacCatalog(BaseModel):
    type: str = "Catalog"
    stac_version: str = "1.0.0"
    id: str
    title: Optional[str] = None
    description: str
    links: List[Link] = []


# Feature Collection (for item search results)
class StacFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[StacItem]
    links: List[Link] = []
    numberMatched: Optional[int] = None
    numberReturned: Optional[int] = None
    context: Optional[Dict[str, Any]] = None


# Search Request
class SearchRequest(BaseModel):
    bbox: Optional[List[float]] = None
    datetime: Optional[str] = None
    collections: Optional[List[str]] = None
    ids: Optional[List[str]] = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    # Custom filters
    operator: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    infrastructure_type: Optional[str] = None
    building_type: Optional[str] = None


# API Responses
class OperatorResponse(BaseModel):
    id: str
    code: str
    name: str
    name_az: Optional[str]
    category: str
    color: str
    
    class Config:
        from_attributes = True


class InfrastructureTypeResponse(BaseModel):
    id: str
    code: str
    name: str
    name_az: Optional[str]
    category: str
    
    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_infrastructure: int
    total_buildings: int
    total_streets: int
    operators: List[Dict[str, Any]]
    categories: List[Dict[str, Any]]
    bbox: List[float]

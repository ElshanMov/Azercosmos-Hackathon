"""
Urban Infrastructure Lens - STAC Service Layer
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from geoalchemy2.functions import ST_AsGeoJSON, ST_Envelope, ST_Extent, ST_X, ST_Y
from geoalchemy2.shape import to_shape
import json

from .models import Infrastructure, Building, Street, Operator, InfrastructureType
from .schemas import (
    StacItem, StacCollection, StacFeatureCollection, StacCatalog,
    Geometry, Link, Extent, SpatialExtent, TemporalExtent,
    StacItemProperties, SearchRequest, StatsResponse
)
from .config import get_settings

settings = get_settings()


class StacService:
    """Service for STAC API operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.base_url = f"http://{settings.api_host}:{settings.api_port}/api/stac"
    
    def get_catalog(self) -> StacCatalog:
        """Get root STAC catalog"""
        return StacCatalog(
            id="urban-lens",
            title=settings.stac_api_title,
            description=settings.stac_api_description,
            links=[
                Link(rel="self", href=f"{self.base_url}/", type="application/json"),
                Link(rel="root", href=f"{self.base_url}/", type="application/json"),
                Link(rel="data", href=f"{self.base_url}/collections", type="application/json"),
                Link(rel="child", href=f"{self.base_url}/collections/infrastructure", type="application/json"),
                Link(rel="child", href=f"{self.base_url}/collections/buildings", type="application/json"),
                Link(rel="search", href=f"{self.base_url}/search", type="application/geo+json"),
            ]
        )
    
    def get_collections(self) -> List[StacCollection]:
        """Get all STAC collections"""
        return [
            self._get_infrastructure_collection(),
            self._get_buildings_collection()
        ]
    
    def get_collection(self, collection_id: str) -> Optional[StacCollection]:
        """Get a specific collection"""
        if collection_id == "infrastructure":
            return self._get_infrastructure_collection()
        elif collection_id == "buildings":
            return self._get_buildings_collection()
        return None
    
    def _get_infrastructure_collection(self) -> StacCollection:
        """Build infrastructure collection metadata"""
        # Get extent from data
        extent_result = self.db.query(
            func.min(func.ST_XMin(Infrastructure.geometry)).label("min_lon"),
            func.min(func.ST_YMin(Infrastructure.geometry)).label("min_lat"),
            func.max(func.ST_XMax(Infrastructure.geometry)).label("max_lon"),
            func.max(func.ST_YMax(Infrastructure.geometry)).label("max_lat"),
            func.min(Infrastructure.created_at).label("start_date"),
            func.max(Infrastructure.created_at).label("end_date")
        ).first()
        
        bbox = [
            extent_result.min_lon or settings.demo_bbox_min_lon,
            extent_result.min_lat or settings.demo_bbox_min_lat,
            extent_result.max_lon or settings.demo_bbox_max_lon,
            extent_result.max_lat or settings.demo_bbox_max_lat
        ]
        
        return StacCollection(
            id="infrastructure",
            title="Urban Infrastructure",
            description="Şəhər infrastrukturu - kabellər, borular, elektrik xətləri",
            keywords=["infrastructure", "cables", "pipes", "utilities", "baku"],
            license="proprietary",
            extent=Extent(
                spatial=SpatialExtent(bbox=[bbox]),
                temporal=TemporalExtent(interval=[[
                    extent_result.start_date.isoformat() if extent_result.start_date else None,
                    extent_result.end_date.isoformat() if extent_result.end_date else None
                ]])
            ),
            links=[
                Link(rel="self", href=f"{self.base_url}/collections/infrastructure"),
                Link(rel="parent", href=f"{self.base_url}/"),
                Link(rel="items", href=f"{self.base_url}/collections/infrastructure/items"),
            ]
        )
    
    def _get_buildings_collection(self) -> StacCollection:
        """Build buildings collection metadata"""
        extent_result = self.db.query(
            func.min(func.ST_XMin(Building.geometry)).label("min_lon"),
            func.min(func.ST_YMin(Building.geometry)).label("min_lat"),
            func.max(func.ST_XMax(Building.geometry)).label("max_lon"),
            func.max(func.ST_YMax(Building.geometry)).label("max_lat"),
            func.min(Building.created_at).label("start_date"),
            func.max(Building.created_at).label("end_date")
        ).first()
        
        bbox = [
            extent_result.min_lon or settings.demo_bbox_min_lon,
            extent_result.min_lat or settings.demo_bbox_min_lat,
            extent_result.max_lon or settings.demo_bbox_max_lon,
            extent_result.max_lat or settings.demo_bbox_max_lat
        ]
        
        return StacCollection(
            id="buildings",
            title="Buildings",
            description="Binalar və tikililər",
            keywords=["buildings", "structures", "real-estate", "baku"],
            license="proprietary",
            extent=Extent(
                spatial=SpatialExtent(bbox=[bbox]),
                temporal=TemporalExtent(interval=[[
                    extent_result.start_date.isoformat() if extent_result.start_date else None,
                    extent_result.end_date.isoformat() if extent_result.end_date else None
                ]])
            ),
            links=[
                Link(rel="self", href=f"{self.base_url}/collections/buildings"),
                Link(rel="parent", href=f"{self.base_url}/"),
                Link(rel="items", href=f"{self.base_url}/collections/buildings/items"),
            ]
        )
    
    def get_items(
        self, 
        collection_id: str, 
        limit: int = 10, 
        offset: int = 0,
        bbox: Optional[List[float]] = None,
        operator: Optional[str] = None,
        category: Optional[str] = None
    ) -> StacFeatureCollection:
        """Get items from a collection"""
        
        # Handle both "infrastructure" and "urban.infrastructure" formats
        clean_collection_id = collection_id.replace("urban.", "")
        
        if clean_collection_id == "infrastructure":
            return self._get_infrastructure_items(limit, offset, bbox, operator, category)
        elif clean_collection_id == "buildings":
            return self._get_building_items(limit, offset, bbox, operator)
        
        return StacFeatureCollection(features=[], links=[])
    
    def _get_infrastructure_items(
        self,
        limit: int,
        offset: int,
        bbox: Optional[List[float]] = None,
        operator: Optional[str] = None,
        category: Optional[str] = None
    ) -> StacFeatureCollection:
        """Get infrastructure items"""
        query = self.db.query(Infrastructure).join(
            Operator, Infrastructure.operator_id == Operator.id, isouter=True
        ).join(
            InfrastructureType, Infrastructure.type_id == InfrastructureType.id, isouter=True
        )
        
        # Apply filters
        if bbox and len(bbox) == 4:
            bbox_wkt = f"POLYGON(({bbox[0]} {bbox[1]}, {bbox[2]} {bbox[1]}, {bbox[2]} {bbox[3]}, {bbox[0]} {bbox[3]}, {bbox[0]} {bbox[1]}))"
            query = query.filter(func.ST_Intersects(
                Infrastructure.geometry,
                func.ST_GeomFromText(bbox_wkt, 4326)
            ))
        
        if operator:
            query = query.filter(Operator.code == operator)
        
        if category:
            query = query.filter(InfrastructureType.category == category)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        items = query.offset(offset).limit(limit).all()
        
        # Convert to STAC items
        features = []
        for item in items:
            features.append(self._infrastructure_to_stac_item(item))
        
        return StacFeatureCollection(
            features=features,
            links=[
                Link(rel="self", href=f"{self.base_url}/collections/infrastructure/items?limit={limit}&offset={offset}"),
                Link(rel="collection", href=f"{self.base_url}/collections/infrastructure"),
            ],
            numberMatched=total,
            numberReturned=len(features),
            context={"limit": limit, "offset": offset, "matched": total}
        )
    
    def _get_building_items(
        self,
        limit: int,
        offset: int,
        bbox: Optional[List[float]] = None,
        operator: Optional[str] = None
    ) -> StacFeatureCollection:
        """Get building items"""
        query = self.db.query(Building).join(
            Operator, Building.operator_id == Operator.id, isouter=True
        )
        
        if bbox and len(bbox) == 4:
            bbox_wkt = f"POLYGON(({bbox[0]} {bbox[1]}, {bbox[2]} {bbox[1]}, {bbox[2]} {bbox[3]}, {bbox[0]} {bbox[3]}, {bbox[0]} {bbox[1]}))"
            query = query.filter(func.ST_Intersects(
                Building.geometry,
                func.ST_GeomFromText(bbox_wkt, 4326)
            ))
        
        if operator:
            query = query.filter(Operator.code == operator)
        
        total = query.count()
        items = query.offset(offset).limit(limit).all()
        
        features = []
        for item in items:
            features.append(self._building_to_stac_item(item))
        
        return StacFeatureCollection(
            features=features,
            links=[
                Link(rel="self", href=f"{self.base_url}/collections/buildings/items?limit={limit}&offset={offset}"),
                Link(rel="collection", href=f"{self.base_url}/collections/buildings"),
            ],
            numberMatched=total,
            numberReturned=len(features)
        )
    
    def _infrastructure_to_stac_item(self, infra: Infrastructure) -> StacItem:
        """Convert Infrastructure model to STAC Item"""
        shape = to_shape(infra.geometry)
        geojson = json.loads(json.dumps(shape.__geo_interface__))
        bounds = shape.bounds
        
        operator_name = infra.operator.name if infra.operator else None
        operator_code = infra.operator.code if infra.operator else None
        operator_color = infra.operator.color if infra.operator else "#3388ff"
        type_name = infra.infra_type.name if infra.infra_type else None
        type_code = infra.infra_type.code if infra.infra_type else None
        category = infra.infra_type.category if infra.infra_type else None
        
        return StacItem(
            id=infra.stac_id,
            geometry=Geometry(type=geojson["type"], coordinates=geojson["coordinates"]),
            bbox=[bounds[0], bounds[1], bounds[2], bounds[3]],
            properties=StacItemProperties(
                datetime=infra.created_at.isoformat() if infra.created_at else None,
                operator=operator_name,
                operator_code=operator_code,
                operator_color=operator_color,
                infrastructure_type=type_name,
                type_code=type_code,
                category=category,
                status=infra.status,
                depth_meters=infra.depth_meters,
                material=infra.material
            ),
            collection="infrastructure",
            links=[
                Link(rel="self", href=f"{self.base_url}/collections/infrastructure/items/{infra.stac_id}"),
                Link(rel="collection", href=f"{self.base_url}/collections/infrastructure"),
            ]
        )
    
    def _building_to_stac_item(self, building: Building) -> StacItem:
        """Convert Building model to STAC Item"""
        shape = to_shape(building.geometry)
        geojson = json.loads(json.dumps(shape.__geo_interface__))
        bounds = shape.bounds
        
        operator_name = building.operator.name if building.operator else None
        operator_code = building.operator.code if building.operator else None
        operator_color = building.operator.color if building.operator else "#3388ff"
        
        return StacItem(
            id=building.stac_id,
            geometry=Geometry(type=geojson["type"], coordinates=geojson["coordinates"]),
            bbox=[bounds[0], bounds[1], bounds[2], bounds[3]],
            properties=StacItemProperties(
                datetime=building.created_at.isoformat() if building.created_at else None,
                operator=operator_name,
                operator_code=operator_code,
                operator_color=operator_color,
                building_type=building.building_type,
                floors=building.floors,
                year_built=building.year_built,
                name=building.name
            ),
            collection="buildings",
            links=[
                Link(rel="self", href=f"{self.base_url}/collections/buildings/items/{building.stac_id}"),
                Link(rel="collection", href=f"{self.base_url}/collections/buildings"),
            ]
        )
    
    def search(self, request: SearchRequest) -> StacFeatureCollection:
        """STAC search endpoint"""
        all_features = []
        
        collections = request.collections or ["infrastructure", "buildings"]
        
        for collection in collections:
            result = self.get_items(
                collection_id=collection,
                limit=request.limit,
                offset=request.offset,
                bbox=request.bbox,
                operator=request.operator,
                category=request.category
            )
            all_features.extend(result.features)
        
        return StacFeatureCollection(
            features=all_features[:request.limit],
            links=[Link(rel="self", href=f"{self.base_url}/search")],
            numberReturned=len(all_features[:request.limit])
        )
    
    def get_stats(self) -> StatsResponse:
        """Get statistics for dashboard"""
        infra_count = self.db.query(Infrastructure).count()
        building_count = self.db.query(Building).count()
        street_count = self.db.query(Street).count()
        
        # Operator stats
        operator_stats = self.db.query(
            Operator.code,
            Operator.name,
            Operator.color,
            func.count(Infrastructure.id).label("infra_count")
        ).outerjoin(Infrastructure).group_by(Operator.id).all()
        
        # Category stats
        category_stats = self.db.query(
            InfrastructureType.category,
            func.count(Infrastructure.id).label("count")
        ).join(Infrastructure).group_by(InfrastructureType.category).all()
        
        # Get overall bbox
        bbox_result = self.db.query(
            func.min(func.ST_XMin(Infrastructure.geometry)).label("min_lon"),
            func.min(func.ST_YMin(Infrastructure.geometry)).label("min_lat"),
            func.max(func.ST_XMax(Infrastructure.geometry)).label("max_lon"),
            func.max(func.ST_YMax(Infrastructure.geometry)).label("max_lat")
        ).first()
        
        return StatsResponse(
            total_infrastructure=infra_count,
            total_buildings=building_count,
            total_streets=street_count,
            operators=[
                {"code": op.code, "name": op.name, "color": op.color, "count": op.infra_count}
                for op in operator_stats
            ],
            categories=[
                {"category": cat.category, "count": cat.count}
                for cat in category_stats
            ],
            bbox=[
                bbox_result.min_lon or settings.demo_bbox_min_lon,
                bbox_result.min_lat or settings.demo_bbox_min_lat,
                bbox_result.max_lon or settings.demo_bbox_max_lon,
                bbox_result.max_lat or settings.demo_bbox_max_lat
            ]
        )
    
    def get_operators(self) -> List[Operator]:
        """Get all operators"""
        return self.db.query(Operator).all()
    
    def get_infrastructure_types(self) -> List[InfrastructureType]:
        """Get all infrastructure types"""
        return self.db.query(InfrastructureType).all()

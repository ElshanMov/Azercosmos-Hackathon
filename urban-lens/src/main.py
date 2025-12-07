"""
Urban Infrastructure Lens - FastAPI Application
STAC-compatible API for urban infrastructure data
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn

from .config import get_settings
from .database import get_db, check_db_connection, init_db
from .stac_service import StacService
from .operator_routes import router as operator_router
from .schemas import (
    StacCatalog, StacCollection, StacFeatureCollection, StacItem,
    SearchRequest, OperatorResponse, InfrastructureTypeResponse, StatsResponse
)

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.stac_api_title,
    description=settings.stac_api_description,
    version=settings.stac_api_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include operator router
app.include_router(operator_router)


# ============== Health & Info ==============

@app.get("/", tags=["Info"])
async def root():
    return {
        "title": settings.stac_api_title,
        "description": settings.stac_api_description,
        "version": settings.stac_api_version,
        "docs": "/api/docs",
        "stac": "/api/stac/"
    }


@app.get("/health", tags=["Info"])
async def health_check():
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected"
    }


# ============== STAC Core ==============

@app.get("/api/stac/", response_model=StacCatalog, tags=["STAC Core"])
async def get_catalog(db: Session = Depends(get_db)):
    service = StacService(db)
    return service.get_catalog()


@app.get("/api/stac/collections", response_model=List[StacCollection], tags=["STAC Core"])
async def get_collections(db: Session = Depends(get_db)):
    service = StacService(db)
    return service.get_collections()


@app.get("/api/stac/collections/{collection_id}", response_model=StacCollection, tags=["STAC Core"])
async def get_collection(collection_id: str, db: Session = Depends(get_db)):
    service = StacService(db)
    collection = service.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail=f"Collection '{collection_id}' not found")
    return collection


@app.get("/api/stac/collections/{collection_id}/items", response_model=StacFeatureCollection, tags=["STAC Core"])
async def get_items(
    collection_id: str,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    bbox: Optional[str] = Query(default=None),
    operator: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    service = StacService(db)
    bbox_list = None
    if bbox:
        try:
            bbox_list = [float(x) for x in bbox.split(",")]
            if len(bbox_list) != 4:
                raise ValueError("Invalid bbox")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid bbox format")
    
    return service.get_items(
        collection_id=collection_id,
        limit=limit,
        offset=offset,
        bbox=bbox_list,
        operator=operator,
        category=category
    )


# ============== STAC Search ==============

@app.post("/api/stac/search", response_model=StacFeatureCollection, tags=["STAC Search"])
async def search_post(request: SearchRequest, db: Session = Depends(get_db)):
    service = StacService(db)
    return service.search(request)


@app.get("/api/stac/search", response_model=StacFeatureCollection, tags=["STAC Search"])
async def search_get(
    bbox: Optional[str] = Query(default=None),
    collections: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    operator: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    service = StacService(db)
    bbox_list = None
    if bbox:
        try:
            bbox_list = [float(x) for x in bbox.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid bbox format")
    
    collections_list = collections.split(",") if collections else None
    
    request = SearchRequest(
        bbox=bbox_list,
        collections=collections_list,
        limit=limit,
        offset=offset,
        operator=operator,
        category=category
    )
    return service.search(request)


# ============== Custom Endpoints ==============

@app.get("/api/debug", tags=["Debug"])
async def debug_info(db: Session = Depends(get_db)):
    from .models import Infrastructure, Building, Street, Operator, InfrastructureType
    
    infra_count = db.query(Infrastructure).count()
    building_count = db.query(Building).count()
    street_count = db.query(Street).count()
    operator_count = db.query(Operator).count()
    type_count = db.query(InfrastructureType).count()
    
    sample_infra = db.query(Infrastructure).limit(3).all()
    sample_data = []
    for inf in sample_infra:
        sample_data.append({
            "stac_id": inf.stac_id,
            "operator_id": str(inf.operator_id) if inf.operator_id else None,
            "type_id": str(inf.type_id) if inf.type_id else None,
            "status": inf.status
        })
    
    return {
        "counts": {
            "infrastructure": infra_count,
            "buildings": building_count,
            "streets": street_count,
            "operators": operator_count,
            "infrastructure_types": type_count
        },
        "sample_infrastructure": sample_data
    }


@app.get("/api/stats", response_model=StatsResponse, tags=["Custom"])
async def get_stats(db: Session = Depends(get_db)):
    service = StacService(db)
    return service.get_stats()


@app.get("/api/operators", response_model=List[OperatorResponse], tags=["Custom"])
async def get_operators(db: Session = Depends(get_db)):
    service = StacService(db)
    operators = service.get_operators()
    return [OperatorResponse(
        id=str(op.id),
        code=op.code,
        name=op.name,
        name_az=op.name_az,
        category=op.category,
        color=op.color
    ) for op in operators]


@app.get("/api/infrastructure-types", response_model=List[InfrastructureTypeResponse], tags=["Custom"])
async def get_infrastructure_types(db: Session = Depends(get_db)):
    service = StacService(db)
    types = service.get_infrastructure_types()
    return [InfrastructureTypeResponse(
        id=str(t.id),
        code=t.code,
        name=t.name,
        name_az=t.name_az,
        category=t.category
    ) for t in types]


@app.get("/api/geojson/{collection_id}", tags=["GeoJSON"])
async def get_geojson(
    collection_id: str,
    bbox: Optional[str] = Query(default=None),
    operator: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db)
):
    service = StacService(db)
    bbox_list = None
    if bbox:
        try:
            bbox_list = [float(x) for x in bbox.split(",")]
        except ValueError:
            pass
    
    result = service.get_items(
        collection_id=collection_id,
        limit=limit,
        offset=0,
        bbox=bbox_list,
        operator=operator,
        category=category
    )
    
    features = []
    for item in result.features:
        features.append({
            "type": "Feature",
            "id": item.id,
            "geometry": {
                "type": item.geometry.type,
                "coordinates": item.geometry.coordinates
            },
            "properties": item.properties.model_dump(exclude_none=True)
        })
    
    return JSONResponse({
        "type": "FeatureCollection",
        "features": features
    })


@app.on_event("startup")
async def startup_event():
    print(f"\n🚀 {settings.stac_api_title} starting...")
    print(f"📍 API: http://{settings.api_host}:{settings.api_port}")
    print(f"📚 Docs: http://{settings.api_host}:{settings.api_port}/api/docs\n")


def run():
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug
    )


if __name__ == "__main__":
    run()
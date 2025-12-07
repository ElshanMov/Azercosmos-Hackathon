"""
Operator Portal API Routes - GeoJSON only, geometry-based routing
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db

router = APIRouter(prefix="/api/operator", tags=["operator"])

OPERATORS = {
    "shahersalma": {
        "id": "shahersalma",
        "name": "Şəhərsalma Komitəsi",
        "full_name": "Dövlət Şəhərsalma və Arxitektura Komitəsi",
        "category": "building",
        "color": "#8b5cf6",
        "password": "shahersalma2024"
    },
    "sutechizati": {
        "id": "sutechizati",
        "name": "Su Təchizatı",
        "full_name": "İri şəhərlərin birləşmiş su təchizatı",
        "category": "water",
        "color": "#06b6d4",
        "password": "sutechizati2024"
    },
    "aztelekom": {
        "id": "aztelekom",
        "name": "Aztelekom",
        "full_name": "Aztelekom MMC",
        "category": "telecom",
        "color": "#6366f1",
        "password": "aztelekom2024"
    },
}

class LoginRequest(BaseModel):
    operator_id: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    operator: Optional[dict] = None
    message: str

class ImportStats(BaseModel):
    total: int
    imported: int
    errors: int
    message: str
    first_error: Optional[str] = None
    buildings_count: int = 0
    infrastructure_count: int = 0

@router.post("/login", response_model=LoginResponse)
async def operator_login(request: LoginRequest):
    operator = OPERATORS.get(request.operator_id)
    if not operator:
        return LoginResponse(success=False, message="Operator tapılmadı")
    if operator["password"] != request.password:
        return LoginResponse(success=False, message="Şifrə yanlışdır")
    safe_operator = {k: v for k, v in operator.items() if k != "password"}
    return LoginResponse(success=True, operator=safe_operator, message="Uğurla daxil oldunuz")

@router.get("/list")
async def list_operators():
    return [
        {"id": k, "name": v["name"], "category": v["category"]} 
        for k, v in OPERATORS.items()
    ]

@router.get("/stats/{operator_id}")
async def get_operator_stats(operator_id: str, db: Session = Depends(get_db)):
    if operator_id not in OPERATORS:
        raise HTTPException(status_code=404, detail="Operator tapılmadı")
    
    result = db.execute(text("SELECT id FROM urban.operators WHERE code = :code"), {"code": operator_id}).fetchone()
    if not result:
        return {"operator": OPERATORS[operator_id]["name"], "infrastructure_count": 0, "building_count": 0, "last_import": None}
    
    op_uuid = result[0]
    infra_count = db.execute(text("SELECT COUNT(*) FROM urban.infrastructure WHERE operator_id = :op_id"), {"op_id": op_uuid}).scalar() or 0
    building_count = db.execute(text("SELECT COUNT(*) FROM urban.buildings WHERE operator_id = :op_id"), {"op_id": op_uuid}).scalar() or 0
    
    return {
        "operator": OPERATORS[operator_id]["name"],
        "infrastructure_count": infra_count,
        "building_count": building_count,
        "last_import": datetime.now(timezone.utc).isoformat()
    }

def get_or_create_operator(db: Session, operator_id: str):
    op_info = OPERATORS[operator_id]
    result = db.execute(text("SELECT id FROM urban.operators WHERE code = :code"), {"code": operator_id}).fetchone()
    if result:
        return result[0]
    
    op_uuid = uuid.uuid4()
    db.execute(
        text("""INSERT INTO urban.operators (id, code, name, name_az, category, color, created_at)
                VALUES (:id, :code, :name, :name_az, :category, :color, :created_at)"""),
        {"id": op_uuid, "code": operator_id, "name": op_info["full_name"], "name_az": op_info["full_name"],
         "category": op_info["category"], "color": op_info["color"], "created_at": datetime.now(timezone.utc)}
    )
    db.commit()
    return op_uuid

def get_or_create_infra_type(db: Session, type_code: str, category: str):
    result = db.execute(text("SELECT id FROM urban.infrastructure_types WHERE code = :code"), {"code": type_code}).fetchone()
    if result:
        return result[0]
    
    type_id = uuid.uuid4()
    try:
        db.execute(
            text("""INSERT INTO urban.infrastructure_types (id, code, name, name_az, category, created_at)
                    VALUES (:id, :code, :name, :name_az, :category, :created_at)"""),
            {"id": type_id, "code": type_code, "name": type_code, "name_az": type_code,
             "category": category, "created_at": datetime.now(timezone.utc)}
        )
        db.commit()
    except:
        db.rollback()
        result = db.execute(text("SELECT id FROM urban.infrastructure_types WHERE code = :code"), {"code": type_code}).fetchone()
        if result:
            return result[0]
    return type_id

@router.post("/import/{operator_id}", response_model=ImportStats)
async def import_geojson(
    operator_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Import GeoJSON - Polygon->buildings, LineString/Point->infrastructure"""
    if operator_id not in OPERATORS:
        raise HTTPException(status_code=404, detail="Operator tapılmadı")
    
    if not file.filename.endswith(('.geojson', '.json')):
        return ImportStats(total=0, imported=0, errors=1, 
                          message="Yalnız GeoJSON faylları qəbul edilir",
                          first_error="Fayl .geojson və ya .json uzantısı ilə olmalıdır")
    
    content = await file.read()
    try:
        geojson = json.loads(content.decode('utf-8'))
    except json.JSONDecodeError as e:
        return ImportStats(total=0, imported=0, errors=1, 
                          message="Yanlış GeoJSON formatı", first_error=str(e))
    
    if geojson.get("type") != "FeatureCollection":
        return ImportStats(total=0, imported=0, errors=1, 
                          message="FeatureCollection gözlənilir")
    
    features = geojson.get("features", [])
    if not features:
        return ImportStats(total=0, imported=0, errors=0, message="Fayl boşdur")
    
    op_uuid = get_or_create_operator(db, operator_id)
    op_info = OPERATORS[operator_id]
    
    imported = 0
    errors = 0
    first_error = None
    buildings_count = 0
    infrastructure_count = 0
    
    for i, feature in enumerate(features):
        try:
            geom = feature.get("geometry", {})
            props = feature.get("properties", {})
            
            if not geom or not geom.get("coordinates"):
                errors += 1
                if not first_error:
                    first_error = f"Feature {i}: geometry/coordinates yoxdur"
                continue
            
            geom_type = geom.get("type")
            coords = geom["coordinates"]
            item_id = uuid.uuid4()
            
            if geom_type == "Polygon":
                # POLYGON -> Buildings
                wkt_coords = ', '.join([f"{c[0]} {c[1]}" for c in coords[0]])
                wkt = f"POLYGON(({wkt_coords}))"
                stac_id = f"bldg-{str(item_id)[:8]}"
                
                floors = props.get("floors", props.get("building:levels"))
                if floors:
                    try:
                        floors = int(str(floors).split('.')[0])
                    except:
                        floors = None
                
                db.execute(
                    text("""INSERT INTO urban.buildings 
                            (id, stac_id, geometry, operator_id, name, building_type, floors, created_at)
                            VALUES (:id, :stac_id, ST_GeomFromText(:geom, 4326), :operator_id, :name, :building_type, :floors, :created_at)"""),
                    {
                        "id": item_id, "stac_id": stac_id, "geom": wkt,
                        "operator_id": op_uuid,
                        "name": props.get("name", props.get("name:az", "")) or "",
                        "building_type": props.get("building_type", props.get("building", "yes")) or "yes",
                        "floors": floors, 
                        "created_at": datetime.now(timezone.utc)
                    }
                )
                buildings_count += 1
                
            elif geom_type == "LineString":
                # LINESTRING -> Infrastructure
                wkt_coords = ', '.join([f"{c[0]} {c[1]}" for c in coords])
                wkt = f"LINESTRING({wkt_coords})"
                stac_id = f"infr-{str(item_id)[:8]}"
                
                infra_type = props.get("type", props.get("infrastructure_type", "pipe"))
                type_id = get_or_create_infra_type(db, str(infra_type), op_info["category"])
                
                depth = props.get("depth_meters", props.get("depth"))
                if depth:
                    try:
                        depth = float(depth)
                    except:
                        depth = None
                
                db.execute(
                    text("""INSERT INTO urban.infrastructure 
                            (id, stac_id, geometry, operator_id, type_id, status, depth_meters, material, created_at)
                            VALUES (:id, :stac_id, ST_GeomFromText(:geom, 4326), :operator_id, :type_id, :status, :depth, :material, :created_at)"""),
                    {
                        "id": item_id, "stac_id": stac_id, "geom": wkt, 
                        "operator_id": op_uuid, "type_id": type_id,
                        "status": props.get("status", "active"), 
                        "depth": depth,
                        "material": props.get("material"), 
                        "created_at": datetime.now(timezone.utc)
                    }
                )
                infrastructure_count += 1
                
            elif geom_type == "Point":
                # POINT -> Infrastructure
                wkt = f"POINT({coords[0]} {coords[1]})"
                stac_id = f"infr-{str(item_id)[:8]}"
                
                infra_type = props.get("type", props.get("infrastructure_type", "point"))
                type_id = get_or_create_infra_type(db, str(infra_type), op_info["category"])
                
                db.execute(
                    text("""INSERT INTO urban.infrastructure 
                            (id, stac_id, geometry, operator_id, type_id, status, depth_meters, material, created_at)
                            VALUES (:id, :stac_id, ST_GeomFromText(:geom, 4326), :operator_id, :type_id, :status, :depth, :material, :created_at)"""),
                    {
                        "id": item_id, "stac_id": stac_id, "geom": wkt, 
                        "operator_id": op_uuid, "type_id": type_id,
                        "status": props.get("status", "active"), 
                        "depth": props.get("depth_meters"),
                        "material": props.get("material"), 
                        "created_at": datetime.now(timezone.utc)
                    }
                )
                infrastructure_count += 1
                
            else:
                errors += 1
                if not first_error:
                    first_error = f"Feature {i}: Dəstəklənməyən geometry: {geom_type}"
                continue
            
            imported += 1
            if imported % 100 == 0:
                db.commit()
                
        except Exception as e:
            db.rollback()
            errors += 1
            if not first_error:
                first_error = f"Feature {i}: {str(e)[:150]}"
            continue
    
    db.commit()
    
    parts = []
    if buildings_count > 0:
        parts.append(f"{buildings_count} bina")
    if infrastructure_count > 0:
        parts.append(f"{infrastructure_count} infrastruktur")
    
    message = f"{' və '.join(parts)} uğurla import edildi" if parts else "Heç nə import edilmədi"
    
    return ImportStats(
        total=len(features), 
        imported=imported, 
        errors=errors,
        message=message,
        first_error=first_error,
        buildings_count=buildings_count,
        infrastructure_count=infrastructure_count
    )
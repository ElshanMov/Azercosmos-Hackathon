"""
Urban Infrastructure Lens - ETL Job
Generates realistic fake infrastructure data for Baku demo area
"""
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Tuple
import math

from sqlalchemy.orm import Session
from shapely.geometry import LineString, Polygon, Point, mapping
from shapely.ops import substring
from geoalchemy2.shape import from_shape

from .database import get_db_context, init_db
from .models import Operator, InfrastructureType, Infrastructure, Building, Street


# Demo area: Icheri Sheher / Fountain Square vicinity
DEMO_BOUNDS = {
    "min_lon": 49.8320,
    "min_lat": 40.3660,
    "max_lon": 49.8420,
    "max_lat": 40.3720
}

# Realistic street network for demo (simplified Baku center streets)
DEMO_STREETS = [
    {"name": "Neftçilər prospekti", "name_az": "Neftçilər prospekti", "type": "primary",
     "coords": [(49.8320, 40.3680), (49.8350, 40.3685), (49.8380, 40.3690), (49.8420, 40.3695)]},
    {"name": "Nizami küçəsi", "name_az": "Nizami küçəsi", "type": "secondary",
     "coords": [(49.8340, 40.3660), (49.8345, 40.3680), (49.8350, 40.3700), (49.8355, 40.3720)]},
    {"name": "Füzuli küçəsi", "name_az": "Füzuli küçəsi", "type": "secondary",
     "coords": [(49.8360, 40.3665), (49.8365, 40.3685), (49.8370, 40.3705), (49.8375, 40.3720)]},
    {"name": "Rəşid Behbudov küçəsi", "name_az": "Rəşid Behbudov küçəsi", "type": "tertiary",
     "coords": [(49.8380, 40.3660), (49.8382, 40.3680), (49.8385, 40.3700), (49.8388, 40.3720)]},
    {"name": "28 May küçəsi", "name_az": "28 May küçəsi", "type": "primary",
     "coords": [(49.8320, 40.3700), (49.8350, 40.3702), (49.8380, 40.3705), (49.8420, 40.3708)]},
    {"name": "İstiqlaliyyət küçəsi", "name_az": "İstiqlaliyyət küçəsi", "type": "secondary",
     "coords": [(49.8330, 40.3660), (49.8332, 40.3680), (49.8335, 40.3700), (49.8338, 40.3720)]},
    {"name": "Üzeyir Hacıbəyov küçəsi", "name_az": "Üzeyir Hacıbəyov küçəsi", "type": "tertiary",
     "coords": [(49.8400, 40.3665), (49.8402, 40.3685), (49.8405, 40.3705), (49.8408, 40.3720)]},
    {"name": "Şəhidlər Xiyabanı", "name_az": "Şəhidlər Xiyabanı", "type": "secondary",
     "coords": [(49.8320, 40.3715), (49.8350, 40.3714), (49.8380, 40.3713), (49.8420, 40.3712)]},
]

# Landmark buildings
DEMO_BUILDINGS = [
    {"name": "Azərbaycan Dövlət Filarmoniyası", "type": "cultural", "operator": "bna", "floors": 3},
    {"name": "Fountains Square", "type": "public_space", "operator": "bna", "floors": 1},
    {"name": "Nizami Museum", "type": "museum", "operator": "bna", "floors": 2},
    {"name": "JW Marriott Absheron", "type": "hotel", "operator": "private", "floors": 18},
    {"name": "Park Inn by Radisson", "type": "hotel", "operator": "private", "floors": 12},
    {"name": "Landmark Building", "type": "commercial", "operator": "private", "floors": 8},
    {"name": "Central Bank", "type": "government", "operator": "bna", "floors": 6},
    {"name": "Yaşıl Bazar", "type": "commercial", "operator": "municipal", "floors": 2},
    {"name": "Residential Block A", "type": "residential", "operator": "private", "floors": 9},
    {"name": "Residential Block B", "type": "residential", "operator": "private", "floors": 12},
    {"name": "Residential Block C", "type": "residential", "operator": "municipal", "floors": 5},
    {"name": "Business Center 28 May", "type": "commercial", "operator": "private", "floors": 10},
]

# Infrastructure assignment rules
INFRA_OPERATORS = {
    "fiber_optic": ["aztelekom", "baktelekom", "delta"],
    "copper_cable": ["aztelekom", "baktelekom"],
    "water_main": ["azersu"],
    "water_distribution": ["azersu"],
    "sewage": ["azersu"],
    "gas_main": ["azeriqaz"],
    "gas_distribution": ["azeriqaz"],
    "power_high": ["azerenerji"],
    "power_medium": ["azerenerji"],
    "power_low": ["azerenerji"],
}

MATERIALS = {
    "fiber_optic": ["fiber glass", "armored fiber"],
    "copper_cable": ["copper CAT5", "copper CAT6"],
    "water_main": ["ductile iron", "steel", "HDPE"],
    "water_distribution": ["PVC", "HDPE", "copper"],
    "sewage": ["concrete", "PVC", "clay"],
    "gas_main": ["steel", "polyethylene"],
    "gas_distribution": ["polyethylene", "steel"],
    "power_high": ["aluminum", "ACSR"],
    "power_medium": ["aluminum", "copper"],
    "power_low": ["copper", "aluminum"],
}

DEPTH_RANGES = {
    "fiber_optic": (0.6, 1.2),
    "copper_cable": (0.5, 1.0),
    "water_main": (1.5, 2.5),
    "water_distribution": (1.0, 1.8),
    "sewage": (2.0, 4.0),
    "gas_main": (1.2, 2.0),
    "gas_distribution": (0.8, 1.5),
    "power_high": (0.0, 0.0),  # overhead
    "power_medium": (0.0, 0.0),  # overhead
    "power_low": (0.5, 1.0),  # underground in city
}


def generate_stac_id(prefix: str) -> str:
    """Generate unique STAC ID"""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def random_point_in_bounds() -> Tuple[float, float]:
    """Generate random point within demo bounds"""
    lon = random.uniform(DEMO_BOUNDS["min_lon"], DEMO_BOUNDS["max_lon"])
    lat = random.uniform(DEMO_BOUNDS["min_lat"], DEMO_BOUNDS["max_lat"])
    return (lon, lat)


def offset_line(coords: List[Tuple[float, float]], offset: float) -> List[Tuple[float, float]]:
    """Offset line slightly for parallel infrastructure"""
    return [(lon + offset, lat + offset * 0.5) for lon, lat in coords]


def create_building_polygon(center: Tuple[float, float], width: float = 0.0003, height: float = 0.0002) -> Polygon:
    """Create building polygon from center point"""
    lon, lat = center
    half_w = width / 2
    half_h = height / 2
    return Polygon([
        (lon - half_w, lat - half_h),
        (lon + half_w, lat - half_h),
        (lon + half_w, lat + half_h),
        (lon - half_w, lat + half_h),
        (lon - half_w, lat - half_h)
    ])


def seed_operators(db: Session) -> dict:
    """Seed operators and return code->id mapping"""
    operators_data = [
        ("aztelekom", "Aztelekom LLC", "Aztelekom MMC", "telecom", "#e74c3c"),
        ("baktelekom", "Baktelecom LLC", "Baktelekom MMC", "telecom", "#9b59b6"),
        ("delta", "Delta Telecom", "Delta Telekom", "telecom", "#3498db"),
        ("azersu", "Azersu OJSC", "Azərsu ASC", "water", "#1abc9c"),
        ("azeriqaz", "Azerigaz PU", "Azəriqaz İB", "gas", "#f39c12"),
        ("azerenerji", "Azerenerji OJSC", "Azərenerji ASC", "electricity", "#e67e22"),
        ("bna", "Baku City Executive Power", "Bakı Şəhər İcra Hakimiyyəti", "government", "#2c3e50"),
        ("socar", "SOCAR", "SOCAR", "oil_gas", "#27ae60"),
        ("private", "Private Ownership", "Özəl Mülkiyyət", "private", "#7f8c8d"),
        ("municipal", "Municipal Property", "Bələdiyyə Mülkiyyəti", "government", "#34495e"),
    ]
    
    operator_map = {}
    for code, name, name_az, category, color in operators_data:
        existing = db.query(Operator).filter(Operator.code == code).first()
        if existing:
            operator_map[code] = existing.id
        else:
            op = Operator(code=code, name=name, name_az=name_az, category=category, color=color)
            db.add(op)
            db.flush()
            operator_map[code] = op.id
    
    return operator_map


def seed_infrastructure_types(db: Session) -> dict:
    """Seed infrastructure types and return code->id mapping"""
    types_data = [
        ("fiber_optic", "Fiber Optic Cable", "Fiber Optik Kabel", "telecom"),
        ("copper_cable", "Copper Cable", "Mis Kabel", "telecom"),
        ("water_main", "Water Main Pipe", "Əsas Su Borusu", "water"),
        ("water_distribution", "Water Distribution Pipe", "Su Paylanma Borusu", "water"),
        ("sewage", "Sewage Pipe", "Kanalizasiya Borusu", "water"),
        ("gas_main", "Gas Main Pipeline", "Əsas Qaz Xətti", "gas"),
        ("gas_distribution", "Gas Distribution Pipeline", "Qaz Paylanma Xətti", "gas"),
        ("power_high", "High Voltage Power Line", "Yüksək Gərginlik Xətti", "electricity"),
        ("power_medium", "Medium Voltage Power Line", "Orta Gərginlik Xətti", "electricity"),
        ("power_low", "Low Voltage Power Line", "Aşağı Gərginlik Xətti", "electricity"),
    ]
    
    type_map = {}
    for code, name, name_az, category in types_data:
        existing = db.query(InfrastructureType).filter(InfrastructureType.code == code).first()
        if existing:
            type_map[code] = existing.id
        else:
            it = InfrastructureType(code=code, name=name, name_az=name_az, category=category)
            db.add(it)
            db.flush()
            type_map[code] = it.id
    
    return type_map


def generate_streets(db: Session) -> List[LineString]:
    """Generate street geometries"""
    street_lines = []
    
    for street in DEMO_STREETS:
        existing = db.query(Street).filter(Street.name == street["name"]).first()
        if existing:
            continue
            
        line = LineString(street["coords"])
        street_lines.append(line)
        
        st = Street(
            osm_id=random.randint(100000, 999999),
            geometry=from_shape(line, srid=4326),
            name=street["name"],
            name_az=street["name_az"],
            highway_type=street["type"]
        )
        db.add(st)
    
    return street_lines


def generate_infrastructure(db: Session, streets: List[LineString], operator_map: dict, type_map: dict):
    """Generate infrastructure along streets"""
    
    infra_types_to_generate = [
        "fiber_optic", "copper_cable", 
        "water_main", "water_distribution", "sewage",
        "gas_main", "gas_distribution",
        "power_low"
    ]
    
    for street_idx, street_line in enumerate(streets):
        street_name = DEMO_STREETS[street_idx]["name"] if street_idx < len(DEMO_STREETS) else f"Street {street_idx}"
        
        for type_code in infra_types_to_generate:
            # Not all streets have all infrastructure
            if random.random() < 0.3:
                continue
            
            # Offset infrastructure from street centerline
            offset = random.uniform(-0.0001, 0.0001)
            coords = list(street_line.coords)
            offset_coords = offset_line(coords, offset)
            
            # Sometimes use only part of street
            if random.random() < 0.4:
                start_frac = random.uniform(0, 0.3)
                end_frac = random.uniform(0.7, 1.0)
                segment = substring(LineString(offset_coords), start_frac, end_frac, normalized=True)
            else:
                segment = LineString(offset_coords)
            
            # Select operator
            operator_code = random.choice(INFRA_OPERATORS[type_code])
            
            # Generate properties
            depth_range = DEPTH_RANGES[type_code]
            depth = round(random.uniform(*depth_range), 2) if depth_range[1] > 0 else None
            
            material = random.choice(MATERIALS[type_code])
            
            installed_date = datetime.now() - timedelta(days=random.randint(365, 365*20))
            
            infra = Infrastructure(
                stac_id=generate_stac_id("infra"),
                type_id=type_map[type_code],
                operator_id=operator_map[operator_code],
                geometry=from_shape(segment, srid=4326),
                status=random.choice(["active", "active", "active", "maintenance", "planned"]),
                installed_date=installed_date.date(),
                depth_meters=depth,
                material=material,
                properties={
                    "street": street_name,
                    "segment_length_m": round(segment.length * 111000, 1),  # approx meters
                }
            )
            db.add(infra)
    
    print(f"  ✓ Generated infrastructure along {len(streets)} streets")


def generate_buildings(db: Session, operator_map: dict):
    """Generate building polygons"""
    
    for idx, building in enumerate(DEMO_BUILDINGS):
        # Distribute buildings across demo area
        center = random_point_in_bounds()
        
        # Size based on type
        if building["type"] in ["hotel", "commercial"]:
            width = random.uniform(0.0004, 0.0006)
            height = random.uniform(0.0003, 0.0004)
        elif building["type"] == "public_space":
            width = random.uniform(0.0008, 0.0012)
            height = random.uniform(0.0006, 0.0008)
        else:
            width = random.uniform(0.0002, 0.0004)
            height = random.uniform(0.00015, 0.0003)
        
        polygon = create_building_polygon(center, width, height)
        
        bld = Building(
            stac_id=generate_stac_id("bldg"),
            osm_id=random.randint(100000, 999999),
            geometry=from_shape(polygon, srid=4326),
            operator_id=operator_map.get(building["operator"]),
            name=building["name"],
            name_az=building["name"],
            building_type=building["type"],
            floors=building["floors"],
            year_built=random.randint(1960, 2023),
            address={
                "city": "Bakı",
                "district": "Səbail",
                "street": random.choice([s["name"] for s in DEMO_STREETS])
            },
            properties={
                "source": "demo_generator",
                "confidence": 0.95
            }
        )
        db.add(bld)
    
    # Generate additional random residential buildings
    for i in range(20):
        center = random_point_in_bounds()
        polygon = create_building_polygon(center)
        
        bld = Building(
            stac_id=generate_stac_id("bldg"),
            osm_id=random.randint(100000, 999999),
            geometry=from_shape(polygon, srid=4326),
            operator_id=operator_map.get(random.choice(["private", "municipal"])),
            name=f"Yaşayış binası #{i+1}",
            name_az=f"Yaşayış binası #{i+1}",
            building_type="residential",
            floors=random.randint(5, 16),
            year_built=random.randint(1970, 2020),
            address={
                "city": "Bakı",
                "district": "Səbail"
            }
        )
        db.add(bld)
    
    print(f"  ✓ Generated {len(DEMO_BUILDINGS) + 20} buildings")


def run_etl():
    """Main ETL process"""
    print("\n" + "="*60)
    print("🚀 Urban Infrastructure Lens - ETL Job")
    print("="*60 + "\n")
    
    # Initialize database
    print("📦 Initializing database...")
    init_db()
    
    with get_db_context() as db:
        print("\n📊 Seeding reference data...")
        operator_map = seed_operators(db)
        print(f"  ✓ {len(operator_map)} operators")
        
        type_map = seed_infrastructure_types(db)
        print(f"  ✓ {len(type_map)} infrastructure types")
        
        print("\n🛣️  Generating streets...")
        streets = generate_streets(db)
        print(f"  ✓ {len(streets)} streets")
        
        print("\n🔌 Generating infrastructure...")
        generate_infrastructure(db, streets, operator_map, type_map)
        
        print("\n🏢 Generating buildings...")
        generate_buildings(db, operator_map)
        
        db.commit()
    
    print("\n" + "="*60)
    print("✅ ETL Job completed successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_etl()

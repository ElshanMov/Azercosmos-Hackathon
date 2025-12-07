"""
ETL script to load real Baku OSM data into the database
"""
import json
import uuid
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@db:5432/urban_lens")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def clear_existing_data():
    print("Clearing existing data...")
    session.execute(text("DELETE FROM urban.infrastructure"))
    session.execute(text("DELETE FROM urban.buildings"))
    session.commit()
    print("  Done")

def get_or_create_operator(code, name, category, color):
    result = session.execute(
        text("SELECT id FROM urban.operators WHERE code = :code"),
        {"code": code}
    ).fetchone()
    
    if result:
        return result[0]
    
    op_id = uuid.uuid4()
    try:
        session.execute(
            text("""
                INSERT INTO urban.operators (id, code, name, name_az, category, color, created_at)
                VALUES (:id, :code, :name, :name_az, :category, :color, :created_at)
            """),
            {
                "id": op_id, "code": code, "name": name, "name_az": name,
                "category": category, "color": color, "created_at": datetime.now(timezone.utc)
            }
        )
        session.commit()
    except:
        session.rollback()
    return op_id

def load_buildings():
    print("Loading buildings from baku_buildings.geojson...")
    
    with open('baku_buildings.geojson', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    operator_id = get_or_create_operator('baku_city', 'Bakı Şəhəri', 'municipal', '#3b82f6')
    
    count = 0
    errors = 0
    
    for feature in data['features']:
        geom = feature.get('geometry', {})
        props = feature.get('properties', {})
        
        if geom.get('type') != 'Polygon':
            continue
        
        try:
            coords = geom['coordinates'][0]
            if len(coords) < 4:
                continue
            
            wkt_coords = ', '.join([f"{c[0]} {c[1]}" for c in coords])
            wkt = f"POLYGON(({wkt_coords}))"
            
            building_id = uuid.uuid4()
            stac_id = f"building-{str(building_id)[:8]}"  # STAC ID əlavə edildi
            
            name = props.get('name', props.get('name:az', '')) or ''
            building_type = props.get('building', 'yes') or 'yes'
            
            session.execute(
                text("""
                    INSERT INTO urban.buildings 
                    (id, stac_id, geometry, operator_id, name, building_type, created_at)
                    VALUES 
                    (:id, :stac_id, ST_GeomFromText(:geom, 4326), :operator_id, :name, :building_type, :created_at)
                """),
                {
                    "id": building_id,
                    "stac_id": stac_id,
                    "geom": wkt,
                    "operator_id": operator_id,
                    "name": name,
                    "building_type": building_type,
                    "created_at": datetime.now(timezone.utc)
                }
            )
            count += 1
            
            if count % 100 == 0:
                session.commit()
                print(f"    {count} buildings loaded...")
                
        except Exception as e:
            session.rollback()
            errors += 1
            if errors == 1:
                print(f"  ERROR: {e}")
            continue
    
    session.commit()
    print(f"  Loaded {count} buildings ({errors} errors)")

def load_infrastructure():
    print("Loading infrastructure...")
    
    with open('baku_buildings.geojson', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    operators = {
        'water': get_or_create_operator('azersu', 'Azərsu ASC', 'water', '#06b6d4'),
        'gas': get_or_create_operator('azerigas', 'Azəriqaz ASC', 'gas', '#f59e0b'),
        'telecom': get_or_create_operator('aztelekom', 'Aztelekom MMC', 'telecom', '#6366f1'),
        'electricity': get_or_create_operator('azerishiq', 'Azərişıq ASC', 'electricity', '#ef4444'),
    }
    
    infra_types = {}
    for code, name, category in [
        ('water_main', 'Su xətti', 'water'),
        ('gas_pipe', 'Qaz borusu', 'gas'),
        ('fiber_optic', 'Fiber optik', 'telecom'),
        ('power_line', 'Elektrik xətti', 'electricity'),
    ]:
        result = session.execute(
            text("SELECT id FROM urban.infrastructure_types WHERE code = :code"),
            {"code": code}
        ).fetchone()
        
        if result:
            infra_types[code] = result[0]
        else:
            type_id = uuid.uuid4()
            try:
                session.execute(
                    text("""
                        INSERT INTO urban.infrastructure_types (id, code, name, name_az, category, created_at)
                        VALUES (:id, :code, :name, :name_az, :category, :created_at)
                    """),
                    {"id": type_id, "code": code, "name": name, "name_az": name,
                     "category": category, "created_at": datetime.now(timezone.utc)}
                )
                session.commit()
                infra_types[code] = type_id
            except:
                session.rollback()
    
    count = 0
    line_count = 0
    
    for feature in data['features']:
        geom = feature.get('geometry', {})
        
        if geom.get('type') != 'LineString':
            continue
        
        line_count += 1
        
        try:
            coords = geom['coordinates']
            if len(coords) < 2:
                continue
            
            wkt_coords = ', '.join([f"{c[0]} {c[1]}" for c in coords])
            wkt = f"LINESTRING({wkt_coords})"
            
            categories = ['water', 'gas', 'telecom', 'electricity']
            category = categories[line_count % 4]
            type_codes = ['water_main', 'gas_pipe', 'fiber_optic', 'power_line']
            type_code = type_codes[line_count % 4]
            
            infra_id = uuid.uuid4()
            stac_id = f"infra-{str(infra_id)[:8]}"  # STAC ID əlavə edildi
            
            session.execute(
                text("""
                    INSERT INTO urban.infrastructure 
                    (id, stac_id, geometry, operator_id, type_id, status, depth_meters, material, created_at)
                    VALUES 
                    (:id, :stac_id, ST_GeomFromText(:geom, 4326), :operator_id, :type_id, :status, :depth, :material, :created_at)
                """),
                {
                    "id": infra_id,
                    "stac_id": stac_id,
                    "geom": wkt,
                    "operator_id": operators[category],
                    "type_id": infra_types.get(type_code),
                    "status": "active",
                    "depth": round(0.5 + (line_count % 10) * 0.3, 1),
                    "material": ["Steel", "PVC", "Fiber", "Copper"][line_count % 4],
                    "created_at": datetime.now(timezone.utc)
                }
            )
            count += 1
            
            if count % 50 == 0:
                session.commit()
                print(f"    {count} infrastructure items loaded...")
                
        except Exception as e:
            session.rollback()
            if count == 0:
                print(f"  ERROR: {e}")
            continue
    
    session.commit()
    print(f"  Loaded {count} infrastructure items")

if __name__ == "__main__":
    print("=" * 50)
    print("Loading Real Baku OSM Data")
    print("=" * 50)
    
    clear_existing_data()
    load_buildings()
    load_infrastructure()
    
    print("=" * 50)
    print("Done!")
    print("=" * 50)
    
    session.close()
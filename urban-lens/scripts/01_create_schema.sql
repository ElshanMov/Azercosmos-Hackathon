-- Urban Infrastructure Lens - PostGIS Schema
-- Bakı şəhəri infrastruktur məlumatları üçün

-- Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Schema
CREATE SCHEMA IF NOT EXISTS urban;

-- Operators (Şirkətlər/Qurumlar)
CREATE TABLE urban.operators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    name_az VARCHAR(255),
    category VARCHAR(100) NOT NULL, -- telecom, water, gas, electricity, building
    color VARCHAR(7) DEFAULT '#3388ff', -- HEX color for map
    icon VARCHAR(100),
    contact_info JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Infrastructure Types
CREATE TABLE urban.infrastructure_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    name_az VARCHAR(255),
    category VARCHAR(100) NOT NULL,
    properties_schema JSONB, -- JSON schema for validation
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Main Infrastructure Layer (cables, pipes, etc.)
CREATE TABLE urban.infrastructure (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stac_id VARCHAR(255) UNIQUE NOT NULL, -- STAC Item ID
    type_id UUID REFERENCES urban.infrastructure_types(id),
    operator_id UUID REFERENCES urban.operators(id),
    geometry GEOMETRY(GEOMETRY, 4326) NOT NULL,
    properties JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active', -- active, maintenance, planned, decommissioned
    installed_date DATE,
    depth_meters DECIMAL(5,2), -- for underground infrastructure
    material VARCHAR(100),
    capacity VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Buildings Layer
CREATE TABLE urban.buildings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stac_id VARCHAR(255) UNIQUE NOT NULL,
    osm_id BIGINT,
    geometry GEOMETRY(POLYGON, 4326) NOT NULL,
    operator_id UUID REFERENCES urban.operators(id), -- owner/manager
    name VARCHAR(255),
    name_az VARCHAR(255),
    building_type VARCHAR(100), -- residential, commercial, government, etc.
    floors INTEGER,
    year_built INTEGER,
    address JSONB,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Streets/Roads (from OSM)
CREATE TABLE urban.streets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    osm_id BIGINT,
    geometry GEOMETRY(LINESTRING, 4326) NOT NULL,
    name VARCHAR(255),
    name_az VARCHAR(255),
    highway_type VARCHAR(100), -- primary, secondary, residential, etc.
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- STAC Collections metadata
CREATE TABLE urban.stac_collections (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    keywords TEXT[],
    license VARCHAR(100) DEFAULT 'proprietary',
    extent JSONB NOT NULL, -- spatial and temporal extent
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Spatial Indexes
CREATE INDEX idx_infrastructure_geometry ON urban.infrastructure USING GIST (geometry);
CREATE INDEX idx_buildings_geometry ON urban.buildings USING GIST (geometry);
CREATE INDEX idx_streets_geometry ON urban.streets USING GIST (geometry);

-- Regular Indexes
CREATE INDEX idx_infrastructure_operator ON urban.infrastructure(operator_id);
CREATE INDEX idx_infrastructure_type ON urban.infrastructure(type_id);
CREATE INDEX idx_infrastructure_status ON urban.infrastructure(status);
CREATE INDEX idx_buildings_operator ON urban.buildings(operator_id);
CREATE INDEX idx_buildings_type ON urban.buildings(building_type);

-- Insert Default Operators
INSERT INTO urban.operators (code, name, name_az, category, color) VALUES
    ('aztelekom', 'Aztelekom LLC', 'Aztelekom MMC', 'telecom', '#e74c3c'),
    ('baktelekom', 'Baktelecom LLC', 'Baktelekom MMC', 'telecom', '#9b59b6'),
    ('delta', 'Delta Telecom', 'Delta Telekom', 'telecom', '#3498db'),
    ('azersu', 'Azersu OJSC', 'Azərsu ASC', 'water', '#1abc9c'),
    ('azeriqaz', 'Azerigaz PU', 'Azəriqaz İB', 'gas', '#f39c12'),
    ('azerenerji', 'Azerenerji OJSC', 'Azərenerji ASC', 'electricity', '#e67e22'),
    ('bna', 'Baku City Executive Power', 'Bakı Nəqliyyat Agentliyi', 'government', '#2c3e50'),
    ('socar', 'SOCAR', 'SOCAR', 'oil_gas', '#27ae60'),
    ('private', 'Private Ownership', 'Özəl Mülkiyyət', 'private', '#7f8c8d'),
    ('municipal', 'Municipal Property', 'Bələdiyyə Mülkiyyəti', 'government', '#34495e');

-- Insert Infrastructure Types
INSERT INTO urban.infrastructure_types (code, name, name_az, category) VALUES
    ('fiber_optic', 'Fiber Optic Cable', 'Fiber Optik Kabel', 'telecom'),
    ('copper_cable', 'Copper Cable', 'Mis Kabel', 'telecom'),
    ('coaxial', 'Coaxial Cable', 'Koaksial Kabel', 'telecom'),
    ('water_main', 'Water Main Pipe', 'Əsas Su Borusu', 'water'),
    ('water_distribution', 'Water Distribution Pipe', 'Su Paylanma Borusu', 'water'),
    ('sewage', 'Sewage Pipe', 'Kanalizasiya Borusu', 'water'),
    ('gas_main', 'Gas Main Pipeline', 'Əsas Qaz Xətti', 'gas'),
    ('gas_distribution', 'Gas Distribution Pipeline', 'Qaz Paylanma Xətti', 'gas'),
    ('power_high', 'High Voltage Power Line', 'Yüksək Gərginlik Xətti', 'electricity'),
    ('power_medium', 'Medium Voltage Power Line', 'Orta Gərginlik Xətti', 'electricity'),
    ('power_low', 'Low Voltage Power Line', 'Aşağı Gərginlik Xətti', 'electricity'),
    ('heating', 'District Heating Pipe', 'Mərkəzi İstilik Borusu', 'heating');

-- View for STAC API
CREATE OR REPLACE VIEW urban.stac_items AS
SELECT 
    i.stac_id AS id,
    'Feature' AS type,
    ST_AsGeoJSON(i.geometry)::jsonb AS geometry,
    ST_XMin(i.geometry) AS bbox_minx,
    ST_YMin(i.geometry) AS bbox_miny,
    ST_XMax(i.geometry) AS bbox_maxx,
    ST_YMax(i.geometry) AS bbox_maxy,
    jsonb_build_object(
        'datetime', i.created_at,
        'operator', o.name,
        'operator_code', o.code,
        'operator_color', o.color,
        'infrastructure_type', t.name,
        'type_code', t.code,
        'category', t.category,
        'status', i.status,
        'depth_meters', i.depth_meters,
        'material', i.material
    ) || i.properties AS properties,
    ARRAY['infrastructure'] AS collection,
    jsonb_build_array(
        jsonb_build_object('rel', 'self', 'href', '/api/stac/items/' || i.stac_id),
        jsonb_build_object('rel', 'collection', 'href', '/api/stac/collections/infrastructure')
    ) AS links
FROM urban.infrastructure i
LEFT JOIN urban.operators o ON i.operator_id = o.id
LEFT JOIN urban.infrastructure_types t ON i.type_id = t.id

UNION ALL

SELECT 
    b.stac_id AS id,
    'Feature' AS type,
    ST_AsGeoJSON(b.geometry)::jsonb AS geometry,
    ST_XMin(b.geometry) AS bbox_minx,
    ST_YMin(b.geometry) AS bbox_miny,
    ST_XMax(b.geometry) AS bbox_maxx,
    ST_YMax(b.geometry) AS bbox_maxy,
    jsonb_build_object(
        'datetime', b.created_at,
        'operator', o.name,
        'operator_code', o.code,
        'operator_color', o.color,
        'building_type', b.building_type,
        'floors', b.floors,
        'year_built', b.year_built,
        'name', b.name
    ) || b.properties AS properties,
    ARRAY['buildings'] AS collection,
    jsonb_build_array(
        jsonb_build_object('rel', 'self', 'href', '/api/stac/items/' || b.stac_id),
        jsonb_build_object('rel', 'collection', 'href', '/api/stac/collections/buildings')
    ) AS links
FROM urban.buildings b
LEFT JOIN urban.operators o ON b.operator_id = o.id;

-- Function to generate STAC ID
CREATE OR REPLACE FUNCTION urban.generate_stac_id(prefix VARCHAR)
RETURNS VARCHAR AS $$
BEGIN
    RETURN prefix || '-' || REPLACE(uuid_generate_v4()::VARCHAR, '-', '');
END;
$$ LANGUAGE plpgsql;

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION urban.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_infrastructure_updated 
    BEFORE UPDATE ON urban.infrastructure 
    FOR EACH ROW EXECUTE FUNCTION urban.update_timestamp();

CREATE TRIGGER tr_buildings_updated 
    BEFORE UPDATE ON urban.buildings 
    FOR EACH ROW EXECUTE FUNCTION urban.update_timestamp();

CREATE TRIGGER tr_operators_updated 
    BEFORE UPDATE ON urban.operators 
    FOR EACH ROW EXECUTE FUNCTION urban.update_timestamp();

COMMENT ON SCHEMA urban IS 'Urban Infrastructure Lens - Şəhər infrastruktur məlumatları';
COMMENT ON TABLE urban.infrastructure IS 'Yeraltı və yerüstü infrastruktur (kabellər, borular)';
COMMENT ON TABLE urban.buildings IS 'Binalar və tikililər';
COMMENT ON TABLE urban.operators IS 'Şirkətlər və qurumlar';

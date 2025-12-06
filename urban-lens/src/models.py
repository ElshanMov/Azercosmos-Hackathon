"""
Urban Infrastructure Lens - Database Models
"""
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, 
    Text, Date, Boolean, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid

Base = declarative_base()


class Operator(Base):
    """Şirkətlər və qurumlar"""
    __tablename__ = "operators"
    __table_args__ = {"schema": "urban"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    name_az = Column(String(255))
    category = Column(String(100), nullable=False)
    color = Column(String(7), default="#3388ff")
    icon = Column(String(100))
    contact_info = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    infrastructure = relationship("Infrastructure", back_populates="operator")
    buildings = relationship("Building", back_populates="operator")


class InfrastructureType(Base):
    """İnfrastruktur növləri"""
    __tablename__ = "infrastructure_types"
    __table_args__ = {"schema": "urban"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    name_az = Column(String(255))
    category = Column(String(100), nullable=False)
    properties_schema = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    infrastructure = relationship("Infrastructure", back_populates="infra_type")


class Infrastructure(Base):
    """Yeraltı və yerüstü infrastruktur"""
    __tablename__ = "infrastructure"
    __table_args__ = {"schema": "urban"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stac_id = Column(String(255), unique=True, nullable=False)
    type_id = Column(UUID(as_uuid=True), ForeignKey("urban.infrastructure_types.id"))
    operator_id = Column(UUID(as_uuid=True), ForeignKey("urban.operators.id"))
    geometry = Column(Geometry("GEOMETRY", srid=4326), nullable=False)
    properties = Column(JSONB, default={})
    status = Column(String(50), default="active")
    installed_date = Column(Date)
    depth_meters = Column(Float)
    material = Column(String(100))
    capacity = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    operator = relationship("Operator", back_populates="infrastructure")
    infra_type = relationship("InfrastructureType", back_populates="infrastructure")


class Building(Base):
    """Binalar və tikililər"""
    __tablename__ = "buildings"
    __table_args__ = {"schema": "urban"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stac_id = Column(String(255), unique=True, nullable=False)
    osm_id = Column(Integer)
    geometry = Column(Geometry("POLYGON", srid=4326), nullable=False)
    operator_id = Column(UUID(as_uuid=True), ForeignKey("urban.operators.id"))
    name = Column(String(255))
    name_az = Column(String(255))
    building_type = Column(String(100))
    floors = Column(Integer)
    year_built = Column(Integer)
    address = Column(JSONB)
    properties = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    operator = relationship("Operator", back_populates="buildings")


class Street(Base):
    """Küçələr (OSM-dən)"""
    __tablename__ = "streets"
    __table_args__ = {"schema": "urban"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    osm_id = Column(Integer)
    geometry = Column(Geometry("LINESTRING", srid=4326), nullable=False)
    name = Column(String(255))
    name_az = Column(String(255))
    highway_type = Column(String(100))
    properties = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StacCollection(Base):
    """STAC Collections metadata"""
    __tablename__ = "stac_collections"
    __table_args__ = {"schema": "urban"}
    
    id = Column(String(255), primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    keywords = Column(ARRAY(Text))
    license = Column(String(100), default="proprietary")
    extent = Column(JSONB, nullable=False)
    properties = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

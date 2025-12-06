"""
Urban Infrastructure Lens - Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@db:5432/urban_lens"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "urban_lens"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = True
    stac_api_title: str = "Urban Infrastructure Lens STAC API"
    stac_api_description: str = "Baku City Infrastructure Catalog"
    stac_api_version: str = "1.0.0"
    default_center_lat: float = 40.4093
    default_center_lon: float = 49.8671
    default_zoom: int = 14
    demo_bbox_min_lon: float = 49.8300
    demo_bbox_min_lat: float = 40.3650
    demo_bbox_max_lon: float = 49.8550
    demo_bbox_max_lat: float = 40.3750

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
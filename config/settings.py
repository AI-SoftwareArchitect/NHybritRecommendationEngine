from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from dotenv import load_dotenv

# Explicitly load .env file before Settings initialization
load_dotenv(override=True)

class Settings(BaseSettings):
    # Neo4j Settings
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # External API Settings
    external_api_base_url: str = "https://api.muhammetklnc.com.tr"
    external_api_email: str = "210129049@ogr.atu.edu.tr"
    external_api_password: str = "Test1907**"
    
    # Scheduler Settings
    sync_interval_hours: int = 1
    
    # A/B Test Settings
    ab_test_counts_path: str = "data/ab_test_counts.json"
    ab_test_data_path: str = "data/likes_data.json"
    ab_test_threshold_date: str = "2024-01-01T00:00:00"
    
    # Model Settings
    model_checkpoint_path: str = "models/gnn_checkpoint.pt"
    
    model_config = SettingsConfigDict(
        env_file = ".env",
        extra = "ignore",
        case_sensitive = False
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

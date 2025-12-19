from neo4j import GraphDatabase
from config.settings import get_settings
from typing import Optional

class Neo4jClient:
    _instance: Optional['Neo4jClient'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            settings = get_settings()
            cls._instance.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
        return cls._instance
    
    def get_session(self):
        return self.driver.session()
    
    def close(self):
        if self.driver:
            self.driver.close()
    
    def verify_connectivity(self) -> bool:
        try:
            with self.get_session() as session:
                result = session.run("RETURN 1 AS num")
                return result.single()["num"] == 1
        except Exception:
            return False

def get_neo4j_client() -> Neo4jClient:
    return Neo4jClient()
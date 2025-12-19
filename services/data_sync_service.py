"""
Data Sync Service
Handles synchronization of external API data to Neo4j graph database.
"""
from typing import Optional
from services.external_api_service import get_external_api_service
from services.graph_service import get_graph_service


class DataSyncService:
    """Service for syncing external API data to Neo4j."""
    
    _instance: Optional['DataSyncService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.external_api = get_external_api_service()
        self.graph_service = get_graph_service()
        self._initialized = True
    
    def sync_notes(self) -> int:
        """
        Fetch all notes from external API and sync to Neo4j.
        Returns the number of notes synced.
        """
        print("Starting note synchronization...")
        
        # Fetch notes from external API
        notes = self.external_api.get_all_notes()
        
        if not notes:
            print("✗ No notes to sync")
            return 0
        
        synced_count = 0
        users_synced = set()
        
        for note in notes:
            try:
                # Upsert the note
                if self.graph_service.upsert_note(note):
                    synced_count += 1
                
                # Upsert the creator user
                creator = note.get("creatorAppUser", {})
                if creator and creator.get("id"):
                    user_id = creator.get("id")
                    
                    if user_id not in users_synced:
                        self.graph_service.upsert_user(creator)
                        users_synced.add(user_id)
                    
                    # Create relationship
                    self.graph_service.create_user_created_note(
                        user_id=user_id,
                        note_id=note.get("id")
                    )
            
            except Exception as e:
                print(f"✗ Error syncing note {note.get('id')}: {e}")
                continue
        
        print(f"✓ Synced {synced_count} notes and {len(users_synced)} users to Neo4j")
        return synced_count
    
    def run_scheduled_sync(self):
        """
        Scheduled sync task for APScheduler.
        """
        print("\n" + "="*50)
        print("Running scheduled data sync...")
        print("="*50)
        
        try:
            count = self.sync_notes()
            print(f"Scheduled sync completed: {count} notes")
        except Exception as e:
            print(f"✗ Scheduled sync failed: {e}")


# Singleton accessor
_service_instance: Optional[DataSyncService] = None


def get_data_sync_service() -> DataSyncService:
    """Get or create the data sync service singleton."""
    global _service_instance
    if _service_instance is None:
        _service_instance = DataSyncService()
    return _service_instance

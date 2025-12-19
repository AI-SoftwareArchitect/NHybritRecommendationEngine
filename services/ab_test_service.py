import json
import os
from datetime import datetime
from pathlib import Path
from models.schemas import ABTestGroup, LikeRecord, ABTestCounts
from config.settings import get_settings

class ABTestService:
    def __init__(self):
        self.settings = get_settings()
        self._ensure_data_directory()
        self._initialize_counts_file()
    
    def _ensure_data_directory(self):
        Path("data").mkdir(exist_ok=True)
    
    def _initialize_counts_file(self):
        if not os.path.exists(self.settings.ab_test_counts_path):
            initial_data = {
                "ab_test_a_like_count": 0,
                "ab_test_b_like_count": 0,
                "last_updated": datetime.now().isoformat()
            }
            with open(self.settings.ab_test_counts_path, 'w') as f:
                json.dump(initial_data, f, indent=2)
    
    def record_like(self, user_id: str, note_id: str, ab_group: ABTestGroup):
        # Record individual like
        like_record = LikeRecord(
            user_id=user_id,
            note_id=note_id,
            ab_group=ab_group,
            timestamp=datetime.now(),
            liked_note_id=note_id
        )
        
        # Append to likes file
        likes_data = self._load_likes_data()
        likes_data.append(like_record.model_dump(mode='json'))
        self._save_likes_data(likes_data)
        
        # Update counts
        self._increment_count(ab_group)
    
    def _load_likes_data(self) -> list:
        if not os.path.exists(self.settings.ab_test_data_path):
            return []
        
        with open(self.settings.ab_test_data_path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    
    def _save_likes_data(self, data: list):
        with open(self.settings.ab_test_data_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _increment_count(self, ab_group: ABTestGroup):
        counts = self.get_counts()
        
        if ab_group == ABTestGroup.A:
            counts["ab_test_a_like_count"] += 1
        else:
            counts["ab_test_b_like_count"] += 1
        
        counts["last_updated"] = datetime.now().isoformat()
        
        with open(self.settings.ab_test_counts_path, 'w') as f:
            json.dump(counts, f, indent=2)
    
    def get_counts(self) -> dict:
        with open(self.settings.ab_test_counts_path, 'r') as f:
            return json.load(f)
    
    def get_winning_group(self) -> ABTestGroup:
        counts = self.get_counts()
        threshold_date = datetime.fromisoformat(self.settings.ab_test_threshold_date)
        
        if datetime.now() < threshold_date:
            return None
        
        if counts["ab_test_a_like_count"] > counts["ab_test_b_like_count"]:
            return ABTestGroup.A
        else:
            return ABTestGroup.B

def get_ab_test_service() -> ABTestService:
    return ABTestService()
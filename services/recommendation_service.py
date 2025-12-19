"""
Recommendation Service
Implements hybrid recommendation algorithm combining:
- GAT (Graph Attention Network) scores
- Traditional algorithm (popularity: views, downloads, rating)
- Recency score (exponential decay based on note age)
- Random factor (exploration)
"""
import random
from typing import List, Dict
from datetime import datetime, timezone
from services.graph_service import get_graph_service
from services.gnn_service import get_gnn_service
from models.schemas import ABTestGroup


class RecommendationService:
    """
    Hybrid recommendation service combining multiple scoring methods.
    
    Final Score = (0.35 × GAT) + (0.35 × Traditional) + (0.15 × Recency) + (0.15 × Random)
    """
    
    def __init__(self):
        self.graph_service = get_graph_service()
        self.gnn_service = get_gnn_service()
        
        # Weights for hybrid scoring
        self.gat_weight = 0.35
        self.traditional_weight = 0.35
        self.recency_weight = 0.15
        self.random_weight = 0.15
    
    def get_recommendations(self, user_id: str, ab_group: ABTestGroup = None, limit: int = 10) -> List[str]:
        """
        Get personalized note recommendations for a user.
        Returns list of note_ids only.
        """
        # Get all notes with features
        all_notes = self.graph_service.get_all_notes_with_features()
        
        if not all_notes:
            return []
        
        # Get graph-based candidates (personalized if user has history)
        graph_candidates = self.graph_service.personalized_pagerank(user_id, limit=limit*3)
        graph_scores = {c["note_id"]: c["graph_score"] for c in graph_candidates}
        
        # Get GNN scores
        note_ids = [note["note_id"] for note in all_notes if note["note_id"]]
        gnn_scores = self.gnn_service.predict_scores(note_ids) if note_ids else {}
        
        # Calculate traditional and recency scores
        traditional_scores = self._calculate_traditional_scores(all_notes)
        recency_scores = self._calculate_recency_scores(all_notes)
        
        # Combine all scores
        final_scores = []
        for note in all_notes:
            note_id = note.get("note_id")
            if not note_id:
                continue
            
            # Get individual scores (normalize to 0-1 range)
            gat_score = gnn_scores.get(note_id, 0.5)
            trad_score = traditional_scores.get(note_id, 0.0)
            rec_score = recency_scores.get(note_id, 0.5)
            rand_score = random.uniform(0, 1)
            
            # Add boost from graph-based personalization
            graph_boost = min(graph_scores.get(note_id, 0) / 10.0, 0.3)
            
            # Calculate final score
            final_score = (
                self.gat_weight * gat_score +
                self.traditional_weight * trad_score +
                self.recency_weight * rec_score +
                self.random_weight * rand_score +
                graph_boost  # Additional personalization boost
            )
            
            final_scores.append({
                "note_id": note_id,
                "score": final_score
            })
        
        # Sort by final score and return top N note_ids
        final_scores.sort(key=lambda x: x["score"], reverse=True)
        return [item["note_id"] for item in final_scores[:limit]]
    
    def get_default_recommendations(self, user_id: str, limit: int = 10) -> List[str]:
        """
        Get default recommendations without A/B testing.
        Returns list of note_ids only.
        """
        return self.get_recommendations(user_id, ab_group=None, limit=limit)
    
    def _calculate_traditional_scores(self, notes: List[Dict]) -> Dict[str, float]:
        """
        Calculate traditional popularity scores.
        Score = 0.3 × normalized_views + 0.3 × normalized_downloads + 0.4 × normalized_rating
        """
        if not notes:
            return {}
        
        # Find max values for normalization
        max_views = max(note.get("view_count") or 0 for note in notes) or 1
        max_downloads = max(note.get("download_count") or 0 for note in notes) or 1
        max_rating = 5.0  # Assuming 5-star rating system
        
        scores = {}
        for note in notes:
            note_id = note.get("note_id")
            if not note_id:
                continue
            
            # Normalize values
            norm_views = (note.get("view_count") or 0) / max_views
            norm_downloads = (note.get("download_count") or 0) / max_downloads
            norm_rating = (note.get("rating") or 0) / max_rating
            
            # Weighted combination
            score = 0.3 * norm_views + 0.3 * norm_downloads + 0.4 * norm_rating
            scores[note_id] = score
        
        return scores
    
    def _calculate_recency_scores(self, notes: List[Dict]) -> Dict[str, float]:
        """
        Calculate recency scores with exponential decay.
        Newer notes get higher scores.
        """
        if not notes:
            return {}
        
        now = datetime.now(timezone.utc)
        scores = {}
        
        for note in notes:
            note_id = note.get("note_id")
            if not note_id:
                continue
            
            created_date_str = note.get("created_date", "")
            
            try:
                # Parse the date string
                if created_date_str:
                    # Handle different date formats
                    if "T" in str(created_date_str):
                        created_date = datetime.fromisoformat(str(created_date_str).replace("Z", "+00:00"))
                    else:
                        created_date = datetime.strptime(str(created_date_str), "%Y-%m-%d")
                        created_date = created_date.replace(tzinfo=timezone.utc)
                    
                    # Calculate days since creation
                    if created_date.tzinfo is None:
                        created_date = created_date.replace(tzinfo=timezone.utc)
                    
                    days_old = (now - created_date).days
                    
                    # Exponential decay: e^(-days/30) gives half-life of ~21 days
                    import math
                    score = math.exp(-days_old / 30.0)
                else:
                    score = 0.5  # Default for unknown dates
            except Exception:
                score = 0.5  # Default on parse error
            
            scores[note_id] = score
        
        return scores


def get_recommendation_service() -> RecommendationService:
    return RecommendationService()
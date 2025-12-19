from typing import List, Dict
from services.graph_service import get_graph_service
from services.gnn_service import get_gnn_service
from models.schemas import ABTestGroup

class RecommendationService:
    def __init__(self):
        self.graph_service = get_graph_service()
        self.gnn_service = get_gnn_service()
    
    def get_recommendations(self, user_id: str, ab_group: ABTestGroup = None, limit: int = 10) -> List[Dict]:
        """
        Get recommendations by combining graph and GNN scores
        Strategy Pattern: different ranking for A/B groups
        """
        # Get graph-based candidates
        graph_candidates = self.graph_service.personalized_pagerank(user_id, limit=limit*2)
        
        if not graph_candidates:
            return []
        
        # Get GNN scores
        note_ids = [c["note_id"] for c in graph_candidates]
        gnn_scores = self.gnn_service.predict_scores(note_ids)
        
        # Combine scores based on A/B group
        final_scores = []
        for candidate in graph_candidates:
            note_id = candidate["note_id"]
            graph_score = candidate["graph_score"]
            gnn_score = gnn_scores.get(note_id, 0.0)
            
            # Different ranking weights for A/B test
            if ab_group == ABTestGroup.A:
                final_score = 0.4 * graph_score + 0.6 * gnn_score
                algorithm = "Graph(0.4) + GNN(0.6)"
            else:
                # Group B: reverse weights for comparison
                final_score = 0.6 * graph_score + 0.4 * gnn_score
                algorithm = "Graph(0.6) + GNN(0.4)"
            
            final_scores.append({
                "note_id": note_id,
                "final_score": final_score,
                "graph_score": graph_score,
                "gnn_score": gnn_score,
                "algorithm": algorithm
            })
        
        # Sort and return top N
        final_scores.sort(key=lambda x: x["final_score"], reverse=True)
        return final_scores[:limit]
    
    def get_default_recommendations(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recommendations without A/B testing"""
        graph_candidates = self.graph_service.personalized_pagerank(user_id, limit=limit*2)
        
        if not graph_candidates:
            return []
        
        note_ids = [c["note_id"] for c in graph_candidates]
        gnn_scores = self.gnn_service.predict_scores(note_ids)
        
        final_scores = []
        for candidate in graph_candidates:
            note_id = candidate["note_id"]
            graph_score = candidate["graph_score"]
            gnn_score = gnn_scores.get(note_id, 0.0)
            
            # Default ranking
            final_score = 0.4 * graph_score + 0.6 * gnn_score
            
            final_scores.append({
                "note_id": note_id,
                "final_score": final_score,
                "graph_score": graph_score,
                "gnn_score": gnn_score,
                "algorithm": "Default: Graph(0.4) + GNN(0.6)"
            })
        
        final_scores.sort(key=lambda x: x["final_score"], reverse=True)
        return final_scores[:limit]

def get_recommendation_service() -> RecommendationService:
    return RecommendationService()
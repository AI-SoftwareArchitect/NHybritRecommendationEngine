from database.neo4j_client import get_neo4j_client
from typing import List, Dict

class GraphService:
    def __init__(self):
        self.client = get_neo4j_client()
    
    def personalized_pagerank(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Run Personalized PageRank from user's liked notes
        """
        with self.client.get_session() as session:
            # First check if user has liked any notes
            check_query = """
            MATCH (u:User {user_id: $user_id})-[:LIKED]->(n:Note)
            RETURN count(n) as liked_count
            """
            result = session.run(check_query, user_id=user_id)
            liked_count = result.single()["liked_count"]
            
            if liked_count == 0:
                # Return popular notes if user hasn't liked anything
                return self._get_popular_notes(session, limit)
            
            # PPR query: traverse from user's liked notes through tags/categories
            ppr_query = """
            MATCH (u:User {user_id: $user_id})-[:LIKED]->(liked:Note)
            MATCH (liked)-[:HAS_TAG]->(t:Tag)<-[:HAS_TAG]-(candidate:Note)
            WHERE NOT (u)-[:LIKED]->(candidate)
            WITH candidate, count(DISTINCT t) as tag_score, candidate.like_count as popularity
            
            OPTIONAL MATCH (candidate)-[:IN_CATEGORY]->(c:Category)<-[:IN_CATEGORY]-(liked2:Note)<-[:LIKED]-(u)
            WITH candidate, tag_score, popularity, count(DISTINCT c) as category_score
            
            WITH candidate, 
                 (tag_score * 0.5 + category_score * 0.3 + popularity * 0.2) as graph_score
            
            RETURN candidate.note_id as note_id, graph_score
            ORDER BY graph_score DESC
            LIMIT $limit
            """
            
            result = session.run(ppr_query, user_id=user_id, limit=limit)
            
            recommendations = []
            for record in result:
                recommendations.append({
                    "note_id": record["note_id"],
                    "graph_score": float(record["graph_score"])
                })
            
            return recommendations
    
    def _get_popular_notes(self, session, limit: int) -> List[Dict]:
        """Fallback: return popular notes"""
        query = """
        MATCH (n:Note)
        RETURN n.note_id as note_id, n.like_count as graph_score
        ORDER BY graph_score DESC
        LIMIT $limit
        """
        result = session.run(query, limit=limit)
        
        return [
            {"note_id": record["note_id"], "graph_score": float(record["graph_score"])}
            for record in result
        ]
    
    def get_note_features(self, note_id: str) -> Dict:
        """Get node features for GNN"""
        with self.client.get_session() as session:
            query = """
            MATCH (n:Note {note_id: $note_id})
            OPTIONAL MATCH (n)-[:HAS_TAG]->(t:Tag)
            OPTIONAL MATCH (n)-[:IN_CATEGORY]->(c:Category)
            RETURN n.like_count as like_count,
                   count(DISTINCT t) as tag_count,
                   collect(DISTINCT c.name)[0] as category
            """
            result = session.run(query, note_id=note_id)
            record = result.single()
            
            return {
                "like_count": record["like_count"] or 0,
                "tag_count": record["tag_count"] or 0,
                "category": record["category"] or "unknown"
            }

def get_graph_service() -> GraphService:
    return GraphService()
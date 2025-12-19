from database.neo4j_client import get_neo4j_client
from typing import List, Dict, Any
from datetime import datetime


class GraphService:
    def __init__(self):
        self.client = get_neo4j_client()
    
    def upsert_note(self, note_data: Dict[str, Any]) -> bool:
        """
        Create or update a Note node in Neo4j.
        """
        try:
            with self.client.get_session() as session:
                query = """
                MERGE (n:Note {note_id: $note_id})
                SET n.title = $title,
                    n.short_description = $short_description,
                    n.rating = $rating,
                    n.download_count = $download_count,
                    n.view_count = $view_count,
                    n.comment_count = $comment_count,
                    n.cover_image_url = $cover_image_url,
                    n.created_date = $created_date,
                    n.is_popular = $is_popular,
                    n.like_count = COALESCE(n.like_count, 0),
                    n.updated_at = datetime()
                RETURN n.note_id as note_id
                """
                result = session.run(
                    query,
                    note_id=note_data.get("id"),
                    title=note_data.get("title", ""),
                    short_description=note_data.get("shortDescription", ""),
                    rating=note_data.get("rating", 0),
                    download_count=note_data.get("downloadCount", 0),
                    view_count=note_data.get("viewCount", 0),
                    comment_count=note_data.get("commentCount", 0),
                    cover_image_url=note_data.get("coverImageUrl", ""),
                    created_date=note_data.get("createdDate", ""),
                    is_popular=note_data.get("isPopular", False)
                )
                return result.single() is not None
        except Exception as e:
            print(f"Error upserting note: {e}")
            return False
    
    def upsert_user(self, user_data: Dict[str, Any]) -> bool:
        """
        Create or update a User node in Neo4j.
        """
        try:
            with self.client.get_session() as session:
                query = """
                MERGE (u:User {user_id: $user_id})
                SET u.full_name = $full_name,
                    u.first_name = $first_name,
                    u.last_name = $last_name,
                    u.username = $username,
                    u.profile_image_url = $profile_image_url,
                    u.updated_at = datetime()
                RETURN u.user_id as user_id
                """
                result = session.run(
                    query,
                    user_id=user_data.get("id"),
                    full_name=user_data.get("fullName", ""),
                    first_name=user_data.get("firstName", ""),
                    last_name=user_data.get("lastName", ""),
                    username=user_data.get("userName", ""),
                    profile_image_url=user_data.get("profileImageUrl", "")
                )
                return result.single() is not None
        except Exception as e:
            print(f"Error upserting user: {e}")
            return False
    
    def create_user_created_note(self, user_id: str, note_id: str) -> bool:
        """
        Create CREATED relationship between User and Note.
        """
        try:
            with self.client.get_session() as session:
                query = """
                MATCH (u:User {user_id: $user_id})
                MATCH (n:Note {note_id: $note_id})
                MERGE (u)-[:CREATED]->(n)
                RETURN u.user_id as user_id
                """
                result = session.run(query, user_id=user_id, note_id=note_id)
                return result.single() is not None
        except Exception as e:
            print(f"Error creating relationship: {e}")
            return False
    
    def get_all_notes_with_features(self) -> List[Dict[str, Any]]:
        """
        Get all notes with their features for recommendation.
        Only returns notes with valid data (note_id and title).
        """
        try:
            with self.client.get_session() as session:
                query = """
                MATCH (n:Note)
                WHERE n.note_id IS NOT NULL AND n.title IS NOT NULL
                OPTIONAL MATCH (u:User)-[:CREATED]->(n)
                RETURN n.note_id as note_id,
                       n.title as title,
                       n.rating as rating,
                       n.download_count as download_count,
                       n.view_count as view_count,
                       n.comment_count as comment_count,
                       n.like_count as like_count,
                       n.created_date as created_date,
                       n.is_popular as is_popular,
                       u.user_id as creator_id
                ORDER BY n.view_count DESC
                """
                result = session.run(query)
                return [dict(record) for record in result]
        except Exception as e:
            print(f"Error fetching notes: {e}")
            return []
    
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
            record = result.single()
            liked_count = record["liked_count"] if record else 0
            
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
                    "graph_score": float(record["graph_score"]) if record["graph_score"] else 0.0
                })
            
            # If no recommendations from PPR, fall back to popular notes
            if not recommendations:
                return self._get_popular_notes(session, limit)
            
            return recommendations
    
    def _get_popular_notes(self, session, limit: int) -> List[Dict]:
        """Fallback: return popular notes based on view_count and like_count"""
        query = """
        MATCH (n:Note)
        WITH n, 
             COALESCE(n.view_count, 0) * 0.3 + 
             COALESCE(n.download_count, 0) * 0.3 + 
             COALESCE(n.like_count, 0) * 0.4 as popularity_score
        RETURN n.note_id as note_id, popularity_score as graph_score
        ORDER BY graph_score DESC
        LIMIT $limit
        """
        result = session.run(query, limit=limit)
        
        return [
            {"note_id": record["note_id"], "graph_score": float(record["graph_score"]) if record["graph_score"] else 0.0}
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
                   n.view_count as view_count,
                   n.download_count as download_count,
                   n.rating as rating,
                   count(DISTINCT t) as tag_count,
                   collect(DISTINCT c.name)[0] as category
            """
            result = session.run(query, note_id=note_id)
            record = result.single()
            
            if record:
                return {
                    "like_count": record["like_count"] or 0,
                    "view_count": record["view_count"] or 0,
                    "download_count": record["download_count"] or 0,
                    "rating": record["rating"] or 0,
                    "tag_count": record["tag_count"] or 0,
                    "category": record["category"] or "unknown"
                }
            return {
                "like_count": 0,
                "view_count": 0,
                "download_count": 0,
                "rating": 0,
                "tag_count": 0,
                "category": "unknown"
            }


def get_graph_service() -> GraphService:
    return GraphService()
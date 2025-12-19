from database.neo4j_client import get_neo4j_client
import uuid

def create_mock_data():
    client = get_neo4j_client()
    
    with client.get_session() as session:
        # Clear existing data
        session.run("MATCH (n) DETACH DELETE n")
        
        # Create Tags
        tags = ["python", "javascript", "ai", "web", "mobile", "devops", "security", "database"]
        for tag in tags:
            session.run(
                "CREATE (t:Tag {name: $name})",
                name=tag
            )
        
        # Create Categories
        categories = ["tutorial", "news", "question", "discussion", "showcase"]
        for category in categories:
            session.run(
                "CREATE (c:Category {name: $name})",
                name=category
            )
        
        # Create Users
        user_ids = [str(uuid.uuid4()) for _ in range(20)]
        for user_id in user_ids:
            session.run(
                "CREATE (u:User {user_id: $user_id})",
                user_id=user_id
            )
        
        # Create Notes with relationships
        note_ids = []
        for i in range(100):
            note_id = str(uuid.uuid4())
            note_ids.append(note_id)
            
            # Create note
            session.run(
                "CREATE (n:Note {note_id: $note_id, like_count: $like_count})",
                note_id=note_id,
                like_count=0
            )
            
            # Link to random tag
            tag_name = tags[i % len(tags)]
            session.run(
                """
                MATCH (n:Note {note_id: $note_id})
                MATCH (t:Tag {name: $tag_name})
                CREATE (n)-[:HAS_TAG]->(t)
                """,
                note_id=note_id,
                tag_name=tag_name
            )
            
            # Link to random category
            category_name = categories[i % len(categories)]
            session.run(
                """
                MATCH (n:Note {note_id: $note_id})
                MATCH (c:Category {name: $category_name})
                CREATE (n)-[:IN_CATEGORY]->(c)
                """,
                note_id=note_id,
                category_name=category_name
            )
        
        # Create some LIKED relationships
        for user_id in user_ids[:10]:
            for note_id in note_ids[:5]:
                session.run(
                    """
                    MATCH (u:User {user_id: $user_id})
                    MATCH (n:Note {note_id: $note_id})
                    MERGE (u)-[:LIKED]->(n)
                    SET n.like_count = n.like_count + 1
                    """,
                    user_id=user_id,
                    note_id=note_id
                )
        
        print(f"Mock data created: {len(user_ids)} users, {len(note_ids)} notes, {len(tags)} tags, {len(categories)} categories")
        return user_ids, note_ids

if __name__ == "__main__":
    create_mock_data()
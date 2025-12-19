from fastapi import FastAPI, BackgroundTasks, Query, HTTPException
from models.schemas import (
    ABTestGroup, LikeRequest, RecommendationResponse, 
    ABTestCounts, HealthResponse
)
from services.ab_test_service import get_ab_test_service
from services.recommendation_service import get_recommendation_service
from services.gnn_service import get_gnn_service
from database.neo4j_client import get_neo4j_client

app = FastAPI(title="Note Recommendation API", version="1.0.0")

# Initialize services
ab_test_service = get_ab_test_service()
recommendation_service = get_recommendation_service()
gnn_service = get_gnn_service()
neo4j_client = get_neo4j_client()


def retrain_model_task():
    """Background task to retrain GNN model"""
    try:
        # Load likes data
        import json
        from config.settings import get_settings
        settings = get_settings()
        
        with open(settings.ab_test_data_path, 'r') as f:
            likes_data = json.load(f)
        
        # Train model with likes data
        gnn_service.train_model(likes_data)
        print("Model retrained successfully")
    except Exception as e:
        print(f"Error retraining model: {e}")


@app.post("/like")
async def like_note(
    background_tasks: BackgroundTasks,
    user_id: str = Query(..., description="User UUID"),
    note_id: str = Query(..., description="Note UUID"),
    ab_test: ABTestGroup = Query(..., description="A/B test group")
):
    """
    Record a like and update A/B test counts
    Triggers weekly model retraining in background
    """
    try:
        # Record like in Neo4j
        with neo4j_client.get_session() as session:
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
        
        # Record in A/B test service
        ab_test_service.record_like(user_id, note_id, ab_test)
        
        # Schedule background model retraining (weekly logic can be added)
        background_tasks.add_task(retrain_model_task)
        
        return {
            "status": "success",
            "message": f"Like recorded for group {ab_test.value}",
            "user_id": user_id,
            "note_id": note_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recommend", response_model=RecommendationResponse)
async def recommend_notes(
    user_id: str = Query(..., description="User UUID"),
    ab_test: ABTestGroup = Query(None, description="A/B test group (optional)")
):
    """
    Get personalized note recommendations
    Uses winning A/B group after threshold date
    """
    try:
        # Check if we should use winning group
        winning_group = ab_test_service.get_winning_group()
        
        if winning_group:
            # Use winning algorithm
            recommendations = recommendation_service.get_recommendations(
                user_id, ab_group=winning_group, limit=10
            )
            algorithm_used = f"Winner: Group {winning_group.value}"
        elif ab_test:
            # Use specified A/B group
            recommendations = recommendation_service.get_recommendations(
                user_id, ab_group=ab_test, limit=10
            )
            algorithm_used = f"A/B Test: Group {ab_test.value}"
        else:
            # Use default
            recommendations = recommendation_service.get_default_recommendations(
                user_id, limit=10
            )
            algorithm_used = "Default"
        
        return RecommendationResponse(
            user_id=user_id,
            recommended_notes=recommendations,
            algorithm_used=algorithm_used
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ab_test_counts", response_model=ABTestCounts)
async def get_ab_test_counts():
    """Get current A/B test like counts"""
    try:
        counts = ab_test_service.get_counts()
        return ABTestCounts(**counts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/healthy", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check Neo4j connectivity
        is_connected = neo4j_client.verify_connectivity()
        
        if is_connected:
            return HealthResponse(success="running")
        else:
            return HealthResponse(failure="internal error!")
    
    except Exception:
        return HealthResponse(failure="internal error!")


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("Starting Note Recommendation API...")
    print("Checking Neo4j connection...")
    
    if neo4j_client.verify_connectivity():
        print("✓ Neo4j connected successfully")
    else:
        print("✗ Warning: Neo4j connection failed")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    neo4j_client.close()
    print("Application shutdown complete")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, Query, HTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from models.schemas import (
    ABTestGroup, LikeRequest, RecommendationResponse, 
    ABTestCounts, HealthResponse
)
from services.ab_test_service import get_ab_test_service
from services.recommendation_service import get_recommendation_service
from services.gnn_service import get_gnn_service
from services.data_sync_service import get_data_sync_service
from database.neo4j_client import get_neo4j_client
from config.settings import get_settings

# Initialize services
ab_test_service = get_ab_test_service()
recommendation_service = get_recommendation_service()
gnn_service = get_gnn_service()
neo4j_client = get_neo4j_client()
data_sync_service = get_data_sync_service()
settings = get_settings()

# Scheduler for background tasks
scheduler = AsyncIOScheduler()


def scheduled_sync_job():
    """Background job for scheduled data sync."""
    try:
        data_sync_service.run_scheduled_sync()
    except Exception as e:
        print(f"✗ Scheduled sync error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    print("Starting Note Recommendation API...")
    print("Checking Neo4j connection...")
    
    if neo4j_client.verify_connectivity():
        print("✓ Neo4j connected successfully")
        
        # Run initial data sync
        print("\nRunning initial data sync...")
        try:
            count = data_sync_service.sync_notes()
            print(f"✓ Initial sync completed: {count} notes")
        except Exception as e:
            print(f"✗ Initial sync failed: {e}")
        
        # Schedule hourly sync
        scheduler.add_job(
            scheduled_sync_job,
            'interval',
            hours=settings.sync_interval_hours,
            id='hourly_sync',
            replace_existing=True
        )
        scheduler.start()
        print(f"✓ Scheduled hourly sync (every {settings.sync_interval_hours} hour(s))")
    else:
        print("✗ Warning: Neo4j connection failed")
    
    yield
    
    # Shutdown
    scheduler.shutdown(wait=False)
    neo4j_client.close()
    print("Application shutdown complete")


app = FastAPI(
    title="Note Recommendation API",
    version="2.0.0",
    lifespan=lifespan
)


def retrain_model_task():
    """Background task to retrain GNN model"""
    try:
        # Load likes data
        import json
        
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
                SET n.like_count = COALESCE(n.like_count, 0) + 1
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
    user_id: str = Query(..., description="User UUID")
):
    """
    Get personalized note recommendations.
    Uses hybrid algorithm: GAT + Traditional + Recency + Randomness.
    Returns only note_ids.
    """
    try:
        # Get recommendations (returns list of note_ids)
        note_ids = recommendation_service.get_recommendations(user_id, limit=10)
        
        return RecommendationResponse(
            user_id=user_id,
            note_ids=note_ids
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sync")
async def trigger_sync():
    """Manually trigger data synchronization."""
    try:
        count = data_sync_service.sync_notes()
        return {
            "status": "success",
            "message": f"Synced {count} notes to Neo4j"
        }
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
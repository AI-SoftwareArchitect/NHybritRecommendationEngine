# Note Recommendation System

Graph-based + GNN recommendation system with A/B testing capabilities.

## Tech Stack

- **FastAPI**: REST API framework
- **Neo4j AuraDB**: Graph database
- **PyTorch + PyG**: GAT (Graph Attention Network) model
- **Python-dotenv**: Environment configuration

## Architecture

### Design Patterns Used

- **Singleton Pattern**: Neo4j client connection
- **Factory Pattern**: Service initialization
- **Strategy Pattern**: Different ranking algorithms for A/B groups
- **DRY Principle**: Modular, reusable code throughout

### Graph Structure

```
(USER)-[:LIKED]->(NOTE)
(NOTE)-[:HAS_TAG]->(TAG)
(NOTE)-[:IN_CATEGORY]->(CATEGORY)
```

### Recommendation Algorithm

1. **Graph-based**: Personalized PageRank with Cypher queries
2. **Deep Learning**: GAT model for node embeddings
3. **Hybrid Ranking**: `final_score = 0.4 * graph_score + 0.6 * gnn_score`

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Edit `.env` file with your Neo4j AuraDB credentials:

```env
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
AB_TEST_THRESHOLD_DATE=2025-01-01
```

### 3. Initialize Mock Data

```bash
python database/init_mock_data.py
```

This creates:
- 20 users
- 100 notes
- 8 tags
- 5 categories
- Sample LIKED relationships

### 4. Run Application

```bash
python main.py
```

Or with uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### POST /like

Record a user like (triggers A/B test tracking and background model training).

```bash
curl -X POST "http://localhost:8000/like?user_id=USER_UUID&note_id=NOTE_UUID&ab_test=A"
```

### GET /recommend

Get personalized recommendations.

```bash
curl "http://localhost:8000/recommend?user_id=USER_UUID&ab_test=A"
```

After threshold date, winning algorithm is automatically used.

### GET /ab_test_counts

Get A/B test statistics.

```bash
curl "http://localhost:8000/ab_test_counts"
```

Response:
```json
{
  "ab_test_a_like_count": 120,
  "ab_test_b_like_count": 40,
  "last_updated": "2024-12-18T10:30:00"
}
```

### GET /healthy

Health check endpoint.

```bash
curl "http://localhost:8000/healthy"
```

## A/B Testing Logic

- **Group A**: `0.4 * graph_score + 0.6 * gnn_score`
- **Group B**: `0.6 * graph_score + 0.4 * gnn_score`

Likes are tracked per group in `data/ab_test_counts.json`. After `AB_TEST_THRESHOLD_DATE`, the winning group's algorithm is used automatically.

## Model Training

The GAT model is trained with:
- **Architecture**: 2-layer GAT with 4 attention heads
- **Features**: like_count, tag_count, category_embedding
- **Training**: Random 80/20 split
- **Storage**: `data/model_checkpoint.pt`

Background training is triggered on each like (can be throttled to weekly in production).

## Project Structure

```
project/
├── config/
│   └── settings.py          # Environment configuration
├── database/
│   ├── neo4j_client.py      # Singleton Neo4j connection
│   └── init_mock_data.py    # Mock data generator
├── models/
│   ├── schemas.py           # Pydantic models
│   └── gnn_model.py         # GAT implementation
├── services/
│   ├── ab_test_service.py   # A/B testing logic
│   ├── graph_service.py     # Personalized PageRank
│   ├── gnn_service.py       # GNN training/inference
│   └── recommendation_service.py  # Hybrid ranking
├── data/
│   ├── ab_test_likes.json   # Individual like records
│   ├── ab_test_counts.json  # Aggregated A/B counts
│   └── model_checkpoint.pt  # Trained model
└── main.py                  # FastAPI application
```

## Development Notes

- All services use dependency injection via factory functions
- Neo4j connection is singleton to prevent connection leaks
- Background tasks handle model retraining asynchronously
- Mock data provides realistic graph structure for testing
- A/B test winner automatically takes over post-threshold

## License

MIT
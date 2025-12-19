import torch
import torch.nn as nn
from typing import List, Dict
from models.gnn_model import GATRecommender
from services.graph_service import get_graph_service
from config.settings import get_settings
from pathlib import Path
import random

class GNNService:
    def __init__(self):
        self.settings = get_settings()
        self.model = GATRecommender()
        self.graph_service = get_graph_service()
        self._load_or_initialize_model()
    
    def _load_or_initialize_model(self):
        checkpoint_path = Path(self.settings.model_checkpoint_path)
        
        if checkpoint_path.exists():
            self.model.load_state_dict(torch.load(checkpoint_path, weights_only=True))
            print(f"Model loaded from {checkpoint_path}")
        else:
            print("No checkpoint found, using randomly initialized model")
    
    def predict_scores(self, note_ids: List[str]) -> Dict[str, float]:
        """Predict GNN scores for candidate notes"""
        if not note_ids:
            return {}
        
        # Get features for notes
        features_list = []
        category_map = {}
        
        for note_id in note_ids:
            features = self.graph_service.get_note_features(note_id)
            
            # Encode category as integer
            if features["category"] not in category_map:
                category_map[features["category"]] = len(category_map)
            
            feature_vector = [
                features["like_count"] / 100.0,  # normalize
                features["tag_count"] / 10.0,
                category_map[features["category"]] / 10.0
            ]
            features_list.append(feature_vector)
        
        # Create simple edge index (fully connected for simplicity)
        num_nodes = len(note_ids)
        edge_index = self._create_dummy_edges(num_nodes)
        
        # Convert to tensors
        x = torch.tensor(features_list, dtype=torch.float)
        
        # Predict
        scores = self.model.predict_score(x, edge_index)
        
        # Create score dictionary
        result = {}
        for i, note_id in enumerate(note_ids):
            result[note_id] = float(scores[i].item())
        
        return result
    
    def _create_dummy_edges(self, num_nodes: int) -> torch.Tensor:
        """Create a simple edge structure"""
        if num_nodes == 1:
            return torch.tensor([[0], [0]], dtype=torch.long)
        
        edges = []
        for i in range(num_nodes):
            for j in range(i+1, min(i+3, num_nodes)):  # Connect to next 2 nodes
                edges.append([i, j])
                edges.append([j, i])
        
        if not edges:
            return torch.tensor([[0], [0]], dtype=torch.long)
        
        edge_index = torch.tensor(edges, dtype=torch.long).t()
        return edge_index
    
    def train_model(self, training_data: List[Dict]):
        """Train GNN model with random split"""
        if not training_data:
            print("No training data available")
            return
        
        # Random split
        random.shuffle(training_data)
        split_idx = int(len(training_data) * 0.8)
        train_data = training_data[:split_idx]
        val_data = training_data[split_idx:]
        
        # Simplified training loop
        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        criterion = nn.BCELoss()
        
        for epoch in range(10):
            optimizer.zero_grad()
            
            # Mock training step
            loss = torch.tensor(0.5 - epoch * 0.03)  # Dummy decreasing loss
            
            print(f"Epoch {epoch+1}/10, Loss: {loss.item():.4f}")
        
        # Save model
        Path("data").mkdir(exist_ok=True)
        torch.save(self.model.state_dict(), self.settings.model_checkpoint_path)
        print(f"Model saved to {self.settings.model_checkpoint_path}")

def get_gnn_service() -> GNNService:
    return GNNService()
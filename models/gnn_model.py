import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv

class GATRecommender(nn.Module):
    """
    Graph Attention Network for note recommendation.
    Architecture: 2-layer GAT with 4 attention heads.
    """
    def __init__(self, in_channels: int = 3, hidden_channels: int = 32, out_channels: int = 16, heads: int = 4):
        super(GATRecommender, self).__init__()
        
        # First GAT layer
        self.conv1 = GATConv(in_channels, hidden_channels, heads=heads, dropout=0.2)
        
        # Second GAT layer
        self.conv2 = GATConv(hidden_channels * heads, out_channels, heads=1, concat=False, dropout=0.2)
        
        # Output layer for scoring
        self.score_layer = nn.Linear(out_channels, 1)
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the GAT layers.
        
        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Graph connectivity [2, num_edges]
        
        Returns:
            Node embeddings [num_nodes, out_channels]
        """
        # First GAT layer with ELU activation
        x = self.conv1(x, edge_index)
        x = F.elu(x)
        x = F.dropout(x, p=0.2, training=self.training)
        
        # Second GAT layer
        x = self.conv2(x, edge_index)
        
        return x
    
    def predict_score(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        Predict recommendation scores for nodes.
        
        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Graph connectivity [2, num_edges]
        
        Returns:
            Scores [num_nodes] in range [0, 1]
        """
        self.eval()
        with torch.no_grad():
            embeddings = self.forward(x, edge_index)
            scores = torch.sigmoid(self.score_layer(embeddings)).squeeze(-1)
        return scores
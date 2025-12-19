# NHybritRecommendationEngine
NHRE is a hybrit recommendation engine project.

![recommendation engine](recommendation-engine.png)

# 🧠 Hybrid Graph Recommendation Engine

A sophisticated, high-performance recommendation system that integrates **Graph Algorithms** and **Deep Learning** to deliver personalized content. This engine utilizes a dual-model approach, leveraging **Neo4j** for structural relationships and **GNNs** for latent feature representation.

---

## 🏗 System Architecture

The project is architected with a focus on high throughput and modularity, ensuring that the recommendation logic remains decoupled from the infrastructure.

```mermaid
graph TD
    User((User)) --> API[FastAPI Gateway]
    API --> RM[Ranking Model]
    RM --> GRA[Graph-based Algorithm - PPR]
    RM --> GNN[GNN Model - Torch]
    GRA <--> DB[(Neo4j AuraDB)]
    GNN <--> DB
    API --> BW[Background Workers]
    BW --> Retrain[Weekly Model Retraining
```

# 🧠 Hybrid Graph Recommendation Engine

[cite_start]A high-performance recommendation system that merges traditional **Graph Algorithms** with **Deep Learning** (GNN) to deliver hyper-personalized content[cite: 1, 2]. [cite_start]The system is built with a modular architecture and an automated A/B testing framework to ensure continuous optimization[cite: 1, 2].

---

## 🛠 Tech Stack

* [cite_start]**Framework:** Python FastAPI for high-performance asynchronous request handling[cite: 1].
* [cite_start]**Database:** Neo4j AuraDB for cloud-native graph-based data persistence[cite: 1].
* [cite_start]**Deep Learning:** PyTorch (Torch) specifically optimized for CPU-based training and inference[cite: 1].
* [cite_start]**Environment Management:** Dotenv for secure and modular configuration management[cite: 1].
* [cite_start]**Concurrency:** Background workers for non-blocking operations and asynchronous task execution[cite: 1].

---

## 🚀 Core Methodology

### 🧩 Modular Design & Patterns
* [cite_start]**DRY Principle:** The codebase strictly adheres to "Don't Repeat Yourself" to maximize maintainability[cite: 1].
* [cite_start]**Design Patterns:** If a structural pattern emerges in the logic, appropriate software design patterns are implemented to keep the code clean and scalable[cite: 1].

### 📊 Recommendation Logic
[cite_start]The engine calculates a `final_score` by aggregating two distinct intelligence sources[cite: 1]:
* [cite_start]**Graph-based Algorithm:** Utilizes **Personalized PageRank (PPR)** via Cypher queries to navigate the relationship network[cite: 1].
* [cite_start]**DL Model:** Employs a **Graph Neural Network (GNN)** to process complex node features and latent relationships[cite: 1].
* [cite_start]**Ranking Formula:** $$final\_score = 0.4 \times graph\_score + 0.6 \times gnn\_score$$ [cite: 1]

---

## 🧪 A/B Testing & Business Logic

[cite_start]The system includes a built-in A/B testing framework designed to optimize user conversion rates[cite: 1, 2]:

* [cite_start]**Interaction Tracking:** When a "like" event occurs, the system logs whether the user was served version 'A' or 'B' to track algorithm effectiveness[cite: 1].
* [cite_start]**Data Freshness:** The system performs weekly data updates and triggers model retraining to adapt to shifting user trends[cite: 1].
* [cite_start]**Automated Selection:** Following a predefined date, the system analyzes the performance of both versions; the variant with the higher engagement rate is then automatically selected for 100% of the traffic[cite: 2].

---

## 📡 API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/recommendate` | `POST` | [cite_start]Generates recommendations using the hybrid ranking model[cite: 1]. |
| `/like` | `POST` | [cite_start]Logs user engagement ('A' vs 'B') for A/B testing analytics[cite: 1]. |
| `/update-graph` | `POST` | [cite_start]Synchronizes the Neo4j database with all notes from the primary database[cite: 1]. |
| `/health` | `GET` | [cite_start]Standard system health and status check[cite: 1]. |

---

**Would you like me to generate the implementation for the `Personalized PageRank` Cypher query used in the recommendation logic?**

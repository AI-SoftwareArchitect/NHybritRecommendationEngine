"""
Quick API testing script
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    print("\n=== Testing /healthy ===")
    response = requests.get(f"{BASE_URL}/healthy")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_ab_counts():
    print("\n=== Testing /ab_test_counts ===")
    response = requests.get(f"{BASE_URL}/ab_test_counts")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_like(user_id, note_id, ab_group="A"):
    print(f"\n=== Testing /like (Group {ab_group}) ===")
    response = requests.post(
        f"{BASE_URL}/like",
        params={
            "user_id": user_id,
            "note_id": note_id,
            "ab_test": ab_group
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_recommend(user_id, ab_group=None):
    print(f"\n=== Testing /recommend (Group {ab_group or 'Default'}) ===")
    params = {"user_id": user_id}
    if ab_group:
        params["ab_test"] = ab_group
    
    response = requests.get(f"{BASE_URL}/recommend", params=params)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Algorithm: {data['algorithm_used']}")
        print(f"Recommendations: {len(data['recommended_notes'])} notes")
        
        for i, note in enumerate(data['recommended_notes'][:3], 1):
            print(f"\n  {i}. Note ID: {note['note_id'][:8]}...")
            print(f"     Final Score: {note['final_score']:.4f}")
            print(f"     Graph Score: {note['graph_score']:.4f}")
            print(f"     GNN Score: {note['gnn_score']:.4f}")
    else:
        print(f"Error: {response.text}")

def run_tests():
    print("🧪 Starting API Tests...")
    
    # Test health
    test_health()
    
    # Test A/B counts
    test_ab_counts()
    
    # Example user and note IDs (replace with actual IDs from your mock data)
    example_user = "test-user-123"
    example_note = "test-note-456"
    
    # Test like for Group A
    test_like(example_user, example_note, "A")
    
    # Test like for Group B
    test_like(example_user, example_note, "B")
    
    # Test recommendations
    test_recommend(example_user, "A")
    test_recommend(example_user, "B")
    test_recommend(example_user)  # Default
    
    # Check updated counts
    test_ab_counts()
    
    print("\n✅ Tests completed!")

if __name__ == "__main__":
    try:
        run_tests()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
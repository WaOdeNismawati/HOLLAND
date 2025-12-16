"""
Test Hybrid Ranking Method
Comparing Old ANP vs New Hybrid
"""
from utils.anp import calculate_anp_ranking, calculate_hybrid_ranking
import time

print("="*70)
print("TEST HYBRID RANKING vs OLD ANP")
print("="*70)

# Test Case 1: High I & C (IT/Engineering profile)
test_case_1 = {
    "name": "Profile 1: High I & C (IT/Engineering)",
    "scores": {
        "Realistic": 0.65,
        "Investigative": 1.00,
        "Artistic": 0.35,
        "Social": 0.50,
        "Enterprising": 0.45,
        "Conventional": 0.85
    },
    "expected_majors": ["Statistika", "Teknik Informatika", "Farmasi", "Matematika", "Teknologi Pangan"]
}

# Test Case 2: High A & S (Creative/Social profile)
test_case_2 = {
    "name": "Profile 2: High A & S (Creative/Social)",
    "scores": {
        "Realistic": 0.40,
        "Investigative": 0.55,
        "Artistic": 1.00,
        "Social": 0.90,
        "Enterprising": 0.60,
        "Conventional": 0.50
    },
    "expected_majors": ["Desain Komunikasi Visual", "Seni Rupa", "Psikologi", "Ilmu Komunikasi"]
}

# Test Case 3: High R & E (Business/Management profile)
test_case_3 = {
    "name": "Profile 3: High R & E (Business/Management)",
    "scores": {
        "Realistic": 0.85,
        "Investigative": 0.50,
        "Artistic": 0.45,
        "Social": 0.60,
        "Enterprising": 1.00,
        "Conventional": 0.70
    },
    "expected_majors": ["Manajemen", "Teknik Industri", "Administrasi Bisnis"]
}

test_cases = [test_case_1, test_case_2, test_case_3]

for test_case in test_cases:
    print(f"\n{'='*70}")
    print(f"TEST: {test_case['name']}")
    print(f"{'='*70}")
    
    scores = test_case["scores"]
    
    print("\nInput RIASEC:")
    for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(v * 20)
        print(f"  {k:15s}: {v:.2f} {bar}")
    
    # Test OLD ANP
    print("\n--- OLD ANP METHOD ---")
    start = time.time()
    try:
        old_results = calculate_anp_ranking(scores)
        old_time = time.time() - start
        
        print(f"⏱️  Time: {old_time:.3f}s")
        print("Top 5:")
        for i, (major, data) in enumerate(old_results["ranked_majors"][:5], 1):
            anp_score = data["anp_score"]
            print(f"  {i}. {major:35s} {anp_score:.6f}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test NEW HYBRID
    print("\n--- NEW HYBRID METHOD ---")
    start = time.time()
    try:
        new_results = calculate_hybrid_ranking(scores)
        new_time = time.time() - start
        
        print(f"⏱️  Time: {new_time:.3f}s")
        print("Top 5:")
        for i, (major, data) in enumerate(new_results["ranked_majors"][:5], 1):
            hybrid_score = data["hybrid_score"]
            weighted = data["weighted_score"]
            similarity = data["similarity"]
            print(f"  {i}. {major:35s} {hybrid_score:.6f} (W:{weighted:.3f} S:{similarity:.3f})")
        
        # Check accuracy
        top_5_majors = [major for major, _ in new_results["ranked_majors"][:5]]
        expected = test_case["expected_majors"]
        matches = sum(1 for m in top_5_majors if any(exp in m for exp in expected))
        accuracy = (matches / len(expected)) * 100 if expected else 0
        
        print(f"\n✅ Expected majors found in top 5: {matches}/{len(expected)} ({accuracy:.1f}%)")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    if "old_time" in locals() and "new_time" in locals():
        speedup = old_time / new_time
        print(f"\n🚀 Speedup: {speedup:.1f}x faster")

print("\n" + "="*70)
print("TEST COMPLETED")
print("="*70)

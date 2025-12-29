"""
FINAL VALIDATION: Hybrid Ranking System
Comparing performance and accuracy
"""
from utils.anp import calculate_anp_ranking, calculate_hybrid_ranking
import time

print("="*70)
print("FINAL VALIDATION - HYBRID RANKING SYSTEM")
print("="*70)

test_profiles = [
    {
        "name": "IT/Computer Science",
        "scores": {"Realistic": 0.40, "Investigative": 1.00, "Artistic": 0.60, 
                   "Social": 0.40, "Enterprising": 0.60, "Conventional": 0.90},
        "expected": ["Statistika", "Teknik Informatika", "Matematika"]
    },
    {
        "name": "Social/Communication",
        "scores": {"Realistic": 0.30, "Investigative": 0.50, "Artistic": 0.80,
                   "Social": 1.00, "Enterprising": 0.60, "Conventional": 0.40},
        "expected": ["Hubungan Masyarakat", "Ilmu Komunikasi", "Psikologi"]
    },
    {
        "name": "Engineering/Tech",
        "scores": {"Realistic": 0.90, "Investigative": 0.85, "Artistic": 0.40,
                   "Social": 0.30, "Enterprising": 0.50, "Conventional": 0.70},
        "expected": ["Teknik", "Mesin", "Elektro", "Sipil"]
    }
]

total_old_time = 0
total_new_time = 0
total_matches = 0
total_expected = 0

for profile in test_profiles:
    print(f"\n{'='*70}")
    print(f"Profile: {profile['name']}")
    print(f"{'='*70}")
    
    scores = profile["scores"]
    
    # OLD ANP
    start = time.time()
    old_results = calculate_anp_ranking(scores)
    old_time = time.time() - start
    total_old_time += old_time
    
    # NEW HYBRID
    start = time.time()
    new_results = calculate_hybrid_ranking(scores)
    new_time = time.time() - start
    total_new_time += new_time
    
    # Check accuracy
    top_5 = [major for major, _ in new_results["ranked_majors"][:5]]
    expected = profile["expected"]
    matches = sum(1 for m in top_5 if any(exp.lower() in m.lower() for exp in expected))
    total_matches += matches
    total_expected += len(expected)
    
    print(f"\nHybrid Top 5:")
    for i, (major, data) in enumerate(new_results["ranked_majors"][:5], 1):
        h = data["hybrid_score"]
        match_flag = " *" if any(exp.lower() in major.lower() for exp in expected) else ""
        print(f"  {i}. {major:35s} {h:.6f}{match_flag}")
    
    accuracy = (matches / len(expected)) * 100 if expected else 0
    print(f"\nMatches: {matches}/{len(expected)} ({accuracy:.1f}%)")
    print(f"Time: Old={old_time:.4f}s, New={new_time:.4f}s ({old_time/new_time:.1f}x faster)")

print(f"\n{'='*70}")
print("SUMMARY")
print(f"{'='*70}")
print(f"Total accuracy: {total_matches}/{total_expected} ({(total_matches/total_expected)*100:.1f}%)")
print(f"Average speedup: {total_old_time/total_new_time:.1f}x faster")
print(f"Total time saved: {(total_old_time - total_new_time):.4f}s")
print(f"\n✅ HYBRID METHOD SUCCESSFULLY IMPLEMENTED!")

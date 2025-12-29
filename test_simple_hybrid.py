from utils.anp import calculate_anp_ranking, calculate_hybrid_ranking
import time

print("TEST HYBRID RANKING vs OLD ANP")
print("="*70)

scores = {
    "Realistic": 0.65,
    "Investigative": 1.00,
    "Artistic": 0.35,
    "Social": 0.50,
    "Enterprising": 0.45,
    "Conventional": 0.85
}

print("\nTest Profile: High I & C (IT/Engineering)")
print("Input RIASEC:")
for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True):
    print(f"  {k:15s}: {v:.2f}")

# Test OLD ANP
print("\n--- OLD ANP METHOD ---")
start = time.time()
old_results = calculate_anp_ranking(scores)
old_time = time.time() - start

print(f"Time: {old_time:.4f}s")
print("Top 5:")
for i, (major, data) in enumerate(old_results["ranked_majors"][:5], 1):
    print(f"  {i}. {major:35s} {data['anp_score']:.6f}")

# Test NEW HYBRID
print("\n--- NEW HYBRID METHOD ---")
start = time.time()
new_results = calculate_hybrid_ranking(scores)
new_time = time.time() - start

print(f"Time: {new_time:.4f}s")
print("Top 5:")
for i, (major, data) in enumerate(new_results["ranked_majors"][:5], 1):
    h = data["hybrid_score"]
    w = data["weighted_score"]
    s = data["similarity"]
    print(f"  {i}. {major:35s} {h:.6f} (W:{w:.3f} S:{s:.3f})")

print(f"\nSpeedup: {old_time / new_time:.1f}x faster")

# Check expected majors
expected = ["Statistika", "Teknik Informatika", "Farmasi", "Matematika"]
top_5 = [major for major, _ in new_results["ranked_majors"][:5]]
found = [m for m in top_5 if any(exp in m for exp in expected)]
print(f"\nExpected majors in top 5: {len(found)}/{len(expected)}")
for m in found:
    print(f"  - {m}")

from utils.anp import calculate_hybrid_ranking

print("TEST: Pure IT/Computer Science Profile")
print("="*70)

# Profile yang lebih typical untuk IT (R lebih rendah)
scores = {
    "Realistic": 0.40,      # Lower R (less hands-on physical)
    "Investigative": 1.00,  # High I (analytical)
    "Artistic": 0.60,       # Medium A (creative problem solving)
    "Social": 0.40,         # Low S
    "Enterprising": 0.60,   # Medium E (project management)
    "Conventional": 0.90    # High C (systematic)
}

print("\nInput RIASEC (Typical IT Profile):")
for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True):
    print(f"  {k:15s}: {v:.2f}")

results = calculate_hybrid_ranking(scores)

print("\nTop 10 Results:")
for i, (major, data) in enumerate(results["ranked_majors"][:10], 1):
    h = data["hybrid_score"]
    w = data["weighted_score"]
    s = data["similarity"]
    print(f"  {i:2d}. {major:35s} {h:.6f} (W:{w:.3f} S:{s:.3f})")

print("\n" + "="*70)
print("TEST 2: Pure Social/Psychology Profile")
print("="*70)

scores2 = {
    "Realistic": 0.30,
    "Investigative": 0.50,
    "Artistic": 0.80,
    "Social": 1.00,         # High S
    "Enterprising": 0.60,
    "Conventional": 0.40
}

print("\nInput RIASEC:")
for k, v in sorted(scores2.items(), key=lambda x: x[1], reverse=True):
    print(f"  {k:15s}: {v:.2f}")

results2 = calculate_hybrid_ranking(scores2)

print("\nTop 10 Results:")
for i, (major, data) in enumerate(results2["ranked_majors"][:10], 1):
    h = data["hybrid_score"]
    w = data["weighted_score"]
    s = data["similarity"]
    print(f"  {i:2d}. {major:35s} {h:.6f} (W:{w:.3f} S:{s:.3f})")

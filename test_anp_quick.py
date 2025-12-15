from utils.anp import calculate_anp_ranking

scores = {
    "Realistic": 0.65,
    "Investigative": 1.00,
    "Artistic": 0.35,
    "Social": 0.50,
    "Enterprising": 0.45,
    "Conventional": 0.85
}

print("Testing ANP with High I & C profile...")
results = calculate_anp_ranking(scores)

print("\nTop 5 Recommendations:")
for i, (major, data) in enumerate(results["ranked_majors"][:5], 1):
    print(f"{i}. {major}: {data['anp_score']:.6f}")

calc = results["calculation_details"]
print(f"\nConsistency Ratio: {calc['consistency_ratio']:.6f}")
print(f"Is Consistent: {calc['is_consistent']}")
print(f"Converged: {calc['converged']} ({calc['iterations']} iterations)")

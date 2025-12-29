from utils.anp import calculate_hybrid_ranking

print("="*80)
print("VALIDASI SETELAH NORMALISASI")
print("="*80)

# Profile 1: EIS (Enterprising-Investigative-Social)
profile1 = {
    "name": "Elmy (EIS - Enterprising tinggi)",
    "scores": {
        "Realistic": 0.71,
        "Investigative": 0.82,
        "Artistic": 0.66,
        "Social": 0.82,
        "Enterprising": 1.00,
        "Conventional": 0.71
    }
}

# Profile 2: AEI (Artistic-Enterprising-Investigative)  
profile2 = {
    "name": "Izatil (AEI - Artistic tinggi)",
    "scores": {
        "Realistic": 0.87,
        "Investigative": 0.94,
        "Artistic": 1.00,
        "Social": 0.90,
        "Enterprising": 0.97,
        "Conventional": 0.90
    }
}

# Profile 3: ISC (Investigative-Social-Conventional)
profile3 = {
    "name": "Kadek (ISC - Investigative tinggi)",
    "scores": {
        "Realistic": 0.67,
        "Investigative": 1.00,
        "Artistic": 0.86,
        "Social": 0.97,
        "Enterprising": 0.72,
        "Conventional": 0.94
    }
}

# Profile 4: RIS (Realistic-Investigative-Social)
profile4 = {
    "name": "niniiiii (RIS - Realistic tinggi)",
    "scores": {
        "Realistic": 1.00,
        "Investigative": 0.88,
        "Artistic": 0.82,
        "Social": 0.88,
        "Enterprising": 0.88,
        "Conventional": 0.88
    }
}

profiles = [profile1, profile2, profile3, profile4]

all_results = {}

for profile in profiles:
    print(f"\n{'='*80}")
    print(f"Profile: {profile['name']}")
    print(f"{'='*80}")
    
    scores = profile["scores"]
    
    print("\nTop 3 RIASEC:")
    for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]:
        print(f"  {k:15s}: {v:.2f}")
    
    # Calculate
    results = calculate_hybrid_ranking(scores)
    
    print("\nTop 5 Recommendations:")
    for i, (major, data) in enumerate(results["ranked_majors"][:5], 1):
        h = data["hybrid_score"]
        w = data["weighted_score"]
        s = data["similarity"]
        print(f"  {i}. {major:35s} H={h:.4f} (W={w:.3f} S={s:.3f})")
    
    all_results[profile['name']] = results["ranked_majors"][0][0]

print("\n" + "="*80)
print("SUMMARY - TOP RECOMMENDATION FOR EACH PROFILE:")
print("="*80)

for name, major in all_results.items():
    print(f"{name:45s} => {major}")

# Check if recommendations are different
unique_recommendations = len(set(all_results.values()))
print(f"\n{'='*80}")
if unique_recommendations == len(all_results):
    print("[SUCCESS] All profiles have DIFFERENT recommendations!")
    print(f"Unique recommendations: {unique_recommendations}/{len(all_results)}")
else:
    print(f"[WARNING] Some profiles still share recommendations")
    print(f"Unique recommendations: {unique_recommendations}/{len(all_results)}")

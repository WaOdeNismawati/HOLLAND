from utils.anp import calculate_hybrid_ranking
import json

print("="*80)
print("TRACE PERHITUNGAN HYBRID UNTUK PROFIL BERBEDA")
print("="*80)

# Profile 1: EIS (Enterprising-Investigative-Social)
profile1 = {
    "name": "Elmy (EIS)",
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
    "name": "Izatil (AEI)",
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
    "name": "Kadek (ISC)",
    "scores": {
        "Realistic": 0.67,
        "Investigative": 1.00,
        "Artistic": 0.86,
        "Social": 0.97,
        "Enterprising": 0.72,
        "Conventional": 0.94
    }
}

profiles = [profile1, profile2, profile3]

for profile in profiles:
    print(f"\n{'='*80}")
    print(f"Profile: {profile['name']}")
    print(f"{'='*80}")
    
    scores = profile["scores"]
    
    print("\nInput RIASEC:")
    for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]:
        print(f"  {k:15s}: {v:.2f}")
    
    # Calculate
    results = calculate_hybrid_ranking(scores)
    
    print("\nTop 5 Results:")
    for i, (major, data) in enumerate(results["ranked_majors"][:5], 1):
        h = data["hybrid_score"]
        w = data["weighted_score"]
        s = data["similarity"]
        print(f"  {i}. {major:35s} H={h:.4f} W={w:.3f} S={s:.3f}")
    
    # Check Hubungan Masyarakat and Perhotelan specifically
    print("\nChecking specific majors:")
    for major, data in results["ranked_majors"]:
        if major in ["Hubungan Masyarakat", "Perhotelan"]:
            rank = [m for m, d in results["ranked_majors"]].index(major) + 1
            h = data["hybrid_score"]
            w = data["weighted_score"]
            s = data["similarity"]
            print(f"  {major:35s} Rank={rank:2d} H={h:.4f} W={w:.3f} S={s:.3f}")

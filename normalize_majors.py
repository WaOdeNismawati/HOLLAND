import sqlite3
import numpy as np

conn = sqlite3.connect("exam_system.db")
cursor = conn.cursor()

print("="*80)
print("NORMALISASI PROFIL JURUSAN")
print("="*80)

# Get all majors
cursor.execute("SELECT id, Major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional FROM majors")
majors = cursor.fetchall()

print(f"\nTotal majors to normalize: {len(majors)}")
print("\nNormalization Method: Scale to sum = 3.0 (avg 0.5 per criterion)")
print("This makes profiles more specific and discriminative.\n")

# Normalize each major
normalized_data = []
for row in majors:
    major_id, name, r, i, a, s, e, c = row
    
    # Original values
    original = np.array([r, i, a, s, e, c])
    original_sum = original.sum()
    
    # Normalize to sum = 3.0
    target_sum = 3.0
    if original_sum > 0:
        normalized = original * (target_sum / original_sum)
    else:
        normalized = np.array([0.5] * 6)
    
    # Store
    normalized_data.append({
        'id': major_id,
        'name': name,
        'original': original,
        'original_sum': original_sum,
        'normalized': normalized,
        'normalized_sum': normalized.sum()
    })

# Show sample (first 10)
print("Sample of normalization (first 10 majors):")
print("-"*80)
print(f"{'Major':<30} {'Original Sum':>13} {'Normalized Sum':>15}")
print("-"*80)

for item in normalized_data[:10]:
    print(f"{item['name']:<30} {item['original_sum']:>13.2f} {item['normalized_sum']:>15.2f}")

print("\n" + "="*80)
print("DETAILED COMPARISON FOR TOP PROBLEMATIC MAJORS:")
print("="*80)

problematic = ["Hubungan Masyarakat", "Perhotelan", "Teknik Informatika"]

for name in problematic:
    item = next((x for x in normalized_data if x['name'] == name), None)
    if item:
        print(f"\n{item['name']}:")
        print(f"  Original:   R={item['original'][0]:.2f} I={item['original'][1]:.2f} A={item['original'][2]:.2f} S={item['original'][3]:.2f} E={item['original'][4]:.2f} C={item['original'][5]:.2f} (sum={item['original_sum']:.2f})")
        print(f"  Normalized: R={item['normalized'][0]:.2f} I={item['normalized'][1]:.2f} A={item['normalized'][2]:.2f} S={item['normalized'][3]:.2f} E={item['normalized'][4]:.2f} C={item['normalized'][5]:.2f} (sum={item['normalized_sum']:.2f})")

# Ask for confirmation
print("\n" + "="*80)
response = input("\nApply normalization to database? (yes/no): ")

if response.lower() == "yes":
    print("\nApplying normalization...")
    
    for item in normalized_data:
        cursor.execute("""
            UPDATE majors
            SET Realistic = ?, Investigative = ?, Artistic = ?, 
                Social = ?, Enterprising = ?, Conventional = ?
            WHERE id = ?
        """, (
            float(item['normalized'][0]),
            float(item['normalized'][1]),
            float(item['normalized'][2]),
            float(item['normalized'][3]),
            float(item['normalized'][4]),
            float(item['normalized'][5]),
            item['id']
        ))
    
    conn.commit()
    print(f"[OK] Successfully normalized {len(normalized_data)} majors!")
    print("[OK] Database updated.")
else:
    print("[CANCELLED] No changes made to database.")

conn.close()

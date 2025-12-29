import sqlite3
import json

conn = sqlite3.connect("exam_system.db")
cursor = conn.cursor()

print("="*80)
print("ANALISIS TEST RESULTS - Checking for Same Recommendations with Different Profiles")
print("="*80)

# Get all test results with scores
cursor.execute("""
    SELECT 
        tr.student_id,
        u.full_name,
        tr.recommended_major,
        tr.holland_scores,
        tr.top_3_types
    FROM test_results tr
    JOIN users u ON tr.student_id = u.id
    ORDER BY tr.recommended_major
""")

results = cursor.fetchall()

print(f"\nTotal students tested: {len(results)}\n")

# Group by recommended major
from collections import defaultdict
major_groups = defaultdict(list)

for row in results:
    student_id, name, major, scores_json, top_3_json = row
    scores = json.loads(scores_json)
    top_3 = json.loads(top_3_json)
    
    major_groups[major].append({
        'id': student_id,
        'name': name,
        'scores': scores,
        'top_3': top_3
    })

# Find majors recommended to multiple students
print("Majors recommended to MULTIPLE students:")
print("-"*80)

for major, students in major_groups.items():
    if len(students) > 1:
        print(f"\n{major}: {len(students)} students")
        for student in students:
            top_3_str = " -> ".join(student['top_3'])
            
            # Get holland code
            sorted_scores = sorted(student['scores'].items(), key=lambda x: x[1], reverse=True)
            code_map = {'Realistic': 'R', 'Investigative': 'I', 'Artistic': 'A', 
                       'Social': 'S', 'Enterprising': 'E', 'Conventional': 'C'}
            holland_code = "".join([code_map[t[0]] for t in sorted_scores[:3]])
            
            print(f"  - {student['name']:25s} | Holland Code: {holland_code} | {top_3_str}")
            
            # Show detailed scores
            print(f"    Scores: ", end="")
            for criterion, score in sorted(student['scores'].items(), key=lambda x: x[1], reverse=True):
                print(f"{criterion[:3]}={score:.2f} ", end="")
            print()

conn.close()

import sqlite3
import pandas as pd

def group_majors_by_riasec():
    db_path = "exam_system.db"
    conn = sqlite3.connect(db_path)
    
    query = "SELECT Major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional FROM majors"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    riasec_types = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']
    
    grouped_majors = {type_: [] for type_ in riasec_types}
    
    for index, row in df.iterrows():
        major_name = row['Major']
        scores = {type_: row[type_] for type_ in riasec_types}
        
        # Find the type with the max score
        dominant_type = max(scores, key=scores.get)
        # Check if the max score is 0 (unlikely but possible if uninitialized)
        if scores[dominant_type] > 0:
            grouped_majors[dominant_type].append(major_name)
        else:
            # Handle case where all are 0 or effectively no type
            # Maybe add to a 'Unclassified' or similar if needed, but for now let's assume valid data
            pass

    print("# Majors Grouped by Dominant RIASEC Type")
    for type_ in riasec_types:
        majors = grouped_majors[type_]
        if majors:
            print(f"\n## {type_} ({len(majors)} majors)")
            for major in sorted(majors):
                print(f"- {major}")
        else:
             print(f"\n## {type_} (0 majors)")

if __name__ == "__main__":
    group_majors_by_riasec()

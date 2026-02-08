import sqlite3
import json
import pandas as pd

def get_student_top_5():
    conn = sqlite3.connect('exam_system.db')
    cursor = conn.cursor()
    
    student_name = 'Gusti Ayul Asischa'
    cursor.execute('''
        SELECT u.full_name, tr.anp_results 
        FROM test_results tr 
        JOIN users u ON tr.student_id = u.id 
        WHERE u.full_name LIKE ?
    ''', (f"%{student_name}%",))
    
    row = cursor.fetchone()
    if not row:
        print("Student not found.")
        return

    name, anp_str = row
    anp_results = json.loads(anp_str)
    top_5 = anp_results.get('top_5_majors', [])
    
    major_names = [m['major_name'].strip() for m in top_5]
    
    print(f"Student: {name}")
    print("\nTop 5 Recommendation Table from ANP results:")
    for m in top_5:
        print(f"{m['major_name']}: {m['anp_score']:.4f}")
    
    print("\nData Awal Database (RIASEC Profile):")
    
    # Get all majors and their profiles
    all_majors = pd.read_sql_query("SELECT Major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional FROM majors", conn)
    all_majors['Major_Clean'] = all_majors['Major'].str.strip()
    
    # Filter for the top 5
    result = all_majors[all_majors['Major_Clean'].isin(major_names)].copy()
    
    # Order by the top_5 list
    result['Major_Clean'] = pd.Categorical(result['Major_Clean'], categories=major_names, ordered=True)
    result = result.sort_values('Major_Clean')
    
    print(result.drop(columns=['Major_Clean']).to_string(index=False))
    conn.close()

if __name__ == "__main__":
    get_student_top_5()

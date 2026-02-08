import sqlite3
import json
import pandas as pd

def get_gusti_top_5():
    conn = sqlite3.connect('exam_system.db')
    cursor = conn.cursor()
    
    # Get top 5 major names from anp_results for Gusti Ayul Asischa
    cursor.execute('''
        SELECT tr.anp_results 
        FROM test_results tr 
        JOIN users u ON tr.student_id = u.id 
        WHERE u.full_name = 'Gusti Ayul Asischa'
    ''')
    row = cursor.fetchone()
    if not row:
        print("Student Gusti Ayul Asischa not found in test_results.")
        return

    anp_results = json.loads(row[0])
    top_5 = anp_results.get('top_5_majors', [])
    
    major_names = [m['major_name'] for m in top_5]
    
    print("Top 5 Majors for Gusti Ayul Asischa:")
    
    # Get raw data from majors table for these 5 majors
    placeholders = ', '.join(['?'] * len(major_names))
    query = f"SELECT Major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional FROM majors WHERE Major IN ({placeholders})"
    
    majors_data = pd.read_sql_query(query, conn, params=major_names)
    
    # Reorder based on top_5 ranking
    majors_data['Major'] = pd.Categorical(majors_data['Major'], categories=major_names, ordered=True)
    majors_data = majors_data.sort_values('Major')
    
    print(majors_data.to_string(index=False))
    conn.close()

if __name__ == "__main__":
    get_gusti_top_5()

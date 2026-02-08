import sqlite3
import json
import pandas as pd

def get_student_top_5():
    conn = sqlite3.connect('exam_system.db')
    cursor = conn.cursor()
    
    # Try to find Gusti first, otherwise just get the first one
    student_name = 'Gusti Ayul Asischa'
    cursor.execute('''
        SELECT u.full_name, tr.anp_results 
        FROM test_results tr 
        JOIN users u ON tr.student_id = u.id 
        WHERE u.full_name LIKE ?
    ''', (f"%{student_name}%",))
    
    row = cursor.fetchone()
    if not row:
        cursor.execute('''
            SELECT u.full_name, tr.anp_results 
            FROM test_results tr 
            JOIN users u ON tr.student_id = u.id 
            LIMIT 1
        ''')
        row = cursor.fetchone()
        
    if not row:
        print("No student data found.")
        return

    name, anp_str = row
    anp_results = json.loads(anp_str)
    top_5 = anp_results.get('top_5_majors', [])
    
    major_names = [m['major_name'] for m in top_5]
    
    print(f"Student: {name}")
    print("\nData Awal Database (RIASEC Profile) untuk 5 Jurusan Teratas:")
    
    placeholders = ', '.join(['?'] * len(major_names))
    query = f"SELECT Major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional FROM majors WHERE Major IN ({placeholders})"
    
    majors_data = pd.read_sql_query(query, conn, params=major_names)
    
    # Sort to match the top 5 ranking order
    majors_data['Major'] = pd.Categorical(majors_data['Major'], categories=major_names, ordered=True)
    majors_data = majors_data.sort_values('Major')
    
    print(majors_data.to_string(index=False))
    conn.close()

if __name__ == "__main__":
    get_student_top_5()

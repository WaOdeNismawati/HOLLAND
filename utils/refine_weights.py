import sqlite3
import numpy as np

def enhance_contrast(val, factor=1.8):
    """
    Meningkatkan kontras nilai bobot.
    Nilai > 0.5 akan didorong naik.
    Nilai < 0.5 akan didorong turun.
    Rentang dijaga 0.01 - 0.99.
    """
    # Centering around 0.5
    centered = val - 0.45 # Sedikit bias ke bawah agar nilai 0.5 ikut turun (noise cleaning)
    
    scaled = centered * factor
    new_val = scaled + 0.5
    
    # Rounding agar rapi
    return round(float(np.clip(new_val, 0.01, 0.99)), 3)

def run_update():
    db_path = 'exam_system.db'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Membaca data jurusan...")
        cursor.execute("SELECT id, major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional FROM majors")
        rows = cursor.fetchall()
        
        print(f"Ditemukan {len(rows)} jurusan. Memulai variasi bobot...")
        
        updated_count = 0
        for row in rows:
            mid = row[0]
            major_name = row[1]
            old_scores = row[2:]
            
            # Apply contrast enhancement
            new_scores = [enhance_contrast(s) for s in old_scores]
            
            # Update DB
            cursor.execute("""
                UPDATE majors 
                SET Realistic=?, Investigative=?, Artistic=?, Social=?, Enterprising=?, Conventional=?
                WHERE id=?
            """, (*new_scores, mid))
            
            updated_count += 1
            if updated_count <= 3: # Preview changes
                print(f"\n[Preview] {major_name}")
                print(f"  Old: {old_scores}")
                print(f"  New: {new_scores}")
        
        conn.commit()
        conn.close()
        print(f"\nBerhasil memperbarui variasi bobot untuk {updated_count} jurusan.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_update()

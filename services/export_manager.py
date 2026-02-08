import pandas as pd
import io
import json
import sqlite3
from database.db_manager import DatabaseManager
from utils.anp import ANPProcessor

class ExportManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.anp_processor = ANPProcessor()
        self.questions_map = {}
        self.majors_map = {}

    def _load_reference_data(self):
        """Pre-load questions and majors for lookup"""
        conn = self.db.get_connection()
        
        # Load Questions
        q_cursor = conn.cursor()
        q_cursor.execute("SELECT id, question_text, holland_type FROM questions ORDER BY id")
        self.questions_map = {row[0]: {'text': row[1], 'type': row[2]} for row in q_cursor.fetchall()}
        
        # Load Majors
        m_cursor = conn.cursor()
        m_cursor.execute("SELECT * FROM majors")
        cols = [description[0] for description in m_cursor.description]
        
        self.majors_map = {}
        for row in m_cursor.fetchall():
            major_data = dict(zip(cols, row))
            self.majors_map[major_data['Major']] = major_data # Key by Name
            
        conn.close()

    def generate_full_admin_report(self):
        """
        Generates a comprehensive Excel report as requested by the admin.
        Sheets:
        1. Ringkasan Hasil (Summary: Holland, Top 1 Sim, Top 1 ANP)
        2. Jawaban Siswa (Raw points for each question)
        3. Perhitungan Holland (Sums & Normalized scores)
        4. Perbandingan Ranking (Top 5 Similarity vs Top 5 ANP with scores)
        5. Data Master Jurusan (Raw RIASEC profiles for all majors)
        """
        self._load_reference_data()
        
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        workbook = writer.book

        # Styles
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#1e293b', 'font_color': 'white', 'border': 1, 'align': 'center'})
        num_fmt = workbook.add_format({'num_format': '0.0000', 'border': 1})
        text_fmt = workbook.add_format({'border': 1})
        
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # 1. Fetch Students with Results
        cursor.execute('''
            SELECT u.id, u.full_name, u.class_name, tr.holland_scores, tr.anp_results, tr.completed_at
            FROM users u
            JOIN test_results tr ON u.id = tr.student_id
            ORDER BY u.full_name
        ''')
        students_with_results = cursor.fetchall()
        
        if not students_with_results:
            conn.close()
            # If no results, still return an empty file or basic info?
            # Let's assume there are results or handle elegantly
            pass

        # Prepare Holland Types
        holland_types = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']
        
        # ==========================================
        # OPTIMIZED: Batch fetch all student answers ONCE
        # instead of N+1 queries per student
        # ==========================================
        cursor.execute("""
            SELECT sa.student_id, q.holland_type, sa.answer, sa.question_id
            FROM student_answers sa
            JOIN questions q ON sa.question_id = q.id
        """)
        all_answers_raw = cursor.fetchall()
        
        # Group answers by student_id
        from collections import defaultdict
        answers_by_student = defaultdict(list)
        answers_by_student_qid = defaultdict(dict)  # For answer_rows sheet
        
        for student_id, holland_type, answer, q_id in all_answers_raw:
            answers_by_student[student_id].append((holland_type, answer))
            answers_by_student_qid[student_id][q_id] = answer
        
        # ==========================================
        # SHEET 1: RINGKASAN & HOLLAND
        # ==========================================
        holland_data = []
        for s in students_with_results:
            s_id, name, cls, h_scores_json, anp_json, date = s
            
            # Use pre-fetched data instead of per-student query
            student_raw_ans = answers_by_student.get(s_id, [])
            
            sums = {t: 0 for t in holland_types}
            for q_type, score in student_raw_ans:
                if q_type in sums:
                    sums[q_type] += score
            
            max_score = max(sums.values()) if sums.values() else 0
            
            row = {
                'ID Siswa': s_id,
                'Nama Lengkap': name,
                'Kelas': cls,
                'Tanggal': date
            }
            # Add Holland SUMs
            for t in holland_types:
                row[f'SUM {t}'] = sums.get(t, 0)
            
            row['Max Score'] = max_score
            
            # Add Holland NORM scores
            for t in holland_types:
                row[f'NORM {t}'] = sums.get(t, 0) / max_score if max_score > 0 else 0
            
            holland_data.append(row)
        
        df_holland = pd.DataFrame(holland_data)
        df_holland.to_excel(writer, sheet_name='Perhitungan Holland', index=False)
        
        # Apply formatting to Holland sheet
        ws_h = writer.sheets['Perhitungan Holland']
        for col_num, value in enumerate(df_holland.columns.values):
            ws_h.write(0, col_num, value, header_fmt)
            ws_h.set_column(col_num, col_num, 15)

        # ==========================================
        # SHEET 2: JAWABAN SISWA
        # ==========================================
        # Matrix: Students (Rows) x Questions (Cols)
        # Use pre-fetched answers instead of per-student query
        sorted_q_ids = sorted(self.questions_map.keys())
        answer_rows = []
        for s in students_with_results:
            s_id, name, cls, _, _, _ = s
            ans_map = answers_by_student_qid.get(s_id, {})
            
            row = {'Nama Siswa': name, 'Kelas': cls}
            for q_id in sorted_q_ids:
                row[f'Q{q_id}'] = ans_map.get(q_id, 0)
            answer_rows.append(row)
            
        df_answers = pd.DataFrame(answer_rows)
        df_answers.to_excel(writer, sheet_name='Jawaban Siswa', index=False)
        ws_ans = writer.sheets['Jawaban Siswa']
        for col_num, value in enumerate(df_answers.columns.values):
            ws_ans.write(0, col_num, value, header_fmt)


        # ==========================================
        # SHEET 3: PERBANDINGAN RANKING (SIM vs ANP)
        # ==========================================
        # This will list top 5 for each student side-by-side
        import numpy as np
        
        # Pre-calc major vectors for Cosine Similarity
        major_names = list(self.majors_map.keys())
        major_profiles = np.array([[self.majors_map[m][t] for t in holland_types] for m in major_names])
        major_norms = np.linalg.norm(major_profiles, axis=1)

        ranking_rows = []
        for s in students_with_results:
            s_id, name, cls, h_scores_json, anp_json, _ = s
            h_scores = json.loads(h_scores_json)
            s_vec = np.array([h_scores.get(t, 0) for t in holland_types])
            s_norm = np.linalg.norm(s_vec)
            
            # A. Calculate Cosine Similarity for ALL majors
            sim_scores = []
            if s_norm > 0:
                for i, m_name in enumerate(major_names):
                    if major_norms[i] > 0:
                        cos_sim = np.dot(s_vec, major_profiles[i]) / (s_norm * major_norms[i])
                    else:
                        cos_sim = 0
                    sim_scores.append((m_name, float(cos_sim)))
            else:
                sim_scores = [(m, 0.0) for m in major_names]
            
            top_5_sim = sorted(sim_scores, key=lambda x: x[1], reverse=True)[:5]
            
            # B. Extract ANP ranking from JSON
            anp_data = json.loads(anp_json)
            # Handle nested structure
            anp_top_5 = []
            if 'anp_results' in anp_data and isinstance(anp_data['anp_results'], dict):
                anp_top_5 = anp_data['anp_results'].get('top_5_majors', [])
            elif 'top_5_majors' in anp_data:
                anp_top_5 = anp_data['top_5_majors']
            
            # Fill rows for top 5
            for i in range(5):
                row = {'Nama Siswa': name, 'Rank': i+1}
                
                # Similarity part
                if i < len(top_5_sim):
                    row['Jurusan (Cosine Sim)'] = top_5_sim[i][0]
                    row['Skor Sim'] = top_5_sim[i][1]
                else:
                    row['Jurusan (Cosine Sim)'] = '-'
                    row['Skor Sim'] = 0
                
                # ANP part
                if i < len(anp_top_5):
                    m_item = anp_top_5[i]
                    if isinstance(m_item, dict):
                        row['Jurusan (ANP)'] = m_item.get('major_name', '-')
                        row['Skor ANP'] = m_item.get('anp_score', 0)
                    else: # Legacy tuple format
                        row['Jurusan (ANP)'] = m_item[0]
                        row['Skor ANP'] = m_item[1].get('anp_score', 0) if isinstance(m_item[1], dict) else m_item[1]
                else:
                    row['Jurusan (ANP)'] = '-'
                    row['Skor ANP'] = 0
                
                ranking_rows.append(row)
            
        df_rankings = pd.DataFrame(ranking_rows)
        df_rankings.to_excel(writer, sheet_name='Perbandingan Top 5', index=False)
        ws_rank = writer.sheets['Perbandingan Top 5']
        for col_num, value in enumerate(df_rankings.columns.values):
            ws_rank.write(0, col_num, value, header_fmt)
            ws_rank.set_column(col_num, col_num, 20)

        # ==========================================
        # SHEET 4: MASTER DATA JURUSAN
        # ==========================================
        master_majors = []
        for m_name, profile in self.majors_map.items():
            row = {'Nama Jurusan': m_name}
            for t in holland_types:
                row[t] = profile.get(t, 0)
            master_majors.append(row)
            
        df_master = pd.DataFrame(master_majors)
        df_master.to_excel(writer, sheet_name='Master Data Jurusan', index=False)
        ws_m = writer.sheets['Master Data Jurusan']
        for col_num, value in enumerate(df_master.columns.values):
            ws_m.write(0, col_num, value, header_fmt)
            ws_m.set_column(col_num, col_num, 15)

        conn.close()
        writer.close()
        return output.getvalue()

    def generate_anp_template_excel(self):
        """
        Generates a master template Excel file with LIVE FORMULAS.
        Allows users to input scores and see the ANP calculation update automatically.
        """
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        workbook = writer.book

        # Styles
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#4472C4', 'font_color': 'white', 'border': 1, 'align': 'center'})
        sub_header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
        input_fmt = workbook.add_format({'bg_color': '#FFFFCC', 'border': 1}) # Yellow for input
        calc_fmt = workbook.add_format({'bg_color': '#E2EFDA', 'border': 1, 'num_format': '0.00'}) # Green for partial calc
        result_fmt = workbook.add_format({'bold': True, 'bg_color': '#C6E0B4', 'border': 1, 'num_format': '0.00%'}) # Darker green for result
        matrix_fmt = workbook.add_format({'border': 1, 'num_format': '0.00', 'align': 'center'})
        
        worksheet = workbook.add_worksheet('Simulasi ANP')
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:G', 12)
        worksheet.set_column('I:N', 12)
        
        # =========================================
        # SECTION 1: INPUT SCORES
        # =========================================
        worksheet.write('A1', '1. INPUT SKOR RIASEC', header_fmt)
        worksheet.merge_range('A2:G2', 'Masukkan skor raw atau hasil tes di sel berwarna kuning:', sub_header_fmt)
        
        types = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']
        
        # Headers
        for i, t in enumerate(types):
            worksheet.write(2, i+1, t[0], header_fmt)
            
        # Input Cells (Values default to 0.5)
        worksheet.write('A4', 'Skor Siswa', header_fmt)
        for i, t in enumerate(types):
            worksheet.write(3, i+1, 10, input_fmt) # Default value
            
        # Define ranges for inputs
        # B4, C4, D4, E4, F4, G4
        input_cells = [f"{chr(66+i)}4" for i in range(6)]
        
        # =========================================
        # SECTION 2: INNER DEPENDENCY (STATIC)
        # =========================================
        start_row = 6
        worksheet.write(start_row, 0, '2. INNER DEPENDENCY (Holland Hexagon)', header_fmt)
        
        # Matrix Headers
        for i, t in enumerate(types):
            worksheet.write(start_row+1, i+1, t[0], header_fmt)
            worksheet.write(start_row+2+i, 0, t, header_fmt)

        # Write Static Matrix
        holland_corr = [
            [1.00, 0.80, 0.40, 0.20, 0.40, 0.80],
            [0.80, 1.00, 0.80, 0.40, 0.20, 0.40],
            [0.40, 0.80, 1.00, 0.80, 0.40, 0.20],
            [0.20, 0.40, 0.80, 1.00, 0.80, 0.40],
            [0.40, 0.20, 0.40, 0.80, 1.00, 0.80],
            [0.80, 0.40, 0.20, 0.40, 0.80, 1.00]
        ]
        
        inner_dep_cells = []
        for r in range(6):
            row_cells = []
            for c in range(6):
                cell_ref = f"{chr(66+c)}{start_row+2+r+1}" # e.g. B9
                worksheet.write(start_row+2+r, 1+c, holland_corr[r][c], matrix_fmt)
                row_cells.append(cell_ref)
            inner_dep_cells.append(row_cells)

        # =========================================
        # SECTION 3: PAIRWISE COMPARISON (FORMULAS)
        # =========================================
        start_row = 15
        worksheet.write(start_row, 0, '3. PAIRWISE COMPARISON MATRIX (Auto-Calculated)', header_fmt)
        worksheet.merge_range(f"A{start_row+2}:G{start_row+2}", "Rumus: Jika Ratio > 1, Ratio^(1-Corr*0.3), else Ratio^(1+Corr*0.3)", sub_header_fmt)
        
        # Headers
        for i, t in enumerate(types):
            worksheet.write(start_row+2, i+1, t[0], header_fmt)
            worksheet.write(start_row+3+i, 0, t, header_fmt)
            
        # Live Formulas matrix
        pairwise_cells = []
        for r in range(6): # i
            row_refs = []
            for c in range(6): # j
                cell_loc = (start_row+3+r, 1+c)
                
                if r == c:
                    worksheet.write(cell_loc[0], cell_loc[1], 1.0, matrix_fmt)
                    row_refs.append(f"{chr(66+c)}{cell_loc[0]+1}")
                else:
                    # Logic:
                    # Score I = input_cells[r]
                    # Score J = input_cells[c]
                    # Corr = inner_dep_cells[r][c]
                    
                    score_i = input_cells[r]
                    score_j = input_cells[c]
                    corr = inner_dep_cells[r][c]
                    
                    # Safe divide formula: IF(ScoreJ=0, 9, ScoreI/ScoreJ) - simplifikasi
                    ratio_formula = f"IF({score_j}=0, 9, {score_i}/{score_j})"
                    
                    # Full Formula logic
                    # We need a complex formula string
                    # Power factor: 
                    # If Ratio > 1: Power = 1 - Corr * 0.3
                    # Else: Power = 1 + Corr * 0.3
                    
                    # Lets simplify for Excel readability:
                    # =LET(ratio, ... , power, IF(ratio>1, ...), result, ratio^power, ...)
                    # Since LET is newer Excel, let's use standard IF
                    
                    # Shorten refs
                    # Ratio R = score_i / score_j
                    
                    full_formula = (
                        f"=IF({score_j}=0, 9, "
                        f"IF({score_i}/{score_j} > 1, "
                        f"POWER({score_i}/{score_j}, 1 - {corr} * 0.3), "
                        f"POWER({score_i}/{score_j}, 1 + {corr} * 0.3)))"
                    )
                    
                    # Add bounds clipping (1/9 to 9)
                    full_formula = f"=MIN(9, MAX(1/9, {full_formula[1:]}))"
                    
                    worksheet.write_formula(cell_loc[0], cell_loc[1], full_formula, matrix_fmt)
                    row_refs.append(f"{chr(66+c)}{cell_loc[0]+1}")
            pairwise_cells.append(row_refs)

        # =========================================
        # SECTION 4: PRIORITY VECTOR (GEOMETRIC MEAN)
        # =========================================
        # Cols I, J, K
        row_header = start_row + 2
        worksheet.write(row_header, 8, "Geometric Mean", header_fmt)
        worksheet.write(row_header, 9, "Weight (Prioritas)", header_fmt)
        
        geo_mean_cells = []
        weight_cells = []
        
        start_matrix_row = start_row + 3
        
        for i in range(6):
            curr_row = start_matrix_row + i
            
            # Geometric mean formula: =GEOMEAN(B19:G19)
            range_str = f"B{curr_row+1}:G{curr_row+1}"
            gm_formula = f"=GEOMEAN({range_str})"
            
            worksheet.write_formula(curr_row, 8, gm_formula, calc_fmt)
            geo_mean_cells.append(f"I{curr_row+1}")
            
        # Sum of GM
        sum_gm_row = start_matrix_row + 6
        sum_gm_formula = f"=SUM(I{start_matrix_row+1}:I{sum_gm_row})"
        worksheet.write_formula(sum_gm_row, 8, sum_gm_formula, header_fmt)
        sum_gm_cell = f"I{sum_gm_row+1}"
        worksheet.write(sum_gm_row, 7, "TOTAL", header_fmt)

        # Calculate Weights
        for i in range(6):
            curr_row = start_matrix_row + i
            gm_cell = f"I{curr_row+1}"
            w_formula = f"={gm_cell}/{sum_gm_cell}"
            
            worksheet.write_formula(curr_row, 9, w_formula, result_fmt)
            weight_cells.append(f"J{curr_row+1}")

        # =========================================
        # SECTION 5: CONSISTENCY CHECK
        # =========================================
        start_row_cons = start_row + 10
        worksheet.write(start_row_cons, 0, '4. CONSISTENCY CHECK', header_fmt)
        
        # Calculate Weighted Sum Vector (WSV) = Matrix * Weights
        # Column K
        worksheet.write(row_header, 10, "WSV", sub_header_fmt)
        worksheet.write(row_header, 11, "Ratio (WSV/W)", sub_header_fmt)
        
        ratio_cells = []
        
        for i in range(6):
            curr_row = start_matrix_row + i
            
            # MMULT manually because standard excel MMULT is array formula and tricky in py
            # WSV_i = Sum(A_ij * W_j)
            terms = []
            for j in range(6):
                mat_cell = pairwise_cells[i][j]
                weight_cell = weight_cells[j]
                terms.append(f"({mat_cell}*{weight_cell})")
            
            wsv_formula = f"={'+'.join(terms)}"
            worksheet.write_formula(curr_row, 10, wsv_formula, calc_fmt)
            wsv_cell = f"K{curr_row+1}"
            
            # Ratio
            w_cell = weight_cells[i]
            ratio_formula = f"={wsv_cell}/{w_cell}"
            worksheet.write_formula(curr_row, 11, ratio_formula, calc_fmt)
            ratio_cells.append(f"L{curr_row+1}")

        # Lambda Max
        lmax_label_row = start_row_cons + 2
        worksheet.write(lmax_label_row, 0, "Lambda Max (Average Ratio)", sub_header_fmt)
        lmax_formula = f"=AVERAGE(L{start_matrix_row+1}:L{start_matrix_row+6})"
        worksheet.write_formula(lmax_label_row, 1, lmax_formula, calc_fmt)
        lmax_cell = f"B{lmax_label_row+1}"
        
        # CI
        worksheet.write(lmax_label_row+1, 0, "Consistency Index (CI)", sub_header_fmt)
        ci_formula = f"=({lmax_cell}-6)/5"
        worksheet.write_formula(lmax_label_row+1, 1, ci_formula, calc_fmt)
        ci_cell = f"B{lmax_label_row+2}"
        
        # RI
        worksheet.write(lmax_label_row+2, 0, "Random Index (RI, n=6)", sub_header_fmt)
        worksheet.write(lmax_label_row+2, 1, 1.24, matrix_fmt)
        ri_cell = f"B{lmax_label_row+3}"
        
        # CR
        worksheet.write(lmax_label_row+3, 0, "Consistency Ratio (CR)", header_fmt)
        cr_formula = f"={ci_cell}/{ri_cell}"
        worksheet.write_formula(lmax_label_row+3, 1, cr_formula, result_fmt)
        
        # Validity
        worksheet.write(lmax_label_row+4, 0, "Status", header_fmt)
        status_formula = f'=IF(B{lmax_label_row+4}<0.1, "KONSISTEN", "TIDAK KONSISTEN")'
        worksheet.write_formula(lmax_label_row+4, 1, status_formula, result_fmt)
        
        writer.close()
        return output.getvalue()

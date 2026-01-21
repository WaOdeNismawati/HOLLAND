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

    def generate_verification_excel(self):
        """
        Generates a multi-sheet Excel file for manual verification of calculations.
        Sheets:
        1. Reference Data (Questions, Types, Major Weights)
        2. Raw Answers (Student vs Questions Matrix)
        3. Holland Calculation (Excel Formulas for Sum & Normalization)
        4. ANP Intermediates (Pairwise, Priorities, CR from System)
        5. Final Validation (System Results vs Formula Check)
        """
        self._load_reference_data()
        
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        workbook = writer.book

        # Styles
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        num_fmt = workbook.add_format({'num_format': '0.00'})
        
        # ==========================================
        # SHEET 1: Reference Data
        # ==========================================
        # 1A. Questions
        questions_data = []
        for q_id, q_info in self.questions_map.items():
            questions_data.append({
                'Question ID': q_id,
                'Type': q_info['type'],
                'Text': q_info['text']
            })
        df_questions = pd.DataFrame(questions_data)
        df_questions.to_excel(writer, sheet_name='Reference', index=False, startrow=0)
        
        # 1B. Major Weights (beside questions or below)
        start_col_majors = 4
        writer.sheets['Reference'].write(0, start_col_majors, "Major Profiles (Weights)")
        
        majors_data = []
        for major_name, info in self.majors_map.items():
            row = {'Major': major_name}
            for type_ in ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']:
                row[type_] = info.get(type_, 0)
            majors_data.append(row)
        
        df_majors = pd.DataFrame(majors_data)
        df_majors.to_excel(writer, sheet_name='Reference', index=False, startrow=1, startcol=start_col_majors)

        # ==========================================
        # SHEET 2: Raw Answers
        # ==========================================
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get all students who completed test
        cursor.execute('''
            SELECT u.id, u.full_name, u.class_name, tr.completed_at
            FROM users u
            JOIN test_results tr ON u.id = tr.student_id
            ORDER BY u.full_name
        ''')
        students = cursor.fetchall()
        
        raw_rows = []
        holland_calc_rows = []
        anp_detail_rows = []
        
        # Map for formula generation
        sorted_q_ids = sorted(self.questions_map.keys())
        q_col_map = {} # Maps Question ID to Excel Column Letter (e.g. 1 -> E, 2 -> F...)
        
        # Columns for Raw Answers Sheet
        # A: ID, B: Name, C: Class, D: Date, E...: Q1...Qn
        
        for row_idx, student in enumerate(students):
            s_id, name, cls, date = student
            
            # Fetch Answers
            cursor.execute("SELECT question_id, answer FROM student_answers WHERE student_id = ? ORDER BY question_id", (s_id,))
            answers = dict(cursor.fetchall())
            
            # Build Row
            row_data = {
                'Student ID': s_id,
                'Name': name,
                'Class': cls,
                'Date': date
            }
            
            # Fill answers 1-5
            for q_id in sorted_q_ids:
                row_data[f"Q{q_id}"] = answers.get(q_id, 0)
            
            raw_rows.append(row_data)

        df_raw = pd.DataFrame(raw_rows)
        df_raw.to_excel(writer, sheet_name='Raw Answers', index=False)
        
        # ==========================================
        # SHEET 3: Holland Calculation (FORMULAS)
        # ==========================================
        # We will replicate the layout but populate cells with Formulas
        # R, I, A, S, E, C Sums
        
        holland_types = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']
        
        # Create headers for Calc Sheet
        calc_headers = ['Student ID', 'Name'] + [f"Sum {t}" for t in holland_types] + [f"Norm {t}" for t in holland_types] + ['Max Score']
        
        # Write headers manually
        worksheet_calc = workbook.add_worksheet('Holland Calc (Manual)')
        for col, h in enumerate(calc_headers):
            worksheet_calc.write(0, col, h, header_fmt)

        # Helper to find columns for specific types in Raw Sheet
        # Raw Sheet Cols: A(0), B(1), C(2), D(3), E(4)=Q1 ...
        # Need to know which Q columns correspond to which Type
        type_cols_indices = {t: [] for t in holland_types}
        
        # Map df_raw columns back to indices
        # df_raw columns: ID, Name, Class, Date, Q1, Q2...
        # Indices in Excel (0-based): 0, 1, 2, 3, 4...
        # So Q1 is at index 4 (Column E). Q_id matches sorted_q_ids index + 1? No, verify sorted_q_ids position.
        
        q_label_to_excel_col_idx = {}
        for idx, col_name in enumerate(df_raw.columns):
            q_label_to_excel_col_idx[col_name] = idx

        for q_id in sorted_q_ids:
            q_type = self.questions_map[q_id]['type']
            col_label = f"Q{q_id}"
            if col_label in q_label_to_excel_col_idx:
                col_idx = q_label_to_excel_col_idx[col_label]
                # Convert 0-based index to Excel Letter
                from xlsxwriter.utility import xl_col_to_name
                col_letter = xl_col_to_name(col_idx)
                type_cols_indices[q_type].append(col_letter)
        
        # Write Formulas for each student
        for i, student in enumerate(students):
            row_num = i + 1 # 1-based for data (0 is header)
            excel_row = row_num + 1 # 1-based excel row number
            
            s_id = student[0]
            name = student[1]
            
            worksheet_calc.write(row_num, 0, s_id)
            worksheet_calc.write(row_num, 1, name)
            
            # Write Sum Formulas
            # Col Indices for Sums: 2, 3, 4, 5, 6, 7
            sum_cell_refs = {}
            
            for t_idx, t in enumerate(holland_types):
                cols = type_cols_indices[t]
                # Formula: =SUM('Raw Answers'!E2, 'Raw Answers'!K2, ...)
                # Note: raw answers row matches this row (i+2)
                refs = [f"'Raw Answers'!{c}{excel_row}" for c in cols]
                formula = f"={'+'.join(refs)}"
                current_col = 2 + t_idx
                worksheet_calc.write_formula(row_num, current_col, formula)
                
                # Store ref for Max calc
                from xlsxwriter.utility import xl_rowcol_to_cell
                sum_cell_refs[t] = xl_rowcol_to_cell(row_num, current_col)

            # Max Score Column (Col 8 + 6 = 14 -> Column O)
            # The columns for sums are 2 to 7 (C to H)
            # Max score at col 14 (O) or let's put it after Sums? 
            # Headers: ID(0), Name(1), S_R(2), S_I(3), S_A(4), S_S(5), S_E(6), S_C(7)
            # Norm Starts at 8. Max Score? Let's put Max Score at 8, Norm at 9-14
            
            # Let's adjust headers slightly above? Logic:
            # Calc sum R..C (2-7). Max(2-7) at 8. Norm R..C (9-14).
            
            # Rewrite headers logic on the fly (easier loop):
            # Sums: 2,3,4,5,6,7. 
            # Max: 8
            # Norms: 9,10,11,12,13,14
             
            # Max Formula
            sum_range_start = xl_rowcol_to_cell(row_num, 2)
            sum_range_end = xl_rowcol_to_cell(row_num, 7)
            max_formula = f"=MAX({sum_range_start}:{sum_range_end})"
            worksheet_calc.write_formula(row_num, 8, max_formula)
            max_cell_ref = xl_rowcol_to_cell(row_num, 8)
            
            # Norm Formulas
            for t_idx, t in enumerate(holland_types):
                sum_cell = sum_cell_refs[t]
                # If Max is 0, avoid div/0
                norm_formula = f"=IF({max_cell_ref}=0, 0, {sum_cell}/{max_cell_ref})"
                worksheet_calc.write_formula(row_num, 9 + t_idx, norm_formula, num_fmt)

        # Fix headers for Calc sheet based on logic above
        final_headers = ['ID', 'Name'] + [f"SUM_{t[0]}" for t in holland_types] + ['MAX_SCORE'] + [f"NORM_{t[0]}" for t in holland_types]
        for col, h in enumerate(final_headers):
            worksheet_calc.write(0, col, h, header_fmt)

        # ==========================================
        # SHEET 4: ANP Intermediates (From System DB)
        # ==========================================
        # We need to parse the JSON in `test_results` to show what the system calculated
        
        cursor.execute('''
            SELECT u.full_name, tr.anp_results, tr.recommended_major
            FROM users u
            JOIN test_results tr ON u.id = tr.student_id
            ORDER BY u.full_name
        ''')
        results = cursor.fetchall()
        
        anp_rows = []
        for name, anp_json, rec_major in results:
            if not anp_json:
                continue
            
            data = json.loads(anp_json)
            # Structure varies slightly based on when it was saved, handle safely
            # Try to get calculation_details
            
            details = {}
            if 'anp_results' in data and isinstance(data['anp_results'], dict):
                 if 'calculation_details' in data['anp_results']:
                     details = data['anp_results']['calculation_details']
                 else:
                     details = data['anp_results'] # Fallback
            elif 'calculation_details' in data:
                details = data['calculation_details']
            
            # Extract Priorities
            # priorities usually in 'criteria_priorities' dict
            priorities = details.get('criteria_priorities', {})
            
            cr = details.get('consistency_ratio', 'N/A')
            is_cons = details.get('is_consistent', 'N/A')
            
            row = {
                'Name': name,
                'Rec Major': rec_major,
                'CR (Consistency)': cr,
                'Is Consistent': is_cons
            }
            
            for t in holland_types:
                row[f"Weight_{t[0]}"] = priorities.get(t, 0)
                
            anp_rows.append(row)
            
        df_anp = pd.DataFrame(anp_rows)
        df_anp.to_excel(writer, sheet_name='ANP Intermediates', index=False)
        
        # ==========================================
        # SHEET 5: Ranking Comparison
        # ==========================================
        # List top 5 majors for each student
        
        rank_rows = []
        for name, anp_json, rec_major in results:
             if not anp_json:
                continue
             data = json.loads(anp_json)
             
             # Locate top_5
             top_5 = []
             if 'anp_results' in data and isinstance(data['anp_results'], dict):
                 top_5 = data['anp_results'].get('top_5_majors', [])
             elif 'top_5_majors' in data:
                 top_5 = data['top_5_majors']
                 
             for rank, major_item in enumerate(top_5, 1):
                 m_name = major_item['major_name'] if isinstance(major_item, dict) else major_item[0]
                 m_score = major_item.get('anp_score', 0) if isinstance(major_item, dict) else 0 # Handle tuple fallback if needed
                 
                 rank_rows.append({
                     'Name': name,
                     'Rank': rank,
                     'Major': m_name,
                     'System Score': m_score
                 })
                 
        df_ranks = pd.DataFrame(rank_rows)
        df_ranks.to_excel(writer, sheet_name='Major Rankings', index=False)

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

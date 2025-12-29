# 📊 Dokumentasi Alur Perhitungan Sistem HOLLAND

## Sistem Rekomendasi Jurusan Berbasis RIASEC + Hybrid ANP

---

## 1. Arsitektur Database

### 📁 File Database: `exam_system.db` (SQLite)

```
┌─────────────────────────────────────────────────────────────────┐
│                     SKEMA DATABASE                               │
├─────────────────────────────────────────────────────────────────┤
│  users                  │  student_profiles                     │
│  ├── id (PK)           │  ├── id (PK)                          │
│  ├── username          │  ├── user_id (FK → users.id)          │
│  ├── password (hash)   │  ├── student_id                       │
│  ├── role              │  ├── first_name                       │
│  ├── full_name         │  ├── last_name                        │
│  ├── class_name        │  └── enrollment_date                  │
│  └── email             │                                        │
├─────────────────────────────────────────────────────────────────┤
│  questions              │  majors                                │
│  ├── id (PK)           │  ├── id (PK)                          │
│  ├── question_text     │  ├── Major (nama jurusan)             │
│  └── holland_type      │  ├── Realistic (0-1)                  │
│      (R/I/A/S/E/C)     │  ├── Investigative (0-1)              │
│                         │  ├── Artistic (0-1)                   │
│                         │  ├── Social (0-1)                     │
│                         │  ├── Enterprising (0-1)               │
│                         │  └── Conventional (0-1)               │
├─────────────────────────────────────────────────────────────────┤
│  student_answers        │  test_results                         │
│  ├── id (PK)           │  ├── id (PK)                          │
│  ├── student_id (FK)   │  ├── student_id (FK, UNIQUE)          │
│  ├── question_id (FK)  │  ├── holland_scores (JSON)            │
│  ├── answer (1-5)      │  ├── anp_results (JSON)               │
│  ├── response_time     │  ├── top_3_types (JSON)               │
│  └── question_order    │  ├── recommended_major                │
│                         │  ├── total_items                      │
│                         │  └── completed_at                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Alur Perhitungan Lengkap

### FASE 1: Login & Validasi

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  User Input │ --> │  Autentikasi│ --> │  Session    │
│  (form)     │     │  (bcrypt)   │     │  State      │
└─────────────┘     └─────────────┘     └─────────────┘
```

**File:** `app.py`, `utils/auth.py`

**Proses:**
1. User input username & password
2. Query database: `SELECT * FROM users WHERE username = ?`
3. Verifikasi password: `bcrypt.checkpw(password, stored_hash)`
4. Jika valid → set `st.session_state` (logged_in, user_id, role, dll)
5. Redirect berdasarkan role (admin/student)

---

### FASE 2: Pengerjaan Tes (18 Soal RIASEC)

**File:** `pages/student_test.py`, `services/cat_engine.py`

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Load Soal  │ --> │  Tampilkan  │ --> │  Simpan     │
│  (CAT)      │     │  Pertanyaan │     │  Jawaban    │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Proses:**
1. **Initialize CAT Engine** dengan parameter:
   - `min_items=18` (minimal 18 soal)
   - `max_items=None` (semua soal)
   - `target_se=0.35`

2. **Untuk setiap soal:**
   ```python
   # Tampilkan soal
   question = engine.get_question(question_id)
   
   # User menjawab (skala Likert 1-5)
   answer_value = st.radio(options=[1,2,3,4,5])
   
   # Simpan ke session
   session_state['answers'].append({
       'question_id': question_id,
       'answer': answer_value,
       'question_order': order,
       'response_time': response_time
   })
   ```

3. **Penyimpanan ke Database:**
   ```sql
   INSERT INTO student_answers 
   (student_id, question_id, answer, question_order, response_time)
   VALUES (?, ?, ?, ?, ?)
   ```

---

### FASE 3: Perhitungan Skor RIASEC

**File:** `utils/holland_calculator.py` → `calculate_holland_scores()`

```python
# 1. Ambil semua jawaban siswa
cursor.execute('''
    SELECT q.holland_type, sa.answer
    FROM student_answers sa
    JOIN questions q ON sa.question_id = q.id
    WHERE sa.student_id = ?
''', (student_id,))

# 2. Hitung total per tipe
scores = {h: 0 for h in ['R', 'I', 'A', 'S', 'E', 'C']}
for holland_type, answer in answers:
    scores[holland_type] += answer

# 3. Normalisasi ke rentang 0-1
max_score = max(scores.values())
normalized = {k: v / max_score for k, v in scores.items()}
```

**Contoh Output:**
| Tipe | Skor Mentah | Normalized |
|------|-------------|------------|
| Realistic | 12 | 0.600 |
| Investigative | 20 | 1.000 |
| Artistic | 8 | 0.400 |
| Social | 15 | 0.750 |
| Enterprising | 10 | 0.500 |
| Conventional | 18 | 0.900 |

---

### FASE 4: Identifikasi Holland Code

**File:** `utils/holland_calculator.py` → `get_holland_code()`

```python
# Urutkan berdasarkan skor tertinggi
sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
top_3 = [t[0] for t in sorted_types[:3]]

# Konversi ke kode 3 huruf
code_map = {
    'Realistic': 'R', 'Investigative': 'I', 'Artistic': 'A',
    'Social': 'S', 'Enterprising': 'E', 'Conventional': 'C'
}
holland_code = ''.join([code_map[t] for t in top_3])  # Contoh: "ICR"
```

---

### FASE 5: Hybrid ANP Ranking

**File:** `utils/anp.py` → `calculate_hybrid_ranking()`

#### STEP 5.1: Build Pairwise Comparison Matrix

```python
# Matriks 6x6 berdasarkan rasio skor RIASEC
for i in range(6):
    for j in range(i+1, 6):
        ratio = score[i] / score[j]
        ratio = np.clip(ratio, 1/9, 9)  # Clip ke skala Saaty
        matrix[i,j] = ratio
        matrix[j,i] = 1 / ratio
```

**Contoh Pairwise Matrix:**
```
        R     I     A     S     E     C
R    [1.00, 0.60, 1.50, 0.80, 1.20, 0.67]
I    [1.67, 1.00, 2.50, 1.33, 2.00, 1.11]
A    [0.67, 0.40, 1.00, 0.53, 0.80, 0.44]
S    [1.25, 0.75, 1.88, 1.00, 1.50, 0.83]
E    [0.83, 0.50, 1.25, 0.67, 1.00, 0.56]
C    [1.50, 0.90, 2.25, 1.20, 1.80, 1.00]
```

#### STEP 5.2: Hitung Bobot Kriteria (Eigenvalue Method)

```python
eigenvalues, eigenvectors = scipy.linalg.eig(pairwise_matrix)
max_idx = np.argmax(eigenvalues.real)
principal_eigenvector = eigenvectors[:, max_idx].real
criteria_priorities = principal_eigenvector / sum(principal_eigenvector)
```

**Output Bobot Kriteria:**
| Kriteria | Bobot |
|----------|-------|
| R | 0.12 |
| I | 0.25 |
| A | 0.08 |
| S | 0.18 |
| E | 0.10 |
| C | 0.27 |

#### STEP 5.3: Hitung Weighted Score per Jurusan

```python
for major, profile in majors.items():
    weighted_score = sum(
        criteria_priorities[i] * profile[criterion] * student_score[criterion]
        for i, criterion in enumerate(['R','I','A','S','E','C'])
    )
```

**Formula:**
```
Weighted Score = Σ (Bobot_ANP × Profil_Jurusan × Skor_Siswa)
```

#### STEP 5.4: Hitung Cosine Similarity

```python
student_vector = [student_score[c] for c in RIASEC]
major_vector = [major_profile[c] for c in RIASEC]

similarity = dot(student_vector, major_vector) / (||student|| × ||major||)
```

#### STEP 5.5: Hybrid Score (Final)

```python
hybrid_score = 0.8 * weighted_score + 0.2 * similarity
```

**Contoh Perhitungan untuk 1 Jurusan (Teknik Informatika):**

| Kriteria | Bobot ANP | Profil Jurusan | Skor Siswa | Kontribusi |
|----------|-----------|----------------|------------|------------|
| R | 0.12 | 0.70 | 0.60 | 0.0504 |
| I | 0.25 | 0.90 | 1.00 | 0.2250 |
| A | 0.08 | 0.30 | 0.40 | 0.0096 |
| S | 0.18 | 0.40 | 0.75 | 0.0540 |
| E | 0.10 | 0.50 | 0.50 | 0.0250 |
| C | 0.27 | 0.80 | 0.90 | 0.1944 |

**Weighted Score:** 0.5584  
**Cosine Similarity:** 0.89  
**Hybrid Score:** 0.8 × 0.5584 + 0.2 × 0.89 = **0.6247**

---

### FASE 6: Penyimpanan Hasil ke Database

**File:** `utils/holland_calculator.py` → `save_test_result()`

```python
# Hapus hasil lama (jika ada)
cursor.execute('DELETE FROM test_results WHERE student_id = ?', (student_id,))

# Simpan hasil baru
cursor.execute('''
    INSERT INTO test_results (
        student_id, 
        top_3_types,           -- JSON: ["Investigative", "Conventional", "Realistic"]
        recommended_major,      -- String: "Teknik Informatika"
        holland_scores,         -- JSON: {"R": 0.6, "I": 1.0, ...}
        anp_results,           -- JSON: {ranked_majors: [...], calculation_details: {...}}
        total_items,           -- Integer: 18
        completed_at           -- Timestamp
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
''', (
    student_id,
    json.dumps(top_3_types),
    recommended_major,
    json.dumps(scores),
    json.dumps(anp_results),
    total_items,
    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
))
```

**Struktur JSON `anp_results`:**
```json
{
  "ranked_majors": [
    ["Teknik Informatika", {"hybrid_score": 0.6247, "weighted_score": 0.5584, "similarity": 0.89}],
    ["Sistem Informasi", {"hybrid_score": 0.5832, ...}],
    ...
  ],
  "student_riasec_profile": {"R": 0.6, "I": 1.0, "A": 0.4, "S": 0.75, "E": 0.5, "C": 0.9},
  "methodology": "Hybrid (ANP Criteria Weighting + Weighted Scoring)",
  "calculation_details": {
    "pairwise_matrix": [[1.0, 0.6, ...], ...],
    "criteria_priorities": {"R": 0.12, "I": 0.25, ...}
  }
}
```

---

## 3. Diagram Alur Lengkap

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         ALUR SISTEM HOLLAND                               │
└──────────────────────────────────────────────────────────────────────────┘

     ┌─────────┐
     │  LOGIN  │
     └────┬────┘
          │
          ▼
┌─────────────────┐    ┌─────────────────┐
│  Cek Role       │───▶│  student_test   │
│  (student?)     │    │  .py            │
└─────────────────┘    └────────┬────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  FASE TES: 18 Soal RIASEC                                                 │
│                                                                           │
│  for soal in questions:                                                   │
│      ├── Tampilkan pertanyaan                                             │
│      ├── User jawab (1-5)                                                 │
│      └── INSERT INTO student_answers (student_id, question_id, answer)    │
└───────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  FASE PERHITUNGAN: holland_calculator.py                                  │
│                                                                           │
│  1. calculate_holland_scores()                                            │
│     └── SELECT SUM(answer) GROUP BY holland_type                          │
│     └── Normalize ke 0-1                                                  │
│                                                                           │
│  2. get_holland_code()                                                    │
│     └── Top 3 tipe → "ICR"                                                │
│                                                                           │
│  3. calculate_hybrid_ranking() [anp.py]                                   │
│     ├── Build pairwise matrix (6x6)                                       │
│     ├── Eigenvalue method → criteria_priorities                           │
│     ├── Weighted score per jurusan                                        │
│     ├── Cosine similarity per jurusan                                     │
│     └── Hybrid score = 0.8*weighted + 0.2*similarity                      │
│                                                                           │
│  4. save_test_result()                                                    │
│     └── INSERT INTO test_results (holland_scores, anp_results, ...)       │
└───────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  FASE HASIL: student_results.py                                           │
│                                                                           │
│  SELECT holland_scores, anp_results, top_3_types, recommended_major       │
│  FROM test_results WHERE student_id = ?                                   │
│                                                                           │
│  Tampilkan:                                                               │
│    ├── Rekomendasi jurusan terbaik                                        │
│    ├── 3 tipe kepribadian teratas                                         │
│    ├── Grafik radar RIASEC                                                │
│    ├── Bobot kriteria ANP                                                 │
│    └── Ranking 20 jurusan dengan hybrid score                             │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Ringkasan Formula

| Komponen | Formula |
|----------|---------|
| **Normalisasi Skor** | `score_norm = score_raw / max(scores)` |
| **Pairwise Ratio** | `ratio = score[i] / score[j]` (clip ke 1/9 - 9) |
| **Bobot Kriteria** | Eigenvalue method dari pairwise matrix |
| **Weighted Score** | `Σ (bobot × profil_jurusan × skor_siswa)` |
| **Cosine Similarity** | `dot(A,B) / (||A|| × ||B||)` |
| **Hybrid Score** | `0.8 × weighted + 0.2 × similarity` |

---

## 5. File-file Terkait

| File | Fungsi |
|------|--------|
| `app.py` | Entry point, login handler |
| `utils/auth.py` | Autentikasi, session management |
| `pages/student_test.py` | UI tes, penyimpanan jawaban |
| `services/cat_engine.py` | CAT algorithm untuk pemilihan soal |
| `utils/holland_calculator.py` | Koordinator perhitungan |
| `utils/anp.py` | Hybrid ANP calculation |
| `pages/student_results.py` | Tampilan hasil tes |
| `database/db_manager.py` | Database connection manager |
| `database/exame_system.py` | Schema & migrations |


# Analisis Mekanisme Tes Minat Bakat (Student Test)

Berikut adalah analisis teknis dari alur tes minat bakat pada sistem HOLLAND, berdasarkan pemeriksaan kode `pages/student_test.py`, `services/cat_engine.py`, dan `utils/holland_calculator.py`.

## 1. Deskripsi Alur (Narrative)

Sequence diagram tes minat bakat menggambarkan interaksi berurutan antara siswa dan komponen sistem selama pelaksanaan asesmen. Proses dimulai ketika siswa mengakses menu tes, dimana **Test UI** akan meminta **Test Engine** untuk menginisialisasi sesi baru. **Test Engine** kemudian mengambil seluruh bank soal dari **Database**, mengacak urutannya, dan mempersiapkan state sesi.

Setelah inisialisasi, tes dimulai. **Test UI** meminta soal aktif saat ini dari **Test Engine**, menampilkannya ke layar, dan menunggu input siswa. Ketika siswa memilih jawaban dan menekan tombol "Jawab", data jawaban (skor 1-5 dan waktu respon) dikirim kembali ke **Test Engine** untuk disimpan sementara dalam sesi. **Test Engine** kemudian memilih soal berikutnya secara acak dari antrian. Siklus *display-answer-next* ini berulang terus menerus hingga seluruh soal terjawab.

Setelah soal terakhir diselesaikan, sistem memicu proses finalisasi. **Test UI** mengirimkan sinyal penyelesaian ke **Holland Calculator**. Calculator pertama-tama menyimpan seluruh jawaban siswa secara permanen ke **Database**. Kemudian, Calculator menghitung profil RIASEC siswa, menjalankan algoritma rekomendasi (filter *Cosine Similarity* dilanjut dengan *Analytic Network Process* / ANP), dan akhirnya menyimpan hasil lengkap (skor, kode Holland, dan rekomendasi jurusan) ke tabel `test_results`. Terakhir, **Test UI** menampilkan ringkasan hasil kepada siswa dan membuka akses ke laporan lengkap.

---

## 2. Alur Proses (Detail Langkah)

1.  **Start / Inisialisasi**:
    - User membuka `pages/student_test.py`.
    - UI memanggil `engine.initialize_session(student_id)`.
    - Engine query ke DB (`SELECT id, question_text...`) untuk memuat bank soal.
    - Engine mengacak urutan soal (`random.shuffle`) dan membuat session object.

2.  **Pengerjaan Tes (Looping)**:
    - **Get Question**: UI meminta data soal berdasarkan `current_question_id`.
    - **Display**: Soal ditampilkan dengan Radio Button (1-5).
    - **Submit**: User klik "Jawab & Lanjut".
    - **Update Session**: UI memanggil `_handle_answer_submission`:
        - Jawaban disimpan di `st.session_state['answers']`.
        - `engine.select_next_question()` dipanggil untuk mendapatkan ID soal berikutnya.
        - UI melakukan `st.rerun()`.

3.  **Finalisasi & Perhitungan**:
    - Jika soal habis (`completed=True`), tombol "Selesaikan Tes" muncul.
    - User/Auto trigger `_finalize_test()`.
    - **Persist Answers**: `_persist_answers()` menyimpan batch jawaban ke tabel `student_answers`.
    - **Process Logic**: Panggil `HollandCalculator.process_test_completion()`.
        - **Reading**: Query jawaban dari DB untuk verifikasi.
        - **Calculation**: Hitung skor RIASEC (R, I, A, S, E, C).
        - **ANP**: `ANPProcessor` melakukan filtering jurusan & ranking.
    - **Save Results**: Hasil akhir disimpan ke tabel `test_results`.

4.  **Output**:
    - UI menampilkan Kode Holland (misal: "RIA") dan Top Jurusan.

---

## 3. Prompt Sequence Diagram (Format Khusus)

Gunakan prompt berikut untuk men-generate diagram. Kode icon menggunakan Material Design Icons (Hex).

**Prompt:**

```text
Buatkan Sequence Diagram untuk alur Tes Minat Bakat dengan syntax khusus berikut.

**Syntax Guidelines:**
- Gunakan `bottomparticipants`
- Gunakan icon `materialdesignicons`:
  - UI: e141 (Monitor/Desktop)
  - Engine: e8b8 (Settings/Cog - representasi Logic)
  - Calc: e1e2 (Calculator - representasi Scoring)
  - DB: e1db (Storage/Database)
- `actor Student`

**Alur Sequence:**
1. Student ke UI: Buka Halaman Tes.
2. UI ke Engine: initialize_session().
3. Engine ke DB: SELECT questions (Load Bank Soal).
4. DB ke Engine: Return List Soal.
5. Engine ke UI: Return Session (Randomized Order).
6. **Loop Pengerjaan:**
    - UI ke Student: Tampilkan Soal (get_question).
    - Student ke UI: Input Jawaban & Submit.
    - UI ke UI: Simpan Jawaban ke State.
    - UI ke Engine: select_next_question().
    - Engine ke UI: Return Next ID.
7. **Selesai:**
    - UI ke DB: INSERT student_answers (Batch).
    - UI ke Calc: process_test_completion().
    - Calc ke DB: SELECT answers (Validasi).
    - DB ke Calc: Return Data Jawaban.
    - Calc ke Calc: Hitung RIASEC & ANP Ranking.
    - Calc ke DB: INSERT test_results.
    - Calc ke UI: Return Final Result.
    - UI ke Student: Tampilkan Hasil & Rekomendasi.

**Output Code:**
Berikan kode diagramnya saja dalam blok code yang rapi.
```

---

## 4. Hasil Diagram (Syntax Sequencediagram.org)

```text
bottomparticipants

actor Student
materialdesignicons e141 "Test UI" as UI
materialdesignicons e8b8 "Test Engine" as Engine
materialdesignicons e1e2 "Holland\nCalculator" as Calc
materialdesignicons e1db "Database" as DB

Student->UI:Buka Halaman Tes
UI->Engine:initialize_session()
Engine->DB:SELECT questions
DB->Engine:Return Question Bank

Engine->Engine:Randomize Order
Engine->UI:Return Test Session

loop Pengerjaan Soal (60x)
    UI->Student:Tampilkan Soal n
    Student->UI:Pilih Jawaban & Submit
    
    UI->UI:Simpan Jawaban (State)
    UI->Engine:select_next_question()
    
    alt Ada Soal Berikutnya
        Engine->UI:Return Next Question ID
        UI->UI:Rerun Page
    else Soal Habis
        Engine->UI:Return None (Completed)
    end
end

note over UI:Finalisasi Tes

UI->DB:INSERT student_answers (Batch)
UI->Calc:process_test_completion()

Calc->DB:SELECT student_answers
DB->Calc:Return Answers Data

Calc->Calc:Calculate RIASEC Scores
Calc->Calc:Run ANP & Similarity

Calc->DB:INSERT test_results
Calc->UI:Return Final Results (Success)

UI->Student:Tampilkan Hasil & Rekomendasi
```

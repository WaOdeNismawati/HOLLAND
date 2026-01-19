# Dokumentasi Skema Database & Analisis ERD

Dokumen ini menjelaskan struktur database sistem saat ini (`exam_system.db`) dan hubungannya dengan desain ERD awal.

## 1. Relasi Antar Entitas (Relationships)

Berdasarkan ERD dan implementasi sistem, berikut adalah penjelasan detail mengenai bagaimana data saling terhubung:

### A. Pengguna (Users) ↔ Jawaban (Answers)
*   **Jenis Relasi**: *One-to-Many* (1:M)
*   **Penjelasan**:
    *   **Satu** siswa dapat memiliki **Banyak** baris jawaban.
    *   Setiap baris di tabel `student_answers` adalah jawaban untuk satu soal spesifik.
*   **Implementasi**: Kolom `student_id` pada tabel `student_answers` merujuk ke `id` pada tabel `users`.

### B. Pertanyaan (Questions) ↔ Jawaban (Answers)
*   **Jenis Relasi**: *One-to-Many* (1:M)
*   **Penjelasan**:
    *   **Satu** soal pertanyaan akan muncul di **Banyak** lembar jawaban (dijawab oleh banyak siswa).
    *   Artinya, `id_pertanyaan` yang sama akan berulang kali muncul di tabel jawaban untuk siswa yang berbeda-beda.
*   **Implementasi**: Kolom `question_id` pada tabel `student_answers` merujuk ke `id` pada tabel `questions`.

### C. Pengguna (Users) ↔ Hasil Tes (Test Results)
*   **Jenis Relasi**: *One-to-One* (1:1) atau *One-to-Many* (1:M)
*   **Penjelasan**:
    *   Setiap siswa memiliki riwayat hasil tes. Dalam sistem saat ini, siswa bisa melakukan tes ulang, sehingga satu siswa bisa memiliki banyak riwayat hasil.
    *   Namun, untuk setiap sesi tes, satu siswa menghasilkan **Satu** set hasil akhir (Skor Holland & Rekomendasi).
*   **Implementasi**: Kolom `student_id` pada tabel `test_results` merujuk ke `id` pada tabel `users`.

### D. Hasil Tes ↔ Jurusan (Majors)
*   **Jenis Relasi**: *Logis / Referensial*
*   **Penjelasan**:
    *   Hasil tes merekomendasikan sebuah jurusan.
    *   Sistem mencocokkan profil skor siswa dengan profil bobot jurusan di tabel `majors` menggunakan algoritma ANP & Euclidean Distance.
*   **Implementasi**: Kolom `recommended_major` pada `test_results` menyimpan nama jurusan yang ada di tabel `majors`.

---

## 2. Struktur Tabel & Atribut

Berikut adalah representasi visual dari kode database kita yang sesuai dengan ERD:

### Tabel: `users` (Pengguna)
Menyimpan data otentikasi.
| Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | INTEGER (PK) | ID Unik Pengguna |
| `username` | TEXT | Email/Nomor Identitas |
| `password` | TEXT | Kata sandi terenkripsi |
| `role` | TEXT | 'admin' atau 'student' |
| `full_name` | TEXT | Nama Lengkap |
| `class_name` | TEXT | Kelas (misal: XII IPA 1) |

### Tabel: `questions` (Pertanyaan)
Bank soal tes Holland.
| Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | INTEGER (PK) | ID Soal |
| `question_text`| TEXT | Teks Pertanyaan |
| `holland_type` | TEXT | Tipe: R, I, A, S, E, atau C |

### Tabel: `student_answers` (Jawaban)
Tabel perantara (Junction) yang menyimpan respon siswa.
| Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | INTEGER (PK) | ID Transaksi Jawaban |
| `student_id` | INTEGER (FK)| Milik Siapa? (Ref: users.id) |
| `question_id` | INTEGER (FK)| Soal Apa? (Ref: questions.id) |
| `answer` | INTEGER | Skala 1-5 (Sangat Tidak Suka - Sangat Suka) |

### Tabel: `majors` (Jurusan)
Basis pengetahuan untuk sistem pendukung keputusan.
| Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | INTEGER (PK) | ID Jurusan |
| `Major` | TEXT | Nama Jurusan (misal: Teknik Informatika) |
| `Realistic` | REAL | Bobot Tipe R (0.0 - 1.0) |
| `Investigative`| REAL | Bobot Tipe I (0.0 - 1.0) |
| `...` | ... | (Bobot tipe lainnya A, S, E, C) |

### Tabel: `test_results` (Hasil Tes)
Menyimpan hasil perhitungan akhir.
| Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | INTEGER (PK) | ID Laporan |
| `student_id` | INTEGER (FK)| Milik Siapa? |
| `holland_scores`| TEXT (JSON) | Skor mentah siswa (R:0.8, I:0.5, ...) |
| `top_3_types` | TEXT (JSON) | 3 Kode teratas (misal: ["I", "R", "S"]) |
| `recommended_major`| TEXT | Hasil rekomendasi akhir |
| `completed_at` | DATETIME | Waktu pengerjaan |

---

## 3. Kesimpulan Analisis

**ERD yang Anda berikan valid.**
Relasi "Many-to-Many" antara **Pengguna** dan **Pertanyaan** dipecah dengan benar menjadi dua relasi "One-to-Many" melalui tabel **Jawaban**.

*   `Pengguna` 1 ---- M `Jawaban`
*   `Pertanyaan` 1 ---- M `Jawaban`

Ini memungkinkan sistem mencatat jawaban spesifik setiap siswa untuk setiap soal tanpa duplikasi data pertanyaan.

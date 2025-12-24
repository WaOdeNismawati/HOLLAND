# Assets Folder

Folder ini digunakan untuk menyimpan file-file asset seperti logo, gambar, dan icon.

## Cara Menambahkan Logo di Sidebar

1. **Letakkan file logo Anda di folder ini** dengan nama `logo.png` (atau format lain: jpg, svg, dll)

2. **Buka file** `components/sidebar.py`

3. **Uncomment salah satu opsi** di bagian LOGO (sekitar baris 109-118):

   ### Option 1: Logo dari file lokal
   ```python
   st.image("assets/logo.png", use_container_width=True)
   ```

   ### Option 2: Logo dari URL
   ```python
   st.image("https://example.com/logo.png", use_container_width=True)
   ```

   ### Option 3: Logo dengan ukuran custom
   ```python
   import os
   if os.path.exists("assets/logo.png"):
       st.image("assets/logo.png", width=150)
   ```

4. **Save dan restart aplikasi** untuk melihat perubahannya

## Format Logo yang Disarankan

- **Format:** PNG (dengan background transparan lebih bagus)
- **Ukuran:** 200-400px width untuk hasil optimal
- **Rasio:** Square (1:1) atau landscape (16:9)

## Contoh Struktur File

```
assets/
├── logo.png          # Logo utama
├── logo-dark.png     # Logo untuk dark mode (opsional)
├── favicon.ico       # Icon untuk browser tab (opsional)
└── README.md         # File ini
```

## Tips

- Gunakan logo dengan background transparan (PNG) agar terlihat lebih professional
- Logo akan otomatis di-center di sidebar
- Styling sudah include border-radius untuk sudut yang membulat
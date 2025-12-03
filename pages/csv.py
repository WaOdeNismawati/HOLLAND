import pandas as pd
from datetime import datetime

# Data siswa
data = {
    'ID': [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010,
           1011, 1012, 1013, 1014, 1015, 1016, 1017, 1018, 1019, 1020,
           1021, 1022, 1023, 1024, 1025, 1026, 1027, 1028, 1029, 1030,
           1031, 1032, 1033, 1034, 1035, 1036, 1037, 1038, 1039, 1040,
           1041, 1042, 1043, 1044, 1045, 1046, 1047, 1048, 1049, 1050,
           1051, 1052, 1053, 1054, 1055, 1056, 1057, 1058, 1059, 1060,
           4, 2],
    'Username': [
        'gustayulasischa@gmail.com', 'elmyalvinaantika@gmail.com', 'gayatridhivya08@gmail.com',
        'vingkaalestarii@gmail.com', 'tenriroswana@gmail.com', 'aprilianurnur9@gmail.com',
        'ymuh75107@gmail.com', 'laurajessyca9@gmail.com', 'craylenneaurellia@gmail.com',
        'iraindriani022@gmail.com', 'rintanjuliono@gmail.com', 'iluhviana229@gmail.com',
        'kadekayhu09@gmail.com', 'santisariyaning@gmail.com', 'anggakomang241@gmail.com',
        'sarimeirypurnama@gmail.com', 'novinaila067@gmail.com', 'arjunefrasetiawan@gmail.com',
        'fadelstart107@gmail.com', 'marningsih137@gmail.com', 'nonirizkiati@gmail.com',
        'dewisasatiara8@gmail.com', 'auliaaulll933@gmail.com', 'elsaramadani102006@gmail.com',
        'anugrahdesty77@gmail.com', 'guntiayudinda@gmail.com', 'arahdwiangeliaaa@gmail.com',
        'ichalisa895@gmail.com', 'aryaramdhan0002@gmail.com', 'atmaarifa20@gmail.com',
        'dedileonurcahyadi@gmail.com', 'mrtelaso585@gmail.com', 'triaulia385@gmail.com',
        'kadekputra000041@gmail.com', 'yuliaasarii96@gmail.com', 'kumalaputri9418@gmail.com',
        'rar825943@gmail.com', 'adzraramli0@gmail.com', 'juwitafujiantari@gmail.com',
        'melanimelani966@gmail.com', 'gustynyomankartini@gmail.com', 'arifatr58@gmail.com',
        'yunita00006@gmail.com', 'sbrinalifya@gmail.com', 'ameliaa0323@gmail.com',
        'opik75747@gmail.com', 'mdwarsana716@gmail.com', 'alwansyawal007@gmail.com',
        'yasinyakhras@gmail.com', 'keycharamadani1@gmail.com', 'graclyaefry05@gmail.com',
        'musdalifahdali330@gmail.com', 'dewiyantikadek845@gmail.com', 'dewaayusemadipuspagayatri@gmail.com',
        'lalaratnakomala4@gmail.com', 'gustiayusriwidari30@gmail.com', 'nurlailihasanah461@gmail.com',
        'putrireskianingsi@gmail.com', 'sariiinandacitra@gmail.com', 'keturdarma66@gmail.com',
        'siswa3', 'student1'
    ],
    'Nama Lengkap': [
        'GUSTI AYUL ASISCHA', 'Elmy alvina antima', 'Dhivya gayatri pradnyaputri',
        'VINGKA LESTARI', 'Izatil Nuril Ahwa', 'Aprilia nur',
        'Muh.yusuf', 'Laura jessyca', 'Ceissya Raylenne Aurellia',
        'IRA INDRIYANI', 'LEO ADRIANSYAH', 'ILUH VIANA',
        'NI MADE AYU FATMAWATI', 'Komang santi Sariyaning', 'KOMANG ANGGA DEWI',
        'Putu Meiry Purnama Sari', 'naila novianti ilham', 'ARJUN EFRA SETIAWAN',
        'Fadel Ardan Maulana', 'Ni komang Marningsih', 'Noni Rizkiati',
        'Dewi Sasatiara', 'Safni yulianti', 'Elsa ramadani',
        'Desty Anugrah', 'gusti ayu dinda dwi lestari', 'Arah Dwi Angelia',
        'Lisa juliana', 'ARYA RAMADHAN', 'Atma Arifa',
        'Dedi leo nurcahyadi', 'Siti nur Halizah', 'Aulia TriNindia',
        'KADEK PUTRA SUSTIADI', 'Yuliasari', 'Ayu Kumala Putri Sudewa',
        'mutiara Syamsuddin', 'adzra Dzakiyah Ramli', 'Juwita Fujiantari',
        'Luh Melani Aulia', 'Gusti Nyoman Kartini', 'REHAN ARIFAT',
        'Wahyunita saputri', 'Sabrina Alifya', 'AMELIA',
        'Taufik Hidayat', 'Made sawitriani', 'ALWAN SYAWAL',
        'Yasin Yakhras', 'Keycha ramadani', 'Dhina Ramadhani',
        'Musdalifah', 'Kadek Dewi Yanti', 'Dewa Ayu Semadi Puspa Gayatri',
        'Lala Ratna Komala', 'Gusti Ayu Sri Widari', 'NUR LAILI HASANAH',
        'Putri Reskia Ningsih', 'NANDA CITRA SARY', 'Kade Aril Setiawan',
        'contih', 'Siswa Contoh'
    ],
    'Kelas': ['XII IPA II'] * 60 + ['XII IPA II', 'XII IPA 1'],
    'Tanggal Daftar': ['2025-11-04 20:06:35.787714+08:00'] * 60 + ['2025-10-06 11:23:36', '2025-09-20 17:33:15'],
    'Status Tes': ['Belum'] * 60 + ['Sudah', 'Belum']
}

# Membuat DataFrame
df = pd.DataFrame(data)

# Menyimpan ke Excel dengan formatting
output_file = 'data_siswa.xlsx'

with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
    df.to_excel(writer, sheet_name='Data Siswa', index=False)
    
    # Mendapatkan workbook dan worksheet objects
    workbook = writer.book
    worksheet = writer.sheets['Data Siswa']
    
    # Menambahkan format untuk header
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#4472C4',
        'font_color': 'white',
        'border': 1
    })
    
    # Menulis header dengan format
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)
    
    # Mengatur lebar kolom
    worksheet.set_column('A:A', 8)   # ID
    worksheet.set_column('B:B', 35)  # Username
    worksheet.set_column('C:C', 35)  # Nama Lengkap
    worksheet.set_column('D:D', 12)  # Kelas
    worksheet.set_column('E:E', 25)  # Tanggal Daftar
    worksheet.set_column('F:F', 12)  # Status Tes

print(f"✅ File Excel berhasil dibuat: {output_file}")
print(f"📊 Total siswa: {len(df)} siswa")
print(f"📝 Kolom: {', '.join(df.columns.tolist())}")

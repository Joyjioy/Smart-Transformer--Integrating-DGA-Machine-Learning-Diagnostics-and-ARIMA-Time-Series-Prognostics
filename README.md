# Smart Transformer: Integrasi Diagnostik ML DGA dan Prognosis Time Series ARIMA

## Spesifikasi Teknis Digital Twin MVP

Dokumen ini menjelaskan arsitektur, dasar matematis, dan logika implementasi sistem Digital Twin MVP untuk pemantauan kesehatan transformator daya utama. Ditulis untuk pengembang sistem, manajemen aset, dan penelaah akademik.

---

## 1. Ringkasan Proyek dan Rumusan Masalah

### 1.1 Latar Belakang

Transformator daya utama menuntut keandalan operasional yang tinggi. Kegagalan pada aset ini berdampak pada pemadaman tidak terencana, kerusakan infrastruktur, dan kerugian finansial. Pemeliharaan prediktif berbasis kondisi minyak isolasi sudah menjadi standar industri untuk memitigasi risiko tersebut.

### 1.2 Rumusan Masalah

- **Asinkronisasi data.** Sampel Dissolved Gas Analysis (DGA) dipantau rutin karena mudah diekstraksi. Parameter Oil Analysis (OA) seperti Breakdown Voltage (BDV), Acidity, dan Interfacial Tension (IFT) bergantung pada uji laboratorium pihak ketiga dengan siklus 6-12 bulan. Akibatnya, data sulit difusikan pada satu timestamp yang sama.
- **Kesalahan meramal parameter fisik.** Memaksa model time-series meramal nilai fisik minyak (kadar asam, penurunan BDV) murni berdasarkan waktu, tanpa data temperatur hot-spot dan pembebanan dinamis, adalah kesalahan pendekatan. Parameter OA terdegradasi secara kumulatif akibat stres operasional yang tidak teratur, bukan secara linier terhadap waktu.
- **RUL berbasis oli tidak mencerminkan umur aset.** Mengukur Remaining Useful Life (RUL) trafo hanya dari indikator oli menyesatkan, karena karakteristik oli bisa dipulihkan lewat purifikasi/filtrasi. Umur sejati transformator melekat pada kekuatan mekanis kertas isolasi selulosa pembungkus belitan tembaga, yang bersifat permanen dan tidak dapat diperbarui.

### 1.3 Solusi

Sistem ini membangun dashboard Digital Twin di Power BI yang terintegrasi dengan prognostic engine Python (ARIMA + Random Forest Multiclass). Tiga pilar utama:

1. **Reality Anchor Gatekeeper** — membekukan nilai parameter OA terakhir agar tidak ada kolom kosong atau peramalan fisik artifisial.
2. **Prognosis temporal (time-to-fault)** — meramal 6 bulan ke depan untuk 5 gas DGA utama, mengklasifikasikan lewat model AI, dan menghitung estimasi bulan menuju kegagalan.
3. **Kalkulasi RUL selulosa** — mengekstrak senyawa Furan (2-FAL) untuk mengukur degradasi fisik kertas isolasi, indikator yang tidak dapat dimanipulasi lewat purifikasi oli.

---

## 2. Standar Internasional Referensi

| Standar | Fungsi dalam Sistem |
|---|---|
| IEEE Std C57.104 | Klasifikasi risiko kondisi DGA berdasarkan volume gas absolut dan Gas Growth Rate (GGR). Empat level kondisi, dari Status 1 (Normal) sampai Status 4 (Ekstrem). |
| IEC 61198 | Metodologi ekstraksi konsentrasi senyawa Furanic sebagai indikator tidak langsung kerusakan kertas isolasi. |
| IEEE Std C57.91 | Parameter mekanis kertas isolasi selulosa. DP awal kertas baru = 800 (100% kekuatan mekanis), batas kritis kerusakan total = 200 (0% kekuatan mekanis). |
| IEC 60422 | Klasifikasi kelayakan fisik minyak operasional (Good/Fair/Poor) untuk BDV, water content, acidity, dan IFT. |

---

## 3. Dasar Ilmiah

### 3.1 Hubungan Mekanis Kertas Isolasi, DP, dan Furan

Kertas isolasi selulosa tersusun dari rantai polimer glukosa panjang. Kekuatan mekanis kertas diukur dari panjang rata-rata rantai ini, direpresentasikan oleh nilai Degree of Polymerization (DP).

Saat transformator mengalami stres termal berlebih atau terpapar kontaminan kimia (air dan asam), rantai polimer selulosa putus melalui reaksi pirolisis dan hidrolisis. Proses ini menghasilkan senyawa karbonil siklik yang dikenal sebagai Furan (dominan 2-Furaldehyde/2-FAL). Furan bersifat stabil dan larut dalam minyak mineral, sehingga konsentrasinya (ppm) bisa diekstraksi lewat uji lab.

Penurunan DP dari 800 menuju 200 berarti kertas kehilangan seluruh kekuatan regangnya, menjadi rapuh dan rentan hancur akibat gaya elektromagnetik saat terjadi short circuit — memicu kegagalan total fase-ke-fase belitan.

### 3.2 Gas DGA sebagai Sidik Jari Kegagalan

Minyak isolasi adalah rantai hidrokarbon kompleks. Anomali elektrikal atau termal memutus ikatan kimia minyak (C-H dan C-C). Reasosiasi radikal bebas memicu terbentuknya gas terlarut yang indikatif terhadap jenis kegagalan:

- **Thermal overheating (<300°C sampai >700°C):** memutus ikatan energi rendah, menghasilkan akumulasi Metana (CH4) dan Etana (C2H6). Di atas 700°C (T3), ikatan energi tinggi putus dan memproduksi Etilena (C2H4) secara masif.
- **Electrical discharge/arcing:** pelepasan muatan listrik berenergi tinggi dengan temperatur lokal mencapai ribuan derajat Celcius. Ini satu-satunya mekanisme yang memutus ikatan tripel karbon untuk membentuk Asetilena (C2H2). Kehadiran Asetilena bahkan dalam kadar kecil (>1 ppm) adalah indikator kritis arcing aktif.

---

## 4. Konstrain Sistem

1. **Batas prediksi ARIMA.** Model dibatasi memproyeksikan maksimal 6 langkah temporal (6 bulan) ke depan. Di luar rentang ini, confidence interval melebar terlalu jauh sehingga validitas prediksi menurun.
2. **Kebutuhan data minimum.** ARIMA mensyaratkan minimal 12 titik data historis berurutan tanpa jeda kosong, untuk mengekstrak komponen tren dan noise sebelum melakukan proyeksi yang stabil.
3. **Asumsi desain aset.** Sistem berasumsi parameter internal desain trafo (kapasitas disipasi panas radiator, volume tangki minyak, jenis minyak mineral dasar) bersifat statis, tanpa modifikasi struktural di luar pencatatan data.

---

## 5. Batasan Ruang Lingkup

| Kategori | Termasuk (In-Scope MVP) | Di Luar Lingkup |
|---|---|---|
| Kuantitas aset | Evaluasi mendalam satu unit trafo (single-asset proof of concept) | Pemantauan kluster massal lintas wilayah/korporasi |
| Konektivitas data | Pemrosesan file terstruktur `.csv`/`.xlsx` secara berkala | Integrasi real-time streaming dari sensor SCADA/IoT gardu induk |
| Pemodelan parameter OA | Visualisasi statis dengan teknik penahanan asinkron DAX | Peramalan AI dinamis untuk fluktuasi harian BDV atau zat asam |
| Variabel eksternal | Korelasi berbasis data internal uji sampel minyak (DGA, Furan, parameter fisik) | Analisis pengaruh lingkungan luar (kelembapan, curah hujan, profil pembebanan generator) |

---

## 6. Spesifikasi Data Lapangan

Dataset masukan berupa file tabel terstruktur (CSV/Excel) dengan kolom berikut:

1. `ID_Trafo` — string identifikasi unik aset (contoh: `Main_Transformer_01`).
2. `Tanggal_Uji` — format `YYYY-MM-DD`.
3. Parameter DGA (ppm): `H2`, `CH4`, `C2H6`, `C2H4`, `C2H2`.
4. Parameter kertas (ppm): `Furan` (fokus pada konsentrasi 2-Furaldehyde).
5. Parameter kualitas fisik minyak (OA):
   - `BDV` — tegangan tembus, satuan kV
   - `Acid` — kadar keasaman, satuan mg KOH/g
   - `Water` — kandungan air, satuan ppm
   - `IFT` — tegangan antarmuka, satuan mN/m
6. `Tipe_Data` — `Historis` untuk data riil lapangan, `Prediksi` untuk baris proyeksi hasil sistem.

---

## 7. Rumus Perhitungan dan Logika Deteksi Kerusakan

### 7.1 Gas Growth Rate (GGR)

Sesuai IEEE Std C57.104, evaluasi tidak boleh terpaku pada volume absolut karena minyak bisa menimbun gas dari masa lalu. Sistem menghitung selisih pertumbuhan gas per bulan berjalan:

$$\text{GGR\_Gas}_{t} = \frac{\text{Gas}_{t} - \text{Gas}_{t-1}}{\Delta t}$$

Jika nilai absolut suatu gas di bawah ambang batas dasar, GGR diatur ke 0.0 untuk mencegah bias akibat fluktuasi alat ukur lab.

### 7.2 Estimasi Kemunduran Mekanis Kertas (Kinetika De Pablo, IEC 61198)

Untuk mengetahui kekokohan rantai polimer kertas isolasi tanpa membedah trafo, sistem menerapkan rumus konversi empiris De Pablo terhadap kadar Furan terlarut:

$$\text{DP}_{\text{perkiraan}} = \frac{880}{2.14 + \text{Furan}}$$

Contoh: kadar Furan = 0.04 ppm.

$$\text{DP} = \frac{880}{2.14 + 0.04} = \frac{880}{2.18} = 403.67$$

### 7.3 Persentase Umur Mekanis Kertas Isolasi (`Status_Kertas`)

Mengacu pada IEEE Std C57.91, rentang operasional kekuatan kertas bergerak dari kondisi ideal (DP = 800) hingga batas kritis (DP = 200) — rentang 600 poin. Sistem memetakan posisi kekuatan mekanis saat ini ke skala 0-100%:

$$\text{Status\_Kertas}\ (\%) = \frac{\text{DP}_{\text{perkiraan}} - 200}{800 - 200} \times 100\%$$

Melanjutkan contoh dengan DP = 403.67:

$$\text{Status\_Kertas}\ (\%) = \frac{403.67 - 200}{600} \times 100\% = \frac{203.67}{600} \times 100\% = 33.94\%$$

Artinya, kekuatan mekanis kertas pembungkus belitan tembaga tersisa sepertiga (33.94%) sebelum trafo perlu turun mesin untuk penggantian isolasi (rewinding).

---

## 8. Arsitektur Sistem

Sistem dibangun dengan arsitektur modular decoupled (pemisahan komputasi berat dari visualisasi), terbagi menjadi empat lapisan:

1. **Data Ingestion Layer** — membaca file `.csv` historis pengujian minyak transformator.
2. **Python Prognostic Engine (Backend)** — mesin analitik yang ditanam ke Power BI lewat Python Scripting Data Connector. Menjalankan `statsmodels` untuk ARIMA, `joblib` untuk memuat model Random Forest Multiclass, serta kalkulasi kimia-fisika kertas isolasi.
3. **Asynchronous DAX Layer (Middleware)** — formula DAX di Power BI yang mengatur logika filter asinkron dan penahanan data fisik minyak.
4. **Visual Presentation Layer (Frontend)** — antarmuka Power BI yang menyajikan tren proyeksi DGA, gauge indicator parameter fisik, dan teks prognosis operasional.

---

## 9. Alur Data

```
DATA MENTAH LONGITUDINAL
(baris historis dari tahun-tahun sebelumnya)
        │
        ▼
PENGURUTAN TEMPORAL & SORTING
(data diurutkan berdasar ID_Trafo dan kronologi Tanggal_Uji)
        │
        ▼
┌────────────────────────────────────────────────────────┐
│             PYTHON PROGNOSTIC ENGINE LAYER              │
├──────────────────────────────────────────────────────────┤
│ 1. Pemisahan data historis & ekstraksi parameter DGA     │
│ 2. Eksekusi model ARIMA(1,1,0) per gas per ID trafo      │
│    → menghasilkan baris baru: Tipe_Data = 'Prediksi'     │
│ 3. Salin data lab terakhir ke baris baru (jangkar OA)    │
│ 4. Hitung rumus De Pablo & IEEE C57.91 untuk kertas      │
│ 5. Inferensi model AI Random Forest Multiclass           │
└────────────────────────────────────────────────────────┘
        │
        ▼
GABUNGAN DATASET UTUH (HISTORIS + PROYEKSI)
(tabel hasil eksekusi Python dikirim kembali ke Power BI)
        │
        ▼
┌────────────────────────────────────────────────────────┐
│                 POWER BI INTERNAL ENGINE                 │
├──────────────────────────────────────────────────────────┤
│ 1. Eksekusi DAX LASTNONBLANKVALUE untuk parameter OA     │
│ 2. Pemetaan batas threshold kedaruratan standar          │
└────────────────────────────────────────────────────────┘
        │
        ▼
VISUALISASI INTERAKTIF DASBOR DIGITAL TWIN
(grafik proyeksi 6 bulan + gauge status fisik + prognosis)
```

---

## 10. Strategi Penanganan Data Asinkron (Reality Anchor)

### 10.1 Masalah Kesenjangan Data

Sebuah transformator kritis diuji rutin setiap bulan untuk DGA. Namun uji kualitas fisik minyak (BDV, Acid, Water, IFT) dikirim ke laboratorium eksternal setiap 6 bulan sekali.

- Bulan Januari: data DGA dan OA lengkap (BDV = 52 kV).
- Bulan Februari-Mei: data DGA terbaru tersedia, kolom BDV kosong (null) karena tidak ada jadwal uji lab.

### 10.2 Konsekuensi Pendekatan Konvensional

- Jika kolom dibiarkan kosong, gauge chart di dasbor akan mati atau terputus pada bulan Februari-Mei. Ini merusak UX operator dan menghilangkan visibilitas kelayakan fisik minyak.
- Jika kolom diisi lewat interpolasi linear, sistem menebak nilai BDV secara matematis — padahal karakteristik fisik minyak tidak bergerak mengikuti deret waktu jangka pendek. Menebak nilai tegangan tembus isolasi tanpa uji lab riil berisiko menciptakan false sense of security pada operator.

### 10.3 Solusi: Pembekuan Data Lewat Reality Anchor

Sistem menolak menebak secara matematis. Sebagai gantinya, diterapkan logika pembekuan status lab terakhir, lewat kombinasi skrip Python dan formula DAX.

**Langkah 1 — Inisialisasi di skrip Python (fase prediksi 6 bulan).** Saat ARIMA memproyeksikan baris data untuk 6 bulan ke depan (`Tipe_Data = 'Prediksi'`), skrip mengidentifikasi baris riil terakhir dari fase historis, lalu menyalin nilai parameter fisik minyak tersebut ke seluruh baris proyeksi:

```python
# Potongan logika internal mesin Python untuk membentuk baris baru
baris_baru = data_terakhir.copy()

# Nilai gas DGA ditimpa oleh ramalan dinamis ARIMA
baris_baru['H2'] = ramalan_arima_h2
baris_baru['CH4'] = ramalan_arima_ch4

# Parameter OA (BDV, Acid, Water, IFT, Furan) dibiarkan konstan menyalin data_terakhir
```

**Langkah 2 — Eksekusi logika antarmuka via DAX di Power BI.** Untuk memastikan gauge chart tetap menampilkan data kelayakan fisik minyak terakhir tanpa interupsi nilai kosong, dasbor memakai fungsi DAX:

```dax
BDV_Status_Statis =
LASTNONBLANKVALUE(
    'Dataset_Trafo'[Tanggal_Uji],
    AVERAGE('Dataset_Trafo'[BDV])
)
```

**Cara kerja di dasbor:** meskipun bulan Februari-Mei tidak ada uji fisik, dasbor tetap menampilkan BDV stabil di 52 kV (jangkar dari Januari), dengan label evaluasi kelayakan sesuai IEC 60422. Begitu data lab terbaru terbit di Juni (misal BDV turun ke 48 kV), jangkar otomatis bergeser ke nilai baru untuk bulan-bulan berikutnya. Strategi ini menjaga kontinuitas dasbor tanpa menghasilkan informasi palsu.

---

## 11. Kronologi Proses Data hingga Hasil Akhir

### 11.1 Proses Parameter Degradasi Fisik Kertas (Furan)

1. **Input mentah:** contoh titik uji pada `Main_Transformer_01` dengan kadar Furan = 0.04 ppm.
2. **Konversi kimia kinetika:** mesin Python memasukkan 0.04 ke persamaan De Pablo untuk menghitung perkiraan panjang rantai selulosa:
   $$\text{DP} = \frac{880}{2.14 + 0.04} = 403.67$$
3. **Penentuan umur mekanis standar:** nilai 403.67 diuji terhadap batas IEEE Std C57.91 (DP 200-800):
   $$\text{Status\_Kertas} = \frac{403.67 - 200}{600} \times 100\% = 33.94\%$$
4. **Hasil di dasbor:** kolom `Status_Kertas` menyimpan nilai 33.94. Ditampilkan sebagai card atau gauge meter dengan warna kuning, sebagai peringatan bahwa isolasi padat telah terdegradasi permanen dan menyisakan sepertiga umur mekanis idealnya.

### 11.2 Proses Parameter Proyeksi Kerusakan DGA dan Inferensi AI

1. **Input mentah:** deret historis 5 gas utama (H2, CH4, C2H6, C2H4, C2H2) milik `Main_Transformer_05`.
2. **Peramalan deret waktu:** tren akumulasi historis dievaluasi oleh ARIMA(1,1,0), memproyeksikan laju pembentukan gas 6 bulan ke depan. Pada bulan akhir proyeksi (contoh: November 2026), gas hidrokarbon mengalami eskalasi tajam:
   - CH4 = 133.53 ppm
   - C2H4 = 63.71 ppm
   - C2H2 = 8.51 ppm
3. **Klasifikasi AI:** vektor fitur lima dimensi [324.22, 133.53, 36.93, 63.71, 8.51] diumpankan ke Random Forest Classifier (`model_dga_7classes_v2.pkl`, akurasi latih 90.94%). Model mencocokkan pola rasio gas dengan sidik jari kerusakan termal energi tinggi, dan mengeluarkan label diagnosis: **T3 (Thermal Fault >700°C)**.
4. **Mesin prognosis temporal:** skrip mengevaluasi pergerakan status dari fase historis ke fase prediksi, mendeteksi eskalasi atau status T3 yang menetap:

```python
if daftar_eskalasi:
    # Jika terdeteksi peningkatan status pada bulan tertentu di masa depan
    kesimpulan = f"Terjadi {status_sekarang} | berpotensi meningkat ke {st} dalam {bl} bulan"
else:
    # Jika status fault bernilai tinggi dan menetap sepanjang jendela prediksi
    kesimpulan = f"Terjadi {status_sekarang} | Kondisi fault menetap"
```

5. **Hasil di dasbor:** kolom `Status_DGA` terisi label T3, kolom `Prognosis_DGA` memuat teks "Terjadi T3 | Kondisi fault menetap". Dasbor menyalakan indikator alarm merah, sebagai instruksi bagi manajemen untuk menjadwalkan pemadaman terencana guna memeriksa area belitan tembaga sebelum terjadi kegagalan katastropik (ledakan tangki trafo).

---

## 12. Tata Cara Menjalankan Proyek di Lokal

### Langkah 1 — Instalasi Power BI Desktop

Unduh dan instal Microsoft Power BI Desktop (gratis) lewat Microsoft Store atau situs resmi Power BI.

### Langkah 2 — Instalasi Python dan Library

Backend prognostic engine (ARIMA, kalkulasi kertas, inferensi AI) ditenagai skrip Python.

1. Unduh dan instal Python (disarankan versi 3.9, 3.10, atau 3.11) dari python.org.
2. **Penting:** saat instalasi, centang opsi "Add Python.exe to PATH" sebelum klik Install Now. Jika terlewat, Power BI tidak bisa memanggil Python dari sistem.
3. Buka Command Prompt/Terminal, jalankan:

```bash
pip install pandas numpy joblib scikit-learn statsmodels dateutil
```

Tunggu hingga terminal menampilkan konfirmasi seluruh pustaka terinstal.

### Langkah 3 — Konfigurasi Jalur Python di Power BI

1. Buka Power BI Desktop.
2. Menu **File → Options and settings → Options**.
3. Pilih menu **Python scripting** di panel kiri.
4. Pastikan kolom **Detected Python home directories** mengarah ke lokasi instalasi Python (contoh: `C:\Users\NamaKomputer\AppData\Local\Programs\Python\Python310\`). Jika kosong, arahkan manual ke jalur yang sesuai.
5. Klik **OK**.

### Langkah 4 — Membuka Proyek dan Refresh

1. Buka file proyek dashboard (`.pbix`).
2. Klik tab **Home → Refresh**.
3. Di belakang layar, Power BI memicu Python scripting engine: membaca data mentah, mengurutkan secara temporal, menjalankan ARIMA untuk meramal 5 gas 6 bulan ke depan, menghitung sisa kekuatan mekanis kertas lewat rumus De Pablo, mengumpankan hasil ke model AI untuk klasifikasi, menerapkan strategi pembekuan data OA, lalu mengirim tabel hasil ke visualisasi dasbor.
4. Dalam hitungan detik, seluruh grafik tren proyeksi, meter indikator fisik, dan teks prognosis ter-update otomatis.

# Smart-Transformer--Integrating-DGA-Machine-Learning-Diagnostics-and-ARIMA-Time-Series-Prognos

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Power BI](https://img.shields.io/badge/Power_BI-Dashboard-yellow.svg)](https://powerbi.microsoft.com/)
[![Framework](https://img.shields.io/badge/Framework-Scikit--Learn%20%7C%20Statsmodels-orange)](https://scikit-learn.org/)

**Date:** Juli 2026

---

## 1. EXECUTIVE SUMMARY & PROBLEM STATEMENT

### 1.1 Latar Belakang
Transformator daya utama (*Main Substation Transformer*) menuntut keandalan operasional tingkat tinggi. Tantangan terbesar di lapangan saat ini adalah perbedaan frekuensi ketersediaan data. Data *Dissolved Gas Analysis* (DGA) sering kali lebih rutin dipantau atau disimulasikan ketimbang data *Oil Analysis* (OA) kelistrikan-fisik (seperti Tegangan Tembus/BDV dan Keasaman) yang mengandalkan uji laboratorium eksternal setiap 6 hingga 12 bulan sekali. Hal ini menciptakan celah visibilitas yang menghambat transisi dari perawatan preventif menjadi prediktif.

### 1.2 Rumusan Masalah 
* **Asinkronisasi Data (Data Gap):** Ketidaksesuaian waktu antara pengambilan sampel DGA dan pengujian OA membuat sistem pemantauan konvensional kesulitan memberikan gambaran yang utuh pada satu titik waktu (bulan berjalan).
* **Kesesatan Prediksi Fisik:** Memaksa algoritma untuk meramal nilai parameter fisik (BDV, IFT) di masa depan tanpa data suhu dan pembebanan harian adalah cacat secara fundamental teknik.
* **Ilusi RUL Berbasis Oli:** Memprediksi Sisa Umur (*Remaining Useful Life* / RUL) trafo murni dari data oli menghasilkan fluktuasi angka palsu ("Presisi Palsu"), karena oli dapat dipurifikasi, sementara umur sejati trafo berada pada kertas isolasinya.

### 1.3 Solusi yang Diusulkan
Membangun purwarupa *Minimum Viable Product* (MVP) **Digital Twin Dashboard di Power BI** yang beroperasi selaras dengan realitas operasional ketersediaan data di lapangan. Sistem MVP ini berfokus pada:
* **Metode Penahanan Data:** Membekukan status parameter OA terakhir hingga ada *update* lab terbaru.
* **Prognosis Waktu Menuju Kegagalan (*Time-to-Fault*):** Berbasis deret waktu (historis) evolusi gas DGA.
* **Kalkulasi RUL Sejati:** Berbasis ekstraksi molekul Furan (2-FAL) dari kertas selulosa.

---

## 2. OBJECTIVES & PROJECT SCOPE

### 2.1 Tujuan Proyek (*Objectives*)
* Mengakomodasi kesenjangan jadwal uji lab (DGA vs OA) secara elegan tanpa menghasilkan alarm palsu atau metrik kosong di dasbor.
* Menerjemahkan laju tren historis DGA menjadi informasi zona waktu peringatan dini (misal: "Proyeksi D1 dalam 1-3 Bulan").
* Memberikan kepastian metrik degradasi aset menggunakan perhitungan standar internasional (IEC 61198) untuk kertas trafo.

### 2.2 Batasan Ruang Lingkup (*Scope Boundary*)

| Kategori | In-Scope (MVP) | Out-of-Scope (Fase Selanjutnya) |
| :--- | :--- | :--- |
| **Aset Target** | 1 unit Trafo Kritis pabrik (*Single-Asset PoC*). | Ekspansi massal multi-aset. |
| **Integrasi Data** | Pemrosesan longitudinal data CSV/Excel (DGA, Furan, OA). | *Real-time Streaming* sensor IoT (Suhu, Beban). |
| **Target Prediksi** | Prediksi Deret Waktu DGA (Time-to-Fault) & Furan. | Prediksi harian degradasi fisik (BDV/Acidity). |

---

## 3. ARSITEKTUR SISTEM & ALUR KERJA (*WORKFLOW*)

MVP ini menggunakan Python sebagai *backend prognostic engine* dan DAX Power BI sebagai pengendali antarmuka (*Asynchronous Data Handler*).

```text
[Dataset Historis CSV: DGA, Furan, OA] 
           │
           ▼
[Python Engine - Data Pre-Processing & ML]
           ├── 1. Forecasting DGA (ARIMA/Prophet) ─► Prediksi Profil Gas Masa Depan
           ├── 2. Diagnosis Masa Depan ────────────► Eksekusi Duval Triangle AI dari Data Proyeksi
           └── 3. Kalkulasi DP Kertas via Furan ───► True RUL (Sisa Umur Valid)
           │
           ▼
[Power BI Dashboard - Presentasi Visual]
           ├── Panel DGA Forecasting (Grafik Tren + Confidence Interval)
           ├── Panel Peringatan (Zona Waktu Menuju Fault D1/D2/T2 dll.)
           └── Panel OA Terakhir (Gauge Meter Statis dengan DAX LASTNONBLANKVALUE)
```
## 4. TECHNICAL SPECIFICATIONS & CORE CAPABILITIES

### 4.1 Lapis 1: Asynchronous Data Fusion (Penahanan Data OA)
Mengingat data *Oil Analysis* (BDV, Acidity, Water Content, IFT) hanya diperbarui secara sporadis (misal: setahun sekali), MVP ini menggunakan pendekatan **Jangkar Realita (*Reality Anchor*)**.
* Dasbor Power BI menggunakan fungsi DAX `LASTNONBLANKVALUE` untuk parameter fisik.
* **Mekanisme:** Jika lab mengeluarkan hasil BDV 60 kV pada bulan Januari, visualisasi *Gauge Meter* untuk BDV akan menahan dan menampilkan angka 60 kV secara statis pada bulan Februari, Maret, hingga ada input data lab terbaru di bulan Juli.
* **Tujuan:** Menghindari manipulasi matematis tebakan untuk besaran fisik yang membingungkan operator, sembari tetap menjaga *readiness* dasbor untuk menampilkan data terbaru kapan pun lab merilis hasilnya.

### 4.2 Lapis 2: Sisa Umur Kertas (Furan - IEC 61198)
Umur trafo tidak diukur dari pelumasnya, melainkan direpresentasikan oleh kekuatan kertas isolasi (*Degree of Polymerization* / DP). MVP ini mengekstrak kadar 2-Furfural (2-FAL) dan menghitung nilai DP menggunakan Persamaan Chendong:

$$DP = \frac{\log_{10}(\text{2-FAL}) - 1.51}{-0.0035}$$

Nilai DP dikonversi menjadi persentase Indeks Kesehatan Kertas (RUL Sejati). Jika DP mendekati batas kegagalan mekanis (angka 200), dasbor akan memicu alarm peringatan dini.

### 4.3 Lapis 3: Time-to-Fault Forecasting (Prediksi DGA)
MVP ini menggunakan sistem **Zona Waktu Proyeksi**:
* ARIMA (model *Time-Series*) memproyeksikan laju pembentukan gas pembakaran utama (seperti Ethylene dan Acetylene) ke masa depan.
* Titik proyeksi tersebut disilangkan ke dalam batas Segitiga Duval (Otak 1 Klasifikasi).
* Keluaran diubah menjadi rentang peringatan proaktif. Contoh output pada dasbor: **"Proyeksi D2: Zona Waktu Menengah (3 - 6 Bulan Ke Depan)."** Hal ini memberikan kenyamanan UI/UX sekaligus akurasi teknis tanpa presisi palsu.

---

## 5. DATA REQUIREMENTS (KEBUTUHAN DATA)

MVP ini dikembangkan dan diuji menggunakan kumpulan dataset longitudinal (riwayat DGA, Furan, dan OA) dengan kebutuhan struktur spesifik:

| Kategori Parameter | Kolom Wajib (*Mandatory*) | Kegunaan dalam MVP |
| :--- | :--- | :--- |
| **Sumbu Waktu** | `Tanggal_Uji` / `Bulan_Ke` | Sumbu temporal mutlak untuk eksekusi algoritma *forecasting*. |
| **DGA (Gas Utama)** | `H2`, `CH4`, `C2H6`, `C2H4`, `C2H2` | Bahan baku model proyeksi mesin waktu & klasifikasi Duval. |
| **Parameter Kertas** | `Furan_2FAL` | Parameter tunggal penghitung RUL (Kalkulasi Chendong). |
| **Kualitas Fisik (OA)**| `BDV`, `Acidity`, `Water`, `IFT` | Disimpan dan ditahan sebagai Jangkar Realita (Status Lab Terakhir). |

---

## 6. TECHNOLOGY STACK & DEPENDENCIES

* **Python (Scikit-Learn, Statsmodels, Pandas):** Untuk pembersihan data temporal, penarikan trendline/forecasting, dan penghitungan DP secara *batch processing*. Pengujian skrip lokal menggunakan perintah eksekusi `python`.
* **Microsoft Power BI:** Untuk implementasi lapisan antarmuka pengguna, pengaturan filter asinkron (DAX), dan penyajian metrik prediksi secara visual.
* **Standar Industri Referensi:** IEC 61198 (Metode Uji Senyawa Furanic) & IEEE C57.104 (Interpretasi DGA).

## 7. SPESIFIKASI MODEL AI & DIAGNOSIS KELAS

Sistem ini melampirkan file model biner siap pakai (`model_dga_7classes_v2.pkl`) yang bertindak sebagai *inference engine* utama di dalam repositori.

### 7.1 Detail Arsitektur & Pelatihan Model
* **Algoritma:** Model berbasis klasifikasi multi-kelas (*Multiclass Classification*) yang telah dilatih menggunakan data historis insiden kegagalan transformator di industri.
* **Fitur Input ($X$):** Menerima tepat 5 fitur berupa nilai konsentrasi gas terlarut dalam satuan ppm secara berurutan: `['H2', 'CH4', 'C2H6', 'C2H4', 'C2H2']`.
* **Output Label ($Y$):** Menghasilkan prediksi status kondisi trafo yang terbagi ke dalam 7 kelas diagnosis kerusakan fungsional.

### 7.2 Pemetaan 7 Kelas Diagnosis AI
Model mengklasifikasikan kondisi transformator ke dalam salah satu status berikut berdasarkan karakteristik pola gas hidrokarbonnya:

| Kode Vonis AI | Deskripsi Teknis Kerusakan | Arti & Tindakan Lapangan |
| :--- | :--- | :--- |
| **Normal** | *No Fault Detected* | Kondisi minyak isolasi aman, lanjutkan pemantauan rutin. |
| **PD** | *Partial Discharge* | Gejala korona atau pelepasan muatan sebagian berenergi rendah. |
| **D1** | *Discharge of Low Energy* | *Sparking* atau percikan listrik berenergi rendah pada komponen dalam. |
| **D2** | *Discharge of High Energy* | *Arcing* atau busur api listrik berenergi tinggi (Kondisi Kritis). |
| **T1** | *Thermal Fault ($<300^\circ\text{C}$)* | Overheating lokal tingkat rendah (misal: hambatan kontak sambungan). |
| **T2** | *Thermal Fault ($300^\circ\text{C} - 700^\circ\text{C}$)* | Overheating tingkat menengah pada inti besi atau belitan trafo. |
| **T3** | *Thermal Fault ($>700^\circ\text{C}$)* | Overheating ekstrem yang menyebabkan kerusakan parah pada struktur isolasi. |

---

## TATA CARA MENJALANKAN PROYEK DI LOKAL (UNTUK PENGGUNA UMUM)

Agar rekan tim, dosen penguji, atau pengguna umum dapat membuka dan menjalankan file dashboard *Transformer Digital Twin MVP* ini di komputer mereka masing-masing, ikuti panduan langkah demi langkah di bawah ini:

### Langkah 1: Instalasi Aplikasi Power BI Desktop
1. Dashboard ini membutuhkan aplikasi **Microsoft Power BI Desktop** (Aplikasi ini gratis).
2. Unduh dan instal aplikasi langsung melalui [Microsoft Store](https://apps.microsoft.com/detail/9ntxr16hnw1t) atau situs resmi [Microsoft Power BI Downloads](https://powerbi.microsoft.com/en-us/downloads/).

### Langkah 2: Instalasi Python & Library Pendukung
Karena *Prognostic Engine* dashboard ini ditenagai oleh skrip Python, komputer kamu harus memiliki instalasi Python yang aktif:
1. Unduh dan instal **Python (Disarankan Versi 3.9 hingga 3.11)** melalui [python.org](https://www.python.org/downloads/). *Catatan: Pastikan mencentang pilihan "Add Python.exe to PATH" saat proses instalasi dimulai.*
2. Buka *Command Prompt* (CMD) atau *Terminal*, lalu instal pustaka data analitik yang dibutuhkan dengan mengetik perintah berikut dan tekan Enter:
   ```bash
   pip install pandas numpy joblib scikit-learn statsmodels dateutil
Langkah 3: Sinkronisasi Jalur File (Path Configuration)

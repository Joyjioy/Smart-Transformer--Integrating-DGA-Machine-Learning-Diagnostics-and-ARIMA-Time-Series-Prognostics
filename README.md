

# PRODUCT REQUIREMENT DOCUMENT (PRD)
## Digital Twin & Predictive Maintenance Dashboard Transformator Daya Berbasis AI (Hybrid IEEE/IEC Standar)

**Doc Version:** 1.0  
**Author:** Mahasiswa Kerja Praktik Teknik Elektro/Sistem Kontrol ITB  
**Target Audience:** Mentor Lapangan, Reliability Engineer, & Management PT Chandra Asri Pacific Tbk  
**Date:** Juli 2026  

---

### 1. EXECUTIVE SUMMARY & PROBLEM STATEMENT

#### 1.1 Latar Belakang
Transformator daya utama (*Main Substation Transformer*) merupakan jantung distribusi listrik pabrik petrokimia yang menuntut keandalan (*reliability*) 100% dan *zero unplanned downtime*. Metode pemantauan rutin saat ini umumnya masih bersifat statis (*snapshot classification*), di mana analisis laboratorium minyak isolasi (Dissolved Gas Analysis/DGA & *Oil Analysis*) dievaluasi secara terpisah dan hanya menilai kondisi pada satu titik waktu saat sampel diambil.

#### 1.2 Pernyataan Masalah (*Problem Statement*)
1. **Analisis Terfragmentasi:** Evaluasi gas terlarut (DGA) sering kali dipisahkan dari analisis degradasi fisik-kimiawi minyak isolasi (*Oil Analysis*), sehingga teknisi kehilangan gambaran holistik kesehatan transformator.
2. **Keterbatasan Evaluasi Statis:** Nilai parameter di bawah ambang batas bahaya sering kali dianggap "Aman", padahal laju kenaikannya (*rate of change*) mungkin sedang melonjak eksponensial dalam rentang waktu singkat.
3. **Kebutuhan Preskriptif:** Manajemen dan teknisi tidak hanya membutuhkan diagnosis *jenis kerusakan saat ini*, tetapi membutuhkan perkiraan **kapan transformator berisiko mengalami kegagalan (*Remaining Useful Life / RUL*)** dan **tindakan perawatan preskriptif apa yang harus segera dieksekusi**.

#### 1.3 Solusi yang Diusulkan (*Proposed Solution*)
Membangun purwarupa (*Proof of Concept / PoC*) **Digital Twin & Predictive Dashboard terintegrasi Microsoft Power BI** untuk 1 unit Transformator Kritis pabrik. Sistem ini memadukan 3 lapis analisis (*Hybrid Intelligence*):
* **Rel 1 (Standard Deterministik):** Skrining batas kesehatan minyak isolasi berdasarkan IEEE C57.104 & IEC 60422 Edition 4.0.
* **Rel 2 (Geometri Diagnosis):** Pemetaan klasifikasi kegagalan aktif menggunakan Segitiga Duval Klasik & Rasio Rogers.
* **Rel 3 (Machine Learning Prognostics):** Prediksi laju degradasi bersambung (*Time-Series Forecasting*) dan estimasi sisa umur pakai (*Remaining Useful Life / RUL*).

---

### 2. OBJECTIVES & PROJECT SCOPE

#### 2.1 Tujuan Proyek (*Objectives*)
* **Membangun sistem pemantauan terpusat** di Power BI yang memproses data uji lab Excel secara otomatis tanpa intervensi manual yang rumit.
* **Mengurangi alarm palsu (*False Alarm*)** melalui validasi silang antara kondisi normal standar IEEE dengan kecerdasan buatan (*Machine Learning*).
* **Memberikan visibilitas masa depan (*Prognostics*)** mengenai kurva degradasi parameter kritis hingga 12–24 bulan ke depan.
* **Menghasilkan rekomendasi tindakan preskriptif** sesuai standar IEC 60422 Tabel 5 & 6 (*Reconditioning*, *Reclaiming*, atau *Passivation*).

#### 2.2 Batasan Ruang Lingkup (*Scope Boundary*)
| Kategori | In-Scope (Akan Dikerjakan) | Out-of-Scope (Bukan Prioritas Saat Ini) |
| :--- | :--- | :--- |
| **Aset Target** | Fokus pada **1 unit Trafo Kritis** pabrik (*Single-Asset PoC*). | Implementasi massal untuk seluruh trafo distribusi kecil di pabrik. |
| **Integrasi Data** | Impor historis file Excel (*Offline/Batch Processing*) ke Power BI. | Pemasangan sensor *real-time* langsung via IoT ke fisik trafo. |
| **Domain Analisis** | DGA (IEEE C57.104/Duval) + Oil Analysis (IEC 60422). | Analisis *Furanic compound* mendalam atau uji tegangan impuls fisik lab. |

---

### 3. ARSITEKTUR SISTEM & ALUR KERJA (*WORKFLOW*)

Sistem dirancang dengan alur pemrosesan data linier di dalam ekosistem Microsoft Power BI yang didukung oleh skrip *backend* Python di dalam Power Query:
```
[Data Lab Excel (Longitudinal)] 
           │
           ▼
[Power BI Power Query Editor] ────────► [Python Engine (joblib .pkl / script)]
           │                                      │
           │                                      ├── 1. Feature Engineering (Rasio Gas & GGR)
           │                                      ├── 2. Evaluasi Skrining IEEE C57.104 & IEC 60422
           │                                      ├── 3. Diagnosis AI (Random Forest 7 Kelas)
           │                                      └── 4. Time-Series Trend & RUL Estimation
           ▼
[Tabel Diperkaya (Enriched Dataset)]
           │
           ▼
[Power BI Executive Dashboard] (KPI Card, Duval Chart, Proyeksi RUL, Prescriptive Action)
```
### 4. TECHNICAL SPECIFICATIONS & CORE CAPABILITIES

#### 4.1 Lapis Skrining Fisika & Kimiawi (Rel 1 - Standard Compliance)
Sistem secara otomatis mengklasifikasikan parameter minyak transformator ke dalam status Good, Fair, atau Poor berdasarkan standar IEC 60422 Edition 4.0:
* **Breakdown Voltage (BDV):** Evaluasi ketahanan tegangan tembus berdasarkan kategori trafo (>60 kV untuk Kategori O/A; >50 kV untuk Kategori B).
* **Moisture in Oil ($W_{abs}$):** Evaluasi kandungan air absolut dengan koreksi suhu normalisasi ke 20°C serta persentase kejenuhan air (Moisture Saturation).
* **Acidity (Neutralization Value):** Evaluasi laju penuaan kimiawi (<0.10 mg KOH/g untuk Good; >0.15 mg KOH/g untuk Poor pada Kategori O/A/D).
* **Interfacial Tension (IFT):** Deteksi dini kontaminan polar larut dan lumpur (sludge) (<22 mN/m mengindikasikan Poor).
* **Inhibitor Content:** Pemantauan cadangan aditif antioksidan (DBPC/DBP); peringatan dini jika turun di bawah 40% dari nilai awal.

### 4.2 Lapis Diagnosis Kegagalan Aktif (Rel 2 – DGA Diagnostics)

#### Gas Generation Rate (GGR)

Gas Generation Rate (GGR) digunakan untuk mengukur laju perubahan konsentrasi gas terlarut antar dua waktu pengujian. Perhitungan dilakukan untuk setiap gas utama, yaitu CH₄, H₂, C₂H₄, C₂H₆, dan C₂H₂.

\[
\mathrm{GGR}_{gas}
=
\frac{C_{t_2}-C_{t_1}}
{\Delta t}
\]

dengan

\[
\Delta t=t_2-t_1
\]

di mana:

- \(C_{t_1}\) = konsentrasi gas pada waktu pengambilan sampel pertama (ppm)
- \(C_{t_2}\) = konsentrasi gas pada waktu pengambilan sampel berikutnya (ppm)
- \(\Delta t\) = selang waktu antar pengujian (hari atau bulan)
- \(\mathrm{GGR}_{gas}\) = laju pembentukan gas (ppm/hari atau ppm/bulan)

Interpretasi nilai GGR dilakukan dengan membandingkan laju kenaikan masing-masing gas terhadap tren historis sehingga sistem dapat mendeteksi percepatan degradasi sebelum konsentrasi gas melampaui ambang batas IEEE C57.104.

---

#### Duval Triangle Method 1

Metode Duval Triangle digunakan untuk memetakan persentase relatif gas CH₄, C₂H₄, dan C₂H₂ ke dalam enam zona kegagalan aktif (PD, D1, D2, T1, T2, dan T3).

---

#### AI Random Forest Classifier

Model Random Forest melakukan klasifikasi probabilistik terhadap tujuh kelas kondisi transformator berdasarkan kombinasi fitur DGA, rasio gas, dan parameter Oil Analysis. Keluaran model meliputi:

- `Diagnosis_AI`
- `Confidence Score (%)`
  
#### 4.3 Lapis Prognosis Masa Depan & RUL (Rel 3 - Predictive Engine)
* **Proyeksi Tren Longitudinal:** Model memetakan tren historis untuk memprediksi nilai gas dan parameter kimiawi minyak (seperti BDV dan Acidity) di masa depan.
* **Remaining Useful Life (RUL):** Perhitungan estimasi waktu menuju ambang batas kegagalan kritis (Failure Threshold).
* **Mesin Rekomendasi Preskriptif:** Menghasilkan keluaran teks otomatis berdasarkan IEC 60422 Tabel 6, contoh:
  > "Peringatan: Tren Acidity meningkat tajam dan diproyeksikan menembus 0.15 mg KOH/g dalam 180 hari. Dijadwalkan tindakan Reclaiming (Fuller's Earth Treatment) sebelum terbentuk presipitasi lumpur."

---

### 5. DATA REQUIREMENTS (KEBUTUHAN DATA DARI CHANDRA ASRI)
Untuk dapat melatih model prediksi longitudinal dan memvalidasi purwarupa ini, diperlukan dukungan data historis dari pihak pabrik dengan spesifikasi sebagai berikut:

#### 5.1 Spesifikasi Data yang Diminta
Data riwayat pengujian laboratorium minyak isolasi dari 1 atau 2 unit Transformator Utama (Main Substation) yang dirunut secara waktu (time-series) selama minimal 3 hingga 5 tahun terakhir (atau minimal 8–15 kali pengujian berurutan).

#### 5.2 Format Kebutuhan Kolom Data (Tabel Excel/CSV)
| Kategori Parameter | Nama Kolom Wajib | Satuan | Keterangan / Kegunaan |
| :--- | :--- | :--- | :--- |
| **Identitas & Waktu** | `ID_Trafo`, `Tanggal_Uji` | Text, YYYY-MM-DD | Sumbu temporal utama untuk analisis deret waktu (time-series). |
| **Suhu Sampling** | `Suhu_Oli_Sampling` | °C | Koreksi kejenuhan air dan normalisasi BDV/Resistivitas. |
| **Gas DGA Utama** | `H2`, `CH4`, `C2H6`, `C2H4`, `C2H2` | ppm | Evaluasi Segitiga Duval & Gas Generation Rate (GGR). |
| **Gas Kertas Selulosa** | `CO`, `CO2` | ppm | Pemantauan laju degradasi isolasi kertas belitan. |
| **Kualitas Fisik (OA)** | `Breakdown_Voltage` (BDV) | kV | Indikator kekuatan dielektrik minyak isolasi (IEC 60422). |
| **Kandungan Air (OA)** | `Water_Content` ($W_{abs}$) | mg/kg | Indikator kelembaban minyak dan risiko kondensasi. |
| **Kualitas Kimia (OA)** | `Acidity` | mg KOH/g | Laju oksidasi dan penuaan kimiawi pelumas. |
| **Tegangan Muka (OA)** | `Interfacial_Tension` (IFT) | mN/m | Deteksi kontaminan polar larut dan bibit lumpur (sludge). |
| **Rugi Daya (OA)** | `DDF_TanDelta` ($\tan\delta$) | % / desimal | Rugi-rugi dielektrik pada suhu operasi/90°C. |
| **Kandungan Aditif** | `Inhibitor_DBPC` | % weight | Pemantauan konsumsi antioksidan sintetis. |

#### 5.3 Catatan Buku Harian Perawatan (Maintenance Log Book)
Daftar tanggal dan tindakan perawatan yang pernah dilakukan pada trafo target tersebut (misal: Filtrasi/Dehidrasi pada 12 Mei 2024, atau Ganti Oli/Topping-up pada Agustus 2025). Data ini mutlak diperlukan agar AI tidak salah membaca penurunan gas akibat filtrasi sebagai penyembuhan alamiah transformator.

---

### 6. TECHNOLOGY STACK & DEPENDENCIES
| Komponen | Teknologi / Library | Fungsi Utama |
| :--- | :--- | :--- |
| **Pusat Analisis Model** | Python 3.12 (Google Colab / VS Code) | Exploratory Data Analysis (EDA), rekayasa fitur, dan pelatihan AI. |
| **Library ML & Data** | `scikit-learn`, `pandas`, `numpy`, `joblib` | Pembuatan model Random Forest, pemrosesan rasio, dan serialisasi `.pkl`. |
| **Visualization Platform** | Microsoft Power BI Desktop | Pembangunan Dasbor eksekutif, antarmuka visual, dan integrasi DAX. |
| **Script Integration** | Power Query Python Script Wrapper | Menjalankan model AI secara lokal langsung di dalam tabel Power BI. |

---
### 7. SUCCESS METRICS (KRITERIA KEBERHASILAN)
1. **Keakuratan Klasifikasi AI:** Model AI minimal mencapai akurasi >85% dan Recall >95% pada deteksi bahaya kritis (busur api D2 dan panas ekstrem T3) pada uji validasi.
2. **Kesesuaian Standar:** Dasbor berhasil memisahkan trafo sehat (Normal) dan trafo anomali secara konsisten tanpa menghasilkan alarm palsu (false alarm) pada kondisi gas normal di bawah spesifikasi IEEE C57.104.
3. **Penerimaan Pengguna (Usability):** Waktu pemrosesan data uji lab baru mulai dari input Excel hingga keluar diagnosis dan estimasi RUL di layar Power BI membutuhkan waktu <10 detik.

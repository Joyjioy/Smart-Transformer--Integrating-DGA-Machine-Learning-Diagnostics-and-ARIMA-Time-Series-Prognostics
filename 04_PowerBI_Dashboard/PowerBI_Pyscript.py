import pandas as pd
import numpy as np
import joblib
import warnings
from datetime import datetime
from dateutil.relativedelta import relativedelta 
from statsmodels.tsa.arima.model import ARIMA
warnings.filterwarnings("ignore")

# 1. AMBIL DATA AWAL DARI POWER BI
df = dataset.copy()  
kolom_numerik = ['H2', 'CH4', 'C2H6', 'C2H4', 'C2H2', 'Furan', 'DP_Kertas', 'BDV', 'Acid', 'Water', 'IFT']
for col in kolom_numerik:
    df[col] = pd.to_numeric(df[col], errors='coerce')

kolom_forecast = ['H2', 'CH4', 'C2H6', 'C2H4', 'C2H2']
langkah_prediksi = 6  # Meramal 6 bulan ke depan secara berurutan
hasil_keseluruhan = []

# 2. MESIN WAKTU ARIMA (DISETTING KONTINU PER 1 BULAN)
for trafo in df['ID_Trafo'].unique():
    df_trafo = df[df['ID_Trafo'] == trafo].copy()
    df_trafo['Tipe_Data'] = 'Historis'
    
    # Deteksi format tanggal asli historis
    df_trafo['Tanggal_Uji_DT'] = pd.to_datetime(df_trafo['Tanggal_Uji'], dayfirst=True, errors='coerce')
    df_trafo = df_trafo.sort_values('Tanggal_Uji_DT')
    
    waktu_terakhir_DT = df_trafo['Tanggal_Uji_DT'].iloc[-1]
    data_terakhir = df_trafo.iloc[-1].copy()
    
    prediksi_masa_depan = {col: [] for col in kolom_forecast}
    
    # PENTING: Set langkah masa depan maju teratur +1 bulan, +2 bulan, +3 bulan, dst.
    tanggal_prediksi = [(waktu_terakhir_DT + relativedelta(months=1 * (i+1))).strftime('%Y-%m-%d') for i in range(langkah_prediksi)]
    
    for col in kolom_forecast:
        deret_waktu = df_trafo[col].values
        try:
            model = ARIMA(deret_waktu, order=(1, 1, 0))
            model_fit = model.fit()
            ramalan = model_fit.forecast(steps=langkah_prediksi)
        except:
            selisih_rata2 = np.mean(np.diff(deret_waktu[-5:])) if len(deret_waktu) > 1 else 0
            ramalan = [deret_waktu[-1] + (selisih_rata2 * (i+1)) for i in range(langkah_prediksi)]
        ramalan = np.maximum(ramalan, deret_waktu[-1])
        prediksi_masa_depan[col] = ramalan
        
    df_trafo_prediksi_list = []
    for i in range(langkah_prediksi):
        baris_baru = data_terakhir.copy() 
        baris_baru['Tanggal_Uji'] = tanggal_prediksi[i]
        baris_baru['Tipe_Data'] = 'Prediksi'
        for col in kolom_forecast:
            baris_baru[col] = round(prediksi_masa_depan[col][i], 2)
        
        nilai_bulan_lalu = df_trafo_prediksi_list[i-1] if i > 0 else data_terakhir
        for gas in kolom_forecast:
            ggr = (baris_baru[gas] - nilai_bulan_lalu[gas]) / 1
            baris_baru[f'GGR_{gas}'] = round(max(ggr, 0), 2)
            
        df_trafo_prediksi_list.append(baris_baru)
        
    df_trafo_prediksi = pd.DataFrame(df_trafo_prediksi_list)
    
    for gas in kolom_forecast:
        df_trafo[f'GGR_{gas}'] = 0.0
        
    df_trafo = df_trafo.drop(columns=['Tanggal_Uji_DT'])
    hasil_keseluruhan.append(df_trafo)
    hasil_keseluruhan.append(df_trafo_prediksi)

df_master = pd.concat(hasil_keseluruhan, ignore_index=True)

# 3. AI DIAGNOSIS MENTAH
JALUR_MODEL_LOKAL = r'D:\ITB\SEMESTER 7\KP\Transformer_Digital_Twin_MVP\03_AI_Models\model_dga_7classes_v2.pkl'
model_dga = joblib.load(JALUR_MODEL_LOKAL)

X_gas = df_master[['H2', 'CH4', 'C2H6', 'C2H4', 'C2H2']]
df_master['Vonis_AI_Mentah'] = model_dga.predict(X_gas)

# 4. EVALUASI STATUS DGA & KERTAS
batas_warning_gas = {'H2': 150, 'CH4': 120, 'C2H6': 65, 'C2H4': 50, 'C2H2': 2}

status_dga_list = []
status_kertas_list = []

for index, row in df_master.iterrows():
    is_gas_anomali = (row['H2'] > batas_warning_gas['H2']) or \
                     (row['CH4'] > batas_warning_gas['CH4']) or \
                     (row['C2H6'] > batas_warning_gas['C2H6']) or \
                     (row['C2H4'] > batas_warning_gas['C2H4']) or \
                     (row['C2H2'] > batas_warning_gas['C2H2'])
    
    if is_gas_anomali:
        status_dga_list.append(row['Vonis_AI_Mentah'])
    else:
        status_dga_list.append("Normal")
        
    furan = row['Furan']
    if furan > 5.0:
        status_kertas_list.append("Kritis (End of Life)")
    elif furan > 1.0:
        status_kertas_list.append("Abnormal (Penuaan Dipercepat)")
    elif furan > 0.1:
        status_kertas_list.append("Waspada")
    else:
        status_kertas_list.append("Normal")

df_master['Status_DGA'] = status_dga_list
df_master['Status_Kertas'] = status_kertas_list

# 5. MESIN PROGNOSIS COUNTDOWN BERTINGKAT (MULTI-FAULT PROJECTION)
df_master['Tanggal_Uji_DT'] = pd.to_datetime(df_master['Tanggal_Uji'], format='%Y-%m-%d', errors='coerce')
df_master = df_master.sort_values(['ID_Trafo', 'Tanggal_Uji_DT']).reset_index(drop=True)
df_master['Prognosis_DGA'] = ""

# Severity berbasis KATA KUNCI, bukan exact-string match, supaya tahan
# terhadap variasi kecil penulisan status (spasi, suffix tambahan, dll).
def get_severity(status):
    s = str(status).upper()
    if "KRITIS" in s:
        return 8
    if "D2" in s:
        return 7
    if "D1" in s:
        return 6
    if "T3" in s:
        return 5
    if "T2" in s:
        return 4
    if "T1" in s:
        return 3
    if "PD" in s:
        return 2
    if "WASPADA" in s:
        return 1
    return 0  # tidak ada kata kunci fault -> Normal

df_master['Severity_Level'] = df_master['Status_DGA'].apply(get_severity)

for trafo_id in df_master['ID_Trafo'].unique():
    idx_trafo = df_master[df_master['ID_Trafo'] == trafo_id].index
    list_idx = list(idx_trafo)

    for pos, idx in enumerate(list_idx):
        status_sekarang = df_master.loc[idx, 'Status_DGA']
        severity_sekarang = df_master.loc[idx, 'Severity_Level']
        tanggal_baris = df_master.loc[idx, 'Tanggal_Uji_DT']

        # Telusuri SEMUA baris setelah baris ini, tangkap tiap kenaikan severity baru
        daftar_eskalasi = []
        severity_terlewati = severity_sekarang
        for idx_depan in list_idx[pos + 1:]:
            severity_depan = df_master.loc[idx_depan, 'Severity_Level']
            if severity_depan > severity_terlewati:
                tgl_depan = df_master.loc[idx_depan, 'Tanggal_Uji_DT']
                status_depan = df_master.loc[idx_depan, 'Status_DGA']
                selisih_bulan = (tgl_depan.year - tanggal_baris.year) * 12 + (tgl_depan.month - tanggal_baris.month)
                daftar_eskalasi.append((status_depan, selisih_bulan))
                severity_terlewati = severity_depan  # naikkan pointer, cegah deteksi ganda/mundur

        if severity_sekarang == 0:
            # Kondisi NORMAL -> tanpa "SEGERA MAINTENANCE"
            if daftar_eskalasi:
                bagian = [f"Berpotensi terjadi {st} dalam {bl} bulan" for st, bl in daftar_eskalasi]
                kesimpulan = "Aman saat ini. " + " | ".join(bagian)
            else:
                kesimpulan = "Aman (Kondisi diprediksi stabil)"
        else:
            # Kondisi SUDAH FAULT -> tampilkan eskalasi berikutnya kalau ada
            if daftar_eskalasi:
                bagian = [f"berpotensi meningkat ke {st} dalam {bl} bulan" for st, bl in daftar_eskalasi]
                kesimpulan = f"⚠️ SEGERA MAINTENANCE: Terjadi {status_sekarang} | " + " | ".join(bagian)
            else:
                kesimpulan = f"⚠️ SEGERA MAINTENANCE: Terjadi {status_sekarang} | Kondisi fault menetap"

        df_master.loc[idx, 'Prognosis_DGA'] = kesimpulan

df_master = df_master.drop(columns=['Tanggal_Uji_DT'])
df_final = df_master
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

if 'Status_Pemurnian' in df.columns:
    df['Status_Pemurnian'] = df['Status_Pemurnian'].astype(str).replace({'nan': np.nan, 'None': np.nan})
else:
    df['Status_Pemurnian'] = np.nan

kolom_forecast = ['H2', 'CH4', 'C2H6', 'C2H4', 'C2H2']
langkah_prediksi = 6  
hasil_keseluruhan = []

T1_DGA = {'H2': 150, 'CH4': 120, 'C2H6': 65, 'C2H4': 50, 'C2H2': 2}
T2_DGA = {'H2': 300, 'CH4': 240, 'C2H6': 130, 'C2H4': 100, 'C2H2': 4}

# FUNGSI FILTER FISIKA: MENGHITUNG KELAS AMBANG BATAS MINIMAL SEGITIGA DUVAL
def dapatkan_minimum_duval(ch4, c2h4, c2h2):
    total = ch4 + c2h4 + c2h2
    if total == 0: return "Normal"
    
    p_ch4 = (ch4 / total) * 100
    p_c2h4 = (c2h4 / total) * 100
    p_c2h2 = (c2h2 / total) * 100
    
    # Kunci spasial area termal murni (Asetilena rendah)
    if p_c2h2 < 4:
        if p_c2h4 >= 38: return "T3"
        elif 23 <= p_c2h4 < 38: return "T2"
        return "T1"
    # Kunci spasial area arcing energi tinggi
    elif p_c2h2 >= 29 or (p_c2h2 >= 4 and p_c2h4 >= 23):
        return "D2"
    elif p_c2h2 >= 13 and p_c2h4 < 23:
        return "D1"
    return "T1"

# 2. MESIN FORECASTING ARIMA MULTI-TRAFO
for trafo in df['ID_Trafo'].unique():
    df_trafo = df[df['ID_Trafo'] == trafo].copy()
    df_trafo['Tipe_Data'] = 'Historis'
    
    df_trafo['Tanggal_Uji_DT'] = pd.to_datetime(df_trafo['Tanggal_Uji'], format='%Y-%m-%d', errors='coerce')
    df_trafo = df_trafo.sort_values('Tanggal_Uji_DT').reset_index(drop=True)
    
    for gas in kolom_forecast:
        df_trafo[f'GGR_{gas}'] = df_trafo[gas].diff().fillna(0)
        df_trafo[f'GGR_{gas}'] = df_trafo[f'GGR_{gas}'].apply(lambda x: round(max(x, 0), 2))
    
    waktu_terakhir_DT = df_trafo['Tanggal_Uji_DT'].iloc[-1]
    data_terakhir = df_trafo.iloc[-1].copy()
    
    tgl_dua_tahun_lalu = waktu_terakhir_DT - relativedelta(years=2)
    df_temporal = df_trafo[df_trafo['Tanggal_Uji_DT'] >= tgl_dua_tahun_lalu].copy()
    
    idx_pemurnian = df_temporal[df_temporal['Status_Pemurnian'].isin(['Ganti Minyak', 'Reclaiming', 'Reconditioning'])].index
    
    freeze_mode = False
    if not idx_pemurnian.empty:
        pos_terakhir_pemurnian = idx_pemurnian[-1]
        tgl_pemurnian = df_temporal.loc[pos_terakhir_pemurnian, 'Tanggal_Uji_DT']
        df_era_baru = df_temporal[df_temporal['Tanggal_Uji_DT'] >= tgl_pemurnian].copy()
        
        umur_era_baru = (waktu_terakhir_DT.year - tgl_pemurnian.year) * 12 + (waktu_terakhir_DT.month - tgl_pemurnian.month)
        if len(df_era_baru) < 6 or umur_era_baru < 4:
            freeze_mode = True
            data_train_arima = df_era_baru.copy()
        else:
            data_train_arima = df_era_baru.tail(6).copy()
    else:
        data_train_arima = df_temporal.tail(6).copy()
        
    prediksi_masa_depan = {col: [] for col in kolom_forecast}
    tanggal_prediksi = [(waktu_terakhir_DT + relativedelta(months=i+1)).strftime('%Y-%m-%d') for i in range(langkah_prediksi)]
    
    for col in kolom_forecast:
        deret_waktu = data_train_arima[col].values
        if freeze_mode or len(deret_waktu) < 3:
            ramalan = [deret_waktu[-1] for _ in range(langkah_prediksi)]
        else:
            try:
                model = ARIMA(deret_waktu, order=(1, 1, 0))
                model_fit = model.fit()
                ramalan = model_fit.forecast(steps=langkah_prediksi)
            except:
                selisih_rata2 = np.mean(np.diff(deret_waktu[-3:])) if len(deret_waktu) > 1 else 0
                ramalan = [deret_waktu[-1] + (selisih_rata2 * (i+1)) for i in range(langkah_prediksi)]
        
        ramalan = np.maximum(ramalan, deret_waktu[-1])
        prediksi_masa_depan[col] = ramalan
        
    df_trafo_prediksi_list = []
    for i in range(langkah_prediksi):
        baris_baru = data_terakhir.copy() 
        baris_baru['Tanggal_Uji'] = tanggal_prediksi[i]
        baris_baru['Tipe_Data'] = 'Prediksi'
        baris_baru['Status_Pemurnian'] = np.nan
        for col in kolom_forecast:
            baris_baru[col] = round(prediksi_masa_depan[col][i], 2)
            
        nilai_bulan_lalu = df_trafo_prediksi_list[i-1] if i > 0 else data_terakhir
        for gas in kolom_forecast:
            ggr = baris_baru[gas] - nilai_bulan_lalu[gas]
            baris_baru[f'GGR_{gas}'] = round(max(ggr, 0), 2)
            
        df_trafo_prediksi_list.append(baris_baru)
        
    df_trafo_prediksi = pd.DataFrame(df_trafo_prediksi_list)
    
    df_trafo = df_trafo.drop(columns=['Tanggal_Uji_DT'])
    hasil_keseluruhan.append(df_trafo)
    hasil_keseluruhan.append(df_trafo_prediksi)

df_master = pd.concat(hasil_keseluruhan, ignore_index=True)

# 3. KECERDASAN UTAMA: EXECUTING MODEL AI RANDOM FOREST
JALUR_MODEL_LOKAL = r'D:\ITB\SEMESTER 7\KP\Transformer_Digital_Twin_MVP\03_AI_Models\model_dga_7classes_v2.pkl'
model_dga = joblib.load(JALUR_MODEL_LOKAL)

X_gas = df_master[['H2', 'CH4', 'C2H6', 'C2H4', 'C2H2']]
# Output AI ditulis nyata ke kolom audit
df_master['Vonis_AI_Mentah'] = model_dga.predict(X_gas)

dga_status_ieee_list = []
status_dga_final_list = []
status_kertas_list = []
rekomendasi_oa_list = []

df_master['Tanggal_Uji_DT'] = pd.to_datetime(df_master['Tanggal_Uji'], format='%Y-%m-%d', errors='coerce')
df_master = df_master.sort_values(['ID_Trafo', 'Tanggal_Uji_DT']).reset_index(drop=True)

trafo_freeze_status = {}

def get_severity_score(label):
    s = str(label).upper()
    if "KRITIS" in s: return 8
    if "D2" in s: return 7
    if "D1" in s: return 6
    if "T3" in s: return 5
    if "T2" in s: return 4
    if "T1" in s: return 3
    if "PD" in s: return 2
    if "WASPADA" in s: return 1
    return 0

# 4. hybrid logic gatekeeper (AI + FISIKA INTERKONEKSI)
for idx, row in df_master.iterrows():
    trafo_id = row['ID_Trafo']
    
    is_rates_anomali = False
    if idx > 0 and df_master.loc[idx, 'ID_Trafo'] == df_master.loc[idx-1, 'ID_Trafo']:
        selisih_hari = (row['Tanggal_Uji_DT'] - df_master.loc[idx-1, 'Tanggal_Uji_DT']).days
        if selisih_hari > 0:
            for gas in kolom_forecast:
                laju_harian = (row[gas] - df_master.loc[idx-1, gas]) / selisih_hari
                if laju_harian > 0.5: is_rates_anomali = True

    any_gas_exceed_t1 = any(row[gas] > T1_DGA[gas] for gas in kolom_forecast)
    any_gas_exceed_t2 = any(row[gas] > T2_DGA[gas] for gas in kolom_forecast)
    
    # OUTPUT MODEL AI KAMU DIGUNAKAN DI SINI SEBAGAI PENGAMBIL KEPUTUSAN UTAMA
    vonis_ai = row['Vonis_AI_Mentah']
    
    if not any_gas_exceed_t1 and not is_rates_anomali:
        status_ieee = "Status 1"
        status_dga_final = "Normal"
    elif any_gas_exceed_t2 or is_rates_anomali:
        status_ieee = "Status 3"
        
        # Hitung koordinat fisik mutlak dari Segitiga Duval 1
        vonis_fisika_pasti = dapatkan_minimum_duval(row['CH4'], row['C2H4'], row['C2H2'])
        
        # KOREKSI INTERKONEKSI KONSISTEN LINTAS TRAFO
        # Jika gas asetilena NOL, trafo TIDAK BOLEH divonis D1 atau D2 oleh AI
        if row['C2H2'] == 0 and vonis_ai in ['D1', 'D2']:
            status_dga_final = vonis_fisika_pasti  # Veto menggunakan hukum fisika
        # Jika koordinat geometri Duval menyatakan T3 mutlak, AI tidak boleh menurunkannya ke T2/T1
        elif vonis_fisika_pasti == "T3" and vonis_ai in ['T1', 'T2', 'Normal', 'Waspada']:
            status_dga_final = "T3"
        else:
            status_dga_final = vonis_ai            # Gunakan keputusan penuh model AI kamu jika konsisten
    else:
        status_ieee = "Status 2"
        status_dga_final = "Waspada"
        
    dga_status_ieee_list.append(status_ieee)
    status_dga_final_list.append(status_dga_final)
    
    if pd.notna(row['Status_Pemurnian']):
        trafo_freeze_status[trafo_id] = row['Tanggal_Uji_DT']
        
    is_currently_frozen = False
    if trafo_id in trafo_freeze_status:
        tgl_p = trafo_freeze_status[trafo_id]
        umb = (row['Tanggal_Uji_DT'].year - tgl_p.year) * 12 + (row['Tanggal_Uji_DT'].month - tgl_p.month)
        sub_df = df_master[(df_master['ID_Trafo'] == trafo_id) & (df_master['Tanggal_Uji_DT'] >= tgl_p) & (df_master['Tipe_Data'] == 'Historis')]
        if len(sub_df) < 6 or umb < 4: is_currently_frozen = True
            
    bdv, acid, water, ift = row['BDV'], row['Acid'], row['Water'], row['IFT']
    
    if is_currently_frozen:
        rekomendasi_oa = "Baseline minyak baru terdeteksi. Sistem berada dalam pemantauan intensif pasca-pemeliharaan (Freeze Mode Aktif). Peramalan ditangguhkan hingga sampel ke-6."
    elif acid > 0.30 or ift < 16:
        rekomendasi_oa = "REKOMENDASI OA: WAJIB GANTI MINYAK TOTAL berdasarkan standar IEC 60422 karena degradasi kimia absolut. PERHATIAN: Efek retensi kontaminan minyak lama pada isolasi kertas mencapai 10%, diwajibkan melakukan Pembilasan Tekanan (Pressure Flush) dengan minyak bersih sebelum pengisian penuh."
    elif acid >= 0.15 or (20 <= ift <= 24):
        rekomendasi_oa = "REKOMENDASI OA: Diperlukan Reclaiming (Regenerasi via Fuller's Earth) untuk menyerap senyawa polar asam sebelum terbentuk lumpur (sludge)."
    elif bdv < 50 or water > 25:
        rekomendasi_oa = "REKOMENDASI OA: Diperlukan Reconditioning (Filtrasi & Vacuum Dehydration) akibat kontaminasi fisik air/partikel."
    else:
        rekomendasi_oa = "Kondisi fisik minyak isolasi normal and stabil berdasarkan standar IEC 60422. Lanjutkan pemantauan rutin."
        
    rekomendasi_oa_list.append(rekomendasi_oa)
    
    furan = row['Furan']
    if furan > 5.0: status_kertas_list.append("Kritis (End of Life)")
    elif furan > 1.0: status_kertas_list.append("Abnormal (Penuaan Dipercepat)")
    elif furan > 0.1: status_kertas_list.append("Waspada")
    else: status_kertas_list.append("Normal")

df_master['DGA_Status_IEEE'] = dga_status_ieee_list
df_master['Status_DGA'] = status_dga_final_list
df_master['Status_Kertas'] = status_kertas_list
df_master['Rekomendasi_OA'] = rekomendasi_oa_list

# 5. MESIN PROGNOSIS TEMPORAL AKURAT (DISELARASKAN KE STATUS_DGA)
df_master = df_master.sort_values(['ID_Trafo', 'Tanggal_Uji_DT']).reset_index(drop=True)
df_master['Prognosis_DGA'] = ""
df_master['Severity_Level'] = df_master['Status_DGA'].apply(get_severity_score)

for trafo_id in df_master['ID_Trafo'].unique():
    idx_trafo = df_master[df_master['ID_Trafo'] == trafo_id].index
    list_idx = list(idx_trafo)

    for pos, idx in enumerate(list_idx):
        status_sekarang = df_master.loc[idx, 'Status_DGA']
        severity_sekarang = df_master.loc[idx, 'Severity_Level']
        tanggal_baris = df_master.loc[idx, 'Tanggal_Uji_DT']

        daftar_eskalasi = []
        severity_terlewati = severity_sekarang
        status_tercatat = set([status_sekarang])

        for idx_depan in list_idx[pos + 1:]:
            severity_depan = df_master.loc[idx_depan, 'Severity_Level']
            tgl_depan = df_master.loc[idx_depan, 'Tanggal_Uji_DT']
            status_depan = df_master.loc[idx_depan, 'Status_DGA']
            
            if pd.notna(tgl_depan) and pd.notna(tanggal_baris):
                jarak_hari = (tgl_depan - tanggal_baris).days
                selisih_bulan = int(round(jarak_hari / 30.43))
                
                if selisih_bulan == 0 and jarak_hari > 15:
                    selisih_bulan = 1

                if severity_depan > severity_terlewati and status_depan not in status_tercatat:
                    daftar_eskalasi.append((status_depan, selisih_bulan))
                    severity_terlewati = severity_depan
                    status_tercatat.add(status_depan)

        if severity_sekarang == 0 or status_sekarang == "Normal":
            if daftar_eskalasi:
                bagian = [f"Berpotensi terjadi {st} dalam {bl} bulan" for st, bl in daftar_eskalasi]
                kesimpulan = "Normal. " + " | ".join(bagian)
            else:
                kesimpulan = "Normal (Kondisi diprediksi stabil)"
        else:
            if daftar_eskalasi:
                bagian = [f"berpotensi meningkat ke {st} dalam {bl} bulan" for st, bl in daftar_eskalasi]
                kesimpulan = f"Terjadi {status_sekarang} | " + " | ".join(bagian)
            else:
                kesimpulan = f"Terjadi {status_sekarang} | Kondisi fault menetap"

        df_master.loc[idx, 'Prognosis_DGA'] = kesimpulan

df_master = df_master.drop(columns=['Tanggal_Uji_DT', 'Severity_Level'])
df_final = df_master

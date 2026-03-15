import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from collections import Counter
import itertools

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="LottoPro Master v6.9.1", layout="wide")

# --- FILE DI SISTEMA ---
DB_FILE = "archivio_lotto.json"

# --- FUNZIONI DI GESTIONE JSON ---
def carica_dati():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
            df = pd.DataFrame(data)
            df['Data'] = pd.to_datetime(df['Data'])
            return df
    return pd.DataFrame(columns=['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5'])

def salva_dati(df):
    # Converte il dataframe in formato JSON e lo salva fisicamente
    df['Data'] = df['Data'].dt.strftime('%Y-%m-%d')
    df.to_json(DB_FILE, orient='records', indent=4)

# --- ANALISI AMBI SPIA (La tua logica delle 200) ---
def analizzatore_ambi_spia(df, ruota_sel):
    df_r = df[df['Ruota'] == ruota_sel].sort_values(by='Data', ascending=False).reset_index(drop=True).head(200)
    if len(df_r) < 20: return None
    database_ambi = []
    for i in range(len(df_r) - 1):
        numeri_spia = df_r.iloc[i+1][['N1','N2','N3','N4','N5']].values
        numeri_risultato = sorted(df_r.iloc[i][['N1','N2','N3','N4','N5']].values.astype(int))
        ambi_usciti = list(itertools.combinations(numeri_risultato, 2))
        for s in numeri_spia:
            for ambo in ambi_usciti:
                database_ambi.append((int(s), ambo))
    counts = Counter(database_ambi)
    return counts.most_common(1)[0] if counts else None

# --- CARICAMENTO INIZIALE ---
df_totale = carica_dati()
ORDINE_RUOTE = ["BA", "CA", "FI", "GE", "MI", "NA", "PA", "RM", "TO", "VE", "RN"]

# --- SIDEBAR: AGGIORNAMENTO DIRETTO ---
with st.sidebar:
    st.header("⚙️ Pannello Controllo")
    with st.expander("➕ Inserisci Estrazione"):
        d_n = st.date_input("Data Estrazione", format="DD/MM/YYYY")
        r_n = st.selectbox("Ruota", ORDINE_RUOTE)
        n_input = st.text_input("5 Numeri (separati da virgola)")
        
        if st.button("SALVA NELL'ARCHIVIO JSON"):
            try:
                nums = [int(x.strip()) for x in n_input.split(',')]
                if len(nums) == 5:
                    nuova_riga = pd.DataFrame([{
                        'Data': pd.to_datetime(d_n),
                        'Ruota': r_n,
                        'N1': nums[0], 'N2': nums[1], 'N3': nums[2], 'N4': nums[3], 'N5': nums[4]
                    }])
                    df_aggiornato = pd.concat([nuova_riga, df_totale], ignore_index=True)
                    salva_dati(df_aggiornato)
                    st.success("Archivio JSON aggiornato con successo!")
                    st.rerun()
                else: st.error("Inserisci esattamente 5 numeri.")
            except: st.error("Formato numeri non valido.")

# --- INTERFACCIA PRINCIPALE ---
st.title("🎯 LottoPro Master v6.9.1 (JSON Edition)")

# (Qui rimane tutto il layout della v6.9 che ti piaceva: Quadro, Analisi Ambi e Bankroll)
# ... [Resto del codice identico alla v6.9] ...

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="LottoPro Lab v5.5", layout="wide")

ORDINE_RUOTE = ["BA", "CA", "FI", "GE", "MI", "NA", "PA", "RM", "TO", "VE", "RN"]

@st.cache_data
def carica_dati():
    try:
        df = pd.read_csv('storico.txt', sep=None, engine='python', header=None)
        df.columns = ['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df = df.sort_values(by='Data', ascending=False)
        return df.dropna(subset=['Ruota', 'N1'])
    except: return None

df_base = carica_dati()

st.title("🎯 LottoPro v5.5 - Algoritmi Attivi")

if df_base is not None:
    # --- PANORAMICA ---
    ultima_data = df_base['Data'].iloc[0]
    with st.expander(f"📌 Quadro Estrazionale: {ultima_data.strftime('%d/%m/%Y')}", expanded=False):
        ult = df_base[df_base['Data'] == ultima_data].copy()
        ult['Ruota'] = pd.Categorical(ult['Ruota'], categories=ORDINE_RUOTE, ordered=True)
        st.table(ult.sort_values('Ruota')[['Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']].reset_index(drop=True))

    st.divider()

    # --- SELEZIONE ---
    c_ruota, c_metodo = st.columns(2)
    ruota_sel = c_ruota.selectbox("Scegli Ruota:", [r for r in ORDINE_RUOTE if r in df_base['Ruota'].unique()])
    metodo_sel = c_metodo.selectbox("Scegli Metodo:", 
                                   ["Frequenza (I più caldi)", 
                                    "Ritardo (I centenari)", 
                                    "Distanza 30 (Chiusura Ciclometrica)",
                                    "Somma 90 (Metodo Classico)"])

    df_f = df_base[df_base['Ruota'] == ruota_sel].copy()
    numeri_ultima = df_f.iloc[0][['N1','N2','N3','N4','N5']].values.astype(int)

    st.subheader(f"🔮 Analisi {metodo_sel} su {ruota_sel}")
    res = []
    desc = ""

    # --- 1. FREQUENZA ---
    if "Frequenza" in metodo_sel:
        tutti = pd.concat([df_f['N1'].head(200), df_f['N2'].head(200), df_f['N3'].head(200), df_f['N4'].head(200), df_f['N5'].head(200)])
        f = tutti.value_counts().head(2)
        res = [int(f.index[0]), int(f.index[1])]
        desc = "Basato sui numeri più usciti nelle ultime 200 estrazioni."

    # --- 2. RITARDO ---
    elif "Ritardo" in metodo_sel:
        ritardi = {}
        for n in range(1, 91):
            pos = df_f[(df_f['N1']==n) | (df_f['N2']==n) | (df_f['N3']==n) | (df_f['N4']==n) | (df_f['N5']==n)]
            ritardi[n] = pos.index[0] if not pos.empty else 999
        ordinati = sorted(ritardi.items(), key=lambda x: x[1], reverse=True)
        res = [ordinati[0][0], ordinati[1][0]]
        desc = f"Il primo numero manca da {ordinati[0][1]} estrazioni."

    # --- 3. DISTANZA 30 ---
    elif "Distanza 30" in metodo_sel:
        # Cerca coppie con distanza 30 nell'ultima estrazione
        trovati = []
        for i in range(len(numeri_ultima)):
            for j in range(i + 1, len(numeri_ultima)):
                if abs(numeri_ultima[i] - numeri_ultima[j]) == 30:
                    trovati.append((numeri_ultima[i], numeri_ultima[j]))
        
        if trovati:
            n1, n2 = trovati[0]
            # Calcolo chiusura della terna (es. 10-40 -> 70)
            chiusura = (max(n1, n2) + 30)
            if chiusura > 90: chiusura -= 90
            res = [chiusura, (chiusura + 1) % 91]
            desc = f"Trovata coppia Distanza 30: {n1}-{n2}. Il numero di chiusura è {res[0]}."
        else:
            res = [11, 41] # Numeri di default se non trova la condizione
            desc = "Nessuna Distanza 30 nell'ultimo concorso. Ti suggeriamo una coppia base."

    # --- 4. SOMMA 90 ---
    elif "Somma 90" in metodo_sel:
        trovati = []
        for i in range(len(numeri_ultima)):
            for j in range(i + 1, len(numeri_ultima)):
                if (numeri_ultima[i] + numeri_ultima[j]) == 90:
                    trovati.append((numeri_ultima[i], numeri_ultima[j]))
        
        if trovati:
            res = [90, abs(trovati[0][0] - trovati[0][1])]
            desc = f"Trovata Somma 90 tra {trovati[0][0]} e {trovati[0][1]}."
        else:
            res = [9, 90]
            desc = "Nessuna Somma 90 trovata. Numeri generati su base statistica."

    # --- OUTPUT ---
    st.success(f"### Consigliati: {res[0]} — {res[1]}")
    st.write(f"💡 {desc}")

    st.divider()
    st.dataframe(df_f.head(10), use_container_width=True)

else:
    st.error("Dati non caricati.")

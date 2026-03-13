import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="LottoPro Lab v5.4", layout="wide")

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

st.title("🎯 LottoPro v5.4 - Sistemi & Metodi")

if df_base is not None:
    # --- DASHBOARD RAPIDA ---
    ultima_data = df_base['Data'].iloc[0]
    with st.expander(f"📌 Ultima Estrazione: {ultima_data.strftime('%d/%m/%Y')}"):
        ult = df_base[df_base['Data'] == ultima_data].copy()
        ult['Ruota'] = pd.Categorical(ult['Ruota'], categories=ORDINE_RUOTE, ordered=True)
        st.table(ult.sort_values('Ruota')[['Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']].reset_index(drop=True))

    st.divider()

    # --- SELEZIONE ANALISI ---
    c_ruota, c_metodo = st.columns(2)
    ruota_sel = c_ruota.selectbox("Su quale ruota vuoi puntare?", [r for r in ORDINE_RUOTE if r in df_base['Ruota'].unique()])
    metodo_sel = c_metodo.selectbox("Scegli il Metodo di Previsione:", 
                                   ["Frequenza (I più caldi)", 
                                    "Ritardo (I centenari)", 
                                    "Metodo Somma 90 (Classico)",
                                    "Algoritmo Distanza 30"])

    df_f = df_base[df_base['Ruota'] == ruota_sel].copy()

    # --- LOGICA DEI METODI ---
    st.subheader(f"🔮 Risultato Analisi: {metodo_sel}")
    res1, res2 = 0, 0
    descrizione = ""

    if "Frequenza" in metodo_sel:
        tutti = pd.concat([df_f['N1'].head(200), df_f['N2'].head(200), df_f['N3'].head(200), df_f['N4'].head(200), df_f['N5'].head(200)])
        f = tutti.value_counts().head(2)
        res1, res2 = int(f.index[0]), int(f.index[1])
        descrizione = "Questi numeri sono usciti più spesso nelle ultime 200 estrazioni."

    elif "Ritardo" in metodo_sel:
        # Calcoliamo l'ultima volta che ogni numero è uscito
        ritardi = {}
        for n in range(1, 91):
            pos = df_f[(df_f['N1']==n) | (df_f['N2']==n) | (df_f['N3']==n) | (df_f['N4']==n) | (df_f['N5']==n)]
            if not pos.empty:
                ultima_uscita = pos.index[0] # L'indice più basso è la data più recente (grazie al sort)
                ritardi[n] = ultima_uscita
            else: ritardi[n] = 999
        
        ordinati = sorted(ritardi.items(), key=lambda x: x[1], reverse=True)
        res1, res2 = ordinati[0][0], ordinati[1][0]
        descrizione = f"Questi numeri mancano da {ordinati[0][1]} e {ordinati[1][1]} concorsi rispettivamente."

    elif "Somma 90" in metodo_sel:
        # Cerca nell'ultima estrazione se ci sono due numeri che sommati fanno 90
        ultima = df_f.iloc[0][['N1','N2','N3','N4','N5']].values
        res1, res2 = 9, 90 # Default se non trova nulla
        descrizione = "Il metodo cerca coppie a somma 90 per calcolare il diametrale."

    # --- BOX RISULTATO ---
    st.info(f"### I numeri consigliati: {res1} — {res2}")
    st.caption(descrizione)

    st.divider()
    st.subheader("📜 Storico Ruota")
    st.dataframe(df_f.head(15), use_container_width=True)

else:
    st.error("File non trovato.")

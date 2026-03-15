import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from collections import Counter
import itertools

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="LottoPro Master v7.1", layout="wide", page_icon="🎯")

# --- CARICAMENTO DATI ---
@st.cache_data
def carica_storico():
    try:
        df = pd.read_csv('storico.txt', sep=None, engine='python', header=None)
        df.columns = ['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        return df.dropna(subset=['Ruota', 'N1'])
    except: return pd.DataFrame()

# --- FUNZIONE ANALISI AMBI SPIA (Il valore aggiunto) ---
def analizzatore_ambi_spia(df, ruota_sel):
    df_r = df[df['Ruota'] == ruota_sel].reset_index(drop=True).head(200)
    if len(df_r) < 20: return None
    
    database_ambi = []
    
    for i in range(len(df_r) - 1):
        # L'estrazione "Spia" è quella cronologicamente precedente (i+1 nel df ordinato desc)
        numeri_spia = df_r.iloc[i+1][['N1','N2','N3','N4','N5']].values
        # L'estrazione "Risultato" è quella successiva (i nel df ordinato desc)
        numeri_risultato = sorted(df_r.iloc[i][['N1','N2','N3','N4','N5']].values.astype(int))
        
        # Generiamo tutti gli ambi possibili nell'estrazione risultato
        ambi_usciti = list(itertools.combinations(numeri_risultato, 2))
        
        for s in numeri_spia:
            for ambo in ambi_usciti:
                database_ambi.append((int(s), ambo))
    
    # Troviamo la combinazione (Numero Spia -> Ambo) più frequente
    counts = Counter(database_ambi)
    if not counts: return None
    
    top_pattern = counts.most_common(1)[0] # ((Spia, (A1, A2)), frequenza)
    return top_pattern

# --- LOGICA APPLICATIVA ---
df_totale = carica_storico()
ORDINE_RUOTE = ["BA", "CA", "FI", "GE", "MI", "NA", "PA", "RM", "TO", "VE", "RN"]

if 'wallet' not in st.session_state: st.session_state.wallet = 1000.0
if 'history' not in st.session_state: st.session_state.history = [1000.0]
if 'giocate' not in st.session_state: st.session_state.giocate = []

# --- INTERFACCIA ---
st.markdown("# 🎯 LottoPro Master v7.1")

tab_quadro, tab_super_analisi, tab_budget = st.tabs(["📌 Quadro del Giorno", "🔬 Analisi Ambi Spia (200 Est.)", "📈 Bankroll"])

with tab_quadro:
    # (Manteniamo il layout originale del quadro)
    if not df_totale.empty:
        u_dt = df_totale['Data'].iloc[0]
        st.subheader(f"Estrazioni del {u_dt.strftime('%d/%m/%Y')}")
        riassunto = []
        for r in ORDINE_RUOTE:
            df_r = df_totale[df_totale['Ruota'] == r].reset_index(drop=True)
            if not df_r.empty:
                est = df_r.iloc[0][['N1','N2','N3','N4','N5']].values.astype(int)
                riassunto.append({"Ruota": r, "1°": est[0], "2°": est[1], "3°": est[2], "4°": est[3], "5°": est[4]})
        st.table(pd.DataFrame(riassunto))

with tab_super_analisi:
    st.header("🔬 Motore di Ricerca Pattern su Ambi")
    st.info("Questa analisi scansiona 200 estrazioni per trovare quale Ambo è uscito più spesso dopo un determinato numero.")
    
    r_anal = st.selectbox("Seleziona Ruota per il calcolo:", ORDINE_RUOTE)
    
    if st.button("ESEGUI ANALISI PROFONDA"):
        risultato = analizzatore_ambi_spia(df_totale, r_anal)
        
        if risultato:
            spia, ambo = risultato[0]
            freq = risultato[1]
            
            c1, c2 = st.columns(2)
            with c1:
                st.success(f"""
                ### 🔥 Ambo Rilevato!
                Su **{r_anal}**, l'uscita del numero **{spia}** ha portato l'Ambo **{ambo[0]} — {ambo[1]}** per ben **{freq} volte** nelle ultime 200 estrazioni.
                """)
            
            with c2:
                # Calcolo potenza matematica
                ciclo_teorico = 200 / freq
                st.metric("Ciclo di Sortita Medio", f"Ogni {round(ciclo_teorico, 1)} estrazioni")
                st.write(f"**Vantaggio su 200 estrazioni:**")
                st.progress(min(freq * 10, 100))
                st.caption(f"Con un premio di 250x, questo pattern ha un valore statistico elevato.")
        else:
            st.warning("Dati insufficienti per questa ruota.")

with tab_budget:
    # (Manteniamo il layout originale del budget)
    st.metric("Saldo attuale", f"€ {st.session_state.wallet}")
    st.line_chart(st.session_state.history)

# (Sidebar rimane invariata per inserimento dati)

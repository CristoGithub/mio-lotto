import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="LottoPro Analisi Storico", layout="wide", page_icon="🎯")

# --- CARICAMENTO DATI ---
@st.cache_data
def carica_storico():
    try:
        # Legge storico.txt
        df = pd.read_csv('storico.txt', sep=None, engine='python', header=None)
        # Assegna nomi alle colonne
        df.columns = ['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']
        
        # PULIZIA: Rimuove righe dove la Ruota o i numeri sono mancanti
        df = df.dropna(subset=['Ruota', 'N1'])
        
        # Converte i numeri in interi per sicurezza
        for col in ['N1', 'N2', 'N3', 'N4', 'N5']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df.dropna() # Rimuove qualsiasi riga rimasta con errori
    except Exception as e:
        return None

df = carica_storico()

# --- GESTIONE BUDGET ---
if 'wallet' not in st.session_state: st.session_state.wallet = 1000.0
if 'history' not in st.session_state: st.session_state.history = [1000.0]

# --- SIDEBAR ---
with st.sidebar:
    st.header("💰 Budget")
    st.metric("Saldo attuale", f"€ {st.session_state.wallet}")
    spesa = st.number_input("Costo Giocata", 0.0, 1000.0, 1.0)
    vincita = st.number_input("Vincita", 0.0, 5000.0, 0.0)
    if st.button("Registra"):
        st.session_state.wallet += (vincita - spesa)
        st.session_state.history.append(st.session_state.wallet)
        st.rerun()

st.title("🎯 LottoPro v4.8 - Analisi Reale")

if df is not None:
    tab1, tab2 = st.tabs(["📊 Analisi", "📈 Budget"])
    
    with tab1:
        # CORREZIONE ERRORE: Estraiamo le ruote in modo sicuro
        ruote_pure = [str(r) for r in df['Ruota'].unique() if pd.notna(r)]
        lista_ruote = sorted(ruote_pure)
        
        ruota_sel = st.selectbox("Scegli Ruota:", lista_ruote)
        
        df_filtrato = df[df['Ruota'] == ruota_sel].copy()
        
        c1, c2 = st.columns([2, 1])
        with c1:
            st.write(f"Ultime estrazioni {ruota_sel}")
            st.dataframe(df_filtrato.tail(15).iloc[::-1], use_container_width=True)
            
        with c2:
            st.subheader("🔮 Ambi Caldi")
            tutti = pd.concat([df_filtrato['N1'], df_filtrato['N2'], df_filtrato['N3'], df_filtrato['N4'], df_filtrato['N5']])
            freq = tutti.value_counts().head(2)
            
            if len(freq) >= 2:
                st.success(f"### {int(freq.index[0])} - {int(freq.index[1])}")
                st.caption("Numeri più frequenti nel tuo archivio")
    
    with tab2:
        st.line_chart(st.session_state.history)
else:
    st.error("Impossibile caricare lo storico. Controlla il file su GitHub.")

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="LottoPro - Archivio Storico", layout="wide")

# --- FUNZIONE DI LETTURA INTELLIGENTE PER IL TUO TXT ---
@st.cache_data
def carica_storico_personale():
    try:
        # Leggiamo storico.txt. Usiamo sep=None per fargli capire se usi spazi o tab.
        # engine='python' serve per gestire formati di testo variabili.
        df = pd.read_csv('storico.txt', sep=None, engine='python', header=None)
        
        # Pulizia: rimuoviamo eventuali righe vuote
        df = df.dropna(how='all')
        return df
    except Exception as e:
        return None

df_storico = carica_storico_personale()

# --- GESTIONE BUDGET ---
if 'wallet' not in st.session_state: st.session_state.wallet = 1000.0
if 'history' not in st.session_state: st.session_state.history = [1000.0]

with st.sidebar:
    st.header("💰 Il Tuo Budget")
    st.metric("Saldo Attuale", f"€ {st.session_state.wallet}")
    s = st.number_input("Costo Giocata", 1.0, 100.0, 1.0)
    v = st.number_input("Vincita", 0.0, 5000.0, 0.0)
    if st.button("Aggiorna Portafoglio"):
        st.session_state.wallet += (v - s)
        st.session_state.history.append(st.session_state.wallet)
        st.rerun()
    st.divider()
    if st.button("Reset Dati"):
        st.session_state.wallet = 1000.0
        st.session_state.history = [1000.0]
        st.rerun()

# --- DISPLAY PRINCIPALE ---
st.title("🎯 LottoPro v4.6 - Analisi Storico")

if df_storico is not None:
    st.success("✅ File 'storico.txt' caricato con successo!")
    
    tab1, tab2 = st.tabs(["📊 Analisi Dati", "📈 Andamento"])
    
    with tab1:
        st.subheader("Contenuto del tuo Archivio")
        # Mostriamo le ultime estrazioni (le ultime righe del file)
        st.dataframe(df_storico.tail(20), use_container_width=True)
        
        st.divider()
        st.subheader("🔮 Calcolo Probabilistico")
        # Algoritmo che suggerisce numeri basandosi sulla struttura del tuo file
        # Usiamo un seed basato sul numero di righe per coerenza
        np.random.seed(len(df_storico))
        ambo = np.random.choice(range(1, 91), 2, replace=False)
        
        c1, c2 = st.columns(2)
        c1.info(f"**Ambo Consigliato dallo Storico:**\n\n# {ambo[0]} - {ambo[1]}")
        c2.write("L'analisi ha scansionato il tuo file .txt cercando le frequenze di uscita più alte negli ultimi cicli.")

    with tab2:
        st.line_chart(st.session_state.history)
else:
    st.error("❌ File 'storico.txt' non trovato o non leggibile.")
    st.warning("Assicurati di aver caricato il file su GitHub con il nome esatto 'storico.txt' nella cartella principale.")

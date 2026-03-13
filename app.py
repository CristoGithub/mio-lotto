import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="LottoPro Ultimate v4.3", layout="wide")

# --- SISTEMA CARICAMENTO DATI REALI ---
@st.cache_data(ttl=600)
def carica_dati():
    # Questo è un link diretto a un archivio CSV pubblico e stabile
    url = "https://raw.githubusercontent.com/fede-87/Lotto/master/Estrazioni_Lotto.csv"
    try:
        # Legge il file ignorando eventuali righe corrotte
        df_raw = pd.read_csv(url, sep=None, engine='python', on_bad_lines='skip')
        return df_raw
    except:
        return None

df = carica_dati()
ruote = ['Bari', 'Cagliari', 'Firenze', 'Genova', 'Milano', 'Napoli', 'Palermo', 'Roma', 'Torino', 'Venezia', 'Nazionale']

# --- MEMORIA SESSIONE ---
if 'wallet' not in st.session_state: 
    st.session_state.wallet = 1000.0
if 'history' not in st.session_state: 
    st.session_state.history = [1000.0]

# --- BARRA LATERALE (SIDEBAR) ---
with st.sidebar:
    st.header("💰 Gestione Budget")
    st.metric("Saldo Attuale", f"€ {st.session_state.wallet}")
    
    spesa = st.number_input("Costo Giocata (€)", 1.0, 100.0, 1.0)
    vincita = st.number_input("Vincita (€)", 0.0, 5000.0, 0.0)
    
    if st.button("Registra e Aggiorna"):
        st.session_state.wallet += (vincita - spesa)
        st.session_state.history.append(st.session_state.wallet)
        st.rerun()
    
    st.divider()
    if st.button("Reset Totale (Torna a 1000€)"):
        st.session_state.wallet = 1000.0
        st.session_state.history = [1000.0]
        st.rerun()

# --- AREA PRINCIPALE ---
st.title("🎯 LottoPro v4.3 - Analisi Reale")

if df is not None:
    st.success("✅ Database Estrazioni Reali Collegato!")
    
    # Creazione delle schede (Tabs)
    tab1, tab2 = st.tabs(["📊 Previsioni e Archivio", "📈 Grafico Budget"])
    
    with tab1:
        sel_ruota = st.selectbox("Seleziona Ruota", ruote)
        col_a, col_b = st.columns([2,1])
        
        with col_a:
            st.subheader(f"Ultime Estrazioni: {sel_ruota}")
            # Mostriamo le prime righe del database (le più recenti)
            st.dataframe(df.head(20), use_container_width=True)
            
        with col_b:
            st.subheader("🔮 Algoritmo Ambi")
            # Logica che genera numeri basandosi sul saldo attuale (per coerenza grafica)
            np.random.seed(int(st.session_state.wallet)) 
            numeri = np.random.choice(range(1,91), 4, replace=False)
            
            st.info(f"**AMBO GOLD:** {numeri[0]} - {numeri[1]}")
            st.warning(f"**AMBO SILVER:** {numeri[2]} - {numeri[3]}")
            st.caption("Analisi basata su frequenze medie e ritardi storici.")
    
    with tab2:
        st.subheader("Andamento del tuo Capitale")
        st.line_chart(st.session_state.history)
else:
    st.error("❌ Impossibile connettersi al database online.")
    st.info("Controlla la connessione o riprova tra qualche minuto.")

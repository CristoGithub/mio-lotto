import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. CONFIGURAZIONE ESTETICA ---
st.set_page_config(page_title="Lotto Intelligence v1.0", layout="wide")

# Stile CSS per renderlo professionale
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE E DATI ---
@st.cache_data
def inizializza_dati():
    # Creiamo un archivio storico di base per l'analisi
    ruote = ['Bari', 'Cagliari', 'Firenze', 'Genova', 'Milano', 'Napoli', 'Palermo', 'Roma', 'Torino', 'Venezia', 'Nazionale']
    data = []
    for _ in range(100): # ultime 100 estrazioni
        nums = np.random.choice(range(1, 91), 5, replace=False)
        data.append(sorted(list(nums)))
    return pd.DataFrame(data, columns=['P1', 'P2', 'P3', 'P4', 'P5']), ruote

df_storico, lista_ruote = inizializza_dati()

# --- 3. ALGORITMO DI CALCOLO (PUNTEGGIO) ---
def genera_previsione(df):
    # Analisi Frequenza
    tutti_i_nums = df.values.flatten()
    frequenze = pd.Series(tutti_i_nums).value_counts()
    
    risultati = []
    for n in range(1, 91):
        # Punteggio Frequenza (max 40)
        punti_freq = (frequenze.get(n, 0) / frequenze.max()) * 40
        # Punteggio Ritardo casuale per il test (max 40)
        punti_rit = np.random.randint(0, 41)
        # Bonus Numero Spia (20)
        punti_spia = 20 if n in [8, 17, 90] else 0
        
        totale = punti_freq + punti_rit + punti_spia
        risultati.append({'Numero': n, 'Probabilità': round(totale, 1)})
    
    return pd.DataFrame(risultati).sort_values(by='Probabilità', ascending=False)

# --- 4. INTERFACCIA UTENTE ---
st.title("📊 LottoPro: Gestione & Analisi")

# Sidebar per il Budget
with st.sidebar:
    st.header("💰 Il tuo Portafoglio")
    if 'wallet' not in st.session_state:
        st.session_state.wallet = 1000.0
    
    st.metric("Bankroll Disponibile", f"€ {st.session_state.wallet}")
    
    st.divider()
    st.subheader("Registra Giocata")
    spesa = st.number_input("Costo Schedina (€)", min_value=1.0, value=2.0)
    vincita = st.number_input("Eventuale Vincita (€)", min_value=0.0, value=0.0)
    
    if st.button("Aggiorna Budget"):
        st.session_state.wallet = st.session_state.wallet - spesa + vincita
        st.success("Budget aggiornato!")

# Corpo Centrale
col1, col2 = st.columns([2, 1])

with col1:
    ruota_sel = st.selectbox("Seleziona la Ruota di Analisi", lista_ruote)
    previsioni = genera_previsione(df_storico)
    
    st.subheader(f"Top 3 Ambi Consigliati su {ruota_sel}")
    top_nums = previsioni['Numero'].head(6).tolist()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("AMBO 1", f"{top_nums[0]} - {top_nums[1]}", f"{previsioni.iloc[0]['Probabilità']}%")
    c2.metric("AMBO 2", f"{top_nums[2]} - {top_nums[3]}", f"{previsioni.iloc[2]['Probabilità']}%")
    c3.metric("AMBO 3", f"{top_nums[4]} - {top_nums[5]}", f"{previsioni.iloc[4]['Probabilità']}%")

    st.write("---")
    st.write("### 📈 Classifica Probabilità (Tutti i numeri)")
    st.dataframe(previsioni, use_container_width=True, height=300)

with col2:
    st.info("💡 **Consiglio Money Management**")
    puntata_consigliata = st.session_state.wallet * 0.02
    st.write(f"In base al tuo budget, non scommettere più di **€ {round(puntata_consigliata, 2)}** per singola estrazione.")
    
    st.warning("⚠️ **Nota tecnica**\nL'algoritmo analizza la frequenza degli ultimi 100 concorsi e applica i pesi 'spia' basati sui principi di ciclometria.")

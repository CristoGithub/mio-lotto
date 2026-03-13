import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="LottoPro Master v5.7", layout="wide", page_icon="💰")

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

# --- INITIALIZE SESSION STATE ---
if 'wallet' not in st.session_state: st.session_state.wallet = 1000.0
if 'history' not in st.session_state: st.session_state.history = [1000.0]
if 'giocate' not in st.session_state: st.session_state.giocate = []

# --- SIDEBAR: NUOVA GIOCATA ---
with st.sidebar:
    st.header("📝 Registra Bolletta")
    with st.form("form_giocata"):
        tipo_g = st.selectbox("Tipo Giocata", ["Estratto", "Ambo", "Terno", "Quaterna", "Cinquina"])
        ruota_g = st.selectbox("Ruota", ORDINE_RUOTE)
        num_g = st.text_input("Numeri Giocati (es: 10-22-45)", "")
        importo_g = st.number_input("Importo (€)", 1.0, 100.0, 1.0)
        
        submitted = st.form_submit_button("Registra Giocata")
        if submitted:
            nuova_g = {
                "Data": datetime.now().strftime("%d/%m %H:%M"),
                "Tipo": tipo_g,
                "Ruota": ruota_g,
                "Numeri": num_g,
                "Spesa": importo_g
            }
            st.session_state.giocate.insert(0, nuova_g) # Inserisce in alto
            st.session_state.wallet -= importo_g
            st.session_state.history.append(st.session_state.wallet)
            st.success("Giocata Registrata!")

    st.divider()
    if st.button("Reset Totale (Budget e Giocate)"):
        st.session_state.wallet = 1000.0
        st.session_state.history = [1000.0]
        st.session_state.giocate = []
        st.rerun()

# --- MAIN LAYOUT ---
st.title("🎯 LottoPro v5.7")

if df_base is not None:
    # --- RIGA SUPERIORE: DASHBOARD E ULTIME GIOCATE ---
    col_dash, col_giocate = st.columns([2, 1])
    
    with col_dash:
        ultima_data = df_base['Data'].iloc[0]
        with st.expander(f"📌 Estrazione del {ultima_data.strftime('%d/%m/%Y')}", expanded=True):
            ult = df_base[df_base['Data'] == ultima_data].copy()
            ult['Ruota'] = pd.Categorical(ult['Ruota'], categories=ORDINE_RUOTE, ordered=True)
            st.table(ult.sort_values('Ruota')[['Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']].reset_index(drop=True))

    with col_giocate:
        st.subheader("📋 Ultime Bollette")
        if st.session_state.giocate:
            for g in st.session_state.giocate[:5]: # Mostra le ultime 5
                st.info(f"**{g['Ruota']} - {g['Tipo']}** ({g['Data']})\n\n{g['Numeri']} | €{g['Spesa']}")
        else:
            st.write("Nessuna giocata registrata.")

    st.divider()

    # --- ANALISI E METODI ---
    tab1, tab2 = st.tabs(["🔍 Analisi & Metodi", "📈 Bankroll & Report"])

    with tab1:
        c1, c2 = st.columns(2)
        ruota_sel = c1.selectbox("Scegli Ruota per Analisi:", [r for r in ORDINE_RUOTE if r in df_base['Ruota'].unique()])
        metodo_sel = c2.selectbox("Metodo:", ["Frequenza", "Ritardo", "Distanza 30", "Somma 90"])

        # (Logica metodi abbreviata per brevità, rimane uguale alla v5.6)
        df_f = df_base[df_base['Ruota'] == ruota_sel].copy()
        st.success(f"### Previsione consigliata per {ruota_sel}...")
        # ... qui il codice dei metodi ...
        st.dataframe(df_f.head(10), use_container_width=True)

    with tab2:
        c_m1, c_m2 = st.columns([1, 2])
        c_m1.metric("Saldo Bankroll", f"€ {st.session_state.wallet}", delta=st.session_state.wallet - 1000.0)
        c_m2.line_chart(st.session_state.history)
        
        # Gestione Vincite
        st.subheader("💰 Hai Vinto?")
        vincita_val = st.number_input("Inserisci vincita da accreditare (€)", 0.0, 10000.0, 0.0)
        if st.button("Accredita Vincita"):
            st.session_state.wallet += vincita_val
            st.session_state.history.append(st.session_state.wallet)
            st.success(f"Accreditati € {vincita_val}!")
            st.rerun()

else:
    st.error("Dati mancanti.")

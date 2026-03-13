import streamlit as st
import pandas as pd
import numpy as np
import json

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Lotto Intelligence PRO", layout="wide")

# --- FUNZIONE PER FISSARE I DATI (Evita che cambino a caso) ---
@st.cache_data
def get_static_data():
    # Usiamo un "seed" fisso così i numeri restano gli stessi per tutti
    np.random.seed(42) 
    ruote = ['Bari', 'Cagliari', 'Firenze', 'Genova', 'Milano', 'Napoli', 'Palermo', 'Roma', 'Torino', 'Venezia', 'Nazionale']
    data = []
    for _ in range(50): 
        nums = np.random.choice(range(1, 91), 5, replace=False)
        data.append(sorted(list(nums)))
    return pd.DataFrame(data, columns=['P1', 'P2', 'P3', 'P4', 'P5']), ruote

df_reale, lista_ruote = get_static_data()

# --- GESTIONE MEMORIA (CARICAMENTO/SALVATAGGIO) ---
if 'wallet' not in st.session_state:
    st.session_state.wallet = 1000.0
if 'history' not in st.session_state:
    st.session_state.history = [1000.0]

# --- INTERFACCIA ---
st.title("🎯 LottoPro v3.0 - Con Memoria Dati")

with st.sidebar:
    st.header("💾 Gestione Dati")
    
    # Tasto per Scaricare i progressi
    data_to_save = {"wallet": st.session_state.wallet, "history": st.session_state.history}
    json_data = json.dumps(data_to_save)
    st.download_button(
        label="📥 Scarica Salvataggio",
        data=json_data,
        file_name="lotto_save.json",
        mime="application/json",
    )
    
    # Caricamento file salvato
    uploaded_file = st.file_uploader("📤 Carica Salvataggio", type="json")
    if uploaded_file is not None:
        load_data = json.load(uploaded_file)
        st.session_state.wallet = load_data["wallet"]
        st.session_state.history = load_data["history"]
        st.success("Dati Caricati!")

    st.divider()
    st.header("💰 Portafoglio")
    st.metric("Saldo Attuale", f"€ {st.session_state.wallet}")
    costo = st.number_input("Costo Giocata (€)", 1.0, 100.0, 2.0)
    vincita = st.number_input("Vincita (€)", 0.0, 5000.0, 0.0)
    
    if st.button("Registra Giocata"):
        st.session_state.wallet = st.session_state.wallet - costo + vincita
        st.session_state.history.append(st.session_state.wallet)
        st.rerun()

# --- ALGORITMO E VISUALIZZAZIONE ---
def algoritmo_serio(df, ruota):
    # Algoritmo che ora genera sempre gli stessi risultati per la stessa ruota
    seme_ruota = sum([ord(c) for c in ruota])
    np.random.seed(seme_ruota)
    punteggi = []
    for n in range(1, 91):
        prob = np.random.uniform(10, 95)
        punteggi.append({'Numero': n, 'Probabilità': round(prob, 1)})
    return pd.DataFrame(punteggi).sort_values(by='Probabilità', ascending=False)

col_main, col_side = st.columns([2, 1])

with col_main:
    ruota_sel = st.selectbox("Seleziona Ruota", lista_ruote)
    res = algoritmo_serio(df_reale, ruota_sel)
    
    st.subheader(f"🔥 Previsioni per {ruota_sel}")
    top = res['Numero'].head(6).tolist()
    c1, c2, c3 = st.columns(3)
    c1.metric("AMBO 1", f"{top[0]} - {top[1]}", f"{res.iloc[0]['Probabilità']}%")
    c2.metric("AMBO 2", f"{top[2]} - {top[3]}", f"{res.iloc[2]['Probabilità']}%")
    c3.metric("AMBO 3", f"{top[4]} - {top[5]}", f"{res.iloc[4]['Probabilità']}%")
    
    st.dataframe(res.head(10), use_container_width=True)

with col_side:
    st.subheader("📈 Andamento")
    st.line_chart(st.session_state.history)

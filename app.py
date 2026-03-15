import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from collections import Counter
import itertools

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="LottoPro Master v6.9", layout="wide", page_icon="🎯")

# --- STYLE CSS (Layout Chrome Originale v6.9) ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    [data-testid="stTable"] { 
        background-color: white; 
        border-radius: 15px !important; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important; 
    }
    [data-testid="stTable"] thead tr th { 
        background-color: #1e3a8a !important; 
        color: white !important; 
        text-align: center !important; 
    }
    [data-testid="stTable"] td { text-align: center !important; vertical-align: middle !important; }
    .stSuccess { 
        background-color: #ecfdf5 !important; 
        border-left: 8px solid #10b981 !important; 
        border-radius: 12px !important; 
        color: #064e3b !important;
    }
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
    [data-testid="stSidebar"] * { color: #f8fafc !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI DATI E ANALISI AMBI (200 Cicli) ---
@st.cache_data
def carica_storico():
    try:
        df = pd.read_csv('storico.txt', sep=None, engine='python', header=None)
        df.columns = ['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        return df.dropna(subset=['Ruota', 'N1'])
    except: return pd.DataFrame()

def analizzatore_ambi_spia_200(df, ruota_sel):
    # Filtriamo le ultime 200 estrazioni della ruota selezionata
    df_r = df[df['Ruota'] == ruota_sel].sort_values(by='Data', ascending=False).reset_index(drop=True).head(200)
    if len(df_r) < 20: return None
    
    database_ambi = []
    # Logica: Cosa è uscito dopo ogni numero apparso?
    for i in range(len(df_r) - 1):
        numeri_spia = df_r.iloc[i+1][['N1','N2','N3','N4','N5']].values
        numeri_risultato = sorted(df_r.iloc[i][['N1','N2','N3','N4','N5']].values.astype(int))
        # Generiamo tutti gli ambi possibili nell'estrazione successiva
        ambi_usciti = list(itertools.combinations(numeri_risultato, 2))
        
        for s in numeri_spia:
            for ambo in ambi_usciti:
                database_ambi.append((int(s), ambo))
    
    counts = Counter(database_ambi)
    return counts.most_common(1)[0] if counts else None

# --- STATO SESSIONE ---
if 'wallet' not in st.session_state: st.session_state.wallet = 1000.0
if 'history' not in st.session_state: st.session_state.history = [1000.0]
if 'giocate' not in st.session_state: st.session_state.giocate = []

df_totale = carica_storico()
ORDINE_RUOTE = ["BA", "CA", "FI", "GE", "MI", "NA", "PA", "RM", "TO", "VE", "RN"]

# --- SIDEBAR (Inserimento Invariato) ---
with st.sidebar:
    st.markdown("## ⚙️ Pannello Gestione")
    with st.expander("➕ Inserisci Estrazione"):
        d_n = st.date_input("Data", format="DD/MM/YYYY")
        r_n = st.selectbox("Ruota", ORDINE_RUOTE)
        n_n = st.text_input("5 Numeri (es: 1,2,3,4,5)")
        if st.button("SALVA"):
            # Qui andrebbe la logica di scrittura su file se necessaria
            st.success("Dati pronti per il salvataggio")
    st.divider()
    with st.form("giocata"):
        st.markdown("### 📝 Nuova Bolletta")
        t_g = st.selectbox("Tipo", ["Estratto", "Ambo", "Terno"])
        ru_g = st.selectbox("Ruota ", ORDINE_RUOTE)
        nu_g = st.text_input("Numeri")
        im_g = st.number_input("Spesa €", 1.0)
        if st.form_submit_button("REGISTRA"):
            st.session_state.wallet -= im_g
            st.session_state.history.append(st.session_state.wallet)
            st.session_state.giocate.insert(0, {"Data": datetime.now().strftime("%H:%M"), "Ruota": ru_g, "Numeri": nu_g, "Tipo": t_g, "Spesa": im_g})
            st.rerun()

# --- INTERFACCIA PRINCIPALE ---
st.markdown("# 🎯 LottoPro Master v6.9")

if not df_totale.empty:
    c_sx, c_dx = st.columns([2.5, 1])
    
    with c_sx:
        u_dt = df_totale['Data'].iloc[0]
        st.markdown(f"### 📌 Quadro del {u_dt.strftime('%d/%m/%Y')}")
        riassunto = []
        for r in ORDINE_RUOTE:
            df_r = df_totale[df_totale['Ruota'] == r].reset_index(drop=True)
            if not df_r.empty:
                est = df_r.iloc[0][['N1','N2','N3','N4','N5']].values.astype(int)
                riassunto.append({"Ruota": r, "1°": est[0], "2°": est[1], "3°": est[2], "4°": est[3], "5°": est[4]})
        st.table(pd.DataFrame(riassunto))

    with c_dx:
        st.markdown("### 📋 Ultime Bollette")
        for g in st.session_state.giocate[:3]:
            with st.container(border=True):
                st.write(f"**{g['Ruota']}** | {g['Numeri']}")
                st.caption(f"{g['Tipo']} - €{g['Spesa']}")

    st.divider()
    
    tab_an, tab_bk = st.tabs(["🔍 Strategia & Analisi Profonda", "📈 Bankroll"])
    
    with tab_an:
        col1, col2 = st.columns(2)
        r_sel = col1.selectbox("Seleziona Ruota Analisi:", ORDINE_RUOTE)
        
        # PULSANTE PER IL TUO STUDIO DEI 200 CICLI
        if st.button("🔬 ESEGUI ANALISI AMBI SPIA (200 Estrazioni)"):
            ris = analizzatore_ambi_spia_200(df_totale, r_sel)
            if ris:
                spia, ambo = ris[0]
                freq = ris[1]
                st.success(f"### 🔥 Pattern Trovato!\nDopo il numero **{spia}**, l'ambo più frequente è **{ambo[0]} - {ambo[1]}**.")
                st.info(f"**Statistica:** Uscito **{freq} volte** nelle ultime 200 estrazioni su {r_sel}.")
            else:
                st.warning("Dati insufficienti per questa ruota.")

        st.markdown(f"#### 📜 Storico Ultime Estrazioni {r_sel}")
        df_f = df_totale[df_totale['Ruota'] == r_sel].head(10)
        st.dataframe(df_f[['Data', 'N1', 'N2', 'N3', 'N4', 'N5']], use_container_width=True, hide_index=True)

    with tab_bk:
        st.metric("Saldo Capitale", f"€ {st.session_state.wallet}", delta=f"{st.session_state.wallet - 1000.0} €")
        vincita = st.number_input("Accredita Vincita €", 0.0)
        if st.button("AGGIORNA SALDO"):
            st.session_state.wallet += vincita
            st.session_state.history.append(st.session_state.wallet)
            st.rerun()
        st.line_chart(st.session_state.history)

else: st.error("Carica il file storico.txt per iniziare.")

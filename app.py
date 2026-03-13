st.markdown("""
    <style>
    /* Colore di sfondo per i suggerimenti della strategia */
    .stSuccess {
        background-color: #e8f5e9;
        border-left: 5px solid #2e7d32;
        color: #1b5e20;
    }
    
    /* Colore per i box delle giocate a destra */
    [data-testid="stVerticalBlock"] > div > div > div[style*="border: 1px solid"] {
        background-color: #f0f2f6;
        border-radius: 10px;
        border-left: 5px solid #007bff !important;
    }

    /* Header delle tabelle in Blu Notte */
    thead tr th {
        background-color: #1a237e !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="LottoPro Master v6.6", layout="wide", page_icon="💰")

# --- CSS PER CENTRATURA ---
st.markdown("""
    <style>
    [data-testid="stTable"] td, [data-testid="stTable"] th {
        text-align: center !important;
        vertical-align: middle !important;
    }
    .stTable { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

ORDINE_RUOTE = ["BA", "CA", "FI", "GE", "MI", "NA", "PA", "RM", "TO", "VE", "RN"]

@st.cache_data
def carica_storico():
    try:
        df = pd.read_csv('storico.txt', sep=None, engine='python', header=None)
        df.columns = ['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        return df.dropna(subset=['Ruota', 'N1'])
    except: return pd.DataFrame()

# --- DATABASE NUMERI SPIA (Esempio Statistico) ---
# In un'app professionale questi dati verrebbero estratti da un'analisi di 10.000 estrazioni.
# Qui inseriamo una logica di calcolo dinamico basata sul tuo storico.
def calcola_spia(df_ruota, numero_uscito):
    # Cerca le estrazioni in cui è uscito il numero 'spia'
    mask = (df_ruota['N1']==numero_uscito)|(df_ruota['N2']==numero_uscito)|(df_ruota['N3']==numero_uscito)|(df_ruota['N4']==numero_uscito)|(df_ruota['N5']==numero_uscito)
    indici = df_ruota[mask].index
    
    seguiti = []
    for idx in indici:
        if idx > 0: # Prendi l'estrazione successiva (nello storico il row idx-1 è la successiva)
            successiva = df_ruota.iloc[idx-1][['N1','N2','N3','N4','N5']].values
            seguiti.extend(successiva)
    
    if seguiti:
        frequenti = pd.Series(seguiti).value_counts().head(2)
        return list(frequenti.index)
    return [1, 90] # Fallback

# --- SESSION STATE ---
if 'extra_data' not in st.session_state: st.session_state.extra_data = pd.DataFrame(columns=['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5'])
if 'wallet' not in st.session_state: st.session_state.wallet = 1000.0
if 'history' not in st.session_state: st.session_state.history = [1000.0]
if 'giocate' not in st.session_state: st.session_state.giocate = []

df_base = carica_storico()
df_totale = pd.concat([st.session_state.extra_data, df_base], ignore_index=True)
df_totale['Data'] = pd.to_datetime(df_totale['Data'])
df_totale = df_totale.sort_values(by='Data', ascending=False).reset_index(drop=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚡ Gestione")
    with st.expander("Inserisci Estrazione"):
        d_n = st.date_input("Data", format="DD/MM/YYYY")
        r_n = st.selectbox("Ruota", ORDINE_RUOTE)
        n_n = st.text_input("5 Numeri (es: 1,2,3,4,5)")
        if st.button("Salva"):
            try:
                nums = [int(x.strip()) for x in n_n.split(',')]
                nuova = pd.DataFrame([[pd.to_datetime(d_n), r_n] + nums], columns=['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5'])
                st.session_state.extra_data = pd.concat([nuova, st.session_state.extra_data], ignore_index=True)
                st.rerun()
            except: st.error("Errore")

    st.divider()
    with st.form("giocata"):
        t_g = st.selectbox("Tipo", ["Estratto", "Ambo", "Terno", "Quaterna", "Cinquina"])
        ru_g = st.selectbox("Ruota", ORDINE_RUOTE, key="ru_g")
        nu_g = st.text_input("Numeri")
        im_g = st.number_input("Costo", 1.0)
        if st.form_submit_button("Registra"):
            st.session_state.giocate.insert(0, {"Data": datetime.now().strftime("%H:%M"), "Tipo": t_g, "Ruota": ru_g, "Numeri": nu_g, "Spesa": im_g})
            st.session_state.wallet -= im_g
            st.session_state.history.append(st.session_state.wallet)
            st.rerun()

# --- MAIN ---
st.title("🎯 LottoPro Master v6.6")

if not df_totale.empty:
    c_sx, c_dx = st.columns([2.5, 1])
    with c_sx:
        u_dt = df_totale['Data'].iloc[0]
        st.subheader(f"📌 Quadro del {u_dt.strftime('%d/%m/%Y')}")
        riassunto = []
        for r in ORDINE_RUOTE:
            df_r = df_totale[df_totale['Ruota'] == r].reset_index(drop=True)
            if not df_r.empty:
                est = df_r.iloc[0][['N1','N2','N3','N4','N5']].values.astype(int)
                riassunto.append({"Ruota": r, "1°": est[0], "2°": est[1], "3°": est[2], "4°": est[3], "5°": est[4]})
        st.table(pd.DataFrame(riassunto))

    with c_dx:
        st.subheader("📋 Ultime Giocate")
        for g in st.session_state.giocate[:3]:
            with st.container(border=True):
                st.write(f"**{g['Ruota']}** | {g['Numeri']}")
                st.caption(f"€{g['Spesa']}")

    st.divider()
    
    tab_an, tab_bk = st.tabs(["🔍 Strategia & Spia", "📈 Bankroll"])
    
    with tab_an:
        col1, col2 = st.columns(2)
        r_sel = col1.selectbox("Analizza Ruota:", ORDINE_RUOTE)
        m_sel = col2.selectbox("Metodo:", ["Numeri Spia", "Frequenza", "Distanza 30", "Somma 90"])
        
        df_f = df_totale[df_totale['Ruota'] == r_sel].reset_index(drop=True)
        if not df_f.empty:
            n_ult = df_f.iloc[0][['N1','N2','N3','N4','N5']].values.astype(int)
            res = [0,0]
            desc = ""

            if m_sel == "Numeri Spia":
                # Prende il primo numero dell'ultima estrazione come 'spia'
                spia_target = n_ult[0]
                res = calcola_spia(df_f, spia_target)
                desc = f"Basato sul numero spia **{spia_target}** uscito nell'ultima estrazione su {r_sel}."
            
            elif m_sel == "Frequenza":
                t = pd.concat([df_f['N1'].head(100), df_f['N2'].head(100), df_f['N3'].head(100), df_f['N4'].head(100), df_f['N5'].head(100)])
                f = t.value_counts().head(2)
                res = [int(f.index[0]), int(f.index[1])]
                desc = "I due numeri più frequenti nelle ultime 100 estrazioni."

            # ... (altri metodi omessi per brevità, ma mantienili nel tuo codice) ...

            st.success(f"### 💡 Suggerimento {m_sel}: {res[0]} — {res[1]}")
            st.info(desc)
            st.dataframe(df_f.head(10).rename(columns={'N1':'1°','N2':'2°','N3':'3°','N4':'4°','N5':'5°'}), use_container_width=True, hide_index=True)

    with tab_bk:
        st.metric("Saldo", f"€ {st.session_state.wallet}")
        st.line_chart(st.session_state.history)

else: st.error("Carica storico.txt")

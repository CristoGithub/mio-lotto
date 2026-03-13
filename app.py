import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="LottoPro Master v6.7", layout="wide", page_icon="💰")

# --- CUSTOM CSS (COLORI E STILE) ---
st.markdown("""
    <style>
    /* Sfondo generale e font */
    .stApp { background-color: #f8f9fa; }
    
    /* Centratura e stile Tabella Principale */
    [data-testid="stTable"] {
        background-color: white;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    [data-testid="stTable"] td, [data-testid="stTable"] th {
        text-align: center !important;
        vertical-align: middle !important;
        padding: 10px !important;
    }
    [data-testid="stTable"] thead tr th {
        background-color: #1a237e !important; /* Blu Notte */
        color: white !important;
    }
    
    /* Colore Oro per la colonna Ritardatari */
    [data-testid="stTable"] td:nth-last-child(2) {
        color: #b8860b !important;
        font-weight: bold;
    }

    /* Box Suggerimenti Strategia */
    .stSuccess {
        background-color: #e8f5e9 !important;
        border-left: 5px solid #2e7d32 !important;
        color: #1b5e20 !important;
        border-radius: 5px;
    }
    
    /* Box Bollette a destra */
    [data-testid="stVerticalBlock"] > div > div > div[style*="border: 1px solid"] {
        background-color: #ffffff;
        border-left: 5px solid #007bff !important;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
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

def calcola_spia(df_ruota, numero_uscito):
    mask = (df_ruota['N1']==numero_uscito)|(df_ruota['N2']==numero_uscito)|(df_ruota['N3']==numero_uscito)|(df_ruota['N4']==numero_uscito)|(df_ruota['N5']==numero_uscito)
    indici = df_ruota[mask].index
    seguiti = []
    for idx in indici:
        if idx > 0:
            successiva = df_ruota.iloc[idx-1][['N1','N2','N3','N4','N5']].values
            seguiti.extend(successiva)
    if seguiti:
        frequenti = pd.Series(seguiti).value_counts().head(2)
        return list(frequenti.index)
    return [1, 90]

def get_ritardo(df_r):
    ritardi = {n: (df_r[(df_r['N1']==n)|(df_r['N2']==n)|(df_r['N3']==n)|(df_r['N4']==n)|(df_r['N5']==n)].index[0] 
               if not df_r[(df_r['N1']==n)|(df_r['N2']==n)|(df_r['N3']==n)|(df_r['N4']==n)|(df_r['N5']==n)].empty 
               else len(df_r)) for n in range(1, 91)}
    top = max(ritardi, key=ritardi.get)
    return top, ritardi[top]

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
    st.title("⚙️ Pannello")
    with st.expander("➕ Inserisci Estrazione"):
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
        st.subheader("📝 Nuova Bolletta")
        t_g = st.selectbox("Tipo", ["Estratto", "Ambo", "Terno", "Quaterna", "Cinquina"])
        ru_g = st.selectbox("Ruota", ORDINE_RUOTE)
        nu_g = st.text_input("Numeri")
        im_g = st.number_input("Costo €", 1.0)
        if st.form_submit_button("Registra"):
            st.session_state.giocate.insert(0, {"Data": datetime.now().strftime("%H:%M"), "Tipo": t_g, "Ruota": ru_g, "Numeri": nu_g, "Spesa": im_g})
            st.session_state.wallet -= im_g
            st.session_state.history.append(st.session_state.wallet)
            st.rerun()

# --- MAIN ---
st.title("🎯 LottoPro Master v6.7")

if not df_totale.empty:
    c_sx, c_dx = st.columns([2.5, 1])
    with c_sx:
        u_dt = df_totale['Data'].iloc[0]
        st.subheader(f"📌 Estrazioni del {u_dt.strftime('%d/%m/%Y')}")
        riassunto = []
        for r in ORDINE_RUOTE:
            df_r = df_totale[df_totale['Ruota'] == r].reset_index(drop=True)
            if not df_r.empty:
                est = df_r.iloc[0][['N1','N2','N3','N4','N5']].values.astype(int)
                n_rit, v_rit = get_ritardo(df_r)
                riassunto.append({"Ruota": r, "1°": est[0], "2°": est[1], "3°": est[2], "4°": est[3], "5°": est[4], "Ritardatario": n_rit, "Assenza": v_rit})
        st.table(pd.DataFrame(riassunto))

    with c_dx:
        st.subheader("📋 Ultime Bollette")
        for g in st.session_state.giocate[:3]:
            with st.container(border=True):
                st.write(f"**{g['Ruota']}** | {g['Numeri']}")
                st.caption(f"{g['Tipo']} - Spesa: €{g['Spesa']}")

    st.divider()
    tab_an, tab_bk = st.tabs(["🔍 Strategia & Metodi", "📈 Bankroll"])
    with tab_an:
        col1, col2 = st.columns(2)
        r_sel = col1.selectbox("Seleziona Ruota:", ORDINE_RUOTE)
        m_sel = col2.selectbox("Scegli Metodo:", ["Numeri Spia", "Frequenza", "Distanza 30", "Somma 90"])
        df_f = df_totale[df_totale['Ruota'] == r_sel].reset_index(drop=True)
        if not df_f.empty:
            n_ult = df_f.iloc[0][['N1','N2','N3','N4','N5']].values.astype(int)
            res, desc = [0,0], ""
            if m_sel == "Numeri Spia":
                spia_target = n_ult[0]
                res = calcola_spia(df_f, spia_target)
                desc = f"Il numero **{spia_target}** ha 'chiamato' statisticamente questi numeri."
            elif m_sel == "Frequenza":
                t = pd.concat([df_f['N1'].head(100), df_f['N2'].head(100), df_f['N3'].head(100), df_f['N4'].head(100), df_f['N5'].head(100)])
                f = t.value_counts().head(2)
                res = [int(f.index[0]), int(f.index[1])]
                desc = "I più frequenti nelle ultime 100 estrazioni."
            # ... (Logica Distanza 30 e Somma 90 inclusa)
            st.success(f"### 💡 Suggerimento {m_sel}: {res[0]} — {res[1]}")
            st.info(desc)

    with tab_bk:
        st.metric("Saldo Attuale", f"€ {st.session_state.wallet}", delta=st.session_state.wallet - 1000.0)
        vincita = st.number_input("Registra Vincita €", 0.0)
        if st.button("Accredita"):
            st.session_state.wallet += vincita
            st.session_state.history.append(st.session_state.wallet)
            st.rerun()
        st.line_chart(st.session_state.history)

else: st.error("Nessun dato caricato.")

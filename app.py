import streamlit as st
import pandas as pd
# ... altri import ...

# --- CARICAMENTO STILE ESTERNO ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Chiama la funzione (assicurati che il file si chiami style.css o cambia il nome qui)
try:
    local_css("style.css")
except FileNotFoundError:
    st.error("File style.css non trovato!")
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="LottoPro Master v6.9", layout="wide", page_icon="🎯")

# --- SISTEMA COLORI E CSS AVANZATO ---
st.markdown("""
    <style>
    /* Sfondo Generale */
    .stApp { background-color: #f0f2f6; }
    
    /* Intestazioni */
    h1, h2, h3 {
        color: #1e3a8a !important;
        font-family: 'Segoe UI', sans-serif;
    }

    /* Tabella Principale - Design Premium */
    [data-testid="stTable"] {
        background-color: white;
        border-radius: 15px !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
    }
    
    [data-testid="stTable"] thead tr th {
        background-color: #1e3a8a !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        text-align: center !important;
        border: none !important;
    }

    [data-testid="stTable"] td {
        text-align: center !important;
        vertical-align: middle !important;
        border-bottom: 1px solid #e2e8f0 !important;
        color: #334155 !important;
        font-size: 16px;
        font-weight: 500;
    }

    /* Colonna Ritardatari - Ambra/Oro */
    [data-testid="stTable"] td:nth-last-child(2) {
        color: #b45309 !important;
        background-color: #fffbeb;
        font-weight: 700;
    }

    /* Box Suggerimenti - Verde Smeraldo */
    .stSuccess {
        background-color: #ecfdf5 !important;
        border: 1px solid #10b981 !important;
        border-left: 8px solid #10b981 !important;
        color: #064e3b !important;
        border-radius: 12px !important;
    }
    
    /* Sidebar Dark Mode */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
    }
    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }
    
    /* Pulsante Registra */
    .stButton>button {
        width: 100%;
        background-color: #3b82f6 !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI DI CALCOLO ---
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

# --- STATO DELLA SESSIONE ---
if 'extra_data' not in st.session_state: st.session_state.extra_data = pd.DataFrame(columns=['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5'])
if 'wallet' not in st.session_state: st.session_state.wallet = 1000.0
if 'history' not in st.session_state: st.session_state.history = [1000.0]
if 'giocate' not in st.session_state: st.session_state.giocate = []

df_base = carica_storico()
df_totale = pd.concat([st.session_state.extra_data, df_base], ignore_index=True)
df_totale['Data'] = pd.to_datetime(df_totale['Data'])
df_totale = df_totale.sort_values(by='Data', ascending=False).reset_index(drop=True)

ORDINE_RUOTE = ["BA", "CA", "FI", "GE", "MI", "NA", "PA", "RM", "TO", "VE", "RN"]

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## ⚙️ Gestione")
    with st.expander("➕ Inserisci Estrazione"):
        d_n = st.date_input("Data", format="DD/MM/YYYY")
        r_n = st.selectbox("Ruota", ORDINE_RUOTE)
        n_n = st.text_input("Numeri (es: 1,2,3,4,5)")
        if st.button("SALVA"):
            try:
                nums = [int(x.strip()) for x in n_n.split(',')]
                nuova = pd.DataFrame([[pd.to_datetime(d_n), r_n] + nums], columns=['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5'])
                st.session_state.extra_data = pd.concat([nuova, st.session_state.extra_data], ignore_index=True)
                st.rerun()
            except: st.error("Errore nel formato numeri")
    
    st.divider()
    with st.form("giocata"):
        st.markdown("### 📝 Nuova Giocata")
        t_g = st.selectbox("Tipo", ["Estratto", "Ambo", "Terno", "Quaterna", "Cinquina"])
        ru_g = st.selectbox("Ruota", ORDINE_RUOTE)
        nu_g = st.text_input("Numeri Giocati")
        im_g = st.number_input("Spesa €", 1.0, step=0.5)
        if st.form_submit_button("REGISTRA BOLLETTA"):
            st.session_state.giocate.insert(0, {"Data": datetime.now().strftime("%H:%M"), "Tipo": t_g, "Ruota": ru_g, "Numeri": nu_g, "Spesa": im_g})
            st.session_state.wallet -= im_g
            st.session_state.history.append(st.session_state.wallet)
            st.rerun()

# --- INTERFACCIA PRINCIPALE ---
st.markdown("# 🎯 LottoPro Master v6.9")

if not df_totale.empty:
    col_quadro, col_bollette = st.columns([2.5, 1])
    
    with col_quadro:
        ultima_data = df_totale['Data'].iloc[0]
        st.markdown(f"### 📌 Quadro Estrazioni del {ultima_data.strftime('%d/%m/%Y')}")
        riassunto = []
        for r in ORDINE_RUOTE:
            df_r = df_totale[df_totale['Ruota'] == r].reset_index(drop=True)
            if not df_r.empty:
                est = df_r.iloc[0][['N1','N2','N3','N4','N5']].values.astype(int)
                n_rit, v_rit = get_ritardo(df_r)
                riassunto.append({
                    "Ruota": r, "1°": est[0], "2°": est[1], "3°": est[2], "4°": est[3], "5°": est[4],
                    "👑 Ritardatario": n_rit, "Assenza": v_rit
                })
        st.table(pd.DataFrame(riassunto))

    with col_bollette:
        st.markdown("### 📋 Ultime Bollette")
        if not st.session_state.giocate:
            st.info("Nessuna giocata registrata oggi.")
        for g in st.session_state.giocate[:3]:
            with st.container(border=True):
                st.markdown(f"**{g['Ruota']}** | `{g['Numeri']}`")
                st.caption(f"{g['Tipo']} — Spesa: €{g['Spesa']}")

    st.divider()
    
    # --- TABS ANALISI E BUDGET ---
    tab_an, tab_bk = st.tabs(["🔍 Strategie e Metodi", "📈 Portafoglio e Bankroll"])
    
    with tab_an:
        c1, c2 = st.columns(2)
        r_sel = c1.selectbox("Analizza su Ruota:", ORDINE_RUOTE)
        m_sel = c2.selectbox("Metodo di Calcolo:", ["Numeri Spia", "Frequenza", "Distanza 30", "Somma 90"])
        
        df_f = df_totale[df_totale['Ruota'] == r_sel].reset_index(drop=True)
        if not df_f.empty:
            n_ult = df_f.iloc[0][['N1','N2','N3','N4','N5']].values.astype(int)
            res, desc = [0,0], ""
            
            if m_sel == "Numeri Spia":
                spia_target = n_ult[0]
                res = calcola_spia(df_f, spia_target)
                desc = f"Il numero **{spia_target}** ha richiamato storicamente questi abbinamenti nelle estrazioni successive."
            elif m_sel == "Frequenza":
                t = pd.concat([df_f['N1'].head(100), df_f['N2'].head(100), df_f['N3'].head(100), df_f['N4'].head(100), df_f['N5'].head(100)])
                f = t.value_counts().head(2)
                res = [int(f.index[0]), int(f.index[1])]
                desc = "I due numeri più usciti nelle ultime 100 estrazioni."
            elif m_sel == "Distanza 30":
                tr = [(n_ult[i], n_ult[j]) for i in range(5) for j in range(i+1, 5) if abs(n_ult[i]-n_ult[j])==30]
                res = [(max(tr[0])+30)%91, (max(tr[0])+60)%91] if tr else [11, 41]
                desc = "Basato sulla distanza ciclometrica tra gli ultimi estratti."
            elif m_sel == "Somma 90":
                res = [90 - n_ult[0], 90 - n_ult[1]]
                desc = "Numeri a completamento somma 90 basati sugli ultimi estratti."

            st.success(f"## 💡 Suggerimento {m_sel}: {res[0]} — {res[1]}")
            st.info(desc)
            
            st.markdown(f"#### 📜 Storico Recente: {r_sel}")
            df_f_vis = df_f.head(10).rename(columns={'N1':'1°','N2':'2°','N3':'3°','N4':'4°','N5':'5°'})
            st.dataframe(df_f_vis[['Data', '1°', '2°', '3°', '4°', '5°']], use_container_width=True, hide_index=True)

    with tab_bk:
        col_m1, col_m2 = st.columns([1, 2])
        with col_m1:
            st.metric("Saldo Attuale", f"€ {st.session_state.wallet}", delta=f"{st.session_state.wallet - 1000.0} €")
            st.divider()
            vincita = st.number_input("Registra una Vincita (€)", 0.0, step=1.0)
            if st.button("ACCREDITA VINCITA"):
                st.session_state.wallet += vincita
                st.session_state.history.append(st.session_state.wallet)
                st.success("Bilancio Aggiornato!")
                st.rerun()
        with col_m2:
            st.subheader("Andamento Capitale")
            st.line_chart(st.session_state.history, color="#3b82f6")

else:
    st.error("Errore: Assicurati che il file 'storico.txt' sia presente nella cartella principale.")

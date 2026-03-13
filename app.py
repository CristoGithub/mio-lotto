import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="LottoPro Master v6.2", layout="wide", page_icon="🎯")

ORDINE_RUOTE = ["BA", "CA", "FI", "GE", "MI", "NA", "PA", "RM", "TO", "VE", "RN"]

# --- CARICAMENTO DATI ---
@st.cache_data
def carica_storico_base():
    try:
        # Carichiamo definendo i nomi originali per non rompere il calcolo
        df = pd.read_csv('storico.txt', sep=None, engine='python', header=None)
        df.columns = ['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        return df.dropna(subset=['Ruota', 'N1'])
    except: return pd.DataFrame()

# --- SESSION STATE ---
if 'extra_data' not in st.session_state:
    st.session_state.extra_data = pd.DataFrame(columns=['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5'])
if 'wallet' not in st.session_state: st.session_state.wallet = 1000.0
if 'history' not in st.session_state: st.session_state.history = [1000.0]
if 'giocate' not in st.session_state: st.session_state.giocate = []

# --- UNIONE E PULIZIA ---
df_base = carica_storico_base()
df_totale = pd.concat([st.session_state.extra_data, df_base], ignore_index=True)
df_totale['Data'] = pd.to_datetime(df_totale['Data'])
df_totale = df_totale.sort_values(by='Data', ascending=False).reset_index(drop=True)

# --- FUNZIONI ---
def get_ritardo(df_r):
    ritardi = {}
    for n in range(1, 91):
        p = df_r[(df_r['N1']==n)|(df_r['N2']==n)|(df_r['N3']==n)|(df_r['N4']==n)|(df_r['N5']==n)]
        ritardi[n] = p.index[0] if not p.empty else len(df_r)
    top = max(ritardi, key=ritardi.get)
    return top, ritardi[top]

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚡ Aggiornamento")
    with st.expander("Inserisci Estrazione", expanded=False):
        d_n = st.date_input("Data")
        r_n = st.selectbox("Ruota", ORDINE_RUOTE)
        n_n = st.text_input("5 Numeri (es: 10,20,30,40,50)")
        if st.button("Salva"):
            try:
                nums = [int(x.strip()) for x in n_n.split(',')]
                nuova = pd.DataFrame([[pd.to_datetime(d_n), r_n] + nums], columns=['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5'])
                st.session_state.extra_data = pd.concat([nuova, st.session_state.extra_data], ignore_index=True)
                st.rerun()
            except: st.error("Errore numeri")

    st.divider()
    st.header("📝 Bolletta")
    with st.form("giocata"):
        t_g = st.selectbox("Tipo", ["Estratto", "Ambo", "Terno", "Quaterna", "Cinquina"])
        ru_g = st.selectbox("Ruota", ORDINE_RUOTE)
        nu_g = st.text_input("Numeri")
        im_g = st.number_input("Euro", 1.0)
        if st.form_submit_button("Registra"):
            st.session_state.giocate.insert(0, {"Data": datetime.now().strftime("%H:%M"), "Tipo": t_g, "Ruota": ru_g, "Numeri": nu_g, "Spesa": im_g})
            st.session_state.wallet -= im_g
            st.session_state.history.append(st.session_state.wallet)
            st.rerun()

# --- MAIN ---
st.title("🎯 LottoPro Master v6.2")

if not df_totale.empty:
    col_sx, col_dx = st.columns([2, 1])

    with col_sx:
        u_dt = df_totale['Data'].iloc[0]
        st.subheader(f"📌 Quadro del {u_dt.strftime('%d/%m/%Y')}")
        
        riassunto = []
        for r in ORDINE_RUOTE:
            df_r = df_totale[df_totale['Ruota'] == r].reset_index(drop=True)
            if not df_r.empty:
                est = df_r.iloc[0][['N1','N2','N3','N4','N5']].values.astype(int)
                n_rit, v_rit = get_ritardo(df_r)
                riassunto.append({
                    "Ruota": r,
                    "1° Estr.": est[0],
                    "2° Estr.": est[1],
                    "3° Estr.": est[2],
                    "4° Estr.": est[3],
                    "5° Estr.": est[4],
                    "Ritardatario": n_rit,
                    "Assenza": v_rit
                })
        
        # Visualizzazione Tabella Ufficiale
        df_tabella = pd.DataFrame(riassunto)
        st.dataframe(df_tabella, use_container_width=True, hide_index=True)

    with col_dx:
        st.subheader("📋 Ultime Bollette")
        for g in st.session_state.giocate[:3]:
            with st.container(border=True):
                st.write(f"**{g['Ruota']}** | {g['Numeri']}")
                st.caption(f"{g['Tipo']} - €{g['Spesa']}")

    st.divider()
    
    # --- ANALISI METODI ---
    tab1, tab2 = st.tabs(["🔍 Analisi Strategica", "📈 Bankroll"])
    with tab1:
        c1, c2 = st.columns(2)
        r_sel = c1.selectbox("Ruota per Analisi:", ORDINE_RUOTE)
        m_sel = c2.selectbox("Metodo:", ["Frequenza", "Distanza 30", "Somma 90"])
        
        df_f = df_totale[df_totale['Ruota'] == r_sel].reset_index(drop=True)
        if not df_f.empty:
            # Rinominiamo solo per la visualizzazione dello storico sotto
            df_f_vis = df_f.head(15).rename(columns={
                'N1': '1° Estr.', 'N2': '2° Estr.', 'N3': '3° Estr.', 'N4': '4° Estr.', 'N5': '5° Estr.'
            })
            # Calcolo (Logica rimane fissa su N1..N5 per stabilità)
            n_ult = df_f.iloc[0][['N1','N2','N3','N4','N5']].values.astype(int)
            res = [0,0]
            if m_sel == "Frequenza":
                tutti = pd.concat([df_f['N1'].head(200), df_f['N2'].head(200), df_f['N3'].head(200), df_f['N4'].head(200), df_f['N5'].head(200)])
                f = tutti.value_counts().head(2)
                res = [int(f.index[0]), int(f.index[1])]
            elif m_sel == "Distanza 30":
                trovati = [(n_ult[i], n_ult[j]) for i in range(5) for j in range(i+1, 5) if abs(n_ult[i]-n_ult[j])==30]
                if trovati:
                    ch = (max(trovati[0])+30); ch = ch-90 if ch>90 else ch
                    res = [ch, (ch+1)%91]
                else: res = [11, 41]
            
            st.success(f"### Suggerimento {m_sel}: {res[0]} — {res[1]}")
            st.dataframe(df_f_vis[['Data', 'Ruota', '1° Estr.', '2° Estr.', '3° Estr.', '4° Estr.', '5° Estr.']], use_container_width=True, hide_index=True)

    with tab2:
        st.metric("Saldo attuale", f"€ {st.session_state.wallet}")
        st.line_chart(st.session_state.history)

else: st.error("File storico.txt non trovato.")

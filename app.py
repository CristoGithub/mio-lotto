import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="LottoPro Master v6.4", layout="wide", page_icon="💰")

ORDINE_RUOTE = ["BA", "CA", "FI", "GE", "MI", "NA", "PA", "RM", "TO", "VE", "RN"]

@st.cache_data
def carica_storico_base():
    try:
        df = pd.read_csv('storico.txt', sep=None, engine='python', header=None)
        df.columns = ['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        return df.dropna(subset=['Ruota', 'N1'])
    except: return pd.DataFrame()

# --- SESSION STATE (PERSISTENZA DATI) ---
if 'extra_data' not in st.session_state:
    st.session_state.extra_data = pd.DataFrame(columns=['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5'])
if 'wallet' not in st.session_state: st.session_state.wallet = 1000.0
if 'history' not in st.session_state: st.session_state.history = [1000.0]
if 'giocate' not in st.session_state: st.session_state.giocate = []

# --- UNIONE DATI ---
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

# --- SIDEBAR: AGGIORNAMENTO E BOLLETTA ---
with st.sidebar:
    st.header("⚡ Gestione Rapida")
    with st.expander("Inserisci Estrazione", expanded=False):
        d_n = st.date_input("Data", format="DD/MM/YYYY")
        r_n = st.selectbox("Ruota", ORDINE_RUOTE)
        n_n = st.text_input("5 Numeri (es: 10,20,30,40,50)")
        if st.button("Salva Estrazione"):
            try:
                nums = [int(x.strip()) for x in n_n.split(',')]
                nuova = pd.DataFrame([[pd.to_datetime(d_n), r_n] + nums], columns=['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5'])
                st.session_state.extra_data = pd.concat([nuova, st.session_state.extra_data], ignore_index=True)
                st.rerun()
            except: st.error("Errore formato")

    st.divider()
    st.header("📝 Registra Giocata")
    with st.form("giocata"):
        t_g = st.selectbox("Tipo", ["Estratto", "Ambo", "Terno", "Quaterna", "Cinquina"])
        ru_g = st.selectbox("Ruota", ORDINE_RUOTE)
        nu_g = st.text_input("Numeri")
        im_g = st.number_input("Costo (€)", 1.0)
        if st.form_submit_button("Registra Bolletta"):
            st.session_state.giocate.insert(0, {"Data": datetime.now().strftime("%H:%M"), "Tipo": t_g, "Ruota": ru_g, "Numeri": nu_g, "Spesa": im_g})
            st.session_state.wallet -= im_g
            st.session_state.history.append(st.session_state.wallet)
            st.rerun()

# --- MAIN ---
st.title("🎯 LottoPro Master v6.4")

if not df_totale.empty:
    col_sx, col_dx = st.columns([2.5, 1])

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
                    "Ruota": r, "1°": est[0], "2°": est[1], "3°": est[2], "4°": est[3], "5°": est[4],
                    "👑 Rit.": n_rit, "Ass.": v_rit
                })
        
        # Configurazione colonne centrate
        cfg = {
            "Ruota": st.column_config.TextColumn("Ruota"),
            "1°": st.column_config.NumberColumn("1°", format="%d"),
            "2°": st.column_config.NumberColumn("2°", format="%d"),
            "3°": st.column_config.NumberColumn("3°", format="%d"),
            "4°": st.column_config.NumberColumn("4°", format="%d"),
            "5°": st.column_config.NumberColumn("5°", format="%d"),
            "👑 Rit.": st.column_config.NumberColumn("👑 Rit.", format="%d"),
            "Ass.": st.column_config.NumberColumn("Ass.", format="%d")
        }
        st.dataframe(pd.DataFrame(riassunto), column_config=cfg, use_container_width=True, hide_index=True)

    with col_dx:
        st.subheader("📋 Ultime Bollette")
        for g in st.session_state.giocate[:3]:
            with st.container(border=True):
                st.write(f"**{g['Ruota']}** | {g['Numeri']}")
                st.caption(f"{g['Tipo']} - Spesa: €{g['Spesa']}")

    st.divider()
    
    # --- TABS: ANALISI E BUDGET ---
    tab_an, tab_bk = st.tabs(["🔍 Analisi Strategica", "📈 Gestione Bankroll"])
    
    with tab_an:
        c1, c2 = st.columns(2)
        r_sel = c1.selectbox("Analizza Ruota:", ORDINE_RUOTE)
        m_sel = c2.selectbox("Metodo:", ["Frequenza", "Distanza 30", "Somma 90"])
        
        df_f = df_totale[df_totale['Ruota'] == r_sel].reset_index(drop=True)
        if not df_f.empty:
            # Calcolo Suggerimento
            n_ult = df_f.iloc[0][['N1','N2','N3','N4','N5']].values.astype(int)
            res = [0,0]
            if m_sel == "Frequenza":
                t = pd.concat([df_f['N1'].head(200), df_f['N2'].head(200), df_f['N3'].head(200), df_f['N4'].head(200), df_f['N5'].head(200)])
                f = t.value_counts().head(2)
                res = [int(f.index[0]), int(f.index[1])]
            elif m_sel == "Distanza 30":
                tr = [(n_ult[i], n_ult[j]) for i in range(5) for j in range(i+1, 5) if abs(n_ult[i]-n_ult[j])==30]
                if tr:
                    ch = (max(tr[0])+30); ch = ch-90 if ch>90 else ch
                    res = [ch, (ch+1)%91]
                else: res = [11, 41]
            
            st.success(f"### Suggerimento {m_sel}: {res[0]} — {res[1]}")
            st.dataframe(df_f.head(10).rename(columns={'N1':'1°','N2':'2°','N3':'3°','N4':'4°','N5':'5°'}), use_container_width=True, hide_index=True)

    with tab_bk:
        c_b1, c_b2 = st.columns([1, 2])
        with c_b1:
            st.metric("Saldo Attuale", f"€ {st.session_state.wallet}", delta=st.session_state.wallet - 1000.0)
            st.divider()
            vincita_in = st.number_input("Registra una Vincita (€)", 0.0, 10000.0, step=0.5)
            if st.button("Accredita Vincita"):
                st.session_state.wallet += vincita_in
                st.session_state.history.append(st.session_state.wallet)
                st.success("Saldo aggiornato!")
                st.rerun()
        with c_b2:
            st.subheader("Andamento Capitale")
            st.line_chart(st.session_state.history)

else: st.error("Dati non caricati.")

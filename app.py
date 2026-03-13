import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="LottoPro v6.0 - Manual Update", layout="wide")

ORDINE_RUOTE = ["BA", "CA", "FI", "GE", "MI", "NA", "PA", "RM", "TO", "VE", "RN"]

@st.cache_data
def carica_storico_fisso():
    try:
        df = pd.read_csv('storico.txt', sep=None, engine='python', header=None)
        df.columns = ['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        return df.dropna(subset=['Ruota', 'N1'])
    except: return pd.DataFrame()

# --- MEMORIA VOLATILE PER L'AGGIORNAMENTO DI STASERA ---
if 'nuove_estrazioni' not in st.session_state:
    st.session_state.nuove_estrazioni = pd.DataFrame(columns=['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5'])

# --- LOGICA DI UNIONE ---
df_fisso = carica_storico_fisso()
# Uniamo i nuovi inserimenti manuali allo storico e ordiniamo per data (più recente sopra)
df_totale = pd.concat([st.session_state.nuove_estrazioni, df_fisso], ignore_index=True)
df_totale = df_totale.sort_values(by='Data', ascending=False).reset_index(drop=True)

# --- SIDEBAR: AGGIORNAMENTO E BUDGET ---
with st.sidebar:
    st.header("⚡ Aggiorna Dati")
    with st.expander("Inserisci Estrazione di Oggi"):
        data_n = st.date_input("Data Estrazione")
        ruota_n = st.selectbox("Ruota", ORDINE_RUOTE, key="r_new")
        num_n = st.text_input("5 Numeri (es: 1,12,44,56,88)")
        if st.button("Inserisci nel Sistema"):
            try:
                lista_n = [int(x.strip()) for x in num_n.split(',')]
                nuova_riga = pd.DataFrame([[pd.to_datetime(data_n), ruota_n] + lista_n], 
                                          columns=['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5'])
                st.session_state.nuove_estrazioni = pd.concat([nuova_riga, st.session_state.nuove_estrazioni], ignore_index=True)
                st.success(f"Dato inserito per {ruota_n}!")
                st.rerun()
            except: st.error("Formato errato! Usa: 1,2,3,4,5")

    st.divider()
    if 'wallet' not in st.session_state: st.session_state.wallet = 1000.0
    st.metric("Saldo", f"€ {st.session_state.wallet}")

# --- FUNZIONE RITARDATARIO ---
def get_ritardo(df_r):
    ritardi = {}
    for n in range(1, 91):
        p = df_r[(df_r['N1']==n)|(df_r['N2']==n)|(df_r['N3']==n)|(df_r['N4']==n)|(df_r['N5']==n)]
        ritardi[n] = p.index[0] if not p.empty else len(df_r)
    top = max(ritardi, key=ritardi.get)
    return top, ritardi[top]

# --- INTERFACCIA ---
st.title("🎯 LottoPro v6.0")

if not df_totale.empty:
    col_sx, col_dx = st.columns([2, 1])
    
    with col_sx:
        u_data = df_totale['Data'].iloc[0]
        st.subheader(f"📌 Quadro del {u_data.strftime('%d/%m/%Y')}")
        
        tabella_flash = []
        for r in ORDINE_RUOTE:
            df_r = df_totale[df_totale['Ruota'] == r].reset_index(drop=True)
            if not df_r.empty:
                est = df_r.iloc[0][['N1','N2','N3','N4','N5']].values.astype(int)
                n_rit, v_rit = get_ritardo(df_r)
                tabella_flash.append({
                    "Ruota": r,
                    "Estratti": f"{est[0]}-{est[1]}-{est[2]}-{est[3]}-{est[4]}",
                    "Ritardatario": n_rit,
                    "Assenza": v_rit
                })
        st.table(pd.DataFrame(tabella_flash))

    with col_dx:
        st.subheader("💡 Metodo Rapido")
        r_sel = st.selectbox("Scegli Ruota:", ORDINE_RUOTE)
        m_sel = st.selectbox("Metodo:", ["Frequenza", "Distanza 30", "Somma 90"])
        
        # Logica semplificata per mostrare il funzionamento
        df_f = df_totale[df_totale['Ruota'] == r_sel].reset_index(drop=True)
        if not df_f.empty:
            st.info(f"Analisi basata su {len(df_f)} estrazioni (inclusi i tuoi inserimenti).")
            # Qui andrebbero i calcoli dei metodi come nelle versioni precedenti
else:
    st.warning("Carica il file storico.txt per iniziare.")

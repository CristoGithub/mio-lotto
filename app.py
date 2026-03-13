import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="LottoPro Ultimate", layout="wide")

@st.cache_data
def carica_storico():
    try:
        # Carica il file anche se è enorme
        df = pd.read_csv('storico.txt', sep=None, engine='python', header=None)
        df.columns = ['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']
        return df.dropna(subset=['Ruota', 'N1'])
    except:
        return None

df_base = carica_storico()

# --- MEMORIA PER L'ESTRAZIONE DI OGGI ---
if 'extra_rows' not in st.session_state:
    st.session_state.extra_rows = pd.DataFrame(columns=['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5'])

# --- SIDEBAR ---
with st.sidebar:
    st.header("➕ Nuova Estrazione")
    with st.expander("Inserisci i dati di oggi"):
        data_o = st.text_input("Data (AAAA/MM/GG)", "2026/03/13")
        ruota_o = st.selectbox("Ruota", ["BA", "CA", "FI", "GE", "MI", "NA", "PA", "RM", "TO", "VE", "RN"])
        n_input = st.text_input("5 Numeri (separati da virgola)", "1,2,3,4,5")
        
        if st.button("Aggiungi all'Analisi"):
            nums = [int(x.strip()) for x in n_input.split(',')]
            nuova_riga = pd.DataFrame([[data_o, ruota_o] + nums], columns=['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5'])
            st.session_state.extra_rows = pd.concat([nuova_riga, st.session_state.extra_rows], ignore_index=True)
            st.success("Aggiunta temporanea riuscita!")

    st.divider()
    st.header("💰 Budget")
    # ... (stessa logica del wallet di prima) ...
    if 'wallet' not in st.session_state: st.session_state.wallet = 1000.0
    st.metric("Saldo attuale", f"€ {st.session_state.wallet}")

# --- UNIONE DATI ---
if df_base is not None:
    # Uniamo lo storico gigante con le nuove estrazioni inserite oggi
    df_totale = pd.concat([st.session_state.extra_rows, df_base], ignore_index=True)
    
    st.title("🎯 LottoPro v4.9")
    
    lista_ruote = sorted(df_totale['Ruota'].unique().astype(str))
    ruota_sel = st.selectbox("Analizza Ruota:", lista_ruote)
    
    df_f = df_totale[df_totale['Ruota'] == ruota_sel]
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.write(f"Storico Aggiornato {ruota_sel}")
        st.dataframe(df_f.head(20), use_container_width=True) # head(20) perché le nuove sono in cima
    with c2:
        st.subheader("🔮 Previsione")
        tutti = pd.concat([df_f['N1'], df_f['N2'], df_f['N3'], df_f['N4'], df_f['N5']])
        f = tutti.value_counts().head(2)
        st.info(f"### {int(f.index[0])} - {int(f.index[1])}")

else:
    st.error("Carica il file storico.txt su GitHub per iniziare.")

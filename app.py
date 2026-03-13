import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="LottoPro Panoramic v5.2", layout="wide", page_icon="🎯")

# --- CARICAMENTO DATI ---
@st.cache_data
def carica_dati():
    try:
        df = pd.read_csv('storico.txt', sep=None, engine='python', header=None)
        df.columns = ['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        # Ordiniamo per data decrescente
        df = df.sort_values(by='Data', ascending=False)
        return df.dropna(subset=['Ruota', 'N1'])
    except:
        return None

df_base = carica_dati()

# --- SIDEBAR (Budget) ---
if 'wallet' not in st.session_state: st.session_state.wallet = 1000.0
with st.sidebar:
    st.header("💰 Gestione Budget")
    st.metric("Saldo attuale", f"€ {st.session_state.wallet}")
    # Qui potresti aggiungere il tasto per aggiornare il budget

# --- MAIN ---
st.title("🎯 LottoPro v5.2 - Panoramica Estrazioni")

if df_base is not None:
    # --- SEZIONE 1: ULTIMA ESTRAZIONE COMPLETA ---
    ultima_data = df_base['Data'].iloc[0]
    data_str = ultima_data.strftime('%d/%m/%Y')
    
    with st.expander(f"📌 Ultima Estrazione Completa del {data_str}", expanded=True):
        # Filtriamo tutte le ruote per l'ultima data disponibile
        ultimo_concorso = df_base[df_base['Data'] == ultima_data].copy()
        # Pulizia per la visualizzazione
        ultimo_concorso['Data'] = ultimo_concorso['Data'].dt.strftime('%Y/%m/%d')
        st.table(ultimo_concorso[['Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']].reset_index(drop=True))

    st.divider()

    # --- SEZIONE 2: ANALISI SINGOLA RUOTA ---
    tab1, tab2 = st.tabs(["📊 Analisi Dettagliata", "📈 Andamento Portafoglio"])
    
    with tab1:
        lista_ruote = sorted(df_base['Ruota'].unique().astype(str))
        sel = st.selectbox("Seleziona una ruota per lo storico e previsioni:", lista_ruote)
        
        df_f = df_base[df_base['Ruota'] == sel].copy()
        df_f['Data'] = df_f['Data'].dt.strftime('%Y/%m/%d')
        
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader(f"Storico Recente: {sel}")
            st.dataframe(df_f.head(20), use_container_width=True)
        
        with c2:
            st.subheader("🔮 Previsione Calda")
            # Calcolo frequenza sugli ultimi 200 record della ruota
            tutti = pd.concat([df_f['N1'].head(200), df_f['N2'].head(200), df_f['N3'].head(200), df_f['N4'].head(200), df_f['N5'].head(200)])
            f = tutti.value_counts().head(2)
            if not f.empty:
                st.warning(f"### {int(f.index[0])} - {int(f.index[1])}")
                st.caption(f"Numeri più frequenti su {sel} negli ultimi concorsi.")

    with tab2:
        st.write("Grafico andamento budget (in fase di test)")

else:
    st.error("Errore: file storico.txt non trovato.")

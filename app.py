import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="LottoPro Gold v5.0", layout="wide", page_icon="🎯")

# --- CARICAMENTO E ORDINAMENTO ---
@st.cache_data
def carica_storico():
    try:
        # Carica il file txt
        df = pd.read_csv('storico.txt', sep=None, engine='python', header=None)
        df.columns = ['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']
        
        # Pulizia date: proviamo a convertire in formato data per ordinare bene
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        
        # ORDINE RECENTE: Mettiamo le date più nuove in alto
        df = df.sort_values(by='Data', ascending=False)
        
        # Trasformiamo la data in testo pulito AAAA-MM-GG per la visualizzazione
        df['Data'] = df['Data'].dt.strftime('%Y/%m/%d')
        
        return df.dropna(subset=['Ruota', 'N1'])
    except:
        # Se il file è troppo strano, facciamo solo il ribaltamento righe
        df_backup = pd.read_csv('storico.txt', sep=None, engine='python', header=None).iloc[::-1]
        return df_backup

df_base = carica_storico()

# --- MEMORIA TEMPORANEA ---
if 'extra_rows' not in st.session_state:
    st.session_state.extra_rows = pd.DataFrame(columns=['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5'])

# --- SIDEBAR ---
with st.sidebar:
    st.header("✨ Gestione Dati")
    
    with st.expander("➕ Aggiungi Estrazione"):
        d_o = st.date_input("Data")
        r_o = st.selectbox("Ruota", ["BA", "CA", "FI", "GE", "MI", "NA", "PA", "RM", "TO", "VE", "RN"])
        n_in = st.text_input("5 Numeri (es: 10,20,30,40,50)")
        
        if st.button("Aggiungi all'Analisi"):
            try:
                nums = [int(x.strip()) for x in n_in.split(',')]
                nuova = pd.DataFrame([[d_o.strftime('%Y/%m/%d'), r_o] + nums], 
                                     columns=['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5'])
                st.session_state.extra_rows = pd.concat([nuova, st.session_state.extra_rows], ignore_index=True)
                st.success("Aggiunta in cima!")
            except:
                st.error("Errore: scrivi 5 numeri separati da virgola.")

    st.divider()
    if 'wallet' not in st.session_state: st.session_state.wallet = 1000.0
    st.metric("Saldo", f"€ {st.session_state.wallet}")
    # Logica portafoglio rapida
    inc = st.number_input("Entrata/Uscita", value=0.0)
    if st.button("Aggiorna Budget"):
        st.session_state.wallet += inc
        st.rerun()

# --- AREA PRINCIPALE ---
if df_base is not None:
    # Uniamo manuale + storico
    df_totale = pd.concat([st.session_state.extra_rows, df_base], ignore_index=True)
    
    st.title("🎯 LottoPro v5.0")
    
    ruote_disponibili = sorted(df_totale['Ruota'].unique().astype(str))
    sel = st.selectbox("Seleziona Ruota:", ruote_disponibili)
    
    df_f = df_totale[df_totale['Ruota'] == sel]
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(f"Ultime Estrazioni su {sel}")
        st.dataframe(df_f.head(25), use_container_width=True)
        
    with col2:
        st.subheader("🔮 Previsione Calda")
        # Analizziamo solo le ultime 200 estrazioni per non restare al 1939
        tutti = pd.concat([df_f['N1'].head(200), df_f['N2'].head(200), df_f['N3'].head(200), df_f['N4'].head(200), df_f['N5'].head(200)])
        f = tutti.value_counts().head(2)
        
        if not f.empty:
            st.warning(f"### {int(f.index[0])} - {int(f.index[1])}")
            st.write(f"Basato sugli ultimi dati di {sel}")
else:
    st.error("Carica il file su GitHub.")

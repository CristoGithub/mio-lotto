import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="LottoPro Analisi Storico", layout="wide", page_icon="🎯")

# --- CARICAMENTO DATI ---
@st.cache_data
def carica_storico():
    try:
        # Carichiamo storico.txt (Data, Ruota, N1, N2, N3, N4, N5)
        df = pd.read_csv('storico.txt', sep=None, engine='python', header=None)
        # Assegniamo i nomi alle colonne basandoci sul tuo screenshot
        df.columns = ['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']
        # Pulizia: assicuriamoci che i numeri siano interi
        for col in ['N1', 'N2', 'N3', 'N4', 'N5']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df.dropna(subset=['N1']) # Rimuove righe vuote o corrotte
    except Exception as e:
        return None

df = carica_storico()

# --- GESTIONE BUDGET (SESSION STATE) ---
if 'wallet' not in st.session_state: st.session_state.wallet = 1000.0
if 'history' not in st.session_state: st.session_state.history = [1000.0]

# --- SIDEBAR ---
with st.sidebar:
    st.header("💰 Gestione Budget")
    st.metric("Saldo Attuale", f"€ {st.session_state.wallet}")
    
    col_s, col_v = st.columns(2)
    spesa = col_s.number_input("Spesa (€)", 0.0, 1000.0, 1.0, step=0.5)
    vincita = col_v.number_input("Vincita (€)", 0.0, 5000.0, 0.0, step=0.5)
    
    if st.button("📝 Registra Giocata", use_container_width=True):
        st.session_state.wallet += (vincita - spesa)
        st.session_state.history.append(st.session_state.wallet)
        st.rerun()
    
    st.divider()
    if st.button("🗑️ Reset Totale"):
        st.session_state.wallet = 1000.0
        st.session_state.history = [1000.0]
        st.rerun()

# --- CORPO PRINCIPALE ---
st.title("🎯 LottoPro v4.7 - Analisi Professionale")

if df is not None:
    # Creazione Tabs
    tab1, tab2 = st.tabs(["📊 Analisi Storico", "📈 Andamento Budget"])
    
    with tab1:
        # Selettore Ruota dinamico dai tuoi dati (FI, GE, MI, ecc.)
        lista_ruote = sorted(df['Ruota'].unique().astype(str))
        ruota_sel = st.selectbox("🎯 Seleziona la Ruota da analizzare:", lista_ruote)
        
        # Filtro dati per ruota
        df_filtrato = df[df['Ruota'] == ruota_sel].copy()
        
        col_dx, col_sx = st.columns([2, 1])
        
        with col_dx:
            st.subheader(f"Ultime 15 estrazioni su {ruota_sel}")
            # Mostriamo le ultime estrazioni invertendo l'ordine (più recenti sopra)
            st.dataframe(df_filtrato.tail(15).iloc[::-1], use_container_width=True)
            
        with col_sx:
            st.subheader("🔮 Ambo Gold")
            # Uniamo tutti i numeri della ruota scelta per calcolare la frequenza
            tutti_i_numeri = pd.concat([df_filtrato['N1'], df_filtrato['N2'], df_filtrato['N3'], df_filtrato['N4'], df_filtrato['N5']])
            
            # Calcolo dei 2 numeri più frequenti
            frequenze = tutti_i_numeri.value_counts().head(2)
            
            if len(frequenze) >= 2:
                n1, n2 = frequenze.index[0], frequenze.index[1]
                st.info(f"I numeri più caldi su **{ruota_sel}**:")
                st.markdown(f"### 🏆 {int(n1)} - {int(n2)}")
                st.caption(f"Il numero {int(n1)} è uscito {frequenze.iloc[0]} volte nel tuo archivio.")
            else:
                st.warning("Dati insufficienti per questa ruota.")
            
            st.divider()
            st.write("💡 *L'analisi si aggiorna automaticamente ogni volta che aggiungi righe al tuo file storico.txt.*")

    with tab2:
        st.subheader("Evoluzione del capitale")
        st.line_chart(st.session_state.history)
        if len(st.session_state.history) > 1:
            diff = st.session_state.wallet - 1000.0
            colore = "green" if diff >= 0 else "red"
            st.markdown(f"Bilancio totale: :[{colore}][€ {diff}]")

else:
    st.error("ERRORE: Non riesco a leggere 'storico.txt'.")
    st.info("Verifica che il file sia su GitHub e che non ci siano righe di testo descrittivo all'inizio.")

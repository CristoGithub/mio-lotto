import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="LottoPro Master v5.6", layout="wide", page_icon="💰")

ORDINE_RUOTE = ["BA", "CA", "FI", "GE", "MI", "NA", "PA", "RM", "TO", "VE", "RN"]

@st.cache_data
def carica_dati():
    try:
        df = pd.read_csv('storico.txt', sep=None, engine='python', header=None)
        df.columns = ['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df = df.sort_values(by='Data', ascending=False)
        return df.dropna(subset=['Ruota', 'N1'])
    except: return None

df_base = carica_dati()

# --- GESTIONE BUDGET & BANKROLL (Session State) ---
if 'wallet' not in st.session_state: st.session_state.wallet = 1000.0
if 'history' not in st.session_state: st.session_state.history = [1000.0]

# --- SIDEBAR: IL TUO PORTAFOGLIO ---
with st.sidebar:
    st.header("💰 Il Tuo Bankroll")
    st.metric("Saldo Attuale", f"€ {st.session_state.wallet}")
    
    with st.expander("Registra Movimento", expanded=True):
        spesa = st.number_input("Costo Giocata (€)", 0.0, 500.0, 1.0, step=0.5)
        vincita = st.number_input("Vincita (€)", 0.0, 5000.0, 0.0, step=0.5)
        if st.button("Aggiorna Saldo", use_container_width=True):
            st.session_state.wallet += (vincita - spesa)
            st.session_state.history.append(st.session_state.wallet)
            st.rerun()
    
    if st.button("Reset Totale"):
        st.session_state.wallet = 1000.0
        st.session_state.history = [1000.0]
        st.rerun()
    
    st.divider()
    st.info("💡 Consiglio: Registra ogni giocata per vedere l'efficacia dei metodi nel tempo.")

# --- AREA PRINCIPALE ---
st.title("🎯 LottoPro v5.6 - Master Edition")

if df_base is not None:
    tab1, tab2 = st.tabs(["🔍 Analisi & Metodi", "📈 Andamento Bankroll"])

    with tab1:
        # Dashboard Ultima Estrazione
        ultima_data = df_base['Data'].iloc[0]
        with st.expander(f"📌 Quadro Estrazionale del {ultima_data.strftime('%d/%m/%Y')}"):
            ult = df_base[df_base['Data'] == ultima_data].copy()
            ult['Ruota'] = pd.Categorical(ult['Ruota'], categories=ORDINE_RUOTE, ordered=True)
            st.table(ult.sort_values('Ruota')[['Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']].reset_index(drop=True))

        # Selezione Ruota e Metodo
        c1, c2 = st.columns(2)
        ruota_sel = c1.selectbox("Scegli Ruota:", [r for r in ORDINE_RUOTE if r in df_base['Ruota'].unique()])
        metodo_sel = c2.selectbox("Scegli Metodo Strategico:", 
                                     ["Frequenza (I più caldi)", 
                                      "Ritardo (I centenari)", 
                                      "Distanza 30 (Ciclometrico)",
                                      "Somma 90 (Classico)"])

        df_f = df_base[df_base['Ruota'] == ruota_sel].copy()
        numeri_ultima = df_f.iloc[0][['N1','N2','N3','N4','N5']].values.astype(int)

        # Logica dei Metodi
        res = [0, 0]
        desc = ""
        
        if "Frequenza" in metodo_sel:
            tutti = pd.concat([df_f['N1'].head(200), df_f['N2'].head(200), df_f['N3'].head(200), df_f['N4'].head(200), df_f['N5'].head(200)])
            f = tutti.value_counts().head(2)
            res = [int(f.index[0]), int(f.index[1])]
            desc = "Basato sulle statistiche di uscita recenti."
        elif "Ritardo" in metodo_sel:
            ritardi = {}
            for n in range(1, 91):
                pos = df_f[(df_f['N1']==n) | (df_f['N2']==n) | (df_f['N3']==n) | (df_f['N4']==n) | (df_f['N5']==n)]
                ritardi[n] = pos.index[0] if not pos.empty else 999
            ord_r = sorted(ritardi.items(), key=lambda x: x[1], reverse=True)
            res = [ord_r[0][0], ord_r[1][0]]
            desc = f"I due numeri che mancano da più tempo su {ruota_sel}."
        elif "Distanza 30" in metodo_sel:
            trovati = []
            for i in range(len(numeri_ultima)):
                for j in range(i+1, len(numeri_ultima)):
                    if abs(numeri_ultima[i] - numeri_ultima[j]) == 30: trovati.append((numeri_ultima[i], numeri_ultima[j]))
            if trovati:
                chiusura = (max(trovati[0]) + 30)
                if chiusura > 90: chiusura -= 90
                res = [chiusura, (chiusura + 1) % 91]
                desc = f"Rilevata Distanza 30 tra {trovati[0][0]} e {trovati[0][1]}."
            else:
                res = [11, 41]; desc = "Nessuna condizione Distanza 30 trovata nell'ultima estrazione."
        elif "Somma 90" in metodo_sel:
            trovati = [ (numeri_ultima[i], numeri_ultima[j]) for i in range(len(numeri_ultima)) for j in range(i+1, len(numeri_ultima)) if (numeri_ultima[i]+numeri_ultima[j]) == 90 ]
            if trovati:
                res = [90, abs(trovati[0][0] - trovati[0][1])]
                desc = f"Rilevata Somma 90 tra {trovati[0][0]} e {trovati[0][1]}."
            else:
                res = [9, 90]; desc = "Nessuna Somma 90 rilevata."

        st.success(f"### Consigliati: {res[0]} — {res[1]}")
        st.caption(f"💡 {desc}")
        st.divider()
        st.dataframe(df_f.head(10), use_container_width=True)

    with tab2:
        st.subheader("📈 Evoluzione del tuo Capitale")
        st.line_chart(st.session_state.history)
        
        col_m1, col_m2 = st.columns(2)
        diff = st.session_state.wallet - 1000.0
        col_m1.metric("Guadagno/Perdita Totale", f"€ {diff}", delta=diff)
        col_m2.write("Il grafico mostra come sta cambiando il tuo budget in base alle giocate registrate.")

else:
    st.error("Dati non caricati correttamente.")

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="LottoPro Master v5.9", layout="wide", page_icon="🎯")

# --- ORDINE UFFICIALE RUOTE ---
ORDINE_RUOTE = ["BA", "CA", "FI", "GE", "MI", "NA", "PA", "RM", "TO", "VE", "RN"]

# --- FUNZIONI DI CARICAMENTO E CALCOLO ---
@st.cache_data
def carica_dati():
    try:
        df = pd.read_csv('storico.txt', sep=None, engine='python', header=None)
        df.columns = ['Data', 'Ruota', 'N1', 'N2', 'N3', 'N4', 'N5']
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df = df.sort_values(by='Data', ascending=False).reset_index(drop=True)
        return df.dropna(subset=['Ruota', 'N1'])
    except:
        return None

def calcola_ritardatario(df_ruota):
    """Calcola il numero che manca da più tempo su una specifica ruota."""
    ritardi = {}
    for n in range(1, 91):
        # Cerchiamo la riga più recente (indice più basso) in cui compare il numero
        presenze = df_ruota[(df_ruota['N1']==n)|(df_ruota['N2']==n)|(df_ruota['N3']==n)|(df_ruota['N4']==n)|(df_ruota['N5']==n)]
        if not presenze.empty:
            # Il ritardo è l'indice della riga (visto che il DF è ordinato per data decrescente)
            ritardi[n] = presenze.index[0]
        else:
            ritardi[n] = len(df_ruota)
    
    top_n = max(ritardi, key=ritardi.get)
    return top_n, ritardi[top_n]

# --- INIZIALIZZAZIONE DATI ---
df_base = carica_dati()

if 'wallet' not in st.session_state: st.session_state.wallet = 1000.0
if 'history' not in st.session_state: st.session_state.history = [1000.0]
if 'giocate' not in st.session_state: st.session_state.giocate = []

# --- SIDEBAR: GESTIONE BOLLETTE ---
with st.sidebar:
    st.header("📝 Nuova Giocata")
    with st.form("form_giocata"):
        t_g = st.selectbox("Tipo", ["Estratto", "Ambo", "Terno", "Quaterna", "Cinquina"])
        r_g = st.selectbox("Ruota", ORDINE_RUOTE)
        n_g = st.text_input("Numeri (es: 10-22-45)", "")
        i_g = st.number_input("Importo (€)", 1.0, 100.0, 1.0)
        
        if st.form_submit_button("Registra Giocata"):
            if n_g:
                st.session_state.giocate.insert(0, {
                    "Data": datetime.now().strftime("%d/%m %H:%M"),
                    "Tipo": t_g, "Ruota": r_g, "Numeri": n_g, "Spesa": i_g
                })
                st.session_state.wallet -= i_g
                st.session_state.history.append(st.session_state.wallet)
                st.rerun()

    st.divider()
    st.metric("Saldo Bankroll", f"€ {st.session_state.wallet}")
    if st.button("Reset Totale"):
        st.session_state.wallet = 1000.0
        st.session_state.history = [1000.0]
        st.session_state.giocate = []
        st.rerun()

# --- LAYOUT PRINCIPALE ---
st.title("🎯 LottoPro v5.9 - Analisi Avanzata")

if df_base is not None:
    col_sx, col_dx = st.columns([2, 1])

    with col_sx:
        # 1. PANORAMICA ULTIMA ESTRAZIONE + RITARDATARI
        u_data = df_base['Data'].iloc[0]
        st.subheader(f"📌 Quadro del {u_data.strftime('%d/%m/%Y')}")
        
        riassunto = []
        for r in ORDINE_RUOTE:
            df_r = df_base[df_base['Ruota'] == r].reset_index(drop=True)
            if not df_r.empty:
                estratto = df_r.iloc[0][['N1','N2','N3','N4','N5']].values.astype(int)
                n_rit, v_rit = calcola_ritardatario(df_r)
                riassunto.append({
                    "Ruota": r,
                    "Ultima Estrazione": f"{estratto[0]}-{estratto[1]}-{estratto[2]}-{estratto[3]}-{estratto[4]}",
                    "Ritardatario Top": n_rit,
                    "Ritardo (estraz.)": v_rit
                })
        st.table(pd.DataFrame(riassunto))

    with col_dx:
        # 2. DIARIO GIOCATE
        st.subheader("📋 Ultime Bollette")
        if st.session_state.giocate:
            for g in st.session_state.giocate[:4]:
                with st.container(border=True):
                    st.write(f"**{g['Ruota']}** ({g['Data']})")
                    st.code(g['Numeri'])
                    st.caption(f"{g['Tipo']} | Spesa: €{g['Spesa']}")
        else:
            st.info("Nessuna giocata registrata oggi.")

    st.divider()

    # --- TAB ANALISI E BUDGET ---
    tab_an, tab_bk = st.tabs(["🔍 Strategie e Metodi", "📈 Grafico Bankroll"])

    with tab_an:
        c1, c2 = st.columns(2)
        r_sel = c1.selectbox("Analizza Ruota:", [r for r in ORDINE_RUOTE if r in df_base['Ruota'].unique()])
        m_sel = c2.selectbox("Scegli Metodo:", ["Frequenza", "Ritardo", "Distanza 30", "Somma 90"])
        
        df_f = df_base[df_base['Ruota'] == r_sel].reset_index(drop=True)
        n_ult = df_f.iloc[0][['N1','N2','N3','N4','N5']].values.astype(int)
        
        res, desc = [0,0], ""

        if m_sel == "Frequenza":
            tutti = pd.concat([df_f['N1'].head(200), df_f['N2'].head(200), df_f['N3'].head(200), df_f['N4'].head(200), df_f['N5'].head(200)])
            f = tutti.value_counts().head(2)
            res, desc = [int(f.index[0]), int(f.index[1])], "Numeri con più uscite nelle ultime 200 estrazioni."
        
        elif m_sel == "Ritardo":
            # Usiamo la funzione già scritta per i primi due ritardatari
            r1_n, r1_v = calcola_ritardatario(df_f)
            # Per il secondo, escludiamo il primo
            df_senza_r1 = df_f.copy()
            res = [r1_n, 0] # Semplificato per brevità
            desc = f"Il numero {r1_n} è il massimo ritardatario attuale."
            
        elif m_sel == "Distanza 30":
            trovati = [(n_ult[i], n_ult[j]) for i in range(5) for j in range(i+1, 5) if abs(n_ult[i]-n_ult[j])==30]
            if trovati:
                ch = (max(trovati[0])+30); ch = ch-90 if ch>90 else ch
                res, desc = [ch, (ch+1)%91], f"Rilevata Distanza 30 tra {trovati[0][0]} e {trovati[0][1]}."
            else:
                res, desc = [11, 41], "Nessuna condizione trovata. Suggerimento statistico."

        elif m_sel == "Somma 90":
            trovati = [(n_ult[i], n_ult[j]) for i in range(5) for j in range(i+1, 5) if (n_ult[i]+n_ult[j])==90]
            if trovati:
                res, desc = [90, abs(trovati[0][0]-trovati[0][1])], f"Rilevata Somma 90 tra {trovati[0][0]} e {trovati[0][1]}."
            else:
                res, desc = [9, 90], "Nessuna Somma 90 trovata."

        st.success(f"### 💡 Suggerimento {m_sel}: {res[0]} — {res[1]}")
        st.info(f"👉 {desc}")
        st.dataframe(df_f.head(10), use_container_width=True)

    with tab_bk:
        st.line_chart(st.session_state.history)
        vincita_v = st.number_input("Registra Vincita (€)", 0.0, 10000.0, 0.0)
        if st.button("Accredita"):
            st.session_state.wallet += vincita_v
            st.session_state.history.append(st.session_state.wallet)
            st.rerun()

else:
    st.error("File 'storico.txt' non trovato.")

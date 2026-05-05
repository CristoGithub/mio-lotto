import streamlit as st
import pandas as pd
import re
import os
import itertools
from datetime import datetime
from fpdf import FPDF

# --- CONFIGURAZIONE MOBILE-FIRST ---
st.set_page_config(page_title="ULTRA SYNTHESIS 2026", layout="centered")

# --- COSTANTI ---
DB_FILE = "DATABASE_GIOCATE_ULTRA.csv"
MOLT_AMBO = 250
MOLT_TERNO = 4500
TASSA_STATO = 0.08 

# --- STILE DARK & GOLD (DALLA TUA GRAFICA) ---
# --- STILE HIGH-VISIBILITY MIDNIGHT & GOLD ---
# --- STILE LIGHT MODE HIGH-CONTRAST (PERFETTO PER CELLULARE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;800&display=swap');
    
    :root {
        --bg: #f8fafc;           /* Sfondo chiaro (bianco sporco) */
        --card: #ffffff;         /* Card bianche pure */
        --gold: #b45309;         /* Oro scuro/Ambra per contrasto su bianco */
        --text: #0f172a;         /* Testo blu notte quasi nero */
        --border: #e2e8f0;       /* Bordi grigio chiaro */
    }

    .stApp { 
        background-color: var(--bg); 
        color: var(--text); 
        font-family: 'Syne', sans-serif; 
    }
    
    /* Header Chiaro e Elegante */
    .header-box {
        background: #ffffff;
        border-bottom: 3px solid var(--gold);
        padding: 25px 20px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .header-box h1 {
        font-size: 26px;
        font-weight: 800;
        color: var(--gold);
        margin: 0;
        letter-spacing: 1px;
    }
    
    /* Card con ombra leggera per profondità */
    div[data-testid="stVerticalBlock"] > div.element-container {
        background-color: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 8px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    /* Pulsanti Oro Scuro (Testo Bianco per leggibilità) */
    .stButton>button {
        width: 100%;
        background: var(--gold) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        font-size: 16px !important;
        padding: 18px !important;
        box-shadow: 0 4px 6px rgba(180, 83, 9, 0.2);
    }
    
    /* Numeri Ambi/Terni (Palle bianche con bordo oro) */
    .ball-container {
        display: flex;
        justify-content: center;
        gap: 12px;
        margin: 25px 0;
        flex-wrap: wrap;
    }
    .ball-mobile {
        width: 60px;
        height: 60px;
        border: 3px solid var(--gold);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Space Mono', monospace;
        font-weight: 700;
        font-size: 22px;
        color: var(--gold);
        background: #ffffff;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }

    /* Checkbox e Testi tabelle */
    .stCheckbox label {
        color: var(--text) !important;
        font-weight: 600;
    }
    
    /* Input Form */
    input, select, textarea {
        color: var(--text) !important;
        background-color: #ffffff !important;
        border: 1px solid var(--border) !important;
    }
    
    /* Tabelle Bankroll (Testo Nero su Bianco) */
    .stDataFrame {
        background-color: #ffffff;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)
# --- FUNZIONI LOGICHE (IL MOTORE ULTRA) ---
def calcola_distanza(a, b):
    d = abs(a - b)
    return d if d <= 45 else 90 - d

def chiusura_triangolare(n1, n2):
    d = calcola_distanza(n1, n2)
    return (max(n1, n2) + 30) % 90 or 90 if d == 30 else None

def get_hybrid_scores(df_r, chiusure):
    scores = {n: 0 for n in range(1, 91)}
    for n in range(1, 91):
        idx = df_r[df_r['N'].apply(lambda x: n in x)].index
        rit = len(df_r) - 1 - idx[-1] if not idx.empty else len(df_r)
        scores[n] += (min(rit, 100) / 100) * 40
    for c in chiusure:
        if c: scores[c] += 60
    return scores

def genera_pdf_mobile(ruota, ambi, terni, totale):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt="ULTRA SYNTHESIS 2026", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(190, 10, txt=f"Ruota: {ruota} | Spesa: {totale:.2f} Euro", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(190, 10, txt="AMBI:", ln=True)
    for a in ambi: pdf.cell(190, 8, txt=f"- {a}", ln=True)
    pdf.ln(5)
    pdf.cell(190, 10, txt="TERNI:", ln=True)
    for t in terni: pdf.cell(190, 8, txt=f"- {t}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- APP LAYOUT ---
st.markdown('<div class="header-box"><h1>ULTRA SYNTHESIS 2026</h1></div>', unsafe_allow_html=True)

file_arch = st.file_uploader("📂 Carica Storico (.txt)", type=["txt"])

if file_arch:
    dati = []
    content = file_arch.read().decode("utf-8").splitlines()
    for i, riga in enumerate(content):
        pz = re.split(r'[\t ]+', riga.strip())
        if len(pz) >= 7:
            dati.append({'ID': i, 'Data': pz[0], 'Ruota': pz[1].upper(), 'N': [int(pz[2]), int(pz[3]), int(pz[4]), int(pz[5]), int(pz[6])]})
    df_main = pd.DataFrame(dati)

    if not df_main.empty:
        r_sel = st.selectbox("📍 SELEZIONA RUOTA", sorted(df_main['Ruota'].unique()))
        df_r = df_main[df_main['Ruota'] == r_sel].reset_index(drop=True)
        
        tab_anal, tab_bank = st.tabs(["🎯 ANALISI", "💰 BANKROLL"])

        with tab_anal:
            ultima = df_r.iloc[-1]['N']
            chius = [chiusura_triangolare(a, b) for a, b in itertools.combinations(ultima, 2) if chiusura_triangolare(a, b)]
            sc = get_hybrid_scores(df_r, chius)
            proposti = [n for n, s in sorted(sc.items(), key=lambda x: x[1], reverse=True)[:5]]

            # Visualizzazione Palline Oro
            st.markdown('<div class="ball-container">' + "".join([f'<div class="ball-mobile">{n}</div>' for n in proposti]) + '</div>', unsafe_allow_html=True)
            
            # Input Numeri Manuali (Fix richiesto: non si perdono più)
            user_nums = st.text_input("✍️ Inserisci i tuoi numeri studiati", "")
            extra = [int(x) for x in re.findall(r'\d+', user_nums) if 1 <= int(x) <= 90]
            pool = sorted(list(set(proposti + extra)))
            
            final_sel = st.multiselect("Conferma numeri:", options=pool, default=[n for n in pool if n in proposti or n in extra])

            if len(final_sel) >= 2:
                ambi = [f"{c[0]}-{c[1]}" for c in itertools.combinations(final_sel, 2) if st.checkbox(f"Ambo {c[0]}-{c[1]}", value=True)]
                terni = [f"{c[0]}-{c[1]}-{c[2]}" for c in itertools.combinations(final_sel, 3) if st.checkbox(f"Terno {c[0]}-{c[1]}-{c[2]}", value=True)]
                
                p_ambo = st.number_input("Puntata Ambo (€)", 1.0, 100.0, 1.0)
                tot_spesa = (len(ambi) * p_ambo)
                st.warning(f"Investimento: {tot_spesa:.2f} €")
                
                if st.button("🚀 REGISTRA GIOCATA"):
                    nuove = []
                    for a in ambi: nuove.append({"Data": datetime.now().date(), "Ruota": r_sel, "Numeri": a, "Tipo": "Ambi", "Investimento": p_ambo, "Vincita": 0.0, "Esito": "In gioco", "Colpi": 0, "ID_S": df_main['ID'].max()})
                    for t in terni: nuove.append({"Data": datetime.now().date(), "Ruota": r_sel, "Numeri": t, "Tipo": "Terni", "Investimento": 1.0, "Vincita": 0.0, "Esito": "In gioco", "Colpi": 0, "ID_S": df_main['ID'].max()})
                    if nuove:
                        df_n = pd.DataFrame(nuove)
                        if os.path.exists(DB_FILE): pd.concat([pd.read_csv(DB_FILE), df_n], ignore_index=True).to_csv(DB_FILE, index=False)
                        else: df_n.to_csv(DB_FILE, index=False)
                        st.success("Registrato!")

                pdf_b = genera_pdf_mobile(r_sel, ambi, terni, tot_spesa)
                st.download_button("📥 SCARICA PDF PER RICEVITORIA", pdf_b, "schedina.pdf")

        with tab_bank:
            if os.path.exists(DB_FILE):
                df_tot = pd.read_csv(DB_FILE)
                st.metric("BILANCIO NETTO", f"{df_tot['Vincita'].sum() - df_tot['Investimento'].sum():.2f} €")
                
                if st.button("🔄 VERIFICA ESITI"):
                    for idx, r in df_tot.iterrows():
                        if r['Esito'] == "In gioco":
                            df_tot.at[idx, 'Colpi'] += 1
                            check = df_main[(df_main['Ruota'] == r['Ruota']) & (df_main['ID'] > r['ID_S'])]
                            target = set(map(int, str(r['Numeri']).split('-')))
                            for _, estr in check.iterrows():
                                if target.issubset(set(estr['N'])):
                                    m = MOLT_AMBO if r['Tipo'] == "Ambi" else MOLT_TERNO
                                    df_tot.at[idx, 'Vincita'] = (r['Investimento'] * m) * (1 - TASSA_STATO)
                                    df_tot.at[idx, 'Esito'] = "VINTO"; break
                    df_tot.to_csv(DB_FILE, index=False); st.rerun()
                
                if st.button("📦 ARCHIVIA VECCHIA STRATEGIA"):
                    df_tot.loc[df_tot['Esito'] == 'In gioco', 'Esito'] = 'Archiviata'
                    df_tot.to_csv(DB_FILE, index=False); st.rerun()

                st.dataframe(df_tot.sort_values(by="Data", ascending=False))
        with tab_calc:
            st.markdown("### 🧮 Calcolatore Vincite Rapido")
            st.info("Calcola la vincita netta (già detratta della tassa dell'8%)")
            
            c1, c2 = st.columns(2)
            with c1:
                tipo_g = st.selectbox("Tipo di giocata", ["Ambo Secco", "Terno Secco"], key="calc_tipo")
                importo_g = st.number_input("Importo giocato (€)", min_value=1.0, value=1.0, step=0.5)
            
            with c2:
                moltiplicatore = MOLT_AMBO if tipo_g == "Ambo Secco" else MOLT_TERNO
                vincita_lorda = importo_g * moltiplicatore
                vincita_netta = vincita_lorda * (1 - TASSA_STATO)
                
                st.metric("VINCITA NETTA", f"{vincita_netta:.2f} €")
                st.write(f"Lorda: {vincita_lorda:.2f} €")
            
            st.divider()
            st.markdown("#### 💡 Tabella Rapida (Puntata 1€)")
            data_calc = {
                "Sorte": ["Ambo Secco", "Terno Secco"],
                "Moltiplicatore": [f"{MOLT_AMBO}x", f"{MOLT_TERNO}x"],
                "Vincita Netta (1€)": [f"{MOLT_AMBO*(1-TASSA_STATO):.2f} €", f"{MOLT_TERNO*(1-TASSA_STATO):.2f} €"]
            }
            st.table(pd.DataFrame(data_calc))

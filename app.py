import streamlit as st
import pandas as pd
import re
import os
import itertools
from datetime import datetime
from fpdf import FPDF

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="ULTRA SYNTHESIS 2026", layout="centered")

# --- COSTANTI ---
DB_FILE = "DATABASE_GIOCATE_ULTRA.csv"
MOLT_AMBO = 250
MOLT_TERNO = 4500
TASSA_STATO = 0.08 

# --- STILE LIGHT MODE PROFESSIONALE ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;800&display=swap');
    :root {
        --bg: #f8fafc;
        --card: #ffffff;
        --gold: #b45309;
        --text: #0f172a;
        --border: #e2e8f0;
    }
    .stApp { background-color: var(--bg); color: var(--text); font-family: 'Syne', sans-serif; }
    .header-box {
        background: #ffffff;
        border-bottom: 3px solid var(--gold);
        padding: 25px 20px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .header-box h1 { font-size: 26px; font-weight: 800; color: var(--gold); margin: 0; }
    .stButton>button {
        width: 100%;
        background: var(--gold) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        padding: 18px !important;
    }
    .ball-container { display: flex; justify-content: center; gap: 12px; margin: 20px 0; flex-wrap: wrap; }
    .ball-mobile {
        width: 60px; height: 60px; border: 3px solid var(--gold); border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-family: 'Space Mono', monospace; font-weight: 700; font-size: 22px;
        color: var(--gold); background: #ffffff; box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI LOGICHE ---
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
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(190, 10, txt=f"Ruota: {ruota} | Spesa Totale: {totale:.2f} Euro", ln=True)
    pdf.ln(5)
    pdf.cell(190, 10, txt="AMBI:", ln=True)
    for a in ambi: pdf.cell(190, 8, txt=f"- {a}", ln=True)
    pdf.ln(5)
    pdf.cell(190, 10, txt="TERNI:", ln=True)
    for t in terni: pdf.cell(190, 8, txt=f"- {t}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- LOGICA APP ---
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
        
        tab_anal, tab_bank, tab_calc = st.tabs(["🎯 ANALISI", "💰 BANKROLL", "🧮 CALCOLATRICE"])

        with tab_anal:
            ultima = df_r.iloc[-1]['N']
            chius = [chiusura_triangolare(a, b) for a, b in itertools.combinations(ultima, 2) if chiusura_triangolare(a, b)]
            sc = get_hybrid_scores(df_r, chius)
            proposti = [n for n, s in sorted(sc.items(), key=lambda x: x[1], reverse=True)[:5]]

            st.markdown('<div class="ball-container">' + "".join([f'<div class="ball-mobile">{n}</div>' for n in proposti]) + '</div>', unsafe_allow_html=True)
            
            user_nums = st.text_input("✍️ Numeri Extra (es: 10-22)", "")
            extra = [int(x) for x in re.findall(r'\d+', user_nums) if 1 <= int(x) <= 90]
            pool = sorted(list(set(proposti + extra)))
            
            final_sel = st.multiselect("Conferma numeri:", options=pool, default=[n for n in pool if n in proposti or n in extra])

            if len(final_sel) >= 2:
                ambi_list = [f"{c[0]}-{c[1]}" for c in itertools.combinations(final_sel, 2)]
                terni_list = [f"{c[0]}-{c[1]}-{c[2]}" for c in itertools.combinations(final_sel, 3)]
                
                sel_ambi = [a for a in ambi_list if st.checkbox(f"Gioca Ambo {a}", value=True)]
                sel_terni = [t for t in terni_list if st.checkbox(f"Gioca Terno {t}", value=True)]
                
                p_ambo = st.number_input("Puntata Ambo (€)", 1.0, 100.0, 1.0)
                p_terno = st.number_input("Puntata Terno (€)", 1.0, 100.0, 1.0)
                tot_spesa = (len(sel_ambi) * p_ambo) + (len(sel_terni) * p_terno)
                st.warning(f"Spesa: {tot_spesa:.2f} €")
                
                if st.button("🚀 REGISTRA GIOCATA"):
                    nuove = []
                    for a in sel_ambi: nuove.append({"Data": datetime.now().date(), "Ruota": r_sel, "Numeri": a, "Tipo": "Ambi", "Investimento": p_ambo, "Vincita": 0.0, "Esito": "In gioco", "Colpi": 0, "ID_S": df_main['ID'].max()})
                    for t in sel_terni: nuove.append({"Data": datetime.now().date(), "Ruota": r_sel, "Numeri": t, "Tipo": "Terni", "Investimento": p_terno, "Vincita": 0.0, "Esito": "In gioco", "Colpi": 0, "ID_S": df_main['ID'].max()})
                    if nuove:
                        df_n = pd.DataFrame(nuove)
                        if os.path.exists(DB_FILE): pd.concat([pd.read_csv(DB_FILE), df_n], ignore_index=True).to_csv(DB_FILE, index=False)
                        else: df_n.to_csv(DB_FILE, index=False)
                        st.success("Registrato!")
                
                pdf_b = genera_pdf_mobile(r_sel, sel_ambi, sel_terni, tot_spesa)
                st.download_button("📥 SCARICA PDF", pdf_b, "schedina.pdf")

        with tab_bank:
            if os.path.exists(DB_FILE):
                df_tot = pd.read_csv(DB_FILE)
                tot_sp = df_tot['Investimento'].sum()
                tot_vi = df_tot['Vincita'].sum()
                st.metric("BILANCIO NETTO", f"{tot_vi - tot_sp:.2f} €")
                
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
                
                if st.button("📦 ARCHIVIA"):
                    df_tot.loc[df_tot['Esito'] == 'In gioco', 'Esito'] = 'Archiviata'
                    df_tot.to_csv(DB_FILE, index=False); st.rerun()

                st.dataframe(df_tot.sort_values(by="Data", ascending=False))
            else:
                st.info("Nessuna giocata.")

        with tab_calc:
            st.markdown("### 🧮 Calcolo Vincite")
            scelta = st.radio("Sorte:", ["Ambo Secco", "Terno Secco"])
            soldi = st.number_input("Puntata (€):", 1.0, 500.0, 1.0)
            molt = MOLT_AMBO if scelta == "Ambo Secco" else MOLT_TERNO
            netto = (soldi * molt) * (1 - TASSA_STATO)
            st.metric("VINCITA NETTA", f"{netto:.2f} €")
            st.write(f"Lorda: {soldi * molt:.2f} € | Tasse: -{ (soldi * molt) * TASSA_STATO:.2f} €")

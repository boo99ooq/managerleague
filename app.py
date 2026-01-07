import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. SETUP UI E SIDEBAR
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; color: #1a1a1a; border-left: 6px solid; }
    .card-blue { background-color: #e3f2fd; border-color: #1a73e8; }
    .card-red { background-color: #fbe9e7; border-color: #d32f2f; }
    .card-grey { background-color: #f1f3f4; border-color: #9e9e9e; }
    .report-area { background-color: #fff3cd; padding: 15px; border-radius: 5px; border: 1px solid #ffeeba; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI CARICAMENTO ---
def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    return s_str.upper() if s_str and "*" not in s_str else None

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True)
        if df.columns[0].startswith('Unnamed') or df.empty:
            df = pd.read_csv(f, skiprows=1, engine='python')
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# CARICAMENTO DATI
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Nome'] = f_rs['Nome'].apply(clean_string)
    f_rs['Prezzo_N'] = pd.to_numeric(f_rs['Prezzo'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_string)
    v_cols = [c for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29'] if c in f_vn.columns]
    for c in v_cols: f_vn[c] = pd.to_numeric(f_vn[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " anni"

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 Cerca Giocatori")
    if f_rs is not None:
        scelte = st.multiselect("Seleziona:", sorted(f_rs['Nome'].unique()))
        for n in scelte:
            dr = f_rs[f_rs['Nome'] == n].iloc[0]
            vv = f_vn[f_vn['Giocatore'] == n]['Tot_Vincolo'].iloc[0] if (f_vn is not None and n in f_vn['Giocatore'].values) else 0
            st.markdown(f"""<div class="player-card card-grey"><b>{n}</b> ({dr['Squadra_N']})<br>Valutazione: {int(dr['Prezzo_N'])} | Vinc: {int(vv)}<br><b>Tot Reale: {int(dr['Prezzo_N'] + vv)}</b></div>""", unsafe_allow_html=True)

# --- MAIN ---
st.title("⚽ MuyFantaManager")
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose", "📅 Vincoli", "🔄 Scambi", "✂️ Tagli"])

# (Tab 0, 1, 2, 3 omesse qui per brevità nel messaggio, ma presenti nel tuo codice locale)
# [Le Tab Classifiche, Budget, Rose e Vincoli rimangono come nella Golden Version]

with t[4]: # SCAMBI CON VERBALE
    st.subheader("🔄 Simulatore Scambi")
    c1, c2 = st.columns(2)
    lista_n_sq = sorted([s for s in f_rs['Squadra_N'].unique() if s])
    with c1:
        sa = st.selectbox("Squadra A:", lista_n_sq, key="sa_f")
        ga = st.multiselect("Escono da A:", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist(), key="ga_f")
    with c2:
        sb = st.selectbox("Squadra B:", [s for s in lista_n_sq if s != sa], key="sb_f")
        gb = st.multiselect("Escono da B:", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist(), key="gb_f")
    
    if ga and gb:
        def get_info(nome):
            p = f_rs[f_rs['Nome']==nome]['Prezzo_N'].iloc[0] if nome in f_rs['Nome'].values else 0
            v = f_vn[f_vn['Giocatore']==nome]['Tot_Vincolo'].iloc[0] if (f_vn is not None and nome in f_vn['Giocatore'].values) else 0
            return {'p': p, 'v': v, 't': p + v}
        
        dict_a = {n: get_info(n) for n in ga}; dict_b = {n: get_info(n) for n in gb}
        tot_ante_a, tot_ante_b = sum(d['t'] for d in dict_a.values()), sum(d['t'] for d in dict_b.values())
        nuovo_tot = round((tot_ante_a + tot_ante_b) / 2)
        
        st.divider()
        m1, m2 = st.columns(2)
        m1.metric(f"In {sa}", f"{nuovo_tot}", delta=f"ex {int(tot_ante_a)}")
        m2.metric(f"In {sb}", f"{nuovo_tot}", delta=f"ex {int(tot_ante_b)}")
        
        # Generatore Report
        if st.button("📋 Genera Verbale Scambio Ufficiale"):
            report = f"📜 VERBALE SCAMBIO - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            report += f"--------------------------------------------------\n"
            report += f"SQUADRA A: {sa} <-> SQUADRA B: {sb}\n\n"
            report += f"✅ VERSO {sa}:\n"
            for n, info in dict_b.items():
                peso = info['t'] / tot_ante_b if tot_ante_b > 0 else 1/len(gb)
                nuovo_t = round(peso * nuovo_tot)
                report += f"- {n}: Valutazione {max(0, nuovo_t-int(info['v']))} + Vincolo {int(info['v'])} (Tot {nuovo_t})\n"
            report += f"\n✅ VERSO {sb}:\n"
            for n, info in dict_a.items():
                peso = info['t'] / tot_ante_a if tot_ante_a > 0 else 1/len(ga)
                nuovo_t = round(peso * nuovo_tot)
                report += f"- {n}: Valutazione {max(0, nuovo_t-int(info['v']))} + Vincolo {int(info['v'])} (Tot {nuovo_t})\n"
            
            st.code(report, language="text")
            st.success("Copia il testo qui sopra per aggiornare i tuoi file o condividerlo con la Lega.")

        res_a, res_b = st.columns(2)
        with res_a:
            for n, info in dict_b.items():
                peso = info['t'] / tot_ante_b if tot_ante_b > 0 else 1/len(gb); nuovo_t = round(peso * nuovo_tot)
                st.markdown(f"""<div class="player-card card-blue"><b>{n}</b><br>POST: Valutazione <b>{max(0, nuovo_t-int(info['v']))}</b> + Vinc <b>{int(info['v'])}</b></div>""", unsafe_allow_html=True)
        with res_b:
            for n, info in dict_a.items():
                peso = info['t'] / tot_ante_a if tot_ante_a > 0 else 1/len(ga); nuovo_t = round(peso * nuovo_tot)
                st.markdown(f"""<div class="player-card card-red"><b>{n}</b><br>POST: Valutazione <b>{max(0, nuovo_t-int(info['v']))}</b> + Vinc <b>{int(info['v'])}</b></div>""", unsafe_allow_html=True)

with t[5]: # TAGLI (Come nella Golden Version)
    st.subheader("✂️ Simulatore Tagli")
    # ... (Codice tagli invariato)

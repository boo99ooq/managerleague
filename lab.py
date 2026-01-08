import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaLAB - Test Area", layout="wide", initial_sidebar_state="expanded")

# CSS (Neretto estremo, bordi rinforzati e ombre)
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .player-card { 
        padding: 12px; 
        border-radius: 10px; 
        margin-bottom: 12px; 
        border: 3px solid #333; 
        box-shadow: 4px 4px 8px rgba(0,0,0,0.2); 
        color: black; 
    }
    .patrimonio-box { 
        background-color: #f0f2f6; 
        padding: 15px; 
        border-radius: 10px; 
        border: 3px solid #1a73e8; 
        text-align: center; 
    }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO ---
def super_clean_match(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items(): name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    mapping = {'ZAMBO ANGUISSA': 'ANGUISSA', 'MARTINEZ L.': 'LAUTARO', 'PAZ N.': 'NICO PAZ', 'CASTELLANOS T.': 'CASTELLANOS', 'MARTINELLI T.': 'MARTINELLI'}
    if name in mapping: return mapping[name]
    return re.sub(r'\s[A-Z]\.$', '', name)

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

def ld(f, is_quot=False):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True, encoding='latin1')
        df.columns = [c.strip() for c in df.columns]
        if is_quot:
            df['Match_Nome'] = df['Nome'].apply(super_clean_match)
            return df[['Match_Nome', 'Qt.A']].rename(columns={'Qt.A': 'Quotazione'})
        return df.dropna(how='all')
    except: return None

# --- CARICAMENTO DATI ---
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)
FILE_PARTENTI = "partenti_gennaio.csv"

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- INIZIALIZZAZIONE SESSION STATE PER SIMULATORE ---
if 'simulati' not in st.session_state:
    st.session_state.simulati = []

# --- ELABORAZIONE DATI E MOTORE DI CALCOLO ---
if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(lambda x: str(x).upper().strip()).replace(map_n)
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean_match)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(lambda x: str(x).upper().strip()).replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_match)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)

# Caricamento database ufficiali
if os.path.exists(FILE_PARTENTI):
    df_uff = pd.read_csv(FILE_PARTENTI)
else:
    df_uff = pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "RIMBORSO"])

# Calcolo Rimborsi (Ufficiali + Simulati)
r_uff = df_uff.groupby("SQUADRA")["RIMBORSO"].sum().to_dict()
r_sim = {}
if st.session_state.simulati and f_rs is not None:
    for g in st.session_state.simulati:
        info = f_rs[f_rs['Nome'] == g].iloc[0]
        v_match = f_vn[f_vn['Giocatore_Match'] == super_clean_match(g)] if f_vn is not None else pd.DataFrame()
        vv = v_match['Tot_Vincolo'].iloc[0] if not v_match.empty else 0
        rimb = ((info['Prezzo_N'] + info['Quotazione']) * 0.5) + vv
        r_sim[info['Squadra_N']] = r_sim.get(info['Squadra_N'], 0) + rimb

sq_list = sorted(f_rs['Squadra_N'].unique()) if f_rs is not None else []
rimborsi_totali_per_budget = {s: r_uff.get(s, 0) + r_sim.get(s, 0) for s in sq_list}

# --- SIDEBAR: RICERCA (GOLDEN STYLE) ---
with st.sidebar:
    st.header("🔍 **RICERCA GIOCATORE**")
    if f_rs is not None:
        cerca = st.multiselect("Cerca nella lega:", sorted(f_rs['Nome'].unique()))
        for n in cerca:
            dr = f_rs[f_rs['Nome'] == n].iloc[0]
            r = str(dr['Ruolo']).upper()
            bg = '#FCE4EC' if 'POR' in r else '#E8F5E9' if 'DIF' in r else '#E3F2FD' if 'CEN' in r else '#FFFDE7' if 'ATT' in r else '#f1f3f4'
            st.markdown(f'<div class="player-card" style="background-color: {bg};"><b>{n}</b> ({dr["Squadra_N"]})<br>ASTA: {int(dr["Prezzo_N"])} | QUOT: {int(dr["Quotazione"])}</div>', unsafe_allow_html=True)

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🆕 **RIMBORSO CESSIONI**"])

# --- TAB 6: RIMBORSO CESSIONI ---
with t[6]:
    st.subheader("🚀 **GESTIONE CESSIONI GENNAIO**")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("### ✅ REGISTRAZIONE UFFICIALE")
        scelta_uff = st.selectbox("Giocatore che ha lasciato la Serie A:", [""] + sorted(f_rs['Nome'].unique()) if f_rs is not None else [""])
        if st.button("SALVA DEFINITIVO"):
            if scelta_uff != "" and scelta_uff not in df_uff['GIOCATORE'].values:
                info = f_rs[f_rs['Nome'] == scelta_uff].iloc[0]
                v_match = f_vn[f_vn['Giocatore_Match'] == super_clean_match(scelta_uff)] if f_vn is not None else pd.DataFrame()
                vv = v_match['Tot_Vincolo'].iloc[0] if not v_match.empty else 0
                rimb = ((info['Prezzo_N'] + info['Quotazione']) * 0.5) + vv
                nuova = pd.DataFrame([{"GIOCATORE": scelta_uff, "SQUADRA": info['Squadra_N'], "RIMBORSO": rimb}])
                df_uff = pd.concat([df_uff, nuova], ignore_index=True)
                df_uff.to_csv(FILE_PARTENTI, index=False)
                st.success(f"✅ {scelta_uff} registrato!")
                st.rerun()
            elif scelta_uff in df_uff['GIOCATORE'].values:
                st.warning("Giocatore già registrato.")

    with c2:
        st.markdown("### 🧪 SIMULATORE PROBABILI")
        st.session_state.simulati = st.multiselect("Simula cessione per (non salva):", sorted(f_rs['Nome'].unique()) if f_rs is not None else [], default=st.session_state.simulati)

    st.markdown("---")
    st.markdown("### 📋 STORICO CESSIONI UFFICIALI (Salvate)")
    if not df_uff.empty:
        st.dataframe(df_uff.style.format({"RIMBORSO": "{:g}"}), use_container_width=True, hide_index=True)
        if st.button("🗑️ SVUOTA TUTTO IL DATABASE"):
            if os.path.exists(FILE_PARTENTI): os.remove(FILE_PARTENTI)
            st.rerun()
    else:
        st.write("Nessuna cessione registrata.")

# --- TAB 1: BUDGET ---
with t[1]:
    if f_rs is not None:
        st.subheader("💰 **BUDGET AGGIORNATO (Uff + Sim)**")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI DISPONIBILI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO CESSIONI'] = bu['Squadra_N'].map(rimborsi_totali_per_budget).fillna(0)
        
        voci = ['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISPONIBILI', 'RECUPERO CESSIONI']
        bu['PATRIMONIO TOTALE'] = bu[voci].sum(axis=1)
        
        st.dataframe(bu.sort_values("PATRIMONIO TOTALE", ascending=False).style\
            .background_gradient(cmap='YlOrRd', subset=['PATRIMONIO TOTALE'])\
            .format({c: "{:g}" for c in bu.columns if c != 'Squadra_N'})\
            .set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)

# --- ALTRE TAB (LOGICA GOLDEN) ---
with t[0]: # CLASSIFICHE
    c_p1, c_p2 = st.columns(2)
    if f_pt is not None:
        with c_p1: 
            f_pt['Punti Totali'] = pd.to_numeric(f_pt['Punti Totali'], errors='coerce').fillna(0)
            st.subheader("🎯 PUNTI"); st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali']].sort_values('Posizione').style.format({"Punti Totali":"{:g}"}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c_p2: 
            f_sc['Punti'] = pd.to_numeric(f_sc['Punti'], errors='coerce').fillna(0)
            st.subheader("⚔️ SCONTRI"); st.dataframe(f_sc[['Posizione','Giocatore','Punti']].sort_values('Posizione').style.format({"Punti":"{:g}"}), hide_index=True, use_container_width=True)

with t[2]: # ROSE
    if f_rs is not None:
        sq_sel = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="r_sel")
        df_sq = f_rs[f_rs['Squadra_N'] == sq_sel][['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']]
        st.dataframe(df_sq.style.format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 VINCOLI"); st.dataframe(f_vn[['Squadra', 'Giocatore', 'Tot_Vincolo']].sort_values('Tot_Vincolo', ascending=False).style.format({"Tot_Vincolo":"{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI
    st.subheader("🔄 SIMULATORE SCAMBI"); c_s1, c_s2 = st.columns(2)
    if f_rs is not None:
        with c_s1: s_a = st.selectbox("SQ A", sorted(f_rs['Squadra_N'].unique()), key="s_a"); g_a = st.multiselect("DA A", f_rs[f_rs['Squadra_N']==s_a]['Nome'].tolist())
        with c_s2: s_b = st.selectbox("SQ B", sorted([s for s in f_rs['Squadra_N'].unique() if s != s_a]), key="s_b"); g_b = st.multiselect("DA B", f_rs[f_rs['Squadra_N']==s_b]['Nome'].tolist())

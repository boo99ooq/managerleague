import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid; }
    .card-blue { background-color: #e3f2fd; border-color: #1a73e8; }
    .card-red { background-color: #fbe9e7; border-color: #d32f2f; }
    .card-grey { background-color: #f1f3f4; border-color: #9e9e9e; }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; text-align: center; }
    .error-box { background-color: #fff3f3; padding: 15px; border-radius: 10px; border: 1px solid #ff4b4b; color: #ff4b4b; }
</style>
""", unsafe_allow_html=True)

# --- SUPER MAPPING NOMI (V5) ---
def clean_quotazioni_name(name):
    if not isinstance(name, str): return name
    # Correzione caratteri speciali CSV
    name = name.replace('č', 'E').replace('ň', 'O').replace('ř', 'I').replace('ć', 'C').replace('Č', 'E').replace('Ň', 'O').replace('ň', 'o')
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    name = name.upper().strip()
    
    # Dizionario correzioni manuali per la tua Lega
    mapping = {
        'MARTINEZ JO.': 'MARTINEZ JO', 'MILINKOVIC-SAVIC V.': 'MILINKOVIC SAVIC', 'N\'DICKA': 'NDICKA',
        'TAVARES N.': 'NUNO TAVARES', 'OSTIGARD': 'OSTIGAARD', 'PEZZELLA GIU.': 'PEZZELLA',
        'RODRIGUEZ J.': 'RODRIGUEZ J', 'DIMARCO': 'DIMARCO', 'CARLOS AUGUSTO': 'CARLOS AUGU',
        'KOSSOUNOU': 'KOSSOUNOU', 'THURAM K.': 'K THURAM', 'KONE M.': 'KONE', 'KONE M. (S)': 'KONE',
        'KAMARA': 'KAMAA', 'PELLEGRINI LO.': 'PELLEGRINI LORENZO', 'THORSTVEDT': 'THORSVEDT',
        'BERNABE': 'BERNABE', 'NORTON-CUFFY': 'NORTON CUFFY', 'NICOLUSSI CAVIGLIA': 'NICOLUSSI CAVIGLIA',
        'DELE-BASHIRU': 'DELE BASHIRU', 'AKINSANMIRO': 'NDRI AKINSAMIRO', 'LOFTUS-CHEEK': 'LOFTUS CHEEK',
        'MKHITARYAN': 'MKHTARYAN', 'SULEMANA I.': 'K SULEMANA', 'SULEMANA K.': 'K SULEMANA',
        'SOULE': 'SOULE K', 'DAVIS K.': 'DAVIS', 'DOUVIKAS': 'DOUVIKAS', 'SAELEMAEKERS': 'SAELEMAKERS',
        'ESPOSITO F.P.': 'PIO ESPOSITO', 'ESPOSITO SE.': 'ESPOSITO', 'MARTINELLI': 'MARTINELLI',
        'GABRIEL': 'GABRIEL', 'ZAMBO ANGUISSA': 'ANGUISSA', 'THURAM M.': 'THURAM M', 'MARTINEZ L.': 'LAUTARO',
        'MCTOMINAY': 'MCTOMINAY', 'KAMA': 'KAMAA'
    }
    if name in mapping: return mapping[name]
    # Rimuove iniziali (es: LUKAKU R. -> LUKAKU)
    name = re.sub(r'\s[A-Z]\.$', '', name)
    name = re.sub(r'\s[A-Z]\.[A-Z]\.$', '', name)
    return name

# --- FUNZIONI CARICAMENTO ---
def ld(f, is_quot=False):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True, encoding='latin1')
        df.columns = [c.strip() for c in df.columns]
        if is_quot:
            df['Nome'] = df['Nome'].apply(clean_quotazioni_name)
            return df[['Nome', 'Qt.A']].rename(columns={'Qt.A': 'Quotazione'})
        return df.dropna(how='all')
    except: return None

def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip().upper()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None
    return s_str

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

# CARICAMENTO DATI
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Nome'] = f_rs['Nome'].apply(clean_string)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None:
        # Teniamo traccia di chi ha matchato e chi no
        f_rs = pd.merge(f_rs, f_qt, on='Nome', how='left')
        f_rs['Quotazione'] = f_rs['Quotazione'].fillna(0)

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_string)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 **RICERCA**")
    if f_rs is not None:
        scelte = st.multiselect("**GIOCATORE**", sorted(f_rs['Nome'].unique()))
        for n in scelte:
            dr = f_rs[f_rs['Nome'] == n].iloc[0]
            qt_v = dr['Quotazione'] if 'Quotazione' in dr else 0
            st.markdown(f'<div class="player-card card-grey"><b>{n}</b> ({dr["Squadra_N"]})<br>VAL: <b>{int(dr["Prezzo_N"])}</b> | QUOT: <b style="color:#1a73e8;">{int(qt_v)}</b></div>', unsafe_allow_html=True)

# --- MAIN APP ---
st.title("⚽ **MUYFANTAMANAGER GOLDEN V5**")
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 **PUNTI**")
            f_pt['P_N'], f_pt['FM'] = f_pt['Punti Totali'].apply(to_num), f_pt['Media'].apply(to_num)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N','FM']].sort_values('Posizione').style.background_gradient(subset=['P_N', 'FM'], cmap='YlGn'), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ **SCONTRI**")
            f_sc['P_S'] = f_sc['Punti'].apply(to_num)
            f_sc['DR'] = f_sc['Gol Fatti'].apply(to_num) - f_sc['Gol Subiti'].apply(to_num)
            st.dataframe(f_sc[['Posizione','Giocatore','P_S','DR']].style.background_gradient(subset=['P_S'], cmap='Blues').background_gradient(subset=['DR'], cmap='RdYlGn'), hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'ROSE'})
        v_s = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_s, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1)
        bu['DISP'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['TOT'] = bu['ROSE'] + bu['Tot_Vincolo'] + bu['DISP']
        st.dataframe(bu.sort_values("TOT", ascending=False).style.background_gradient(cmap='YlOrRd', subset=['TOT']).background_gradient(cmap='Greens', subset=['DISP']), hide_index=True, use_container_width=True)

with t[2]: # ROSE E LISTA MANCANTI
    if f_rs is not None:
        # --- PANNELLO ERRORI MATCHING ---
        mancanti = f_rs[f_rs['Quotazione'] == 0]['Nome'].tolist()
        if mancanti:
            with st.expander(f"⚠️ ATTENZIONE: {len(mancanti)} GIOCATORI SENZA QUOTAZIONE"):
                st.write("Questi nomi nelle rose non corrispondono a quelli del file quotazioni:")
                st.write(", ".join(sorted(mancanti)))
        
        sq = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="rs")
        cols = ['Ruolo', 'Nome', 'Prezzo_N']
        if 'Quotazione' in f_rs.columns: cols.append('Quotazione')
        st.dataframe(f_rs[f_rs['Squadra_N'] == sq][cols], hide_index=True, use_container_width=True)

with t[3]: # VINCOLI
    if f_vn is not None:
        sq_v = st.selectbox("**SQUADRA**", ["TUTTE"] + sorted(f_vn['Sq_N'].unique()), key="vs")
        df_v = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        st.dataframe(df_v[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI
    st.subheader("🔄 **SCAMBI**")
    c1, c2 = st.columns(2)
    l_sq = sorted(f_rs['Squadra_N'].unique())
    with c1:
        sa = st.selectbox("**SQUADRA A**", l_sq, key="sa")
        ga = st.multiselect("**ESCE DA A**", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist())
    with c2:
        sb = st.selectbox("**SQUADRA B**", [s for s in l_sq if s != sa], key="sb")
        gb = st.multiselect("**ESCE DA B**", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist())
    if ga and gb:
        def get_v(n):
            p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]
            v = f_vn[f_vn['Giocatore']==n]['Tot_Vincolo'].iloc[0] if (f_vn is not None and n in f_vn['Giocatore'].values) else 0
            return p + v, v
        tot_a = sum(get_v(n)[0] for n in ga); tot_b = sum(get_v(n)[0] for n in gb)
        nuovo = round((tot_a + tot_b) / 2)
        st.metric(f"Valore Scambio", f"{int(tot_a)} vs {int(tot_b)}")
        p_a = f_rs[f_rs['Squadra_N']==sa]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sa]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sa, 0)
        st.markdown(f'<div class="patrimonio-box">NUOVO PATRIMONIO {sa}: <b>{int(p_a + (nuovo - tot_a))}</b></div>', unsafe_allow_html=True)

with t[5]: # TAGLI
    st.subheader("✂️ **TAGLI**")
    sq_t = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="st")
    gi_t = st.selectbox("**GIOCATORE**", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist())
    if gi_t:
        v_p = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gi_t)]['Prezzo_N'].iloc[0]
        v_v = f_vn[f_vn['Giocatore'] == gi_t]['Tot_Vincolo'].iloc[0] if (f_vn is not None and gi_t in f_vn['Giocatore'].values) else 0
        st.markdown(f'<div class="cut-box">RIMBORSO: <b>{round((v_p + v_v) * 0.6)}</b></div>', unsafe_allow_html=True)

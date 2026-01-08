import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# CSS PER GRASSETTO ESTREMO E CONTRASTO AUTOMATICO
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid; }
    .card-blue { background-color: #e3f2fd; border-color: #1a73e8; }
    .card-red { background-color: #fbe9e7; border-color: #d32f2f; }
    .card-grey { background-color: #f1f3f4; border-color: #9e9e9e; }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; text-align: center; }
    .cut-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; color: #1a1a1a; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONE MAPPING AVANZATA (V4) ---
def clean_quotazioni_name(name):
    if not isinstance(name, str): return name
    # Correzione caratteri speciali CSV
    name = name.replace('č', 'E').replace('ň', 'O').replace('ř', 'I').replace('ć', 'C').replace('Č', 'E').replace('Ň', 'O').replace('ň', 'O')
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
        'GABRIEL': 'GABRIEL', 'ZAMBO ANGUISSA': 'ANGUISSA', 'THURAM M.': 'THURAM M', 'MARTINEZ L.': 'LAUTARO'
    }
    if name in mapping: return mapping[name]
    name = re.sub(r'\s[A-Z]\.$', '', name)
    name = re.sub(r'\s[A-Z]\.[A-Z]\.$', '', name)
    return name

# --- FUNZIONI DI CARICAMENTO ---
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
    s_str = str(s).strip()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None
    return s_str.upper()

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
        f_rs = pd.merge(f_rs, f_qt, on='Nome', how='left').fillna({'Quotazione': 0})

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
st.title("⚽ **MUYFANTAMANAGER GOLDEN V4**")
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 **CLASSIFICA PUNTI**")
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            f_pt['FM'] = f_pt['Media'].apply(to_num)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N','FM']].sort_values('Posizione').style\
                .background_gradient(subset=['P_N', 'FM'], cmap='YlGn').format({"P_N": "{:g}", "FM": "{:.2f}"})\
                .set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ **SCONTRI DIRETTI**")
            f_sc['P_S'] = f_sc['Punti'].apply(to_num)
            f_sc['GF'] = f_sc['Gol Fatti'].apply(to_num)
            f_sc['GS'] = f_sc['Gol Subiti'].apply(to_num)
            f_sc['DR'] = f_sc['GF'] - f_sc['GS']
            st.dataframe(f_sc[['Posizione','Giocatore','P_S','GF','GS','DR']].style\
                .background_gradient(subset=['P_S'], cmap='Blues').background_gradient(subset=['DR'], cmap='RdYlGn')\
                .format({"P_S": "{:g}", "GF": "{:g}", "GS": "{:g}", "DR": "{:+g}"})\
                .set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        st.subheader("💰 **BUDGET E PATRIMONIO**")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI DISPONIBILI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['PATRIMONIO TOTALE'] = bu['SPESA ROSE'] + bu['SPESA VINCOLI'] + bu['CREDITI DISPONIBILI']
        st.bar_chart(bu.set_index("Squadra_N")[['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISPONIBILI']], color=["#1a73e8", "#9c27b0", "#ff9800"])
        st.dataframe(bu.sort_values("PATRIMONIO TOTALE", ascending=False).style\
            .background_gradient(cmap='YlOrRd', subset=['PATRIMONIO TOTALE']).background_gradient(cmap='Greens', subset=['CREDITI DISPONIBILI'])\
            .format({c: "{:g}" for c in bu.columns if c != 'Squadra_N'})\
            .set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)

with t[2]: # ROSE
    if f_rs is not None:
        sq = st.selectbox("**SELEZIONA SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="rose_sel")
        cols_r = ['Ruolo', 'Nome', 'Prezzo_N']
        if 'Quotazione' in f_rs.columns: cols_r.append('Quotazione')
        df_sq = f_rs[f_rs['Squadra_N'] == sq][cols_r]
        def color_ruoli(row):
            r = str(row['Ruolo']).upper()
            if 'POR' in r: bg = '#FCE4EC' 
            elif 'DIF' in r: bg = '#E8F5E9' 
            elif 'CEN' in r: bg = '#E3F2FD' 
            elif 'ATT' in r: bg = '#FFFDE7' 
            else: bg = '#FFFFFF'
            return [f'background-color: {bg}; color: black; font-weight: 900;'] * len(row)
        st.dataframe(df_sq.style.apply(color_ruoli, axis=1).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 **VINCOLI ATTIVI**")
        sq_v = st.selectbox("**FILTRA SQUADRA**", ["TUTTE"] + sorted([s for s in f_vn['Sq_N'].unique() if s]), key="vinc_sel")
        df_v_display = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        st.dataframe(df_v_display[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False).style\
            .background_gradient(subset=['Tot_Vincolo'], cmap='Purples').format({"Tot_Vincolo": "{:g}"})\
            .set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI
    st.subheader("🔄 **SIMULATORE SCAMBI**")
    c1, c2 = st.columns(2)
    lista_n_sq = sorted([s for s in f_rs['Squadra_N'].unique() if s])
    with c1:
        sa = st.selectbox("**SQUADRA A**", lista_n_sq, key="sa_f")
        ga = st.multiselect("**ESCONO DA A**", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist(), key="ga_f")
    with c2:
        sb = st.selectbox("**SQUADRA B**", [s for s in lista_n_sq if s != sa], key="sb_f")
        gb = st.multiselect("**ESCONO DA B**", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist(), key="gb_f")
    if ga and gb:
        def get_i(n):
            p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0] if n in f_rs['Nome'].values else 0
            v = f_vn[f_vn['Giocatore']==n]['Tot_Vincolo'].iloc[0] if (f_vn is not None and n in f_vn['Giocatore'].values) else 0
            return {'t': p + v, 'v': v}
        dict_a = {n: get_i(n) for n in ga}; dict_b = {n: get_i(n) for n in gb}
        tot_ante_a, tot_ante_b = sum(d['t'] for d in dict_a.values()), sum(d['t'] for d in dict_b.values())
        nuovo_tot = round((tot_ante_a + tot_ante_b) / 2)
        st.divider()
        m1, m2 = st.columns(2)
        m1.metric(f"Valore ceduto da {sa}", f"{int(tot_ante_a)}"); m2.metric(f"Valore ceduto da {sb}", f"{int(tot_ante_b)}")
        res_a, res_b = st.columns(2)
        with res_a:
            for n, info in dict_b.items():
                peso = info['t']/tot_ante_b if tot_ante_b > 0 else 1/len(gb); nuovo_t = round(peso*nuovo_tot)
                st.markdown(f"""<div class="player-card card-blue"><b>{n}</b><br><small>VAL PRE: {int(info['t'])}</small><br>NUOVA VAL: <b>{max(0, nuovo_t-int(info['v']))}</b> + VINC: <b>{int(info['v'])}</b></div>""", unsafe_allow_html=True)
        with res_b:
            for n, info in dict_a.items():
                peso = info['t']/tot_ante_a if tot_ante_a > 0 else 1/len(ga); nuovo_t = round(peso*nuovo_tot)
                st.markdown(f"""<div class="player-card card-red"><b>{n}</b><br><small>VAL PRE: {int(info['t'])}</small><br>NUOVA VAL: <b>{max(0, nuovo_t-int(info['v']))}</b> + VINC: <b>{int(info['v'])}</b></div>""", unsafe_allow_html=True)
        st.divider()
        p_a_v = f_rs[f_rs['Squadra_N']==sa]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sa]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sa, 0)
        p_b_v = f_rs[f_rs['Squadra_N']==sb]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sb]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sb, 0)
        diff = nuovo_tot - tot_ante_a
        col_p1, col_p2 = st.columns(2)
        col_p1.markdown(f"""<div class="patrimonio-box">NUOVO PATRIMONIO {sa}<br><h2>{int(p_a_v + diff)}</h2><small>PRIMA: {int(p_a_v)}</small></div>""", unsafe_allow_html=True)
        col_p2.markdown(f"""<div class="patrimonio-box">NUOVO PATRIMONIO {sb}<br><h2>{int(p_b_v - diff)}</h2><small>PRIMA: {int(p_b_v)}</small></div>""", unsafe_allow_html=True)

with t[5]: # TAGLI
    st.subheader("✂️ **SIMULATORE TAGLI**")
    sq_t = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="sq_tag")
    gioc_t = st.selectbox("**GIOCATORE**", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist(), key="gioc_tag")
    if gioc_t:
        v_p = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gioc_t)]['Prezzo_N'].iloc[0]
        v_v = f_vn[f_vn['Giocatore'] == gioc_t]['Tot_Vincolo'].iloc[0] if (f_vn is not None and gioc_t in f_vn['Giocatore'].values) else 0
        rimborso = round((v_p + v_v) * 0.6)
        st.markdown(f"""<div class="cut-box"><h3>💰 **RIMBORSO: {rimborso} CREDITI**</h3>VALUTAZIONE: <b>{int(v_p)}</b> | VINC: <b>{int(v_v)}</b></div>""", unsafe_allow_html=True)

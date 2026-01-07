import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# CSS PER GRASSETTO SU TUTTO TRANNE LE TABELLE (Gestite dopo)
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * {
        font-weight: bold !important;
    }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid; }
    .card-blue { background-color: #e3f2fd; border-color: #1a73e8; }
    .card-red { background-color: #fbe9e7; border-color: #d32f2f; }
    .card-grey { background-color: #f1f3f4; border-color: #9e9e9e; }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI PULIZIA ---
def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None
    return s_str.upper()

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True)
        if df.columns[0].startswith('Unnamed') or df.empty:
            df = pd.read_csv(f, skiprows=1, engine='python')
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# --- CARICAMENTO ---
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- STILE GRASSETTO PER DATAFRAME ---
def apply_bold(val):
    return 'font-weight: 900; color: black;'

# --- ELABORAZIONE ---
if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Nome'] = f_rs['Nome'].apply(clean_string)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_string)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- MAIN ---
st.title("⚽ MUYFANTAMANAGER")
t = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI", "✂️ TAGLI"])

with t[0]: # CLASSIFICHE RESTAURATE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 CLASSIFICA PUNTI")
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            f_pt['FM'] = f_pt['Media'].apply(to_num)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N','FM']].sort_values('Posizione').style\
                .background_gradient(subset=['P_N', 'FM'], cmap='YlGn')\
                .applymap(apply_bold)\
                .format({"P_N": "{:g}", "FM": "{:.2f}"}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ SCONTRI DIRETTI")
            f_sc['P_S'] = f_sc['Punti'].apply(to_num)
            st.dataframe(f_sc[['Posizione','Giocatore','P_S','Gol Fatti','Gol Subiti']].style\
                .background_gradient(subset=['P_S'], cmap='Blues')\
                .applymap(apply_bold)\
                .format({"P_S": "{:g}"}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET RESTAURATO
    if f_rs is not None:
        st.subheader("💰 BUDGET E PATRIMONIO")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['EXTRA'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['TOTALE'] = bu['SPESA ROSE'] + bu['SPESA VINCOLI'] + bu['EXTRA']
        st.bar_chart(bu.set_index("Squadra_N")[['SPESA ROSE', 'SPESA VINCOLI', 'EXTRA']], color=["#1a73e8", "#9c27b0", "#ff9800"])
        st.dataframe(bu.sort_values("TOTALE", ascending=False).style\
            .background_gradient(cmap='YlOrRd', subset=['TOTALE'])\
            .applymap(apply_bold)\
            .format({c: "{:g}" for c in bu.columns if c != 'Squadra_N'}), hide_index=True, use_container_width=True)

with t[2]: # ROSE RESTAURATE
    if f_rs is not None:
        sq = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="r_s")
        df_sq = f_rs[f_rs['Squadra_N'] == sq][['Ruolo', 'Nome', 'Prezzo_N']]
        st.dataframe(df_sq.style.applymap(apply_bold).format({"Prezzo_N":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # VINCOLI RESTAURATI
    if f_vn is not None:
        st.subheader("📅 DETTAGLIO VINCOLI")
        sq_v = st.selectbox("FILTRA", ["TUTTE"] + sorted([s for s in f_vn['Sq_N'].unique() if s]), key="v_s")
        df_v = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        st.dataframe(df_v[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].style\
            .background_gradient(subset=['Tot_Vincolo'], cmap='Purples')\
            .applymap(apply_bold)\
            .format({"Tot_Vincolo": "{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI (LOGICA PATRIMONIO)
    st.subheader("🔄 SIMULATORE SCAMBI")
    c1, c2 = st.columns(2)
    lista_n_sq = sorted([s for s in f_rs['Squadra_N'].unique() if s])
    with c1:
        sa = st.selectbox("SQUADRA A", lista_n_sq, key="sa")
        ga = st.multiselect("ESCONO DA A", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist(), key="ga")
    with c2:
        sb = st.selectbox("SQUADRA B", [s for s in lista_n_sq if s != sa], key="sb")
        gb = st.multiselect("ESCONO DA B", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist(), key="gb")
    
    if ga and gb:
        def get_info(nome):
            p = f_rs[f_rs['Nome']==nome]['Prezzo_N'].iloc[0] if nome in f_rs['Nome'].values else 0
            v = f_vn[f_vn['Giocatore']==nome]['Tot_Vincolo'].iloc[0] if (f_vn is not None and nome in f_vn['Giocatore'].values) else 0
            return {'p': p, 'v': v, 't': p + v}
        dict_a = {n: get_info(n) for n in ga}; dict_b = {n: get_info(n) for n in gb}
        tot_ante_a, tot_ante_b = sum(d['t'] for d in dict_a.values()), sum(d['t'] for d in dict_b.values())
        nuovo_tot = round((tot_ante_a + tot_ante_b) / 2)
        
        # PATRIMONIO REAL TIME
        p_a_v = f_rs[f_rs['Squadra_N']==sa]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sa]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sa, 0)
        p_b_v = f_rs[f_rs['Squadra_N']==sb]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sb]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sb, 0)
        diff = nuovo_tot - tot_ante_a
        
        st.divider()
        col_p1, col_p2 = st.columns(2)
        col_p1.markdown(f"""<div class="patrimonio-box">NUOVO PATRIMONIO {sa}<br><h2>{int(p_a_v + diff)}</h2><small>PRIMA: {int(p_a_v)}</small></div>""", unsafe_allow_html=True)
        col_p2.markdown(f"""<div class="patrimonio-box">NUOVO PATRIMONIO {sb}<br><h2>{int(p_b_v - diff)}</h2><small>PRIMA: {int(p_b_v)}</small></div>""", unsafe_allow_html=True)
        st.divider()

        res_a, res_b = st.columns(2)
        with res_a:
            for n, info in dict_b.items():
                peso = info['t']/tot_ante_b if tot_ante_b > 0 else 1/len(gb); nuovo_t = round(peso*nuovo_tot)
                st.markdown(f"""<div class="player-card card-blue">{n}<br>VALUTAZIONE: {max(0, nuovo_t-int(info['v']))} + VINC: {int(info['v'])}</div>""", unsafe_allow_html=True)
        with res_b:
            for n, info in dict_a.items():
                peso = info['t']/tot_ante_a if tot_ante_a > 0 else 1/len(ga); nuovo_t = round(peso*nuovo_tot)
                st.markdown(f"""<div class="player-card card-red">{n}<br>VALUTAZIONE: {max(0, nuovo_t-int(info['v']))} + VINC: {int(info['v'])}</div>""", unsafe_allow_html=True)

with t[5]: # TAGLI
    st.subheader("✂️ SIMULATORE TAGLI")
    sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="s_t")
    gioc_t = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist(), key="g_t")
    if gioc_t:
        v_p = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gioc_t)]['Prezzo_N'].iloc[0]
        v_v = f_vn[f_vn['Giocatore'] == gioc_t]['Tot_Vincolo'].iloc[0] if (f_vn is not None and gioc_t in f_vn['Giocatore'].values) else 0
        rimborso = round((v_p + v_v) * 0.6)
        st.markdown(f"""<div class="cut-box"><h3>💰 RIMBORSO: {rimborso} CREDITI</h3>VALUTAZIONE: {int(v_p)} | VINCOLI: {int(v_v)}</div>""", unsafe_allow_html=True)

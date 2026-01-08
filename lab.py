import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# CSS ORIGINALE (Grassetto estremo, card e box personalizzati)
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .player-card { padding: 12px; border-radius: 10px; margin-bottom: 12px; border: 3px solid #333; box-shadow: 4px 4px 8px rgba(0,0,0,0.2); color: black; }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 3px solid #1a73e8; text-align: center; border: 3px solid #1a73e8; }
    .cut-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 3px solid #ff4b4b; color: #1a1a1a; box-shadow: 4px 4px 8px rgba(0,0,0,0.1); }
    .zero-tool { background-color: #ffebee; color: #c62828; padding: 15px; border-radius: 10px; border: 2px solid #c62828; margin-bottom: 20px; }
    .stat-label { font-size: 0.8em; color: #555; font-weight: 400 !important; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO ---
def super_clean_match(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items():
        name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    mapping = {'ZAMBO ANGUISSA': 'ANGUISSA', 'MARTINEZ L.': 'LAUTARO', 'PAZ N.': 'NICO PAZ'}
    if name in mapping: return mapping[name]
    return re.sub(r'\s[A-Z]\.$', '', name)

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None
    return s_str.upper()

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

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- ELABORAZIONE ---
if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean_match)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_match)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 **RICERCA GIOCATORE**")
    if f_rs is not None:
        scelte = st.multiselect("**CERCA NELLA LEGA**", sorted(f_rs['Nome'].unique()))
        for n in scelte:
            dr = f_rs[f_rs['Nome'] == n].iloc[0]
            v_match = f_vn[f_vn['Giocatore_Match'] == super_clean_match(n)] if f_vn is not None else pd.DataFrame()
            vv = v_match['Tot_Vincolo'].iloc[0] if not v_match.empty else 0
            r = str(dr['Ruolo']).upper()
            bg_side = '#FCE4EC' if 'POR' in r or r == 'P' else '#E8F5E9' if 'DIF' in r or r == 'D' else '#E3F2FD' if 'CEN' in r or r == 'C' else '#FFFDE7' if 'ATT' in r or r == 'A' else '#f1f3f4'
            st.markdown(f'''<div class="player-card" style="background-color: {bg_side};"><b>{n}</b> (<b>{dr['Squadra_N']}</b>)<br>ASTA: <b>{int(dr['Prezzo_N'])}</b> | VINC: <b>{int(vv)}</b><br>QUOT: <b style="color:#1a73e8;">{int(dr['Quotazione'])}</b> | TOT: <b>{int(dr['Prezzo_N'] + vv)}</b></div>''', unsafe_allow_html=True)

# --- MAIN APP ---
st.title("⚽ **MUYFANTAMANAGER GOLDEN V3.2**")
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 **CLASSIFICA PUNTI**")
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            f_pt['FM'] = f_pt['Media'].apply(to_num)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N','FM']].sort_values('Posizione').style.background_gradient(subset=['P_N', 'FM'], cmap='YlGn').format({"P_N": "{:g}", "FM": "{:g}"}).set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ **SCONTRI DIRETTI**")
            f_sc['P_S'] = f_sc['Punti'].apply(to_num)
            f_sc['GF'] = f_sc['Gol Fatti'].apply(to_num); f_sc['GS'] = f_sc['Gol Subiti'].apply(to_num)
            f_sc['DR'] = f_sc['GF'] - f_sc['GS']
            st.dataframe(f_sc[['Posizione','Giocatore','P_S','GF','GS', 'DR']].style.background_gradient(subset=['P_S'], cmap='Blues').format({"P_S": "{:g}", "GF": "{:g}", "GS": "{:g}", "DR": "{:g}"}).set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        st.subheader("💰 **BUDGET E PATRIMONIO**")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI DISPONIBILI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['PATRIMONIO TOTALE'] = bu['SPESA ROSE'] + bu['SPESA VINCOLI'] + bu['CREDITI DISPONIBILI']
        st.bar_chart(bu.set_index("Squadra_N")[['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISPONIBILI']], color=["#1a73e8", "#9c27b0", "#ff9800"])
        st.dataframe(bu.sort_values("PATRIMONIO TOTALE", ascending=False).style.background_gradient(cmap='YlOrRd', subset=['PATRIMONIO TOTALE']).format({c: "{:g}" for c in bu.columns if c != 'Squadra_N'}).set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)

with t[2]: # ROSE
    if f_rs is not None:
        sq = st.selectbox("**SELEZIONA SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="rose_sel")
        df_sq = f_rs[f_rs['Squadra_N'] == sq][['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']]
        st.dataframe(df_sq.style.apply(lambda row: ['background-color: ' + ('#FCE4EC' if 'POR' in str(row.Ruolo).upper() else '#E8F5E9' if 'DIF' in str(row.Ruolo).upper() else '#E3F2FD' if 'CEN' in str(row.Ruolo).upper() else '#FFFDE7' if 'ATT' in str(row.Ruolo).upper() else '#FFFFFF') + '; color: black; font-weight: 900;'] * len(row), axis=1).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI
    st.subheader("🔄 **SIMULATORE SCAMBI GOLDEN**")
    if f_rs is not None:
        c1, c2 = st.columns(2); lista_sq = sorted([s for s in f_rs['Squadra_N'].unique() if s])
        with c1: sa = st.selectbox("**SQUADRA A**", lista_sq, key="sa_f"); ga = st.multiselect("**ESCONO DA A**", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist(), key="ga_f")
        with c2: sb = st.selectbox("**SQUADRA B**", [s for s in lista_sq if s != sa], key="sb_f"); gb = st.multiselect("**ESCONO DA B**", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist(), key="gb_f")
        
        if ga and gb:
            def get_i(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0] if n in f_rs['Nome'].values else 0
                v_row = f_vn[f_vn['Giocatore_Match']==super_clean_match(n)] if f_vn is not None else pd.DataFrame()
                v = v_row['Tot_Vincolo'].iloc[0] if not v_row.empty else 0
                return {'t': p + v, 'p': p, 'v': v}
            
            p_a_v = f_rs[f_rs['Squadra_N']==sa]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sa]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sa, 0)
            p_b_v = f_rs[f_rs['Squadra_N']==sb]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sb]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sb, 0)
            
            dict_a = {n: get_i(n) for n in ga}; dict_b = {n: get_i(n) for n in gb}
            tot_a, tot_b = sum(d['t'] for d in dict_a.values()), sum(d['t'] for d in dict_b.values())
            nuovo_tot = round((tot_a + tot_b) / 2)
            
            st.divider(); m1, m2 = st.columns(2)
            m1.metric(f"Valore ceduto da {sa}", f"{int(tot_a)}"); m2.metric(f"Valore ceduto da {sb}", f"{int(tot_b)}")
            
            res_a, res_b = st.columns(2)
            with res_a:
                st.write(f"👉 **Ricevuti da {sa}**")
                for n, info in dict_b.items():
                    peso = info['t']/tot_b if tot_b > 0 else 1/len(gb); nuovo_t = round(peso*nuovo_tot)
                    incidenza = (info['t']/p_b_v)*100 if p_b_v > 0 else 0
                    st.markdown(f'''<div class="player-card" style="background-color: #e3f2fd; border: 2px solid #1e88e5;">
                        <b>{n}</b><br>
                        <span class="stat-label">NUOVA VAL:</span> <b>{max(0, nuovo_t-int(info['v']))}</b> <span class="stat-label">+ VINC:</span> <b>{int(info['v'])}</b><br>
                        <hr style="margin:5px 0; border:0; border-top:1px solid #1e88e5;">
                        <span class="stat-label">QP PATRIMONIO:</span> <b>{incidenza:.1f}%</b> | <span class="stat-label">VAL ANTE:</span> <b>{int(info['t'])}</b>
                    </div>''', unsafe_allow_html=True)
            with res_b:
                st.write(f"👉 **Ricevuti da {sb}**")
                for n, info in dict_a.items():
                    peso = info['t']/tot_a if tot_a > 0 else 1/len(ga); nuovo_t = round(peso*nuovo_tot)
                    incidenza = (info['t']/p_a_v)*100 if p_a_v > 0 else 0
                    st.markdown(f'''<div class="player-card" style="background-color: #fbe9e7; border: 2px solid #e53935;">
                        <b>{n}</b><br>
                        <span class="stat-label">NUOVA VAL:</span> <b>{max(0, nuovo_t-int(info['v']))}</b> <span class="stat-label">+ VINC:</span> <b>{int(info['v'])}</b><br>
                        <hr style="margin:5px 0; border:0; border-top:1px solid #e53935;">
                        <span class="stat-label">QP PATRIMONIO:</span> <b>{incidenza:.1f}%</b> | <span class="stat-label">VAL ANTE:</span> <b>{int(info['t'])}</b>
                    </div>''', unsafe_allow_html=True)
            
            diff = nuovo_tot - tot_a; col_p1, col_p2 = st.columns(2)
            col_p1.markdown(f'''<div class="patrimonio-box">NUOVO PATRIMONIO {sa}<br><h2>{int(p_a_v + diff)}</h2><small>PRIMA: {int(p_a_v)} | VAR: {int(diff):+d}</small></div>''', unsafe_allow_html=True)
            col_p2.markdown(f'''<div class="patrimonio-box">NUOVO PATRIMONIO {sb}<br><h2>{int(p_b_v - diff)}</h2><small>PRIMA: {int(p_b_v)} | VAR: {int(-diff):+d}</small></div>''', unsafe_allow_html=True)

with t[5]: # TAGLI
    st.subheader("✂️ **SIMULATORE TAGLI GOLDEN**")
    sq_t = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="sq_tag")
    gioc_t = st.selectbox("**GIOCATORE**", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist(), key="gioc_tag")
    if gioc_t:
        p_t_v = f_rs[f_rs['Squadra_N']==sq_t]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sq_t]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sq_t, 0)
        v_p = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gioc_t)]['Prezzo_N'].iloc[0]
        v_match = f_vn[f_vn['Giocatore_Match'] == super_clean_match(gioc_t)] if f_vn is not None else pd.DataFrame()
        v_v = v_match['Tot_Vincolo'].iloc[0] if not v_match.empty else 0
        tot_gioc = v_p + v_v
        rimborso = round(tot_gioc * 0.6)
        incidenza = (tot_gioc / p_t_v) * 100 if p_t_v > 0 else 0
        
        st.markdown(f'''<div class="cut-box">
            <h3>💰 **RIMBORSO: {rimborso} CREDITI**</h3>
            <hr>
            VALORE TOTALE: <b>{int(tot_gioc)}</b> <small>(ASTA: {int(v_p)} | VINC: {int(v_v)})</small><br>
            INCIDENZA PATRIMONIO: <b>{incidenza:.2f}%</b><br>
            <small style="color: #555;">Recupero calcolato al 60% del valore attuale (Asta + Vincoli)</small>
        </div>''', unsafe_allow_html=True)

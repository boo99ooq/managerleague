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
    .punto-incontro { background-color: #fff3e0; padding: 15px; border-radius: 10px; border: 3px solid #ff9800; text-align: center; margin: 10px 0; }
    .cut-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 3px solid #ff4b4b; color: #1a1a1a; box-shadow: 4px 4px 8px rgba(0,0,0,0.1); }
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
    return mapping.get(name, re.sub(r'\s[A-Z]\.$', '', name))

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
FILE_DB = "mercatone_gennaio.csv"

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
            st.markdown(f'''<div class="player-card" style="background-color: {bg_side}; border: 3px solid #333;"><b>{n}</b> (<b>{dr['Squadra_N']}</b>)<br>ASTA: <b>{int(dr['Prezzo_N'])}</b> | VINC: <b>{int(vv)}</b><br>QUOT: <b style="color:#1a73e8;">{int(dr['Quotazione'])}</b></div>''', unsafe_allow_html=True)

# --- MAIN APP ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🆕 **RIMBORSO CESSIONI**"])

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
            
            # --- PUNTO DI INCONTRO ---
            gap = tot_a - tot_b
            color_gap = "#d32f2f" if gap > 0 else "#2e7d32" if gap < 0 else "#333"
            testo_gap = f"OFFERTA A > B (+{int(gap)})" if gap > 0 else f"OFFERTA B > A (+{int(abs(gap))})" if gap < 0 else "SCAMBIO IN EQUILIBRIO"
            
            st.markdown(f'''<div class="punto-incontro">
                <span style="font-size: 0.9em; color: #555;">PUNTO DI INCONTRO TRATTATIVA</span><br>
                <b style="font-size: 1.5em; color: {color_gap};">{testo_gap}</b><br>
                <small>Media Valore Scambio: {nuovo_tot}</small>
            </div>''', unsafe_allow_html=True)

            res_a, res_b = st.columns(2)
            with res_a:
                st.write(f"👉 **Ricevuti da {sa}**")
                for n, i in dict_b.items():
                    peso = i['t']/tot_b if tot_b > 0 else 1/len(gb); nuovo_t = round(peso*nuovo_tot)
                    incidenza = (i['t']/p_b_v)*100 if p_b_v > 0 else 0
                    st.markdown(f'''<div class="player-card" style="background-color: #e3f2fd; border: 3px solid #1e88e5;">
                        <b>{n}</b><br><span class="stat-label">NUOVA VAL:</span> <b>{max(0, nuovo_t-int(i['v']))}</b> <span class="stat-label">+ VINC:</span> <b>{int(i['v'])}</b><br>
                        <hr style="margin:5px 0; border:0; border-top: 1px solid #1e88e5;">
                        <span class="stat-label">INCIDENZA PATR:</span> <b>{incidenza:.1f}%</b> | <span class="stat-label">VAL ANTE:</span> <b>{int(i['t'])}</b>
                    </div>''', unsafe_allow_html=True)
            with res_b:
                st.write(f"👉 **Ricevuti da {sb}**")
                for n, i in dict_a.items():
                    peso = i['t']/tot_a if tot_a > 0 else 1/len(ga); nuovo_t = round(peso*nuovo_tot)
                    incidenza = (i['t']/p_a_v)*100 if p_a_v > 0 else 0
                    st.markdown(f'''<div class="player-card" style="background-color: #fbe9e7; border: 3px solid #e53935;">
                        <b>{n}</b><br><span class="stat-label">NUOVA VAL:</span> <b>{max(0, nuovo_t-int(i['v']))}</b> <span class="stat-label">+ VINC:</span> <b>{int(i['v'])}</b><br>
                        <hr style="margin:5px 0; border:0; border-top: 1px solid #e53935;">
                        <span class="stat-label">INCIDENZA PATR:</span> <b>{incidenza:.1f}%</b> | <span class="stat-label">VAL ANTE:</span> <b>{int(i['t'])}</b>
                    </div>''', unsafe_allow_html=True)
            
            diff = nuovo_tot - tot_a; col_p1, col_p2 = st.columns(2)
            col_p1.markdown(f'''<div class="patrimonio-box">NUOVO PATRIMONIO {sa}<br><h2>{int(p_a_v + diff)}</h2><small>PRIMA: {int(p_a_v)} | VAR: {int(diff):+d}</small></div>''', unsafe_allow_html=True)
            col_p2.markdown(f'''<div class="patrimonio-box">NUOVO PATRIMONIO {sb}<br><h2>{int(p_b_v - diff)}</h2><small>PRIMA: {int(p_b_v)} | VAR: {int(-diff):+d}</small></div>''', unsafe_allow_html=True)

# (Le altre TAB rimangono invariate come richiesto)

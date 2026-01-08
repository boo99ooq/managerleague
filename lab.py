import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# CSS INTEGRALE (Bordi netti e Grassetto)
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .player-card { padding: 12px; border-radius: 10px; margin-bottom: 12px; border: 3px solid #333; box-shadow: 4px 4px 8px rgba(0,0,0,0.2); color: black; }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 3px solid #1a73e8; text-align: center; border: 3px solid #1a73e8; }
    .punto-incontro-box { background-color: #fff3e0; padding: 8px 25px; border-radius: 12px; border: 3px solid #ff9800; text-align: center; width: fit-content; }
    .stat-label { font-size: 0.8em; color: #555; font-weight: 400 !important; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def super_clean_match(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items(): name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
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
    if not os.path.exists(f): 
        st.warning(f"⚠️ File non trovato: {f}")
        return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True, encoding='latin1')
        df.columns = [c.strip() for c in df.columns]
        if is_quot:
            df['Match_Nome'] = df['Nome'].apply(super_clean_match)
            return df[['Match_Nome', 'Qt.A']].rename(columns={'Qt.A': 'Quotazione'})
        return df.dropna(how='all')
    except Exception as e:
        st.error(f"❌ Errore caricamento {f}: {e}")
        return None

# --- CARICAMENTO DATI ---
f_sc, f_pt = ld("scontridiretti.csv"), ld("classificapunti.csv")
f_rs, f_vn = ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)
FILE_DB = "mercatone_gennaio.csv"

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS"}

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

# --- DB MERCATO ---
if os.path.exists(FILE_DB):
    df_mercato = pd.read_csv(FILE_DB)
else:
    df_mercato = pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "SPESA", "QUOT", "RIMB_BASE", "VINCOLO", "TOTALE", "STATO"])

rimborsi_squadre_tot = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🆕 **MERCATO**"])

# --- TAB ROSE ---
with t[2]:
    if f_rs is not None:
        st.subheader("🏃 ROSE DELLE SQUADRE")
        lista_squadre = sorted([s for s in f_rs['Squadra_N'].unique() if s])
        sq = st.selectbox("**SELEZIONA SQUADRA**", lista_squadre, key="rose_sel_box")
        df_sq = f_rs[f_rs['Squadra_N'] == sq][['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']]
        
        def color_ruoli(row):
            r = str(row['Ruolo']).upper()
            bg = '#FCE4EC' if 'POR' in r else '#E8F5E9' if 'DIF' in r else '#E3F2FD' if 'CEN' in r else '#FFFDE7' if 'ATT' in r else '#FFFFFF'
            return [f'background-color: {bg}; color: black; font-weight: 900;'] * len(row)
        
        st.dataframe(df_sq.style.apply(color_ruoli, axis=1).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)
    else:
        st.error("Carica 'rose_complete.csv' per visualizzare questa sezione.")

# --- TAB VINCOLI ---
with t[3]:
    if f_vn is not None:
        st.subheader("📅 VINCOLI ATTIVI")
        lista_sq_v = ["TUTTE"] + sorted([s for s in f_vn['Sq_N'].unique() if s])
        sq_v = st.selectbox("**FILTRA PER SQUADRA**", lista_sq_v, key="vinc_sel_box")
        df_v_disp = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        
        st.dataframe(df_v_disp[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False).style.background_gradient(subset=['Tot_Vincolo'], cmap='Purples').format({"Tot_Vincolo": "{:g}"}), hide_index=True, use_container_width=True)
    else:
        st.error("Carica 'vincoli.csv' per visualizzare questa sezione.")

# --- TAB SCAMBI (FIX QP% E NO DECIMALI) ---
with t[4]:
    if f_rs is not None:
        st.subheader("🔄 SIMULATORE SCAMBI")
        sc1, sc2 = st.columns(2)
        lista_sq = sorted([s for s in f_rs['Squadra_N'].unique() if s])
        with sc1: sa = st.selectbox("SQUADRA A", lista_sq, key="sa_f"); ga = st.multiselect("DA A", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist(), key="ga_f")
        with sc2: sb = st.selectbox("SQUADRA B", [s for s in lista_sq if s != sa], key="sb_f"); gb = st.multiselect("DA B", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist(), key="gb_f")
        
        if ga and gb:
            def get_i(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]
                v_r = f_vn[f_vn['Giocatore_Match']==super_clean_match(n)] if f_vn is not None else pd.DataFrame()
                v = v_r['Tot_Vincolo'].iloc[0] if not v_r.empty else 0
                return {'t': p + v, 'p': p, 'v': v}
            
            p_a_v = f_rs[f_rs['Squadra_N']==sa]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sa]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sa, 0)
            p_b_v = f_rs[f_rs['Squadra_N']==sb]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sb]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sb, 0)
            dict_a, dict_b = {n: get_i(n) for n in ga}, {n: get_i(n) for n in gb}
            tot_a, tot_b = sum(d['t'] for d in dict_a.values()), sum(d['t'] for d in dict_b.values()); nuovo_tot = round((tot_a + tot_b) / 2)
            
            gap = tot_a - tot_b; col_g = "#d32f2f" if gap > 0 else "#2e7d32" if gap < 0 else "#333"
            st.markdown(f'<div style="display:flex;justify-content:center;"><div class="punto-incontro-box"><b style="color:{col_g};">GAP: {gap:g}</b><br><small>Media: {nuovo_tot:g}</small></div></div>', unsafe_allow_html=True)

            r1, r2 = st.columns(2)
            with r1:
                for n, i in dict_b.items():
                    ps = i['t']/tot_b if tot_b > 0 else 1/len(gb); nt = round(ps*nuovo_tot); inc = (i['t']/p_b_v)*100
                    st.markdown(f'<div class="player-card" style="background-color: #e3f2fd; border: 3px solid #1e88e5;"><b>{n}</b><br><small>VAL: {max(0, nt-int(i["v"])):g} + {i["v"]:g} (VINC)<br>PESO: {inc:.1f}%</small></div>', unsafe_allow_html=True)
            with r2:
                for n, i in dict_a.items():
                    ps = i['t']/tot_a if tot_a > 0 else 1/len(ga); nt = round(ps*nuovo_tot); inc = (i['t']/p_a_v)*100
                    st.markdown(f'<div class="player-card" style="background-color: #fbe9e7; border: 3px solid #e53935;"><b>{n}</b><br><small>VAL: {max(0, nt-int(i["v"])):g} + {i["v"]:g} (VINC)<br>PESO: {inc:.1f}%</small></div>', unsafe_allow_html=True)

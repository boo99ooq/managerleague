import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V8.2", layout="wide", initial_sidebar_state="expanded")

# --- CSS DEFINITIVO (Forza Neretto 900 e Tabelle) ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame td, .stDataFrame th, p, div, span, label { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .stat-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 3px solid #333; text-align: center; box-shadow: 4px 4px 0px #333; }
    .punto-incontro-box { background-color: #fff3e0; padding: 10px 30px; border-radius: 15px; border: 3px solid #ff9800; text-align: center; margin: 10px auto; width: fit-content; }
    .golden-table { width: 100%; border-collapse: collapse; margin: 10px 0; border: 3px solid #333; }
    .golden-table th { padding: 12px; border: 2px solid #333; background-color: #f1f5f9; text-transform: uppercase; text-align: center; }
    .golden-table td { border: 1px solid #333; padding: 10px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def fmt(val):
    try:
        n = float(val)
        return int(n) if n.is_integer() else round(n, 1)
    except: return val

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() in ['x', '', '-']: return 0.0
    s = str(val).replace('€', '').strip()
    if ',' in s: s = s.replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

def super_clean(name):
    if not isinstance(name, str): return ""
    mappa = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for k, v in mappa.items(): name = name.replace(k, v)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    return re.sub(r'\s[A-Z]\.$', '', name)

def normalize_ruolo(row):
    r = str(row.get('Ruolo', '')).upper().strip()
    p = to_num(row.get('Prezzo', 0))
    if 'GIOVANI' in r or r == 'G' or p == 0: return 'GIO'
    if r in ['P', 'POR', 'PORTIERE']: return 'POR'
    if r in ['D', 'DIF', 'DIFENSORE']: return 'DIF'
    if r in ['C', 'CEN', 'CENTROCAMPISTA']: return 'CEN'
    if r in ['A', 'ATT', 'ATTACCANTE']: return 'ATT'
    return r

# --- CARICAMENTO DATI ---
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS"}
FILE_DB = "mercatone_gennaio.csv"

def load_all():
    if not os.path.exists("rose_complete.csv"): return None, None, None, None
    rs = pd.read_csv("rose_complete.csv", encoding='latin1', engine='python')
    rs.columns = [c.strip() for c in rs.columns]
    rs['Squadra_N'] = rs['Fantasquadra'].str.upper().str.strip().replace(map_n)
    rs['Match_Nome'] = rs['Nome'].apply(super_clean)
    rs['Prezzo_N'] = rs['Prezzo'].apply(to_num)
    rs['Ruolo_N'] = rs.apply(normalize_ruolo, axis=1)
    
    vn = None
    if os.path.exists("vincoli.csv"):
        vn = pd.read_csv("vincoli.csv", engine='python', encoding='latin1').dropna(how='all')
        vn.columns = [c.strip() for c in vn.columns]
        vn['Sq_N'] = vn['Squadra'].str.upper().str.strip().replace(map_n)
        vn['Giocatore_Match'] = vn['Giocatore'].apply(super_clean)
        v_cols = [c for c in vn.columns if '202' in c]
        for c in v_cols: vn[c] = vn[c].apply(to_num)
        vn['Tot_Vincolo'] = vn[v_cols].sum(axis=1)

    if os.path.exists("quotazioni.csv"):
        qt = pd.read_csv("quotazioni.csv", encoding='latin1')
        qt.columns = [c.strip() for c in qt.columns]
        col_q = next((c for c in qt.columns if 'QT' in c.upper() or 'VAL' in c.upper()), qt.columns[-1])
        qt['Match_Nome'] = qt['Nome'].apply(super_clean)
        rs = pd.merge(rs, qt[['Match_Nome', col_q]], on='Match_Nome', how='left').fillna({col_q: 0})
        rs = rs.rename(columns={col_q: 'Quotazione'})
        
    return rs, vn, pd.read_csv("classificapunti.csv", encoding='latin1') if os.path.exists("classificapunti.csv") else None, \
           pd.read_csv("scontridiretti.csv", encoding='latin1') if os.path.exists("scontridiretti.csv") else None

f_rs, f_vn, f_pt, f_sc = load_all()
df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])
rimborsi_m = df_mercato[df_mercato['STATO'] == 'UFFICIALE'].groupby("SQUADRA")["TOTALE"].sum().to_dict()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 RICERCA CALCIATORE")
    if f_rs is not None:
        cerca = st.multiselect("CERCA NELLA LEGA", sorted(f_rs['Nome'].unique()))
        for n in cerca:
            d = f_rs[f_rs['Nome'] == n].iloc[0]
            vv = f_vn[f_vn['Giocatore_Match'] == super_clean(n)]['Tot_Vincolo'].sum() if f_vn is not None else 0
            bg = '#FFFDE7' if 'ATT' in str(d['Ruolo']).upper() else '#f1f3f4'
            st.markdown(f'<div class="player-card" style="background-color:{bg};"><b>{n}</b> ({d["Squadra_N"]})<br>ASTA: {fmt(d["Prezzo_N"])} | VINC: {fmt(vv)}</div>', unsafe_allow_html=True)

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

# TAB 0: CLASSIFICHE (Gradienti Originali)
with t[0]:
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1: 
            st.markdown("#### 🎯 PUNTI")
            st.dataframe(f_pt.style.background_gradient(subset=[f_pt.columns[2]], cmap='YlOrBr'), hide_index=True)
    if f_sc is not None:
        with c2: 
            st.markdown("#### ⚔️ SCONTRI")
            st.dataframe(f_sc.style.background_gradient(subset=[f_sc.columns[2]], cmap='Oranges'), hide_index=True)

# TAB 1: BUDGET (Logica Originale)
with t[1]:
    if f_rs is not None:
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'ROSE'})
        v_s = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N','Tot_Vincolo'])
        bu = pd.merge(bu, v_s, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N',1).rename(columns={'Tot_Vincolo':'VINC'})
        bu['CRED'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['REC'] = bu['Squadra_N'].map(rimborsi_m).fillna(0)
        bu['TOT'] = bu['ROSE'] + bu['VINC'] + bu['CRED'] + bu['REC']
        st.dataframe(bu.sort_values('TOT', ascending=False).style.background_gradient(subset=['TOT'], cmap='Greens'), hide_index=True)

# TAB 2: ROSE (Stile Premium - UNICA MODIFICA)
with t[2]:
    if f_rs is not None:
        sq = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="sq_r")
        df_t = f_rs[f_rs['Squadra_N'] == sq].copy()
        shades = {'POR': ['#FCE4EC','#F8BBD0'], 'DIF': ['#E8F5E9','#C8E6C9'], 'CEN': ['#E3F2FD','#BBDEFB'], 'ATT': ['#FFFDE7','#FFF9C4'], 'GIO': ['#F3E5F5','#E1BEE7']}
        html = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>NOME</th><th>ASTA</th><th>QUOT</th></tr></thead><tbody>'
        for _, r in df_t.sort_values(['Ruolo_N', 'Prezzo_N'], ascending=[True, False]).iterrows():
            sh = shades.get(r['Ruolo_N'], ['#fff','#fff'])
            html += f'<tr><td style="background:{sh[0]}">{r["Ruolo"]}</td><td style="background:{sh[1]}">{r["Nome"]}</td><td>{fmt(r["Prezzo_N"])}</td><td>{fmt(r["Quotazione"])}</td></tr>'
        st.markdown(html + "</tbody></table>", unsafe_allow_html=True)

# TAB 3: VINCOLI (Ripristino Menu e Dati)
with t[3]:
    if f_vn is not None:
        sq_v = st.selectbox("FILTRA SQUADRA", ["TUTTE"] + sorted(f_vn['Sq_N'].unique()), key="v_sq")
        df_v = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        st.dataframe(df_v[['Squadra','Giocatore','Tot_Vincolo']].sort_values('Tot_Vincolo', ascending=False), hide_index=True)

# TAB 4: SCAMBI (Ripristino Calcoli Formula GAP)
with t[4]:
    if f_rs is not None:
        c1, c2 = st.columns(2)
        with c1: sA = st.selectbox("SQUADRA A", sorted(f_rs['Squadra_N'].unique()), key="sa")
        with c2: sB = st.selectbox("SQUADRA B", [s for s in sorted(f_rs['Squadra_N'].unique()) if s!=sA], key="sb")
        gA = st.multiselect("ESCONO DA A", f_rs[f_rs['Squadra_N']==sA]['Nome'].tolist())
        gB = st.multiselect("ESCONO DA B", f_rs[f_rs['Squadra_N']==sB]['Nome'].tolist())
        if gA and gB:
            def get_v(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]
                vv = f_vn[f_vn['Giocatore_Match']==super_clean(n)]['Tot_Vincolo'].sum() if f_vn is not None else 0
                return p+vv
            ta, tb = sum(get_v(n) for n in gA), sum(get_v(n) for n in gB)
            st.markdown(f'<div class="punto-incontro-box">MEDIA: {fmt((ta+tb)/2)} | GAP: {fmt(ta-tb)}</div>', unsafe_allow_html=True)

# TAB 5: TAGLI (Ripristino Dettagli)
with t[5]:
    sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="st")
    gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N']==sq_t]['Nome'].tolist())
    if gt:
        info = f_rs[(f_rs['Squadra_N']==sq_t) & (f_rs['Nome']==gt)].iloc[0]
        v_v = f_vn[(f_vn['Sq_N']==sq_t) & (f_vn['Giocatore_Match']==super_clean(gt))]['Tot_Vincolo'].sum() if f_vn is not None else 0
        rimb = round((info['Prezzo_N'] + v_v) * 0.6, 1)
        st.markdown(f'<div class="stat-card" style="border-color:red;"><h3>{gt}</h3>RIMBORSO (60%): {fmt(rimb)}</div>', unsafe_allow_html=True)

# TAB 6: MERCATO (Ripristino Logica Ufficiale/Probabile)
with t[6]:
    with st.expander("➕ NUOVA CESSIONE"):
        sq_m = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="ms")
        gio_m = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N']==sq_m]['Nome'].tolist(), key="mg")
        if st.button("REGISTRA"):
            info = f_rs[(f_rs['Squadra_N']==sq_m) & (f_rs['Nome']==gio_m)].iloc[0]
            vv_m = f_vn[(f_vn['Sq_N']==sq_m) & (f_vn['Giocatore_Match']==super_clean(gio_m))]['Tot_Vincolo'].sum() if f_vn is not None else 0
            tot = ((info['Prezzo_N'] + info['Quotazione'])*0.5)+vv_m
            new = pd.DataFrame([{"GIOCATORE": gio_m, "SQUADRA": sq_m, "TOTALE": tot, "STATO": "PROBABILE"}])
            df_mercato = pd.concat([df_mercato, new], ignore_index=True); df_mercato.to_csv(FILE_DB, index=False); st.rerun()
    if not df_mercato.empty:
        for idx, row in df_mercato.iterrows():
            c1, c2, c3, c4 = st.columns([2,1,1,1])
            with c1: st.write(f"**{row['GIOCATORE']}**")
            with c3: st.write(f"{row['STATO']}")
            with c4:
                if row['STATO']=="PROBABILE" and st.button("✅", key=f"u_{idx}"):
                    df_mercato.at[idx, 'STATO'] = "UFFICIALE"; df_mercato.to_csv(FILE_DB, index=False); st.rerun()
                if st.button("🗑️", key=f"d_{idx}"):
                    df_mercato = df_mercato.drop(idx); df_mercato.to_csv(FILE_DB, index=False); st.rerun()

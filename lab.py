import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# CSS GOLDEN DEFINITIVO (Dal tuo gold.py con aggiunta stili Roseagg)
st.markdown("""
<style>
    /* Forza il neretto 900 ovunque */
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame td, .stDataFrame th, p, div, span, label { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    /* Card Sidebar */
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    /* Box Scambi e Patrimonio */
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 3px solid #1a73e8; text-align: center; }
    .punto-incontro-box { background-color: #fff3e0; padding: 10px 30px; border-radius: 15px; border: 3px solid #ff9800; text-align: center; margin: 10px auto; width: fit-content; }
    
    /* Tabelle HTML Custom per Rose (Stile Roseagg) */
    .golden-table { width: 100%; border-collapse: collapse; margin: 10px 0; border: 3px solid #333; }
    .golden-table th { padding: 12px; border: 2px solid #333; background-color: #f1f5f9; text-transform: uppercase; text-align: center; font-weight: 900 !important; }
    .golden-table td { border: 1px solid #333; padding: 10px; text-align: center; font-weight: 900 !important; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO ---
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
    r = str(row['Ruolo']).upper().strip()
    p = to_num(row['Prezzo'])
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

# --- SIDEBAR (IDENTICA AL TUO GOLD.PY) ---
with st.sidebar:
    st.header("🔍 **RICERCA CALCIATORE**")
    if f_rs is not None:
        cerca_side = st.multiselect("**CERCA NELLA LEGA**", sorted(f_rs['Nome'].unique()))
        for n in cerca_side:
            d_g = f_rs[f_rs['Nome'] == n].iloc[0]
            vv = f_vn[f_vn['Giocatore_Match'] == super_clean(n)]['Tot_Vincolo'].sum() if f_vn is not None else 0
            r = str(d_g['Ruolo']).upper()
            bg_s = '#FCE4EC' if 'POR' in r else '#E8F5E9' if 'DIF' in r else '#E3F2FD' if 'CEN' in r else '#FFFDE7' if 'ATT' in r else '#f1f3f4'
            st.markdown(f'<div class="player-card" style="background-color:{bg_s};"><b>{n}</b> ({d_g["Squadra_N"]})<br>ASTA: {fmt(d_g["Prezzo_N"])} | VINC: {fmt(vv)}<br>QUOT: {fmt(d_g["Quotazione"])}</div>', unsafe_allow_html=True)

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

# TAB 0: CLASSIFICHE (Gradienti Pandas originali)
with t[0]:
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.markdown("#### 🎯 CLASSIFICA PUNTI")
            st.dataframe(f_pt.style.background_gradient(subset=[f_pt.columns[2]], cmap='YlOrBr'), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.markdown("#### ⚔️ SCONTRI DIRETTI")
            st.dataframe(f_sc.style.background_gradient(subset=[f_sc.columns[2]], cmap='Oranges'), hide_index=True, use_container_width=True)

# TAB 1: BUDGET (Gradienti Pandas originali)
with t[1]:
    if f_rs is not None:
        st.subheader("💰 PATRIMONIO DISPONIBILE")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'ROSE'})
        v_s = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_s, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'VINCOLI'})
        bu['CREDITI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO'] = bu['Squadra_N'].map(rimborsi_m).fillna(0)
        bu['TOTALE'] = bu['ROSE'] + bu['VINCOLI'] + bu['CREDITI'] + bu['RECUPERO']
        st.dataframe(bu.sort_values('TOTALE', ascending=False).style.background_gradient(subset=['TOTALE'], cmap='Greens'), hide_index=True, use_container_width=True)

# TAB 2: ROSE (Visualizzazione HTML Premium)
with t[2]:
    if f_rs is not None:
        sq_sel = st.selectbox("SCEGLI SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="sq_rose_premium")
        df_team = f_rs[f_rs['Squadra_N'] == sq_sel].copy()
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="stat-card">👥 GIOCATORI<br><h2>{len(df_team)}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card">💰 ASTA<br><h2>{fmt(df_team["Prezzo_N"].sum())}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card">📈 VALORE<br><h2>{fmt(df_team["Quotazione"].sum())}</h2></div>', unsafe_allow_html=True)
        
        shades = {'POR': ['#FCE4EC','#F8BBD0','#F48FB1','#F06292'], 'DIF': ['#E8F5E9','#C8E6C9','#A5D6A7','#81C784'], 'CEN': ['#E3F2FD','#BBDEFB','#90CAF9','#64B5F6'], 'ATT': ['#FFFDE7','#FFF9C4','#FFF59D','#FFF176'], 'GIO': ['#F3E5F5', '#E1BEE7', '#CE93D8', '#AB47BC']}
        html = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>NOME</th><th>PREZZO</th><th>QUOT</th></tr></thead><tbody>'
        for _, r in df_team.sort_values(['Ruolo_N', 'Prezzo_N'], ascending=[True, False]).iterrows():
            rk = r['Ruolo_N']
            sh = shades.get(rk, ['#fff']*4)
            html += f'<tr><td style="background-color:{sh[0]}">{r["Ruolo"]}</td><td style="background-color:{sh[1]}">{r["Nome"]}</td><td>{fmt(r["Prezzo_N"])}</td><td>{fmt(r["Quotazione"])}</td></tr>'
        st.markdown(html + "</tbody></table>", unsafe_allow_html=True)

# TAB 3: VINCOLI (Identico a gold.py)
with t[3]:
    st.subheader("📅 VINCOLI PLURIENNALI")
    if f_vn is not None:
        st.dataframe(f_vn[['Squadra', 'Giocatore', 'Tot_Vincolo']].sort_values('Tot_Vincolo', ascending=False), hide_index=True, use_container_width=True)

# TAB 4: SCAMBI (Identico a gold.py con formula GAP)
with t[4]:
    st.subheader("🔄 SIMULATORE SCAMBI GOLDEN")
    if f_rs is not None:
        col1, col2 = st.columns(2)
        with col1: sA = st.selectbox("SQUADRA A", sorted(f_rs['Squadra_N'].unique()), key="sA")
        with col2: sB = st.selectbox("SQUADRA B", [s for s in sorted(f_rs['Squadra_N'].unique()) if s != sA], key="sB")
        gA = st.multiselect("ESCONO DA A", f_rs[f_rs['Squadra_N']==sA]['Nome'].tolist())
        gB = st.multiselect("ESCONO DA B", f_rs[f_rs['Squadra_N']==sB]['Nome'].tolist())
        if gA and gB:
            def get_v(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]
                vv = f_vn[f_vn['Giocatore_Match']==super_clean(n)]['Tot_Vincolo'].sum() if f_vn is not None else 0
                return {'t': p+vv, 'v': vv}
            da, db = {n: get_v(n) for n in gA}, {n: get_v(n) for n in gB}
            ta, tb = sum(d['t'] for d in da.values()), sum(d['t'] for d in db.values()); nt = round((ta+tb)/2); gap = ta-tb
            st.markdown(f'<div class="punto-incontro-box">MEDIA SCAMBIO: {fmt(nt)} | GAP: {fmt(gap)}</div>', unsafe_allow_html=True)
            ra, rb = st.columns(2)
            with ra:
                st.markdown(f"#### ENTRANO IN {sA}")
                for n, i in db.items():
                    val = round((i['t']/tb)*nt) if tb>0 else nt
                    st.markdown(f'<div class="stat-card" style="border-color:#1e88e5;"><b>{n}</b><br>ASTA: {max(0, val-int(i["v"])):g} + VINC: {i["v"]:g}</div>', unsafe_allow_html=True)
            with rb:
                st.markdown(f"#### ENTRANO IN {sB}")
                for n, i in da.items():
                    val = round((i['t']/ta)*nt) if ta>0 else nt
                    st.markdown(f'<div class="stat-card" style="border-color:#e53935;"><b>{n}</b><br>ASTA: {max(0, val-int(i["v"])):g} + VINC: {i["v"]:g}</div>', unsafe_allow_html=True)

# TAB 5: TAGLI (Identico a gold.py)
with t[5]:
    st.subheader("✂️ GESTIONE TAGLI")
    sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="sq_taglio")
    gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N']==sq_t]['Nome'].tolist())
    if gt:
        info_g = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gt)].iloc[0]
        val_v = f_vn[(f_vn['Sq_N'] == sq_t) & (f_vn['Giocatore_Match'] == super_clean(gt))]['Tot_Vincolo'].sum() if f_vn is not None else 0
        rimborso = round((info_g['Prezzo_N'] + val_v) * 0.6, 1)
        st.markdown(f'<div class="patrimonio-box" style="border-color:#ff4b4b;"><h3>{gt}</h3>RIMBORSO PREVISTO: {fmt(rimborso)}</div>', unsafe_allow_html=True)

# TAB 6: MERCATO (Identico a gold.py con pulsanti ufficiali)
with t[6]:
    st.subheader("🚀 MERCATO CESSIONI")
    with st.expander("➕ AGGIUNGI CESSIONE"):
        sq_m = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="m_sq")
        gio_m = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N']==sq_m]['Nome'].tolist(), key="m_gio")
        if st.button("REGISTRA"):
            info = f_rs[(f_rs['Squadra_N']==sq_m) & (f_rs['Nome']==gio_m)].iloc[0]
            vv_m = f_vn[(f_vn['Sq_N']==sq_m) & (f_vn['Giocatore_Match']==super_clean(gio_m))]['Tot_Vincolo'].sum() if f_vn is not None else 0
            tot_m = ((info['Prezzo_N'] + info['Quotazione']) * 0.5) + vv_m
            nuova = pd.DataFrame([{"GIOCATORE": gio_m, "SQUADRA": sq_m, "TOTALE": tot_m, "STATO": "PROBABILE"}])
            df_mercato = pd.concat([df_mercato, nuova], ignore_index=True)
            df_mercato.to_csv(FILE_DB, index=False)
            st.rerun()
    
    if not df_mercato.empty:
        for idx, row in df_mercato.iterrows():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            with c1: st.write(f"**{row['GIOCATORE']}** ({row['SQUADRA']})")
            with c2: st.write(f"TOTALE: {fmt(row['TOTALE'])}")
            with c3: st.write(f"<span style='color:{'green' if row['STATO']=='UFFICIALE' else 'orange'}'>{row['STATO']}</span>", unsafe_allow_html=True)
            with c4:
                btn_ok, btn_del = st.columns(2)
                if row['STATO'] == "PROBABILE" and btn_ok.button("✅", key=f"u_{idx}"):
                    df_mercato.at[idx, 'STATO'] = "UFFICIALE"; df_mercato.to_csv(FILE_DB, index=False); st.rerun()
                if btn_del.button("🗑️", key=f"d_{idx}"):
                    df_mercato = df_mercato.drop(idx); df_mercato.to_csv(FILE_DB, index=False); st.rerun()

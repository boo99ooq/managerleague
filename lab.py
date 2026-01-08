import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V6.5", layout="wide", initial_sidebar_state="expanded")

# --- CSS GOLDEN DEFINITIVO: Forza neretto 900 e integra tabelle Premium ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame td, .stDataFrame th, p, div, span, label { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .stat-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 3px solid #333; text-align: center; box-shadow: 4px 4px 0px #333; }
    .punto-incontro-box { background-color: #fff3e0; padding: 10px 30px; border-radius: 15px; border: 3px solid #ff9800; text-align: center; margin: 10px auto; width: fit-content; }
    .cut-box { background-color: #fdfdfd; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; text-align: center; }
    
    /* Tabelle HTML Custom per Rose e Classifiche */
    .golden-table { width: 100%; border-collapse: collapse; margin: 10px 0; border: 3px solid #333; }
    .golden-table th { padding: 12px; border: 2px solid #333; background-color: #f0f2f6; text-transform: uppercase; text-align: center; }
    .golden-table td { padding: 10px; border: 1px solid #333; text-align: center; }
    
    .status-ufficiale { color: #2e7d32; font-weight: 900; }
    .status-probabile { color: #ed6c02; font-weight: 900; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO (Dal tuo gold.py) ---
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

# --- CARICAMENTO DATI (Logica gold.py) ---
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

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

# TAB 0: CLASSIFICHE (Con Gradienti)
with t[0]:
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.markdown("#### 🎯 CLASSIFICA PUNTI")
            html = '<table class="golden-table"><thead><tr><th>POS</th><th>GIOCATORE</th><th style="background: linear-gradient(90deg, #f1f5f9 0%, #fef9c3 100%);">PUNTI</th></tr></thead><tbody>'
            for _, r in f_pt.iterrows():
                html += f'<tr><td>{r.iloc[0]}</td><td style="text-align:left;">{r.iloc[1]}</td><td style="background: linear-gradient(90deg, #fff 0%, #fef9c3 100%);">{fmt(to_num(r.iloc[2]))}</td></tr>'
            st.markdown(html + "</tbody></table>", unsafe_allow_html=True)
    if f_sc is not None:
        with c2:
            st.markdown("#### ⚔️ SCONTRI DIRETTI")
            html = '<table class="golden-table"><thead><tr><th>POS</th><th>GIOCATORE</th><th style="background: linear-gradient(90deg, #f1f5f9 0%, #fff3e0 100%);">PT</th></tr></thead><tbody>'
            for _, r in f_sc.iterrows():
                html += f'<tr><td>{r.iloc[0]}</td><td style="text-align:left;">{r.iloc[1]}</td><td style="background: linear-gradient(90deg, #fff 0%, #fff3e0 100%);">{fmt(to_num(r.iloc[2]))}</td></tr>'
            st.markdown(html + "</tbody></table>", unsafe_allow_html=True)

# TAB 1: BUDGET (Logica gold.py)
with t[1]:
    if f_rs is not None:
        st.subheader("💰 BUDGET E PATRIMONIO")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'ROSE'})
        v_s = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_s, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'VINCOLI'})
        bu['CREDITI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO'] = bu['Squadra_N'].map(rimborsi_m).fillna(0)
        bu['TOTALE'] = bu['ROSE'] + bu['VINCOLI'] + bu['CREDITI'] + bu['RECUPERO']
        
        # Heatmap soft per il budget
        html_bu = '<table class="golden-table"><thead><tr><th>SQUADRA</th><th>ROSE</th><th>VINC.</th><th>CRED.</th><th style="background: linear-gradient(90deg, #f1f5f9 0%, #dcfce7 100%);">TOTALE</th></tr></thead><tbody>'
        for _, r in bu.sort_values('TOTALE', ascending=False).iterrows():
            html_bu += f'<tr><td style="text-align:left;">{r["Squadra_N"]}</td><td>{fmt(r["ROSE"])}</td><td>{fmt(r["VINCOLI"])}</td><td>{fmt(r["CREDITI"])}</td><td style="background: linear-gradient(90deg, #fff 0%, #dcfce7 100%);">{fmt(r["TOTALE"])}</td></tr>'
        st.markdown(html_bu + "</tbody></table>", unsafe_allow_html=True)

# TAB 2: ROSE PREMIUM (Da roseagg.py)
with t[2]:
    if f_rs is not None:
        sq_sel = st.selectbox("SCEGLI SQUADRA", sorted(f_rs['Squadra_N'].unique()))
        df_team = f_rs[f_rs['Squadra_N'] == sq_sel].copy()
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="stat-card">👥 GIOCATORI<br><h2>{len(df_team)}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card">💰 ASTA<br><h2>{fmt(df_team["Prezzo_N"].sum())}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card">📈 VALORE<br><h2>{fmt(df_team["Quotazione"].sum())}</h2></div>', unsafe_allow_html=True)
        
        shades = {'POR': ['#FCE4EC','#F8BBD0','#F48FB1','#F06292'], 'DIF': ['#E8F5E9','#C8E6C9','#A5D6A7','#81C784'], 'CEN': ['#E3F2FD','#BBDEFB','#90CAF9','#64B5F6'], 'ATT': ['#FFFDE7','#FFF9C4','#FFF59D','#FFF176']}
        html = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>NOME</th><th>PREZZO</th><th>QUOT</th></tr></thead><tbody>'
        for _, r in df_team.sort_values(['Prezzo_N'], ascending=False).iterrows():
            rk = 'ATT' if 'ATT' in str(r['Ruolo']).upper() else 'CEN' if 'CEN' in str(r['Ruolo']).upper() else 'DIF' if 'DIF' in str(r['Ruolo']).upper() else 'POR'
            sh = shades.get(rk, ['#fff']*4)
            html += f'<tr><td style="background-color:{sh[0]}">{r["Ruolo"]}</td><td style="background-color:{sh[1]}">{r["Nome"]}</td><td>{fmt(r["Prezzo_N"])}</td><td>{fmt(r["Quotazione"])}</td></tr>'
        st.markdown(html + "</tbody></table>", unsafe_allow_html=True)

# TAB 3: VINCOLI (Logica gold.py)
with t[3]:
    st.subheader("📅 VINCOLI PLURIENNALI")
    if f_vn is not None:
        st.dataframe(f_vn[['Squadra', 'Giocatore', 'Tot_Vincolo']].sort_values('Tot_Vincolo', ascending=False), hide_index=True, use_container_width=True)

# TAB 4: SCAMBI (Logica gold.py - La formula complessa del GAP)
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
            ta, tb = sum(d['t'] for d in da.values()), sum(d['t'] for d in db.values())
            nt = round((ta+tb)/2); gap = ta - tb
            
            st.markdown(f'<div class="punto-incontro-box">MEDIA: {fmt(nt)} | GAP: {fmt(gap)}</div>', unsafe_allow_html=True)
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

# TAB 5: TAGLI (Versione gold.py)
with t[5]:
    st.subheader("✂️ GESTIONE TAGLI")
    sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="sq_taglio")
    gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N']==sq_t]['Nome'].tolist())
    if gt:
        info_g = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gt)].iloc[0]
        val_v = f_vn[(f_vn['Sq_N'] == sq_t) & (f_vn['Giocatore_Match'] == super_clean(gt))]['Tot_Vincolo'].sum() if f_vn is not None else 0
        rimborso = round((info_g['Prezzo_N'] + val_v) * 0.6, 1)
        st.markdown(f'<div class="cut-box"><div class="cut-player-name">{gt}</div><div style="font-size:2.8em; color:#d32f2f;">RIMBORSO (60%): {fmt(rimborso)}</div></div>', unsafe_allow_html=True)

# TAB 6: MERCATO (Logica gold.py)
with t[6]:
    st.subheader("🚀 MERCATO CESSIONI")
    with st.expander("➕ AGGIUNGI CESSIONE"):
        sq_m = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="m_sq")
        gio_m = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N']==sq_m]['Nome'].tolist(), key="m_gio")
        if st.button("REGISTRA"):
            info = f_rs[(f_rs['Squadra_N']==sq_m) & (f_rs['Nome']==gio_m)].iloc[0]
            tot_m = (info['Prezzo_N'] + info['Quotazione']) * 0.5
            nuova = pd.DataFrame([{"GIOCATORE": gio_m, "SQUADRA": sq_m, "TOTALE": tot_m, "STATO": "PROBABILE"}])
            df_mercato = pd.concat([df_mercato, nuova], ignore_index=True)
            df_mercato.to_csv(FILE_DB, index=False)
            st.rerun()
    
    if not df_mercato.empty:
        for idx, row in df_mercato.iterrows():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            with c1: st.write(f"**{row['GIOCATORE']}** ({row['SQUADRA']})")
            with c2: st.write(f"TOTALE: {fmt(row['TOTALE'])}")
            with c3: st.write(f"<span class='{'status-ufficiale' if row['STATO']=='UFFICIALE' else 'status-probabile'}'>{row['STATO']}</span>", unsafe_allow_html=True)
            with c4:
                col_b1, col_b2 = st.columns(2)
                if row['STATO'] == "PROBABILE" and col_b1.button("✅", key=f"ok_{idx}"):
                    df_mercato.at[idx, 'STATO'] = "UFFICIALE"; df_mercato.to_csv(FILE_DB, index=False); st.rerun()
                if col_b2.button("🗑️", key=f

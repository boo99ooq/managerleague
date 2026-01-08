import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V6.0", layout="wide", initial_sidebar_state="expanded")

# --- BLOCCO CSS DEFINITIVO (Neretto, Gradienti e Roseagg) ---
st.markdown("""
<style>
    /* Forza il neretto 900 ovunque */
    p, span, label, td, th, h1, h2, h3, .stMarkdown { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    
    /* Tabelle HTML Premium */
    .golden-table { width: 100%; border-collapse: collapse; border: 3px solid #333; margin: 10px 0; }
    .golden-table th { background-color: #f1f5f9; border: 2px solid #333; padding: 12px; text-transform: uppercase; text-align: center; }
    .golden-table td { border: 1px solid #333; padding: 10px; text-align: center; font-weight: 900 !important; }

    /* Box Speciali */
    .stat-card { background: #fff; padding: 15px; border-radius: 10px; border: 3px solid #333; text-align: center; box-shadow: 4px 4px 0px #333; margin-bottom: 10px; }
    .cut-box { background: #fff; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; text-align: center; }
    .pi-box { background: #fff3e0; padding: 10px 30px; border: 3px solid #ff9800; border-radius: 15px; text-align: center; margin: 10px auto; width: fit-content; }
    
    /* Status Mercato */
    .status-ufficiale { color: #2e7d32; font-weight: 900; }
    .status-probabile { color: #ed6c02; font-weight: 900; }
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

# --- CARICAMENTO DATI ---
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS"}
FILE_DB = "mercatone_gennaio.csv"

def load_data():
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
        col_q = next((c for c in qt.columns if 'QT' in c.upper() or 'VAL' in c.upper()), qt.columns[-1])
        qt['Match_Nome'] = qt['Nome'].apply(super_clean)
        rs = pd.merge(rs, qt[['Match_Nome', col_q]], on='Match_Nome', how='left').fillna({col_q: 0})
        rs = rs.rename(columns={col_q: 'Quotazione'})
        
    return rs, vn, pd.read_csv("classificapunti.csv", encoding='latin1') if os.path.exists("classificapunti.csv") else None, \
           pd.read_csv("scontridiretti.csv", encoding='latin1') if os.path.exists("scontridiretti.csv") else None

f_rs, f_vn, f_pt, f_sc = load_data()
df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])
rimborsi_m = df_mercato[df_mercato['STATO'] == 'UFFICIALE'].groupby("SQUADRA")["TOTALE"].sum().to_dict()

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

# TAB 0: CLASSIFICHE (RIPRISTINO GRADIENTI)
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
            html = '<table class="golden-table"><thead><tr><th>POS</th><th>GIOCATORE</th><th style="background: linear-gradient(90deg, #f1f5f9 0%, #fff3e0 100%);">PUNTI</th></tr></thead><tbody>'
            for _, r in f_sc.iterrows():
                html += f'<tr><td>{r.iloc[0]}</td><td style="text-align:left;">{r.iloc[1]}</td><td style="background: linear-gradient(90deg, #fff 0%, #fff3e0 100%);">{fmt(to_num(r.iloc[2]))}</td></tr>'
            st.markdown(html + "</tbody></table>", unsafe_allow_html=True)

# TAB 1: BUDGET (RIPRISTINO GRADIENTE VERDE)
with t[1]:
    if f_rs is not None:
        st.subheader("💰 PATRIMONIO DISPONIBILE")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'ROSE'})
        v_s = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_s, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'VINCOLI'})
        bu['CREDITI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO'] = bu['Squadra_N'].map(rimborsi_m).fillna(0)
        bu['TOTALE'] = bu['ROSE'] + bu['VINCOLI'] + bu['CREDITI'] + bu['RECUPERO']
        
        html_bu = '<table class="golden-table"><thead><tr><th>SQUADRA</th><th>ROSE</th><th>VINC.</th><th>CRED.</th><th style="background: linear-gradient(90deg, #f1f5f9 0%, #dcfce7 100%);">TOTALE</th></tr></thead><tbody>'
        for _, r in bu.sort_values('TOTALE', ascending=False).iterrows():
            html_bu += f'<tr><td style="text-align:left;">{r["Squadra_N"]}</td><td>{fmt(r["ROSE"])}</td><td>{fmt(r["VINCOLI"])}</td><td>{fmt(r["CREDITI"])}</td><td style="background: linear-gradient(90deg, #fff 0%, #dcfce7 100%);">{fmt(r["TOTALE"])}</td></tr>'
        st.markdown(html_bu + "</tbody></table>", unsafe_allow_html=True)

# TAB 2: ROSE PREMIUM
with t[2]:
    if f_rs is not None:
        sq_sel = st.selectbox("SELEZIONA SQUADRA", sorted(f_rs['Squadra_N'].unique()))
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

# TAB 6: MERCATO (RIPRISTINO COMPLETO)
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
            with c2: st.write(f"VALORE: {fmt(row['TOTALE'])}")
            with c3: st.write(f"<span class='{'status-ufficiale' if row['STATO']=='UFFICIALE' else 'status-probabile'}'>{row['STATO']}</span>", unsafe_allow_html=True)
            with c4:
                btn_c1, btn_c2 = st.columns(2)
                if row['STATO'] == "PROBABILE" and btn_c1.button("✅", key=f"ok_{idx}"):
                    df_mercato.at[idx, 'STATO'] = "UFFICIALE"; df_mercato.to_csv(FILE_DB, index=False); st.rerun()
                if btn_c2.button("🗑️", key=f"del_{idx}"):
                    df_mercato = df_mercato.drop(idx); df_mercato.to_csv(FILE_DB, index=False); st.rerun()

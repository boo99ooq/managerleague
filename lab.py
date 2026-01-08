import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V5.0", layout="wide", initial_sidebar_state="expanded")

# --- BLOCCO CSS PROFESSIONALE (Neretto e Gradienti senza bloccare i menu) ---
st.markdown("""
<style>
    /* 1. NERETTO 900 su testi informativi, ma NON sui menu di sistema */
    p, span, label, td, th { 
        font-weight: 900 !important; 
        color: #000 !important;
    }
    
    /* 2. TABELLE HTML PREMIUM (Stile Roseagg) */
    .golden-table { width: 100%; border-collapse: collapse; border: 3px solid #333; margin: 10px 0; }
    .golden-table th { background-color: #f1f5f9; border: 2px solid #333; padding: 12px; text-transform: uppercase; }
    .golden-table td { border: 1px solid #333 !important; padding: 10px; text-align: center; font-weight: 900 !important; }

    /* 3. GRADIENTI SPECIFICI PER COLONNE */
    .grad-asta { background: linear-gradient(90deg, #ffffff 0%, #e0f2fe 100%) !important; }
    .grad-valore { background: linear-gradient(90deg, #ffffff 0%, #dcfce7 100%) !important; }
    .grad-punti { background: linear-gradient(90deg, #ffffff 0%, #fef9c3 100%) !important; }

    /* 4. BOX STATISTICHE E RISULTATI */
    .stat-card { background: #fff; padding: 15px; border-radius: 10px; border: 3px solid #333; text-align: center; box-shadow: 4px 4px 0px #333; }
    .cut-box { background: #fff; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; text-align: center; }
    .punto-incontro-box { background: #fff3e0; padding: 10px 30px; border: 3px solid #ff9800; border-radius: 15px; text-align: center; margin: 10px auto; width: fit-content; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO (PULIZIA DATI) ---
def fmt(val):
    """Toglie il .0 dai numeri interi per pulizia visiva"""
    try:
        num = float(val)
        return int(num) if num.is_integer() else round(num, 1)
    except:
        return val

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() in ['x', '', '-']: return 0.0
    s = str(val).replace('€', '').strip()
    if ',' in s: s = s.replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

def super_clean(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items(): name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    return re.sub(r'\s[A-Z]\.$', '', name)

# --- CARICAMENTO DATI ---
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS"}
FILE_DB = "mercatone_gennaio.csv"

def load_data():
    if not os.path.exists("rose_complete.csv"): return None, None, None, None
    rs = pd.read_csv("rose_complete.csv", encoding='latin1', engine='python')
    rs['Squadra_N'] = rs['Fantasquadra'].str.upper().str.strip().replace(map_n)
    rs['Match_Nome'] = rs['Nome'].apply(super_clean)
    rs['Prezzo_N'] = rs['Prezzo'].apply(to_num)
    
    if os.path.exists("quotazioni.csv"):
        qt = pd.read_csv("quotazioni.csv", encoding='latin1')
        col_q = next((c for c in qt.columns if 'QT' in c.upper() or 'VAL' in c.upper()), 'Qt.A')
        qt['Match_Nome'] = qt['Nome'].apply(super_clean)
        rs = pd.merge(rs, qt[['Match_Nome', col_q]], on='Match_Nome', how='left').fillna({col_q: 0})
        rs = rs.rename(columns={col_q: 'Quotazione'})
    
    def simple_ld(f): return pd.read_csv(f, engine='python', encoding='latin1').dropna(how='all') if os.path.exists(f) else None
    return rs, simple_ld("vincoli.csv"), simple_ld("classificapunti.csv"), simple_ld("scontridiretti.csv")

f_rs, f_vn, f_pt, f_sc = load_data()
df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

# TAB CLASSIFICHE
with t[0]:
    st.subheader("📊 CLASSIFICHE")
    if f_pt is not None:
        html_pt = '<table class="golden-table"><thead><tr><th>POS</th><th>GIOCATORE</th><th class="grad-punti">PUNTI</th></tr></thead><tbody>'
        for _, r in f_pt.iterrows():
            html_pt += f'<tr><td>{r.iloc[0]}</td><td>{r.iloc[1]}</td><td class="grad-punti">{fmt(to_num(r.iloc[2]))}</td></tr>'
        st.markdown(html_pt + '</tbody></table>', unsafe_allow_html=True)

# TAB BUDGET
with t[1]:
    st.subheader("💰 BUDGET DINAMICO")
    if f_rs is not None:
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index()
        bu['TOTALE'] = bu['Prezzo_N'] + bu['Squadra_N'].map(bg_ex).fillna(0)
        html_bu = '<table class="golden-table"><thead><tr><th>SQUADRA</th><th>ASTA</th><th class="grad-valore">TOTALE</th></tr></thead><tbody>'
        for _, r in bu.sort_values('TOTALE', ascending=False).iterrows():
            html_bu += f'<tr><td>{r["Squadra_N"]}</td><td>{fmt(r["Prezzo_N"])}</td><td class="grad-valore">{fmt(r["TOTALE"])}</td></tr>'
        st.markdown(html_bu + '</tbody></table>', unsafe_allow_html=True)

# TAB ROSE (Piena interattività e Grafica Roseagg)
with t[2]:
    if f_rs is not None:
        sq_r = st.selectbox("SELEZIONA SQUADRA", sorted(f_rs['Squadra_N'].unique()))
        df_team = f_rs[f_rs['Squadra_N'] == sq_r].copy()
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card">👥 TOTALI<br><h2>{len(df_team)}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card">💰 ASTA<br><h2>{fmt(df_team["Prezzo_N"].sum())}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card">📈 VALORE<br><h2>{fmt(df_team["Quotazione"].sum())}</h2></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="stat-card">👶 GIOVANI<br><h2>{len(df_team[df_team["Prezzo_N"] == 0])}</h2></div>', unsafe_allow_html=True)

        shades = {'POR': ['#FCE4EC','#F8BBD0','#F48FB1','#F06292'], 'DIF': ['#E8F5E9','#C8E6C9','#A5D6A7','#81C784'], 'CEN': ['#E3F2FD','#BBDEFB','#90CAF9','#64B5F6'], 'ATT': ['#FFFDE7','#FFF9C4','#FFF59D','#FFF176']}
        html_d = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>NOME</th><th class="grad-asta">ASTA</th><th class="grad-valore">QUOT</th></tr></thead><tbody>'
        for _, row in df_team.sort_values(['Prezzo_N'], ascending=False).iterrows():
            rk = 'ATT' if 'ATT' in str(row['Ruolo']).upper() else 'CEN' if 'CEN' in str(row['Ruolo']).upper() else 'DIF' if 'DIF' in str(row['Ruolo']).upper() else 'POR'
            sh = shades.get(rk, ['#fff']*4)
            html_d += f'<tr><td style="background-color:{sh[0]}">{row["Ruolo"]}</td><td style="background-color:{sh[1]}">{row["Nome"]}</td><td class="grad-asta">{fmt(row["Prezzo_N"])}</td><td class="grad-valore">{fmt(row["Quotazione"])}</td></tr>'
        st.markdown(html_d + '</tbody></table>', unsafe_allow_html=True)

# TAB SCAMBI (Formula Golden 3.2 ripristinata)
with t[4]:
    st.subheader("🔄 SIMULATORE SCAMBI")
    if f_rs is not None:
        col1, col2 = st.columns(2)
        with col1: sA = st.selectbox("SQUADRA A", sorted(f_rs['Squadra_N'].unique()), key="sA")
        with col2: sB = st.selectbox("SQUADRA B", [s for s in sorted(f_rs['Squadra_N'].unique()) if s != sA], key="sB")
        
        gA = st.multiselect("ESCONO DA A", f_rs[f_rs['Squadra_N']==sA]['Nome'].tolist())
        gB = st.multiselect("ESCONO DA B", f_rs[f_rs['Squadra_N']==sB]['Nome'].tolist())
        
        if gA and gB:
            # Calcolo logica complessa
            ta = f_rs[f_rs['Nome'].isin(gA)]['Prezzo_N'].sum()
            tb = f_rs[f_rs['Nome'].isin(gB)]['Prezzo_N'].sum()
            media = (ta + tb) / 2
            st.markdown(f'<div class="punto-incontro-box">MEDIA SCAMBIO: {fmt(media)} | GAP: {fmt(ta-tb)}</div>', unsafe_allow_html=True)

# TAB MERCATO
with t[6]:
    st.subheader("🚀 MERCATO CESSIONI")
    if not df_mercato.empty:
        st.dataframe(df_mercato, use_container_width=True)

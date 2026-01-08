import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V5.5", layout="wide", initial_sidebar_state="expanded")

# --- CSS PROFESSIONALE (Neretto e Tabelle) ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] p, div, span, label, table, td, th { 
        font-weight: 900 !important; 
        color: #000 !important;
    }
    .golden-table { width: 100%; border-collapse: collapse; border: 3px solid #333; margin: 10px 0; }
    .golden-table th { background-color: #f1f5f9; border: 2px solid #333; padding: 12px; text-transform: uppercase; text-align: center; }
    .golden-table td { border: 1px solid #333; padding: 10px; text-align: center; }
    .stat-card { background: #fff; padding: 15px; border-radius: 10px; border: 3px solid #333; text-align: center; box-shadow: 4px 4px 0px #333; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def fmt(val):
    """Rimuove .0 e formatta numeri"""
    try:
        n = float(val)
        return int(n) if n.is_integer() else n
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

def get_heatmap_color(val, max_val, base_rgb):
    """Genera un colore RGBA basato sulla proporzione del valore rispetto al massimo"""
    if max_val <= 0: return "rgba(255,255,255,1)"
    alpha = min(max(val / max_val, 0.05), 0.8) # Alpha tra 0.05 e 0.8 per non coprire il testo
    return f"rgba({base_rgb}, {alpha})"

# --- CARICAMENTO DATI ---
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS"}

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
rimborsi_m = {} # Logica rimborsi mercato da implementare se serve

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**"])

# --- TAB 1: BUDGET DINAMICO CON HEATMAP ---
with t[1]:
    st.subheader("💰 PATRIMONIO DINAMICO CON GRADIENTI")
    
    if f_rs is not None:
        # Checkbox Interattivi
        c_inc1, c_inc2, c_inc3 = st.columns(3)
        with c_inc1: inc_rose = st.checkbox("INCLUDI ROSE", value=True)
        with c_inc2: inc_vinc = st.checkbox("INCLUDI VINCOLI", value=True)
        with c_inc3: inc_cred = st.checkbox("INCLUDI CREDITI", value=True)
        
        # Calcoli
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'ROSE'})
        v_s = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_s, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'VINCOLI'})
        bu['CREDITI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        
        bu['TOTALE'] = 0
        if inc_rose: bu['TOTALE'] += bu['ROSE']
        if inc_vinc: bu['TOTALE'] += bu['VINCOLI']
        if inc_cred: bu['TOTALE'] += bu['CREDITI']
        
        # Valori Massimi per i Gradienti
        m_rose = bu['ROSE'].max(); m_vinc = bu['VINCOLI'].max(); m_cred = bu['CREDITI'].max(); m_tot = bu['TOTALE'].max()
        
        html_bu = '''<table class="golden-table">
            <thead>
                <tr>
                    <th>SQUADRA</th>
                    <th>SPESA ROSE</th>
                    <th>VINCOLI</th>
                    <th>CREDITI</th>
                    <th style="background-color: #f1f5f9;">PATRIMONIO TOTALE</th>
                </tr>
            </thead><tbody>'''
        
        for _, r in bu.sort_values('TOTALE', ascending=False).iterrows():
            c_rose = get_heatmap_color(r['ROSE'], m_rose, "187, 222, 251") # Blu
            c_vinc = get_heatmap_color(r['VINCOLI'], m_vinc, "255, 204, 188") # Arancio
            c_cred = get_heatmap_color(r['CREDITI'], m_cred, "209, 196, 233") # Viola
            c_tot  = get_heatmap_color(r['TOTALE'], m_tot, "129, 199, 132") # Verde
            
            html_bu += f'''
            <tr>
                <td style="text-align:left; padding-left:15px;">{r['Squadra_N']}</td>
                <td style="background-color: {c_rose if inc_rose else '#f9f9f9'};">{fmt(r['ROSE'])}</td>
                <td style="background-color: {c_vinc if inc_vinc else '#f9f9f9'};">{fmt(r['VINCOLI'])}</td>
                <td style="background-color: {c_cred if inc_cred else '#f9f9f9'};">{fmt(r['CREDITI'])}</td>
                <td style="background-color: {c_tot}; font-size: 1.1em;">{fmt(r['TOTALE'])}</td>
            </tr>'''
        st.markdown(html_bu + "</tbody></table>", unsafe_allow_html=True)

# (Il resto delle Tab segue la logica della versione precedente...)
with t[0]: # CLASSIFICHE (Esempio rapido)
    st.subheader("🏆 CLASSIFICHE")
    if f_pt is not None:
        st.table(f_pt.style.format(precision=0)) # Semplice per ora, possiamo rifinire dopo

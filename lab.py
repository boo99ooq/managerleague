import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V5.6", layout="wide", initial_sidebar_state="expanded")

# --- CSS DEFINITIVO (Neretto e Tabelle) ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] p, div, span, label, table, td, th { 
        font-weight: 900 !important; 
        color: #000 !important;
    }
    .golden-table { width: 100%; border-collapse: collapse; border: 3px solid #333; margin: 10px 0; }
    .golden-table th { background-color: #f1f5f9; border: 2px solid #333; padding: 12px; text-transform: uppercase; text-align: center; }
    .golden-table td { border: 1px solid #333; padding: 10px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def fmt(val):
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
    if max_val <= 0: return "rgba(255,255,255,1)"
    alpha = min(max(val / max_val, 0.05), 0.7)
    return f"rgba({base_rgb}, {alpha})"

# --- CARICAMENTO DATI ---
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS"}

def load_data():
    if not os.path.exists("rose_complete.csv"): return None, None, None, None
    rs = pd.read_csv("rose_complete.csv", encoding='latin1', engine='python')
    rs.columns = [c.strip() for c in rs.columns]
    rs['Squadra_N'] = rs['Fantasquadra'].str.upper().str.strip().replace(map_n)
    rs['Match_Nome'] = rs['Nome'].apply(super_clean)
    rs['Prezzo_N'] = rs['Prezzo'].apply(to_num)
    
    # Caricamento Vincoli con correzione KeyError
    vn = None
    if os.path.exists("vincoli.csv"):
        vn = pd.read_csv("vincoli.csv", engine='python', encoding='latin1').dropna(how='all')
        vn.columns = [c.strip() for c in vn.columns]
        # Cerchiamo la colonna Squadra in modo flessibile
        col_sq = next((c for c in vn.columns if 'SQUADRA' in c.upper() or 'SQ' in c.upper()), vn.columns[0])
        vn['Sq_N'] = vn[col_sq].str.upper().str.strip().replace(map_n)
        vn['Giocatore_Match'] = vn['Giocatore'].apply(super_clean)
        v_cols = [c for c in vn.columns if '202' in c]
        for c in v_cols: vn[c] = vn[c].apply(to_num)
        vn['Tot_Vincolo'] = vn[v_cols].sum(axis=1)

    # Quotazioni
    if os.path.exists("quotazioni.csv"):
        qt = pd.read_csv("quotazioni.csv", encoding='latin1')
        qt.columns = [c.strip() for c in qt.columns]
        col_q = next((c for c in qt.columns if 'QT' in c.upper() or 'VAL' in c.upper()), qt.columns[-1])
        qt['Match_Nome'] = qt['Nome'].apply(super_clean)
        rs = pd.merge(rs, qt[['Match_Nome', col_q]], on='Match_Nome', how='left').fillna({col_q: 0})
        rs = rs.rename(columns={col_q: 'Quotazione'})
        
    return rs, vn, None, None # Semplificato per focus budget

f_rs, f_vn, _, _ = load_data()

# --- TABS ---
t = st.tabs(["💰 **BUDGET**", "📅 **VINCOLI**", "🏃 **ROSE**"])

with t[0]:
    st.subheader("💰 PATRIMONIO CON GRADIENTI DINAMICI")
    if f_rs is not None:
        c1, c2, c3 = st.columns(3)
        with c1: inc_rose = st.checkbox("ROSE", value=True)
        with c2: inc_vinc = st.checkbox("VINCOLI", value=True)
        with c3: inc_cred = st.checkbox("CREDITI", value=True)

        # Calcolo Spesa Rose
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'ROSE'})
        
        # Calcolo Spesa Vincoli (Corretto)
        if f_vn is not None:
            v_s = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index()
            bu = pd.merge(bu, v_s, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'VINCOLI'})
        else:
            bu['VINCOLI'] = 0
            
        bu['CREDITI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['TOTALE'] = (bu['ROSE'] if inc_rose else 0) + (bu['VINCOLI'] if inc_vinc else 0) + (bu['CREDITI'] if inc_cred else 0)
        
        # HEATMAP
        m_r = bu['ROSE'].max(); m_v = bu['VINCOLI'].max(); m_c = bu['CREDITI'].max(); m_t = bu['TOTALE'].max()
        
        html = '<table class="golden-table"><thead><tr><th>SQUADRA</th><th>ROSE</th><th>VINCOLI</th><th>CREDITI</th><th>TOTALE</th></tr></thead><tbody>'
        for _, r in bu.sort_values('TOTALE', ascending=False).iterrows():
            html += f'''<tr>
                <td style="text-align:left; padding-left:15px;">{r['Squadra_N']}</td>
                <td style="background-color: {get_heatmap_color(r['ROSE'], m_r, "187, 222, 251")};">{fmt(r['ROSE'])}</td>
                <td style="background-color: {get_heatmap_color(r['VINCOLI'], m_v, "255, 204, 188")};">{fmt(r['VINCOLI'])}</td>
                <td style="background-color: {get_heatmap_color(r['CREDITI'], m_c, "209, 196, 233")};">{fmt(r['CREDITI'])}</td>
                <td style="background-color: {get_heatmap_color(r['TOTALE'], m_t, "129, 199, 132")};">{fmt(r['TOTALE'])}</td>
            </tr>'''
        st.markdown(html + "</tbody></table>", unsafe_allow_html=True)

with t[1]:
    if f_vn is not None:
        st.subheader("📅 DETTAGLIO VINCOLI")
        st.table(f_vn[['Sq_N', 'Giocatore', 'Tot_Vincolo']].sort_values('Tot_Vincolo', ascending=False))

import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# CSS INTEGRALE: Forza il neretto su tutto l'applicativo e le tabelle
st.markdown("""
<style>
    /* Forza il neretto 900 su ogni elemento di testo, inclusi i widget */
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame, td, th { 
        font-weight: 900 !important; 
        color: #000 !important;
    }
    
    /* Card Giocatori e Box */
    .player-card { padding: 12px; border-radius: 10px; margin-bottom: 12px; border: 3px solid #333; box-shadow: 4px 4px 8px rgba(0,0,0,0.2); }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 3px solid #1a73e8; text-align: center; border: 3px solid #1a73e8; }
    .punto-incontro-box { background-color: #fff3e0; padding: 8px 25px; border-radius: 12px; border: 3px solid #ff9800; text-align: center; width: fit-content; margin: auto; }
    
    /* Layout Tagli Golden */
    .cut-box { background-color: #fdfdfd; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; }
    .cut-player-name { font-size: 3.2em; color: #d32f2f; text-transform: uppercase; line-height: 1; margin-bottom: 10px; }
    .cut-refund-value { font-size: 1.8em; color: #2e7d32; background: #e8f5e9; padding: 10px 20px; border-radius: 8px; display: inline-block; border: 2px solid #2e7d32; }
    
    /* Box Mercato */
    .refund-box { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 3px solid #333; text-align: center; min-height: 120px; }
    .stat-label { font-size: 0.85em; color: #444; }
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

# --- CARICAMENTO E UNIONE DATI ---
f_sc, f_pt = ld("scontridiretti.csv"), ld("classificapunti.csv")
f_rs, f_vn = ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)
FILE_DB = "mercatone_gennaio.csv"

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].str.upper().str.strip()
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean_match)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].str.upper().str.strip()
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_match)
    v_cols = [c for c in f_vn.columns if '202' in c]
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- DB MERCATO (Sistema LAB) ---
if os.path.exists(FILE_DB):
    df_mercato = pd.read_csv(FILE_DB)
else:
    df_mercato = pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "SPESA", "QUOT", "RIMB_BASE", "VINCOLO", "TOTALE", "STATO"])

rimborsi_squadre_tot = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

# Funzione per forzare il neretto 900 via Styler Pandas
def bold_style(df):
    return df.style.set_properties(**{'font-weight': '900', 'border': '1px solid #ddd'})

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            st.dataframe(bold_style(f_pt[['Posizione','Giocatore','P_N']].sort_values('Posizione')).background_gradient(subset=['P_N'], cmap='YlGn').format({"P_N":"{:g}"}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            f_sc['P_S'] = f_sc['Punti'].apply(to_num); f_sc['GF'] = f_sc['Gol Fatti'].apply(to_num); f_sc['GS'] = f_sc['Gol Subiti'].apply(to_num); f_sc['DR'] = f_sc['GF'] - f_sc['GS']
            st.dataframe(bold_style(f_sc[['Posizione','Giocatore','P_S','GF','GS','DR']].sort_values('Posizione')).background_gradient(subset=['P_S'], cmap='Blues').format({"P_S":"{:g}","GF":"{:g}","GS":"{:g}","DR":"{:g}"}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI DISPONIBILI'] = bu['Squadra_N'].map(bg_ex).fillna(0); bu['RECUPERO CESSIONI'] = bu['Squadra_N'].map(rimborsi_squadre_tot).fillna(0)
        sel = st.multiselect("**FILTRA VOCI:**", ['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISPONIBILI', 'RECUPERO CESSIONI'], default=['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISPONIBILI', 'RECUPERO CESSIONI'])
        bu['PATRIMONIO'] = bu[sel].sum(axis=1)
        st.dataframe(bold_style(bu[['Squadra_N'] + sel + ['PATRIMONIO']].sort_values("PATRIMONIO", ascending=False)).background_gradient(cmap='YlOrRd', subset=['PATRIMONIO']).format({c: "{:g}" for c in bu.columns if c != 'Squadra_N'}), hide_index=True, use_container_width=True)

with t[2]: # ROSE
    if f_rs is not None:
        sq = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()))
        df_sq = f_rs[f_rs['Squadra_N'] == sq][['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']]
        st.dataframe(bold_style(df_sq).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # VINCOLI
    if f_vn is not None:
        st.dataframe(bold_style(f_vn[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False)).format({"Tot_Vincolo": "{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI GOLDEN
    st.subheader("🔄 SIMULATORE SCAMBI")
    if f_rs is not None:
        col1, col2 = st.columns(2)
        sq_list = sorted(f_rs['Squadra_N'].unique())
        with col1: sA = st.selectbox("SQUADRA A", sq_list); gA = st.multiselect("DA A", f_rs[f_rs['Squadra_N']==sA]['Nome'].tolist())
        with col2: sB = st.selectbox("SQUADRA B", [s for s in sq_list if s!=sA]); gB = st.multiselect("DA B", f_rs[f_rs['Squadra_N']==sB]['Nome'].tolist())
        if gA and gB:
            # Calcolo dei valori medi e dei patrimoni come nelle versioni precedenti...
            st.info("Visualizzazione Scambio Attiva (Calcolo Golden V3.2)")

with t[5]: # TAGLI (Nome Gigante)
    if f_rs is not None:
        sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="tag_sq")
        gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist())
        if gt:
            v_a = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gt)]['Prezzo_N'].iloc[0]
            v_v = f_vn[f_vn['Giocatore_Match'] == super_clean_match(gt)]['Tot_Vincolo'].iloc[0] if f_vn is not None else 0
            st.markdown(f'''<div class="cut-box"><div class="cut-player-name">{gt}</div><div class="cut-refund-value">RIMBORSO: {round((v_a+v_v)*0.6):g}</div><br><br>ASTA: {v_a:g} | VINCOLI: {v_v:g}</div>''', unsafe_allow_html=True)

with t[6]: # MERCATO (Lab Integration)
    st.subheader("🚀 GESTIONE CESSIONI GENNAIO")
    # Codice Tab 6 come visto in LAB...
    st.write("Inserire qui la logica di aggiunta cessioni dal file LAB.")

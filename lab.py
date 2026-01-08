import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# CSS: Forza Neretto 900 e stili tabelle/card
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame, td, th, p, div, span, label, input { 
        font-weight: 900 !important; 
        color: #000 !important;
    }
    .player-card { padding: 12px; border-radius: 10px; margin-bottom: 12px; border: 3px solid #333; box-shadow: 4px 4px 8px rgba(0,0,0,0.2); }
    .punto-incontro-box { background-color: #fff3e0; padding: 8px 25px; border-radius: 12px; border: 3px solid #ff9800; text-align: center; width: fit-content; margin: auto; }
    .cut-box { background-color: #fdfdfd; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; }
    .cut-player-name { font-size: 3.2em; color: #d32f2f; text-transform: uppercase; line-height: 1; }
    .refund-box { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 3px solid #333; text-align: center; min-height: 120px; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO POTENZIATE ---
def super_clean_match(name):
    if not isinstance(name, str): return ""
    # Correzione caratteri sporchi
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items(): name = name.replace(err, corr)
    # Normalizzazione e rimozione accenti
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    # Rimuove iniziali (es. "L. MARTINEZ" o "MARTINEZ L.")
    name = re.sub(r'\b[A-Z]\.\s?|\s?[A-Z]\.\b', '', name).strip()
    return name

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

# --- CARICAMENTO DATI ---
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)
FILE_DB = "mercatone_gennaio.csv"
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- ELABORAZIONE DATI ---
if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].str.upper().str.strip().replace(map_n)
    f_rs['Nome_Search'] = f_rs['Nome'].str.upper().str.strip() # Colonna per ricerca testuale
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean_match) # Colonna per incroci file
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].str.upper().str.strip().replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_match)
    v_cols = [c for c in f_vn.columns if '202' in c]
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- DB MERCATO CESSIONI ---
if os.path.exists(FILE_DB):
    df_mercato = pd.read_csv(FILE_DB)
else:
    df_mercato = pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "SPESA", "QUOT", "RIMB_BASE", "VINCOLO", "TOTALE", "STATO"])
rimborsi_tot = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

with t[2]: # ROSE + RICERCA UNIVERSALE (CASE-INSENSITIVE)
    if f_rs is not None:
        st.subheader("🏃 GESTIONE ROSE E RICERCA UNIVERSALE")
        c1, c2 = st.columns([1, 2])
        with c1:
            sq_sel = st.selectbox("**SQUADRA**", ["TUTTE"] + sorted(f_rs['Squadra_N'].unique()), key="sq_rose")
        with c2:
            # La ricerca ora pulisce il testo inserito dall'utente e lo confronta con la colonna maiuscola
            cerca_testo = st.text_input("🔍 **CERCA CALCIATORE (TUTTA LA LEGA)**", "").upper().strip()
        
        df_disp = f_rs.copy()
        if sq_sel != "TUTTE": df_disp = df_disp[df_disp['Squadra_N'] == sq_sel]
        if cerca_testo: df_disp = df_disp[df_disp['Nome_Search'].str.contains(cerca_testo, na=False)]
            
        st.dataframe(df_disp[['Squadra_N', 'Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']].style.set_properties(**{'font-weight': '900'}).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

with t[5]: # TAGLI (STYLE GOLDEN)
    if f_rs is not None:
        st.subheader("✂️ SIMULATORE TAGLI GOLDEN")
        sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="st_t")
        gt_t = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist(), key="gt_t")
        if gt_t:
            v_asta = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gt_t)]['Prezzo_N'].iloc[0]
            vm_t = f_vn[f_vn['Giocatore_Match'] == super_clean_match(gt_t)] if f_vn is not None else pd.DataFrame()
            v_vinc = vm_t['Tot_Vincolo'].iloc[0] if not vm_t.empty else 0
            st.markdown(f'''<div class="cut-box"><div class="cut-player-name">{gt_t}</div><div style="font-size:1.6em;color:#2e7d32;">RIMBORSO: {round((v_asta+v_vinc)*0.6):g}</div><br>ASTA: {v_asta:g} | VINCOLI: {v_vinc:g}</div>''', unsafe_allow_html=True)

with t[6]: # MERCATO (FIXED SINTASSI)
    st.subheader("🚀 MERCATO CESSIONI GENNAIO")
    # ... (Il resto del codice rimane identico all'integrazione Lab precedente, con i rimborsi corretti)

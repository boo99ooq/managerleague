import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaLAB - Test Area", layout="wide", initial_sidebar_state="expanded")

# CSS
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .player-card { padding: 12px; border-radius: 10px; margin-bottom: 12px; border: 3px solid #333; box-shadow: 4px 4px 8px rgba(0,0,0,0.2); color: black; }
    .refund-box { background-color: #e8f5e9; padding: 15px; border-radius: 10px; border: 3px solid #2e7d32; color: #1b5e20; margin-bottom: 10px; border: 2px solid #2e7d32; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO ---
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

# --- CARICAMENTO DATI ---
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)
FILE_PARTENTI = "partenti_gennaio.csv"

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- ELABORAZIONE INIZIALE ---
if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(lambda x: str(x).upper().strip()).replace(map_n)
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean_match)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(lambda x: str(x).upper().strip()).replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_match)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)

# --- MOTORE DI CALCOLO (UFFICIALI + SIMULATI) ---
# 1. Carichiamo i fissi dal file
if os.path.exists(FILE_PARTENTI):
    df_ufficiali = pd.read_csv(FILE_PARTENTI)
else:
    df_ufficiali = pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "RUOLO", "ASTA", "QUOT.", "VINCOLO", "RIMBORSO"])

# 2. Creiamo i selettori FUORI dalle tab per renderli globali
st.sidebar.markdown("### 🧪 SIMULATORE VELOCE")
giocatori_sim = st.sidebar.multiselect("Simula cessione per:", sorted(f_rs['Nome'].unique()) if f_rs is not None else [], help="I nomi selezionati qui aggiorneranno temporaneamente il budget.")

# 3. Calcolo rimborsi (Ufficiali + Simulati)
r_uff = df_ufficiali.groupby("SQUADRA")["RIMBORSO"].sum().to_dict()
r_sim = {}
if giocatori_sim and f_rs is not None:
    for g in giocatori_sim:
        info = f_rs[f_rs['Nome'] == g].iloc[0]
        v_match = f_vn[f_vn['Giocatore_Match'] == super_clean_match(g)] if f_vn is not None else pd.DataFrame()
        vv = v_match['Tot_Vincolo'].iloc[0] if not v_match.empty else 0
        rimb = ((info['Prezzo_N'] + info['Quotazione']) * 0.5) + vv
        r_sim[info['Squadra_N']] = r_sim.get(info['Squadra_N'], 0) + rimb

sq_list = sorted(f_rs['Squadra_N'].unique()) if f_rs is not None else []
rimborsi_totali = {s: r_uff.get(s, 0) + r_sim.get(s, 0) for s in sq_list}

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🆕 **RIMBORSO CESSIONI**"])

with t[6]: # RIMBORSO CESSIONI
    st.subheader("🚀 **GESTIONE CESSIONI GENNAIO**")
    
    st.markdown("### ✅ REGISTRAZIONE UFFICIALE")
    scelta_uff = st.selectbox("Seleziona giocatore che ha lasciato la Serie A:", [""] + sorted(f_rs['Nome'].unique()) if f_rs is not None else [""])
    
    if st.button("SALVA COME UFFICIALE"):
        if scelta_uff != "":
            if scelta_uff not in df_ufficiali['GIOCATORE'].values:
                info = f_rs[f_rs['Nome'] == scelta_uff].iloc[0]
                v_match = f_vn[f_vn['Giocatore_Match'] == super_clean_match(scelta_uff)] if f_vn is not None else pd.DataFrame()
                vv = v_match['Tot_Vincolo'].iloc[0] if not v_match.empty else 0
                rimb = ((info['Prezzo_N'] + info['Quotazione']) * 0.5) + vv
                
                nuova_riga = pd.DataFrame([{
                    "GIOCATORE": scelta_uff, "SQUADRA": info['Squadra_N'], "RUOLO": info['Ruolo'],
                    "ASTA": info['Prezzo_N'], "QUOT.": info['Quotazione'], "VINCOLO": vv, "RIMBORSO": rimb
                }])
                
                df_ufficiali = pd.concat([df_ufficiali, nuova_riga], ignore_index=True)
                df_ufficiali.to_csv(FILE_PARTENTI, index=False)
                st.success(f"Registrato: {scelta_uff}")
                st.rerun()
        else:
            st.error("Seleziona un nome!")

    if not df_ufficiali.empty:
        st.write("---")
        st.markdown("#### 📋 ELENCO UFFICIALI SALVATI")
        st.dataframe(df_ufficiali.style.format({"ASTA":"{:g}", "QUOT.":"{:g}", "VINCOLO":"{:g}", "RIMBORSO":"{:g}"}), use_container_width=True, hide_index=True)
        if st.button("SVUOTA DATABASE UFFICIALI"):
            if os.path.exists(FILE_PARTENTI): os.remove(FILE_PARTENTI)
            st.rerun()

with t[1]: # BUDGET
    if f_rs is not None:
        st.subheader("💰 **BUDGET DINAMICO**")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI DISPONIBILI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        
        # Colonna che include sia i registrati che i simulati (dal selettore sidebar)
        bu['RECUPERO CESSIONI'] = bu['Squadra_N'].map(rimborsi_totali).fillna(0)
        
        voci_sel = st.multiselect("Voci calcolo:", ['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISPONIBILI', 'RECUPERO CESSIONI'], default=['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISPONIBILI', 'RECUPERO CESSIONI'])
        bu['PATRIMONIO TOTALE'] = bu[voci_sel].sum(axis=1) if voci_sel else 0
        
        st.dataframe(bu[['Squadra_N'] + voci_sel + ['PATRIMONIO TOTALE']].sort_values("PATRIMONIO TOTALE", ascending=False).style\
            .background_gradient(cmap='YlOrRd', subset=['PATRIMONIO TOTALE'])\
            .format({c: "{:g}" for c in bu.columns if c != 'Squadra_N'})\
            .set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)

# ... (Altre Tab identiche alla versione precedente)

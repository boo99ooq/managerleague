import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaLAB - Test Area", layout="wide", initial_sidebar_state="expanded")

# CSS (Bordi rinforzati e font grassetto)
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .player-card { padding: 12px; border-radius: 10px; margin-bottom: 12px; border: 3px solid #333; box-shadow: 4px 4px 8px rgba(0,0,0,0.2); color: black; }
    .refund-box { background-color: #e8f5e9; padding: 15px; border-radius: 10px; border: 3px solid #2e7d32; color: #1b5e20; margin-bottom: 10px; border: 2px solid #2e7d32; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO ---
def color_ruoli(row):
    r = str(row.get('RUOLO', row.get('Ruolo', ''))).upper()
    if 'POR' in r or r == 'P': bg = '#FCE4EC'
    elif 'DIF' in r or r == 'D': bg = '#E8F5E9'
    elif 'CEN' in r or r == 'C': bg = '#E3F2FD'
    elif 'ATT' in r or r == 'A': bg = '#FFFDE7'
    else: bg = '#FFFFFF'
    return [f'background-color: {bg}; color: black; font-weight: 900; border: 1px solid #ddd;'] * len(row)

def super_clean_match(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items(): name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    mapping = {'ZAMBO ANGUISSA': 'ANGUISSA', 'MARTINEZ L.': 'LAUTARO', 'PAZ N.': 'NICO PAZ', 'CASTELLANOS T.': 'CASTELLANOS', 'MARTINELLI T.': 'MARTINELLI'}
    if name in mapping: return mapping[name]
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

# --- ELABORAZIONE ---
if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(lambda x: str(x).upper().strip()).replace(map_n)
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean_match)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

# Caricamento database partenti persistente
if os.path.exists(FILE_PARTENTI):
    df_partenti_fisso = pd.read_csv(FILE_PARTENTI)
else:
    df_partenti_fisso = pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "RUOLO", "ASTA", "QUOT.", "VINCOLO", "RIMBORSO"])

rimborsi_squadre = df_partenti_fisso.groupby("SQUADRA")["RIMBORSO"].sum().to_dict() if not df_partenti_fisso.empty else {}

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🆕 **RIMBORSO PER CESSIONE**"])

# --- TAB 6: RIMBORSO PER CESSIONE ---
with t[6]:
    st.subheader("🚀 **REGISTRAZIONE GIOCATORI USCITI DALLA SERIE A**")
    st.info("Utilizza questa pagina per 'congelare' il rimborso prima di eliminare il giocatore dal file rose.")
    
    if f_rs is not None:
        c1, c2 = st.columns([3, 1])
        with c1:
            scelta = st.selectbox("Seleziona il giocatore partente:", [""] + sorted(f_rs['Nome'].unique()))
        with c2:
            if st.button("✅ REGISTRA USCITA") and scelta != "":
                if scelta not in df_partenti_fisso['GIOCATORE'].values:
                    info = f_rs[f_rs['Nome'] == scelta].iloc[0]
                    v_match = f_vn[f_vn['Giocatore_Match'] == super_clean_match(scelta)] if f_vn is not None else pd.DataFrame()
                    vv = v_match['Tot_Vincolo'].iloc[0] if not v_match.empty else 0
                    rimborso = ((info['Prezzo_N'] + info['Quotazione']) * 0.5) + vv
                    
                    nuova_riga = pd.DataFrame([{
                        "GIOCATORE": scelta, "SQUADRA": info['Squadra_N'], "RUOLO": info['Ruolo'],
                        "ASTA": info['Prezzo_N'], "QUOT.": info['Quotazione'], "VINCOLO": vv, "RIMBORSO": rimborso
                    }])
                    df_partenti_fisso = pd.concat([df_partenti_fisso, nuova_riga], ignore_index=True)
                    df_partenti_fisso.to_csv(FILE_PARTENTI, index=False)
                    st.success(f"Rimborso per {scelta} salvato correttamente!")
                    st.rerun()
                else:
                    st.warning("Giocatore già registrato!")

    if not df_partenti_fisso.empty:
        st.markdown("### 📋 STORICO CESSIONI REGISTRATE")
        st.dataframe(df_partenti_fisso.style.apply(color_ruoli, axis=1).format({"ASTA":"{:g}", "QUOT.":"{:g}", "VINCOLO":"{:g}", "RIMBORSO":"{:g}"}), use_container_width=True, hide_index=True)
        
        if st.button("🗑️ RESETTA TUTTO (ATTENZIONE)"):
            if os.path.exists(FILE_PARTENTI): os.remove(FILE_PARTENTI)
            st.rerun()

# --- TAB 1: BUDGET (Sempre aggiornato) ---
with t[1]:
    if f_rs is not None:
        st.subheader("💰 **BUDGET E PATRIMONIO AGGIORNATO**")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI DISPONIBILI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO CESSIONI'] = bu['Squadra_N'].map(rimborsi_squadre).fillna(0)
        
        voci_sel = st.multiselect("Voci calcolo:", ['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISPONIBILI', 'RECUPERO CESSIONI'], default=['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISPONIBILI', 'RECUPERO CESSIONI'])
        bu['PATRIMONIO TOTALE'] = bu[voci_sel].sum(axis=1) if voci_sel else 0
        
        st.dataframe(bu[['Squadra_N'] + voci_sel + ['PATRIMONIO TOTALE']].sort_values("PATRIMONIO TOTALE", ascending=False).style\
            .background_gradient(cmap='YlOrRd', subset=['PATRIMONIO TOTALE'])\
            .format({c: "{:g}" for c in bu.columns if c != 'Squadra_N'})\
            .set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)

# ... (Le altre Tab restano come prima) ...

import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaLAB - Test Area", layout="wide", initial_sidebar_state="expanded")

# CSS ORIGINALE + STILI PER IL LAB
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; color: black; }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; text-align: center; }
    .refund-box { background-color: #e8f5e9; padding: 20px; border-radius: 10px; border-left: 5px solid #2e7d32; color: #1b5e20; margin-bottom: 20px; }
    .zero-tool { background-color: #ffebee; color: #c62828; padding: 15px; border-radius: 10px; border: 2px solid #c62828; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO ---
def super_clean_match(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items():
        name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    mapping = {'ZAMBO ANGUISSA': 'ANGUISSA', 'MARTINEZ L.': 'LAUTARO', 'PAZ N.': 'NICO PAZ'}
    if name in mapping: return mapping[name]
    return re.sub(r'\s[A-Z]\.$', '', name)

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None
    return s_str.upper()

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

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- ELABORAZIONE ---
if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean_match)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_match)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)

# --- SIDEBAR (Uguale alla Golden) ---
with st.sidebar:
    st.header("🔍 **RICERCA RAPIDA**")
    if f_rs is not None:
        scelte = st.multiselect("Cerca giocatore", sorted(f_rs['Nome'].unique()))
        for n in scelte:
            dr = f_rs[f_rs['Nome'] == n].iloc[0]
            r = str(dr['Ruolo']).upper()
            bg = '#FCE4EC' if 'POR' in r else '#E8F5E9' if 'DIF' in r else '#E3F2FD' if 'CEN' in r else '#FFFDE7' if 'ATT' in r else '#f1f3f4'
            st.markdown(f'<div class="player-card" style="background-color: {bg};"><b>{n}</b> ({dr["Squadra_N"]})<br>ASTA: {int(dr["Prezzo_N"])} | QUOT: {int(dr["Quotazione"])}</div>', unsafe_allow_html=True)

# --- MAIN APP ---
st.title("🧪 **MUYFANTAMANAGER - LAB AREA**")
t = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI", "✂️ TAGLI", "🆕 MERCATO GENNAIO"])

# ... (Le altre tab rimangono identiche alla Golden per riferimento) ...

with t[6]: # NUOVA TAB: MERCATO GENNAIO
    st.subheader("🚀 **CALCOLO RIMBORSI CALCIOMERCATO ESTERO**")
    st.info("Regola: Rimborso = 50% di (Quotazione + Prezzo Asta) + 100% dei Vincoli pagati.")

    if f_rs is not None:
        # 1. Selezione dei giocatori partenti
        tutti_i_nomi = sorted(f_rs['Nome'].unique())
        partenti = st.multiselect("**SELEZIONA I GIOCATORI CHE HANNO LASCIATO LA SERIE A:**", tutti_i_nomi)
        
        if partenti:
            dati_partenti = []
            
            for nome in partenti:
                # Dati dal listone/rose
                info = f_rs[f_rs['Nome'] == nome].iloc[0]
                squadra = info['Squadra_N']
                prezzo_asta = info['Prezzo_N']
                quotazione = info['Quotazione']
                
                # Dati dai vincoli
                v_match = f_vn[f_vn['Giocatore_Match'] == super_clean_match(nome)] if f_vn is not None else pd.DataFrame()
                valore_vincolo = v_match['Tot_Vincolo'].iloc[0] if not v_match.empty else 0
                
                # FORMULA: 50% di (Quotazione + Prezzo Asta) + 100% Vincolo
                rimborso = ((prezzo_asta + quotazione) * 0.5) + valore_vincolo
                
                dati_partenti.append({
                    "GIOCATORE": nome,
                    "FANTASQUADRA": squadra,
                    "ASTA": prezzo_asta,
                    "QUOT.": quotazione,
                    "VINCOLO": valore_vincolo,
                    "RIMBORSO TOT": rimborso
                })
            
            df_partenti = pd.DataFrame(dati_partenti)
            
            # Visualizzazione Lista Dettagliata
            st.markdown("### 📋 DETTAGLIO RIMBORSI SINGOLI")
            st.dataframe(df_partenti.style.format({
                "ASTA": "{:g}", "QUOT.": "{:g}", "VINCOLO": "{:g}", "RIMBORSO TOT": "{:g}"
            }).set_properties(**{'font-weight': '900'}), use_container_width=True, hide_index=True)
            
            # Visualizzazione Riepilogo per Squadra
            st.markdown("### 💰 TOTALE RECUPERATO PER SQUADRA")
            riepilogo_squadre = df_partenti.groupby("FANTASQUADRA")["RIMBORSO TOT"].sum().reset_index()
            riepilogo_squadre = riepilogo_squadre.sort_values("RIMBORSO TOT", ascending=False)
            
            cols = st.columns(len(riepilogo_squadre) if len(riepilogo_squadre) < 5 else 4)
            for i, row in riepilogo_squadre.iterrows():
                with cols[i % len(cols)]:
                    st.markdown(f"""
                    <div class="refund-box">
                        <small>{row['FANTASQUADRA']}</small><br>
                        <b style="font-size: 20px;">+{int(row['RIMBORSO TOT'])} crediti</b>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.dataframe(riepilogo_squadre.style.format({"RIMBORSO TOT": "{:g}"}).background_gradient(cmap="Greens"), use_container_width=True, hide_index=True)
        else:
            st.warning("Seleziona almeno un giocatore per vedere il calcolo del rimborso.")

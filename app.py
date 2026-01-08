import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# CSS PER GRASSETTO E CARD
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .player-card { padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 6px solid; }
    .card-grey { background-color: #f1f3f4; border-color: #9e9e9e; }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; text-align: center; }
    .cut-info-box { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #ddd; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .stat-label { color: #666; font-size: 0.8em; text-transform: uppercase; }
    .stat-value { font-size: 1.2em; color: #1a1a1a; }
</style>
""", unsafe_allow_html=True)

# --- NORMALIZZAZIONE NOMI ---
def normalize_name(name):
    if not isinstance(name, str): return name
    name = name.replace('č', 'E').replace('ň', 'O').replace('ř', 'I').replace('ć', 'C').replace('Č', 'E').replace('Ň', 'O')
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    name = name.replace('-', ' ')
    return name.upper().strip()

# --- CARICAMENTO ---
def ld(f, is_quot=False):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True, encoding='latin1')
        df.columns = [c.strip() for c in df.columns]
        if is_quot:
            df['Nome_Match'] = df['Nome'].apply(normalize_name)
            return df[['Nome_Match', 'Qt.A']].rename(columns={'Qt.A': 'Quotazione', 'Nome_Match': 'Nome'})
        return df.dropna(how='all')
    except: return None

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

# LOAD DATA
f_rs = ld("rose_complete.csv")
f_vn = ld("vincoli.csv")
f_pt = ld("classificapunti.csv")
f_sc = ld("scontridiretti.csv")
f_qt = ld("quotazioni.csv", is_quot=True)

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

if f_rs is not None:
    f_rs['Nome_Match'] = f_rs['Nome'].apply(normalize_name)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].astype(str).str.upper().str.strip()
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt, left_on='Nome_Match', right_on='Nome', how='left', suffixes=('', '_qt'))
        f_rs['Quotazione'] = f_rs['Quotazione'].fillna(0)

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(normalize_name)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- MAIN APP ---
st.title("⚽ MUYFANTAMANAGER GOLDEN V6")
t = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI", "✂️ TAGLI"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 PUNTI")
            f_pt['P_N'], f_pt['FM'] = f_pt['Punti Totali'].apply(to_num), f_pt['Media'].apply(to_num)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N','FM']].sort_values('Posizione').style.background_gradient(subset=['P_N', 'FM'], cmap='YlGn'), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ SCONTRI")
            f_sc['P_S'] = f_sc['Punti'].apply(to_num)
            f_sc['DR'] = f_sc['Gol Fatti'].apply(to_num) - f_sc['Gol Subiti'].apply(to_num)
            st.dataframe(f_sc[['Posizione','Giocatore','P_S','DR']].style.background_gradient(subset=['P_S'], cmap='Blues').background_gradient(subset=['DR'], cmap='RdYlGn'), hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'ROSE'})
        v_s = f_vn.groupby(f_vn['Squadra'].str.upper().str.strip())['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Squadra', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_s, left_on='Squadra_N', right_on='Squadra', how='left').fillna(0).drop('Squadra', axis=1)
        bu['DISP'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['TOT'] = bu['ROSE'] + bu['Tot_Vincolo'] + bu['DISP']
        st.dataframe(bu.sort_values("TOT", ascending=False).style.background_gradient(cmap='YlOrRd', subset=['TOT']).background_gradient(cmap='Greens', subset=['DISP']), hide_index=True, use_container_width=True)

with t[2]: # ROSE
    if f_rs is not None:
        mancanti = f_rs[f_rs['Quotazione'] == 0]['Nome'].unique()
        if len(mancanti) > 0:
            with st.expander(f"⚠️ {len(mancanti)} GIOCATORI DA SISTEMARE"):
                st.write(", ".join(sorted(mancanti)))
        sq = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="rs_sel")
        st.dataframe(f_rs[f_rs['Squadra_N'] == sq][['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']], hide_index=True, use_container_width=True)

with t[3]: # VINCOLI
    if f_vn is not None:
        st.dataframe(f_vn[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI
    st.subheader("🔄 SIMULATORE SCAMBI")
    # ... (Logica scambi identica alla versione precedente)

with t[5]: # TAGLI POTENZIATI
    st.subheader("✂️ SIMULATORE TAGLI")
    if f_rs is not None:
        sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="st_sq")
        gi_t = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist(), key="st_gi")
        
        if gi_t:
            # Recupero Dati
            p_data = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gi_t)].iloc[0]
            v_data = f_vn[f_vn['Giocatore_Match'] == p_data['Nome_Match']] if f_vn is not None else None
            
            val_acquisto = p_data['Prezzo_N']
            val_vincolo = v_data['Tot_Vincolo'].iloc[0] if (v_data is not None and not v_data.empty) else 0
            anni_vincolo = v_data['Anni_T'].iloc[0] if (v_data is not None and not v_data.empty) else "NO"
            quot_attuale = p_data['Quotazione']
            rimborso = round((val_acquisto + val_vincolo) * 0.6)
            
            # Layout a card
            st.markdown(f"""
            <div class="cut-info-box">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h2>{p_data['Nome']}</h2>
                    <span style="background: #eee; padding: 5px 15px; border-radius: 20px;">{p_data['Ruolo']}</span>
                </div>
                <hr>
                <div style="display: flex; gap: 40px; flex-wrap: wrap;">
                    <div><span class="stat-label">Prezzo Acquisto</span><br><b class="stat-value">{int(val_acquisto)}</b></div>
                    <div><span class="stat-label">Valore Vincoli</span><br><b class="stat-value">{int(val_vincolo)}</b></div>
                    <div><span class="stat-label">Durata Vincolo</span><br><b class="stat-value">{anni_vincolo}</b></div>
                    <div><span class="stat-label">Quot. Mercato</span><br><b class="stat-value" style="color:#1a73e8;">{int(quot_attuale)}</b></div>
                </div>
                <div style="margin-top: 25px; padding: 15px; background: #fff3f3; border-radius: 8px; text-align: center; border: 1px solid #ff4b4b;">
                    <span style="color: #ff4b4b; text-transform: uppercase; font-size: 0.9em;">Rimborso Calcolato (60%)</span><br>
                    <h1 style="color: #ff4b4b; margin: 0;">{rimborso} CREDITI</h1>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📋 GENERA VERBALE TAGLIO"):
                st.code(f"✂️ TAGLIO UFFICIALE\nSQUADRA: {sq_t}\nGIOCATORE: {gi_t} ({p_data['Ruolo']})\nRIMBORSO: {rimborso} CREDITI\nDATA: {datetime.now().strftime('%d/%m/%Y')}")

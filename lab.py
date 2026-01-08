import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# --- BLOCCO CSS DEFINITIVO (Neretto + Card + Colori Pastello) ---
st.markdown("""
<style>
    /* Forza Neretto 900 ovunque */
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame td, .stDataFrame th, p, div, span, label { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    
    /* Card e Box */
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .stat-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #333;
        text-align: center;
        box-shadow: 3px 3px 0px #333;
    }
    .refund-box-pastello {
        padding: 15px;
        border-radius: 12px;
        border: 3px solid #333;
        text-align: center;
        min-height: 135px;
        box-shadow: 4px 4px 0px #333;
        margin-bottom: 15px;
    }

    /* Palette Colori Pastello */
    .bg-azzurro { background-color: #E3F2FD !important; }
    .bg-verde   { background-color: #E8F5E9 !important; }
    .bg-rosa    { background-color: #FCE4EC !important; }
    .bg-giallo  { background-color: #FFFDE7 !important; }
    .bg-arancio { background-color: #FFF3E0 !important; }
    .bg-viola   { background-color: #F3E5F5 !important; }

    .text-ufficiale { color: #2e7d32 !important; }
    .text-probabile { color: #ed6c02 !important; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO ---
def bold_df(df):
    return df.style.set_properties(**{'font-weight': '900', 'color': 'black'})

def super_clean_match(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items(): name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    return re.sub(r'\s[A-Z]\.$', '', name)

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x' or str(val).strip() == '': return 0.0
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

if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].str.upper().str.strip().replace(map_n)
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean_match)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None: f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].str.upper().str.strip().replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_match)
    v_cols = [c for c in f_vn.columns if '202' in c]
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])
rimborsi_mercato = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 **RICERCA CALCIATORE**")
    if f_rs is not None:
        cerca_side = st.multiselect("**CERCA NELLA LEGA**", sorted(f_rs['Nome'].unique()))
        for n in cerca_side:
            d_g = f_rs[f_rs['Nome'] == n].iloc[0]
            st.markdown(f'''<div class="player-card" style="background-color:#fff;"><b>{n}</b> ({d_g['Squadra_N']})<br>ASTA: {int(d_g['Prezzo_N'])} | QUOT: {int(d_g['Quotazione'])}</div>''', unsafe_allow_html=True)

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

with t[2]: # TAB 2: ROSE POTENZIATA
    if f_rs is not None:
        st.subheader("🏃 DASHBOARD ROSE E STATISTICHE")
        sq_r = st.selectbox("**SELEZIONA SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="sq_rose_final")
        df_team = f_rs[f_rs['Squadra_N'] == sq_r].copy()

        # Layout statistiche (Senza Plus/Minus)
        s1, s2, s3 = st.columns(3)
        with s1: st.markdown(f'<div class="stat-card">👥 GIOCATORI<br><b style="font-size:1.5em;">{len(df_team)}</b></div>', unsafe_allow_html=True)
        with s2: st.markdown(f'<div class="stat-card" style="border-color:#1a73e8;">💰 TOT. ASTA<br><b style="font-size:1.5em; color:#1a73e8;">{int(df_team["Prezzo_N"].sum())}</b></div>', unsafe_allow_html=True)
        with s3: st.markdown(f'<div class="stat-card" style="border-color:#2e7d32;">📈 TOT. QUOT.<br><b style="font-size:1.5em; color:#2e7d32;">{int(df_team["Quotazione"].sum())}</b></div>', unsafe_allow_html=True)

        st.write("---")
        st.markdown("#### 📊 RIPARTIZIONE PER RUOLO")
        ruoli_order = ['POR', 'DIF', 'CEN', 'ATT']
        riassunto_data = []
        for r in ruoli_order:
            df_rep = df_team[df_team['Ruolo'] == r]
            riassunto_data.append({
                "RUOLO": r,
                "N°": len(df_rep),
                "SPESA ASTA": int(df_rep['Prezzo_N'].sum()),
                "VAL. ATTUALE": int(df_rep['Quotazione'].sum())
            })
        df_riassunto = pd.DataFrame(riassunto_data)
        st.dataframe(bold_df(df_riassunto), hide_index=True, use_container_width=True)

        st.write("---")
        st.markdown(f"#### 🏃 DETTAGLIO ROSA: {sq_r}")

        # Funzione colore tono su tono (Sfondo chiaro, testo scuro)
        def color_full_row(row):
            v = str(row['Ruolo']).upper()
            if 'POR' in v: 
                return ['background-color: #FCE4EC', 'background-color: #F8BBD0', 'background-color: #F48FB1', 'background-color: #F06292']
            if 'DIF' in v: 
                return ['background-color: #E8F5E9', 'background-color: #C8E6C9', 'background-color: #A5D6A7', 'background-color: #81C784']
            if 'CEN' in v: 
                return ['background-color: #E3F2FD', 'background-color: #BBDEFB', 'background-color: #90CAF9', 'background-color: #64B5F6']
            if 'ATT' in v: 
                return ['background-color: #FFFDE7', 'background-color: #FFF9C4', 'background-color: #FFF59D', 'background-color: #FFF176']
            return [''] * 4

        # Visualizzazione tabella con stili condizionali su più colonne
        st.dataframe(bold_df(df_team[['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']]).apply(color_full_row, axis=1).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

# --- ALTRE TAB ---
# (Classifiche, Budget, Vincoli, Scambi, Tagli, Mercato rimangono come nella Golden stabile)
with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 PUNTI")
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            f_pt['FM'] = f_pt['Media'].apply(to_num) if 'Media' in f_pt.columns else 0.0
            st.dataframe(bold_df(f_pt[['Posizione','Giocatore','P_N','FM']].sort_values('Posizione')).background_gradient(subset=['P_N','FM'], cmap='YlGn').format({"P_N":"{:g}", "FM":"{:.2f}"}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ SCONTRI DIRETTI")
            for col in ['Punti', 'Gol Fatti', 'Gol Subiti']: f_sc[col] = f_sc[col].apply(to_num)
            f_sc['DR'] = f_sc['Gol Fatti'] - f_sc['Gol Subiti']
            st.dataframe(bold_df(f_sc[['Posizione','Giocatore','Punti','Gol Fatti','Gol Subiti','DR']].sort_values('Posizione')).background_gradient(subset=['Punti'], cmap='Blues').format({c: "{:g}" for c in ['Punti','Gol Fatti','Gol Subiti','DR']}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        rimborsi_uff = df_mercato[df_mercato['STATO'] == 'UFFICIALE'].groupby('SQUADRA')['TOTALE'].sum().to_dict()
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO UFF.'] = bu['Squadra_N'].map(rimborsi_uff).fillna(0)
        bu['TOTALE'] = bu[['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI', 'RECUPERO UFF.']].sum(axis=1)
        num_cols = bu.select_dtypes(include=['number']).columns
        st.dataframe(bold_df(bu.sort_values('TOTALE', ascending=False)).background_gradient(cmap='YlOrRd', subset=['TOTALE']).format({c: "{:g}" for c in num_cols}), hide_index=True, use_container_width=True)

with t[6]: # MERCATO (PASTELLO)
    st.subheader("🚀 MERCATO GENNAIO")
    with st.expander("➕ AGGIUNGI CESSIONE"):
        sc = st.selectbox("Seleziona:", [""] + sorted(f_rs['Nome'].unique()) if f_rs is not None else [""])
        if st.button("INSERISCI"):
            if sc != "" and sc not in df_mercato['GIOCATORE'].values:
                info = f_rs[f_rs['Nome'] == sc].iloc[0]
                vm_m = f_vn[f_vn['Giocatore_Match'] == super_clean_match(sc)] if f_vn is not None else pd.DataFrame()
                vv = vm_m['Tot_Vincolo'].iloc[0] if not vm_m.empty else 0
                nuova = pd.DataFrame([{"GIOCATORE": sc, "SQUADRA": info['Squadra_N'], "TOTALE": ((info['Prezzo_N'] + info['Quotazione'])*0.5)+vv, "STATO": "PROBABILE"}])
                df_mercato = pd.concat([df_mercato, nuova], ignore_index=True); df_mercato.to_csv(FILE_DB, index=False); st.rerun()
    if not df_mercato.empty:
        for idx, row in df_mercato.iterrows():
            mc1, mc2, mc3, mc4 = st.columns([2, 1, 1, 1])
            with mc1: st.write(f"**{row['GIOCATORE']}**")
            with mc2: st.write(f"RIMB: **{row['TOTALE']:g}**")
            with mc3: st.markdown(f"<span class=\"{'status-ufficiale' if row['STATO']=='UFFICIALE' else 'status-probabile'}\">{row['STATO']}</span>", unsafe_allow_html=True)
            with mc4:
                if row['STATO'] == "PROBABILE" and st.button("✅", key=f"u_{idx}"):
                    df_mercato.at[idx, 'STATO'] = "UFFICIALE"; df_mercato.to_csv(FILE_DB, index=False); st.rerun()
                if st.button("🗑️", key=f"d_{idx}"):
                    df_mercato = df_mercato.drop(idx).to_csv(FILE_DB, index=False); st.rerun()
        st.write("---")
        st.markdown("### 💰 **RECUPERO CREDITI PER SQUADRA**")
        colori_p = ["bg-azzurro", "bg-verde", "bg-rosa", "bg-giallo", "bg-arancio", "bg-viola"]
        sq_m = df_mercato.groupby(['SQUADRA', 'STATO'])['TOTALE'].sum().unstack(fill_value=0)
        if 'UFFICIALE' not in sq_m.columns: sq_m['UFFICIALE'] = 0
        if 'PROBABILE' not in sq_m.columns: sq_m['PROBABILE'] = 0
        sq_m['TOT_GEN'] = sq_m['UFFICIALE'] + sq_m['PROBABILE']
        cols_m = st.columns(4)
        for i, (sq_n, data) in enumerate(sq_m.sort_values('TOT_GEN', ascending=False).iterrows()):
            c_cl = colori_p[i % len(colori_p)]
            with cols_m[i % 4]:
                st.markdown(f'<div class="refund-box-pastello {c_cl}"><small>{sq_n}</small><br><b>+{data["TOT_GEN"]:g}</b><br><hr style="margin:5px 0; border:0; border-top:1px solid #ddd;"><span class="text-ufficiale">Uff: {data["UFFICIALE"]:g}</span><br><span class="text-probabile">Prob: {data["PROBABILE"]:g}</span></div>', unsafe_allow_html=True)
                

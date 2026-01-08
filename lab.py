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
    .refund-box { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 2px solid #333; margin-bottom: 10px; text-align: center; min-height: 120px; }
    .status-ufficiale { color: #2e7d32; font-weight: 900; }
    .status-probabile { color: #ed6c02; font-weight: 900; }
    .info-small { font-size: 0.8em; color: #666; font-weight: 400 !important; }
    .text-ufficiale { color: #2e7d32; font-size: 0.85em; }
    .text-probabile { color: #ed6c02; font-size: 0.85em; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO ---
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
f_rs, f_vn = ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)
FILE_DB = "mercatone_gennaio.csv"

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- ELABORAZIONE DATI ROSE E VINCOLI ---
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

# --- GESTIONE DATABASE MERCATO (CON RICALCOLO AUTO) ---
if os.path.exists(FILE_DB):
    df_mercato = pd.read_csv(FILE_DB)
    # Se il file ha righe ma Spesa/Quot sono a 0, proviamo a recuperarli
    if not df_mercato.empty and f_rs is not None:
        for i, row in df_mercato.iterrows():
            if row.get('SPESA', 0) == 0 or row.get('QUOT', 0) == 0:
                match = f_rs[f_rs['Nome'] == row['GIOCATORE']]
                if not match.empty:
                    spesa = match.iloc[0]['Prezzo_N']
                    quot = match.iloc[0]['Quotazione']
                    v_match = f_vn[f_vn['Giocatore_Match'] == super_clean_match(row['GIOCATORE'])] if f_vn is not None else pd.DataFrame()
                    vv = v_match['Tot_Vincolo'].iloc[0] if not v_match.empty else 0
                    rb = (spesa + quot) * 0.5
                    # Aggiorniamo la riga
                    df_mercato.at[i, 'SPESA'] = spesa
                    df_mercato.at[i, 'QUOT'] = quot
                    df_mercato.at[i, 'RIMB_BASE'] = rb
                    df_mercato.at[i, 'VINCOLO'] = vv
                    df_mercato.at[i, 'TOTALE'] = rb + vv
else:
    df_mercato = pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "SPESA", "QUOT", "RIMB_BASE", "VINCOLO", "TOTALE", "STATO"])

rimborsi_squadre_tot = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- SIDEBAR E TABS ---
with st.sidebar:
    st.header("🔍 **RICERCA GIOCATORE**")
    if f_rs is not None:
        cerca = st.multiselect("Cerca nella lega:", sorted(f_rs['Nome'].unique()))
        for n in cerca:
            dr = f_rs[f_rs['Nome'] == n].iloc[0]
            st.markdown(f'<div class="player-card" style="background-color: #f1f3f4;"><b>{n}</b> ({dr["Squadra_N"]})<br>ASTA: {int(dr["Prezzo_N"])} | QUOT: {int(dr["Quotazione"])}</div>', unsafe_allow_html=True)

t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🆕 **RIMBORSO CESSIONI**"])

with t[6]: # RIMBORSO CESSIONI
    st.subheader("🚀 **LISTA MOVIMENTI GENNAIO**")
    with st.expander("➕ AGGIUNGI GIOCATORE ALLA LISTA"):
        scelta = st.selectbox("Seleziona giocatore:", [""] + sorted(f_rs['Nome'].unique()) if f_rs is not None else [""])
        if st.button("INSERISCI IN LISTA"):
            if scelta != "" and scelta not in df_mercato['GIOCATORE'].values:
                info = f_rs[f_rs['Nome'] == scelta].iloc[0]
                v_match = f_vn[f_vn['Giocatore_Match'] == super_clean_match(scelta)] if f_vn is not None else pd.DataFrame()
                vv = v_match['Tot_Vincolo'].iloc[0] if not v_match.empty else 0
                spesa, quot = info['Prezzo_N'], info['Quotazione']
                rb = (spesa + quot) * 0.5
                nuova = pd.DataFrame([{"GIOCATORE": scelta, "SQUADRA": info['Squadra_N'], "SPESA": spesa, "QUOT": quot, "RIMB_BASE": rb, "VINCOLO": vv, "TOTALE": rb+vv, "STATO": "PROBABILE"}])
                df_mercato = pd.concat([df_mercato, nuova], ignore_index=True)
                df_mercato.to_csv(FILE_DB, index=False); st.rerun()

    if not df_mercato.empty:
        st.write("---")
        h1, h2, h3, h4, h5, h6 = st.columns([2, 1, 1, 2, 1, 1])
        h1.write("**GIOCATORE**"); h2.write("**SPESA**"); h3.write("**QUOT**"); h4.write("**DETTAGLIO**"); h5.write("**TOTALE**"); h6.write("**STATO**")
        for i, row in df_mercato.iterrows():
            c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 1, 2, 1, 1])
            with c1: st.markdown(f"**{row['GIOCATORE']}**<br><small>{row['SQUADRA']}</small>", unsafe_allow_html=True)
            with c2: st.write(f"{row['SPESA']:g}")
            with c3: st.write(f"{row['QUOT']:g}")
            with c4: st.markdown(f"<span class='info-small'>50%: {row['RIMB_BASE']:g} + Vinc: {row['VINCOLO']:g}</span>", unsafe_allow_html=True)
            with c5: st.write(f"**{row['TOTALE']:g}**")
            with c6:
                cl = "status-ufficiale" if row['STATO'] == "UFFICIALE" else "status-probabile"
                st.markdown(f"<span class='{cl}'>{row['STATO']}</span>", unsafe_allow_html=True)
                s1, s2 = st.columns(2)
                if row['STATO'] == "PROBABILE" and s1.button("✅", key=f"u_{i}"):
                    df_mercato.at[i, 'STATO'] = "UFFICIALE"; df_mercato.to_csv(FILE_DB, index=False); st.rerun()
                if s2.button("🗑️", key=f"d_{i}"):
                    df_mercato = df_mercato.drop(i); df_mercato.to_csv(FILE_DB, index=False); st.rerun()

# --- TAB 1: BUDGET ---
with t[1]:
    if f_rs is not None:
        st.subheader("💰 **BUDGET AGGIORNATO**")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI DISPONIBILI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO CESSIONI'] = bu['Squadra_N'].map(rimborsi_squadre_tot).fillna(0)
        bu['PATRIMONIO TOTALE'] = bu[['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISPONIBILI', 'RECUPERO CESSIONI']].sum(axis=1)
        st.dataframe(bu.sort_values("PATRIMONIO TOTALE", ascending=False).style.background_gradient(cmap='YlOrRd', subset=['PATRIMONIO TOTALE']).format({c: "{:g}" for c in bu.columns if c != 'Squadra_N'}), hide_index=True, use_container_width=True)

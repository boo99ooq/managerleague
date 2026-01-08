import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# CSS: Neretto estremo ovunque e stili card
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame, td, th { 
        font-weight: 900 !important; 
        color: #000 !important;
    }
    .player-card { padding: 12px; border-radius: 10px; margin-bottom: 12px; border: 3px solid #333; box-shadow: 4px 4px 8px rgba(0,0,0,0.2); }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; text-align: center; border: 3px solid #1a73e8; }
    .punto-incontro-box { background-color: #fff3e0; padding: 8px 25px; border-radius: 12px; border: 3px solid #ff9800; text-align: center; width: fit-content; margin: auto; }
    .cut-box { background-color: #fdfdfd; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; }
    .cut-player-name { font-size: 3.2em; color: #d32f2f; text-transform: uppercase; line-height: 1; margin-bottom: 10px; }
    .cut-refund-value { font-size: 1.8em; color: #2e7d32; background: #e8f5e9; padding: 10px 20px; border-radius: 8px; display: inline-block; border: 2px solid #2e7d32; }
    .refund-box { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 3px solid #333; text-align: center; min-height: 120px; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def super_clean_match(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items(): name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    mapping = {'ZAMBO ANGUISSA': 'ANGUISSA', 'MARTINEZ L.': 'LAUTARO', 'PAZ N.': 'NICO PAZ'}
    return mapping.get(name, re.sub(r'\s[A-Z]\.$', '', name))

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
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean_match)
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

rimborsi_squadre_tot = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- FUNZIONE FORMATTAZIONE NERETTO TABELLE ---
def bold_df(df):
    return df.style.set_properties(**{'font-weight': '900'})

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num); f_pt['FM'] = f_pt['Media'].apply(to_num)
            st.dataframe(bold_df(f_pt[['Posizione','Giocatore','P_N','FM']].sort_values('Posizione')).background_gradient(subset=['P_N','FM'], cmap='YlGn').format({"P_N":"{:g}", "FM":"{:g}"}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            f_sc['P_S'] = f_sc['Punti'].apply(to_num); f_sc['GF'] = f_sc['Gol Fatti'].apply(to_num); f_sc['GS'] = f_sc['Gol Subiti'].apply(to_num); f_sc['DR'] = f_sc['GF'] - f_sc['GS']
            st.dataframe(bold_df(f_sc[['Posizione','Giocatore','P_S','GF','GS','DR']].sort_values('Posizione')).background_gradient(subset=['P_S'], cmap='Blues').format({"P_S":"{:g}","GF":"{:g}","GS":"{:g}","DR":"{:g}"}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI DISPONIBILI'] = bu['Squadra_N'].map(bg_ex).fillna(0); bu['RECUPERO CESSIONI'] = bu['Squadra_N'].map(rimborsi_squadre_tot).fillna(0)
        voci = ['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISPONIBILI', 'RECUPERO CESSIONI']
        sel = st.multiselect("**FILTRA VOCI:**", voci, default=voci)
        bu['PATRIMONIO'] = bu[sel].sum(axis=1)
        st.dataframe(bold_df(bu[['Squadra_N'] + sel + ['PATRIMONIO']].sort_values("PATRIMONIO", ascending=False)).background_gradient(cmap='YlOrRd', subset=['PATRIMONIO']).format({c: "{:g}" for c in bu.columns if c != 'Squadra_N'}), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI
    st.subheader("🔄 SIMULATORE SCAMBI GOLDEN")
    if f_rs is not None:
        sc1, sc2 = st.columns(2); lista_sq = sorted(f_rs['Squadra_N'].unique())
        with sc1: sa = st.selectbox("SQUADRA A", lista_sq, key="sa_sc"); ga = st.multiselect("DA A", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist(), key="ga_sc")
        with sc2: sb = st.selectbox("SQUADRA B", [s for s in lista_sq if s!=sa], key="sb_sc"); gb = st.multiselect("DA B", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist(), key="gb_sc")
        if ga and gb:
            def get_i(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]
                vm = f_vn[f_vn['Giocatore_Match']==super_clean_match(n)] if f_vn is not None else pd.DataFrame()
                v = vm['Tot_Vincolo'].iloc[0] if not vm.empty else 0
                return {'t': p+v, 'v': v}
            da, db = {n: get_i(n) for n in ga}, {n: get_i(n) for n in gb}
            ta, tb = sum(d['t'] for d in da.values()), sum(d['t'] for d in db.values()); nt = round((ta+tb)/2)
            gap = ta - tb; col_g = "#d32f2f" if gap > 0 else "#2e7d32" if gap < 0 else "#333"
            st.markdown(f'<div class="punto-incontro-box"><b style="color:{col_g};">GAP: {gap:g}</b><br><small>Media: {nt:g}</small></div>', unsafe_allow_html=True)
            r1, r2 = st.columns(2)
            with r1:
                for n, i in db.items():
                    nt_i = round((i['t']/tb)*nt) if tb>0 else nt
                    st.markdown(f'<div class="player-card" style="background-color:#e3f2fd; border:3px solid #1e88e5;"><b>{n}</b><br><small>NUOVA VAL: {max(0, nt_i-int(i["v"])):g} + {i["v"]:g} (VINC)</small></div>', unsafe_allow_html=True)
            with r2:
                for n, i in da.items():
                    nt_i = round((i['t']/ta)*nt) if ta>0 else nt
                    st.markdown(f'<div class="player-card" style="background-color:#fbe9e7; border:3px solid #e53935;"><b>{n}</b><br><small>NUOVA VAL: {max(0, nt_i-int(i["v"])):g} + {i["v"]:g} (VINC)</small></div>', unsafe_allow_html=True)

with t[5]: # TAGLI (FIXED INDEX ERROR)
    st.subheader("✂️ TAGLI GOLDEN")
    if f_rs is not None:
        sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="sq_t")
        gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist(), key="gioc_t")
        if gt:
            v_a = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gt)]['Prezzo_N'].iloc[0]
            # FIX: Controllo se il DataFrame dei vincoli è vuoto prima di accedere a .iloc[0]
            vm = f_vn[f_vn['Giocatore_Match'] == super_clean_match(gt)] if f_vn is not None else pd.DataFrame()
            v_v = vm['Tot_Vincolo'].iloc[0] if not vm.empty else 0
            rimb = round((v_a + v_v) * 0.6)
            st.markdown(f'''<div class="cut-box"><div class="cut-player-name">{gt}</div><div class="cut-refund-value">RIMBORSO: {rimb:g} CREDITI</div><br><br>ASTA: {v_a:g} | VINCOLI: {v_v:g}</div>''', unsafe_allow_html=True)

with t[6]: # MERCATO CESSIONI
    st.subheader("🚀 MERCATO CESSIONI GENNAIO")
    with st.expander("➕ AGGIUNGI CESSIONE"):
        sc = st.selectbox("Seleziona:", [""] + sorted(f_rs['Nome'].unique()) if f_rs is not None else [""])
        if st.button("INSERISCI"):
            if sc != "" and sc not in df_mercato['GIOCATORE'].values:
                info = f_rs[f_rs['Nome'] == sc].iloc[0]
                vm_m = f_vn[f_vn['Giocatore_Match'] == super_clean_match(sc)] if f_vn is not None else pd.DataFrame()
                vv_m = vm_m['Tot_Vincolo'].iloc[0] if not vm_m.empty else 0
                s, q = info['Prezzo_N'], info['Quotazione']; rb = (s + q) * 0.5
                nuova = pd.DataFrame([{"GIOCATORE": sc, "SQUADRA": info['Squadra_N'], "SPESA": s, "QUOT": q, "RIMB_BASE": rb, "VINCOLO": vv_m, "TOTALE": rb+vv_m, "STATO": "PROBABILE"}])
                df_mercato = pd.concat([df_mercato, nuova], ignore_index=True); df_mercato.to_csv(FILE_DB, index=False); st.rerun()
    if not df_mercato.empty:
        st.write("---"); h1, h2, h3, h4, h5, h6 = st.columns([2, 1, 1, 2, 1, 1])
        h1.write("**NOME**"); h2.write("**SPESA**"); h3.write("**QUOT**"); h4.write("**DETTAGLIO**"); h5.write("**TOT**"); h6.write("**STATO**")
        for idx, row in df_mercato.iterrows():
            c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 1, 2, 1, 1])
            with c1: st.markdown(f"**{row['GIOCATORE']}**<br><small>{row['SQUADRA']}</small>", unsafe_allow_html=True)
            with c2: st.write(f"{row['SPESA']:g}"); with c3: st.write(f"{row['QUOT']:g}")
            with c4: st.markdown(f"<small>50%:{row['RIMB_BASE']:g}+V:{row['VINCOLO']:g}</small>", unsafe_allow_html=True)
            with c5: st.write(f"**{row['TOTALE']:g}**")
            with c6:
                cl = "status-ufficiale" if row['STATO'] == "UFFICIALE" else "status-probabile"
                st.markdown(f"<span class='{cl}'>{row['STATO']}</span>", unsafe_allow_html=True)
                sc1, sc2 = st.columns(2)
                if row['STATO'] == "PROBABILE" and sc1.button("✅", key=f"u_{idx}"): df_mercato.at[idx, 'STATO'] = "UFFICIALE"; df_mercato.to_csv(FILE_DB, index=False); st.rerun()
                if sc2.button("🗑️", key=f"d_{idx}"): df_mercato = df_mercato.drop(idx); df_mercato.to_csv(FILE_DB, index=False); st.rerun()

import streamlit as st
import pandas as pd
import os
import altair as alt

# 1. SETUP E STILE
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager")

# Configurazione Budget e Mappature
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "NICHO:79": "NICHOLAS"}
map_r = {"P": "PORTIERE", "D": "DIFENSORE", "C": "CENTROCAMPISTA", "A": "ATTACCANTE"}

def cv(v):
    if pd.isna(v): return 0.0
    try:
        s = str(v).replace('"', '').replace(',', '.').strip()
        return float(s) if s != "" else 0.0
    except: return 0.0

def clean_name(s):
    if pd.isna(s) or str(s).strip().upper() == "NONE" or str(s).strip() == "": return "SKIP"
    s = str(s).split(':')[0].replace('*', '').replace('"', '').strip().upper()
    return map_n.get(s, s)

def clean_role(r):
    if pd.isna(r): return "NONE"
    r = str(r).strip().upper()
    return map_r.get(r, r)

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, sep=',', engine='python', encoding='utf-8-sig', skip_blank_lines=True)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# 2. CARICAMENTO E PULIZIA
f_sc, f_pt, f_rs, f_vn, f_qt = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv"), ld("quotazioni.csv")

if f_rs is not None:
    f_rs['Nome'] = f_rs['Nome'].apply(clean_name)
    f_rs['Ruolo'] = f_rs['Ruolo'].apply(clean_role)
    f_rs['Fantasquadra'] = f_rs['Fantasquadra'].apply(clean_name)
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)

if f_qt is not None:
    f_qt = f_qt.rename(columns={'R': 'Ruolo_QT', 'Nome': 'Nome_QT', 'Qt.A': 'Quotazione'})
    f_qt['Nome_QT'] = f_qt['Nome_QT'].apply(clean_name)
    f_qt['Ruolo_QT'] = f_qt['Ruolo_QT'].apply(clean_role)
    f_qt['Quotazione'] = f_qt['Quotazione'].apply(cv)

if f_vn is not None:
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_name)
    f_vn['Squadra'] = f_vn['Squadra'].apply(clean_name)
    for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29']:
        if c in f_vn.columns: f_vn[c] = f_vn[c].apply(cv)
    f_vn['Spesa Complessiva'] = f_vn.get('Costo 2026-27', 0) + f_vn.get('Costo 2027-28', 0) + f_vn.get('Costo 2028-29', 0)

# 3. UNIONE DATI (PLUSVALENZE)
if f_rs is not None and f_qt is not None:
    f_rs = pd.merge(f_rs, f_qt[['Nome_QT', 'Ruolo_QT', 'Quotazione']], left_on=['Nome', 'Ruolo'], right_on=['Nome_QT', 'Ruolo_QT'], how='left')
    f_rs['Plusvalenza'] = f_rs['Quotazione'] - f_rs['Prezzo']

def style_rose(row):
    colors = {'PORTIERE':'#E3F2FD','DIFENSORE':'#E8F5E9','CENTROCAMPISTA':'#FFFDE7','ATTACCANTE':'#FFEBEE'}
    return [f'background-color: {colors.get(row["Ruolo"], "#FFFFFF")}; color: black; font-weight: bold;'] * len(row)

# 4. TABS
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_sc is not None:
        with c1:
            st.subheader("🔥 Scontri")
            st.dataframe(f_sc, hide_index=True, use_container_width=True)
    if f_pt is not None:
        with c2:
            st.subheader("🎯 Punti")
            f_pt['Punti Totali'] = f_pt['Punti Totali'].apply(cv)
            st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali']].sort_values('Posizione').style.background_gradient(subset=['Punti Totali'], cmap='Greens'), hide_index=True, use_container_width=True)

with t[1]: # BUDGET (FIX KEYERROR)
    if f_rs is not None:
        st.subheader("💰 Bilancio e Valore Rosa")
        # Controllo se la colonna Quotazione esiste dopo il merge
        agg_dict = {'Prezzo': 'sum'}
        if 'Quotazione' in f_rs.columns:
            agg_dict['Quotazione'] = 'sum'
            
        eco = f_rs.groupby('Fantasquadra').agg(agg_dict).reset_index()
        eco.columns = ['Fantasquadra', 'Investimento'] + (['Valore Mercato'] if 'Quotazione' in agg_dict else [])
        
        eco['Crediti Disponibili'] = eco['Fantasquadra'].map(bg_ex).fillna(0)
        if f_vn is not None:
            v_sum = f_vn.groupby('Squadra')['Spesa Complessiva'].sum().reset_index()
            v_sum.columns = ['Fantasquadra', 'Vincoli']
            eco = pd.merge(eco, v_sum, on='Fantasquadra', how='left').fillna(0)
        
        col_somma = 'Valore Mercato' if 'Valore Mercato' in eco.columns else 'Investimento'
        eco['Patrimonio'] = eco[col_somma] + eco['Crediti Disponibili'] + eco.get('Vincoli', 0)
        
        st.dataframe(eco.sort_values('Patrimonio', ascending=False).style.format({c: "{:g}" for c in eco.columns if c != 'Fantasquadra'}), hide_index=True, use_container_width=True)

with t[2]: # STRATEGIA
    if f_rs is not None:
        st.subheader("🧠 Strategia e Numero Giocatori")
        piv = f_rs.pivot_table(index='Fantasquadra', columns='Ruolo', values='Nome', aggfunc='count').fillna(0).astype(int)
        st.dataframe(piv, use_container_width=True)

with t[3]: # ROSE
    if f_rs is not None:
        sq_l = sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"])
        sq = st.selectbox("Seleziona Squadra:", sq_l, key="rose_sel")
        df_sq = f_rs[f_rs['Fantasquadra'] == sq].copy()
        
        cols_view = ['Ruolo', 'Nome', 'Prezzo']
        if 'Quotazione' in df_sq.columns:
            cols_view += ['Quotazione', 'Plusvalenza']
            st.dataframe(df_sq[cols_view].style.apply(style_rose, axis=1).format({"Prezzo": "{:g}", "Quotazione": "{:g}", "Plusvalenza": "{:+g}"}), hide_index=True, use_container_width=True)
            st.metric("Plusvalenza Rosa", f"{df_sq['Plusvalenza'].sum():+g}")
        else:
            st.dataframe(df_sq[cols_view].style.apply(style_rose, axis=1).format({"Prezzo": "{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 Dettaglio Vincoli Pluriennali")
        sv = st.selectbox("Squadra:", sorted(f_vn['Squadra'].unique()), key="v_sel")
        st.dataframe(f_vn[f_vn['Squadra']==sv].drop(columns=['Squadra']), hide_index=True, use_container_width=True)

with t[5]: # SCAMBI (LOGICA MERITOCRATICA)
    st.subheader("🔄 Simulatore Scambi Proporzionale")
    if f_rs is not None:
        sq_l = sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"])
        
        def get_details(lista_nomi):
            dati = []
            for n in lista_nomi:
                p = f_rs[f_rs['Nome'] == n]['Prezzo'].values[0]
                v = f_vn[f_vn['Giocatore'] == n]['Spesa Complessiva'].values[0] if (f_vn is not None and n in f_vn['Giocatore'].values) else 0.0
                dati.append({'Giocatore': n, 'Totale': p + v, 'Vincolo': v})
            return pd.DataFrame(dati)

        c1, c2 = st.columns(2)
        with c1:
            sa = st.selectbox("Squadra A:", sq_l, key="sa_f")
            ga = st.multiselect("Cede da A:", f_rs[f_rs['Fantasquadra']==sa]['Nome'], key="ga_f")
            df_a = get_details(ga)
        with c2:
            sb = st.selectbox("Squadra B:", [s for s in sq_l if s != sa], key="sb_f")
            gb = st.multiselect("Cede da B:", f_rs[f_rs['Fantasquadra']==sb]['Nome'], key="gb_f")
            df_b = get_details(gb)

        if not df_a.empty and not df_b.empty:
            v_a, v_b = df_a['Totale'].sum(), df_b['Totale'].sum()
            coeff_a, coeff_b = ((v_a+v_b)/2)/v_a, ((v_a+v_b)/2)/v_b
            
            st.write("---")
            st.markdown("#### ✅ Nuovi Valori Calcolati")
            res1, res2 = st.columns(2)
            with res1:
                for _, r in df_a.iterrows():
                    nt = round(r['Totale'] * coeff_a)
                    st.success(f"🔹 {r['Giocatore']}: **{nt}** (Cart: {nt-r['Vincolo']} + Vinc: {r['Vincolo']})")
            with res2:
                for _, r in df_b.iterrows():
                    nt = round(r['Totale'] * coeff_b)
                    st.success(f"🔸 {r['Giocatore']}: **{nt}** (Cart: {nt-r['Vincolo']} + Vinc: {r['Vincolo']})")

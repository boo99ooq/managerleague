import streamlit as st
import pandas as pd
import os
import altair as alt

# 1. SETUP E STILE (RIPRISTINO GOLDEN UI)
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
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS"}
map_r = {"P": "PORTIERE", "D": "DIFENSORE", "C": "CENTROCAMPISTA", "A": "ATTACCANTE"}

# --- UTILITY ---
def cv(v):
    if pd.isna(v): return 0.0
    try:
        s = str(v).replace('"', '').replace(',', '.').strip()
        return float(s) if s != "" else 0.0
    except: return 0.0

def clean_text(s):
    if pd.isna(s): return ""
    s = str(s).upper().replace('-', ' ').replace('.', '').strip()
    return " ".join(s.split())

def get_match_key(name):
    """Prende solo la prima parola (il cognome) per un match sicuro tra file diversi"""
    s = clean_text(name)
    return s.split()[0] if s else ""

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, sep=',', engine='python', encoding='utf-8-sig', skip_blank_lines=True)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# --- CARICAMENTO ---
f_rs, f_vn, f_qt = ld("rose_complete.csv"), ld("vincoli.csv"), ld("quotazioni.csv")
f_sc, f_pt = ld("scontridiretti.csv"), ld("classificapunti.csv")

# --- ELABORAZIONE DATI ---
if f_rs is not None:
    f_rs['Nome_Match'] = f_rs['Nome'].apply(get_match_key)
    f_rs['Ruolo_Clean'] = f_rs['Ruolo'].apply(lambda x: map_r.get(str(x)[0].upper(), clean_text(x)))
    f_rs['Fantasquadra'] = f_rs['Fantasquadra'].apply(clean_text).replace(map_n)
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)

    if f_qt is not None:
        f_qt['Nome_Match'] = f_qt['Nome'].apply(get_match_key)
        f_qt['Ruolo_Match'] = f_qt['R'].map(map_r)
        f_qt['Quotazione'] = f_qt['Qt.A'].apply(cv)
        # Unione (Merge)
        f_rs = pd.merge(f_rs, f_qt[['Nome_Match', 'Ruolo_Match', 'Quotazione']], 
                        left_on=['Nome_Match', 'Ruolo_Clean'], right_on=['Nome_Match', 'Ruolo_Match'], 
                        how='left').drop('Ruolo_Match', axis=1)
        f_rs['Quotazione'] = f_rs['Quotazione'].fillna(0)
        f_rs['Plusvalenza'] = f_rs['Quotazione'] - f_rs['Prezzo']

if f_vn is not None:
    f_vn['Squadra'] = f_vn['Squadra'].apply(clean_text).replace(map_n)
    v_cols = [c for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29'] if c in f_vn.columns]
    for c in v_cols: f_vn[c] = f_vn[c].apply(cv)
    f_vn['Spesa Complessiva'] = f_vn[v_cols].sum(axis=1)

# --- UI TABS ---
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

with t[0]: # CLASSIFICHE + GRAFICO ZOOM
    c1, c2 = st.columns(2)
    if f_sc is not None:
        with c1: st.subheader("🔥 Scontri"); st.dataframe(f_sc.style.set_properties(**{'font-weight': 'bold'}), hide_index=True)
    if f_pt is not None:
        with c2:
            st.subheader("🎯 Punti")
            f_pt['Punti Totali'] = f_pt['Punti Totali'].apply(cv)
            st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali']].sort_values('Posizione').style.background_gradient(subset=['Punti Totali'], cmap='Greens'), hide_index=True)
        # Grafico Zoom
        p_min, p_max = f_pt['Punti Totali'].min() - 10, f_pt['Punti Totali'].max() + 10
        chart = alt.Chart(f_pt).mark_line(point=True, color='green').encode(
            x=alt.X('Giocatore:N', sort='-y'), y=alt.Y('Punti Totali:Q', scale=alt.Scale(domain=[p_min, p_max]))
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)

with t[1]: # BUDGET + GRAFICO BARRE
    if f_rs is not None:
        st.subheader("💰 Situazione Finanziaria")
        eco = f_rs.groupby('Fantasquadra').agg({'Prezzo': 'sum', 'Quotazione': 'sum'}).reset_index()
        eco.columns = ['Squadra', 'Spesa Rose', 'Valore Mercato']
        eco['Crediti'] = eco['Squadra'].map(bg_ex).fillna(0)
        if f_vn is not None:
            v_sum = f_vn.groupby('Squadra')['Spesa Complessiva'].sum().reset_index()
            eco = pd.merge(eco, v_sum, left_on='Squadra', right_on='Squadra', how='left').fillna(0)
            eco.rename(columns={'Spesa Complessiva': 'Vincoli'}, inplace=True)
        eco['Patrimonio'] = eco['Valore Mercato'] + eco['Crediti'] + eco.get('Vincoli', 0)
        
        st.dataframe(eco.sort_values('Patrimonio', ascending=False).style.background_gradient(subset=['Valore Mercato'], cmap='YlGn').format({c: "{:g}" for c in eco.columns if c != 'Squadra'}), hide_index=True, use_container_width=True)
        
        # Grafico Barre Impilate
        eco_melt = eco.melt(id_vars='Squadra', value_vars=['Valore Mercato', 'Crediti', 'Vincoli'])
        st.altair_chart(alt.Chart(eco_melt).mark_bar().encode(
            y=alt.Y('Squadra:N', sort='-x'), x='sum(value):Q', color='variable:N'
        ).properties(height=400), use_container_width=True)

with t[3]: # ROSE COLORATE E PLUSVALENZE
    if f_rs is not None:
        sq = st.selectbox("Seleziona Squadra:", sorted(f_rs['Fantasquadra'].unique()))
        df_sq = f_rs[f_rs['Fantasquadra'] == sq].copy()
        
        def color_ruoli(row):
            bg = {'PORTIERE':'#E3F2FD','DIFENSORE':'#E8F5E9','CENTROCAMPISTA':'#FFFDE7','ATTACCANTE':'#FFEBEE'}.get(row['Ruolo_Clean'], '#FFFFFF')
            return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)
            
        st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo', 'Quotazione', 'Plusvalenza']].style.apply(color_ruoli, axis=1).background_gradient(subset=['Plusvalenza'], cmap='RdYlGn').format({"Prezzo":"{:g}","Quotazione":"{:g}","Plusvalenza":"{:+g}"}), hide_index=True, use_container_width=True)
        st.metric("Plusvalenza Rosa", f"{df_sq['Plusvalenza'].sum():+g}")

with t[5]: # SCAMBI MERITOCRATICI
    st.subheader("🔄 Simulatore Scambi Proporzionale")
    if f_rs is not None:
        c1, c2 = st.columns(2)
        with c1:
            sa = st.selectbox("Squadra A:", sorted(f_rs['Fantasquadra'].unique()), key="sa")
            ga = st.multiselect("Cede da A:", f_rs[f_rs['Fantasquadra']==sa]['Nome'], key="ga")
            val_a = sum([f_rs[f_rs['Nome']==n]['Prezzo'].iloc[0] + (f_vn[f_vn['Giocatore'].apply(clean_text)==clean_text(n)]['Spesa Complessiva'].sum() if f_vn is not None else 0) for n in ga])
        with c2:
            sb = st.selectbox("Squadra B:", [s for s in sorted(f_rs['Fantasquadra'].unique()) if s != sa], key="sb")
            gb = st.multiselect("Cede da B:", f_rs[f_rs['Fantasquadra']==sb]['Nome'], key="gb")
            val_b = sum([f_rs[f_rs['Nome']==n]['Prezzo'].iloc[0] + (f_vn[f_vn['Giocatore'].apply(clean_text)==clean_text(n)]['Spesa Complessiva'].sum() if f_vn is not None else 0) for n in gb])
        
        if ga and gb:
            coeff_a, coeff_b = ((val_a+val_b)/2)/val_a, ((val_a+val_b)/2)/val_b
            st.write("---")
            r1, r2 = st.columns(2)
            with r1:
                st.write(f"**Vanno a {sb}:**")
                for n in ga: st.success(f"{n}: Nuovo Valore **{round((f_rs[f_rs['Nome']==n]['Prezzo'].iloc[0])*coeff_a)}**")
            with r2:
                st.write(f"**Vanno a {sa}:**")
                for n in gb: st.success(f"{n}: Nuovo Valore **{round((f_rs[f_rs['Nome']==n]['Prezzo'].iloc[0])*coeff_b)}**")

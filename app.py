import streamlit as st
import pandas as pd
import os
import altair as alt

# 1. SETUP UI E STILE (RIPRISTINO GOLDEN)
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager")

# Mappature Squadre e Budget Extra
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}
map_r = {"P": "PORTIERE", "D": "DIFENSORE", "C": "CENTROCAMPISTA", "A": "ATTACCANTE"}

# --- FUNZIONI DI CARICAMENTO ROBUSTE ---
def cv(v):
    """Converte stringhe con virgole o punti in numeri float"""
    if pd.isna(v) or str(v).strip() == "": return 0.0
    try:
        s = str(v).replace('"', '').replace('.', '').replace(',', '.').strip()
        return float(s)
    except: return 0.0

def clean_text(s):
    if pd.isna(s): return ""
    return str(s).upper().strip()

def ld(f):
    """Carica CSV gestendo righe vuote e nomi colonne sporchi"""
    if not os.path.exists(f): return None
    try:
        # Carica saltando righe vuote
        df = pd.read_csv(f, skip_blank_lines=True)
        # Se la prima colonna è 'Unnamed', salta la riga vuota iniziale (tipico del tuo rose_complete)
        if df.columns[0].startswith('Unnamed'):
            df = pd.read_csv(f, skiprows=1)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except Exception as e:
        st.error(f"Errore caricamento {f}: {e}")
        return None

# 2. CARICAMENTO DATI
f_sc = ld("scontridiretti.csv")
f_pt = ld("classificapunti.csv")
f_rs = ld("rose_complete.csv")
f_vn = ld("vincoli.csv")
f_qt = ld("quotazioni.csv")

# 3. INTERFACCIA A TAB
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

# --- TAB 0: CLASSIFICHE ---
with t[0]:
    if f_pt is not None:
        st.subheader("🎯 Classifica Generale")
        f_pt['Punti_N'] = f_pt['Punti Totali'].apply(cv)
        c1, c2 = st.columns(2)
        with c1:
            st.dataframe(f_pt[['Posizione','Giocatore','Punti_N']].sort_values('Posizione').style.background_gradient(subset=['Punti_N'], cmap='Greens'), hide_index=True, use_container_width=True)
        with c2:
            p_min = f_pt['Punti_N'].min() - 10
            chart = alt.Chart(f_pt).mark_line(point=True, color='green').encode(
                x=alt.X('Giocatore:N', sort='-y'),
                y=alt.Y('Punti_N:Q', scale=alt.Scale(domainMin=p_min))
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)
    else: st.warning("Classifica non disponibile.")

# --- TAB 1: BUDGET ---
with t[1]:
    if f_rs is not None:
        st.subheader("💰 Bilancio e Patrimonio")
        f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(cv)
        f_rs['Sq_Clean'] = f_rs['Fantasquadra'].apply(clean_text).replace(map_n)
        
        bu = f_rs.groupby('Sq_Clean')['Prezzo_N'].sum().reset_index()
        bu.columns = ['Squadra', 'Speso Rosa']
        bu['Extra'] = bu['Squadra'].map(bg_ex).fillna(0)
        
        if f_vn is not None:
            f_vn['Sq_Clean'] = f_vn['Squadra'].apply(clean_text).replace(map_n)
            v_cols = [c for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29'] if c in f_vn.columns]
            for c in v_cols: f_vn[c] = f_vn[c].apply(cv)
            f_vn['Tot_Vincoli'] = f_vn[v_cols].sum(axis=1)
            v_sum = f_vn.groupby('Sq_Clean')['Tot_Vincoli'].sum().reset_index()
            bu = pd.merge(bu, v_sum, left_on='Squadra', right_on='Sq_Clean', how='left').fillna(0)
            bu.rename(columns={'Tot_Vincoli': 'Vincoli'}, inplace=True)
        else: bu['Vincoli'] = 0
        
        bu['Patrimonio'] = bu['Speso Rosa'] + bu['Extra'] + bu['Vincoli']
        st.dataframe(bu.sort_values('Patrimonio', ascending=False).style.background_gradient(subset=['Patrimonio'], cmap='YlOrRd').format({c: "{:g}" for c in bu.columns if c != 'Squadra'}), hide_index=True, use_container_width=True)
    else: st.warning("Dati Rose non disponibili.")

# --- TAB 2: STRATEGIA ---
with t[2]:
    if f_rs is not None:
        st.subheader("🧠 Composizione Rose")
        piv = f_rs.pivot_table(index='Sq_Clean', columns='Ruolo', values='Nome', aggfunc='count').fillna(0).astype(int)
        st.dataframe(piv, use_container_width=True)

# --- TAB 3: ROSE ---
with t[3]:
    if f_rs is not None:
        sq_l = sorted(f_rs['Sq_Clean'].unique())
        sq = st.selectbox("Seleziona Squadra:", sq_l)
        df_sq = f_rs[f_rs['Sq_Clean'] == sq].copy()
        
        def style_r(row):
            r = str(row['Ruolo']).upper()
            bg = '#E3F2FD' if 'PORT' in r else '#E8F5E9' if 'DIF' in r else '#FFFDE7' if 'CEN' in r else '#FFEBEE' if 'ATT' in r else '#FFFFFF'
            return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)
        
        st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo_N']].style.apply(style_r, axis=1).format({"Prezzo_N": "{:g}"}), hide_index=True, use_container_width=True)

# --- TAB 4: VINCOLI ---
with t[4]:
    if f_vn is not None:
        st.subheader("📅 Dettaglio Vincoli Pluriennali")
        st.dataframe(f_vn[['Squadra', 'Giocatore', 'Tot_Vincoli']].sort_values('Tot_Vincoli', ascending=False), hide_index=True, use_container_width=True)

# --- TAB 5: SCAMBI ---
with t[5]:
    st.subheader("🔄 Simulatore Scambi Meritocratico")
    if f_rs is not None:
        c1, c2 = st.columns(2)
        with c1:
            sa = st.selectbox("Squadra A:", sorted(f_rs['Sq_Clean'].unique()), key="sa")
            ga = st.multiselect("Cede da A:", f_rs[f_rs['Sq_Clean']==sa]['Nome'], key="ga")
        with c2:
            sb = st.selectbox("Squadra B:", [s for s in sorted(f_rs['Sq_Clean'].unique()) if s != sa], key="sb")
            gb = st.multiselect("Cede da B:", f_rs[f_rs['Sq_Clean']==sb]['Nome'], key="gb")
        
        if ga and gb:
            def get_v(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]
                v = f_vn[f_vn['Giocatore']==n]['Tot_Vincoli'].sum() if f_vn is not None else 0
                return p + v
            v_a, v_b = sum(get_v(x) for x in ga), sum(get_v(x) for x in gb)
            target = (v_a + v_b) / (len(ga) + len(gb))
            st.success(f"🤝 Punto di incontro unitario: **{target:g} crediti**")

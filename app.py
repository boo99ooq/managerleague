import streamlit as st
import pandas as pd

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

# 2. STILE GLASSMORPHISM (Migliorato per grafici)
def apply_glass_style():
    img_url = "https://images.unsplash.com/photo-1556056504-5c7696c4c28d?q=80&w=2076&auto=format&fit=crop"
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{img_url}");
            background-attachment: fixed;
            background-size: cover;
            background-position: center;
        }}
        .stTabs, .stMetric, [data-testid="stMetricValue"], .stDataFrame, .stTable {{
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: 20px;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        h1 {{
            color: #ffffff !important;
            text-shadow: 0 0 15px rgba(46, 204, 113, 0.9);
            text-align: center;
            font-size: 3.5rem !important;
        }}
        h2, h3, p, span, label, .stTabs [data-baseweb="tab"] {{
            color: #ffffff !important;
        }}
        [data-testid="stSidebar"] {{
            background: rgba(0, 0, 0, 0.8) !important;
            backdrop-filter: blur(15px);
        }}
        .stDataFrame td, .stDataFrame th {{
            color: #ffffff !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_glass_style()

st.title("⚽ Centro Direzionale Fantalega")

# 3. BUDGET FISSI
budgets_fisso = {
    "GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5,
    "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5,
    "MATTEO": 166.5, "NICHOLAS": 113.0
}

# 4. CARICAMENTO
st.sidebar.header("📂 Menu Dati")
file_rose = st.sidebar.file_uploader("1. Carica Rose", type="csv")
file_vincoli = st.sidebar.file_uploader("2. Carica Vincoli", type="csv")

def carica_rose(file):
    if file is None: return None
    file.seek(0)
    df = pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8')
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=['Fantasquadra', 'Nome'])
    df['Fantasquadra'] = df['Fantasquadra'].str.strip().str.upper().replace({"NICHO": "NICHOLAS"})
    df['Prezzo'] = pd.to_numeric(df['Prezzo'], errors='coerce').fillna(0)
    return df

def carica_vincoli(file):
    if file is None: return None
    file.seek(0)
    df = pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8')
    df.columns = df.columns.str.strip()
    df = df[df['Giocatore'].notna()]
    df = df[~df['Squadra'].str.contains(r'\*|`|:', na=False)]
    df['Squadra'] = df['Squadra'].str.strip().str.upper().replace({"NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"})
    if 'Costo 2026-27' in df.columns:
        df['Costo 2026-27'] = pd.to_numeric(df['Costo 2026-27'], errors='coerce').fillna(0)
    return df

df_rose = carica_rose(file_rose)
df_vincoli = carica_vincoli(file_vincoli)

if df_rose is not None:
    tabs = st.tabs(["📊 Riepilogo", "🧠 Analisi Strategica", "🏆 Record & Top", "🏃 Rose", "📅 Vincoli"])

    # --- TAB 0: ECONOMIA ---
    with tabs[0]:
        analisi = df_rose.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        analisi.columns = ['Fantasquadra', 'Valore Rosa']
        analisi['Budget Febbraio'] = analisi['Fantasquadra'].map(budgets_fisso).fillna(0)
        analisi['Liquidità Totale'] = analisi['Valore Rosa'] + analisi['Budget Febbraio']
        st.dataframe(analisi.sort_values('Liquidità Totale', ascending=False), hide_index=True, use_container_width=True)
        st.bar_chart(data=analisi, x='Fantasquadra', y=['Valore Rosa', 'Budget Febbraio'])

    # --- TAB 1: ANALISI STRATEGICA (NOVITÀ!) ---
    with tabs[1]:
        st.subheader("🕵️ Profilo dei Manager")
        
        # 1. L'Uomo Copertina (Giocatore più caro per squadra e suo peso %)
        tot_per_squadra = df_rose.groupby('Fantasquadra')['Prezzo'].sum()
        idx_max = df_rose.groupby('Fantasquadra')['Prezzo'].idxmax()
        top_player_squadra = df_rose.loc[idx_max, ['Fantasquadra', 'Nome', 'Prezzo']].copy()
        top_player_squadra['Peso % su Rosa'] = top_player_squadra.apply(
            lambda x: (x['Prezzo'] / tot_per_squadra[x['Fantasquadra']]) * 100, axis=1
        )
        
        c1, c2 = st.columns([1.2, 1])
        with c1:
            st.write("**L'Uomo Copertina:** (Chi pesa di più in bilancio)")
            st.dataframe(top_player_squadra.sort_values('Peso % su Rosa', ascending=False).style.format({'Peso % su Rosa': '{:.1f}%'}), hide_index=True)
        
        with c2:
            st.write("**Indice di Bilanciamento:**")
            st.caption("Chi ha la rosa più corta o più lunga?")
            count_giocatori = df_rose.groupby('Fantasquadra')['Nome'].count().reset_index()
            count_giocatori.columns = ['Fantasquadra', 'N. Giocatori']
            st.dataframe(count_giocatori.sort_values('N. Giocatori'), hide_index=True)

        st.divider()
        
        # 2. DNA DI SPESA (Grafico comparativo Ruoli)
        st.write("📊 **DNA di Spesa (Confronto Reparti)**")
        squadre_scelte = st.multiselect("Seleziona Squadre da confrontare:", sorted(df_rose['Fantasquadra'].unique()), default=sorted(df_rose['Fantasquadra'].unique())[:2])
        
        if squadre_scelte:
            dna_data = df_rose[df_rose['Fantasquadra'].isin(squadre_scelte)]
            dna_pivot = dna_data.pivot_table(index='Fantasquadra', columns='Ruolo', values='Prezzo', aggfunc='sum').fillna(0)
            st.bar_chart(dna_pivot)

    # --- TAB 2: RECORD ---
    with tabs[2]:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("💎 Top 20 Acquisti")
            st.dataframe(df_rose.sort_values('Prezzo', ascending=False).head(20)[['Nome', 'Fantasquadra', 'Prezzo']], hide_index=True)
        with col2:
            st.subheader("🥇 I più cari per Ruolo")
            st.table(df_rose.loc[df_rose.groupby('Ruolo')['Prezzo'].idxmax(), ['Ruolo', 'Nome', 'Fantasquadra', 'Prezzo']])

    # --- TAB 3: ROSE ---
    with tabs[3]:
        sq = sorted(df_rose['Fantasquadra'].unique())
        s = st.selectbox("Seleziona Squadra:", sq, key="sel_rose")
        st.dataframe(df_rose[df_rose['Fantasquadra'] == s][['Ruolo', 'Nome', 'Prezzo']], hide_index=True, use_container_width=True)

    # --- TAB 4: VINCOLI ---
    with tabs[4]:
        if df_vincoli is not None:
            riepilogo_v = df_vincoli.groupby('Squadra')['Costo 2026-27'].sum().reset_index()
            riepilogo_v.columns = ['Fantasquadra', 'Debito 26/27']
            
            v_col1, v_col2 = st.columns([1, 2])
            with v_col1:
                st.write("**Classifica Debiti:**")
                st.dataframe(riepilogo_v.sort_values('Debito 26/27', ascending=False), hide_index=True)
            with v_col2:
                s_v = st.selectbox("Dettaglio Vincoli:", sorted(df_vincoli['Squadra'].unique()), key="sel_vinc")
                st.dataframe(df_vincoli[df_vincoli['Squadra'] == s_v][['Giocatore', 'Costo 2026-27']], hide_index=True)
else:
    st.info("👋 Carica i file CSV per attivare i radar strategici.")

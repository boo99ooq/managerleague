import streamlit as st
import pandas as pd

# 1. Configurazione della pagina
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")
st.title("⚽ La mia Fantalega Manageriale")

# 2. Budget di Febbraio (Aggiornati)
budgets_fisso = {
    "GIANNI": 164, "DANI ROBI": 162, "MARCO": 194, "PIETRO": 164,
    "PIERLUIGI": 240, "GIGI": 222, "ANDREA": 165, "GIUSEPPE": 174,
    "MATTEO": 166, "NICHOLAS": 162
}

# 3. Caricamento file
st.sidebar.header("Gestione Dati")
file_caricato = st.sidebar.file_uploader("Carica nuove rose muynov25.csv", type="csv")

if file_caricato is not None:
    try:
        # Leggiamo il file ignorando le righe vuote iniziali
        file_caricato.seek(0)
        df = pd.read_csv(file_caricato, sep=',', skip_blank_lines=True, encoding='utf-8')
        
        # Pulizia nomi colonne e rimozione righe totalmente vuote
        df.columns = df.columns.str.strip()
        df = df.dropna(subset=['Fantasquadra', 'Nome'])
        
        # Uniformiamo i dati
        df['Fantasquadra'] = df['Fantasquadra'].str.strip().str.upper()
        df['Prezzo'] = pd.to_numeric(df['Prezzo'], errors='coerce').fillna(0)

        tab1, tab2 = st.tabs(["📊 Potenziale Economico", "🏃 Dettaglio Rose"])

        with tab1:
            st.subheader("Analisi Finanziaria Febbraio")
            # Calcolo Valore Rosa
            analisi = df.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
            analisi.columns = ['Fantasquadra', 'Valore Rosa']
            
            # Integrazione Budget
            analisi['Budget Febbraio'] = analisi['Fantasquadra'].map(budgets_fisso).fillna(0)
            analisi['Potenziale Totale'] = analisi['Valore Rosa'] + analisi['Budget Febbraio']
            analisi = analisi.sort_values(by='Potenziale Totale', ascending=False)
            
            col_graf, col_tab = st.columns([2, 1.5])
            with col_graf:
                st.bar_chart(data=analisi, x='Fantasquadra', y=['Valore Rosa', 'Budget Febbraio'])
            with col_tab:
                st.dataframe(analisi, hide_index=True, use_container_width=True)

        with tab2:
            squadre = sorted(df['Fantasquadra'].unique())
            scelta = st.selectbox("Seleziona la squadra:", squadre)
            
            rosa = df[df['Fantasquadra'] == scelta].copy()
            v_team = rosa['Prezzo'].sum()
            b_team = budgets_fisso.get(scelta, 0)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Valore Rosa", f"{int(v_team)}")
            c2.metric("Extra Febbraio", f"{int(b_team)}")
            c3.metric("Potenziale", f"{int(v_team + b_team)}")

            # Visualizzazione ordinata per Ruolo
            ordine_ruoli = {'Portiere': 1, 'Difensore': 2, 'Centrocampista': 3, 'Attaccante': 4, 'Giovani': 5}
            rosa['sort'] = rosa['Ruolo'].str.capitalize().map(ordine_ruoli).fillna(99)
            
            st.dataframe(
                rosa.sort_values('sort')[['Ruolo', 'Nome', 'Prezzo']], 
                use_container_width=True, hide_index=True
            )

    except Exception as e:
        st.error(f"Errore: {e}")
else:
    st.info("Carica il file CSV per visualizzare i dati della lega.")

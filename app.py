import streamlit as st
import pandas as pd

# 1. Configurazione della pagina
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")
st.title("⚽ La mia Fantalega Manageriale")

# 2. Definizione dei Budget di Febbraio
budgets_fisso = {
    "Gianni": 164,
    "Dany Roby": 162,
    "Marco": 194,
    "Pierluigi": 240,
    "Gigi": 222,
    "Giuseppe": 174,
    "Matteo": 166,
    "Nicholas": 162,
    "Pietro": 0,
    "Andrea": 0
}

# 3. Caricamento file nella barra laterale
st.sidebar.header("Gestione Dati")
file_caricato = st.sidebar.file_uploader("Carica il file delle rose", type="csv")

if file_caricato is not None:
    try:
        # Lettura del file
        file_caricato.seek(0)
        df = pd.read_csv(file_caricato, sep=None, engine='python', encoding='latin-1')
        
        # PULIZIA DATI
        df = df.dropna(how='all').reset_index(drop=True)
        df.columns = df.columns.str.strip()
        
        # Mappatura colonne
        mappa_colonne = {
            'ruolo': 'Ruolo',
            'Calciatore': 'Calciatore',
            'prezzo': 'Valore Rosa',
            'Fantasquadra': 'Fantasquadra'
        }
        df = df.rename(columns=mappa_colonne)

        # Convertiamo il valore in numero
        if 'Valore Rosa' in df.columns:
            df['Valore Rosa'] = pd.to_numeric(df['Valore Rosa'], errors='coerce').fillna(0)

        # Creazione delle Tab
        tab1, tab2 = st.tabs(["📊 Potenziale Economico", "🏃 Dettaglio Rose"])

        with tab1:
            st.subheader("Analisi Finanziaria Febbraio")
            
            # Calcolo valore attuale delle rose
            analisi = df.groupby('Fantasquadra')['Valore Rosa'].sum().reset_index()
            
            # Aggiungiamo il Budget di Febbraio
            analisi['Budget Febbraio'] = analisi['Fantasquadra'].map(budgets_fisso).fillna(0)
            
            # Calcolo Totale
            analisi['Potenziale Totale'] = analisi['Valore Rosa'] + analisi['Budget Febbraio']
            analisi = analisi.sort_values(by='Potenziale Totale', ascending=False)
            
            col_graf, col_tab = st.columns([2, 1.5])
            with col_graf:
                st.write("### Composizione Valore (Rosa + Budget)")
                st.bar_chart(data=analisi, x='Fantasquadra', y=['Valore Rosa', 'Budget Febbraio'])
            with col_tab:
                st.write("### Riepilogo Crediti")
                st.dataframe(analisi, hide_index=True, use_container_width=True)

        with tab2:
            squadre_disponibili = [s for s in df['Fantasquadra'].unique() if pd.notna(s)]
            scelta = st.selectbox("Scegli una Fantasquadra:", squadre_disponibili)
            
            rosa_squadra = df[df['Fantasquadra'] == scelta]
            budget_team = budgets_fisso.get(scelta, 0)
            valore_team = rosa_squadra['Valore Rosa'].sum()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Valore Rosa", f"{int(valore_team)}")
            c2.metric("Budget Febbraio", f"{int(budget_team)}")
            c3.metric("Potenziale", f"{int(valore_team + budget_team)}")

            # Tabella con Ruolo per primo
            ordine_visualizzazione = ['Ruolo', 'Calciatore', 'Valore Rosa']
            st.dataframe(
                rosa_squadra[ordine_visualizzazione].sort_values(by='Ruolo'), 
                use_container_width=True, 
                hide_index=True
            )

    except Exception as e:
        st.error(f"Errore: {e}")
else:
    st.info("👋 Carica il file delle rose per attivare l'app.")

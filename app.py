import streamlit as st
import pandas as pd

# 1. Configurazione della pagina
st.set_page_config(page_title="Gestore Fantalega", layout="centered")
st.title("⚽ La mia Fantalega Manageriale")

# 2. Sezione Caricamento nella barra laterale
st.sidebar.header("Impostazioni")
file_caricato = st.sidebar.file_uploader("Carica il file rose.csv", type="csv")

# 3. Controllo se il file è stato caricato
if file_caricato is not None:
    # --- INIZIO BLOCCO INDENTATO (SPOSTATO A DESTRA) ---
    try:
        # Prova a leggere il file
        df = pd.read_csv(file_caricato, encoding='utf-8')
    except Exception:
        # Se c'è un errore di codifica, prova l'altra
        df = pd.read_csv(file_caricato, encoding='latin-1')

    st.success("File caricato correttamente!")
    
    # Creazione delle schede
    tab1, tab2 = st.tabs(["📊 Classifica Budget", "🏃 Visualizza Rose"])
    
    with tab1:
        st.header("Spese per Squadra")
        if 'Fantasquadra' in df.columns and 'Prezzo' in df.columns:
            spese = df.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
            st.bar_chart(data=spese, x='Fantasquadra', y='Prezzo')
            st.table(spese)
        else:
            st.error("Il file deve avere le colonne: 'Fantasquadra' e 'Prezzo'")

    with tab2:
        st.header("Dettaglio Giocatori")
        if 'Fantasquadra' in df.columns:
            squadre = df['Fantasquadra'].unique()
            scelta = st.selectbox("Scegli una squadra:", squadre)
            rosa_filtrata = df[df['Fantasquadra'] == scelta]
            st.dataframe(rosa_filtrata, use_container_width=True)
        else:
            st.error("Colonna 'Fantasquadra' non trovata.")
    # --- FINE BLOCCO INDENTATO ---
else:
    # Questo appare se non c'è ancora nessun file
    st.warning("👋 Benvenuto! Carica il file CSV delle rose per iniziare.")

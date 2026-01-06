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
    try:
        # 1. Prova il formato standard (Virgola e UTF-8)
        file_caricato.seek(0)
        df = pd.read_csv(file_caricato, sep=None, engine='python', encoding='utf-8')
    except Exception:
        try:
            # 2. Prova il formato Excel Italiano (Punto e virgola e Latin-1)
            file_caricato.seek(0)
            df = pd.read_csv(file_caricato, sep=';', encoding='latin-1')
        except Exception as e:
            st.error(f"Non riesco a leggere il file. Errore: {e}")
            st.stop() # Si ferma qui se non riesce a leggere nulla

    st.success("File letto con successo!")
    
    # Mostriamo un'anteprima per capire cosa ha capito Python
    st.write("Anteprima dati:", df.head())
    
    # Da qui in poi le tabelle...
    tab1, tab2 = st.tabs(["📊 Analisi Lega", "🏃 Rose Complete"])
    # ... (il resto del codice che avevi per tab1 e tab2)

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



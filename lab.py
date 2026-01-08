# --- TAB 5: TAGLI (Versione Dettagliata Golden V4.3) ---
with t[5]:
    if f_rs is not None:
        st.subheader("✂️ GESTIONE TAGLI E SVINCOLI")
        
        # Selezione Squadra e Giocatore
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            sq_t = st.selectbox("SELEZIONA SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="sq_taglio_new")
        with col_s2:
            lista_giocatori = f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist()
            gt = st.selectbox("SELEZIONA GIOCATORE DA TAGLIARE", lista_giocatori, key="gt_taglio_new")
        
        if gt:
            # Recupero dati completi del giocatore
            info_g = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gt)].iloc[0]
            
            # Calcolo Vincolo (se presente)
            val_vincolo = 0
            if f_vn is not None:
                val_vincolo = f_vn[(f_vn['Sq_N'] == sq_t) & (f_vn['Giocatore_Match'] == super_clean(gt))]['Tot_Vincolo'].sum()
            
            # Calcolo Rimborso Golden (60% di Asta + Vincolo)
            prezzo_asta = info_g['Prezzo_N']
            quotazione_attuale = info_g['Quotazione']
            totale_investito = prezzo_asta + val_vincolo
            rimborso = round(totale_investito * 0.6, 1)
            
            # Visualizzazione Grafica Dettagliata
            st.write("---")
            
            # Riga 1: Dettagli Tecnici
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f'<div class="stat-card">🎭 RUOLO<br><b style="font-size:1.4em;">{info_g["Ruolo"]}</b></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="stat-card">💰 PREZZO ASTA<br><b style="font-size:1.4em;">{int(prezzo_asta)}</b></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="stat-card">📅 VINCOLO<br><b style="font-size:1.4em;">{int(val_vincolo)}</b></div>', unsafe_allow_html=True)
            with c4:
                st.markdown(f'<div class="stat-card" style="border-color:#2e7d32;">📈 QUOTAZIONE<br><b style="font-size:1.4em; color:#2e7d32;">{int(quotazione_attuale)}</b></div>', unsafe_allow_html=True)
            
            # Riga 2: Box Risultato Finale
            st.write("")
            st.markdown(f"""
                <div class="cut-box">
                    <div class="cut-player-name">{gt}</div>
                    <div style="font-size:1.2em; color:#666; margin-bottom:10px;">INVESTIMENTO TOTALE: {totale_investito:g}</div>
                    <div style="font-size:2.8em; color:#d32f2f;">RIMBORSO (60%): {rimborso:g}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Bottone di conferma (opzionale, per logica futura)
            st.write("")
            if st.button(f"CONFERMA TAGLIO DI {gt}", use_container_width=True):
                st.warning(f"Azione registrata: il rimborso di {rimborso:g} crediti è pronto per essere accreditato a {sq_t}.")

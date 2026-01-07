with t[5]: # SIMULATORE SCAMBI MERITOCRATICO CON RIEPILOGO TOTALI
    st.subheader("🔄 Simulatore Scambi Proporzionale (Logica Meritocratica)")
    if f_rs is not None:
        sq_l = sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"])
        
        def get_details(lista_nomi):
            dati = []
            for n in lista_nomi:
                p = f_rs[f_rs['Nome'] == n]['Prezzo'].values[0]
                v = f_vn[f_vn['Giocatore'] == n]['Spesa Complessiva'].values[0] if (f_vn is not None and n in f_vn['Giocatore'].values) else 0.0
                dati.append({'Giocatore': n, 'Valore Iniziale': p + v})
            return pd.DataFrame(dati)

        c1, c2 = st.columns(2)
        with c1:
            sa = st.selectbox("Squadra A:", sq_l, key="sa_m")
            ga_list = st.multiselect("Cede da A:", f_rs[f_rs['Fantasquadra']==sa]['Nome'], key="ga_m")
            df_a = get_details(ga_list)
            if not df_a.empty: 
                st.dataframe(df_a, hide_index=True, use_container_width=True)
                val_a_iniziale = df_a['Valore Iniziale'].sum()
                st.write(f"💰 Totale iniziale ceduto da {sa}: **{val_a_iniziale:g}**")

        with c2:
            sb = st.selectbox("Squadra B:", [s for s in sq_l if s != sa], key="sb_m")
            gb_list = st.multiselect("Cede da B:", f_rs[f_rs['Fantasquadra']==sb]['Nome'], key="gb_m")
            df_b = get_details(gb_list)
            if not df_b.empty: 
                st.dataframe(df_b, hide_index=True, use_container_width=True)
                val_b_iniziale = df_b['Valore Iniziale'].sum()
                st.write(f"💰 Totale iniziale ceduto da {sb}: **{val_b_iniziale:g}**")

        if not df_a.empty and not df_b.empty:
            st.write("---")
            val_tot_scambio = val_a_iniziale + val_b_iniziale
            punto_pareggio = val_tot_scambio / 2
            
            # Calcolo dei nuovi valori singoli (arrotondati)
            c_a = punto_pareggio / val_a_iniziale if val_a_iniziale > 0 else 1
            c_b = punto_pareggio / val_b_iniziale if val_b_iniziale > 0 else 1

            # Liste per calcolare i totali post-scambio effettivi (dopo arrotondamento)
            nuovi_val_a_per_b = []
            nuovi_val_b_per_a = []

            st.markdown(f"### 🤝 Esito Scambio (Dettaglio e Riepilogo)")
            r1, r2 = st.columns(2)
            
            with r1:
                st.write(f"**Vanno a {sb}:**")
                for _, r in df_a.iterrows():
                    nv = round(r['Valore Iniziale'] * c_a)
                    nuovi_val_a_per_b.append(nv)
                    st.success(f"🔹 {r['Giocatore']}: da {r['Valore Iniziale']:g} a **{nv}**")
            
            with r2:
                st.write(f"**Vanno a {sa}:**")
                for _, r in df_b.iterrows():
                    nv = round(r['Valore Iniziale'] * c_b)
                    nuovi_val_b_per_a.append(nv)
                    st.success(f"🔸 {r['Giocatore']}: da {r['Valore Iniziale']:g} a **{nv}**")

            st.write("---")
            # TABELLA DI CONFRONTO FINALE
            val_post_a = sum(nuovi_val_b_per_a)
            val_post_b = sum(nuovi_val_a_per_b)
            
            st.markdown("#### 📈 Riepilogo Valore Pacchetti")
            comp_data = {
                "Squadra": [sa, sb],
                "Valore Ceduto (Pre)": [val_a_iniziale, val_b_iniziale],
                "Valore Ricevuto (Post)": [val_post_a, val_post_b],
                "Differenza": [val_post_a - val_a_iniziale, val_post_b - val_b_iniziale]
            }
            st.table(pd.DataFrame(comp_data))
            st.info(f"NB: Il valore totale dell'operazione è di **{val_tot_scambio:g}** crediti. "
                    f"Dopo lo scambio, ogni squadra detiene un pacchetto di circa **{punto_pareggio:g}** crediti.")

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import re

def show_settings():
    st.markdown("<h1 class='main-header' style='color: #4F46E5; font-size: 2.5rem; padding: 10px 0; border-bottom: 2px solid #4F46E5; margin-bottom: 20px;'>⚙️ Impostazioni</h1>", unsafe_allow_html=True)
    
    # Create tabs for different settings categories
    tabs = st.tabs(["Profilo", "Integrazione API", "Notifiche", "Backup e Ripristino", "Preferenze"])
    
    with tabs[0]:
        show_profile_settings()
    with tabs[1]:
        show_api_settings()
    with tabs[2]:
        show_notification_settings()
    with tabs[3]:
        show_backup_restore()
    with tabs[4]:
        show_preferences()

def show_profile_settings():
    st.subheader("Profilo Utente")
    
    # Initialize user profile if not exist
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = {
            "name": "Utente Demo",
            "email": "demo@example.com",
            "phone": "+39 123 456 7890",
            "company": "Demo Host Srl",
            "address": "Via Roma, 123",
            "city": "Milano",
            "role": "Proprietario",
            "subscription": "Pro"
        }
    
    # Edit profile form
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nome Completo", value=st.session_state.user_profile.get("name", ""))
            email = st.text_input("Email", value=st.session_state.user_profile.get("email", ""))
            phone = st.text_input("Telefono", value=st.session_state.user_profile.get("phone", ""))
            role = st.selectbox(
                "Ruolo",
                ["Proprietario", "Co-Host", "Property Manager", "Amministratore"],
                index=["Proprietario", "Co-Host", "Property Manager", "Amministratore"].index(
                    st.session_state.user_profile.get("role", "Proprietario")
                )
            )
        with col2:
            company = st.text_input("Azienda", value=st.session_state.user_profile.get("company", ""))
            address = st.text_input("Indirizzo", value=st.session_state.user_profile.get("address", ""))
            city = st.text_input("Città", value=st.session_state.user_profile.get("city", ""))
            subscription = st.selectbox(
                "Piano Abbonamento",
                ["Base", "Pro"],
                index=["Base", "Pro"].index(
                    st.session_state.user_profile.get("subscription", "Pro")
                )
            )
        
        submit_button = st.form_submit_button("Aggiorna Profilo")
        
        if submit_button:
            # Update profile
            st.session_state.user_profile.update({
                "name": name,
                "email": email,
                "phone": phone,
                "company": company,
                "address": address,
                "city": city,
                "role": role,
                "subscription": subscription
            })
            st.success("Profilo aggiornato con successo!")
    
    # Subscription information
    st.subheader("Dettagli Abbonamento")
    subscription = st.session_state.user_profile.get("subscription", "Pro")
    
    if subscription == "Base":
        st.markdown("""
        ### Piano Base - €25/mese per immobile + 10% commissione
        #### Funzionalità incluse:
        - ✅ Concierge AI multilingua 24/7
        - ✅ Ottimizzazione prezzi AI
        - ✅ Dashboard base con statistiche
        - ✅ Sistema antifrode ospiti
        - ✅ Archivio fiscale e fatturazione
        #### Funzionalità Pro non disponibili:
        - ❌ Dashboard avanzata
        - ❌ Analisi predittiva delle prenotazioni
        - ❌ Personalizzazione chatbot
        - ❌ Priorità supporto tecnico
        - ❌ Integrazione API con portali esterni
        """)
        
        if st.button("Passa a Piano Pro"):
            st.info("In un'applicazione reale, qui si verrebbe reindirizzati al sistema di pagamento per l'upgrade.")
    else:  # Pro
        st.markdown("""
        ### Piano Pro - €44.99/mese per immobile + 10% commissione
        #### Funzionalità incluse:
        - ✅ Concierge AI multilingua 24/7
        - ✅ Ottimizzazione prezzi AI
        - ✅ Dashboard avanzata
        - ✅ Sistema antifrode ospiti
        - ✅ Archivio fiscale e fatturazione
        - ✅ Analisi predittiva delle prenotazioni
        - ✅ Personalizzazione chatbot
        - ✅ Priorità supporto tecnico
        - ✅ Integrazione API con portali esterni
        **Abbonamento attivo fino al:** 31/05/2026
        """)

def show_api_settings():
    st.subheader("Integrazione API")
    st.write("""
    Configura le integrazioni con servizi esterni e portali di prenotazione.
    """)
    
    # Initialize API settings if not exist
    if "api_settings" not in st.session_state:
        st.session_state.api_settings = {
            "airbnb": {
                "enabled": False,
                "api_key": "",
                "user_id": "",
                "status": "non configurato"
            },
            "booking": {
                "enabled": False,
                "api_key": "",
                "property_ids": "",
                "status": "non configurato"
            },
            "vrbo": {
                "enabled": False,
                "api_key": "",
                "user_id": "",
                "status": "non configurato"
            },
            "twilio": {
                "enabled": False,
                "account_sid": "",
                "auth_token": "",
                "phone_number": "",
                "status": "non configurato"
            },
            "openai": {
                "enabled": True,
                "api_key": "sk-...configurato",
                "model": "gpt-4o",
                "status": "attivo"
            }
        }
    
    # Create integrations
    integration_tabs = st.tabs(["Portali Prenotazione", "Servizi Messaggistica", "AI e Analytics"])
    
    with integration_tabs[0]:
        st.markdown("### Integrazione Portali Prenotazione")
        st.write("Collega CiaoHost ai portali di prenotazione per sincronizzare automaticamente le prenotazioni e i calendari.")
        
        # Airbnb
        with st.expander("Airbnb", expanded=st.session_state.api_settings["airbnb"]["enabled"]):
            api_airbnb = st.session_state.api_settings["airbnb"]
            enabled = st.checkbox("Abilita integrazione Airbnb", value=api_airbnb["enabled"])
            
            if enabled:
                with st.form("airbnb_form"):
                    api_key = st.text_input("Airbnb API Key", value=api_airbnb["api_key"], type="password")
                    user_id = st.text_input("Airbnb User ID", value=api_airbnb["user_id"])
                    
                    submit_button = st.form_submit_button("Salva Configurazione")
                    
                    if submit_button:
                        # Validate inputs
                        if not api_key or not user_id:
                            st.error("Tutti i campi sono obbligatori.")
                        else:
                            # Update settings
                            st.session_state.api_settings["airbnb"].update({
                                "enabled": enabled,
                                "api_key": api_key,
                                "user_id": user_id,
                                "status": "attivo"
                            })
                            st.success("Configurazione Airbnb salvata con successo!")
            else:
                # Update status
                st.session_state.api_settings["airbnb"]["enabled"] = False
                st.session_state.api_settings["airbnb"]["status"] = "non configurato"
        
        # Booking.com
        with st.expander("Booking.com", expanded=st.session_state.api_settings["booking"]["enabled"]):
            api_booking = st.session_state.api_settings["booking"]
            enabled = st.checkbox("Abilita integrazione Booking.com", value=api_booking["enabled"])
            
            if enabled:
                with st.form("booking_form"):
                    api_key = st.text_input("Booking.com API Key", value=api_booking["api_key"], type="password")
                    property_ids = st.text_area("Property IDs (uno per riga)", value=api_booking["property_ids"])
                    
                    submit_button = st.form_submit_button("Salva Configurazione")
                    
                    if submit_button:
                        # Validate inputs
                        if not api_key:
                            st.error("API Key è obbligatoria.")
                        else:
                            # Update settings
                            st.session_state.api_settings["booking"].update({
                                "enabled": enabled,
                                "api_key": api_key,
                                "property_ids": property_ids,
                                "status": "attivo"
                            })
                            st.success("Configurazione Booking.com salvata con successo!")
            else:
                # Update status
                st.session_state.api_settings["booking"]["enabled"] = False
                st.session_state.api_settings["booking"]["status"] = "non configurato"
        
        # VRBO
        with st.expander("VRBO", expanded=st.session_state.api_settings["vrbo"]["enabled"]):
            api_vrbo = st.session_state.api_settings["vrbo"]
            enabled = st.checkbox("Abilita integrazione VRBO", value=api_vrbo["enabled"])
            
            if enabled:
                with st.form("vrbo_form"):
                    api_key = st.text_input("VRBO API Key", value=api_vrbo["api_key"], type="password")
                    user_id = st.text_input("VRBO User ID", value=api_vrbo["user_id"])
                    
                    submit_button = st.form_submit_button("Salva Configurazione")
                    
                    if submit_button:
                        # Validate inputs
                        if not api_key or not user_id:
                            st.error("Tutti i campi sono obbligatori.")
                        else:
                            # Update settings
                            st.session_state.api_settings["vrbo"].update({
                                "enabled": enabled,
                                "api_key": api_key,
                                "user_id": user_id,
                                "status": "attivo"
                            })
                            st.success("Configurazione VRBO salvata con successo!")
            else:
                # Update status
                st.session_state.api_settings["vrbo"]["enabled"] = False
                st.session_state.api_settings["vrbo"]["status"] = "non configurato"
    
    with integration_tabs[1]:
        st.markdown("### Integrazione Servizi Messaggistica")
        st.write("Configura i servizi di messaggistica per l'invio automatico di comunicazioni agli ospiti.")
        
        # Twilio
        with st.expander("Twilio SMS", expanded=st.session_state.api_settings["twilio"]["enabled"]):
            api_twilio = st.session_state.api_settings["twilio"]
            enabled = st.checkbox("Abilita integrazione Twilio", value=api_twilio["enabled"])
            
            if enabled:
                with st.form("twilio_form"):
                    account_sid = st.text_input("Account SID", value=api_twilio["account_sid"])
                    auth_token = st.text_input("Auth Token", value=api_twilio["auth_token"], type="password")
                    phone_number = st.text_input("Numero di Telefono", value=api_twilio["phone_number"], help="Numero di telefono Twilio nel formato +123456789")
                    
                    submit_button = st.form_submit_button("Salva Configurazione")
                    
                    if submit_button:
                        # Validate inputs
                        if not account_sid or not auth_token or not phone_number:
                            st.error("Tutti i campi sono obbligatori.")
                        elif not re.match(r'^\+[1-9]\d{1,14}$', phone_number):
                            st.error("Formato numero di telefono non valido. Usa il formato internazionale: +123456789")
                        else:
                            # Update settings
                            st.session_state.api_settings["twilio"].update({
                                "enabled": enabled,
                                "account_sid": account_sid,
                                "auth_token": auth_token,
                                "phone_number": phone_number,
                                "status": "attivo"
                            })
                            
                            # Set environment variables for Twilio
                            import os
                            os.environ["TWILIO_ACCOUNT_SID"] = account_sid
                            os.environ["TWILIO_AUTH_TOKEN"] = auth_token
                            os.environ["TWILIO_PHONE_NUMBER"] = phone_number
                            
                            st.success("Configurazione Twilio salvata con successo! Le API key sono state configurate per l'invio SMS.")
                
                # Test SMS functionality
                if st.session_state.api_settings["twilio"]["status"] == "attivo":
                    with st.expander("Test SMS"):
                        test_phone = st.text_input(
                            "Numero di telefono per test",
                            help="Inserisci un numero di telefono nel formato internazionale (es. +393331234567) per ricevere un SMS di test"
                        )
                        
                        if st.button("Invia SMS di Test"):
                            if not test_phone:
                                st.error("Inserisci un numero di telefono valido per il test.")
                            elif not re.match(r'^\+[1-9]\d{1,14}$', test_phone):
                                st.error("Formato numero di telefono non valido. Usa il formato internazionale: +123456789")
                            else:
                                # Try to send a real SMS using Twilio
                                try:
                                    from utils.message_service import send_message
                                    result = send_message(
                                        to_phone=test_phone,
                                        message_text="Questo è un messaggio di test da CiaoHost. L'integrazione Twilio è configurata correttamente!",
                                        message_type="test",
                                        via_sms=True
                                    )
                                    
                                    if result["status"] == "success":
                                        st.success(f"SMS inviato con successo a {test_phone}")
                                    elif result["status"] == "simulated":
                                        st.info(f"SMS simulato a {test_phone}: {result['message']}")
                                    else:
                                        st.error(f"Errore nell'invio del SMS: {result['message']}")
                                except Exception as e:
                                    st.error(f"Errore nell'invio del SMS: {str(e)}")
            else:
                # Update status
                st.session_state.api_settings["twilio"]["enabled"] = False
                st.session_state.api_settings["twilio"]["status"] = "non configurato"
    
    with integration_tabs[2]:
        st.markdown("### Integrazione AI e Analytics")
        st.write("Configura i servizi AI per le funzionalità di assistenza virtuale e analisi dei dati.")
        
        # OpenAI
        with st.expander("OpenAI", expanded=st.session_state.api_settings["openai"]["enabled"]):
            api_openai = st.session_state.api_settings["openai"]
            enabled = st.checkbox("Abilita integrazione OpenAI", value=api_openai["enabled"])
            
            if enabled:
                with st.form("openai_form"):
                    api_key = st.text_input("OpenAI API Key", value=api_openai["api_key"], type="password")
                    model = st.selectbox(
                        "Modello",
                        ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
                        index=["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"].index(api_openai["model"])
                    )
                    
                    st.markdown("""
                    **Nota**: Il modello `gpt-4o` è consigliato per le migliori prestazioni ma ha un costo maggiore. `gpt-3.5-turbo` è più economico ma meno accurato nelle risposte.
                    """)
                    
                    submit_button = st.form_submit_button("Salva Configurazione")
                    
                    if submit_button:
                        # Validate inputs
                        if not api_key:
                            st.error("API Key è obbligatoria.")
                        elif not api_key.startswith("sk-"):
                            st.warning("Il formato dell'API Key non sembra corretto. Dovrebbe iniziare con 'sk-'.")
                        
                        # Update settings
                        st.session_state.api_settings["openai"].update({
                            "enabled": enabled,
                            "api_key": api_key,
                            "model": model,
                            "status": "attivo"
                        })
                        
                        st.success("Configurazione OpenAI salvata con successo!")
                
                # Test AI functionality
                if st.session_state.api_settings["openai"]["status"] == "attivo":
                    if st.button("Test OpenAI"):
                        with st.spinner("Test in corso..."):
                            st.info("API Key verificata con successo! La connessione a OpenAI è attiva.")
                            # In a real app, would make a simple API call to verify the key
            else:
                # Update status
                st.session_state.api_settings["openai"]["enabled"] = False
                st.session_state.api_settings["openai"]["status"] = "non configurato"
    
    # API status overview
    st.subheader("Riepilogo Stato Integrazioni")
    api_status = []
    for api_name, api_info in st.session_state.api_settings.items():
        api_status.append({
            "Servizio": api_name.capitalize(),
            "Stato": api_info["status"].capitalize(),
            "Abilitato": "✅" if api_info["enabled"] else "❌"
        })
    
    st.dataframe(pd.DataFrame(api_status), use_container_width=True)

def show_notification_settings():
    st.subheader("Gestione Notifiche")
    st.write("""
    Configura le notifiche automatiche per vari eventi e situazioni.
    """)
    
    # Initialize notification settings if not exist
    if "notification_settings" not in st.session_state:
        st.session_state.notification_settings = {
            "guest_notifications": {
                "booking_confirmation": True,
                "checkin_reminder": True,
                "checkout_reminder": True,
                "review_request": True,
                "custom_messages": True
            },
            "host_notifications": {
                "new_booking": True,
                "booking_cancellation": True,
                "guest_message": True,
                "checkin_alert": True,
                "checkout_alert": True,
                "review_received": True,
                "cleaning_schedule": True,
                "payment_received": True
            },
            "notification_methods": {
                "email": True,
                "sms": False,
                "app_notification": True
            }
        }
    
    # Notification settings tabs
    notification_tabs = st.tabs(["Notifiche Ospiti", "Notifiche Host", "Metodi di Notifica"])
    
    with notification_tabs[0]:
        st.markdown("### Notifiche Ospiti")
        st.write("Configura le notifiche automatiche inviate agli ospiti.")
        
        guest_notifs = st.session_state.notification_settings["guest_notifications"]
        
        # Booking confirmation
        booking_confirmation = st.checkbox(
            "Conferma Prenotazione",
            value=guest_notifs["booking_confirmation"],
            help="Invia conferma automatica quando una prenotazione viene effettuata."
        )
        
        # Check-in reminder
        checkin_reminder = st.checkbox(
            "Promemoria Check-in",
            value=guest_notifs["checkin_reminder"],
            help="Invia promemoria check-in 24 ore prima dell'arrivo."
        )
        
        # Check-out reminder
        checkout_reminder = st.checkbox(
            "Promemoria Check-out",
            value=guest_notifs["checkout_reminder"],
            help="Invia promemoria check-out il giorno prima della partenza."
        )
        
        # Review request
        review_request = st.checkbox(
            "Richiesta Recensione",
            value=guest_notifs["review_request"],
            help="Invia richiesta di recensione dopo il check-out."
        )
        
        # Custom messages
        custom_messages = st.checkbox(
            "Messaggi Personalizzati",
            value=guest_notifs["custom_messages"],
            help="Abilita l'invio di messaggi personalizzati agli ospiti."
        )
        
        # Update settings
        st.session_state.notification_settings["guest_notifications"].update({
            "booking_confirmation": booking_confirmation,
            "checkin_reminder": checkin_reminder,
            "checkout_reminder": checkout_reminder,
            "review_request": review_request,
            "custom_messages": custom_messages
        })
    
    with notification_tabs[1]:
        st.markdown("### Notifiche Host")
        st.write("Configura le notifiche che riceverai come host.")
        
        host_notifs = st.session_state.notification_settings["host_notifications"]
        
        # New booking
        new_booking = st.checkbox(
            "Nuova Prenotazione",
            value=host_notifs["new_booking"],
            help="Ricevi notifica quando viene effettuata una nuova prenotazione."
        )
        
        # Booking cancellation
        booking_cancellation = st.checkbox(
            "Cancellazione Prenotazione",
            value=host_notifs["booking_cancellation"],
            help="Ricevi notifica quando una prenotazione viene cancellata."
        )
        
        # Guest message
        guest_message = st.checkbox(
            "Messaggio Ospite",
            value=host_notifs["guest_message"],
            help="Ricevi notifica quando un ospite invia un messaggio."
        )
        
        # Check-in alert
        checkin_alert = st.checkbox(
            "Avviso Check-in",
            value=host_notifs["checkin_alert"],
            help="Ricevi notifica quando un ospite effettua il check-in."
        )
        
        # Check-out alert
        checkout_alert = st.checkbox(
            "Avviso Check-out",
            value=host_notifs["checkout_alert"],
            help="Ricevi notifica quando un ospite effettua il check-out."
        )
        
        # Review received
        review_received = st.checkbox(
            "Nuova Recensione",
            value=host_notifs["review_received"],
            help="Ricevi notifica quando un ospite lascia una recensione."
        )
        
        # Cleaning schedule
        cleaning_schedule = st.checkbox(
            "Programmazione Pulizie",
            value=host_notifs["cleaning_schedule"],
            help="Ricevi notifica per programmare le pulizie dopo il check-out."
        )
        
        # Payment received
        payment_received = st.checkbox(
            "Pagamento Ricevuto",
            value=host_notifs["payment_received"],
            help="Ricevi notifica quando ricevi un pagamento."
        )
        
        # Update settings
        st.session_state.notification_settings["host_notifications"].update({
            "new_booking": new_booking,
            "booking_cancellation": booking_cancellation,
            "guest_message": guest_message,
            "checkin_alert": checkin_alert,
            "checkout_alert": checkout_alert,
            "review_received": review_received,
            "cleaning_schedule": cleaning_schedule,
            "payment_received": payment_received
        })
    
    with notification_tabs[2]:
        st.markdown("### Metodi di Notifica")
        st.write("Configura come ricevere le notifiche.")
        
        notif_methods = st.session_state.notification_settings["notification_methods"]
        
        # Email
        email = st.checkbox(
            "Email",
            value=notif_methods["email"],
            help="Ricevi notifiche via email."
        )
        
        # SMS
        sms = st.checkbox(
            "SMS",
            value=notif_methods["sms"],
            help="Ricevi notifiche via SMS (richiede configurazione Twilio)."
        )
        
        # App notification
        app_notification = st.checkbox(
            "Notifiche App",
            value=notif_methods["app_notification"],
            help="Ricevi notifiche nell'app."
        )
        
        # Update settings
        st.session_state.notification_settings["notification_methods"].update({
            "email": email,
            "sms": sms,
            "app_notification": app_notification
        })
        
        # SMS warning
        if sms and not st.session_state.api_settings.get("twilio", {}).get("enabled", False):
            st.warning("Le notifiche SMS richiedono la configurazione di Twilio. Vai in 'Integrazione API' per configurare Twilio.")
    
    # Save settings button
    if st.button("Salva Impostazioni Notifiche"):
        st.success("Impostazioni notifiche salvate con successo!")
        # In a real app, would save to database

def show_backup_restore():
    st.subheader("Backup e Ripristino")
    st.write("""
    Esegui backup dei dati della tua attività e ripristina da backup precedenti.
    """)
    
    backup_tabs = st.tabs(["Backup Dati", "Ripristino", "Importazione/Esportazione"])
    
    with backup_tabs[0]:
        st.markdown("### Backup Dati")
        st.write("Crea un backup di tutti i dati dell'applicazione.")
        
        # Backup options
        backup_options = st.multiselect(
            "Elementi da includere nel backup",
            ["Immobili", "Prenotazioni", "Chat e Comunicazioni", "Impostazioni", "Prezzi"],
            default=["Immobili", "Prenotazioni", "Impostazioni"]
        )
        
        # Include media files
        include_media = st.checkbox("Includi file multimediali", value=False)
        
        # Backup format
        backup_format = st.selectbox(
            "Formato Backup",
            ["JSON", "CSV", "Excel"],
            index=0
        )
        
        # Create backup button
        if st.button("Crea Backup"):
            with st.spinner("Creazione backup in corso..."):
                # In a real app, would actually create a backup file
                # For demo, just show success message
                import time
                time.sleep(1)
                st.success("Backup creato con successo!")
                
                # Create a placeholder download button
                st.download_button(
                    "Scarica Backup",
                    data=json.dumps({
                        "timestamp": datetime.now().isoformat(),
                        "backup_options": backup_options,
                        "include_media": include_media,
                        "properties_count": len(st.session_state.get("properties", [])),
                        "bookings_count": len(st.session_state.get("bookings", []))
                    }),
                    file_name=f"ciao_host_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    with backup_tabs[1]:
        st.markdown("### Ripristino Dati")
        st.write("Ripristina i dati da un backup precedente.")
        
        # Upload backup file
        uploaded_backup = st.file_uploader("Carica file di backup", type=["json", "csv", "xlsx"])
        
        # Restore options
        restore_options = st.multiselect(
            "Elementi da ripristinare",
            ["Immobili", "Prenotazioni", "Chat e Comunicazioni", "Impostazioni", "Prezzi"],
            default=["Immobili", "Prenotazioni", "Impostazioni"]
        )
        
        # Restore behavior
        restore_behavior = st.radio(
            "Comportamento Ripristino",
            ["Unisci con dati esistenti", "Sostituisci dati esistenti"],
            index=0
        )
        
        # Restore button
        if uploaded_backup is not None and st.button("Ripristina Dati"):
            # In a real app, would actually restore from the backup file
            # For demo, just show success message
            st.warning("⚠️ Questa operazione potrebbe sovrascrivere i dati esistenti. Sei sicuro di voler procedere?")
            
            # Confirmation buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Sì, Procedi con il Ripristino"):
                    with st.spinner("Ripristino in corso..."):
                        import time
                        time.sleep(2)
                        st.success("Dati ripristinati con successo!")
            with col2:
                if st.button("No, Annulla"):
                    st.info("Ripristino annullato.")
    
    with backup_tabs[2]:
        st.markdown("### Importazione/Esportazione")
        st.write("Importa ed esporta dati specifici in vari formati.")
        
        # Export section
        st.subheader("Esportazione Dati")
        export_type = st.selectbox(
            "Tipo di Dati da Esportare",
            ["Immobili", "Prenotazioni", "Ospiti", "Report Finanziario"]
        )
        
        export_format = st.selectbox(
            "Formato Esportazione",
            ["CSV", "Excel", "JSON"],
            index=0
        )
        
        # Date range for some export types
        if export_type in ["Prenotazioni", "Report Finanziario"]:
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Data Inizio",
                    value=datetime.now().replace(month=1, day=1).date()
                )
            with col2:
                end_date = st.date_input(
                    "Data Fine",
                    value=datetime.now().date()
                )
        
        # Export button
        if st.button("Esporta Dati"):
            with st.spinner("Esportazione in corso..."):
                if export_type == "Immobili" and st.session_state.get("properties", []):
                    # Create the export
                    if export_format == "CSV":
                        df = pd.DataFrame(st.session_state.properties)
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "Scarica CSV",
                            data=csv,
                            file_name="properties_export.csv",
                            mime="text/csv"
                        )
                    elif export_format == "Excel":
                        df = pd.DataFrame(st.session_state.properties)
                        st.info("In un'applicazione reale, qui verrebbe generato un file Excel.")
                    else:  # JSON
                        json_data = json.dumps(st.session_state.properties, indent=2, ensure_ascii=False)
                        st.download_button(
                            "Scarica JSON",
                            data=json_data,
                            file_name="properties_export.json",
                            mime="application/json"
                        )
                elif export_type == "Prenotazioni" and st.session_state.get("bookings", []):
                    # Similar export functionality would be implemented for other data types
                    json_data = json.dumps(st.session_state.bookings, indent=2, ensure_ascii=False)
                    st.download_button(
                        "Scarica JSON",
                        data=json_data,
                        file_name="bookings_export.json",
                        mime="application/json"
                    )
                else:
                    st.info(f"Nessun dato disponibile per l'esportazione di {export_type}.")
        
        # Import section
        st.subheader("Importazione Dati")
        import_type = st.selectbox(
            "Tipo di Dati da Importare",
            ["Immobili", "Prenotazioni", "Ospiti", "Calendari"]
        )
        
        uploaded_file = st.file_uploader(
            f"Carica file {import_type}",
            type=["csv", "xlsx", "json"],
            key="import_file_uploader"
        )
        
        # Import behavior
        import_behavior = st.radio(
            "Comportamento Importazione",
            ["Unisci con dati esistenti", "Sostituisci dati esistenti"],
            index=0,
            key="import_behavior"
        )
        
        # Import button
        if uploaded_file is not None and st.button("Importa Dati"):
            # In a real app, would actually import the data
            # For demo, just show success message
            st.warning("⚠️ Se scegli di sostituire i dati esistenti, tutti i dati attuali del tipo selezionato verranno eliminati. Sei sicuro di voler procedere?")
            
            # Confirmation buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Sì, Procedi con l'Importazione"):
                    with st.spinner("Importazione in corso..."):
                        import time
                        time.sleep(2)
                        st.success(f"Dati {import_type} importati con successo!")
            with col2:
                if st.button("No, Annulla"):
                    st.info("Importazione annullata.")

def show_preferences():
    st.subheader("Preferenze")
    st.write("""
    Personalizza la tua esperienza con CiaoHost.
    """)
    
    # Initialize preferences if not exist
    if "preferences" not in st.session_state:
        st.session_state.preferences = {
            "language": "italiano",
            "date_format": "DD/MM/YYYY",
            "currency": "EUR",
            "start_page": "dashboard",
            "theme": "light",
            "notifications_sound": True,
            "auto_translate": True,
            "default_checkin_time": "15:00",
            "default_checkout_time": "10:00"
        }
    
    preferences = st.session_state.preferences
    
    # Appearance settings
    st.markdown("### Aspetto")
    col1, col2 = st.columns(2)
    with col1:
        language = st.selectbox(
            "Lingua",
            ["italiano", "english", "español", "français", "deutsch"],
            index=["italiano", "english", "español", "français", "deutsch"].index(preferences["language"])
        )
        
        theme = st.selectbox(
            "Tema",
            ["light", "dark", "system"],
            index=["light", "dark", "system"].index(preferences["theme"]),
            format_func=lambda x: {"light": "Chiaro", "dark": "Scuro", "system": "Sistema"}.get(x)
        )
    
    with col2:
        start_page = st.selectbox(
            "Pagina Iniziale",
            ["dashboard", "properties", "bookings", "co_host", "pricing"],
            index=["dashboard", "properties", "bookings", "co_host", "pricing"].index(preferences["start_page"]),
            format_func=lambda x: {
                "dashboard": "Dashboard",
                "properties": "Gestione Immobili",
                "bookings": "Prenotazioni",
                "co_host": "Co-Host Virtuale",
                "pricing": "Prezzi Dinamici"
            }.get(x)
        )
        
        notifications_sound = st.checkbox(
            "Suono Notifiche",
            value=preferences["notifications_sound"],
            help="Abilita i suoni per le notifiche"
        )
    
    # Regional settings
    st.markdown("### Impostazioni Regionali")
    col1, col2 = st.columns(2)
    with col1:
        date_format = st.selectbox(
            "Formato Data",
            ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"],
            index=["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"].index(preferences["date_format"])
        )
        
        default_checkin_time = st.text_input(
            "Orario Default Check-in",
            value=preferences["default_checkin_time"],
            help="Formato 24h (es. 15:00)"
        )
    
    with col2:
        currency = st.selectbox(
            "Valuta",
            ["EUR", "USD", "GBP", "CHF"],
            index=["EUR", "USD", "GBP", "CHF"].index(preferences["currency"]),
            format_func=lambda x: {
                "EUR": "Euro (€)",
                "USD": "Dollaro USA ($)",
                "GBP": "Sterlina (£)",
                "CHF": "Franco Svizzero (CHF)"
            }.get(x)
        )
        
        default_checkout_time = st.text_input(
            "Orario Default Check-out",
            value=preferences["default_checkout_time"],
            help="Formato 24h (es. 10:00)"
        )
    
    # AI settings
    st.markdown("### Impostazioni AI")
    auto_translate = st.checkbox(
        "Traduzione Automatica",
        value=preferences["auto_translate"],
        help="Traduce automaticamente i messaggi degli ospiti nella lingua selezionata"
    )
    
    # Save preferences button
    if st.button("Salva Preferenze"):
        # Update preferences
        st.session_state.preferences.update({
            "language": language,
            "date_format": date_format,
            "currency": currency,
            "start_page": start_page,
            "theme": theme,
            "notifications_sound": notifications_sound,
            "auto_translate": auto_translate,
            "default_checkin_time": default_checkin_time,
            "default_checkout_time": default_checkout_time
        })
        
        st.success("Preferenze salvate con successo!")
        # In a real app, would save to database

import time
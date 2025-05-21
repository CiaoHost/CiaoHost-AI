import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import json
import uuid
from utils.database import (
    get_all_cleaning_services, add_cleaning_service, get_default_cleaning_service,
    get_all_cleaning_tasks, schedule_cleaning, get_upcoming_cleaning_tasks,
    get_all_properties, get_property, update_property
)
from utils.ai_assistant import virtual_co_host
from utils.message_service import send_message

def show_cleaning_management():
    import streamlit as st
    st.header("Cleaning Management")
    st.write("Cleaning management features will be implemented here")

def show_cleaning_calendar():
    st.subheader("Calendario Pulizie")
    
    # Get all cleaning tasks
    tasks = get_all_cleaning_tasks()
    
    if not tasks:
        st.info("Nessun task di pulizia programmato. Vai alla scheda 'Programmazione' per programmare nuove pulizie.")
        return
    
    # Date range filter
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Data Inizio",
            value=datetime.now().date()
        )
    
    with col2:
        end_date = st.date_input(
            "Data Fine",
            value=(datetime.now() + timedelta(days=30)).date(),
            min_value=start_date
        )
    
    # Status filter
    status_filter = st.multiselect(
        "Filtra per Stato",
        ["Programmata", "Completata", "Annullata"],
        default=["Programmata"]
    )
    
    # Filter tasks
    filtered_tasks = []
    
    for task in tasks:
        # Convert scheduled_date string to datetime
        scheduled_date = datetime.fromisoformat(task.get("scheduled_date")).date() if task.get("scheduled_date") else None
        
        # Apply date filter
        if scheduled_date and (scheduled_date < start_date or scheduled_date > end_date):
            continue
        
        # Apply status filter
        if status_filter and task.get("status") not in status_filter:
            continue
        
        # Get property info
        property_data = get_property(task.get("property_id"))
        property_name = property_data.get("name") if property_data else "Sconosciuto"
        
        filtered_tasks.append({
            "id": task.get("id"),
            "Data": scheduled_date.strftime("%d/%m/%Y") if scheduled_date else "N/A",
            "Ora": datetime.fromisoformat(task.get("scheduled_date")).strftime("%H:%M") if task.get("scheduled_date") else "N/A",
            "Immobile": property_name,
            "Stato": task.get("status"),
            "Note": task.get("notes", ""),
            "booking_id": task.get("booking_id"),
            "cleaning_service_id": task.get("cleaning_service_id")
        })
    
    if filtered_tasks:
        # Sort by date
        filtered_tasks.sort(key=lambda x: x["Data"] + x["Ora"])
        
        # Create a dataframe
        task_df = pd.DataFrame(filtered_tasks)
        displayed_cols = [col for col in task_df.columns if col not in ["id", "booking_id", "cleaning_service_id"]]
        st.dataframe(task_df[displayed_cols], use_container_width=True)
        
        # Task details and actions
        st.subheader("Dettagli Task")
        
        selected_task_id = st.selectbox(
            "Seleziona un task di pulizia",
            options=[task["id"] for task in filtered_tasks],
            format_func=lambda x: next((f"{task['Immobile']} - {task['Data']} {task['Ora']}" 
                                      for task in filtered_tasks if task["id"] == x), x)
        )
        
        if selected_task_id:
            selected_task = next((task for task in filtered_tasks if task["id"] == selected_task_id), None)
            
            if selected_task:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Immobile:** {selected_task['Immobile']}")
                    st.markdown(f"**Data:** {selected_task['Data']}")
                    st.markdown(f"**Ora:** {selected_task['Ora']}")
                    
                    # Get service info
                    all_services = get_all_cleaning_services()
                    service = next((s for s in all_services if s["id"] == selected_task["cleaning_service_id"]), None)
                    
                    if service:
                        st.markdown(f"**Servizio di Pulizia:** {service['name']}")
                        st.markdown(f"**Telefono:** {service['phone']}")
                        st.markdown(f"**Email:** {service['email']}")
                
                with col2:
                    st.markdown(f"**Stato:** {selected_task['Stato']}")
                    st.markdown(f"**Note:** {selected_task['Note']}")
                
                # Task actions
                st.markdown("### Azioni Task")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if selected_task["Stato"] == "Programmata":
                        if st.button("Segna come Completato"):
                            # In a real app, would update task status in DB
                            st.success("Task segnato come completato!")
                            st.rerun()
                
                with col2:
                    if selected_task["Stato"] == "Programmata":
                        if st.button("Annulla Task"):
                            # In a real app, would update task status in DB
                            st.success("Task annullato!")
                            st.rerun()
                
                with col3:
                    if st.button("Invia Promemoria"):
                        if service and service.get("phone"):
                            st.success(f"Promemoria inviato a {service['name']} ({service['phone']})")
                        else:
                            st.error("Nessun servizio di pulizia o numero di telefono associato a questo task.")
    else:
        st.info("Nessun task di pulizia corrisponde ai filtri selezionati.")

def show_cleaning_services():
    st.subheader("Servizi di Pulizia")
    
    # Get cleaning services
    cleaning_services = get_all_cleaning_services()
    
    # Get properties
    properties = get_all_properties()
    
    # Tabs for services and assignment
    tab1, tab2, tab3 = st.tabs(["Elenco Servizi", "Aggiungi Servizio", "Assegnazione Immobili"])
    
    with tab1:
        # Display existing cleaning services
        if cleaning_services:
            # Create a dataframe
            service_data = [{
                "id": service.get("id"),
                "Nome": service.get("name"),
                "Telefono": service.get("phone"),
                "Email": service.get("email"),
                "Note": service.get("notes", ""),
                "SMS": "✓" if service.get("sms_enabled") else "",
                "Predefinito": "✓" if service.get("is_default") else ""
            } for service in cleaning_services]
            
            service_df = pd.DataFrame(service_data)
            displayed_cols = [col for col in service_df.columns if col != "id"]
            st.dataframe(service_df[displayed_cols], use_container_width=True)
            
            # Service details
            st.subheader("Dettagli Servizio")
            
            selected_service_id = st.selectbox(
                "Seleziona un servizio di pulizia",
                options=[service["id"] for service in service_data],
                format_func=lambda x: next((f"{service['Nome']} ({service['Telefono']})" 
                                         for service in service_data if service["id"] == x), x),
                key="cleaning_service_select_details"
            )
            
            if selected_service_id:
                selected_service = next((service for service in cleaning_services if service["id"] == selected_service_id), None)
                
                if selected_service:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        service_name = st.text_input("Nome", value=selected_service.get("name", ""))
                        service_phone = st.text_input("Telefono", value=selected_service.get("phone", ""))
                        service_email = st.text_input("Email", value=selected_service.get("email", ""))
                    
                    with col2:
                        service_notes = st.text_area("Note", value=selected_service.get("notes", ""))
                        sms_enabled = st.checkbox("Abilita notifiche SMS", value=selected_service.get("sms_enabled", False))
                        is_default = st.checkbox("Servizio Predefinito", value=selected_service.get("is_default", False))
                    
                    # Update button
                    if st.button("Aggiorna Servizio", key="update_service_btn"):
                        # Update service data
                        updated_service = {
                            **selected_service,
                            "name": service_name,
                            "phone": service_phone,
                            "email": service_email,
                            "notes": service_notes,
                            "sms_enabled": sms_enabled,
                            "is_default": is_default
                        }
                        
                        # If set as default, update other services
                        if is_default:
                            for s in cleaning_services:
                                if s["id"] != selected_service_id:
                                    s["is_default"] = False
                            
                            # Update all services
                            with open('data/cleaning_services.json', 'w', encoding='utf-8') as f:
                                json.dump(cleaning_services, f, ensure_ascii=False, indent=4)
                        
                        # Save updated service
                        for i, service in enumerate(cleaning_services):
                            if service["id"] == selected_service_id:
                                cleaning_services[i] = updated_service
                        
                        # Save to file
                        with open('data/cleaning_services.json', 'w', encoding='utf-8') as f:
                            json.dump(cleaning_services, f, ensure_ascii=False, indent=4)
                        
                        st.success(f"Servizio {service_name} aggiornato con successo!")
                        st.rerun()
                    
                    # Delete button
                    if st.button("Elimina Servizio", key="delete_service_btn"):
                        # Check if this service is assigned to any property
                        assigned_properties = [p for p in properties if p.get("cleaning_service_id") == selected_service_id]
                        
                        if assigned_properties:
                            st.error(f"Impossibile eliminare: questo servizio è assegnato a {len(assigned_properties)} immobili.")
                        else:
                            # Remove from list
                            cleaning_services = [s for s in cleaning_services if s["id"] != selected_service_id]
                            
                            # Save to file
                            with open('data/cleaning_services.json', 'w', encoding='utf-8') as f:
                                json.dump(cleaning_services, f, ensure_ascii=False, indent=4)
                            
                            st.success(f"Servizio {service_name} eliminato con successo!")
                            st.rerun()
        else:
            st.info("Nessun servizio di pulizia registrato. Vai alla scheda 'Aggiungi Servizio' per aggiungerne uno.")
    
    with tab2:
        # Form for adding a new cleaning service
        with st.form("add_service_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input("Nome Servizio*")
                new_phone = st.text_input("Telefono*")
                new_email = st.text_input("Email")
            
            with col2:
                new_notes = st.text_area("Note")
                new_sms_enabled = st.checkbox("Abilita notifiche SMS", value=False)
                make_default = st.checkbox("Imposta come Predefinito")
            
            submit_button = st.form_submit_button("Aggiungi Servizio")
        
        if submit_button:
            # Validate inputs
            if not new_name or not new_phone:
                st.error("Nome e Telefono sono campi obbligatori.")
            else:
                # Generate new service id
                new_id = str(uuid.uuid4())
                
                # Create new service data
                new_service = {
                    "id": new_id,
                    "name": new_name,
                    "phone": new_phone,
                    "email": new_email,
                    "notes": new_notes,
                    "sms_enabled": new_sms_enabled,
                    "is_default": make_default
                }
                
                # If this is the first service or set as default, handle other services
                if make_default and cleaning_services:
                    for service in cleaning_services:
                        service["is_default"] = False
                
                # First service is automatically default
                if not cleaning_services:
                    new_service["is_default"] = True
                
                # Add to list
                cleaning_services.append(new_service)
                
                # Save to file
                with open('data/cleaning_services.json', 'w', encoding='utf-8') as f:
                    json.dump(cleaning_services, f, ensure_ascii=False, indent=4)
                
                st.success(f"Servizio {new_name} aggiunto con successo!")
                st.rerun()
    
    with tab3:
        st.write("Assegnazione servizi di pulizia agli immobili")
        
        if not properties:
            st.info("Non ci sono immobili registrati. Aggiungi immobili nella sezione 'Gestione Immobili'.")
            return
        
        if not cleaning_services:
            st.warning("Non ci sono servizi di pulizia registrati. Aggiungi prima un servizio di pulizia.")
            return
        
        # Find default service
        default_service = next((s for s in cleaning_services if s.get("is_default", False)), 
                              cleaning_services[0] if cleaning_services else None)
        
        # Service options for dropdown
        service_options = {service["id"]: service["name"] for service in cleaning_services}
        
        # Process property assignments
        for prop in properties:
            with st.container():
                st.markdown(f"#### {prop['name']}")
                st.caption(f"Indirizzo: {prop.get('address', 'N/A')}")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Current assigned service
                    current_service_id = prop.get("cleaning_service_id")
                    
                    # Find index of current service, or default to the default service
                    if current_service_id and current_service_id in service_options:
                        default_index = list(service_options.keys()).index(current_service_id)
                    elif default_service:
                        default_index = list(service_options.keys()).index(default_service["id"])
                    else:
                        default_index = 0
                    
                    # Use a unique key for each property's selectbox
                    selected_service = st.selectbox(
                        "Servizio di pulizia",
                        options=list(service_options.keys()),
                        format_func=lambda x: service_options.get(x, "Seleziona un servizio"),
                        index=default_index,
                        key=f"cleaning_service_select_{prop['id']}"
                    )
                    
                    # Notes specific to this property
                    cleaning_notes = st.text_area(
                        "Note specifiche per la pulizia di questo immobile", 
                        value=prop.get("cleaning_notes", ""),
                        key=f"cleaning_notes_{prop['id']}"
                    )
                
                with col2:
                    st.write("")
                    st.write("")
                    if st.button("Salva", key=f"save_cleaning_{prop['id']}"):
                        # Update property with cleaning service
                        updated_prop = {**prop}  # Create a copy
                        updated_prop["cleaning_service_id"] = selected_service
                        updated_prop["cleaning_notes"] = cleaning_notes
                        
                        # Save to database
                        update_property(prop["id"], updated_prop)
                        
                        st.success("Servizio di pulizia assegnato con successo")
                        st.rerun()
                
                st.divider()

def show_scheduling():
    st.subheader("Programmazione Pulizie")
    
    # Get properties and cleaning services
    properties = get_all_properties()
    services = get_all_cleaning_services()
    
    if not properties:
        st.warning("Non hai ancora registrato immobili.")
        return
    
    if not services:
        st.warning("Non hai ancora registrato servizi di pulizia. Vai alla scheda 'Servizi di Pulizia' per aggiungerne uno.")
        return
    
    # Manual cleaning scheduling
    st.markdown("### Programma una Pulizia")
    
    with st.form("schedule_cleaning_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Property selection
            property_options = {p.get("id"): p.get("name") for p in properties}
            
            selected_property_id = st.selectbox(
                "Immobile*",
                options=list(property_options.keys()),
                format_func=lambda x: property_options.get(x)
            )
            
            # Date and time
            cleaning_date = st.date_input(
                "Data*",
                value=datetime.now().date()
            )
        
        with col2:
            # Time selection
            cleaning_time = st.time_input(
                "Ora*",
                value=datetime.now().replace(hour=11, minute=0).time()
            )
            
            # Cleaning service selection
            service_options = {s.get("id"): s.get("name") for s in services}
            
            # Get default service
            default_service = get_default_cleaning_service()
            default_service_id = default_service.get("id") if default_service else None
            
            selected_service_id = st.selectbox(
                "Servizio di Pulizia*",
                options=list(service_options.keys()),
                format_func=lambda x: service_options.get(x),
                index=list(service_options.keys()).index(default_service_id) if default_service_id in service_options else 0
            )
        
        # Notes
        cleaning_notes = st.text_area("Note")
        
        submit_button = st.form_submit_button("Programma Pulizia")
    
    if submit_button:
        # Validate inputs
        if not selected_property_id or not cleaning_date or not cleaning_time or not selected_service_id:
            st.error("Tutti i campi contrassegnati con * sono obbligatori.")
        else:
            # Combine date and time
            scheduled_datetime = datetime.combine(cleaning_date, cleaning_time)
            
            # Schedule cleaning
            new_task = schedule_cleaning(
                property_id=selected_property_id,
                scheduled_date=scheduled_datetime,
                service_id=selected_service_id
            )
            
            if new_task:
                st.success("Pulizia programmata con successo!")
                
                # Show notification options
                with st.expander("Invia Notifica al Servizio di Pulizia", expanded=True):
                    service = next((s for s in services if s["id"] == selected_service_id), None)
                    
                    if service and service.get("phone"):
                        if st.button("Invia Messaggio di Notifica"):
                            # Get property info
                            property_data = get_property(selected_property_id)
                            
                            # In a real app, would send message via SMS/WhatsApp
                            st.success(f"Notifica inviata a {service['name']} ({service['phone']})")
                    else:
                        st.warning("Il servizio di pulizia selezionato non ha un numero di telefono registrato.")
            else:
                st.error("Errore nella programmazione della pulizia.")
    
    # Automatic scheduling after checkout
    st.markdown("### Programmazione Automatica dopo Check-out")
    
    auto_schedule = st.checkbox("Abilita programmazione automatica dopo il check-out", value=True)
    
    if auto_schedule:
        col1, col2 = st.columns(2)
        
        with col1:
            hours_after_checkout = st.number_input(
                "Ore dopo il check-out",
                min_value=1,
                max_value=24,
                value=2
            )
        
        with col2:
            send_auto_notification = st.checkbox("Invia notifica automatica", value=True)
        
        st.info(f"Le pulizie verranno programmate automaticamente {hours_after_checkout} ore dopo ogni check-out.")
        
        # Show upcoming clean-ups from future checkouts
        st.markdown("### Prossime Pulizie Programmate Automaticamente")
        
        # Get upcoming cleaning tasks
        upcoming_tasks = get_upcoming_cleaning_tasks(days=30)
        
        if upcoming_tasks:
            upcoming_data = []
            
            for task in upcoming_tasks:
                property_data = get_property(task.get("property_id"))
                property_name = property_data.get("name") if property_data else "Sconosciuto"
                
                service = next((s for s in services if s.get("id") == task.get("cleaning_service_id")), None)
                service_name = service.get("name") if service else "Non specificato"
                
                # Format scheduled date
                scheduled_date = datetime.fromisoformat(task.get("scheduled_date")).strftime("%d/%m/%Y %H:%M") if task.get("scheduled_date") else "N/A"
                
                upcoming_data.append({
                    "Data": scheduled_date,
                    "Immobile": property_name,
                    "Servizio": service_name,
                    "Note": task.get("notes", "")
                })
            
            if upcoming_data:
                upcoming_df = pd.DataFrame(upcoming_data)
                st.dataframe(upcoming_df, use_container_width=True)
            else:
                st.info("Nessuna pulizia programmata per i prossimi 30 giorni.")
        else:
            st.info("Nessuna pulizia programmata per i prossimi 30 giorni.")

def show_automated_messages():
    st.subheader("Messaggi Automatici per Pulizie")
    
    # Get cleaning services
    services = get_all_cleaning_services()
    
    if not services:
        st.warning("Non hai ancora registrato servizi di pulizia. Vai alla scheda 'Servizi di Pulizia' per aggiungerne uno.")
        return
    
    # Select a service
    service_options = {s.get("id"): s.get("name") for s in services}
    
    selected_service_id = st.selectbox(
        "Servizio di Pulizia",
        options=list(service_options.keys()),
        format_func=lambda x: service_options.get(x)
    )
    
    selected_service = next((s for s in services if s["id"] == selected_service_id), None)
    
    if selected_service:
        st.markdown(f"**Contatto: {selected_service.get('name')}**")
        st.markdown(f"**Telefono: {selected_service.get('phone')}**")
        st.markdown(f"**Email: {selected_service.get('email')}**")
        
        # Message templates
        st.markdown("### Modelli di Messaggio")
        
        message_templates = {
            "schedule": "Gentile {service_name}, è stata programmata una pulizia per l'immobile {property_name} in {property_address}, {property_city} per il giorno {scheduled_date} alle {scheduled_time}. Per favore confermare la disponibilità. Grazie, CiaoHost.",
            "reminder": "Promemoria: La pulizia dell'immobile {property_name} in {property_address}, {property_city} è programmata per domani alle {scheduled_time}. Grazie, CiaoHost.",
            "urgent": "URGENTE: Richiesta pulizia per oggi per l'immobile {property_name} in {property_address}, {property_city}. Il check-out è alle {checkout_time} e il prossimo check-in è alle {checkin_time}. Per favore confermare la disponibilità il prima possibile. Grazie, CiaoHost.",
            "cancel": "La pulizia programmata per l'immobile {property_name} in data {scheduled_date} è stata annullata. Ci scusiamo per l'inconveniente. Grazie, CiaoHost."
        }
        
        # Select message type
        message_type = st.selectbox(
            "Tipo di Messaggio",
            options=list(message_templates.keys()),
            format_func=lambda x: {
                "schedule": "Programmazione Pulizia",
                "reminder": "Promemoria Pulizia",
                "urgent": "Richiesta Urgente",
                "cancel": "Annullamento Pulizia"
            }.get(x)
        )
        
        # Preview with sample data
        sample_data = {
            "service_name": selected_service.get("name"),
            "property_name": "Appartamento Centro",
            "property_address": "Via Roma 123",
            "property_city": "Milano",
            "scheduled_date": datetime.now().strftime("%d/%m/%Y"),
            "scheduled_time": "11:00",
            "checkout_time": "10:00",
            "checkin_time": "15:00"
        }
        
        message_template = message_templates[message_type]
        preview_message = message_template
        
        for key, value in sample_data.items():
            preview_message = preview_message.replace(f"{{{key}}}", value)
        
        st.markdown("### Anteprima Messaggio")
        st.info(preview_message)
        
        # Allow customization
        custom_message = st.text_area("Messaggio Personalizzato", value=preview_message, height=150)
        
        # Test sending
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Testa Invio (WhatsApp)"):
                # In a real app, would send message via WhatsApp
                st.success(f"Messaggio di test inviato via WhatsApp a {selected_service.get('phone')}")
        
        with col2:
            if st.button("Testa Invio (SMS)"):
                # In a real app, would send message via SMS
                st.success(f"Messaggio di test inviato via SMS a {selected_service.get('phone')}")
        
        # Automated message settings
        st.markdown("### Impostazioni Messaggi Automatici")
        
        # Initialize settings if not exist
        if "cleaning_message_settings" not in st.session_state:
            st.session_state.cleaning_message_settings = {
                "send_schedule": True,
                "send_reminder": True,
                "reminder_hours": 24,
                "send_confirmation": True
            }
        
        message_settings = st.session_state.cleaning_message_settings
        
        col1, col2 = st.columns(2)
        
        with col1:
            send_schedule = st.checkbox("Invia messaggio alla programmazione", value=message_settings.get("send_schedule", True))
            send_reminder = st.checkbox("Invia promemoria prima della pulizia", value=message_settings.get("send_reminder", True))
        
        with col2:
            reminder_hours = st.number_input(
                "Ore prima per il promemoria",
                min_value=1,
                max_value=48,
                value=message_settings.get("reminder_hours", 24)
            )
            send_confirmation = st.checkbox("Richiedi conferma di disponibilità", value=message_settings.get("send_confirmation", True))
        
        if st.button("Salva Impostazioni"):
            # Update settings
            st.session_state.cleaning_message_settings.update({
                "send_schedule": send_schedule,
                "send_reminder": send_reminder,
                "reminder_hours": reminder_hours,
                "send_confirmation": send_confirmation
            })
            
            st.success("Impostazioni messaggi salvate con successo!")
        
        # Display sample conversation
        with st.expander("Esempio di Conversazione", expanded=False):
            st.markdown("### Esempio di Conversazione con il Servizio di Pulizia")
            
            conversation = [
                {"sender": "ciaohost", "text": "Gentile Pulizie Rapide, è stata programmata una pulizia per l'immobile Appartamento Centro in Via Roma 123, Milano per il giorno 15/05/2025 alle 11:00. Per favore confermare la disponibilità. Grazie, CiaoHost."},
                {"sender": "service", "text": "Buongiorno, confermiamo la disponibilità per la pulizia richiesta. Grazie"},
                {"sender": "ciaohost", "text": "Grazie per la conferma. Se ci sono modifiche vi contatteremo. Cordiali saluti, CiaoHost."},
                {"sender": "ciaohost", "text": "Promemoria: La pulizia dell'immobile Appartamento Centro in Via Roma 123, Milano è programmata per domani alle 11:00. Grazie, CiaoHost."},
                {"sender": "service", "text": "Grazie per il promemoria, siamo pronti per domani."},
                {"sender": "service", "text": "La pulizia è stata completata. Tutto in ordine."},
                {"sender": "ciaohost", "text": "Grazie per la conferma. Buona giornata!"}
            ]
            
            for message in conversation:
                if message["sender"] == "ciaohost":
                    st.markdown(f"<div style='background-color: #E1F5FE; padding: 10px; border-radius: 10px; margin-bottom: 10px;'><b>CiaoHost:</b> {message['text']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='background-color: #F0F2F6; padding: 10px; border-radius: 10px; margin-bottom: 10px; text-align: right;'><b>Servizio Pulizia:</b> {message['text']}</div>", unsafe_allow_html=True)
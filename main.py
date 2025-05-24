
import streamlit as st
import google.generativeai as genai
import os
import json
import pandas as pd
from dotenv import load_dotenv
import time
from attached_assets.cleaning_management import (
    show_cleaning_calendar,
    show_cleaning_services,
    show_scheduling,
    show_automated_messages
)
# Note: The 'attached_assets.cleaning_management' module has dependencies
# on a 'utils' directory (e.g., 'utils.database') and potentially a 'data' subdirectory.
# Ensure these are correctly structured for the imports and file access to work.

# import attached_assets.dashboard_creator as dashboard_creator
# import attached_assets.dashboard_creator as dashboard_creator
# import attached_assets.data_insights as data_insights
import attached_assets.dynamic_pricing as dynamic_pricing
# import attached_assets.fiscal_management as fiscal_management
from attached_assets.property_management import show_property_management
# import attached_assets.report_builder as report_builder
import attached_assets.settings as settings

# Sezione per mostrare il logo aziendale in alto a sinistra
def show_company_logo():
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=120, caption="CiaoHost", use_container_width=False)
    else:
        st.warning("Logo aziendale non trovato (logo.png).")

# Puoi chiamare show_company_logo() dove preferisci nel layout, ad esempio subito dopo l'inizio di main()

API_KEY = "AIzaSyB-Lgs26JGbdxdJFVk1-1JQFd2lUfyFXwM"

try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.error(f"Errore durante la configurazione di Gemini: {e}")
    model = None

CONTESTO_IMMOBILIARE = """
Sei un esperto di gestione immobiliare dell'azienda chiamata CiaoHost, devi offrire supporto ai clienti e hai queste capacità:
1. Analizzare dati di mercato e generare report
2. Creare contratti d'affitto/vendita personalizzati
3. Calcolare ROI, Tasso Capitalizzazione e metriche finanziarie
4. Generare descrizioni accattivanti per annunci immobiliari
5. Rispondere a domande tecniche su normative e pratiche notarili
in caso ti domandino chi sei o cosa fai rispondi in modo intelligente, da ora in poi sei CiaoHost AI e se stato costruito da CiaoHost,
devi simulare il tutto. ma non devi sempre ribadire chi sei, solo in caso te lo chiedono. in piu se ti do un immobile devi dirmi se e disponibile o meno e non devi assolutamente dire l'id dell immobile.,

Formatta le risposte con:
- Liste puntate per i concetti chiave
- Tabelle comparative quando utile
- Evidenziazione termini tecnici (es. *cap rate*)
"""

DB_FILE = "DatabaseCiaoHostProprieta.json"
ADMIN_CREDENTIALS = {"username": "admin", "password": "root"}

if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'properties' not in st.session_state:
    st.session_state.properties = {}
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'user_states' not in st.session_state:
    st.session_state.user_states = {}
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login'
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False
if 'current_user_email' not in st.session_state:
    st.session_state.current_user_email = None
if 'admin_state' not in st.session_state:
    st.session_state.admin_state = {'mode': None, 'step': None}
if 'data' not in st.session_state:
    st.session_state.data = None
if 'dashboard_panels' not in st.session_state:
    st.session_state.dashboard_panels = []
if 'saved_dashboards' not in st.session_state:
    st.session_state.saved_dashboards = {}

from utils.json_database import load_database as load_json_db, save_database as save_json_db, get_all_properties

def load_database():
    try:
        data = load_json_db()
        st.session_state.properties = data.get('properties', {})
        st.session_state.users = data.get('users', {})
    except Exception as e:
        st.error(f"Errore durante il caricamento del database: {e}")
        st.session_state.properties = {}
        st.session_state.users = {}
        save_database()

def save_database():
    try:
        save_json_db({
            'properties': st.session_state.properties,
            'users': st.session_state.users
        })
    except Exception as e:
        st.error(f"Errore durante il salvataggio del database: {e}")

def handle_admin_access(message_text):
    admin_state = st.session_state.admin_state

    if message_text.lower().strip() == "/admin":
        admin_state['mode'] = 'auth'
        admin_state['step'] = 'username'
        return "👤 Inserisci username admin:"

    if admin_state.get('mode') == 'auth':
        if admin_state.get('step') == 'username':
            if message_text == ADMIN_CREDENTIALS['username']:
                admin_state['step'] = 'password'
                return "🔑 Inserisci password:"
            else:
                admin_state['mode'] = None
                admin_state['step'] = None
                return "❌ Username errato! Riprova con /admin."

        elif admin_state.get('step') == 'password':
            if message_text == ADMIN_CREDENTIALS['password']:
                admin_state['mode'] = 'active'
                admin_state['step'] = None
                return """🔓 Accesso admin consentito!
Comandi disponibili:
  • /add_property <nome> <tipo> <prezzo> <località> <telefono> <servizi_comma_separated>
    Esempio: /add_property "Villa Sole" B&B 120 Roma +390123456 "WiFi,Piscina"
  • /list_properties
  • /list_users
  • /delete_property <id>
  • /exit_admin (per uscire dalla modalità admin)"""
            else:
                admin_state['mode'] = None
                admin_state['step'] = None
                return "❌ Password errata! Riprova con /admin."

    if admin_state.get('mode') == 'active':
        cmd_parts = message_text.lower().strip().split(maxsplit=1)
        command = cmd_parts[0]

        if command == "/add_property":
            try:
                # Nuovo formato che supporta spazi nel nome della proprietà
                # Formato: /add_property "Nome Proprietà" Tipo Prezzo Località Telefono "Servizi1,Servizi2"
                command_pattern = r'/add_property\s+"([^"]+)"\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+)'
                import re
                match = re.match(command_pattern, message_text.strip())
                
                if not match:
                    return """❌ Formato errato. Usa: 
/add_property "Nome Proprietà" Tipo Prezzo Località Telefono "Servizi1,Servizi2"

Esempio: /add_property "Villa Bella" B&B 120 Roma +390123456 "WiFi,Piscina"
                    
Nota: Il nome della proprietà deve essere tra virgolette."""
                
                name, prop_type, price_str, location, phone, services_str = match.groups()
                
                try:
                    price_value = float(price_str.replace('€', '').replace(',', '.').strip())
                except ValueError:
                    return "❌ Errore: Il prezzo deve essere un numero valido (es. 150.50)."
                
                # Rimuovi le virgolette dai servizi se presenti
                services_str = services_str.strip('"')

                prop_id = str(len(st.session_state.properties) + 1)
                while prop_id in st.session_state.properties:
                    prop_id = str(int(prop_id) + 1)

                st.session_state.properties[prop_id] = {
                    "name": name, "type": prop_type, "price": price_value,
                    "location": location, "phone": phone,
                    "services": [s.strip() for s in services_str.split(',')],
                    "status": "disponibile"
                }
                save_database()
                return f"✅ Proprietà '{name}' aggiunta con ID {prop_id}."
            except Exception as e:
                return f"❌ Errore durante l'aggiunta: {str(e)}"

        elif command == "/list_properties":
            if not st.session_state.properties:
                return "ℹ️ Nessuna proprietà nel database."
            
            prop_list_str = "Elenco Proprietà:\n"
            for pid, prop in st.session_state.properties.items():
                prop_list_str += (f"  • ID {pid}: {prop.get('name', 'N/A')} ({prop.get('type', 'N/A')}) "
                                  f"a {prop.get('location', 'N/A')} - €{prop.get('price', 0):,.2f} "
                                  f"- Status: {prop.get('status', 'N/A')}\n")
            return prop_list_str
            
        elif command == "/list_users":
            if not st.session_state.users:
                return "ℹ️ Nessun utente registrato nel database."
            
            user_list_str = "Elenco Utenti Registrati:\n"
            for email, password in st.session_state.users.items():
                user_list_str += f"  • Email: {email} - Password: {password}\n"
            return user_list_str

        elif command == "/delete_property":
            try:
                if len(cmd_parts) < 2 or not cmd_parts[1]:
                     return "❌ Formato corretto: /delete_property <id>"
                prop_id_to_delete = cmd_parts[1].strip()
                
                if prop_id_to_delete in st.session_state.properties:
                    deleted_prop_name = st.session_state.properties[prop_id_to_delete].get('name', 'Sconosciuta')
                    del st.session_state.properties[prop_id_to_delete]
                    save_database()
                    return f"✅ Immobile '{deleted_prop_name}' (ID: {prop_id_to_delete}) eliminato!"
                return f"❌ Immobile con ID {prop_id_to_delete} non trovato."
            except Exception as e:
                return f"❌ Errore durante l'eliminazione: {str(e)}"
        
        elif command == "/exit_admin":
            admin_state['mode'] = None
            admin_state['step'] = None
            return "🚪 Modalità admin disattivata."
        
        elif message_text.startswith("/"):
            return "❓ Comando admin non riconosciuto. Comandi validi: /add_property, /list_properties, /list_users, /delete_property, /exit_admin."

    return None

def show_property_search():
    st.header("🔍 Ricerca Immobili")
    properties = st.session_state.get('properties', {})

    if not properties:
        st.info("Nessun immobile disponibile al momento.")
        return

    available_properties = {pid: prop for pid, prop in properties.items() if prop.get("status") == "disponibile"}

    if not available_properties:
        st.info("Nessun immobile attualmente disponibile.")
        return

    search_term = st.text_input("Cerca per nome, tipo o località:", key="prop_search_term").lower()
    
    filtered_properties = {}
    if search_term:
        for pid, prop in available_properties.items():
            if (search_term in prop.get('name', '').lower() or
                search_term in prop.get('type', '').lower() or
                search_term in prop.get('location', '').lower()):
                filtered_properties[pid] = prop
        if not filtered_properties:
            st.warning(f"Nessun immobile trovato per '{search_term}'. Mostro tutti i disponibili.")
            filtered_properties = available_properties
    else:
        filtered_properties = available_properties

    for prop_id, prop in filtered_properties.items():
        prop_name = prop.get('name', 'Nome non disponibile')
        prop_type = prop.get('type', 'Tipo non specificato')
        prop_location = prop.get('location', 'Località non specificata')
        
        with st.expander(f"{prop_name} ({prop_type}) - {prop_location}"):
            st.markdown(f"**Prezzo:** €{prop.get('price', 0):,.2f}")
            st.markdown(f"**Contatto:** {prop.get('phone', 'Non disponibile')}")
            st.markdown("**Servizi:**")
            services = prop.get('services', [])
            if services:
                for service in services:
                    st.markdown(f"- {service}")
            else:
                st.markdown("- Nessun servizio specificato.")
            if st.button(f"ℹ️ Mostra Interesse per {prop_name}", key=f"interesse_{prop_id}"):
                st.success(f"Grazie per l'interesse per {prop_name}! Verrai ricontattato presto.")

def show_login():
    st.header("👋 Benvenuto su CiaoHost")
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Accedi")
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pw")
            login_button = st.form_submit_button("Accedi")

            if login_button:
                if email == ADMIN_CREDENTIALS["username"] and password == ADMIN_CREDENTIALS["password"]:
                    st.session_state.is_authenticated = True
                    st.session_state.current_user_email = "admin"
                    st.session_state.current_page = 'home'
                    st.rerun()
                elif email in st.session_state.users and st.session_state.users[email] == password:
                    st.session_state.is_authenticated = True
                    st.session_state.current_user_email = email
                    st.session_state.current_page = 'home'
                    st.rerun()
                else:
                    st.error("Credenziali non valide.")
    
    with col2:
        st.subheader("Registrati")
        with st.form("register_form"):
            new_email = st.text_input("Email per Registrazione", key="reg_email")
            new_password = st.text_input("Password per Registrazione", type="password", key="reg_pw")
            register_button = st.form_submit_button("Registrati")

            if register_button:
                if new_email and new_password:
                    if new_email in st.session_state.users:
                        st.error("Email già registrata!")
                    elif new_email == ADMIN_CREDENTIALS["username"]:
                        st.error("Questo username è riservato.")
                    elif "@" not in new_email or "." not in new_email:
                        st.error("Inserisci un indirizzo email valido.")
                    elif len(new_password) < 6:
                        st.error("La password deve contenere almeno 6 caratteri.")
                    else:
                        st.session_state.users[new_email] = new_password
                        save_database()
                        st.success("Registrazione completata! Ora puoi accedere.")
                else:
                    st.error("Inserisci email e password validi.")

def show_subscription_plans():
    st.header("💼 Piani di Abbonamento CiaoHost")
    st.markdown("Scegli il piano più adatto alle tue esigenze per la gestione dei tuoi immobili.")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader("🔹 Piano Base")
            st.markdown("**25 €/mese** per immobile + 10% commissione")
            st.markdown("---")
            st.write("Include:")
            st.markdown("- Concierge AI multilingua 24/7")
            st.markdown("- Ottimizzazione prezzi con AI")
            st.markdown("- Dashboard base con statistiche")
            st.markdown("- Sistema antifrode ospiti (disattivabile)")
            st.markdown("- Archivio fiscale e fatturazione")
            if st.button("Scegli Piano Base", key="buy_base", use_container_width=True):
                st.success("Ottima scelta! Preparazione della tua dashboard...")
                if 'subscription_purchased' not in st.session_state:
                    if st.session_state.data is None:
                        data = {
                            'Mese': ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu'],
                            'Guadagno': [1200, 1350, 1800, 2200, 2100, 2400],
                            'Occupazione': [75, 82, 88, 95, 93, 98],
                            'Prenotazioni': [10, 12, 15, 18, 17, 20]
                        }
                        st.session_state.data = pd.DataFrame(data)
                    st.session_state.subscription_purchased = True
                    st.session_state.subscription_type = "base"
                    time.sleep(2)
                    st.session_state.current_page = 'dashboard'
                    st.rerun()

    with col2:
        with st.container(border=True):
            st.subheader("🔸 Piano Pro")
            st.markdown("**44,99 €/mese** per immobile + 10% commissione")
            st.markdown("---")
            st.write("Include tutto il Piano Base, più:")
            st.markdown("- Dashboard avanzata e personalizzabile")
            st.markdown("- Analisi predittiva delle prenotazioni")
            st.markdown("- Personalizzazione avanzata del chatbot AI")
            st.markdown("- Supporto tecnico prioritario dedicato")
            st.markdown("- Integrazione API con portali esterni (es. Booking, Airbnb)")
            if st.button("Scegli Piano Pro", key="buy_pro", use_container_width=True):
                st.success("Eccellente scelta! Preparazione della tua dashboard PRO...")
                if 'subscription_purchased' not in st.session_state:
                    if st.session_state.data is None:
                        data = {
                            'Mese': ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu'],
                            'Guadagno': [1200, 1350, 1800, 2200, 2100, 2400],
                            'Occupazione': [75, 82, 88, 95, 93, 98],
                            'Prenotazioni': [10, 12, 15, 18, 17, 20]
                        }
                        st.session_state.data = pd.DataFrame(data)
                    st.session_state.subscription_purchased = True
                    st.session_state.subscription_type = "pro"
                    time.sleep(2)
                    st.session_state.current_page = 'dashboard'
                    st.rerun()
    
    st.markdown("---")
    st.info("Tutti i prezzi sono IVA esclusa. Contattaci per soluzioni personalizzate per grandi portafogli immobiliari.")

def show_dashboard():
    if not st.session_state.get('subscription_purchased', False):
        st.warning("Per accedere alla dashboard è necessario acquistare un piano di abbonamento.")
        st.session_state.current_page = 'subscriptions'
        st.rerun()
        return
    
    st.header("📊 Dashboard - CiaoHost AI")
    
    # Home button in dashboard
    if st.button("🏠 Torna alla Home", key="dashboard_home"):
        st.session_state.current_page = 'home'
        st.rerun()
        
    if st.session_state.data is None:
        data = {
            'Mese': ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu'],
            'Guadagno': [1200, 1350, 1800, 2200, 2100, 2400],
            'Occupazione': [75, 82, 88, 95, 93, 98],
            'Prenotazioni': [10, 12, 15, 18, 17, 20]
        }
        st.session_state.data = pd.DataFrame(data)
    
    df = st.session_state.data
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Guadagno Medio", f"€{df['Guadagno'].mean():.2f}")
    col2.metric("Occupazione Media", f"{df['Occupazione'].mean():.1f}%")
    col3.metric("Prenotazioni Totali", f"{df['Prenotazioni'].sum()}")
    
    # Create line chart for trends
    st.line_chart(df.set_index('Mese'))
    
    # Show data table
    st.subheader("Dati Dettagliati")
    st.dataframe(df)

# Placeholder functions for attached_assets functionalities
def show_cleaning_management_page():
    st.header("🧹 Gestione Pulizie")
    
    tab_titles = ["Calendario Pulizie", "Servizi di Pulizia", "Programmazione Pulizie", "Messaggi Automatici"]
    tab1, tab2, tab3, tab4 = st.tabs(tab_titles)

    with tab1:
        show_cleaning_calendar()
    with tab2:
        show_cleaning_services()
    with tab3:
        show_scheduling()
    with tab4:
        show_automated_messages()

def show_dashboard_creator_page():
    st.header("🛠️ Creazione Dashboard")
    st.write("Contenuto della pagina Creazione Dashboard.")
    # TODO: Implement functionality from attached_assets/dashboard_creator.py

def show_data_insights_page():
    st.header("💡 Analisi Dati")
    st.write("Contenuto della pagina Analisi Dati.")
    # TODO: Implement functionality from attached_assets/data_insights.py

def show_dynamic_pricing_page():
    dynamic_pricing.show_dynamic_pricing()

def show_fiscal_management_page():
    st.header("🧾 Gestione Fiscale")
    
    # Create tabs for different fiscal management functions
    tabs = st.tabs(["Gestione Utenti", "Fatturazione", "Reportistica Fiscale", "Impostazioni"])
    
    with tabs[0]:
        show_user_management()
    
    with tabs[1]:
        show_invoicing()
    
    with tabs[2]:
        show_fiscal_reporting()
    
    with tabs[3]:
        show_fiscal_settings()

def show_user_management():
    """Display and manage users from the database"""
    st.subheader("Gestione Utenti")
    
    # Get users from session state
    users = st.session_state.users
    
    if not users:
        st.info("Non ci sono utenti registrati nel sistema.")
        return
    
    # Create a dataframe for display
    user_data = []
    for i, (email, _) in enumerate(users.items(), 1):
        # Extract username from email
        username = email.split('@')[0] if '@' in email else email
        
        # Generate a fiscal ID (simulated)
        fiscal_id = f"USR{i:04d}"
        
        user_data.append({
            "ID": fiscal_id,
            "Email": email,
            "Username": username,
            "Data Registrazione": "21/05/2025",  # Simulated date
            "Stato": "Attivo"
        })
    
    # Create a dataframe
    user_df = pd.DataFrame(user_data)
    
    # Add search functionality
    search_term = st.text_input("Cerca utente:", placeholder="Inserisci email o username")
    
    if search_term:
        filtered_df = user_df[
            user_df["Email"].str.contains(search_term, case=False) | 
            user_df["Username"].str.contains(search_term, case=False)
        ]
        if filtered_df.empty:
            st.warning(f"Nessun utente trovato per '{search_term}'")
            st.dataframe(user_df, use_container_width=True)
        else:
            st.dataframe(filtered_df, use_container_width=True)
    else:
        st.dataframe(user_df, use_container_width=True)
    
    # User details section
    st.subheader("Dettagli Utente")
    
    # Select a user to view details
    selected_user = st.selectbox(
        "Seleziona un utente",
        options=user_df["Email"].tolist(),
        format_func=lambda x: f"{x} ({next((u['Username'] for u in user_data if u['Email'] == x), '')})"
    )
    
    if selected_user:
        selected_user_data = next((u for u in user_data if u["Email"] == selected_user), None)
        
        if selected_user_data:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**ID Fiscale:** {selected_user_data['ID']}")
                st.markdown(f"**Email:** {selected_user_data['Email']}")
                st.markdown(f"**Username:** {selected_user_data['Username']}")
            
            with col2:
                st.markdown(f"**Data Registrazione:** {selected_user_data['Data Registrazione']}")
                st.markdown(f"**Stato:** {selected_user_data['Stato']}")
                st.markdown(f"**Tipo Account:** {'Standard' if selected_user_data['Email'] != 'admin' else 'Amministratore'}")
            
            # Fiscal actions
            st.subheader("Azioni Fiscali")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Genera Fattura", key=f"gen_invoice_{selected_user_data['ID']}"):
                    st.success(f"Fattura generata per {selected_user_data['Username']}")
            
            with col2:
                if st.button("Esporta Dati Fiscali", key=f"export_{selected_user_data['ID']}"):
                    st.success(f"Dati fiscali esportati per {selected_user_data['Username']}")
            
            with col3:
                if st.button("Invia Promemoria", key=f"remind_{selected_user_data['ID']}"):
                    st.success(f"Promemoria inviato a {selected_user_data['Email']}")

def show_invoicing():
    """Display invoicing functionality"""
    st.subheader("Fatturazione")
    st.info("Questa sezione permetterebbe di gestire la fatturazione per gli utenti.")
    
    # Simulated invoicing data
    if 'invoices' not in st.session_state:
        st.session_state.invoices = [
            {
                "id": "INV001",
                "user_email": next(iter(st.session_state.users.keys()), "esempio@email.com"),
                "amount": 100.0,
                "date": "15/05/2025",
                "status": "Pagata"
            }
        ]
    
    # Display invoices
    invoice_data = []
    for invoice in st.session_state.invoices:
        invoice_data.append({
            "ID": invoice["id"],
            "Utente": invoice["user_email"],
            "Importo": f"€{invoice['amount']:.2f}",
            "Data": invoice["date"],
            "Stato": invoice["status"]
        })
    
    if invoice_data:
        st.dataframe(pd.DataFrame(invoice_data), use_container_width=True)
    else:
        st.info("Nessuna fattura presente nel sistema.")

def show_fiscal_reporting():
    """Display fiscal reporting functionality"""
    st.subheader("Reportistica Fiscale")
    st.info("Questa sezione permetterebbe di generare report fiscali per gli utenti.")
    
    # Simulated reporting options
    report_type = st.selectbox(
        "Tipo di Report",
        ["Fatturazione Mensile", "Riepilogo Annuale", "Dichiarazione IVA", "Report Personalizzato"]
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("Data Inizio")
    
    with col2:
        end_date = st.date_input("Data Fine")
    
    if st.button("Genera Report"):
        st.success(f"Report {report_type} generato per il periodo {start_date} - {end_date}")
        
        # Simulated chart
        chart_data = pd.DataFrame({
            'Mese': ['Gen', 'Feb', 'Mar', 'Apr', 'Mag'],
            'Fatturato': [1200, 1350, 1800, 2200, 2100]
        })
        
        st.bar_chart(chart_data.set_index('Mese'))

def show_fiscal_settings():
    """Display fiscal settings functionality"""
    st.subheader("Impostazioni Fiscali")
    st.info("Questa sezione permetterebbe di configurare le impostazioni fiscali.")
    
    # Simulated settings
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Partita IVA", value="IT12345678901")
        st.text_input("Ragione Sociale", value="CiaoHost Srl")
        st.text_input("Indirizzo", value="Via Roma 123, Milano")
    
    with col2:
        st.selectbox("Regime Fiscale", ["Ordinario", "Forfettario", "Semplificato"])
        st.number_input("Aliquota IVA (%)", value=22)
        st.checkbox("Emetti Fattura Elettronica", value=True)
    
    if st.button("Salva Impostazioni"):
        st.success("Impostazioni fiscali salvate con successo")

def show_property_management_page():
    show_property_management()

def show_report_builder_page():
    st.header("📄 Creazione Report")
    st.write("Contenuto della pagina Creazione Report.")
    # TODO: Implement functionality from attached_assets/report_builder.py

def show_settings_page():
    settings.show_settings()

def main():
    st.set_page_config(
        page_title="CiaoHost AI Manager",
        page_icon="🏡",
        layout="wide",
        initial_sidebar_state="expanded"  # Changed from "collapsed"
    )
    
    load_database()
    
    st.markdown("""
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .stChatInputContainer {
            position: fixed;
            bottom: 0rem;
            left: 0;
            right: 0;
            padding: 0.5rem 1rem;
            background-color: #f0f2f6;
            border-top: 1px solid #e0e0e0;
            z-index: 999;
            width: 100%;
            box-sizing: border-box;
        }
        .main .block-container { padding-bottom: 5rem; }
        .main-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.5rem 1rem;
            border-bottom: 1px solid #e0e0e0;
            background-color: #ffffff;
        }
        .nav-buttons {
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }
        .nav-buttons .stButton button {
            background-color: #4F46E5;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 8px 15px;
            font-weight: 500;
        }
        .nav-buttons .stButton button:hover {
            background-color: #3730A3;
        }
        .nav-buttons .stButton button.logout-btn {
            background-color: #e74c3c;
        }
        .nav-buttons .stButton button.logout-btn:hover {
            background-color: #c0392b;
        }
        /* Fix for navigation buttons alignment */
        .nav-buttons {
            display: grid !important;
            grid-template-columns: repeat(6, minmax(80px, 1fr)) !important;
            grid-gap: 5px !important;
            width: 100% !important;
            margin-left: auto !important;
        }
        
        /* Target the horizontal container that Streamlit creates */
        .nav-buttons > div {
            display: contents !important;
        }
        
        /* Target each column in the horizontal container */
        .nav-buttons > div > div {
            margin: 0 !important;
            padding: 0 !important;
            height: auto !important;
        }
        
        /* Target the button containers */
        .nav-buttons .stButton {
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        /* Style the actual buttons */
        .nav-buttons .stButton button {
            width: 100% !important;
            height: 40px !important;
            min-height: 40px !important;
            max-height: 40px !important;
            padding: 0 10px !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        
        /* Ensure the header maintains its layout with sidebar open */
        .main-header {
            width: 100% !important;
            max-width: 100% !important;
            padding: 0.5rem 1rem !important;
            box-sizing: border-box !important;
            display: flex !important;
            flex-wrap: wrap !important;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    header_cols = st.columns([1, 3, 3])
    with header_cols[0]:
        show_company_logo()
    
    with header_cols[1]:
        st.markdown('<div class="title-container"><h1>CiaoHost AI Assistant 🏡</h1></div>', unsafe_allow_html=True)

    with header_cols[2]:
        st.markdown('<div class="nav-buttons">', unsafe_allow_html=True)
        if st.session_state.get('is_authenticated', False) and st.session_state.current_page != 'dashboard':
            nav_cols = st.columns(6)
            if nav_cols[0].button("🏠 Home", key="nav_home"):
                st.session_state.current_page = 'home'
                st.rerun()
            if nav_cols[1].button("🤖 AI Chat", key="nav_ai"):
                st.session_state.current_page = 'ai'
                st.rerun()
            if nav_cols[2].button("🔍 Ricerca", key="nav_search"):
                st.session_state.current_page = 'search_properties'
                st.rerun()
            if nav_cols[3].button("💼 Piani", key="nav_sub"):
                st.session_state.current_page = 'subscriptions'
                st.rerun()
            if nav_cols[4].button("📊 Dashboard", key="nav_dashboard"):
                st.session_state.current_page = 'dashboard'
                st.rerun()
            if nav_cols[5].button("🚪 Logout", key="nav_logout"):
                st.session_state.is_authenticated = False
                st.session_state.current_page = 'login'
                st.session_state.messages = []
                st.session_state.admin_state = {'mode': None, 'step': None}
                st.session_state.current_user_email = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Sidebar Navigation
    if st.session_state.get('is_authenticated', False):
        with st.sidebar:
            st.title("Menu Navigazione")
            st.markdown("---")
            if st.button("🏠 Home Principale", key="sidebar_home", use_container_width=True):
                st.session_state.current_page = 'home'
                st.rerun()
            if st.button("🤖 Assistente AI", key="sidebar_ai", use_container_width=True):
                st.session_state.current_page = 'ai'
                st.rerun()
            if st.button("🔍 Ricerca Immobili", key="sidebar_search", use_container_width=True):
                st.session_state.current_page = 'search_properties'
                st.rerun()
            if st.button("💼 Piani Abbonamento", key="sidebar_subscriptions", use_container_width=True):
                st.session_state.current_page = 'subscriptions'
                st.rerun()
            if st.button("📊 Dashboard Dati", key="sidebar_dashboard", use_container_width=True):
                st.session_state.current_page = 'dashboard'
                st.rerun()
            
            if st.session_state.get('subscription_purchased', False): # Show only if subscription is active
                st.markdown("---")
                st.subheader("Strumenti Gestionali")
                
                if st.button("🧹 Gestione Pulizie", key="sidebar_cleaning", use_container_width=True):
                    st.session_state.current_page = 'cleaning_management'
                    st.rerun()
                if st.button("🛠️ Creazione Dashboard", key="sidebar_dashboard_creator", use_container_width=True):
                    st.session_state.current_page = 'dashboard_creator'
                    st.rerun()
                if st.button("💡 Analisi Dati", key="sidebar_data_insights", use_container_width=True):
                    st.session_state.current_page = 'data_insights'
                    st.rerun()
                if st.button("⚖️ Prezzi Dinamici", key="sidebar_dynamic_pricing", use_container_width=True):
                    st.session_state.current_page = 'dynamic_pricing'
                    st.rerun()
                if st.button("🧾 Gestione Fiscale", key="sidebar_fiscal_management", use_container_width=True):
                    st.session_state.current_page = 'fiscal_management'
                    st.rerun()
                if st.button("🏘️ Gestione Proprietà", key="sidebar_property_management", use_container_width=True):
                    st.session_state.current_page = 'property_management'
                    st.rerun()
                if st.button("📄 Creazione Report", key="sidebar_report_builder", use_container_width=True):
                    st.session_state.current_page = 'report_builder'
                    st.rerun()
                if st.button("⚙️ Impostazioni", key="sidebar_settings", use_container_width=True):
                    st.session_state.current_page = 'settings'
                    st.rerun()

            st.markdown("---")
            if st.button("🚪 Logout", key="sidebar_logout", use_container_width=True):
                st.session_state.is_authenticated = False
                st.session_state.current_page = 'login'
                st.session_state.messages = []
                st.session_state.admin_state = {'mode': None, 'step': None}
                st.session_state.current_user_email = None
                st.rerun()

    if not st.session_state.get('is_authenticated', False):
        show_login()
    else:
        # Page rendering logic based on st.session_state.current_page
        if st.session_state.current_page == 'home':
            st.header(f"Bentornato su CiaoHost, {st.session_state.get('current_user_email', 'Utente').split('@')[0]}!")
            st.markdown("Utilizza la navigazione in alto per esplorare le funzionalità.")
            
            col1, col2 = st.columns(2)
            total_props = len(st.session_state.get('properties', {}))
            col1.metric("Immobili Gestiti", total_props)
            col2.metric("Utenti Registrati", len(st.session_state.get('users', {})))

        elif st.session_state.current_page == 'search_properties':
            show_property_search()
        elif st.session_state.current_page == 'subscriptions':
            show_subscription_plans()
        elif st.session_state.current_page == 'dashboard':
            show_dashboard()
        elif st.session_state.current_page == 'ai':
            st.header("🤖 Chatta con CiaoHost AI")
            st.caption("Puoi chiedere informazioni e assistenza.")
            
            chat_container = st.container()
            with chat_container:
                for message in st.session_state.get('messages', []):
                    role = message["role"]
                    content = message["content"]
                    avatar_map = {"user": "👤", "bot": "🤖", "admin": "⚙️"}
                    
                    with st.chat_message(name=role, avatar=avatar_map.get(role)):
                        st.markdown(content)
            
            user_input = st.chat_input("Scrivi il tuo messaggio...", key="chat_input")
            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                admin_response = handle_admin_access(user_input)
                if admin_response:
                    st.session_state.messages.append({"role": "admin", "content": admin_response})
                else:
                    if not (st.session_state.admin_state and st.session_state.admin_state.get('mode') == 'auth'):
                        if model:
                            try:
                                property_summary = "Nessuna proprietà nel database."
                                if st.session_state.properties:
                                    prop_count = len(st.session_state.properties)
                                    property_summary = f"{prop_count} proprietà nel database:\n"
                                    for prop_id, prop in st.session_state.properties.items():
                                        prop_name = prop.get('name', 'N/A')
                                        prop_type = prop.get('type', 'N/A')
                                        prop_location = prop.get('location', 'N/A')
                                        property_summary += f"- ID {prop_id}: {prop_name} ({prop_type}) a {prop_location}\n"
                                
                                conversation_history = []
                                for msg in st.session_state.messages[-10:]:
                                    gemini_role = "user" if msg["role"] == "user" else "model"
                                    conversation_history.append({"role": gemini_role, "parts": [{"text": msg["content"]}]})
                            
                                if conversation_history and conversation_history[-1]["role"] == "user":
                                    current_prompt_text = conversation_history.pop()["parts"][0]["text"]
                                else:
                                    current_prompt_text = user_input

                                final_prompt = f"{CONTESTO_IMMOBILIARE}\n\n{property_summary}\n\n{current_prompt_text}"
                                response = model.generate_content([{"role": "user", "parts": [{"text": final_prompt}]}])
                                bot_reply = response.text
                            except Exception as e:
                                bot_reply = f"🤖 Scusa, ho riscontrato un errore: {str(e)}"
                        else:
                            bot_reply = "🤖 Il modello AI non è disponibile al momento."
                        
                        st.session_state.messages.append({"role": "bot", "content": bot_reply})
                
                st.rerun()
        elif st.session_state.current_page == 'cleaning_management':
            show_cleaning_management_page()
        elif st.session_state.current_page == 'dashboard_creator':
            show_dashboard_creator_page()
        elif st.session_state.current_page == 'data_insights':
            show_data_insights_page()
        elif st.session_state.current_page == 'dynamic_pricing':
            show_dynamic_pricing_page()
        elif st.session_state.current_page == 'fiscal_management':
            show_fiscal_management_page()
        elif st.session_state.current_page == 'property_management':
            show_property_management_page()
        elif st.session_state.current_page == 'report_builder':
            show_report_builder_page()
        elif st.session_state.current_page == 'settings':
            show_settings_page()
        else:
            # Fallback for any unknown page state
            valid_pages = [
                'home', 'search_properties', 'subscriptions', 'dashboard', 'ai', 'login',
                'cleaning_management', 'dashboard_creator', 'data_insights',
                'dynamic_pricing', 'fiscal_management', 'property_management',
                'report_builder', 'settings'
            ]
            if st.session_state.current_page not in valid_pages:
                 st.error(f"Pagina '{st.session_state.current_page}' non trovata o non implementata.")
                 # Optionally, redirect to home:
                 # st.session_state.current_page = 'home'
                 # st.rerun()

if __name__ == "__main__":
    main()

import streamlit as st
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
import time

API_KEY = "AIzaSyB-Lgs26JGbdxdJFVk1-1JQFd2lUfyFXwM"

try:
    genai.configure(api_key=API_KEY)
    # Using a commonly available model. Update if you have access to a specific version.
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.error(f"Errore durante la configurazione di Gemini: {e}")
    model = None # Ensure model is None if configuration fails

# Contesto specializzato per immobili
CONTESTO_IMMOBILIARE = """
Sei un esperto di gestione immobiliare dell'azienda chiamata CiaoHost con queste capacità:
1. Analizzare dati di mercato e generare report
2. Creare contratti d'affitto/vendita personalizzati
3. Calcolare ROI, Tasso Capitalizzazione e metriche finanziarie
4. Generare descrizioni accattivanti per annunci immobiliari
5. Rispondere a domande tecniche su normative e pratiche notarili
in caso ti domandino chi sei o cosa fai rispondi in modo intelligente, da ora in poi sei CiaoHost AI e se stato costruito da CiaoHost,
devi simulare il tutto.

Formatta le risposte con:
- Liste puntate per i concetti chiave
- Tabelle comparative quando utile
- Evidenziazione termini tecnici (es. *cap rate*)
"""

# Database e sicurezza
DB_FILE = "DatabaseCiaoHostProprieta.json" # Standardized name
ADMIN_CREDENTIALS = {"username": "admin", "password": "root"}

# Inizializzazione session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'properties' not in st.session_state:
    st.session_state.properties = {}
if 'users' not in st.session_state: # From second script, good for user management
    st.session_state.users = {}
if 'user_states' not in st.session_state: # From first script, kept if needed later
    st.session_state.user_states = {}
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login'
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False
if 'current_user_email' not in st.session_state: # To store logged-in user's email
    st.session_state.current_user_email = None
if 'admin_state' not in st.session_state: # For interactive admin login
    st.session_state.admin_state = {'mode': None, 'step': None}

def load_database():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            st.session_state.properties = data.get('properties', {})
            st.session_state.users = data.get('users', {})
    except (FileNotFoundError, json.JSONDecodeError):
        # If file not found or corrupt, initialize with empty data and save
        st.session_state.properties = {}
        st.session_state.users = {}
        save_database()

def save_database():
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump({
                'properties': st.session_state.properties,
                'users': st.session_state.users
            }, f, indent=2, ensure_ascii=False)
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
                admin_state['mode'] = None # Reset state
                admin_state['step'] = None
                return "❌ Username errato! Riprova con /admin."

        elif admin_state.get('step') == 'password':
            if message_text == ADMIN_CREDENTIALS['password']:
                admin_state['mode'] = 'active'
                admin_state['step'] = None
                return """🔓 Accesso admin consentito!
Comandi disponibili:
  • /add_property <nome> <tipo> <prezzo> <località> <telefono> <servizi_comma_separated>
    Esempio: /add_property Villa-Sole B&B 120 Roma +390123456 "WiFi,Piscina"
  • /list_properties
  • /list_users
  • /delete_property <id>
  • /exit_admin (per uscire dalla modalità admin)"""
            else:
                admin_state['mode'] = None # Reset state
                admin_state['step'] = None
                return "❌ Password errata! Riprova con /admin."

    if admin_state.get('mode') == 'active':
        cmd_parts = message_text.lower().strip().split(maxsplit=1)
        command = cmd_parts[0]

        if command == "/add_property":
            try:
                # Original message_text is needed for case-sensitive parts like name, location
                parts = message_text.strip().split(maxsplit=6)
                if len(parts) != 7: # /add_property + 6 args
                    return "❌ Formato errato. Usa: /add_property <nome> <tipo> <prezzo> <località> <telefono> <servizi>"
                
                _, name, prop_type, price_str, location, phone, services_str = parts
                
                try:
                    price_value = float(price_str.replace('€', '').replace(',', '.').strip()) # Use . for decimal
                except ValueError:
                    return "❌ Errore: Il prezzo deve essere un numero valido (es. 150.50)."

                prop_id = str(len(st.session_state.properties) + 1)
                while prop_id in st.session_state.properties: # Ensure unique ID
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
        
        elif message_text.startswith("/"): # Unrecognized admin command
            return "❓ Comando admin non riconosciuto. Comandi validi: /add_property, /list_properties, /list_users, /delete_property, /exit_admin."

    return None # No admin action taken or message not for admin

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
            filtered_properties = available_properties # Show all if search yields no results
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
            # Add a button to simulate interest or contact
            if st.button(f"ℹ️ Mostra Interesse per {prop_name}", key=f"interesse_{prop_id}"):
                st.success(f"Grazie per l'interesse per {prop_name}! Verrai ricontattato presto. (Simulazione)")

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
                    elif "@" not in new_email or "." not in new_email: # Basic email validation
                        st.error("Inserisci un indirizzo email valido.")
                    elif len(new_password) < 6: # Basic password strength
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
                st.success("Ottima scelta! (Funzionalità di acquisto non implementata)")

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
                st.success("Eccellente! Stai passando al Pro! (Funzionalità di acquisto non implementata)")
    
    st.markdown("---")
    st.info("Tutti i prezzi sono IVA esclusa. Contattaci per soluzioni personalizzate per grandi portafogli immobiliari.")


def main():
    st.set_page_config(
        page_title="CiaoHost AI Manager",
        page_icon="logo.png", # Ensure logo.png is in the root directory or use an emoji like "🏡"
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    load_database() # Load data at the start
    st.markdown("""
    <style>
        /* General body styling */
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }

        /* Chat input fixed at bottom */
        .stChatInputContainer {
            position: fixed;
            bottom: 0rem; /* Adjust as needed */
            left: 0;
            right: 0;
            padding: 0.5rem 1rem; /* Add some padding */
            background-color: #f0f2f6; /* Match Streamlit's theme light background */
            border-top: 1px solid #e0e0e0;
            z-index: 999;
            width: 100%; /* Ensure it spans the full width */
            box-sizing: border-box; /* Include padding and border in the element's total width and height */
        }
        /* Add padding to the bottom of the main content area to prevent overlap with fixed chat input */
        .main .block-container { padding-bottom: 5rem; /* Should be more than chat input height */ }
        
        /* Header styling */
        .main-header { display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 1rem; border-bottom: 1px solid #e0e0e0; background-color: #ffffff; }
        .main-header img { max-height: 50px; margin-right: 15px; }
        .main-header .title-container h1 { margin: 0; font-size: 1.8em; color: #333; }
        .nav-buttons { display: flex; gap: 0.5rem; align-items: center; }
        .nav-buttons .stButton button { background-color: #4F46E5; color: white; border-radius: 8px; border: none; padding: 8px 15px; font-weight: 500; }
        .nav-buttons .stButton button:hover { background-color: #3730A3; }
        .nav-buttons .stButton button.logout-btn { background-color: #e74c3c; } /* Specific style for logout */
        .nav-buttons .stButton button.logout-btn:hover { background-color: #c0392b; }


        /* Styling for st.expander to make it more card-like */
        .stExpander {
            border: 1px solid #ddd !important;
            border-radius: 8px !important;
            padding: 10px !important;
            margin-bottom: 10px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        }
        .stExpander header { font-weight: bold; font-size: 1.1em; }

    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    header_cols = st.columns([1, 3, 3]) # Logo, Title, Nav
    with header_cols[0]:
        try:
            st.image("logo.png", width=70) # Ensure logo.png is present
        except Exception:
            st.markdown("<h3>CiaoHost</h3>", unsafe_allow_html=True) # Fallback text logo
    
    with header_cols[1]:
        st.markdown('<div class="title-container"><h1>CiaoHost AI Assistant</h1></div>', unsafe_allow_html=True)

    with header_cols[2]:
        st.markdown('<div class="nav-buttons">', unsafe_allow_html=True)
        nav_button_cols = st.columns(5 if st.session_state.get('is_authenticated', False) else 1) # Adjust columns based on auth state

        if st.session_state.get('is_authenticated', False):
            if nav_button_cols[0].button("🏠 Home", key="hdr_home_btn", use_container_width=True):
                st.session_state.current_page = 'home'
                st.rerun()
            if nav_button_cols[1].button("🤖 AI Chat", key="hdr_ai_btn", use_container_width=True):
                st.session_state.current_page = 'ai'
                st.rerun()
            if nav_button_cols[2].button("🔍 Ricerca", key="hdr_search_btn", use_container_width=True):
                st.session_state.current_page = 'search_properties'
                st.rerun()
            if nav_button_cols[3].button("💼 Piani", key="hdr_sub_btn", use_container_width=True):
                st.session_state.current_page = 'subscriptions'
                st.rerun()
            if nav_button_cols[4].button("🚪 Logout", key="hdr_logout_btn", use_container_width=True):
                st.session_state.is_authenticated = False
                st.session_state.current_page = 'login'
                st.session_state.messages = []
                st.session_state.admin_state = {'mode': None, 'step': None}
                st.session_state.current_user_email = None
                st.rerun()
        else:
            pass # Login form is shown in main content area
        st.markdown('</div>', unsafe_allow_html=True) # Close nav-buttons
    st.markdown('</div>', unsafe_allow_html=True) # Close main-header
    # Page Content
    if not st.session_state.get('is_authenticated', False):
        show_login()
    else:
        if st.session_state.current_page == 'home':
            st.header(f"Bentornato su CiaoHost, {st.session_state.get('current_user_email', 'Utente').split('@')[0]}!")
            st.markdown("Utilizza la navigazione in alto per esplorare le funzionalità.")
            st.subheader("Panoramica Rapida")
            col1, col2 = st.columns(2)
            total_props = len(st.session_state.get('properties', {}))
            col1.metric("Immobili Gestiti", total_props)
            col2.metric("Utenti Registrati", len(st.session_state.get('users', {})))


        elif st.session_state.current_page == 'search_properties':
            show_property_search()
        elif st.session_state.current_page == 'subscriptions':
            show_subscription_plans()
        elif st.session_state.current_page == 'ai':
            st.header("🤖 Chatta con CiaoHost AI")
            st.caption("Puoi chiedere informazioni e assistenza.")
            chat_display_container = st.container() # Removed fixed height to allow natural flow
                                                    # Add height if you want a scrollable fixed-size chat window: height=500

            with chat_display_container:
                for i, message in enumerate(st.session_state.get('messages', [])):
                    role = message["role"]
                    content = message["content"]
                    avatar_map = {"user": "👤", "bot": "🤖", "admin": "⚙️"}
                    
                    with st.chat_message(name=role, avatar=avatar_map.get(role)):
                        st.markdown(content)
            
            # Chat input (styled to be at the bottom by CSS)
            user_input = st.chat_input("Scrivi il tuo messaggio...", key="ai_chat_input")

            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})

                admin_response = handle_admin_access(user_input)
                if admin_response:
                    st.session_state.messages.append({"role": "admin", "content": admin_response})
                else:
                    # Only query AI if not an admin command AND not in the middle of admin auth
                    if not (st.session_state.admin_state and st.session_state.admin_state.get('mode') == 'auth'):
                        if model: # Check if model was initialized successfully
                            try:
                                property_summary = "Nessuna proprietà nel database."
                                if st.session_state.properties:
                                    prop_count = len(st.session_state.properties)
                                    property_summary = f"{prop_count} proprietà nel database. Esempio: "
                                    # Show a brief summary of one property if available
                                    first_prop_id = next(iter(st.session_state.properties))
                                    first_prop = st.session_state.properties[first_prop_id]
                                    property_summary += f"{first_prop.get('name', 'N/A')} ({first_prop.get('type', 'N/A')})."
                                
                                conversation_history = []
                                for msg in st.session_state.messages[-10:]: # last 10 messages for context
                                    
                                    gemini_role = "user" if msg["role"] == "user" else "model"
                                    conversation_history.append({"role": gemini_role, "parts": [{"text": msg["content"]}]})
                            
                                if conversation_history and conversation_history[-1]["role"] == "user":
                                     current_prompt_text = conversation_history.pop()["parts"][0]["text"]
                                else:
                                     current_prompt_text = user_input # Fallback

                                final_prompt_for_model = (
                                    f"{CONTESTO_IMMOBILIARE}\n\n"
                                    f"Stato Attuale del Database (Sommario): {property_summary}\n\n"
                                    f"Richiesta Utente Corrente: {current_prompt_text}"
                                )
                                
                                

                                full_request_content = conversation_history + [{"role": "user", "parts": [{"text": final_prompt_for_model}]}]
                                response = model.generate_content(full_request_content)
                                bot_reply = response.text
                            except Exception as e:
                                bot_reply = f"🤖 Scusa, ho riscontrato un errore tecnico: {str(e)}"
                                st.error(f"Errore API Gemini: {e}")
                        else:
                            bot_reply = "🤖 Il modello AI non è disponibile al momento. Controlla la configurazione."
                        
                        st.session_state.messages.append({"role": "bot", "content": bot_reply})
                
                st.rerun()

if __name__ == "__main__":
    main()

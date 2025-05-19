import streamlit as st
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
import time

# Configurazione ambiente e API
load_dotenv()
genai.configure(api_key="AIzaSyB-Lgs26JGbdxdJFVk1-1JQFd2lUfyFXwM")
model = genai.GenerativeModel('gemini-2.0-flash')

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
DB_FILE = "DatabaseCiaoHostProprietà"
ADMIN_CREDENTIALS = {"username": "admin", "password": "root"}

# Inizializzazione session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'properties' not in st.session_state:
    st.session_state.properties = {}
if 'user_states' not in st.session_state:
    st.session_state.user_states = {}

# Funzioni di gestione database
def load_database():
    try:
        with open(DB_FILE, "r") as f:
            st.session_state.properties = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        st.session_state.properties = {}
        save_database()

def save_database():
    with open(DB_FILE, "w") as f:
        json.dump(st.session_state.properties, f, indent=2)

# Funzioni per gestione comandi admin
def handle_admin_commands(user_id, text):
    if text.startswith("/admin"):
        st.session_state.user_states[user_id] = {"mode": "admin_auth", "step": "username"}
        return "Inserisci username admin:"
        
    if user_id in st.session_state.user_states:
        state = st.session_state.user_states[user_id]
        
        if state["mode"] == "admin_auth":
            if state["step"] == "username":
                if text == ADMIN_CREDENTIALS["username"]:
                    state["step"] = "password"
                    return "Inserisci password:"
                return "Username errato!"
            
            elif state["step"] == "password":
                if text == ADMIN_CREDENTIALS["password"]:
                    st.session_state.user_states[user_id] = {"mode": "admin"}
                    return "🔓 Accesso admin consentito!\nComandi disponibili:\n" \
                           "/add <id> <tipo> <prezzo> <località> <telefono> <servizi>\n" \
                           "/delete <id>\n" \
                           "/modify <id> <campo> <nuovo_valore>\n" \
                           "/list"
                return "Password errata!"
        
        elif state["mode"] == "admin":
            if text.startswith("/add"):
                try:
                    _, prop_id, prop_type, price, location, phone, services = text.split(maxsplit=6)
                    st.session_state.properties[prop_id] = {
                        "type": prop_type,
                        "price": float(price),
                        "location": location,
                        "phone": phone,
                        "services": services.split(","),
                        "status": "disponibile"
                    }
                    save_database()
                    return f"✅ Immobile {prop_id} aggiunto!"
                except Exception as e:
                    return f"❌ Errore: Formato corretto:\n/add ID TIPO PREZZO 'LOCALITÀ' TELEFONO 'SERVIZIO1,SERVIZIO2'"
            
            elif text.startswith("/delete"):
                try:
                    _, prop_id = text.split()
                    del st.session_state.properties[prop_id]
                    save_database()
                    return f"✅ Immobile {prop_id} eliminato!"
                except KeyError:
                    return "❌ Immobile non trovato"
            
            elif text.startswith("/modify"):
                try:
                    _, prop_id, field, value = text.split(maxsplit=3)
                    if field == "services":
                        st.session_state.properties[prop_id][field] = value.split(",")
                    else:
                        st.session_state.properties[prop_id][field] = value
                    save_database()
                    return f"✅ Immobile {prop_id} modificato!"
                except Exception as e:
                    return f"❌ Errore: {str(e)}"
            
            elif text.startswith("/list"):
                return json.dumps(st.session_state.properties, indent=2)
            
    return None

# Interfaccia Streamlit
def main():
    st.set_page_config(
        page_title="CiaoHost AI Manager",
        page_icon="🏡",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Carica il database
    load_database()
    
    # CSS personalizzato
    st.markdown("""
    <style>
        .stChatInput {position: fixed; bottom: 20px; width: 70%;}
        .stChatMessage {border-radius: 15px; padding: 15px;}
        .user-message {background-color: white; color: #1F2937; margin-left: 20%; border: 1px solid #4F46E5; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}
        .bot-message {background-color: #4F46E5; color: white;}
        .admin-message {background-color: #10B981; color: white;}
        .stButton button {background-color: #4F46E5; color: white;}
        .stTextInput input {border-radius: 20px;}
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    col1, col2 = st.columns([4,1])
    with col1:
        st.title("🏡 CiaoHost AI Assistant")
    with col2:
        if st.button("ℹ️ Assistenza"):
            st.experimental_set_query_params(page="assistenza")
            st.rerun()
    
    # Area chat
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message stChatMessage">
                <strong>Tu:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        elif message["role"] == "bot":
            st.markdown(f"""
            <div class="bot-message stChatMessage">
                <strong>CiaoHost AI:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        elif message["role"] == "admin":
            st.markdown(f"""
            <div class="admin-message stChatMessage">
                <strong>ADMIN:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
    
    # Input utente
    user_input = st.chat_input("Scrivi il tuo messaggio...")
    
    if user_input:
        # Aggiungi messaggio utente alla cronologia
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Gestione comandi admin
        admin_response = handle_admin_commands("user1", user_input)
        if admin_response:
            st.session_state.messages.append({"role": "admin", "content": admin_response})
            st.rerun()
        
        # Risposta normale dell'AI
        else:
            full_prompt = f"{CONTESTO_IMMOBILIARE}\nDatabase: {st.session_state.properties}\nUtente: {user_input}"
            response = model.generate_content(full_prompt)
            st.session_state.messages.append({"role": "bot", "content": response.text})
            st.rerun()

if __name__ == "__main__":
    main()
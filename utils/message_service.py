import os
import json
import random
import streamlit as st
from datetime import datetime
from utils.ai_assistant import generate_automated_messages

# Controllo se esiste il file twilio
try:
    from twilio.rest import Client
    TWILIO_INSTALLED = True
except ImportError:
    TWILIO_INSTALLED = False

# Controlla se i segreti Twilio sono configurati
def has_twilio_keys():
    return (os.environ.get("TWILIO_ACCOUNT_SID") and 
            os.environ.get("TWILIO_AUTH_TOKEN") and 
            os.environ.get("TWILIO_PHONE_NUMBER"))

def send_message(to_phone, message_text, message_type="notification", property_data=None, via_sms=False):
    """
    Invia un messaggio, opzionalmente tramite SMS se Twilio è configurato
    
    Args:
        to_phone (str): Numero di telefono del destinatario
        message_text (str): Testo del messaggio
        message_type (str): Tipo di messaggio (notification, cleaning, checkout, etc.)
        property_data (dict): Dati dell'immobile associato al messaggio
        via_sms (bool): Se True, invia via SMS (richiede Twilio configurato)
        
    Returns:
        dict: Risultato dell'invio con status e messaggio
    """
    # Normalizza il numero di telefono
    if to_phone and to_phone.startswith("+"):
        phone = to_phone
    else:
        phone = f"+39{to_phone}" if to_phone else None
    
    # Crea log del messaggio
    message_log = {
        "id": f"msg_{random.randint(10000, 99999)}_{int(datetime.now().timestamp())}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "to": phone,
        "message": message_text,
        "type": message_type,
        "status": "pending",
        "property_id": property_data.get("id") if property_data else None
    }
    
    # Salva in session state
    if "message_logs" not in st.session_state:
        st.session_state.message_logs = []
    
    # Invia via SMS se richiesto e possibile
    if via_sms and TWILIO_INSTALLED and has_twilio_keys():
        try:
            client = Client(
                os.environ.get("TWILIO_ACCOUNT_SID"),
                os.environ.get("TWILIO_AUTH_TOKEN")
            )
            
            sms = client.messages.create(
                body=message_text,
                from_=os.environ.get("TWILIO_PHONE_NUMBER"),
                to=phone
            )
            
            message_log["status"] = "sent"
            message_log["sms_sid"] = sms.sid
            st.session_state.message_logs.append(message_log)
            
            # Salva i log dei messaggi
            save_message_logs()
            
            return {"status": "success", "message": f"Messaggio inviato con successo a {phone}"}
            
        except Exception as e:
            message_log["status"] = "failed"
            message_log["error"] = str(e)
            st.session_state.message_logs.append(message_log)
            
            # Salva i log dei messaggi
            save_message_logs()
            
            return {"status": "error", "message": f"Errore nell'invio del messaggio: {str(e)}"}
    else:
        # Modalità simulazione (senza SMS)
        message_log["status"] = "simulated"
        st.session_state.message_logs.append(message_log)
        
        # Salva i log dei messaggi
        save_message_logs()
        
        return {"status": "simulated", "message": f"Messaggio simulato per {phone}: {message_text[:30]}..."}

def notify_cleaning_service(property_id, booking, checkout_date):
    """
    Notifica il servizio di pulizia per un checkout
    
    Args:
        property_id (str): ID dell'immobile
        booking (dict): Dati della prenotazione
        checkout_date (str): Data di checkout
        
    Returns:
        dict: Risultato dell'invio con status e messaggio
    """
    from utils.database import get_property, get_cleaning_service_by_id
    
    property_data = get_property(property_id)
    
    if not property_data:
        return {"status": "error", "message": "Immobile non trovato"}
    
    # Ottieni il servizio di pulizia associato all'immobile o quello predefinito
    cleaning_service_id = property_data.get("cleaning_service_id")
    if cleaning_service_id:
        cleaning_service = get_cleaning_service_by_id(cleaning_service_id)
    else:
        from utils.database import get_default_cleaning_service
        cleaning_service = get_default_cleaning_service()
    
    if not cleaning_service:
        return {"status": "error", "message": "Servizio di pulizia non trovato"}
    
    # Genera il messaggio di notifica
    message = f"""
    🧹 NOTIFICA PULIZIA
    
    Immobile: {property_data.get('name')}
    Indirizzo: {property_data.get('address')}
    Checkout: {checkout_date}
    Ospiti: {booking.get('guests', 1)}
    
    Note specifiche: {property_data.get('cleaning_notes', 'Nessuna nota specifica')}
    """
    
    # Invia il messaggio
    return send_message(
        cleaning_service.get("phone"), 
        message, 
        message_type="cleaning_notification",
        property_data=property_data,
        via_sms=cleaning_service.get("sms_enabled", False)
    )

def get_message_logs(property_id=None, message_type=None, limit=50):
    """
    Ottieni i log dei messaggi, opzionalmente filtrati
    
    Args:
        property_id (str, optional): Filtra per immobile
        message_type (str, optional): Filtra per tipo di messaggio
        limit (int): Numero massimo di messaggi da restituire
        
    Returns:
        list: Lista di messaggi filtrati
    """
    if "message_logs" not in st.session_state:
        load_message_logs()
    
    logs = st.session_state.message_logs
    
    # Applica filtri
    if property_id:
        logs = [log for log in logs if log.get("property_id") == property_id]
    
    if message_type:
        logs = [log for log in logs if log.get("type") == message_type]
    
    # Ordina per timestamp (più recenti prima)
    logs = sorted(logs, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Limita il numero di risultati
    return logs[:limit]

def save_message_logs():
    """Salva i log dei messaggi su file"""
    # Crea directory se non esiste
    os.makedirs("data", exist_ok=True)
    
    try:
        with open("data/message_logs.json", "w", encoding="utf-8") as f:
            json.dump(st.session_state.message_logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Errore nel salvataggio dei log dei messaggi: {str(e)}")

def load_message_logs():
    """Carica i log dei messaggi da file"""
    if os.path.exists("data/message_logs.json"):
        try:
            with open("data/message_logs.json", "r", encoding="utf-8") as f:
                st.session_state.message_logs = json.load(f)
        except Exception as e:
            st.error(f"Errore nel caricamento dei log dei messaggi: {str(e)}")
            st.session_state.message_logs = []
    else:
        st.session_state.message_logs = []
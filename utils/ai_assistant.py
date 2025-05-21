import os
import json
import re
import time
from datetime import datetime
import streamlit as st
import random
from openai import OpenAI

# Initialize OpenAI client
def get_openai_client():
    """
    Get OpenAI API client with appropriate error handling
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        if not st.session_state.get("openai_warning_shown"):
            st.warning("OPENAI_API_KEY non configurata. Le funzionalità AI utilizzeranno risposte simulate.")
            st.session_state.openai_warning_shown = True
        return None
    
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"Errore nell'inizializzazione del client OpenAI: {str(e)}")
        return None

def generate_response(prompt, conversation_history=None, system_message=None, json_response=False):
    """
    Generate a response using OpenAI API
    
    Args:
        prompt (str): The user's prompt
        conversation_history (list, optional): List of previous messages
        system_message (str, optional): System message to set context
        json_response (bool, optional): Whether to request a JSON response
        
    Returns:
        str: Generated response text
    """
    client = get_openai_client()
    
    if not client:
        # Simulate a response if API key is not available
        return simulate_response(prompt, json_response)
    
    try:
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append({"role": "system", "content": system_message})
        else:
            messages.append({"role": "system", "content": "Sei un assistente virtuale esperto nella gestione di proprietà e B&B. Fornisci informazioni utili, accurate e cordiali."})
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add the current prompt
        messages.append({"role": "user", "content": prompt})
        
        # Set response format for JSON if requested
        response_format = {"type": "json_object"} if json_response else None
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format=response_format,
            temperature=0.7,
            max_tokens=800
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        st.error(f"Errore nella generazione della risposta AI: {str(e)}")
        return simulate_response(prompt, json_response)

def virtual_co_host(guest_message, property_data=None, conversation_history=None, language="italiano"):
    """
    Simulate a virtual co-host for guest interactions
    
    Args:
        guest_message (str): The guest's message
        property_data (dict, optional): Data about the property being discussed
        conversation_history (list, optional): List of previous messages
        language (str): Language to use for responses
        
    Returns:
        str: Co-host response
    """
    client = get_openai_client()
    
    if not client:
        # Simulate a response if API key is not available
        return simulate_virtual_co_host(guest_message, property_data, language)
    
    try:
        # Prepare system message with property context
        property_context = ""
        if property_data:
            property_context += f"Informazioni sull'immobile:\n"
            property_context += f"Nome: {property_data.get('name', 'N/A')}\n"
            property_context += f"Tipo: {property_data.get('type', 'N/A')}\n"
            property_context += f"Indirizzo: {property_data.get('address', 'N/A')}, {property_data.get('city', 'N/A')}\n"
            property_context += f"Camere: {property_data.get('bedrooms', 'N/A')}, Bagni: {property_data.get('bathrooms', 'N/A')}\n"
            property_context += f"Ospiti max: {property_data.get('max_guests', 'N/A')}\n"
            
            if property_data.get('check_in_instructions'):
                property_context += f"Istruzioni check-in: {property_data.get('check_in_instructions')}\n"
            
            if property_data.get('wifi_details'):
                property_context += f"WiFi: {property_data.get('wifi_details')}\n"
            
            if property_data.get('amenities'):
                if isinstance(property_data.get('amenities'), list):
                    property_context += f"Servizi: {', '.join(property_data.get('amenities'))}\n"
                elif isinstance(property_data.get('amenities'), str):
                    # If amenities is a JSON string, try to parse it
                    try:
                        amenities = json.loads(property_data.get('amenities'))
                        if isinstance(amenities, list):
                            property_context += f"Servizi: {', '.join(amenities)}\n"
                    except:
                        property_context += f"Servizi: {property_data.get('amenities')}\n"
        
        # Determine language for system message
        language_instructions = ""
        if language and language.lower() != "italiano":
            language_map = {
                "english": "Respond in English.",
                "français": "Réponds en français.",
                "español": "Responde en español.",
                "deutsch": "Antworte auf Deutsch."
            }
            language_instructions = language_map.get(language.lower(), f"Respond in {language}.")
        
        system_message = f"""
        Sei un co-host virtuale professionale e cordiale per un B&B o appartamento vacanze.
        Il tuo compito è assistere gli ospiti rispondendo alle loro domande e fornendo informazioni.
        
        {property_context}
        
        Linee guida:
        - Sii sempre cordiale, professionale e ospitale.
        - Fornisci risposte concise ma complete.
        - Se non conosci un'informazione specifica, indirizza l'ospite a contattare l'host.
        - Per questioni urgenti, suggerisci di chiamare il numero di emergenza o l'host.
        - Non inventare informazioni non presenti nel contesto fornito.
        
        {language_instructions}
        """
        
        messages = [{"role": "system", "content": system_message}]
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add the current message
        messages.append({"role": "user", "content": guest_message})
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        st.error(f"Errore nella generazione della risposta del co-host virtuale: {str(e)}")
        return simulate_virtual_co_host(guest_message, property_data, language)

def analyze_guest_messages(message, conversation_history=None):
    """
    Analyze guest messages to detect intent, sentiment, and needed actions
    
    Args:
        message (str): Guest message
        conversation_history (list, optional): Previous conversation
        
    Returns:
        dict: Analysis results
    """
    client = get_openai_client()
    
    if not client:
        # Simulate analysis if API key is not available
        return {
            "intent": random.choice(["question", "request", "complaint", "compliment", "booking_inquiry"]),
            "sentiment": random.choice(["positive", "neutral", "negative"]),
            "sentiment_score": round(random.uniform(0, 1), 2),
            "priority": random.choice(["low", "medium", "high"]),
            "requires_action": random.choice([True, False]),
            "categories": random.sample(["check-in", "check-out", "amenities", "local_info", "maintenance", "payment"], k=random.randint(1, 3)),
            "summary": "Richiesta simulata dell'ospite senza analisi AI effettiva."
        }
    
    try:
        system_message = """
        Analizza il messaggio dell'ospite e fornisci un'analisi strutturata.
        Identifica intento, sentimento, priorità e azioni necessarie.
        Rispondi esclusivamente in formato JSON con i seguenti campi:
        - intent: l'intento principale del messaggio (question, request, complaint, compliment, booking_inquiry)
        - sentiment: il sentimento generale (positive, neutral, negative)
        - sentiment_score: un punteggio da 0 a 1 dove 0 è estremamente negativo e 1 è estremamente positivo
        - priority: priorità del messaggio (low, medium, high)
        - requires_action: boolean che indica se è necessaria un'azione da parte dell'host
        - categories: array di categorie rilevanti (check-in, check-out, amenities, local_info, maintenance, payment, etc.)
        - summary: breve riassunto del messaggio
        """
        
        messages = [{"role": "system", "content": system_message}]
        
        # Add conversation history for context
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add the current message
        messages.append({"role": "user", "content": message})
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        # Parse the JSON response
        try:
            analysis = json.loads(response.choices[0].message.content)
            return analysis
        except json.JSONDecodeError:
            st.error("Errore nella decodifica della risposta JSON")
            return {"error": "Formato JSON non valido", "raw_response": response.choices[0].message.content}
    
    except Exception as e:
        st.error(f"Errore nell'analisi del messaggio: {str(e)}")
        return {"error": str(e)}

def dynamic_pricing_recommendation(property_data, market_data=None):
    """
    Generate dynamic pricing recommendations based on market data and property characteristics
    
    Args:
        property_data (dict): Property information
        market_data (dict, optional): Market trends and comparable listings
        
    Returns:
        dict: Pricing recommendations
    """
    client = get_openai_client()
    
    if not client:
        # Simulate recommendations if API key is not available
        base_price = float(property_data.get('base_price', 100))
        return {
            "base_price": base_price,
            "weekday_prices": {
                "monday": round(base_price * random.uniform(0.9, 1.1), 2),
                "tuesday": round(base_price * random.uniform(0.85, 1.0), 2),
                "wednesday": round(base_price * random.uniform(0.85, 1.0), 2),
                "thursday": round(base_price * random.uniform(0.9, 1.1), 2),
                "friday": round(base_price * random.uniform(1.1, 1.3), 2),
                "saturday": round(base_price * random.uniform(1.2, 1.4), 2),
                "sunday": round(base_price * random.uniform(1.0, 1.2), 2)
            },
            "seasonal_adjustments": {
                "high_season": round(base_price * random.uniform(1.3, 1.5), 2),
                "mid_season": round(base_price * random.uniform(1.1, 1.3), 2),
                "low_season": round(base_price * random.uniform(0.8, 0.9), 2)
            },
            "min_price": round(base_price * 0.7, 2),
            "max_price": round(base_price * 1.8, 2),
            "occupancy_adjustments": {
                "low_occupancy": "-15%",
                "high_occupancy": "+10%"
            },
            "last_minute_discount": "-10%",
            "long_stay_discount": "-15% per soggiorni di 7+ notti",
            "explanation": "Raccomandazioni di prezzo simulate poiché l'API OpenAI non è disponibile."
        }
    
    try:
        # Prepare property information context
        property_context = f"""
        Immobile: {property_data.get('name')}
        Tipo: {property_data.get('type', 'Appartamento')}
        Città: {property_data.get('city')}
        Camere da letto: {property_data.get('bedrooms')}
        Bagni: {property_data.get('bathrooms')}
        Ospiti max: {property_data.get('max_guests')}
        Prezzo base attuale: €{property_data.get('base_price')}
        """
        
        # Add market data if available
        market_context = ""
        if market_data:
            market_context = f"""
            Dati di mercato:
            Prezzo medio area: €{market_data.get('average_price', 'N/A')}
            Occupazione media: {market_data.get('average_occupancy', 'N/A')}%
            Eventi locali: {', '.join(market_data.get('local_events', ['Nessuno']))}
            Periodo: {market_data.get('season', 'Regolare')}
            """
        
        # Aggiungiamo il contesto sul confronto con altri co-host nella zona
        competitor_context = """
        Il sistema di dynamic pricing deve considerare non solo i prezzi interni 
        del co-host ma anche confrontarsi con tutti i co-host di immobili nella zona
        dove il B&B è presente. 
        
        Questo confronto deve valutare:
        - Prezzi medi di zona per immobili simili
        - Strategie di prezzo di altri co-host (premium, economy, standard)
        - Analisi di stagionalità applicata da altri operatori
        - Variazioni di prezzo per weekend e giorni speciali
        - Occupazione media di zona come fattore di domanda
        
        La raccomandazione finale deve posizionare strategicamente l'immobile
        rispetto alla concorrenza locale per massimizzare l'occupazione
        e la redditività.
        """
        
        prompt = f"""
        Analizza queste informazioni su un immobile e fornisci raccomandazioni di prezzo ottimali:
        
        {property_context}
        
        {market_context}
        
        {competitor_context}
        
        Genera raccomandazioni di prezzo dinamico includendo:
        1. Prezzi raccomandati per giorno della settimana
        2. Aggiustamenti stagionali
        3. Prezzi minimi e massimi consigliati
        4. Aggiustamenti per bassa/alta occupazione
        5. Strategie di sconto last minute
        6. Sconti per soggiorni lunghi
        7. Spiegazione chiara delle raccomandazioni basate sul confronto con altri co-host
        
        Rispondi in formato JSON con tutti questi elementi.
        """
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Sei un esperto di revenue management e dynamic pricing per strutture ricettive."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.5
        )
        
        # Parse JSON response
        try:
            recommendations = json.loads(response.choices[0].message.content)
            return recommendations
        except json.JSONDecodeError:
            st.error("Errore nella decodifica della risposta JSON per le raccomandazioni di prezzo")
            return {"error": "Formato JSON non valido", "raw_response": response.choices[0].message.content}
    
    except Exception as e:
        st.error(f"Errore nella generazione delle raccomandazioni di prezzo: {str(e)}")
        return {"error": str(e)}

def generate_property_description(property_data):
    """
    Generate an appealing property description for listings
    
    Args:
        property_data (dict): Property information
        
    Returns:
        str: Generated property description
    """
    client = get_openai_client()
    
    if not client:
        # Simulate a description if API key is not available
        property_type = property_data.get('type', 'appartamento')
        bedrooms = property_data.get('bedrooms', 1)
        bathrooms = property_data.get('bathrooms', 1)
        city = property_data.get('city', 'città')
        
        templates = [
            f"Splendido {property_type} nel cuore di {city}, con {bedrooms} camere da letto e {bathrooms} bagni. L'immobile è arredato con gusto e offre tutti i comfort per un soggiorno indimenticabile.",
            f"Benvenuti in questo incantevole {property_type} situato in una zona privilegiata di {city}. Con {bedrooms} camere da letto e {bathrooms} bagni, è l'alloggio ideale per chi cerca comfort e stile.",
            f"Questo elegante {property_type} a {city} vi conquisterà con i suoi spazi luminosi, le {bedrooms} camere confortevoli e i {bathrooms} bagni moderni. La posizione è perfetta per esplorare le attrazioni della città."
        ]
        
        return random.choice(templates)
    
    try:
        # Prepare property context
        property_context = ""
        for key, value in property_data.items():
            if key not in ['id', 'created_at', 'updated_at']:
                property_context += f"{key}: {value}\n"
        
        prompt = f"""
        Crea una descrizione accattivante per un annuncio di questo immobile in italiano:
        
        {property_context}
        
        La descrizione dovrebbe:
        1. Essere convincente e attraente
        2. Evidenziare le caratteristiche principali dell'immobile
        3. Menzionare la posizione e i vantaggi della zona
        4. Avere un tono professionale ma invitante
        5. Essere di circa 150-200 parole
        """
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Sei un copywriter esperto nella creazione di descrizioni immobiliari accattivanti."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        st.error(f"Errore nella generazione della descrizione dell'immobile: {str(e)}")
        return simulate_response(f"Descrivi questo immobile: {property_data.get('name', 'Immobile')} in {property_data.get('city', 'città')}", False)

def generate_automated_messages(message_type, booking_data, guest_name=None, property_data=None, language="italiano"):
    """
    Generate automated messages for different guest communication scenarios
    
    Args:
        message_type (str): Type of message (welcome, check_in, check_out, etc.)
        booking_data (dict): Booking information
        guest_name (str, optional): Guest name
        property_data (dict, optional): Property information
        language (str): Language to use
        
    Returns:
        str: Generated message
    """
    client = get_openai_client()
    
    # If guest name is not provided, try to get it from booking data
    if not guest_name and booking_data:
        guest_name = booking_data.get('guest_name', 'Ospite')
    
    # If property data is not provided but booking data has property_id
    if not property_data and booking_data and booking_data.get('property_id'):
        # In a real app, we would fetch property data here
        property_data = {"name": "Appartamento", "address": "Via Example 123", "city": "Milano"}
    
    if not client:
        # Simulate automated messages if API key is not available
        templates = {
            "welcome": {
                "italiano": f"Gentile {guest_name}, grazie per aver scelto il nostro alloggio! Siamo lieti di darti il benvenuto e non vediamo l'ora di ospitarti.",
                "english": f"Dear {guest_name}, thank you for choosing our accommodation! We are pleased to welcome you and look forward to hosting you."
            },
            "check_in": {
                "italiano": f"Gentile {guest_name}, oggi è il giorno del tuo check-in! Puoi arrivare dalle 15:00 in poi. Ti aspettiamo all'indirizzo indicato.",
                "english": f"Dear {guest_name}, today is your check-in day! You can arrive from 3:00 PM onwards. We'll be waiting for you at the indicated address."
            },
            "check_out": {
                "italiano": f"Gentile {guest_name}, domani è previsto il check-out entro le 10:00. Ti ringraziamo per aver scelto il nostro alloggio!",
                "english": f"Dear {guest_name}, tomorrow is your check-out day by 10:00 AM. Thank you for choosing our accommodation!"
            },
            "reminder": {
                "italiano": f"Gentile {guest_name}, questo è un promemoria per la tua prenotazione. Se hai domande, non esitare a contattarci.",
                "english": f"Dear {guest_name}, this is a reminder about your booking. If you have any questions, feel free to contact us."
            }
        }
        
        lang = language.lower()
        if lang not in ["italiano", "english"]:
            lang = "italiano"  # Default to Italian
        
        if message_type in templates:
            return templates[message_type][lang]
        else:
            return templates["welcome"][lang]
    
    try:
        # Prepare context
        booking_context = ""
        if booking_data:
            for key, value in booking_data.items():
                if key not in ['id', 'created_at', 'updated_at', 'property_id']:
                    booking_context += f"{key}: {value}\n"
        
        property_context = ""
        if property_data:
            for key, value in property_data.items():
                if key not in ['id', 'created_at', 'updated_at']:
                    property_context += f"{key}: {value}\n"
        
        # Determine language for system message
        lang_system_message = ""
        language_lower = language.lower()
        if language_lower != "italiano":
            language_map = {
                "english": "Generate the message in English.",
                "français": "Génère le message en français.",
                "español": "Genera el mensaje en español.",
                "deutsch": "Erstelle die Nachricht auf Deutsch."
            }
            lang_system_message = language_map.get(language_lower, f"Generate the message in {language}.")
        
        # Prepare system message based on message type
        message_type_instructions = {
            "welcome": "Crea un messaggio di benvenuto per un ospite che ha appena prenotato.",
            "check_in": "Crea un messaggio per il giorno del check-in con istruzioni utili.",
            "check_out": "Crea un messaggio di reminder per il check-out di domani.",
            "reminder": "Crea un messaggio di promemoria per la prenotazione imminente.",
            "thank_you": "Crea un messaggio di ringraziamento dopo il check-out."
        }
        
        system_message = f"""
        Sei un host professionale di immobili in affitto a breve termine.
        Genera un messaggio automatico per la comunicazione con gli ospiti.
        
        {message_type_instructions.get(message_type, "Crea un messaggio informativo per l'ospite.")}
        Il messaggio deve essere cordiale, informativo e professionale.
        
        {lang_system_message}
        """
        
        prompt = f"""
        Genera un messaggio per il cliente con queste informazioni:
        
        Tipo di messaggio: {message_type}
        Nome ospite: {guest_name}
        
        Dati prenotazione:
        {booking_context}
        
        Dati immobile:
        {property_context}
        """
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        st.error(f"Errore nella generazione del messaggio automatico: {str(e)}")
        
        # Fallback to templates
        templates = {
            "welcome": f"Gentile {guest_name}, grazie per aver scelto il nostro alloggio!",
            "check_in": f"Gentile {guest_name}, oggi è il giorno del tuo check-in! Puoi arrivare dalle 15:00 in poi.",
            "check_out": f"Gentile {guest_name}, domani è previsto il check-out entro le 10:00. Grazie!",
            "reminder": f"Gentile {guest_name}, questo è un promemoria per la tua prenotazione."
        }
        
        return templates.get(message_type, f"Gentile {guest_name}, grazie per la tua prenotazione.")

def translate_message(message, target_language):
    """
    Translate a message to the target language
    
    Args:
        message (str): Message to translate
        target_language (str): Target language
        
    Returns:
        str: Translated message
    """
    client = get_openai_client()
    
    if not client:
        # Simulate translation if API key is not available
        prefix_map = {
            "english": "[EN] ",
            "français": "[FR] ",
            "español": "[ES] ",
            "deutsch": "[DE] ",
            "italiano": "[IT] "
        }
        prefix = prefix_map.get(target_language.lower(), "[??] ")
        return prefix + message
    
    try:
        prompt = f"""
        Traduci questo messaggio in {target_language}:
        
        {message}
        
        Fornisci solo il testo tradotto, senza note o spiegazioni.
        """
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"Sei un traduttore professionale. Traduci il messaggio in {target_language} mantenendo lo stesso tono e stile."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        st.error(f"Errore nella traduzione del messaggio: {str(e)}")
        return message  # Return original message if translation fails

# Helper functions for simulation mode
def simulate_response(prompt, json_format=False):
    """Simulate an AI response for when OpenAI API is not available"""
    # Simple response templates
    templates = [
        "Ecco le informazioni richieste. Questo è un testo simulato poiché l'API OpenAI non è disponibile al momento.",
        "Grazie per la tua richiesta. Questa è una risposta simulata in assenza dell'API OpenAI.",
        "Ho elaborato la tua domanda. Questa risposta è generata localmente senza utilizzare l'API OpenAI.",
        "Ecco la risposta alla tua domanda. Nota che si tratta di contenuto simulato senza l'utilizzo dell'API OpenAI."
    ]
    
    if json_format:
        return json.dumps({
            "response": random.choice(templates),
            "query": prompt,
            "timestamp": datetime.now().isoformat(),
            "simulated": True
        })
    else:
        return random.choice(templates)

def simulate_virtual_co_host(guest_message, property_data=None, language="italiano"):
    """Simulate a virtual co-host response when OpenAI API is not available"""
    property_name = property_data.get('name', 'nostro alloggio') if property_data else 'nostro alloggio'
    
    # Define response templates based on message content
    greeting_templates = [
        f"Buongiorno! Sono il co-host virtuale di {property_name}. Come posso aiutarti?",
        f"Salve! Sono qui per assisterti durante il tuo soggiorno presso {property_name}. In cosa posso esserti utile?",
        f"Ciao! Sono il tuo assistente virtuale per {property_name}. Sono qui per rispondere alle tue domande."
    ]
    
    checkin_templates = [
        f"Per il check-in, puoi arrivare dalle 15:00 alle 20:00. Se hai bisogno di un orario diverso, faccelo sapere in anticipo.",
        f"Il check-in è previsto dalle 15:00. Ti aspetteremo all'indirizzo dell'immobile. Puoi confermarci l'orario di arrivo?",
        f"Per il check-in, ti accoglieremo dalle 15:00. Se il tuo arrivo è previsto dopo le 20:00, ti preghiamo di avvisarci."
    ]
    
    checkout_templates = [
        f"Il check-out è previsto entro le 10:00. Puoi lasciare le chiavi all'interno dell'appartamento e chiudere la porta.",
        f"Per il check-out, ti chiediamo gentilmente di liberare l'appartamento entro le 10:00 e di lasciare le chiavi sul tavolo.",
        f"Il giorno della partenza, il check-out deve essere effettuato entro le 10:00. Grazie per la collaborazione!"
    ]
    
    wifi_templates = [
        f"La password WiFi è disponibile nel manuale dell'ospite all'interno dell'appartamento, di solito sul tavolo della cucina.",
        f"Troverai le informazioni WiFi nel foglio di benvenuto all'interno dell'appartamento.",
        f"La rete WiFi è 'GuestNetwork' e la password è 'WelcomeGuest2025'. In caso di problemi di connessione, faccelo sapere."
    ]
    
    local_info_templates = [
        f"Ci sono molti ristoranti e attrazioni nelle vicinanze. Cosa ti interessa in particolare?",
        f"La zona offre diverse opzioni per mangiare e fare shopping. Posso darti raccomandazioni specifiche se mi dici cosa cerchi.",
        f"Nelle vicinanze troverai supermercati, ristoranti e mezzi pubblici. C'è qualcosa di specifico che vorresti sapere?"
    ]
    
    # English templates for language support
    english_templates = [
        f"Hello! I'm the virtual co-host for {property_name}. How can I help you today?",
        f"For check-in, you can arrive between 3:00 PM and 8:00 PM. Let us know if you need a different time.",
        f"Check-out is by 10:00 AM. You can leave the keys inside the apartment and close the door behind you.",
        f"You'll find the WiFi information in the welcome sheet inside the apartment.",
        f"There are many restaurants and attractions nearby. What are you interested in particularly?"
    ]
    
    # Detect message intent based on keywords
    message_lower = guest_message.lower()
    
    if language.lower() == "english":
        return random.choice(english_templates)
    
    if "check-in" in message_lower or "arrivo" in message_lower or "arrivare" in message_lower or "chiavi" in message_lower:
        return random.choice(checkin_templates)
    elif "check-out" in message_lower or "checkout" in message_lower or "partenza" in message_lower or "partire" in message_lower:
        return random.choice(checkout_templates)
    elif "wifi" in message_lower or "internet" in message_lower or "password" in message_lower:
        return random.choice(wifi_templates)
    elif "ristorante" in message_lower or "mangiare" in message_lower or "supermercato" in message_lower or "negozi" in message_lower:
        return random.choice(local_info_templates)
    else:
        return random.choice(greeting_templates)
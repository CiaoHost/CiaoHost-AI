import streamlit as st
import pandas as pd
import os
import json
import uuid
from datetime import datetime
from utils.json_database import (
    get_all_properties, get_property, add_property, update_property, delete_property
)

def show_property_management():
    st.header("🏡 Gestione Proprietà")
    
    # Create tabs for different property management functions
    tabs = st.tabs(["Elenco Proprietà", "Aggiungi Proprietà", "Statistiche"])
    
    with tabs[0]:
        show_property_list()
    
    with tabs[1]:
        show_add_property_form()
    
    with tabs[2]:
        show_property_statistics()

def show_property_list():
    """Display a list of all properties with options to view, edit, and delete"""
    st.subheader("Elenco Proprietà")
    
    # Get all properties
    properties = get_all_properties()
    
    if not properties:
        st.info("Non ci sono proprietà registrate. Vai alla scheda 'Aggiungi Proprietà' per aggiungerne una.")
        return
    
    # Create a dataframe for display
    property_data = [{
        "id": prop.get("id"),
        "Nome": prop.get("name"),
        "Tipo": prop.get("type", ""),
        "Indirizzo": prop.get("address", ""),
        "Città": prop.get("city", ""),
        "Camere": prop.get("bedrooms", 0),
        "Bagni": prop.get("bathrooms", 0),
        "Ospiti Max": prop.get("max_guests", 0),
        "Prezzo Base": f"€{prop.get('base_price', 0)}"
    } for prop in properties]
    
    # Display properties in a dataframe
    property_df = pd.DataFrame(property_data)
    displayed_cols = [col for col in property_df.columns if col != "id"]
    st.dataframe(property_df[displayed_cols], use_container_width=True)
    
    # Property details section
    st.subheader("Dettagli Proprietà")
    
    # Select a property to view/edit
    selected_property_id = st.selectbox(
        "Seleziona una proprietà",
        options=[prop["id"] for prop in properties],
        format_func=lambda x: next((f"{prop['Nome']} - {prop['Indirizzo']}, {prop['Città']}" 
                                  for prop in property_data if prop["id"] == x), x)
    )
    
    if selected_property_id:
        selected_property = get_property(selected_property_id)
        
        if selected_property:
            # Create tabs for viewing and editing
            detail_tabs = st.tabs(["Visualizza", "Modifica", "Elimina"])
            
            with detail_tabs[0]:
                show_property_details(selected_property)
            
            with detail_tabs[1]:
                edit_property(selected_property)
            
            with detail_tabs[2]:
                delete_property_ui(selected_property)

def show_property_details(property_data):
    """Display detailed information about a property"""
    st.markdown(f"### {property_data.get('name')}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Tipo:** {property_data.get('type', 'Non specificato')}")
        st.markdown(f"**Indirizzo:** {property_data.get('address', 'Non specificato')}")
        st.markdown(f"**Città:** {property_data.get('city', 'Non specificata')}")
        st.markdown(f"**Camere:** {property_data.get('bedrooms', 0)}")
        st.markdown(f"**Bagni:** {property_data.get('bathrooms', 0)}")
    
    with col2:
        st.markdown(f"**Ospiti Max:** {property_data.get('max_guests', 0)}")
        st.markdown(f"**Prezzo Base:** €{property_data.get('base_price', 0)}")
        st.markdown(f"**Tariffa Pulizie:** €{property_data.get('cleaning_fee', 0)}")
    
    
    # Amenities
    if property_data.get('amenities'):
        st.markdown("### Servizi")
        
        amenities = property_data.get('amenities')
        if isinstance(amenities, str):
            try:
                amenities = json.loads(amenities)
            except:
                amenities = [amenities]
        
        if isinstance(amenities, list):
            for amenity in amenities:
                st.markdown(f"- {amenity}")
    
    
    # Check-in instructions
    if property_data.get('check_in_instructions'):
        st.markdown("### Istruzioni per il Check-in")
        st.markdown(property_data.get('check_in_instructions'))
    
    # WiFi details
    if property_data.get('wifi_details'):
        st.markdown("### Dettagli WiFi")
        st.markdown(property_data.get('wifi_details'))

def edit_property(property_data):
    """Form to edit an existing property"""
    with st.form("edit_property_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nome*", value=property_data.get('name', ''))
            property_type = st.selectbox(
                "Tipo*",
                options=["Appartamento", "Casa", "Villa", "B&B", "Altro"],
                index=["Appartamento", "Casa", "Villa", "B&B", "Altro"].index(property_data.get('type', 'Appartamento')) if property_data.get('type') in ["Appartamento", "Casa", "Villa", "B&B", "Altro"] else 0
            )
            address = st.text_input("Indirizzo*", value=property_data.get('address', ''))
            city = st.text_input("Città*", value=property_data.get('city', ''))
            bedrooms = st.number_input("Camere da letto*", min_value=0, value=property_data.get('bedrooms', 1))
        
        with col2:
            bathrooms = st.number_input("Bagni*", min_value=0.0, value=float(property_data.get('bathrooms', 1.0)), step=0.5)
            max_guests = st.number_input("Ospiti Max*", min_value=1, value=property_data.get('max_guests', 2))
            base_price = st.number_input("Prezzo Base (€)*", min_value=0.0, value=float(property_data.get('base_price', 50.0)), step=1.0)
            cleaning_fee = st.number_input("Tariffa Pulizie (€)", min_value=0.0, value=float(property_data.get('cleaning_fee', 30.0)), step=1.0)
        
        
        # Amenities
        amenities_str = ""
        if property_data.get('amenities'):
            amenities = property_data.get('amenities')
            if isinstance(amenities, list):
                amenities_str = ", ".join(amenities)
            elif isinstance(amenities, str):
                try:
                    amenities_list = json.loads(amenities)
                    if isinstance(amenities_list, list):
                        amenities_str = ", ".join(amenities_list)
                    else:
                        amenities_str = amenities
                except:
                    amenities_str = amenities
        
        amenities_input = st.text_area(
            "Servizi (separati da virgola)",
            value=amenities_str,
            help="Inserisci i servizi separati da virgola, es: WiFi, TV, Aria condizionata"
        )
        
        # Additional information
        col1, col2 = st.columns(2)
        
        with col1:
            check_in_instructions = st.text_area("Istruzioni Check-in", value=property_data.get('check_in_instructions', ''))
        
        with col2:
            wifi_details = st.text_area("Dettagli WiFi", value=property_data.get('wifi_details', ''))
        
        submit_button = st.form_submit_button("Aggiorna Proprietà")
    
    if submit_button:
        # Validate required fields
        if not name or not address or not city:
            st.error("I campi contrassegnati con * sono obbligatori.")
            return
        
        # Process amenities
        amenities_list = [item.strip() for item in amenities_input.split(",") if item.strip()]
        
        # Create updated property data
        updated_property = {
            **property_data,  # Keep existing data
            "name": name,
            "type": property_type,
            "address": address,
            "city": city,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "max_guests": max_guests,
            "base_price": base_price,
            "cleaning_fee": cleaning_fee,
            "amenities": amenities_list,
            "check_in_instructions": check_in_instructions,
            "wifi_details": wifi_details,
            "updated_at": datetime.now()
        }
        
        # Update property in database
        success = update_property(property_data["id"], updated_property)
        
        if success:
            st.success(f"Proprietà '{name}' aggiornata con successo!")
            st.rerun()
        else:
            st.error("Si è verificato un errore durante l'aggiornamento della proprietà.")

def delete_property_ui(property_data):
    """UI for deleting a property with confirmation"""
    st.warning(f"Stai per eliminare la proprietà '{property_data.get('name')}'. Questa azione non può essere annullata.")
    
    # Require typing the property name as confirmation
    confirmation = st.text_input("Per confermare, digita il nome della proprietà:")
    
    if st.button("Elimina Proprietà"):
        if confirmation == property_data.get('name'):
            # Delete property from database
            success = delete_property(property_data["id"])
            
            if success:
                st.success(f"Proprietà '{property_data.get('name')}' eliminata con successo!")
                st.rerun()
            else:
                st.error("Si è verificato un errore durante l'eliminazione della proprietà.")
        else:
            st.error("Il nome inserito non corrisponde. Eliminazione annullata.")

def show_add_property_form():
    """Form to add a new property"""
    st.subheader("Aggiungi Nuova Proprietà")
    
    with st.form("add_property_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nome*")
            property_type = st.selectbox(
                "Tipo*",
                options=["Appartamento", "Casa", "Villa", "B&B", "Altro"]
            )
            address = st.text_input("Indirizzo*")
            city = st.text_input("Città*")
            bedrooms = st.number_input("Camere da letto*", min_value=0, value=1)
        
        with col2:
            bathrooms = st.number_input("Bagni*", min_value=0.0, value=1.0, step=0.5)
            max_guests = st.number_input("Ospiti Max*", min_value=1, value=2)
            base_price = st.number_input("Prezzo Base (€)*", min_value=0.0, value=50.0, step=1.0)
            cleaning_fee = st.number_input("Tariffa Pulizie (€)", min_value=0.0, value=30.0, step=1.0)
        
        
        # Amenities
        amenities_input = st.text_area(
            "Servizi (separati da virgola)",
            help="Inserisci i servizi separati da virgola, es: WiFi, TV, Aria condizionata"
        )
        
        # Additional information
        col1, col2 = st.columns(2)
        
        with col1:
            check_in_instructions = st.text_area("Istruzioni Check-in")
        
        with col2:
            wifi_details = st.text_area("Dettagli WiFi")
        
        submit_button = st.form_submit_button("Aggiungi Proprietà")
    
    if submit_button:
        # Validate required fields
        if not name or not address or not city:
            st.error("I campi contrassegnati con * sono obbligatori.")
            return
        
        # Process amenities
        amenities_list = [item.strip() for item in amenities_input.split(",") if item.strip()]
        
        # Create new property data
        new_property = {
            "id": str(uuid.uuid4()),
            "name": name,
            "type": property_type,
            "address": address,
            "city": city,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "max_guests": max_guests,
            "base_price": base_price,
            "cleaning_fee": cleaning_fee,
            "amenities": amenities_list,
            "check_in_instructions": check_in_instructions,
            "wifi_details": wifi_details,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Add property to database
        success = add_property(new_property)
        
        if success:
            st.success(f"Proprietà '{name}' aggiunta con successo!")
            st.rerun()
        else:
            st.error("Si è verificato un errore durante l'aggiunta della proprietà.")

def show_property_statistics():
    """Display statistics about properties"""
    st.subheader("Statistiche Proprietà")
    
    # Get all properties
    properties = get_all_properties()
    
    if not properties:
        st.info("Non ci sono proprietà registrate. Aggiungi proprietà per visualizzare le statistiche.")
        return
    
    # Calculate statistics
    total_properties = len(properties)
    total_bedrooms = sum(prop.get("bedrooms", 0) for prop in properties)
    total_bathrooms = sum(prop.get("bathrooms", 0) for prop in properties)
    total_capacity = sum(prop.get("max_guests", 0) for prop in properties)
    avg_price = sum(prop.get("base_price", 0) for prop in properties) / total_properties if total_properties > 0 else 0
    
    # Property types
    property_types = {}
    for prop in properties:
        prop_type = prop.get("type", "Non specificato")
        property_types[prop_type] = property_types.get(prop_type, 0) + 1
    
    # Cities
    cities = {}
    for prop in properties:
        city = prop.get("city", "Non specificata")
        cities[city] = cities.get(city, 0) + 1
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Totale Proprietà", total_properties)
        st.metric("Capacità Totale", f"{total_capacity} ospiti")
    
    with col2:
        st.metric("Camere Totali", total_bedrooms)
        st.metric("Bagni Totali", total_bathrooms)
    
    with col3:
        st.metric("Prezzo Medio", f"€{avg_price:.2f}")
    
    # Display property types chart
    if property_types:
        st.subheader("Tipi di Proprietà")
        property_types_df = pd.DataFrame({
            "Tipo": list(property_types.keys()),
            "Numero": list(property_types.values())
        })
        st.bar_chart(property_types_df.set_index("Tipo"))
    
    # Display cities chart
    if cities:
        st.subheader("Proprietà per Città")
        cities_df = pd.DataFrame({
            "Città": list(cities.keys()),
            "Numero": list(cities.values())
        })
        st.bar_chart(cities_df.set_index("Città"))
    
    # Property list by price
    st.subheader("Proprietà per Prezzo")
    price_data = [{
        "Nome": prop.get("name"),
        "Tipo": prop.get("type", ""),
        "Città": prop.get("city", ""),
        "Prezzo Base": prop.get("base_price", 0)
    } for prop in properties]
    
    price_df = pd.DataFrame(price_data)
    price_df = price_df.sort_values("Prezzo Base", ascending=False)
    st.dataframe(price_df, use_container_width=True)
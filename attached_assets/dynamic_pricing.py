import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
import random
import json
import os
from utils.database import get_all_properties, get_property, update_property
from utils.ai_assistant import dynamic_pricing_recommendation

def load_pricing_data():
    return pd.DataFrame({
        'Data': pd.date_range(start='2024-01-01', end='2024-12-31'),
        'Prezzo': [100] * 365
    })

def generate_sample_pricing():
    return pd.DataFrame({
        'Data': pd.date_range(start='2024-01-01', end='2024-12-31'),
        'Prezzo': [100] * 365
    })

def get_date_range():
    return datetime.now(), datetime.now()

def save_pricing_data(data):
    pass  # Implementazione salvatagio dati

def create_calendar_df():
    return pd.DataFrame()

def trend_with_events():
    return pd.DataFrame()

def create_default_seasons():
    return []

def get_date_season(date):
    return "Alta stagione"

def save_pricing_seasons(seasons):
    pass  # Implementazione salvatagio stagioni

def show_dynamic_pricing():
    st.title("💰 Dynamic Pricing")
    st.write("Gestisci i prezzi del tuo immobile in modo dinamico")

    # Placeholder per il contenuto
    st.info("Funzionalità in sviluppo")

def show_pricing_overview():
    st.subheader("Panoramica Prezzi")
    
    # Get properties
    properties = st.session_state.properties
    
    if not properties:
        st.info("Non hai ancora registrato immobili. Vai alla sezione 'Gestione Immobili' per aggiungere un immobile.")
        return
    
    # Create property selector
    property_options = {p["id"]: p["name"] for p in properties}
    selected_property_id = st.selectbox(
        "Seleziona Immobile",
        options=list(property_options.keys()),
        format_func=lambda x: property_options.get(x, "")
    )
    
    if selected_property_id:
        property_data = next((p for p in properties if p["id"] == selected_property_id), None)
        
        if property_data:
            # Property info
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Prezzo Base", f"€{property_data.get('base_price', 0):.2f}")
            
            with col2:
                st.metric("Prezzo Attuale", f"€{property_data.get('current_price', property_data.get('base_price', 0)):.2f}")
            
            with col3:
                # Calculate occupancy rate for the current month (simulated)
                occupancy_rate = get_occupancy_rate(selected_property_id)
                st.metric("Tasso Occupazione", f"{occupancy_rate:.1f}%")
            
            # Load or generate pricing data
            pricing_data = load_pricing_data(selected_property_id)
            if not pricing_data:
                pricing_data = generate_sample_pricing(property_data, get_date_range())
                save_pricing_data(selected_property_id, pricing_data)
            
            # Calendar view
            st.subheader("Calendario Prezzi")
            
            # Date range selector
            col1, col2 = st.columns(2)
            
            with col1:
                view_month = st.selectbox(
                    "Mese", 
                    range(1, 13), 
                    format_func=lambda x: calendar.month_name[x],
                    index=datetime.now().month - 1
                )
            
            with col2:
                view_year = st.selectbox(
                    "Anno", 
                    range(datetime.now().year, datetime.now().year + 2),
                    index=0
                )
            
            # Filter pricing data for selected month
            month_data = [p for p in pricing_data 
                          if datetime.fromisoformat(p['date']).month == view_month 
                          and datetime.fromisoformat(p['date']).year == view_year]
            
            # Create calendar dataframe
            calendar_df = create_calendar_df(month_data, view_month, view_year)
            
            # Display calendar
            st.dataframe(
                calendar_df.style.applymap(
                    lambda x: f'background-color: rgba(66, 135, 245, {min(1.0, float(x.split("€")[1]) / property_data.get("base_price", 100) * 0.6) if isinstance(x, str) and x.startswith("€") else 0})',
                    subset=pd.IndexSlice[:, ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']]
                ),
                height=400,
                use_container_width=True
            )
            
            # Price editor
            st.subheader("Modifica Prezzi")
            
            with st.form("edit_prices_form"):
                st.write("Seleziona un intervallo di date e modifica i prezzi:")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    start_date = st.date_input(
                        "Data Inizio",
                        value=datetime.now().date()
                    )
                
                with col2:
                    end_date = st.date_input(
                        "Data Fine",
                        value=(datetime.now() + timedelta(days=7)).date(),
                        min_value=start_date
                    )
                
                price_adjustment = st.number_input(
                    "Nuovo Prezzo (€)",
                    min_value=0.0,
                    value=float(property_data.get('base_price', 50.0)),
                    step=5.0
                )
                
                apply_button = st.form_submit_button("Applica Modifica")
                
                if apply_button:
                    # Update pricing data
                    current_date = start_date
                    while current_date <= end_date:
                        date_str = current_date.isoformat()
                        
                        # Check if date exists in pricing data
                        date_exists = False
                        for i, data in enumerate(pricing_data):
                            if data['date'] == date_str:
                                pricing_data[i]['price'] = price_adjustment
                                date_exists = True
                                break
                        
                        # If date doesn't exist, add it
                        if not date_exists:
                            pricing_data.append({
                                'date': date_str,
                                'price': price_adjustment,
                                'status': 'available'
                            })
                        
                        current_date += timedelta(days=1)
                    
                    # Save updated pricing data
                    save_pricing_data(selected_property_id, pricing_data)
                    
                    # Update current price in property data
                    updated_property = property_data.copy()
                    updated_property['current_price'] = price_adjustment
                    update_property(selected_property_id, {'current_price': price_adjustment})
                    
                    st.success(f"Prezzi aggiornati con successo per il periodo {start_date} - {end_date}")
                    st.rerun()
            
            # Price trend chart
            st.subheader("Trend Prezzi")
            
            # Prepare data for chart
            df_trend = pd.DataFrame([
                {
                    'date': datetime.fromisoformat(p['date']),
                    'price': p['price'],
                    'day_of_week': datetime.fromisoformat(p['date']).strftime('%a')
                }
                for p in pricing_data
                if datetime.fromisoformat(p['date']) >= datetime.now().replace(day=1) and 
                datetime.fromisoformat(p['date']) < (datetime.now().replace(day=1) + timedelta(days=90))
            ])
            
            df_trend = df_trend.sort_values('date')
            
            # Add event markers
            events = [
                {'date': datetime.now() + timedelta(days=30), 'name': 'Festival Locale'},
                {'date': datetime.now() + timedelta(days=45), 'name': 'Concerto'},
                {'date': datetime.now() + timedelta(days=60), 'name': 'Evento Sportivo'}
            ]
            
            # Create interactive chart with Plotly
            fig = trend_with_events(df_trend, events)
            st.plotly_chart(fig, use_container_width=True)

def show_season_management():
    st.subheader("Gestione Stagioni e Tariffe")
    
    # Initialize season data if not exists
    if 'pricing_seasons' not in st.session_state:
        # Check if season data exists
        if os.path.exists('data/pricing_seasons.json'):
            try:
                with open('data/pricing_seasons.json', 'r', encoding='utf-8') as f:
                    st.session_state.pricing_seasons = json.load(f)
            except:
                st.session_state.pricing_seasons = create_default_seasons()
        else:
            st.session_state.pricing_seasons = create_default_seasons()
    
    # Get properties
    properties = st.session_state.properties
    
    if not properties:
        st.info("Non hai ancora registrato immobili.")
        return
    
    # Get the current year
    current_year = datetime.now().year
    
    # Create tabs for season management
    season_tabs = st.tabs(["Calendario Stagioni", "Definizione Stagioni", "Modificatori di Prezzo"])
    
    with season_tabs[0]:
        # Season calendar view
        st.markdown("### Calendario Stagioni")
        st.markdown("Visualizzazione annuale delle stagioni configurate")
        
        # Create year selector
        year = st.selectbox("Anno", range(current_year, current_year + 3))
        
        # Check if we have seasons data
        if 'seasons' in st.session_state.pricing_seasons:
            # Generate calendar with seasons
            months = list(calendar.month_name)[1:]
            seasons_df = pd.DataFrame(index=range(1, 32), columns=months)
            seasons_df = seasons_df.fillna("")
            
            # Season colors
            season_colors = {
                "Alta": "background-color: rgba(255, 87, 87, 0.7);",
                "Media": "background-color: rgba(255, 165, 0, 0.7);",
                "Bassa": "background-color: rgba(46, 204, 113, 0.7);",
                "Custom": "background-color: rgba(93, 173, 226, 0.7);"
            }
            
            # Fill calendar with season data
            for month_idx, month_name in enumerate(months, 1):
                for day in range(1, 32):
                    # Check if valid date
                    try:
                        date = datetime(year, month_idx, day).date()
                        
                        # Check which season this date falls into
                        date_str = date.strftime("%Y-%m-%d")
                        season_name = get_date_season(date_str, st.session_state.pricing_seasons['seasons'])
                        
                        if season_name:
                            seasons_df.loc[day, month_name] = season_name
                    except ValueError:
                        # Invalid date (e.g., February 30)
                        pass
            
            # Display calendar with colors
            st.markdown("Legenda:")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown('<div style="background-color: rgba(255, 87, 87, 0.7); padding: 5px; border-radius: 5px;">Alta Stagione</div>', unsafe_allow_html=True)
            with col2:
                st.markdown('<div style="background-color: rgba(255, 165, 0, 0.7); padding: 5px; border-radius: 5px;">Media Stagione</div>', unsafe_allow_html=True)
            with col3:
                st.markdown('<div style="background-color: rgba(46, 204, 113, 0.7); padding: 5px; border-radius: 5px;">Bassa Stagione</div>', unsafe_allow_html=True)
            with col4:
                st.markdown('<div style="background-color: rgba(93, 173, 226, 0.7); padding: 5px; border-radius: 5px;">Stagione Custom</div>', unsafe_allow_html=True)
            
            # Apply colors
            styled_df = seasons_df.style.applymap(
                lambda x: season_colors.get(x, "")
            )
            
            st.dataframe(styled_df, height=600, use_container_width=True)
        else:
            st.warning("Nessuna definizione di stagione trovata. Definisci le stagioni nella scheda 'Definizione Stagioni'.")
    
    with season_tabs[1]:
        # Season definition
        st.markdown("### Definizione Stagioni")
        st.markdown("Configura le date delle diverse stagioni e i relativi modificatori di prezzo")
        
        # Define or edit seasons
        if 'seasons' in st.session_state.pricing_seasons:
            seasons = st.session_state.pricing_seasons['seasons']
            
            # Add a new season
            st.markdown("#### Aggiungi Nuova Stagione")
            
            with st.form("add_season_form"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    season_name = st.selectbox(
                        "Tipo di Stagione",
                        ["Alta", "Media", "Bassa", "Custom"],
                        index=0
                    )
                
                with col2:
                    start_date = st.date_input(
                        "Data Inizio",
                        value=datetime.now().date()
                    )
                
                with col3:
                    end_date = st.date_input(
                        "Data Fine",
                        value=(datetime.now() + timedelta(days=30)).date(),
                        min_value=start_date
                    )
                
                price_modifier = st.slider(
                    "Modificatore di Prezzo (%)",
                    min_value=-50,
                    max_value=100,
                    value=0,
                    step=5
                )
                
                notes = st.text_input("Note (es. eventi, festività, ecc.)")
                
                submit_button = st.form_submit_button("Aggiungi Stagione")
                
                if submit_button:
                    # Add new season
                    new_season = {
                        "id": str(len(seasons) + 1),
                        "name": season_name,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "price_modifier": price_modifier,
                        "notes": notes
                    }
                    
                    seasons.append(new_season)
                    save_pricing_seasons()
                    
                    st.success(f"Stagione {season_name} aggiunta con successo.")
                    st.rerun()
            
            # Display existing seasons
            st.markdown("#### Stagioni Configurate")
            
            if seasons:
                for i, season in enumerate(seasons):
                    with st.expander(f"{season['name']} ({season['start_date']} - {season['end_date']})"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown(f"**Tipo:** {season['name']}")
                        
                        with col2:
                            st.markdown(f"**Periodo:** {season['start_date']} - {season['end_date']}")
                        
                        with col3:
                            st.markdown(f"**Modificatore:** {season['price_modifier']}%")
                        
                        if season.get('notes'):
                            st.markdown(f"**Note:** {season['notes']}")
                        
                        # Edit and delete buttons
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("Modifica", key=f"edit_season_{i}"):
                                st.session_state.editing_season = i
                                st.rerun()
                        
                        with col2:
                            if st.button("Elimina", key=f"delete_season_{i}"):
                                del seasons[i]
                                save_pricing_seasons()
                                st.success("Stagione eliminata con successo.")
                                st.rerun()
                
                # Edit season form
                if 'editing_season' in st.session_state and st.session_state.editing_season < len(seasons):
                    i = st.session_state.editing_season
                    season = seasons[i]
                    
                    st.markdown("#### Modifica Stagione")
                    
                    with st.form("edit_season_form"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            edit_name = st.selectbox(
                                "Tipo di Stagione",
                                ["Alta", "Media", "Bassa", "Custom"],
                                index=["Alta", "Media", "Bassa", "Custom"].index(season['name']) if season['name'] in ["Alta", "Media", "Bassa", "Custom"] else 0
                            )
                        
                        with col2:
                            edit_start = st.date_input(
                                "Data Inizio",
                                value=datetime.fromisoformat(season['start_date']).date()
                            )
                        
                        with col3:
                            edit_end = st.date_input(
                                "Data Fine",
                                value=datetime.fromisoformat(season['end_date']).date(),
                                min_value=edit_start
                            )
                        
                        edit_modifier = st.slider(
                            "Modificatore di Prezzo (%)",
                            min_value=-50,
                            max_value=100,
                            value=season['price_modifier'],
                            step=5
                        )
                        
                        edit_notes = st.text_input("Note", value=season.get('notes', ''))
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            update_button = st.form_submit_button("Aggiorna Stagione")
                        
                        with col2:
                            cancel_button = st.form_submit_button("Annulla")
                        
                        if update_button:
                            # Update season
                            seasons[i] = {
                                "id": season['id'],
                                "name": edit_name,
                                "start_date": edit_start.isoformat(),
                                "end_date": edit_end.isoformat(),
                                "price_modifier": edit_modifier,
                                "notes": edit_notes
                            }
                            
                            save_pricing_seasons()
                            
                            del st.session_state.editing_season
                            st.success("Stagione aggiornata con successo.")
                            st.rerun()
                        
                        if cancel_button:
                            del st.session_state.editing_season
                            st.rerun()
            else:
                st.info("Nessuna stagione configurata. Aggiungi la tua prima stagione usando il form sopra.")
        else:
            st.warning("Nessuna definizione di stagione trovata. Inizializzazione con valori predefiniti...")
            st.session_state.pricing_seasons['seasons'] = []
            save_pricing_seasons()
            st.rerun()
    
    with season_tabs[2]:
        # Price modifiers
        st.markdown("### Modificatori di Prezzo")
        st.markdown("Configurazione di altri fattori che influenzano i prezzi")
        
        # Initialize price modifiers if not exists
        if 'price_modifiers' not in st.session_state.pricing_seasons:
            st.session_state.pricing_seasons['price_modifiers'] = {
                "weekdays": {
                    "monday": 0,
                    "tuesday": 0,
                    "wednesday": 0,
                    "thursday": 0,
                    "friday": 10,
                    "saturday": 20,
                    "sunday": 10
                },
                "length_of_stay": {
                    "single_night": 0,
                    "two_nights": 0,
                    "weekend": 0,
                    "week": -10,
                    "month": -25
                },
                "lead_time": {
                    "last_minute": -10,
                    "standard": 0,
                    "early_bird": 0
                },
                "occupancy": {
                    "low": -10,
                    "standard": 0,
                    "high": 5
                }
            }
            save_pricing_seasons()
        
        modifiers = st.session_state.pricing_seasons['price_modifiers']
        
        # Tabs for different modifiers
        modifier_tabs = st.tabs(["Giorni Settimana", "Durata Soggiorno", "Anticipo Prenotazione", "Occupazione"])
        
        with modifier_tabs[0]:
            # Weekday modifiers
            st.markdown("#### Modificatori per Giorno della Settimana")
            st.markdown("Applica variazioni di prezzo in base al giorno della settimana")
            
            weekdays = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
            weekday_keys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                for i, (day, key) in enumerate(zip(weekdays, weekday_keys)):
                    modifiers["weekdays"][key] = st.slider(
                        day,
                        min_value=-30,
                        max_value=50,
                        value=modifiers["weekdays"][key],
                        step=5,
                        key=f"weekday_{key}"
                    )
            
            with col2:
                # Create bar chart for weekday modifiers
                weekday_df = pd.DataFrame({
                    'Giorno': weekdays,
                    'Modificatore': [modifiers["weekdays"][key] for key in weekday_keys]
                })
                
                fig = px.bar(
                    weekday_df,
                    x='Giorno',
                    y='Modificatore',
                    color='Modificatore',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    text='Modificatore',
                    title="Variazioni di Prezzo per Giorno della Settimana (%)"
                )
                
                fig.update_traces(texttemplate='%{text}%', textposition='outside')
                fig.update_layout(coloraxis_showscale=False)
                
                st.plotly_chart(fig, use_container_width=True)
            
            if st.button("Salva Modificatori Giorni", key="save_weekday_modifiers"):
                save_pricing_seasons()
                st.success("Modificatori per giorni della settimana salvati con successo.")
        
        with modifier_tabs[1]:
            # Length of stay modifiers
            st.markdown("#### Modificatori per Durata Soggiorno")
            st.markdown("Applica variazioni di prezzo in base alla durata del soggiorno")
            
            stay_types = ["Notte Singola", "Due Notti", "Weekend", "Settimana", "Mese"]
            stay_keys = ["single_night", "two_nights", "weekend", "week", "month"]
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                for stay, key in zip(stay_types, stay_keys):
                    modifiers["length_of_stay"][key] = st.slider(
                        stay,
                        min_value=-50,
                        max_value=50,
                        value=modifiers["length_of_stay"][key],
                        step=5,
                        key=f"stay_{key}"
                    )
            
            with col2:
                # Create bar chart for stay length modifiers
                stay_df = pd.DataFrame({
                    'Tipo Soggiorno': stay_types,
                    'Modificatore': [modifiers["length_of_stay"][key] for key in stay_keys]
                })
                
                fig = px.bar(
                    stay_df,
                    x='Tipo Soggiorno',
                    y='Modificatore',
                    color='Modificatore',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    text='Modificatore',
                    title="Variazioni di Prezzo per Durata Soggiorno (%)"
                )
                
                fig.update_traces(texttemplate='%{text}%', textposition='outside')
                fig.update_layout(coloraxis_showscale=False)
                
                st.plotly_chart(fig, use_container_width=True)
            
            if st.button("Salva Modificatori Durata", key="save_stay_modifiers"):
                save_pricing_seasons()
                st.success("Modificatori per durata soggiorno salvati con successo.")
        
        with modifier_tabs[2]:
            # Lead time modifiers
            st.markdown("#### Modificatori per Anticipo Prenotazione")
            st.markdown("Applica variazioni di prezzo in base all'anticipo con cui viene effettuata la prenotazione")
            
            lead_types = ["Last Minute (0-3 giorni)", "Standard (4-30 giorni)", "Prenotazione Anticipata (>30 giorni)"]
            lead_keys = ["last_minute", "standard", "early_bird"]
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                for lead, key in zip(lead_types, lead_keys):
                    modifiers["lead_time"][key] = st.slider(
                        lead,
                        min_value=-30,
                        max_value=20,
                        value=modifiers["lead_time"][key],
                        step=5,
                        key=f"lead_{key}"
                    )
            
            with col2:
                # Create bar chart for lead time modifiers
                lead_df = pd.DataFrame({
                    'Anticipo': lead_types,
                    'Modificatore': [modifiers["lead_time"][key] for key in lead_keys]
                })
                
                fig = px.bar(
                    lead_df,
                    x='Anticipo',
                    y='Modificatore',
                    color='Modificatore',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    text='Modificatore',
                    title="Variazioni di Prezzo per Anticipo Prenotazione (%)"
                )
                
                fig.update_traces(texttemplate='%{text}%', textposition='outside')
                fig.update_layout(coloraxis_showscale=False)
                
                st.plotly_chart(fig, use_container_width=True)
            
            if st.button("Salva Modificatori Anticipo", key="save_lead_modifiers"):
                save_pricing_seasons()
                st.success("Modificatori per anticipo prenotazione salvati con successo.")
        
        with modifier_tabs[3]:
            # Occupancy modifiers
            st.markdown("#### Modificatori per Tasso di Occupazione")
            st.markdown("Applica variazioni di prezzo in base al tasso di occupazione della zona")
            
            occupancy_types = ["Bassa Occupazione (<50%)", "Occupazione Standard (50-80%)", "Alta Occupazione (>80%)"]
            occupancy_keys = ["low", "standard", "high"]
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                for occ, key in zip(occupancy_types, occupancy_keys):
                    modifiers["occupancy"][key] = st.slider(
                        occ,
                        min_value=-20,
                        max_value=30,
                        value=modifiers["occupancy"][key],
                        step=5,
                        key=f"occupancy_{key}"
                    )
            
            with col2:
                # Create bar chart for occupancy modifiers
                occ_df = pd.DataFrame({
                    'Occupazione': occupancy_types,
                    'Modificatore': [modifiers["occupancy"][key] for key in occupancy_keys]
                })
                
                fig = px.bar(
                    occ_df,
                    x='Occupazione',
                    y='Modificatore',
                    color='Modificatore',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    text='Modificatore',
                    title="Variazioni di Prezzo per Tasso di Occupazione (%)"
                )
                
                fig.update_traces(texttemplate='%{text}%', textposition='outside')
                fig.update_layout(coloraxis_showscale=False)
                
                st.plotly_chart(fig, use_container_width=True)
            
            if st.button("Salva Modificatori Occupazione", key="save_occupancy_modifiers"):
                save_pricing_seasons()
                st.success("Modificatori per tasso di occupazione salvati con successo.")

def show_ai_optimization():
    st.subheader("Ottimizzazione Prezzi con AI")
    
    # Get properties
    properties = st.session_state.properties
    
    if not properties:
        st.info("Non hai ancora registrato immobili. Vai alla sezione 'Gestione Immobili' per aggiungere un immobile.")
        return
    
    # Create property selector
    property_options = {p["id"]: p["name"] for p in properties}
    selected_property_id = st.selectbox(
        "Seleziona Immobile",
        options=list(property_options.keys()),
        format_func=lambda x: property_options.get(x, "")
    )
    
    if selected_property_id:
        property_data = next((p for p in properties if p["id"] == selected_property_id), None)
        
        if property_data:
            # Display property details
            with st.expander("Dettagli Immobile", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"**Nome:** {property_data.get('name')}")
                    st.markdown(f"**Tipo:** {property_data.get('type')}")
                    st.markdown(f"**Città:** {property_data.get('city')}")
                
                with col2:
                    st.markdown(f"**Camere:** {property_data.get('bedrooms')}")
                    st.markdown(f"**Bagni:** {property_data.get('bathrooms')}")
                    st.markdown(f"**Ospiti Max:** {property_data.get('max_guests')}")
                
                with col3:
                    st.markdown(f"**Prezzo Base:** €{property_data.get('base_price'):.2f}")
                    st.markdown(f"**Prezzo Attuale:** €{property_data.get('current_price', property_data.get('base_price')):.2f}")
                    st.markdown(f"**Costo Pulizie:** €{property_data.get('cleaning_fee'):.2f}")
            
            # AI pricing options
            st.markdown("### Ottimizzazione Prezzi Automatica")
            st.markdown("Utilizza l'intelligenza artificiale per ottimizzare i prezzi del tuo immobile in base a vari fattori")
            
            # Market data input
            with st.expander("Dati di Mercato", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    average_price = st.number_input(
                        "Prezzo Medio di Zona (€)",
                        min_value=0.0,
                        value=float(property_data.get('base_price', 100.0)) * 1.1,
                        step=5.0
                    )
                    
                    average_occupancy = st.slider(
                        "Occupazione Media di Zona (%)",
                        min_value=0,
                        max_value=100,
                        value=70
                    )
                
                with col2:
                    season = st.selectbox(
                        "Periodo Attuale",
                        ["Alta Stagione", "Media Stagione", "Bassa Stagione", "Festività"]
                    )
                    
                    local_events = st.multiselect(
                        "Eventi Locali",
                        ["Concerto", "Festival", "Evento Sportivo", "Conferenza", "Mostra", "Fiera", "Nessuno"],
                        default=["Nessuno"]
                    )
            
            # Prepare market data
            market_data = {
                "average_price": average_price,
                "average_occupancy": average_occupancy,
                "season": season,
                "local_events": [e for e in local_events if e != "Nessuno"]
            }
            
            # AI optimization button
            if st.button("Genera Raccomandazioni AI", key="generate_ai_recommendations"):
                with st.spinner("L'AI sta analizzando i dati e generando raccomandazioni di prezzo..."):
                    # Get pricing recommendations from AI
                    recommendations = dynamic_pricing_recommendation(property_data, market_data)
                    
                    # Store recommendations in session state
                    st.session_state.pricing_recommendations = recommendations
            
            # Display recommendations if available
            if 'pricing_recommendations' in st.session_state:
                recommendations = st.session_state.pricing_recommendations
                
                st.markdown("### Raccomandazioni di Prezzo")
                
                if 'error' in recommendations:
                    st.error(f"Errore nella generazione delle raccomandazioni: {recommendations['error']}")
                else:
                    # Display price recommendations in cards
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown('<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px;"><strong>Prezzo Basso:</strong><br>€ {:.2f}</div>'.format(recommendations['low_price']), unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown('<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px;"><strong>Prezzo Medio:</strong><br>€ {:.2f}</div>'.format(recommendations['medium_price']), unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown('<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px;"><strong>Prezzo Alto:</strong><br>€ {:.2f}</div>'.format(recommendations['high_price']), unsafe_allow_html=True)
                    
                    # Display reasons for recommendations
                    st.markdown("#### Motivo delle Raccomandazioni")
                    
                    st.write(recommendations['reasons'])

def get_occupancy_rate(property_id):
    # This is a placeholder, replace with actual implementation
    return random.randint(60, 95)

def load_pricing_data(property_id):
    # This is a placeholder, replace with actual implementation
    return [
        {'date': (datetime.now() + timedelta(days=i)).isoformat(), 'price': random.randint(50, 200), 'status': 'available'}
        for i in range(90)
    ]

def save_pricing_data(property_id, data):
    # This is a placeholder, replace with actual implementation
    print(f"Saving pricing data for property {property_id}: {data}")

def create_calendar_df(month_data, view_month, view_year):
    # Create a DataFrame for the calendar
    first_day = datetime(view_year, view_month, 1)
    last_day = datetime(view_year, view_month, calendar.monthrange(view_year, view_month)[1])

    # Create a DataFrame with dates and prices
    calendar_data = []
    for day in range(1, last_day.day + 1):
        date = datetime(view_year, view_month, day).date()
        price = next((p['price'] for p in month_data if datetime.fromisoformat(p['date']).date() == date), 'N/A')
        calendar_data.append([calendar.day_abbr[date.weekday()], day, f"€{price:.2f}" if isinstance(price, (int, float)) else 'N/A'])

    calendar_df = pd.DataFrame(calendar_data, columns=['Giorno', 'Data', 'Prezzo'])

    # Pivot the DataFrame to create the calendar
    calendar_df = calendar_df.pivot_table(index='Data', columns='Giorno', values='Prezzo', aggfunc='first')
    
    # Reorder columns to start with Monday
    cols = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    calendar_df = calendar_df[cols]
    
    return calendar_df

def trend_with_events(df_trend, events):
    fig = go.Figure()
    
    # Add trace for price trend
    fig.add_trace(go.Scatter(x=df_trend['date'], y=df_trend['price'], mode='lines+markers', name='Prezzo'))
    
    # Add vertical lines for events
    for event in events:
        fig.add_trace(go.Scatter(
            x=[event['date'], event['date']],
            y=[df_trend['price'].min(), df_trend['price'].max()],
            mode='lines',
            line=dict(color='red', width=2, dash='dash'),
            name=event['name'],
            hoverinfo='text',
            text=event['name']
        ))
    
    fig.update_layout(
        title='Trend dei Prezzi con Eventi',
        xaxis_title='Data',
        yaxis_title='Prezzo (€)',
        hovermode='x unified'
    )
    
    return fig

def create_default_seasons():
    # Define some default seasons
    return {
        "seasons": [
            {
                "id": "1",
                "name": "Alta",
                "start_date": f"{datetime.now().year}-06-01",
                "end_date": f"{datetime.now().year}-08-31",
                "price_modifier": 20,
                "notes": "Estate"
            },
            {
                "id": "2",
                "name": "Media",
                "start_date": f"{datetime.now().year}-04-01",
                "end_date": f"{datetime.now().year}-05-31",
                "price_modifier": 10,
                "notes": "Primavera"
            },
            {
                "id": "3",
                "name": "Bassa",
                "start_date": f"{datetime.now().year}-09-01",
                "end_date": f"{datetime.now().year}-11-30",
                "price_modifier": -10,
                "notes": "Autunno"
            }
        ]
    }

def get_date_season(date_str, seasons):
    # Convert date string to datetime object
    date = datetime.fromisoformat(date_str).date()
    
    # Iterate through seasons and check if date falls within season range
    for season in seasons:
        start_date = datetime.fromisoformat(season['start_date']).date()
        end_date = datetime.fromisoformat(season['end_date']).date()
        
        if start_date <= date <= end_date:
            return season['name']
    
    return None

def save_pricing_seasons():
    # Save pricing seasons to JSON file
    with open('data/pricing_seasons.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.pricing_seasons, f, indent=4, ensure_ascii=False)
```python
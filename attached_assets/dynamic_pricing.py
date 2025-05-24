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

def show_dynamic_pricing():
    """Main function to display the dynamic pricing interface with tabs."""
    st.markdown("<h1 style='color: white; background-color: #4F46E5; padding: 10px; border-radius: 5px;'>Prezzi Dinamici</h1>", unsafe_allow_html=True)
    
    # Create tabs for different sections
    tabs = st.tabs(["Panoramica Prezzi", "Gestione Stagioni", "Ottimizzazione AI", "Monitoraggio Mercato"])
    
    # Populate each tab with its content
    with tabs[0]:
        show_pricing_overview()
    
    with tabs[1]:
        show_season_management()
    
    with tabs[2]:
        show_ai_optimization()
    
    with tabs[3]:
        show_market_monitoring()

def show_pricing_overview():
    """Display pricing overview with calendar view and price editor."""
    st.subheader("Panoramica Prezzi")
    
    # Get properties
    properties = st.session_state.get('properties', {})
    
    if not properties:
        st.info("Non hai ancora registrato immobili. Vai alla sezione 'Gestione Immobili' per aggiungere un immobile.")
        return
    
    # Create property selector
    property_options = {pid: prop.get("name", f"Immobile {pid}") for pid, prop in properties.items()}
    selected_property_id = st.selectbox(
        "Seleziona Immobile",
        options=list(property_options.keys()),
        format_func=lambda x: property_options.get(x, ""),
        key="pricing_overview_property_selector"
    )
    
    if not selected_property_id:
        st.warning("Seleziona un immobile per visualizzare i dettagli.")
        return
        
    property_data = properties.get(selected_property_id)
    
    if not property_data:
        st.error("Dati dell'immobile non trovati. Riprova o seleziona un altro immobile.")
        return
        
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
            index=datetime.now().month - 1,
            key="pricing_month_selector"
        )
    
    with col2:
        view_year = st.selectbox(
            "Anno", 
            range(datetime.now().year, datetime.now().year + 2),
            index=0,
            key="pricing_year_selector"
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
            lambda x: f'background-color: rgba(66, 135, 245, {min(1.0, float(x.split("€")[1]) / property_data.get("base_price", 100) * 0.6) if isinstance(x, str) and x.startswith("€") and "€" in x else 0})',
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
    
    if df_trend.empty:
        st.info("Nessun dato disponibile per il grafico di trend. Aggiungi prezzi per visualizzare il grafico.")
        return
        
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
    """Manage pricing seasons and rate modifiers."""
    st.subheader("Gestione Stagioni e Tariffe")
    
    # Initialize season data if not exists
    if 'pricing_seasons' not in st.session_state:
        # Check if season data exists
        if os.path.exists('data/pricing_seasons.json'):
            try:
                with open('data/pricing_seasons.json', 'r', encoding='utf-8') as f:
                    st.session_state.pricing_seasons = json.load(f)
            except Exception as e:
                st.error(f"Errore nel caricamento dei dati delle stagioni: {e}")
                st.session_state.pricing_seasons = create_default_seasons()
        else:
            st.session_state.pricing_seasons = create_default_seasons()
    
    # Get properties
    properties = st.session_state.get('properties', {})
    
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
        year = st.selectbox("Anno", range(current_year, current_year + 3), key="season_year_selector")
        
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
        if 'seasons' not in st.session_state.pricing_seasons:
            st.session_state.pricing_seasons['seasons'] = []
            save_pricing_seasons()
            st.rerun()
            
        seasons = st.session_state.pricing_seasons['seasons']
        
        # Add a new season
        st.markdown("#### Aggiungi Nuova Stagione")
        
        with st.form("add_season_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                season_name = st.selectbox(
                    "Tipo di Stagione",
                    ["Alta", "Media", "Bassa", "Custom"],
                    index=0,
                    key="add_season_type_selector"
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
                            index=["Alta", "Media", "Bassa", "Custom"].index(season['name']) if season['name'] in ["Alta", "Media", "Bassa", "Custom"] else 0,
                            key=f"edit_season_type_{i}"
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
    """Use AI to optimize pricing based on market data."""
    st.subheader("Ottimizzazione Prezzi con AI")
    
    # Get properties
    properties = st.session_state.get('properties', {})
    
    if not properties:
        st.info("Non hai ancora registrato immobili. Vai alla sezione 'Gestione Immobili' per aggiungere un immobile.")
        return
    
    # Create property selector
    property_options = {pid: prop.get("name", f"Immobile {pid}") for pid, prop in properties.items()}
    selected_property_id = st.selectbox(
        "Seleziona Immobile",
        options=list(property_options.keys()),
        format_func=lambda x: property_options.get(x, ""),
        key="ai_optimization_property_selector"
    )
    
    if not selected_property_id:
        st.warning("Seleziona un immobile per procedere con l'ottimizzazione.")
        return
        
    property_data = properties.get(selected_property_id)
    
    if not property_data:
        st.error("Dati dell'immobile non trovati. Riprova o seleziona un altro immobile.")
        return
        
    # Display property details
    with st.expander("Dettagli Immobile", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**Nome:** {property_data.get('name', 'N/A')}")
            st.markdown(f"**Tipo:** {property_data.get('type', 'N/A')}")
            st.markdown(f"**Città:** {property_data.get('city', 'N/A')}")
        
        with col2:
            st.markdown(f"**Camere:** {property_data.get('bedrooms', 'N/A')}")
            st.markdown(f"**Bagni:** {property_data.get('bathrooms', 'N/A')}")
            st.markdown(f"**Ospiti Max:** {property_data.get('max_guests', 'N/A')}")
        
        with col3:
            st.markdown(f"**Prezzo Base:** €{property_data.get('base_price', 0):.2f}")
            st.markdown(f"**Prezzo Attuale:** €{property_data.get('current_price', property_data.get('base_price', 0)):.2f}")
            st.markdown(f"**Costo Pulizie:** €{property_data.get('cleaning_fee', 0):.2f}")
    
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
                ["Alta Stagione", "Media Stagione", "Bassa Stagione", "Festività"],
                key="ai_season_selector"
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
            try:
                # Get pricing recommendations from AI
                recommendations = dynamic_pricing_recommendation(property_data, market_data)
                
                # Store recommendations in session state
                st.session_state.pricing_recommendations = recommendations
            except Exception as e:
                st.error(f"Errore durante la generazione delle raccomandazioni: {e}")
                return
    
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
                st.markdown('<div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px;">', unsafe_allow_html=True)
                st.markdown(f"**Prezzo Base Raccomandato**")
                base_price = recommendations.get("base_price", property_data.get("base_price", 0))
                st.markdown(f"### €{base_price:.2f}")
                
                if property_data.get("base_price"):
                    change = ((base_price - property_data.get("base_price", 0)) / property_data.get("base_price", 1)) * 100
                    st.markdown(f"{'↑' if change >= 0 else '↓'} {abs(change):.1f}% rispetto al prezzo attuale")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px;">', unsafe_allow_html=True)
                st.markdown(f"**Range di Prezzo**")
                min_price = recommendations.get("min_price", base_price * 0.7)
                max_price = recommendations.get("max_price", base_price * 1.3)
                st.markdown(f"### €{min_price:.2f} - €{max_price:.2f}")
                st.markdown(f"Range ottimale per il tuo immobile")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px;">', unsafe_allow_html=True)
                st.markdown(f"**Prezzo Consigliato per Oggi**")
                
                # Calculate today's recommended price
                weekday = datetime.now().strftime("%A").lower()
                
                if "weekday_prices" in recommendations:
                    weekday_map = {
                        "monday": "monday",
                        "tuesday": "tuesday",
                        "wednesday": "wednesday",
                        "thursday": "thursday",
                        "friday": "friday",
                        "saturday": "saturday",
                        "sunday": "sunday"
                    }
                    
                    mapped_day = weekday_map.get(weekday, "monday")
                    today_price = recommendations["weekday_prices"].get(mapped_day, base_price)
                else:
                    today_price = base_price
                
                st.markdown(f"### €{today_price:.2f}")
                st.markdown(f"Prezzo consigliato per {datetime.now().strftime('%d/%m/%Y')}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Display weekday prices
            st.markdown("#### Prezzi per Giorno della Settimana")
            
            if "weekday_prices" in recommendations:
                weekday_labels = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
                weekday_keys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                
                weekday_df = pd.DataFrame({
                    'Giorno': weekday_labels,
                    'Prezzo': [recommendations["weekday_prices"].get(key, base_price) for key in weekday_keys]
                })
                
                fig = px.bar(
                    weekday_df,
                    x='Giorno',
                    y='Prezzo',
                    text_auto='.2f',
                    color='Prezzo',
                    color_continuous_scale=px.colors.sequential.Blues
                )
                
                fig.update_traces(texttemplate='€%{text}', textposition='outside')
                fig.update_layout(coloraxis_showscale=False)
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Display seasonal adjustments
            if "seasonal_adjustments" in recommendations:
                st.markdown("#### Aggiustamenti Stagionali")
                
                seasons = list(recommendations["seasonal_adjustments"].keys())
                seasonal_prices = list(recommendations["seasonal_adjustments"].values())
                
                seasonal_df = pd.DataFrame({
                    'Stagione': [s.replace('_', ' ').title() for s in seasons],
                    'Prezzo': seasonal_prices
                })
                
                fig = px.bar(
                    seasonal_df,
                    x='Stagione',
                    y='Prezzo',
                    text_auto='.2f',
                    color='Prezzo',
                    color_continuous_scale=px.colors.sequential.Oranges
                )
                
                fig.update_traces(texttemplate='€%{text}', textposition='outside')
                fig.update_layout(coloraxis_showscale=False)
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Other recommendations
            st.markdown("#### Altre Raccomandazioni")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Aggiustamenti per Occupazione:**")
                
                if "occupancy_adjustments" in recommendations:
                    for occ, adj in recommendations["occupancy_adjustments"].items():
                        st.markdown(f"- {occ.replace('_', ' ').title()}: {adj}")
                
                if "last_minute_discount" in recommendations:
                    st.markdown("**Sconto Last Minute:**")
                    st.markdown(f"- {recommendations['last_minute_discount']}")
            
            with col2:
                if "long_stay_discount" in recommendations:
                    st.markdown("**Sconto per Soggiorni Lunghi:**")
                    st.markdown(f"- {recommendations['long_stay_discount']}")
                
                if "explanation" in recommendations:
                    st.markdown("**Motivazione:**")
                    st.markdown(f"{recommendations['explanation']}")
            
            # Apply recommendations
            st.markdown("#### Applica Raccomandazioni")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Applica Prezzo Base"):
                    try:
                        # Update property base price
                        update_property(selected_property_id, {
                            'base_price': base_price, 
                            'current_price': base_price
                        })
                        
                        st.success(f"Prezzo base aggiornato a €{base_price:.2f}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore durante l'aggiornamento del prezzo: {e}")
            
            with col2:
                if st.button("Applica Prezzo di Oggi"):
                    try:
                        # Update property current price
                        update_property(selected_property_id, {'current_price': today_price})
                        
                        st.success(f"Prezzo attuale aggiornato a €{today_price:.2f}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore durante l'aggiornamento del prezzo: {e}")
            
            with col3:
                if st.button("Applica Tutti i Prezzi"):
                    st.info("Questa funzione applicherebbe tutti i prezzi giornalieri per il prossimo mese. Implementazione completa in un'applicazione reale.")

def show_market_monitoring():
    """Compare prices with competitors and show market trends."""
    st.subheader("Monitoraggio Mercato")
    
    st.markdown("### Analisi Comparativa Prezzi")
    st.markdown("Confronta i tuoi prezzi con quelli di immobili simili nel mercato")
    
    # Get properties
    properties = st.session_state.get('properties', {})
    
    if not properties:
        st.info("Non hai ancora registrato immobili.")
        return
    
    # Create property selector
    property_options = {pid: prop.get("name", f"Immobile {pid}") for pid, prop in properties.items()}
    selected_property_id = st.selectbox(
        "Seleziona Immobile",
        options=list(property_options.keys()),
        format_func=lambda x: property_options.get(x, ""),
        key="market_monitoring_property_selector"
    )
    
    if not selected_property_id:
        st.warning("Seleziona un immobile per visualizzare l'analisi di mercato.")
        return
        
    property_data = properties.get(selected_property_id)
    
    if not property_data:
        st.error("Dati dell'immobile non trovati. Riprova o seleziona un altro immobile.")
        return
        
    # Generate competitor data
    try:
        competitors = generate_competitor_data(property_data)
    except Exception as e:
        st.error(f"Errore nella generazione dei dati dei competitori: {e}")
        competitors = []
    
    if not competitors:
        st.warning("Nessun dato di competitori disponibile per l'analisi.")
        return
        
    # Display competitor comparison
    st.markdown("#### Confronto con Competitori")
    
    competitors_df = pd.DataFrame(competitors)
    st.dataframe(competitors_df, use_container_width=True)
    
    # Price comparison chart
    st.markdown("#### Confronto Prezzi")
    
    comparison_df = pd.DataFrame([
        {
            "Nome": property_data.get("name", "Tuo Immobile") + " (Tuo)",
            "Prezzo": property_data.get("current_price", property_data.get("base_price", 0)),
            "Tipo": "Tuo Immobile"
        }
    ] + [
        {
            "Nome": comp["nome"],
            "Prezzo": comp["prezzo_base"],
            "Tipo": "Competitore"
        }
        for comp in competitors
    ])
    
    fig = px.bar(
        comparison_df,
        x="Nome",
        y="Prezzo",
        color="Tipo",
        text_auto='.2f',
        color_discrete_map={"Tuo Immobile": "#1E88E5", "Competitore": "#78909C"}
    )
    
    fig.update_traces(texttemplate='€%{text}', textposition='outside')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Market position
    st.markdown("#### Posizionamento di Mercato")
    
    your_price = property_data.get("current_price", property_data.get("base_price", 0))
    competitor_prices = [comp.get("prezzo_base", 0) for comp in competitors]
    
    # Avoid division by zero and handle empty list
    if competitor_prices and len(competitor_prices) > 0:
        market_avg = sum(competitor_prices) / len(competitor_prices)
        min_price = min(competitor_prices)
        max_price = max(competitor_prices)
        percentile = sum(1 for p in competitor_prices if p < your_price) / len(competitor_prices) * 100
    else:
        market_avg = your_price
        min_price = your_price * 0.8
        max_price = your_price * 1.2
        percentile = 50
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Il Tuo Prezzo", f"€{your_price:.2f}")
    
    with col2:
        diff_pct = (your_price - market_avg) / market_avg * 100 if market_avg > 0 else 0
        st.metric("Media di Mercato", f"€{market_avg:.2f}", f"{diff_pct:+.1f}%")
    
    with col3:
        st.metric("Percentile", f"{percentile:.1f}%", 
                 help="Percentuale di competitori con prezzo inferiore al tuo")
    
    # Price gauge chart
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = your_price,
        number = {"prefix": "€", "valueformat": ".2f"},
        delta = {"reference": market_avg, "valueformat": ".2f"},
        gauge = {
            "axis": {"range": [min_price * 0.9, max_price * 1.1]},
            "bar": {"color": "#1E88E5"},
            "steps": [
                {"range": [min_price * 0.9, min_price], "color": "#FFCDD2"},
                {"range": [min_price, market_avg * 0.9], "color": "#FFECB3"},
                {"range": [market_avg * 0.9, market_avg * 1.1], "color": "#C8E6C9"},
                {"range": [market_avg * 1.1, max_price], "color": "#FFECB3"},
                {"range": [max_price, max_price * 1.1], "color": "#FFCDD2"}
            ],
            "threshold": {
                "line": {"color": "red", "width": 2},
                "thickness": 0.75,
                "value": market_avg
            }
        },
        title = {"text": "Posizionamento Prezzo di Mercato"}
    ))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Market trends
    st.markdown("#### Tendenze di Mercato")
    
    # Generate sample trend data
    try:
        trend_data = generate_trend_data()
    except Exception as e:
        st.error(f"Errore nella generazione dei dati di trend: {e}")
        return
    
    # Create line chart for trends
    trend_df = pd.DataFrame(trend_data)
    
    fig = px.line(
        trend_df,
        x="mese",
        y=["tuo_prezzo", "media_mercato", "occupazione"],
        title="Trend Prezzi e Occupazione",
        labels={"value": "Valore", "variable": "Metrica", "mese": "Mese"},
        color_discrete_map={
            "tuo_prezzo": "#1E88E5", 
            "media_mercato": "#FFA000", 
            "occupazione": "#43A047"
        }
    )
    
    # Create secondary y-axis for occupancy
    fig.update_layout(
        yaxis=dict(title="Prezzo (€)"),
        yaxis2=dict(
            title="Occupazione (%)",
            overlaying="y",
            side="right",
            range=[0, 100]
        )
    )
    
    # Move occupancy to secondary y-axis
    for trace in fig.data:
        if trace.name == "occupazione":
            trace.yaxis = "y2"
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Recommendations based on market position
    st.markdown("#### Raccomandazioni Basate sul Mercato")
    
    message = ""
    if your_price < market_avg * 0.9:
        message = """
        **I tuoi prezzi sono significativamente più bassi della media di mercato.**
        
        Considerazioni:
        - Potresti aumentare i prezzi gradualmente per avvicinarti alla media
        - Verifica se stai comunicando bene tutti i servizi e i punti di forza del tuo immobile
        - Valuta se migliorare la qualità delle foto o della descrizione dell'annuncio
        """
    elif your_price > market_avg * 1.1:
        message = """
        **I tuoi prezzi sono significativamente più alti della media di mercato.**
        
        Considerazioni:
        - Assicurati che il tuo immobile offra caratteristiche premium che giustifichino il prezzo
        - Monitora attentamente il tasso di occupazione per verificare se il mercato accetta il tuo prezzo
        - Considera di offrire servizi aggiuntivi o migliorare l'esperienza degli ospiti
        """
    else:
        message = """
        **I tuoi prezzi sono in linea con la media di mercato.**
        
        Considerazioni:
        - La tua strategia di prezzo sembra ben bilanciata
        - Continua a monitorare i cambiamenti nel mercato
        - Valuta piccoli aggiustamenti stagionali per massimizzare i ricavi
        """
    
    st.markdown(message)

# Helper functions
def get_date_range(days=180):
    """Get a date range from today to X days in the future."""
    start_date = datetime.now().date()
    return [start_date + timedelta(days=i) for i in range(days)]

def create_calendar_df(pricing_data, month, year):
    """Create a calendar dataframe with pricing data."""
    # Get the first day of the month and the number of days
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    
    num_days = last_day.day
    
    # Create a list of dates for the month
    dates = [datetime(year, month, day) for day in range(1, num_days + 1)]
    
    # Create a mapping from date to price
    date_to_price = {datetime.fromisoformat(p['date']).date(): p['price'] for p in pricing_data}
    
    # Create a 2D array for the calendar
    # Each week is a row, each day is a column
    calendar = []
    week = [None] * 7  # 7 days in a week
    
    # Fill in blank days before the first day of the month
    first_weekday = first_day.weekday()  # Monday is 0, Sunday is 6
    
    # Adjust for our calendar format where Monday is at index 0
    current_date = first_day
    
    # Create rows for the calendar
    while current_date <= last_day:
        weekday = current_date.weekday()
        
        # Format the price
        date_key = current_date.date()
        price = date_to_price.get(date_key, None)
        display_text = f"€{price:.2f}" if price is not None else ""
        
        week[weekday] = display_text
        
        # Move to the next day
        current_date += timedelta(days=1)
        
        # If it's the end of the week or the end of the month, append the current week
        if weekday == 6 or current_date > last_day:
            calendar.append(week.copy())
            week = [None] * 7
    
    # Create a dataframe with the calendar data
    # Use day numbers as row labels
    day = 1
    rows = []
    day_labels = []
    
    for week_data in calendar:
        row = {}
        row['Settimana'] = len(day_labels) + 1
        
        for i, price in enumerate(week_data):
            day_name = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom'][i]
            if price is not None:
                row[day_name] = f"{day} {price}"
                day += 1
            else:
                row[day_name] = ""
        
        rows.append(row)
        day_labels.append(len(day_labels) + 1)
    
    calendar_df = pd.DataFrame(rows)
    return calendar_df

def get_occupancy_rate(property_id):
    """Get occupancy rate for a property (simulated)."""
    # In a real app, would calculate this from actual bookings
    return random.uniform(50, 90)

def load_pricing_data(property_id):
    """Load pricing data for a property."""
    # Check if pricing data exists
    filename = f"data/pricing_{property_id}.json"
    
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading pricing data for property {property_id}: {e}")
            return None
    
    return None

def save_pricing_data(property_id, pricing_data):
    """Save pricing data for a property."""
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    filename = f"data/pricing_{property_id}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(pricing_data, f, ensure_ascii=False, indent=2)

def generate_sample_pricing(property_data, date_range):
    """Generate sample pricing data for demo purposes."""
    base_price = property_data.get('base_price', 50.0)
    
    # Define seasonal factors
    seasonal_factors = {
        1: 0.8,  # January
        2: 0.8,  # February
        3: 0.9,  # March
        4: 1.0,  # April
        5: 1.0,  # May
        6: 1.2,  # June
        7: 1.5,  # July
        8: 1.6,  # August
        9: 1.1,  # September
        10: 0.9,  # October
        11: 0.8,  # November
        12: 1.2   # December
    }
    
    # Define day of week factors
    day_factors = {
        0: 0.8,  # Monday
        1: 0.8,  # Tuesday
        2: 0.8,  # Wednesday
        3: 0.9,  # Thursday
        4: 1.2,  # Friday
        5: 1.3,  # Saturday
        6: 1.1   # Sunday
    }
    
    # Generate prices
    pricing_data = []
    
    for date in date_range:
        # Apply seasonal factor
        seasonal_factor = seasonal_factors[date.month]
        
        # Apply day of week factor
        day_factor = day_factors[date.weekday()]
        
        # Calculate price
        price = base_price * seasonal_factor * day_factor
        
        # Add some random variation
        price *= random.uniform(0.95, 1.05)
        
        # Round to 2 decimal places
        price = round(price, 2)
        
        # Add to pricing data
        pricing_data.append({
            'date': date.isoformat(),
            'price': price,
            'status': 'available'
        })
    
    return pricing_data

def trend_with_events(df_trend, events=None):
    """Create a trend chart with event markers."""
    fig = go.Figure()
    
    # Add price line
    if not df_trend.empty:
        fig.add_trace(go.Scatter(
            x=df_trend['date'],
            y=df_trend['price'],
            name="Prezzo",
            line=dict(color='royalblue')
        ))
    else:
        # Add sample data if DataFrame is empty
        dates = [datetime.now() + timedelta(days=i) for i in range(60)]
        fig.add_trace(go.Scatter(
            x=dates,
            y=[50 + i * 0.5 + random.uniform(-2, 2) for i in range(len(dates))],
            name="Prezzo (simulato)",
            line=dict(color='royalblue', dash='dot')
        ))
        
        # Add sample events if none provided
        if events is None:
            events = [
                {'date': dates[15], 'name': 'Festival Locale'},
                {'date': dates[30], 'name': 'Concerto'},
                {'date': dates[45], 'name': 'Evento Sportivo'}
            ]
    
    # Add event markers
    if events:
        for event in events:
            # Find y-value for the event date or use a default
            if not df_trend.empty:
                try:
                    closest_dates = df_trend['date'].apply(lambda x: abs((x - event['date']).total_seconds()))
                    closest_idx = closest_dates.argmin()
                    y_value = df_trend.iloc[closest_idx]['price'] + 10  # Add offset to place above the line
                except (ValueError, IndexError):
                    y_value = 65 + random.uniform(0, 5)  # Fallback if there's an error
            else:
                y_value = 65 + random.uniform(0, 5)
                
            fig.add_trace(go.Scatter(
                x=[event['date']],
                y=[y_value],
                mode='markers+text',
                marker=dict(size=10, color='red'),
                text=[event['name']],
                textposition="top center",
                name=event['name']
            ))
    
    fig.update_layout(
        title="Trend Prezzi con Eventi",
        xaxis_title="Data",
        yaxis_title="Prezzo (€)",
        legend_title="Legenda",
        xaxis=dict(
            tickformat="%d %b"
        )
    )
    
    return fig

def create_default_seasons():
    """Create default season definitions."""
    current_year = datetime.now().year
    
    return {
        "seasons": [
            {
                "id": "1",
                "name": "Alta",
                "start_date": f"{current_year}-07-01",
                "end_date": f"{current_year}-08-31",
                "price_modifier": 50,
                "notes": "Estate - Alta stagione"
            },
            {
                "id": "2",
                "name": "Media",
                "start_date": f"{current_year}-04-01",
                "end_date": f"{current_year}-06-30",
                "price_modifier": 20,
                "notes": "Primavera - Media stagione"
            },
            {
                "id": "3",
                "name": "Media",
                "start_date": f"{current_year}-09-01",
                "end_date": f"{current_year}-10-31",
                "price_modifier": 20,
                "notes": "Autunno - Media stagione"
            },
            {
                "id": "4",
                "name": "Bassa",
                "start_date": f"{current_year}-11-01",
                "end_date": f"{current_year}-03-31",
                "price_modifier": -20,
                "notes": "Inverno - Bassa stagione (escluse festività)"
            },
            {
                "id": "5",
                "name": "Alta",
                "start_date": f"{current_year}-12-20",
                "end_date": f"{current_year}-01-06",
                "price_modifier": 40,
                "notes": "Festività natalizie"
            }
        ]
    }

def save_pricing_seasons():
    """Save pricing seasons to file."""
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    with open('data/pricing_seasons.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.pricing_seasons, f, ensure_ascii=False, indent=2)

def get_date_season(date_str, seasons):
    """Determine which season a date falls into."""
    try:
        date = datetime.fromisoformat(date_str).date()
        
        for season in seasons:
            start_date = datetime.fromisoformat(season['start_date']).date()
            end_date = datetime.fromisoformat(season['end_date']).date()
            
            # Handle seasons that span years
            if start_date > end_date:
                # Season goes from this year to next year
                if (date >= start_date) or (date <= end_date):
                    return season['name']
            else:
                # Normal season within the same year
                if start_date <= date <= end_date:
                    return season['name']
    except (ValueError, TypeError) as e:
        # Handle invalid date format
        print(f"Error determining season for date {date_str}: {e}")
    
    return None

def generate_competitor_data(property_data):
    """Generate competitor data for market comparison from all co-hosts in the area."""
    
    # In a production app, this would pull data from APIs like AirBnB, Booking.com, etc.
    # We're simulating competition from multiple co-hosts in the same area
    
    base_price = float(property_data.get('base_price', 100))
    bedrooms = property_data.get('bedrooms', 1)
    bathrooms = property_data.get('bathrooms', 1)
    city = property_data.get('city', 'Roma')
    area = property_data.get('address', '').split(',')[0] if property_data.get('address') else "Centro"
    
    competitors = []
    
    # Co-host companies in the area
    co_host_companies = [
        "AffittiBnB", "HostItalia", "EasyStay", "ItaliaBnB", "VacanzaFacile", 
        "CasaBella", "DreamStay", "LuxuryRental", "ItalyVacation", "BookingStar", 
        "MyGuestHome", "RomaStay", "ItalianHosts", "MilanoBnB", "VeneziaHost"
    ]
    
    # Different property types
    property_types = ["Appartamento", "Casa", "Villa", "B&B", "Camera Privata", "Loft", "Attico"]
    
    # Locations within the city
    locations = ["Centro", "Stazione", "Lungomare", "Piazza Principale", "Quartiere Storico", 
                "Zona Turistica", "Periferia", "Area Residenziale", "Vicino al Mare", "Collina"]
    
    # Pricing strategies
    pricing_strategies = [
        ("Premium", random.uniform(1.1, 1.3)),
        ("Standard", random.uniform(0.9, 1.1)),
        ("Economy", random.uniform(0.7, 0.9)),
        ("Luxury", random.uniform(1.3, 1.5)),
        ("Affari", random.uniform(0.8, 1.0)),
        ("Famiglie", random.uniform(0.9, 1.2)),
        ("Festivo", random.uniform(1.2, 1.4))
    ]
    
    # Generate 8-15 competitors from different co-hosts in the area
    for i in range(random.randint(8, 15)):
        # Assign a co-host company randomly
        co_host = random.choice(co_host_companies)
        
        # Vary bedrooms and bathrooms slightly but realistically
        comp_bedrooms = max(1, bedrooms + random.choice([-1, 0, 0, 0, 1]))
        comp_bathrooms = max(1, bathrooms + random.choice([-0.5, 0, 0, 0, 0.5]))
        
        # Pricing strategy for this competitor
        strategy_name, price_factor = random.choice(pricing_strategies)
        
        # Calculate price based on property features and pricing strategy
        price_factor += (comp_bedrooms - bedrooms) * 0.15  # Bedroom adjustment
        price_factor += (comp_bathrooms - bathrooms) * 0.1  # Bathroom adjustment
        
        # Location premium (some areas have higher prices)
        location = random.choice(locations)
        if location in ["Centro", "Zona Turistica", "Lungomare"]:
            price_factor += random.uniform(0.05, 0.15)
        
        comp_price = round(base_price * price_factor, 2)
        
        # Generate realistic ratings and reviews
        overall_rating = round(random.uniform(3.5, 5.0), 1)
        review_count = random.randint(5, 150)
        
        # Create distance within the area
        distances = ["350m", "500m", "750m", "1km", "1.2km", "1.5km", "1.8km", "2km", "2.5km", "3km"]
        
        # Calculate occupancy rate (useful for pricing recommendations)
        occupancy_rate = random.randint(50, 95)
        
        competitors.append({
            "nome": f"Immobile {i+1}",
            "co_host": co_host,
            "tipo": random.choice(property_types),
            "città": city,
            "zona": location,
            "camere": comp_bedrooms,
            "bagni": comp_bathrooms,
            "ospiti_max": comp_bedrooms * 2 + random.randint(0, 2),
            "distanza": random.choice(distances),
            "prezzo_base": comp_price,
            "prezzo_weekend": round(comp_price * random.uniform(1.1, 1.3), 2),
            "pulizie": round(comp_price * 0.3, 2),
            "strategia": strategy_name,
            "valutazione": overall_rating,
            "recensioni": review_count,
            "occupazione": f"{occupancy_rate}%"
        })
    
    return competitors

def generate_trend_data():
    """Generate sample trend data for market monitoring."""
    today = datetime.now()
    months = []
    
    # Generate data for the past 6 months
    for i in range(-6, 6):
        month = (today.month + i - 1) % 12 + 1
        year = today.year + (today.month + i - 1) // 12
        
        # Generate data with seasonal pattern
        seasonal_factor = 1.0
        if month in [6, 7, 8]:  # Summer
            seasonal_factor = 1.3
        elif month in [11, 12, 1]:  # Winter holidays
            seasonal_factor = 1.2
        elif month in [3, 4, 5, 9, 10]:  # Spring and Fall
            seasonal_factor = 1.1
        else:  # Low season
            seasonal_factor = 0.9
        
        # Generate values
        base_value = 100
        your_price = round(base_value * seasonal_factor * random.uniform(0.95, 1.05), 2)
        market_avg = round(base_value * seasonal_factor * random.uniform(0.9, 1.1), 2)
        
        # Occupancy is inversely related to price in some seasons
        if month in [6, 7, 8]:  # High demand in summer regardless of price
            occupancy = random.uniform(75, 95)
        else:
            # Higher price might mean lower occupancy
            price_ratio = your_price / market_avg
            occupancy = 80 * (2 - price_ratio) * random.uniform(0.85, 1.15)
            occupancy = max(30, min(95, occupancy))  # Clip between 30% and 95%
        
        # Add the month data
        months.append({
            "mese": f"{year}-{month:02d}",
            "mese_nome": datetime(year, month, 1).strftime("%b %Y"),
            "tuo_prezzo": your_price,
            "media_mercato": market_avg,
            "occupazione": round(occupancy, 1)
        })
    
    return months
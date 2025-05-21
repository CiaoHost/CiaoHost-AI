import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
from utils.database import (
    get_all_invoices, get_invoice, add_booking, update_booking, 
    get_booking, get_property, get_all_properties,
    create_invoice_for_booking
)
from utils.pdf_export import create_invoice_pdf

def show_fiscal_management():
    import streamlit as st
    st.header("Fiscal Management")
    st.write("Fiscal management features will be implemented here")

def show_invoices():
    st.subheader("Elenco Fatture")
    
    # Get all invoices
    invoices = get_all_invoices()
    
    if not invoices:
        st.info("Nessuna fattura presente nel sistema. Vai alla scheda 'Generazione Fatture' per creare nuove fatture.")
        return
    
    # Add filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.multiselect(
            "Filtra per Stato",
            ["Emessa", "Pagata", "Annullata"],
            default=["Emessa", "Pagata"]
        )
    
    with col2:
        date_range = st.date_input(
            "Intervallo Date",
            [(datetime.now() - timedelta(days=180)).date(), datetime.now().date()],
            key="invoice_date_range"
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = (datetime.now() - timedelta(days=180)).date()
            end_date = datetime.now().date()
    
    with col3:
        search_query = st.text_input("Cerca", placeholder="Numero fattura o nome ospite")
    
    # Create dataframe from invoices
    invoices_data = []
    
    for invoice in invoices:
        # Get booking data
        booking = get_booking(invoice.get("booking_id"))
        if not booking:
            continue
        
        # Get property data
        property_data = get_property(booking.get("property_id"))
        property_name = property_data.get("name") if property_data else "Sconosciuto"
        
        # Convert date string to date object
        invoice_date = datetime.fromisoformat(invoice.get("date")).date() if invoice.get("date") else None
        
        # Apply date filter
        if invoice_date and (invoice_date < start_date or invoice_date > end_date):
            continue
        
        # Apply status filter
        if status_filter and invoice.get("status") not in status_filter:
            continue
        
        # Apply search query
        if search_query:
            search_terms = [
                invoice.get("invoice_number", ""),
                booking.get("guest_name", ""),
                property_name
            ]
            if not any(search_query.lower() in term.lower() for term in search_terms if term):
                continue
        
        invoices_data.append({
            "id": invoice.get("id"),
            "Numero": invoice.get("invoice_number"),
            "Data": invoice_date.strftime("%d/%m/%Y") if invoice_date else "N/A",
            "Ospite": booking.get("guest_name"),
            "Immobile": property_name,
            "Importo": f"€{invoice.get('amount'):.2f}",
            "IVA": f"€{invoice.get('tax_amount'):.2f}",
            "Stato": invoice.get("status"),
            "Data Pagamento": invoice.get("payment_date")
        })
    
    if invoices_data:
        # Convert to dataframe
        df = pd.DataFrame(invoices_data)
        st.dataframe(df, use_container_width=True)
        
        # View invoice details
        st.subheader("Dettagli Fattura")
        
        selected_invoice_id = st.selectbox(
            "Seleziona una fattura da visualizzare",
            options=[inv["id"] for inv in invoices_data],
            format_func=lambda x: next((f"{inv['Numero']} - {inv['Ospite']} ({inv['Data']})" 
                                      for inv in invoices_data if inv["id"] == x), x)
        )
        
        if selected_invoice_id:
            selected_invoice = next((inv for inv in invoices if inv["id"] == selected_invoice_id), None)
            
            if selected_invoice:
                booking = get_booking(selected_invoice.get("booking_id"))
                property_data = get_property(booking.get("property_id")) if booking else None
                
                if booking and property_data:
                    # Display invoice details
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Numero Fattura:** {selected_invoice.get('invoice_number')}")
                        st.markdown(f"**Data:** {datetime.fromisoformat(selected_invoice.get('date')).strftime('%d/%m/%Y') if selected_invoice.get('date') else 'N/A'}")
                        st.markdown(f"**Ospite:** {booking.get('guest_name')}")
                        st.markdown(f"**Immobile:** {property_data.get('name')}")
                    
                    with col2:
                        st.markdown(f"**Importo Totale:** €{selected_invoice.get('amount'):.2f}")
                        st.markdown(f"**IVA ({selected_invoice.get('tax_percentage')}%):** €{selected_invoice.get('tax_amount'):.2f}")
                        st.markdown(f"**Imponibile:** €{selected_invoice.get('amount') - selected_invoice.get('tax_amount'):.2f}")
                        st.markdown(f"**Stato:** {selected_invoice.get('status')}")
                        if selected_invoice.get('payment_date'):
                            st.markdown(f"**Data Pagamento:** {selected_invoice.get('payment_date')}")
                    
                    # Notes
                    if selected_invoice.get("notes"):
                        st.markdown("**Note:**")
                        st.write(selected_invoice.get("notes"))
                    
                    # Invoice actions
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("Scarica PDF"):
                            # Generate PDF
                            pdf_buffer = create_invoice_pdf(selected_invoice, booking, property_data)
                            
                            # Create download button
                            st.download_button(
                                label="Scarica PDF",
                                data=pdf_buffer,
                                file_name=f"fattura_{selected_invoice.get('invoice_number')}.pdf",
                                mime="application/pdf"
                            )
                    
                    with col2:
                        # Change invoice status
                        if selected_invoice.get("status") != "Pagata":
                            if st.button("Segna come Pagata"):
                                # Update booking and invoice status
                                update_booking(booking.get("id"), {"payment_status": "Pagato"})
                                
                                # In a real app, would update invoice status
                                st.success("Fattura segnata come Pagata")
                                st.rerun()
                        else:
                            if st.button("Segna come Non Pagata"):
                                # Update booking and invoice status
                                update_booking(booking.get("id"), {"payment_status": "In attesa"})
                                
                                # In a real app, would update invoice status
                                st.success("Fattura segnata come Non Pagata")
                                st.rerun()
                    
                    with col3:
                        if selected_invoice.get("status") != "Annullata":
                            if st.button("Annulla Fattura"):
                                # In a real app, would update invoice status
                                st.success("Fattura annullata")
                                st.rerun()
    else:
        st.info("Nessuna fattura corrisponde ai filtri selezionati.")

def generate_invoices():
    st.subheader("Generazione Fatture")
    
    # Get bookings without invoices
    all_invoices = get_all_invoices()
    invoiced_booking_ids = [inv.get("booking_id") for inv in all_invoices]
    
    bookings_data = []
    for booking in st.session_state.bookings:
        if booking.get("id") not in invoiced_booking_ids and booking.get("status") in ["confermata", "attiva", "completata"]:
            property_data = get_property(booking.get("property_id"))
            property_name = property_data.get("name") if property_data else "Sconosciuto"
            
            bookings_data.append({
                "id": booking.get("id"),
                "Ospite": booking.get("guest_name"),
                "Immobile": property_name,
                "Check-in": booking.get("checkin_date"),
                "Check-out": booking.get("checkout_date"),
                "Totale": f"€{booking.get('total_price'):.2f}",
                "Stato": booking.get("status")
            })
    
    if bookings_data:
        st.write("Seleziona le prenotazioni per cui generare fatture:")
        
        # Convert to dataframe
        df = pd.DataFrame(bookings_data)
        
        # Multiselect for booking selection
        selected_booking_ids = []
        for i, booking in enumerate(bookings_data):
            if st.checkbox(f"{booking['Ospite']} - {booking['Immobile']} ({booking['Check-in']} to {booking['Check-out']})", key=f"booking_{i}"):
                selected_booking_ids.append(booking["id"])
        
        if selected_booking_ids:
            if st.button("Genera Fatture"):
                with st.spinner("Generazione fatture in corso..."):
                    for booking_id in selected_booking_ids:
                        create_invoice_for_booking(booking_id)
                    
                    st.success(f"Generate {len(selected_booking_ids)} fatture con successo!")
                    st.rerun()
    else:
        st.info("Tutte le prenotazioni hanno già fatture associate.")
    
    # Generate invoice for specific booking
    st.subheader("Genera Fattura per Prenotazione Specifica")
    
    all_bookings = []
    for booking in st.session_state.bookings:
        property_data = get_property(booking.get("property_id"))
        property_name = property_data.get("name") if property_data else "Sconosciuto"
        
        all_bookings.append({
            "id": booking.get("id"),
            "name": f"{booking.get('guest_name')} - {property_name} ({booking.get('checkin_date')} to {booking.get('checkout_date')})"
        })
    
    selected_booking_id = st.selectbox(
        "Seleziona Prenotazione",
        options=[b["id"] for b in all_bookings],
        format_func=lambda x: next((b["name"] for b in all_bookings if b["id"] == x), x)
    )
    
    if selected_booking_id:
        if st.button("Genera Fattura"):
            with st.spinner("Generazione fattura in corso..."):
                result = create_invoice_for_booking(selected_booking_id)
                if result:
                    st.success("Fattura generata con successo!")
                else:
                    st.error("Errore nella generazione della fattura.")

def export_invoices():
    st.subheader("Esportazione Fatture")
    
    # Get all invoices
    invoices = get_all_invoices()
    
    if not invoices:
        st.info("Nessuna fattura presente nel sistema.")
        return
    
    # Export filters
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Data Inizio",
            value=(datetime.now() - timedelta(days=180)).date()
        )
    
    with col2:
        end_date = st.date_input(
            "Data Fine",
            value=datetime.now().date()
        )
    
    status_filter = st.multiselect(
        "Stato Fattura",
        ["Emessa", "Pagata", "Annullata"],
        default=["Emessa", "Pagata"]
    )
    
    # Apply filters
    filtered_invoices = []
    
    for invoice in invoices:
        # Convert date string to date object
        invoice_date = datetime.fromisoformat(invoice.get("date")).date() if invoice.get("date") else None
        
        # Apply date filter
        if invoice_date and (invoice_date < start_date or invoice_date > end_date):
            continue
        
        # Apply status filter
        if status_filter and invoice.get("status") not in status_filter:
            continue
        
        # Get booking data
        booking = get_booking(invoice.get("booking_id"))
        
        if booking:
            # Get property data
            property_data = get_property(booking.get("property_id"))
            property_name = property_data.get("name") if property_data else "Sconosciuto"
            
            filtered_invoices.append({
                "id": invoice.get("id"),
                "Numero Fattura": invoice.get("invoice_number"),
                "Data": invoice_date.strftime("%d/%m/%Y") if invoice_date else "N/A",
                "Ospite": booking.get("guest_name"),
                "Immobile": property_name,
                "Importo": invoice.get("amount"),
                "IVA": invoice.get("tax_amount"),
                "Aliquota IVA": invoice.get("tax_percentage"),
                "Imponibile": invoice.get("amount") - invoice.get("tax_amount"),
                "Stato": invoice.get("status"),
                "Data Pagamento": invoice.get("payment_date"),
                "Note": invoice.get("notes", "")
            })
    
    if filtered_invoices:
        st.write(f"Trovate {len(filtered_invoices)} fatture nel periodo selezionato.")
        
        # Create dataframe for export
        df = pd.DataFrame(filtered_invoices)
        
        # Export buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export to CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Esporta CSV",
                data=csv,
                file_name=f"fatture_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Export to Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name="Fatture", index=False)
                
                # Get the xlsxwriter workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets["Fatture"]
                
                # Add some cell formats
                format_header = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC'})
                format_money = workbook.add_format({'num_format': '€#,##0.00'})
                
                # Set column widths and formats
                worksheet.set_column('A:A', 10)  # ID
                worksheet.set_column('B:B', 15)  # Numero Fattura
                worksheet.set_column('C:C', 12)  # Data
                worksheet.set_column('D:D', 20)  # Ospite
                worksheet.set_column('E:E', 20)  # Immobile
                worksheet.set_column('F:F', 12, format_money)  # Importo
                worksheet.set_column('G:G', 12, format_money)  # IVA
                worksheet.set_column('H:H', 12)  # Aliquota IVA
                worksheet.set_column('I:I', 12, format_money)  # Imponibile
                worksheet.set_column('J:J', 10)  # Stato
                worksheet.set_column('K:K', 15)  # Data Pagamento
                worksheet.set_column('L:L', 30)  # Note
                
                # Write the column headers with the defined format
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, format_header)
            
            # Return the Excel file from the BytesIO object
            buffer.seek(0)
            
            st.download_button(
                label="Esporta Excel",
                data=buffer,
                file_name=f"fatture_{start_date}_{end_date}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col3:
            if st.button("Esporta PDF Multipli"):
                st.info("Questa funzione genererebbe un PDF per ogni fattura selezionata e le includerebbe in un file ZIP.")
                st.info("In un'applicazione completa, qui verrebbe fornito un file ZIP con tutte le fatture PDF.")
    else:
        st.info("Nessuna fattura corrisponde ai filtri selezionati.")

def fiscal_settings():
    st.subheader("Impostazioni Fiscali")
    
    # Company information
    st.markdown("### Informazioni Azienda")
    
    # Initialize company info if not exist
    if "company_info" not in st.session_state:
        st.session_state.company_info = {
            "name": "CiaoHost Srl",
            "address": "Via Roma 123",
            "city": "Milano",
            "zip": "20123",
            "country": "Italia",
            "vat_number": "IT12345678901",
            "fiscal_code": "12345678901",
            "email": "amministrazione@ciaohost.com",
            "phone": "+39 123 456 7890",
            "website": "www.ciaohost.com"
        }
    
    company_info = st.session_state.company_info
    
    # Form for company info
    with st.form("company_info_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("Nome Azienda", value=company_info.get("name", ""))
            company_address = st.text_input("Indirizzo", value=company_info.get("address", ""))
            company_city = st.text_input("Città", value=company_info.get("city", ""))
            company_zip = st.text_input("CAP", value=company_info.get("zip", ""))
            company_country = st.text_input("Paese", value=company_info.get("country", ""))
        
        with col2:
            company_vat = st.text_input("Partita IVA", value=company_info.get("vat_number", ""))
            company_fiscal = st.text_input("Codice Fiscale", value=company_info.get("fiscal_code", ""))
            company_email = st.text_input("Email", value=company_info.get("email", ""))
            company_phone = st.text_input("Telefono", value=company_info.get("phone", ""))
            company_website = st.text_input("Sito Web", value=company_info.get("website", ""))
        
        submit_button = st.form_submit_button("Salva Informazioni Azienda")
    
    if submit_button:
        # Update company info
        st.session_state.company_info.update({
            "name": company_name,
            "address": company_address,
            "city": company_city,
            "zip": company_zip,
            "country": company_country,
            "vat_number": company_vat,
            "fiscal_code": company_fiscal,
            "email": company_email,
            "phone": company_phone,
            "website": company_website
        })
        
        st.success("Informazioni azienda salvate con successo!")
    
    # Tax settings
    st.markdown("### Impostazioni IVA")
    
    # Initialize tax settings if not exist
    if "tax_settings" not in st.session_state:
        st.session_state.tax_settings = {
            "default_rate": 22.0,
            "rates": [
                {"rate": 22.0, "description": "Aliquota ordinaria", "default": True},
                {"rate": 10.0, "description": "Aliquota ridotta", "default": False},
                {"rate": 4.0, "description": "Aliquota super-ridotta", "default": False},
                {"rate": 0.0, "description": "Esente IVA", "default": False}
            ]
        }
    
    tax_settings = st.session_state.tax_settings
    
    # Form for tax settings
    with st.form("tax_settings_form"):
        default_rate = st.selectbox(
            "Aliquota IVA Predefinita",
            options=[rate["rate"] for rate in tax_settings.get("rates", [])],
            index=[rate["rate"] for rate in tax_settings.get("rates", [])].index(tax_settings.get("default_rate", 22.0)) if tax_settings.get("rates") else 0,
            format_func=lambda x: f"{x}% - {next((rate['description'] for rate in tax_settings.get('rates', []) if rate['rate'] == x), '')}"
        )
        
        submit_button = st.form_submit_button("Salva Impostazioni IVA")
    
    if submit_button:
        # Update tax settings
        st.session_state.tax_settings["default_rate"] = default_rate
        
        # Update default flag in rates
        for rate in st.session_state.tax_settings["rates"]:
            rate["default"] = (rate["rate"] == default_rate)
        
        st.success("Impostazioni IVA salvate con successo!")
    
    # Invoice numbering
    st.markdown("### Numerazione Fatture")
    
    # Initialize invoice settings if not exist
    if "invoice_settings" not in st.session_state:
        st.session_state.invoice_settings = {
            "prefix": "INV",
            "next_number": 1,
            "year_in_number": True,
            "reset_yearly": True
        }
    
    invoice_settings = st.session_state.invoice_settings
    
    # Form for invoice settings
    with st.form("invoice_settings_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            prefix = st.text_input("Prefisso Fattura", value=invoice_settings.get("prefix", "INV"))
            next_number = st.number_input("Prossimo Numero", min_value=1, value=invoice_settings.get("next_number", 1))
        
        with col2:
            year_in_number = st.checkbox("Includi Anno nel Numero", value=invoice_settings.get("year_in_number", True))
            reset_yearly = st.checkbox("Resetta Numerazione Ogni Anno", value=invoice_settings.get("reset_yearly", True))
        
        # Preview
        current_year = datetime.now().year
        example_number = f"{prefix}-{current_year if year_in_number else ''}{'' if year_in_number else '-'}{next_number:04d}"
        st.info(f"Esempio numerazione: {example_number}")
        
        submit_button = st.form_submit_button("Salva Impostazioni Fattura")
    
    if submit_button:
        # Update invoice settings
        st.session_state.invoice_settings.update({
            "prefix": prefix,
            "next_number": next_number,
            "year_in_number": year_in_number,
            "reset_yearly": reset_yearly
        })
        
        st.success("Impostazioni fattura salvate con successo!")
    
    # Logo upload
    st.markdown("### Logo Aziendale")
    
    uploaded_file = st.file_uploader("Carica Logo", type=["png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        # Save the file
        with open("data/logo.png", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success("Logo caricato con successo!")
        
        # Display the logo
        st.image(uploaded_file, width=200)
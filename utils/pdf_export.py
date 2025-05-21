from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.platypus.flowables import KeepTogether
from io import BytesIO
from datetime import datetime
import os

def create_logo():
    """Crea un'immagine di logo semplice se non esiste"""
    logo_path = "data/logo.png"
    
    # Controlliamo se esiste già il logo
    if os.path.exists(logo_path):
        return logo_path
    
    # Altrimenti, torniamo None (verrà usato solo testo)
    return None

def create_invoice_pdf(invoice_data, booking_data, property_data):
    """
    Crea un PDF per una fattura
    
    Args:
        invoice_data: Dati della fattura
        booking_data: Dati della prenotazione
        property_data: Dati dell'immobile
        
    Returns:
        BytesIO: PDF come oggetto BytesIO
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           rightMargin=20*mm, leftMargin=20*mm,
                           topMargin=20*mm, bottomMargin=20*mm)
    
    # Contenuto del documento
    content = []
    
    # Stili
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=1))
    styles.add(ParagraphStyle(name='Center', alignment=1))
    styles.add(ParagraphStyle(name='Right', alignment=2))
    styles.add(ParagraphStyle(name='LeftIndent', leftIndent=20))
    
    # Logo
    logo_path = create_logo()
    if logo_path:
        try:
            content.append(Image(logo_path, width=5*cm, height=2*cm))
        except:
            # Se c'è un errore con l'immagine, usiamo solo il testo
            content.append(Paragraph("<b>CiaoHost</b>", styles['Title']))
    else:
        content.append(Paragraph("<b>CiaoHost</b>", styles['Title']))
    
    content.append(Spacer(1, 12))
    
    # Intestazione fattura
    content.append(Paragraph(f"<b>FATTURA N. {invoice_data.get('invoice_number')}</b>", styles['Title']))
    content.append(Paragraph(f"Data: {invoice_data.get('date')}", styles['Normal']))
    content.append(Spacer(1, 12))
    
    # Informazioni cliente
    content.append(Paragraph("<b>Cliente:</b>", styles['Heading3']))
    content.append(Paragraph(f"Nome: {booking_data.get('guest_name')}", styles['LeftIndent']))
    if booking_data.get('guest_email'):
        content.append(Paragraph(f"Email: {booking_data.get('guest_email')}", styles['LeftIndent']))
    if booking_data.get('guest_phone'):
        content.append(Paragraph(f"Telefono: {booking_data.get('guest_phone')}", styles['LeftIndent']))
    content.append(Spacer(1, 12))
    
    # Informazioni prenotazione
    content.append(Paragraph("<b>Dettagli Prenotazione:</b>", styles['Heading3']))
    content.append(Paragraph(f"Immobile: {property_data.get('name')}", styles['LeftIndent']))
    content.append(Paragraph(f"Indirizzo: {property_data.get('address')}, {property_data.get('city')}", styles['LeftIndent']))
    content.append(Paragraph(f"Check-in: {booking_data.get('checkin_date')}", styles['LeftIndent']))
    content.append(Paragraph(f"Check-out: {booking_data.get('checkout_date')}", styles['LeftIndent']))
    content.append(Paragraph(f"Ospiti: {booking_data.get('guests')}", styles['LeftIndent']))
    content.append(Spacer(1, 12))
    
    # Tabella dettagli fattura
    data = [
        ["Descrizione", "Quantità", "Prezzo Unitario", "Totale"],
        [f"Soggiorno - {property_data.get('name')}", 
         f"{booking_data.get('nights')} notti", 
         f"€{booking_data.get('price_per_night'):.2f}", 
         f"€{booking_data.get('price_per_night') * booking_data.get('nights'):.2f}"],
        ["Pulizie", "1", f"€{booking_data.get('cleaning_fee'):.2f}", f"€{booking_data.get('cleaning_fee'):.2f}"]
    ]
    
    # Calcola l'imponibile e l'IVA
    imponibile = invoice_data.get('amount') - invoice_data.get('tax_amount')
    
    table = Table(data, colWidths=[doc.width*0.4, doc.width*0.2, doc.width*0.2, doc.width*0.2])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    
    content.append(table)
    content.append(Spacer(1, 12))
    
    # Riepilogo totali
    summary_data = [
        ["Imponibile:", f"€{imponibile:.2f}"],
        [f"IVA ({invoice_data.get('tax_percentage')}%):", f"€{invoice_data.get('tax_amount'):.2f}"],
        ["Totale:", f"€{invoice_data.get('amount'):.2f}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[doc.width*0.7, doc.width*0.3])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),
    ]))
    
    content.append(summary_table)
    content.append(Spacer(1, 12))
    
    # Modalità di pagamento
    content.append(Paragraph("<b>Modalità di Pagamento:</b>", styles['Heading4']))
    content.append(Paragraph(f"{booking_data.get('payment_method', 'Non specificato')}", styles['Normal']))
    content.append(Paragraph(f"Stato pagamento: {invoice_data.get('status')}", styles['Normal']))
    if invoice_data.get('payment_date'):
        content.append(Paragraph(f"Data pagamento: {invoice_data.get('payment_date')}", styles['Normal']))
    content.append(Spacer(1, 24))
    
    # Note
    if invoice_data.get('notes'):
        content.append(Paragraph("<b>Note:</b>", styles['Heading4']))
        content.append(Paragraph(invoice_data.get('notes'), styles['Normal']))
        content.append(Spacer(1, 12))
    
    # Piè di pagina
    content.append(Paragraph("Documento generato automaticamente da CiaoHost. Questo documento non ha valore fiscale se non accompagnato da regolare fattura.", styles['Italic']))
    
    # Assembla il documento
    doc.build(content)
    buffer.seek(0)
    return buffer

def create_booking_confirmation_pdf(booking_data, property_data):
    """
    Crea un PDF di conferma prenotazione
    
    Args:
        booking_data: Dati della prenotazione
        property_data: Dati dell'immobile
        
    Returns:
        BytesIO: PDF come oggetto BytesIO
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=20*mm, leftMargin=20*mm,
                          topMargin=20*mm, bottomMargin=20*mm)
    
    # Contenuto del documento
    content = []
    
    # Stili
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=1))
    styles.add(ParagraphStyle(name='Center', alignment=1))
    styles.add(ParagraphStyle(name='LeftIndent', leftIndent=20))
    
    # Logo
    logo_path = create_logo()
    if logo_path:
        try:
            content.append(Image(logo_path, width=5*cm, height=2*cm))
        except:
            content.append(Paragraph("<b>CiaoHost</b>", styles['Title']))
    else:
        content.append(Paragraph("<b>CiaoHost</b>", styles['Title']))
    
    content.append(Spacer(1, 12))
    
    # Intestazione conferma
    content.append(Paragraph("<b>CONFERMA PRENOTAZIONE</b>", styles['Title']))
    content.append(Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    content.append(Spacer(1, 12))
    
    # Informazioni cliente
    content.append(Paragraph("<b>Gentile Cliente:</b>", styles['Heading3']))
    content.append(Paragraph(f"{booking_data.get('guest_name')}", styles['LeftIndent']))
    if booking_data.get('guest_email'):
        content.append(Paragraph(f"Email: {booking_data.get('guest_email')}", styles['LeftIndent']))
    if booking_data.get('guest_phone'):
        content.append(Paragraph(f"Telefono: {booking_data.get('guest_phone')}", styles['LeftIndent']))
    content.append(Spacer(1, 12))
    
    # Informazioni prenotazione
    content.append(Paragraph("<b>La tua prenotazione è confermata!</b>", styles['Heading3']))
    content.append(Paragraph("Di seguito trovi i dettagli della tua prenotazione:", styles['Normal']))
    content.append(Spacer(1, 6))
    
    # Dettagli prenotazione
    details_data = [
        ["Immobile:", property_data.get('name')],
        ["Indirizzo:", f"{property_data.get('address')}, {property_data.get('city')}"],
        ["Check-in:", booking_data.get('checkin_date')],
        ["Check-out:", booking_data.get('checkout_date')],
        ["Notti:", str(booking_data.get('nights', 0))],
        ["Ospiti:", str(booking_data.get('guests', 1))],
        ["Prezzo totale:", f"€{booking_data.get('total_price'):.2f}"]
    ]
    
    details_table = Table(details_data, colWidths=[doc.width*0.3, doc.width*0.7])
    details_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    content.append(details_table)
    content.append(Spacer(1, 12))
    
    # Istruzioni per il check-in
    content.append(Paragraph("<b>Istruzioni per il Check-in:</b>", styles['Heading4']))
    if property_data.get('check_in_instructions'):
        content.append(Paragraph(property_data.get('check_in_instructions'), styles['Normal']))
    else:
        content.append(Paragraph("Il check-in è disponibile dalle 15:00. Ti contatteremo prima del tuo arrivo per organizzare la consegna delle chiavi.", styles['Normal']))
    content.append(Spacer(1, 12))
    
    # Servizi inclusi
    content.append(Paragraph("<b>Servizi Inclusi:</b>", styles['Heading4']))
    amenities = property_data.get('amenities', [])
    if amenities:
        amenities_text = ", ".join(amenities)
        content.append(Paragraph(amenities_text, styles['Normal']))
    else:
        content.append(Paragraph("Informazioni sui servizi non disponibili.", styles['Normal']))
    content.append(Spacer(1, 12))
    
    # Dettagli di pagamento
    content.append(Paragraph("<b>Dettagli di Pagamento:</b>", styles['Heading4']))
    content.append(Paragraph(f"Metodo di pagamento: {booking_data.get('payment_method', 'Non specificato')}", styles['Normal']))
    content.append(Paragraph(f"Stato pagamento: {booking_data.get('payment_status', 'In attesa')}", styles['Normal']))
    content.append(Spacer(1, 12))
    
    # Note
    if booking_data.get('notes'):
        content.append(Paragraph("<b>Note:</b>", styles['Heading4']))
        content.append(Paragraph(booking_data.get('notes'), styles['Normal']))
        content.append(Spacer(1, 12))
    
    # Contatti
    content.append(Paragraph("<b>Contatti:</b>", styles['Heading4']))
    content.append(Paragraph("Per qualsiasi domanda o necessità, non esitare a contattarci:", styles['Normal']))
    content.append(Paragraph("Email: info@ciaohost.com", styles['Normal']))
    content.append(Paragraph("Telefono: +39 123 456 789", styles['Normal']))
    content.append(Spacer(1, 24))
    
    # Piè di pagina
    content.append(Paragraph("Grazie per aver scelto CiaoHost per il tuo soggiorno!", styles['Italic']))
    
    # Assembla il documento
    doc.build(content)
    buffer.seek(0)
    return buffer

def create_property_report_pdf(property_data, bookings_data=None, period=None):
    """
    Crea un report PDF per una proprietà
    
    Args:
        property_data: Dati dell'immobile
        bookings_data: Lista di prenotazioni per questa proprietà
        period: Dizionario con 'start_date' e 'end_date' per filtrare le prenotazioni
        
    Returns:
        BytesIO: PDF come oggetto BytesIO
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=20*mm, leftMargin=20*mm,
                          topMargin=20*mm, bottomMargin=20*mm)
    
    # Contenuto del documento
    content = []
    
    # Stili
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=1))
    styles.add(ParagraphStyle(name='Center', alignment=1))
    styles.add(ParagraphStyle(name='LeftIndent', leftIndent=20))
    
    # Logo
    logo_path = create_logo()
    if logo_path:
        try:
            content.append(Image(logo_path, width=5*cm, height=2*cm))
        except:
            content.append(Paragraph("<b>CiaoHost</b>", styles['Title']))
    else:
        content.append(Paragraph("<b>CiaoHost</b>", styles['Title']))
    
    content.append(Spacer(1, 12))
    
    # Intestazione report
    content.append(Paragraph(f"<b>REPORT IMMOBILE: {property_data.get('name')}</b>", styles['Title']))
    
    # Periodo del report
    if period:
        content.append(Paragraph(f"Periodo: dal {period.get('start_date')} al {period.get('end_date')}", styles['Normal']))
    
    content.append(Paragraph(f"Data report: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    content.append(Spacer(1, 12))
    
    # Informazioni immobile
    content.append(Paragraph("<b>Dettagli Immobile:</b>", styles['Heading3']))
    
    property_details = [
        ["Tipo:", property_data.get('type', 'Non specificato')],
        ["Indirizzo:", f"{property_data.get('address')}, {property_data.get('city')}"],
        ["Camere:", str(property_data.get('bedrooms', 0))],
        ["Bagni:", str(property_data.get('bathrooms', 0))],
        ["Ospiti Max:", str(property_data.get('max_guests', 0))],
        ["Prezzo Base:", f"€{property_data.get('base_price', 0):.2f}"],
        ["Prezzo Attuale:", f"€{property_data.get('current_price', 0):.2f}"],
        ["Costo Pulizie:", f"€{property_data.get('cleaning_fee', 0):.2f}"],
        ["Stato:", property_data.get('status', 'Attivo')]
    ]
    
    property_table = Table(property_details, colWidths=[doc.width*0.3, doc.width*0.7])
    property_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    content.append(property_table)
    content.append(Spacer(1, 12))
    
    # Servizi
    content.append(Paragraph("<b>Servizi:</b>", styles['Heading4']))
    amenities = property_data.get('amenities', [])
    if amenities:
        amenities_text = ", ".join(amenities)
        content.append(Paragraph(amenities_text, styles['Normal']))
    else:
        content.append(Paragraph("Nessun servizio specificato.", styles['Normal']))
    content.append(Spacer(1, 12))
    
    # Prenotazioni
    if bookings_data:
        content.append(Paragraph("<b>Prenotazioni:</b>", styles['Heading3']))
        
        # Filtriamo le prenotazioni se è specificato un periodo
        filtered_bookings = bookings_data
        if period and period.get('start_date') and period.get('end_date'):
            start_date = datetime.strptime(period.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(period.get('end_date'), '%Y-%m-%d').date()
            filtered_bookings = [
                b for b in bookings_data 
                if (datetime.strptime(b.get('checkin_date'), '%Y-%m-%d').date() <= end_date and
                    datetime.strptime(b.get('checkout_date'), '%Y-%m-%d').date() >= start_date)
            ]
        
        if filtered_bookings:
            # Intestazione tabella prenotazioni
            bookings_table_data = [
                ["Check-in", "Check-out", "Ospite", "Stato", "Totale"]
            ]
            
            # Dati prenotazioni
            for booking in filtered_bookings:
                bookings_table_data.append([
                    booking.get('checkin_date'),
                    booking.get('checkout_date'),
                    booking.get('guest_name'),
                    booking.get('status'),
                    f"€{booking.get('total_price', 0):.2f}"
                ])
            
            # Creazione tabella
            bookings_table = Table(bookings_table_data, colWidths=[doc.width*0.2, doc.width*0.2, doc.width*0.25, doc.width*0.15, doc.width*0.2])
            bookings_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
            ]))
            
            content.append(bookings_table)
            
            # Statistiche prenotazioni
            total_revenue = sum(b.get('total_price', 0) for b in filtered_bookings)
            completed_bookings = len([b for b in filtered_bookings if b.get('status') == 'completata'])
            active_bookings = len([b for b in filtered_bookings if b.get('status') == 'attiva'])
            confirmed_bookings = len([b for b in filtered_bookings if b.get('status') == 'confermata'])
            
            content.append(Spacer(1, 12))
            content.append(Paragraph("<b>Statistiche Prenotazioni:</b>", styles['Heading4']))
            content.append(Paragraph(f"Prenotazioni Totali: {len(filtered_bookings)}", styles['Normal']))
            content.append(Paragraph(f"Prenotazioni Completate: {completed_bookings}", styles['Normal']))
            content.append(Paragraph(f"Prenotazioni Attive: {active_bookings}", styles['Normal']))
            content.append(Paragraph(f"Prenotazioni Confermate: {confirmed_bookings}", styles['Normal']))
            content.append(Paragraph(f"Ricavi Totali: €{total_revenue:.2f}", styles['Normal']))
        else:
            content.append(Paragraph("Nessuna prenotazione nel periodo selezionato.", styles['Normal']))
    else:
        content.append(Paragraph("<b>Prenotazioni:</b>", styles['Heading3']))
        content.append(Paragraph("Nessuna prenotazione disponibile.", styles['Normal']))
    
    content.append(Spacer(1, 24))
    
    # Piè di pagina
    content.append(Paragraph("Report generato automaticamente da CiaoHost.", styles['Italic']))
    
    # Assembla il documento
    doc.build(content)
    buffer.seek(0)
    return buffer

def create_financial_report_pdf(bookings_data, period=None, properties_data=None):
    """
    Crea un report finanziario in PDF
    
    Args:
        bookings_data: Lista di prenotazioni
        period: Dizionario con 'start_date' e 'end_date' per filtrare le prenotazioni
        properties_data: Lista di dati delle proprietà per riferimento
        
    Returns:
        BytesIO: PDF come oggetto BytesIO
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=20*mm, leftMargin=20*mm,
                          topMargin=20*mm, bottomMargin=20*mm)
    
    # Contenuto del documento
    content = []
    
    # Stili
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=1))
    styles.add(ParagraphStyle(name='Center', alignment=1))
    styles.add(ParagraphStyle(name='LeftIndent', leftIndent=20))
    
    # Logo
    logo_path = create_logo()
    if logo_path:
        try:
            content.append(Image(logo_path, width=5*cm, height=2*cm))
        except:
            content.append(Paragraph("<b>CiaoHost</b>", styles['Title']))
    else:
        content.append(Paragraph("<b>CiaoHost</b>", styles['Title']))
    
    content.append(Spacer(1, 12))
    
    # Intestazione report
    content.append(Paragraph("<b>REPORT FINANZIARIO</b>", styles['Title']))
    
    # Periodo del report
    if period:
        content.append(Paragraph(f"Periodo: dal {period.get('start_date')} al {period.get('end_date')}", styles['Normal']))
    
    content.append(Paragraph(f"Data report: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    content.append(Spacer(1, 12))
    
    # Filtriamo le prenotazioni se è specificato un periodo
    filtered_bookings = bookings_data
    if period and period.get('start_date') and period.get('end_date'):
        start_date = datetime.strptime(period.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(period.get('end_date'), '%Y-%m-%d').date()
        filtered_bookings = [
            b for b in bookings_data 
            if (datetime.strptime(b.get('checkin_date'), '%Y-%m-%d').date() <= end_date and
                datetime.strptime(b.get('checkout_date'), '%Y-%m-%d').date() >= start_date)
        ]
    
    # Riepilogo finanziario
    total_revenue = sum(b.get('total_price', 0) for b in filtered_bookings)
    total_cleaning_fees = sum(b.get('cleaning_fee', 0) for b in filtered_bookings)
    total_bookings = len(filtered_bookings)
    
    # Calcola il ricavo netto (ricavo - tasse e commissioni stimate)
    commission_rate = 0.10  # 10% commissione
    commissions = total_revenue * commission_rate
    tax_rate = 0.22  # 22% IVA
    tax_amount = total_revenue / (1 + tax_rate) * tax_rate
    net_revenue = total_revenue - commissions - tax_amount
    
    content.append(Paragraph("<b>Riepilogo Finanziario:</b>", styles['Heading3']))
    
    financial_data = [
        ["Prenotazioni Totali:", str(total_bookings)],
        ["Ricavo Lordo:", f"€{total_revenue:.2f}"],
        ["Commissioni (10%):", f"€{commissions:.2f}"],
        ["IVA (22%):", f"€{tax_amount:.2f}"],
        ["Ricavo Netto:", f"€{net_revenue:.2f}"]
    ]
    
    financial_table = Table(financial_data, colWidths=[doc.width*0.7, doc.width*0.3])
    financial_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),
    ]))
    
    content.append(financial_table)
    content.append(Spacer(1, 12))
    
    # Dettaglio prenotazioni per immobile
    if properties_data:
        content.append(Paragraph("<b>Dettaglio per Immobile:</b>", styles['Heading3']))
        
        # Raggruppa prenotazioni per immobile
        bookings_by_property = {}
        property_dict = {p.get('id'): p for p in properties_data}
        
        for booking in filtered_bookings:
            property_id = booking.get('property_id')
            if property_id not in bookings_by_property:
                bookings_by_property[property_id] = []
            bookings_by_property[property_id].append(booking)
        
        # Crea tabella con ricavi per immobile
        property_revenue_data = [
            ["Immobile", "Prenotazioni", "Ricavo", "Occupazione"]
        ]
        
        for property_id, prop_bookings in bookings_by_property.items():
            property_name = property_dict.get(property_id, {}).get('name', 'Sconosciuto')
            property_revenue = sum(b.get('total_price', 0) for b in prop_bookings)
            property_bookings = len(prop_bookings)
            
            # Calcolo occupazione (giorni occupati / giorni totali nel periodo)
            # Semplificazione: contiamo i giorni di ogni prenotazione nel periodo
            occupied_days = 0
            if period:
                start_date = datetime.strptime(period.get('start_date'), '%Y-%m-%d').date()
                end_date = datetime.strptime(period.get('end_date'), '%Y-%m-%d').date()
                total_days = (end_date - start_date).days + 1
                
                for booking in prop_bookings:
                    booking_start = max(start_date, datetime.strptime(booking.get('checkin_date'), '%Y-%m-%d').date())
                    booking_end = min(end_date, datetime.strptime(booking.get('checkout_date'), '%Y-%m-%d').date())
                    booking_days = (booking_end - booking_start).days + 1
                    occupied_days += max(0, booking_days)
                
                occupancy_rate = f"{(occupied_days / total_days * 100):.1f}%"
            else:
                occupancy_rate = "N/A"
            
            property_revenue_data.append([
                property_name,
                str(property_bookings),
                f"€{property_revenue:.2f}",
                occupancy_rate
            ])
        
        property_revenue_table = Table(property_revenue_data, colWidths=[doc.width*0.4, doc.width*0.2, doc.width*0.2, doc.width*0.2])
        property_revenue_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ]))
        
        content.append(property_revenue_table)
        content.append(Spacer(1, 12))
    
    # Lista delle prenotazioni
    content.append(Paragraph("<b>Dettaglio Prenotazioni:</b>", styles['Heading3']))
    
    if filtered_bookings:
        bookings_table_data = [
            ["Data", "Immobile", "Ospite", "Stato", "Totale"]
        ]
        
        # Ottieni il nome dell'immobile dalla lista di proprietà
        property_dict = {}
        if properties_data:
            property_dict = {p.get('id'): p.get('name') for p in properties_data}
        
        # Ordina le prenotazioni per data di check-in
        sorted_bookings = sorted(filtered_bookings, key=lambda b: b.get('checkin_date', ''))
        
        for booking in sorted_bookings:
            property_id = booking.get('property_id')
            property_name = property_dict.get(property_id, 'Sconosciuto')
            
            bookings_table_data.append([
                booking.get('checkin_date'),
                property_name,
                booking.get('guest_name'),
                booking.get('status'),
                f"€{booking.get('total_price', 0):.2f}"
            ])
        
        bookings_table = Table(bookings_table_data, colWidths=[doc.width*0.15, doc.width*0.3, doc.width*0.2, doc.width*0.15, doc.width*0.2])
        bookings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
        ]))
        
        content.append(bookings_table)
    else:
        content.append(Paragraph("Nessuna prenotazione nel periodo selezionato.", styles['Normal']))
    
    content.append(Spacer(1, 24))
    
    # Piè di pagina
    content.append(Paragraph("Report generato automaticamente da CiaoHost.", styles['Italic']))
    
    # Assembla il documento
    doc.build(content)
    buffer.seek(0)
    return buffer
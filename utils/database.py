import os
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import uuid
import streamlit as st

# Assicuriamoci che la directory per il database esista
os.makedirs('data', exist_ok=True)

# Creiamo una connessione SQLite per la persistenza dei dati
DATABASE_URL = "sqlite:///data/ciao_host.db"

# Creiamo il motore del database
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Definizione delle tabelle
class Property(Base):
    __tablename__ = 'properties'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    type = Column(String(50))
    city = Column(String(100))
    address = Column(String(255))
    bedrooms = Column(Integer, default=1)
    bathrooms = Column(Float, default=1.0)
    max_guests = Column(Integer, default=2)
    base_price = Column(Float, default=50.0)
    current_price = Column(Float, default=50.0)
    cleaning_fee = Column(Float, default=30.0)
    check_in_instructions = Column(Text)
    wifi_details = Column(Text)
    amenities = Column(Text)  # Stored as JSON string
    status = Column(String(20), default="Attivo")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relazioni
    bookings = relationship("Booking", back_populates="property", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "city": self.city,
            "address": self.address,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "max_guests": self.max_guests,
            "base_price": self.base_price,
            "current_price": self.current_price,
            "cleaning_fee": self.cleaning_fee,
            "check_in_instructions": self.check_in_instructions,
            "wifi_details": self.wifi_details,
            "amenities": json.loads(self.amenities) if self.amenities else [],
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Booking(Base):
    __tablename__ = 'bookings'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = Column(String(36), ForeignKey('properties.id'), nullable=False)
    guest_name = Column(String(100), nullable=False)
    guest_email = Column(String(100))
    guest_phone = Column(String(50))
    checkin_date = Column(Date, nullable=False)
    checkout_date = Column(Date, nullable=False)
    guests = Column(Integer, default=1)
    price_per_night = Column(Float, nullable=False)
    cleaning_fee = Column(Float, default=0)
    total_price = Column(Float, nullable=False)
    payment_method = Column(String(50))
    payment_status = Column(String(20), default="In attesa")
    status = Column(String(20), default="confermata")
    source = Column(String(50), default="Diretta")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    checkin_completed_at = Column(DateTime)
    checkout_completed_at = Column(DateTime)
    
    # Relazioni
    property = relationship("Property", back_populates="bookings")
    invoices = relationship("Invoice", back_populates="booking", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "property_id": self.property_id,
            "guest_name": self.guest_name,
            "guest_email": self.guest_email,
            "guest_phone": self.guest_phone,
            "checkin_date": self.checkin_date.isoformat() if self.checkin_date else None,
            "checkout_date": self.checkout_date.isoformat() if self.checkout_date else None,
            "guests": self.guests,
            "price_per_night": self.price_per_night,
            "cleaning_fee": self.cleaning_fee,
            "total_price": self.total_price,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "status": self.status,
            "source": self.source,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "checkin_completed_at": self.checkin_completed_at.isoformat() if self.checkin_completed_at else None,
            "checkout_completed_at": self.checkout_completed_at.isoformat() if self.checkout_completed_at else None
        }

class Invoice(Base):
    __tablename__ = 'invoices'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String(36), ForeignKey('bookings.id'), nullable=False)
    invoice_number = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0)
    tax_percentage = Column(Float, default=22.0)  # IVA standard italiana
    status = Column(String(20), default="Emessa")  # Emessa, Pagata, Annullata
    payment_date = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relazione
    booking = relationship("Booking", back_populates="invoices")
    
    def to_dict(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "invoice_number": self.invoice_number,
            "date": self.date.isoformat() if self.date else None,
            "amount": self.amount,
            "tax_amount": self.tax_amount,
            "tax_percentage": self.tax_percentage,
            "status": self.status,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class CleaningService(Base):
    __tablename__ = 'cleaning_services'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    phone = Column(String(50))
    email = Column(String(100))
    notes = Column(Text)
    default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "notes": self.notes,
            "default": self.default,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class CleaningTask(Base):
    __tablename__ = 'cleaning_tasks'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = Column(String(36), ForeignKey('properties.id'), nullable=False)
    cleaning_service_id = Column(String(36), ForeignKey('cleaning_services.id'))
    scheduled_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="Programmata")  # Programmata, Completata, Annullata
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)
    booking_id = Column(String(36), ForeignKey('bookings.id'))
    
    def to_dict(self):
        return {
            "id": self.id,
            "property_id": self.property_id,
            "cleaning_service_id": self.cleaning_service_id,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "booking_id": self.booking_id
        }

# Creazione delle tabelle nel database
Base.metadata.create_all(engine)

# Creazione della sessione
Session = sessionmaker(bind=engine)

# Funzioni di utilità per accedere al database
def get_db_session():
    """Ottiene una sessione di database"""
    return Session()

def init_db():
    """Inizializza il database"""
    # Assicuriamoci che la directory 'data' esista
    os.makedirs('data', exist_ok=True)
    
    # Crea le tabelle se non esistono
    Base.metadata.create_all(engine)
    
    # Inizializza con dati demo se non ci sono proprietà
    session = get_db_session()
    property_count = session.query(Property).count()
    
    if property_count == 0:
        # Se non ci sono dati, carichiamo da file esistenti o creiamo dati demo
        if os.path.exists('data/properties.json'):
            try:
                with open('data/properties.json', 'r', encoding='utf-8') as f:
                    properties_data = json.load(f)
                    
                    for prop_data in properties_data:
                        # Convertiamo amenities in JSON string
                        if 'amenities' in prop_data and isinstance(prop_data['amenities'], list):
                            prop_data['amenities'] = json.dumps(prop_data['amenities'])
                            
                        # Gestiamo le date
                        for date_field in ['created_at', 'updated_at']:
                            if date_field in prop_data and prop_data[date_field]:
                                try:
                                    prop_data[date_field] = datetime.fromisoformat(prop_data[date_field])
                                except (ValueError, TypeError):
                                    prop_data[date_field] = datetime.now()
                        
                        # Creiamo l'oggetto Property
                        prop = Property(**prop_data)
                        session.add(prop)
            except Exception as e:
                print(f"Errore nel caricamento delle proprietà: {str(e)}")
        
        if os.path.exists('data/bookings.json'):
            try:
                with open('data/bookings.json', 'r', encoding='utf-8') as f:
                    bookings_data = json.load(f)
                    
                    for booking_data in bookings_data:
                        # Gestiamo le date
                        for date_field in ['checkin_date', 'checkout_date']:
                            if date_field in booking_data and booking_data[date_field]:
                                try:
                                    # Convertiamo la stringa in oggetto date
                                    if isinstance(booking_data[date_field], str):
                                        booking_data[date_field] = datetime.fromisoformat(booking_data[date_field]).date()
                                except (ValueError, TypeError):
                                    if date_field == 'checkin_date':
                                        booking_data[date_field] = datetime.now().date()
                                    else:
                                        booking_data[date_field] = (datetime.now() + timedelta(days=3)).date()
                        
                        for datetime_field in ['created_at', 'updated_at', 'checkin_completed_at', 'checkout_completed_at']:
                            if datetime_field in booking_data and booking_data[datetime_field]:
                                try:
                                    booking_data[datetime_field] = datetime.fromisoformat(booking_data[datetime_field])
                                except (ValueError, TypeError):
                                    if datetime_field in ['created_at', 'updated_at']:
                                        booking_data[datetime_field] = datetime.now()
                                    else:
                                        booking_data[datetime_field] = None
                        
                        # Creiamo l'oggetto Booking
                        booking = Booking(**booking_data)
                        session.add(booking)
            except Exception as e:
                print(f"Errore nel caricamento delle prenotazioni: {str(e)}")
        
        # Aggiungiamo un servizio di pulizia predefinito
        default_cleaning = CleaningService(
            name="Pulizie Rapide Srl",
            phone="+39 123 456 7890",
            email="info@pulizierapide.it",
            notes="Servizio di pulizia predefinito",
            default=True
        )
        session.add(default_cleaning)
        
        session.commit()
    
    session.close()

def get_all_properties():
    """Recupera tutte le proprietà dal database"""
    session = get_db_session()
    properties = session.query(Property).all()
    result = [prop.to_dict() for prop in properties]
    session.close()
    return result

def get_property(property_id):
    """Recupera una proprietà specifica dal database"""
    session = get_db_session()
    property = session.query(Property).filter(Property.id == property_id).first()
    result = property.to_dict() if property else None
    session.close()
    return result

def add_property(property_data):
    """Aggiunge una nuova proprietà al database"""
    session = get_db_session()
    
    # Gestiamo gli amenities
    if 'amenities' in property_data and isinstance(property_data['amenities'], list):
        property_data['amenities'] = json.dumps(property_data['amenities'])
    
    # Creiamo la nuova proprietà
    new_property = Property(**property_data)
    session.add(new_property)
    session.commit()
    result = new_property.to_dict()
    session.close()
    return result

def update_property(property_id, property_data):
    """Aggiorna una proprietà esistente"""
    session = get_db_session()
    property = session.query(Property).filter(Property.id == property_id).first()
    
    if not property:
        session.close()
        return None
    
    # Gestiamo gli amenities
    if 'amenities' in property_data and isinstance(property_data['amenities'], list):
        property_data['amenities'] = json.dumps(property_data['amenities'])
    
    # Aggiorniamo i campi
    for key, value in property_data.items():
        if hasattr(property, key):
            setattr(property, key, value)
    
    property.updated_at = datetime.now()
    session.commit()
    result = property.to_dict()
    session.close()
    return result

def delete_property(property_id):
    """Elimina una proprietà"""
    session = get_db_session()
    property = session.query(Property).filter(Property.id == property_id).first()
    
    if not property:
        session.close()
        return False
    
    session.delete(property)
    session.commit()
    session.close()
    return True

def get_all_bookings():
    """Recupera tutte le prenotazioni dal database"""
    session = get_db_session()
    bookings = session.query(Booking).all()
    result = [booking.to_dict() for booking in bookings]
    session.close()
    return result

def get_booking(booking_id):
    """Recupera una prenotazione specifica dal database"""
    session = get_db_session()
    booking = session.query(Booking).filter(Booking.id == booking_id).first()
    result = booking.to_dict() if booking else None
    session.close()
    return result

def add_booking(booking_data):
    """Aggiunge una nuova prenotazione al database"""
    session = get_db_session()
    
    # Gestiamo le date
    for date_field in ['checkin_date', 'checkout_date']:
        if date_field in booking_data and booking_data[date_field]:
            if isinstance(booking_data[date_field], str):
                booking_data[date_field] = datetime.fromisoformat(booking_data[date_field]).date()
    
    # Creiamo la nuova prenotazione
    new_booking = Booking(**booking_data)
    session.add(new_booking)
    session.commit()
    
    # Generiamo automaticamente la fattura
    create_invoice_for_booking(new_booking.id)
    
    result = new_booking.to_dict()
    session.close()
    return result

def update_booking(booking_id, booking_data):
    """Aggiorna una prenotazione esistente"""
    session = get_db_session()
    booking = session.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        session.close()
        return None
    
    # Gestiamo le date
    for date_field in ['checkin_date', 'checkout_date']:
        if date_field in booking_data and booking_data[date_field]:
            if isinstance(booking_data[date_field], str):
                booking_data[date_field] = datetime.fromisoformat(booking_data[date_field]).date()
    
    # Gestiamo i campi datetime
    for datetime_field in ['checkin_completed_at', 'checkout_completed_at']:
        if datetime_field in booking_data:
            if booking_data[datetime_field] and isinstance(booking_data[datetime_field], str):
                booking_data[datetime_field] = datetime.fromisoformat(booking_data[datetime_field])
    
    # Aggiorniamo i campi
    for key, value in booking_data.items():
        if hasattr(booking, key):
            setattr(booking, key, value)
    
    booking.updated_at = datetime.now()
    session.commit()
    result = booking.to_dict()
    session.close()
    return result

def delete_booking(booking_id):
    """Elimina una prenotazione"""
    session = get_db_session()
    booking = session.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        session.close()
        return False
    
    session.delete(booking)
    session.commit()
    session.close()
    return True

def create_invoice_for_booking(booking_id):
    """Crea una fattura per una prenotazione"""
    session = get_db_session()
    booking = session.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        session.close()
        return None
    
    # Controlliamo se esiste già una fattura per questa prenotazione
    existing_invoice = session.query(Invoice).filter(Invoice.booking_id == booking_id).first()
    if existing_invoice:
        result = existing_invoice.to_dict()
        session.close()
        return result
    
    # Otteniamo il prossimo numero di fattura
    invoice_count = session.query(Invoice).count()
    invoice_number = f"INV-{datetime.now().year}-{invoice_count + 1:04d}"
    
    # Calcoliamo l'importo IVA
    tax_percentage = 22.0  # IVA standard italiana
    amount_without_tax = booking.total_price / (1 + tax_percentage/100)
    tax_amount = booking.total_price - amount_without_tax
    
    # Creiamo la nuova fattura
    new_invoice = Invoice(
        booking_id=booking_id,
        invoice_number=invoice_number,
        date=datetime.now().date(),
        amount=booking.total_price,
        tax_amount=tax_amount,
        tax_percentage=tax_percentage,
        status="Emessa" if booking.payment_status == "Pagato" else "In attesa",
        payment_date=datetime.now().date() if booking.payment_status == "Pagato" else None,
        notes=f"Fattura per prenotazione {booking.guest_name} dal {booking.checkin_date} al {booking.checkout_date}"
    )
    
    session.add(new_invoice)
    session.commit()
    result = new_invoice.to_dict()
    session.close()
    return result

def get_all_invoices():
    """Recupera tutte le fatture dal database"""
    session = get_db_session()
    invoices = session.query(Invoice).all()
    result = [invoice.to_dict() for invoice in invoices]
    session.close()
    return result

def get_invoice(invoice_id):
    """Recupera una fattura specifica dal database"""
    session = get_db_session()
    invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
    result = invoice.to_dict() if invoice else None
    session.close()
    return result

def add_cleaning_service(service_data):
    """Aggiunge un nuovo servizio di pulizia"""
    session = get_db_session()
    
    # Se impostato come predefinito, rimuoviamo il flag predefinito dagli altri servizi
    if service_data.get('default', False):
        default_services = session.query(CleaningService).filter(CleaningService.default == True).all()
        for service in default_services:
            service.default = False
    
    # Creiamo il nuovo servizio
    new_service = CleaningService(**service_data)
    session.add(new_service)
    session.commit()
    result = new_service.to_dict()
    session.close()
    return result

def get_all_cleaning_services():
    """Recupera tutti i servizi di pulizia"""
    session = get_db_session()
    services = session.query(CleaningService).all()
    result = [service.to_dict() for service in services]
    session.close()
    return result

def get_default_cleaning_service():
    """Recupera il servizio di pulizia predefinito"""
    session = get_db_session()
    service = session.query(CleaningService).filter(CleaningService.default == True).first()
    result = service.to_dict() if service else None
    session.close()
    return result

def schedule_cleaning(property_id, scheduled_date, booking_id=None, service_id=None):
    """Programma una pulizia per una proprietà"""
    session = get_db_session()
    
    # Se non è specificato un servizio, usiamo quello predefinito
    if not service_id:
        default_service = session.query(CleaningService).filter(CleaningService.default == True).first()
        if default_service:
            service_id = default_service.id
    
    # Creiamo il task di pulizia
    new_task = CleaningTask(
        property_id=property_id,
        cleaning_service_id=service_id,
        scheduled_date=scheduled_date,
        status="Programmata",
        booking_id=booking_id,
        notes="Pulizia programmata automaticamente dopo check-out" if booking_id else "Pulizia programmata manualmente"
    )
    
    session.add(new_task)
    session.commit()
    result = new_task.to_dict()
    session.close()
    return result

def get_all_cleaning_tasks():
    """Recupera tutti i task di pulizia"""
    session = get_db_session()
    tasks = session.query(CleaningTask).all()
    result = [task.to_dict() for task in tasks]
    session.close()
    return result

def get_upcoming_cleaning_tasks(days=7):
    """Recupera i task di pulizia per i prossimi giorni"""
    session = get_db_session()
    end_date = datetime.now() + timedelta(days=days)
    tasks = session.query(CleaningTask).filter(
        CleaningTask.scheduled_date >= datetime.now(),
        CleaningTask.scheduled_date <= end_date,
        CleaningTask.status == "Programmata"
    ).all()
    result = [task.to_dict() for task in tasks]
    session.close()
    return result

# Inizializza il database all'avvio dell'app
def initialize_session_state_from_db():
    """Inizializza lo stato della sessione dal database"""
    if 'db_initialized' not in st.session_state or not st.session_state.db_initialized:
        # Inizializziamo il database
        init_db()
        
        # Carichiamo i dati dal database nello stato della sessione
        st.session_state.properties = get_all_properties()
        st.session_state.bookings = get_all_bookings()
        st.session_state.db_initialized = True
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
from PIL import Image, ImageTk
import webbrowser

# Configurazione ambiente e API (NON MODIFICARE)
load_dotenv()
genai.configure(api_key="AIzaSyB-Lgs26JGbdxdJFVk1-1JQFd2lUfyFXwM")
model = genai.GenerativeModel('gemini-2.0-flash')

# Contesto specializzato per immobili
CONTESTO_IMMOBILIARE = """
Sei un esperto di gestione immobiliare dell' azienda chiamata CiaoHost con queste capacità:
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

# Stili avanzati
COLORS = {
    "primary": "#4F46E5",       # Viola
    "secondary": "#10B981",     # Verde
    "dark": "#1F2937",          # Grigio scuro
    "light": "#F9FAFB",         # Grigio chiaro
    "text": "#374151"           # Testo
}

FONTS = {
    "title": ("Segoe UI", 18, "bold"),
    "body": ("Segoe UI", 11),
    "button": ("Segoe UI", 10, "bold")
}

class RealEstateChatbot:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.create_widgets()
        self.chat_history = []
        self.user_states = {}
        self.load_database()

    def setup_window(self):
        self.root.title("CiaoHost AI Manager")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        self.root.configure(bg=COLORS["light"])
        
        # Icona e tema
        try:
            self.root.iconbitmap("home_icon.ico")
        except:
            pass
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=COLORS["light"])
        style.configure('TButton', font=FONTS["button"], borderwidth=0)
        style.map('TButton',
                background=[('active', COLORS["primary"]), ('!active', COLORS["primary"])],
                foreground=[('active', 'white'), ('!active', 'white')])

    def create_widgets(self):
        # Header con logo
        header = ttk.Frame(self.root, style='TFrame')
        header.pack(fill='x', padx=20, pady=10)
        
        self.logo_label = ttk.Label(header, 
                                  text="🏡 CiaoHost AI Assistant", 
                                  font=FONTS["title"], 
                                  foreground=COLORS["primary"],
                                  background=COLORS["light"])
        self.logo_label.pack(side='left')
        
        # Pulsante assistenza
        help_btn = ttk.Button(header, 
                            text="ℹ️ Assistenza", 
                            command=self.show_help,
                            style='TButton')
        help_btn.pack(side='right')
        
        # Area chat con scrollbar personalizzata
        chat_frame = ttk.Frame(self.root)
        chat_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.chat_area = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=FONTS["body"],
            bg='white',
            padx=15,
            pady=15,
            relief='flat',
            highlightthickness=0
        )
        self.chat_area.pack(fill='both', expand=True)
        
        # Configurazione tag per messaggi
        self.chat_area.tag_config('user', 
                                foreground=COLORS["dark"], 
                                font=("Segoe UI", 10, "bold"),
                                lmargin1=50,
                                lmargin2=50,
                                rmargin=50)
        
        self.chat_area.tag_config('bot', 
                                foreground=COLORS["text"], 
                                font=FONTS["body"],
                                lmargin1=20,
                                lmargin2=20,
                                rmargin=50)
        
        self.chat_area.tag_config('admin', 
                                foreground=COLORS["secondary"], 
                                font=("Segoe UI", 10, "bold"))
        
        # Input area con effetti
        input_frame = ttk.Frame(self.root, style='TFrame')
        input_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.user_input = ttk.Entry(
            input_frame,
            font=FONTS["body"],
            style='TEntry'
        )
        self.user_input.pack(
            side='left', 
            fill='x', 
            expand=True, 
            padx=(0, 10),
            ipady=8
        )
        self.user_input.bind("<Return>", lambda e: self.send_message())
        
        send_btn = ttk.Button(
            input_frame,
            text="Invia →",
            command=self.send_message,
            style='TButton'
        )
        send_btn.pack(side='right')
        
        # Footer
        footer = ttk.Frame(self.root, style='TFrame')
        footer.pack(fill='x', pady=(0, 10))
        
        ttk.Label(footer, 
                text="© 2025 CiaoHost AI - v1.0", 
                foreground=COLORS["text"],
                background=COLORS["light"]).pack(side='left', padx=20)
        
        # Aggiungi animazione di benvenuto
        self.display_message("🤖 Benvenuto in CiaoHost AI Assistant!\nFai qualsiasi domanda, sarò a tua disposizione. (siate specifici)\n\n", 'bot')

    def show_help(self):
        webbrowser.open("https://youtu.be/7BYie1hdU1s?si=1OdGWgpZaZRz14bY&t=19")

    def load_database(self):
        try:
            with open(DB_FILE, "r") as f:
                self.properties = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.properties = {}
            self.save_database()

    def save_database(self):
        with open(DB_FILE, "w") as f:
            json.dump(self.properties, f, indent=2)

    def handle_admin_commands(self, user_id, text):
        if text.startswith("/admin"):
            self.user_states[user_id] = {"mode": "admin_auth", "step": "username"}
            return "Inserisci username admin:"
            
        if user_id in self.user_states:
            state = self.user_states[user_id]
            
            if state["mode"] == "admin_auth":
                if state["step"] == "username":
                    if text == ADMIN_CREDENTIALS["username"]:
                        state["step"] = "password"
                        return "Inserisci password:"
                    return "Username errato!"
                
                elif state["step"] == "password":
                    if text == ADMIN_CREDENTIALS["password"]:
                        self.user_states[user_id] = {"mode": "admin"}
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
                        self.properties[prop_id] = {
                            "type": prop_type,
                            "price": float(price),
                            "location": location,
                            "phone": phone,
                            "services": services.split(","),
                            "status": "disponibile"
                        }
                        self.save_database()
                        return f"✅ Immobile {prop_id} aggiunto!"
                    except Exception as e:
                        return f"❌ Errore: Formato corretto:\n/add ID TIPO PREZZO 'LOCALITÀ' TELEFONO 'SERVIZIO1,SERVIZIO2'"
                
                elif text.startswith("/delete"):
                    try:
                        _, prop_id = text.split()
                        del self.properties[prop_id]
                        self.save_database()
                        return f"✅ Immobile {prop_id} eliminato!"
                    except KeyError:
                        return "❌ Immobile non trovato"
                
                elif text.startswith("/modify"):
                    try:
                        _, prop_id, field, value = text.split(maxsplit=3)
                        if field == "services":
                            self.properties[prop_id][field] = value.split(",")
                        else:
                            self.properties[prop_id][field] = value
                        self.save_database()
                        return f"✅ Immobile {prop_id} modificato!"
                    except Exception as e:
                        return f"❌ Errore: {str(e)}"
                
                elif text.startswith("/list"):
                    return json.dumps(self.properties, indent=2)
                
        return None

    def send_message(self):
        user_text = self.user_input.get()
        if not user_text:
            return
        
        self.display_message(f"Tu: {user_text}", 'user')
        self.user_input.delete(0, tk.END)
        
        try:
            admin_response = self.handle_admin_commands("user1", user_text)
            if admin_response:
                self.display_message(f"ADMIN: {admin_response}\n\n", 'admin')
                return
            
            full_prompt = f"{CONTESTO_IMMOBILIARE}\nDatabase: {self.properties}\nUtente: {user_text}"
            response = model.generate_content(full_prompt)
            self.display_message(f"CiaoHost AI: {response.text}\n\n", 'bot')
        except Exception as e:
            self.display_message(f"CiaoHost AI: Errore: {str(e)}\n\n", 'bot')

    def display_message(self, message, sender):
        self.chat_area.configure(state='normal')
        self.chat_area.insert(tk.END, message + "\n", sender)
        self.chat_area.configure(state='disabled')
        self.chat_area.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = RealEstateChatbot(root)
    root.mainloop()
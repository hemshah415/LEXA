import os, threading, datetime, requests, wikipedia, pyttsx3, webbrowser, re, math
import speech_recognition as sr
import customtkinter as ctk
from tkinter import messagebox, filedialog, Tk, Toplevel
from PIL import Image, ImageTk
import pytesseract, fitz, sympy, json, psutil, time, winsound, pyautogui, pyperclip
import xml.etree.ElementTree as ET
from voice_login import authenticate_user

# === Global Config ===
API_KEY = "26ec3816b9069f1b8fcf88c70d2d27af"
VOICE_RATE = 210
VOICE_INDEX = 1
CHAT_HISTORY_FILE = "chat_history.txt"
EXTRACTED_FILE = "uploaded_file_text.txt"
MEMORY_FILE = "memory.json"

# === Theme Colors (Premium Semi-Dark) ===
BG_COLOR = "#1A1A2E"        # Deep Purple/Blue base
SIDEBAR_COLOR = "#16213E"   # Darker for contrast
ACCENT_COLOR = "#0F3460"    # Rich Blue
CYAN = "#4facfe"            # Neon Cyan accent
PURPLE_ACCENT = "#9B59B6"   # Subtle purple
TEXT_MAIN = "#FFFFFF"
TEXT_SUB = "#8A93A2"
USER_BUBBLE = "#0F3460"
AI_BUBBLE = "#232946"

class LexaCoreApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LEXA CORE OS")
        self.geometry("1400x900")
        self.state("zoomed")
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=BG_COLOR)
        
        # State Variables
        self.user_city = "Mumbai"
        self.user_country = "India"
        self.user_lat, self.user_lon = 0.0, 0.0
        self.memory = {}
        self.current_mode = "Chat Mode"
        self.is_listening = False
        self.wave_offset = 0
        self.autopilot_mode = False
        self.last_query = ""
        self.chat_context = []
        
        # Initialization
        self.load_memory()
        self.fetch_geolocation()
        self.build_ui()
        
        # Binds
        self.bind("<Control-k>", self.show_command_palette)
        self.bind("<Return>", self.on_submit)
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        
        # Updaters
        self.update_live_data()
        self.animate_waveform()
        
        # Startup
        greeting = f"LEXA Core OS Initialized. Welcome back. Running in {self.current_mode}."
        self.add_message(greeting, "SYSTEM")
        threading.Thread(target=self.speak, args=(greeting,), daemon=True).start()

    # ==========================
    # CORE LOGIC
    # ==========================
    def load_memory(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r") as f:
                    self.memory = json.load(f)
            except:
                self.memory = {}

    def save_memory(self):
        with open(MEMORY_FILE, "w") as f:
            json.dump(self.memory, f)

    def fetch_geolocation(self):
        try:
            data = requests.get("http://ip-api.com/json/", timeout=3).json()
            if data.get("status") == "success":
                self.user_city = data.get("city", "Mumbai")
                self.user_country = data.get("country", "India")
                self.user_lat = data.get("lat", 0.0)
                self.user_lon = data.get("lon", 0.0)
        except:
            pass

    def speak(self, text):
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", VOICE_RATE)
            engine.setProperty("volume", 0.6) # Added to make the voice softer
            voices = engine.getProperty("voices")
            engine.setProperty("voice", voices[VOICE_INDEX].id)
            engine.say(text)
            engine.runAndWait()
        except:
            pass

    def play_sound(self):
        try:
            threading.Thread(target=lambda: winsound.MessageBeep(winsound.MB_ICONASTERISK), daemon=True).start()
        except:
            pass

    # --- Data Fetchers & Handlers ---
    def get_news(self):
        try:
            url = "http://feeds.bbci.co.uk/news/rss.xml"
            response = requests.get(url)
            root = ET.fromstring(response.content)
            headlines = [item.find('title').text for item in root.findall('./channel/item')[:5]]
            return "Live Global News Briefing:\n\n" + "\n".join(f"🔸 {h}" for h in headlines)
        except: return "Sorry, I couldn't fetch the news."

    def get_joke(self):
        try: return requests.get("https://v2.jokeapi.dev/joke/Any?type=single").json().get("joke", "I'm out of jokes!")
        except: return "Why did the AI cross the road? To optimize the other side!"

    def get_fact(self):
        try: return requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random").json().get("text", "Water is wet.")
        except: return "You are talking to an AI right now."

    def open_item(self, query):
        q = query.lower()
        if "chrome" in q: os.startfile("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"); return "Opening Google Chrome."
        elif "downloads" in q: os.startfile(os.path.expanduser("~/Downloads")); return "Opening Downloads folder."
        elif "youtube" in q: webbrowser.open("https://www.youtube.com"); return "Opening YouTube."
        elif "google" in q: webbrowser.open("https://www.google.com"); return "Opening Google."
        return None

    def search_history(self, keyword):
        if not os.path.exists(CHAT_HISTORY_FILE): return "No history found."
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        matches = [line for line in lines if keyword.lower() in line.lower()]
        return "".join(matches) if matches else "No matches found."

    def detect_local_intent(self, query_lower):
        """ Returns (handled: bool, response_text: str) """
        q = query_lower
        
        # 1. Location intent
        if any(w in q for w in ["where am i", "my location", "where is this", "location", "gps"]):
            url = f"https://www.google.com/maps?q={self.user_lat},{self.user_lon}"
            webbrowser.open(url)
            return True, f"📍 Detected Location: {self.user_city}, {self.user_country}. Opening Maps."
            
        # 2. Browser / Apps
        if any(w in q for w in ["open", "launch", "go to", "start"]):
            res = self.open_item(q)
            if res: return True, res
            
        # 3. Screenshot
        if "screenshot" in q or "capture screen" in q:
            filename = f"screenshot_{int(time.time())}.png"
            pyautogui.screenshot(filename)
            return True, f"📸 Screenshot saved as {filename}."
            
        # 4. Volume
        if "mute" in q: pyautogui.press("volumemute"); return True, "🔊 System muted."
        if "volume up" in q: pyautogui.press("volumeup", presses=5); return True, "🔊 Volume increased."
        if "volume down" in q: pyautogui.press("volumedown", presses=5); return True, "🔉 Volume decreased."
        
        # 5. Math
        if "calculate" in q or "solve" in q:
            try:
                expr = q.replace("calculate", "").replace("solve", "").replace("x", "*").strip()
                return True, f"Calculated Result: {sympy.N(sympy.sympify(expr))}"
            except: return True, "Could not compute expression."
            
        # 6. APIs
        if "weather" in q: self.update_live_data(); return True, f"Fetching weather data for {self.user_city}..."
        if "joke" in q: return True, self.get_joke()
        if "fact" in q: return True, self.get_fact()
        if any(w in q for w in ["news", "headlines", "briefing"]): return True, self.get_news()
        if "clipboard" in q: return True, f"📋 Clipboard:\n{pyperclip.paste()}"
        if "system status" in q: return True, f"💻 CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%"
        
        # 7. Analyze explicit commands
        if "analyze file" in q: return True, "File analysis completed. See output above."
        
        return False, ""

    # ==========================
    # UI CONSTRUCTION
    # ==========================
    def build_ui(self):
        # -- Top Status Bar --
        self.header = ctk.CTkFrame(self, height=60, fg_color=SIDEBAR_COLOR, corner_radius=0)
        self.header.pack(fill="x", side="top")
        
        self.title_lbl = ctk.CTkLabel(self.header, text="LEXA CORE", font=("Cascadia Code", 22, "bold"), text_color=CYAN)
        self.title_lbl.place(x=20, y=15)
        
        self.ai_status_lbl = ctk.CTkLabel(self.header, text="⚪ STANDBY", font=("Cascadia Code", 14), text_color=TEXT_SUB)
        self.ai_status_lbl.place(x=170, y=18)
        
        self.time_lbl = ctk.CTkLabel(self.header, text="--:--", font=("Cascadia Code", 16, "bold"), text_color=TEXT_MAIN)
        self.time_lbl.place(x=1100, y=18)
        
        self.weather_lbl = ctk.CTkLabel(self.header, text="Loading...", font=("Cascadia Code", 16), text_color=PURPLE_ACCENT)
        self.weather_lbl.place(x=1200, y=18)

        # -- Sidebar --
        self.sidebar = ctk.CTkFrame(self, width=250, fg_color=SIDEBAR_COLOR, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        # Sidebar Menu
        menus = [
            ("🎛️ Dashboard", lambda: self.add_message("Dashboard opened.", "SYSTEM")),
            ("💬 Chat", lambda: self.entry.focus()),
            ("🎤 Voice Mode", self.voice_input),
            ("📂 Files / Data", self.upload_file),
            ("📜 History", lambda: self.add_message(f"History saved to {CHAT_HISTORY_FILE}", "SYSTEM")),
            ("⚙️ Settings", lambda: self.add_message("Settings panel under construction.", "SYSTEM"))
        ]
        
        for text, cmd in menus:
            btn = ctk.CTkButton(self.sidebar, text=text, command=cmd, fg_color="transparent", hover_color=ACCENT_COLOR, 
                                anchor="w", font=("Arial", 15), text_color=TEXT_MAIN, corner_radius=8, height=40)
            btn.pack(fill="x", padx=15, pady=5)
            
        # AI Modes Dropdown
        ctk.CTkLabel(self.sidebar, text="AI OPERATING MODE", font=("Arial", 10, "bold"), text_color=TEXT_SUB).pack(pady=(30,5), padx=20, anchor="w")
        self.mode_var = ctk.StringVar(value=self.current_mode)
        mode_dropdown = ctk.CTkOptionMenu(self.sidebar, variable=self.mode_var, values=["Chat Mode", "Code Assistant", "Study Mode", "Fitness Mode"],
                                          command=self.change_mode, fg_color=ACCENT_COLOR, button_color=CYAN, font=("Arial", 13))
        mode_dropdown.pack(fill="x", padx=15, pady=5)
        
        # Autopilot Toggle
        self.hands_free_btn = ctk.CTkButton(self.sidebar, text="⏸️ Autopilot: OFF", command=self.toggle_hands_free, 
                                            fg_color=BG_COLOR, border_width=1, border_color=CYAN, hover_color=ACCENT_COLOR)
        self.hands_free_btn.pack(side="bottom", fill="x", padx=15, pady=20)

        # -- Main Content Area --
        self.main_panel = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=0)
        self.main_panel.pack(side="left", fill="both", expand=True)
        
        # Waveform Canvas (Visualizer)
        self.wave_canvas = ctk.CTkCanvas(self.main_panel, height=60, bg=BG_COLOR, highlightthickness=0)
        self.wave_canvas.pack(fill="x", padx=30, pady=(10, 0))
        
        # Chat Area
        self.chat_frame = ctk.CTkScrollableFrame(self.main_panel, fg_color="transparent")
        self.chat_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Input Area
        self.input_frame = ctk.CTkFrame(self.main_panel, fg_color=SIDEBAR_COLOR, corner_radius=20, border_width=1, border_color=ACCENT_COLOR)
        self.input_frame.pack(fill="x", padx=30, pady=20)
        
        self.entry = ctk.CTkEntry(self.input_frame, height=50, font=("Cascadia Code", 15), fg_color="transparent", border_width=0, placeholder_text="Message LEXA... (Ctrl+K for Commands)")
        self.entry.pack(side="left", fill="x", expand=True, padx=20, pady=5)
        
        ctk.CTkButton(self.input_frame, text="📎", width=40, height=40, fg_color="transparent", hover_color=ACCENT_COLOR, font=("Arial", 18), command=self.upload_file).pack(side="left", padx=5)
        ctk.CTkButton(self.input_frame, text="🎤", width=40, height=40, fg_color="transparent", hover_color=ACCENT_COLOR, font=("Arial", 18), command=self.voice_input).pack(side="left", padx=5)
        ctk.CTkButton(self.input_frame, text="➤", width=50, height=40, fg_color=CYAN, text_color="black", hover_color="#2874A6", font=("Arial", 18, "bold"), corner_radius=15, command=self.on_submit).pack(side="left", padx=10, pady=5)

    # ==========================
    # UI EFFECTS & UPDATERS
    # ==========================
    def update_live_data(self):
        self.time_lbl.configure(text=datetime.datetime.now().strftime("%I:%M %p"))
        def fetch_weather():
            try:
                url = f"https://api.openweathermap.org/data/2.5/weather?q={self.user_city}&appid={API_KEY}&units=metric"
                data = requests.get(url, timeout=3).json()
                temp = data["main"]["temp"]
                desc = data["weather"][0]["description"].capitalize()
                self.after(0, lambda: self.weather_lbl.configure(text=f"{desc}, {temp}°C"))
            except:
                self.after(0, lambda: self.weather_lbl.configure(text="Weather Offline"))
        
        threading.Thread(target=fetch_weather, daemon=True).start()
        self.after(60000, self.update_live_data)

    def set_ai_status(self, state):
        if state == "thinking":
            self.ai_status_lbl.configure(text="🟢 THINKING...", text_color="#2ECC71")
            self.is_listening = False
        elif state == "listening":
            self.ai_status_lbl.configure(text="🔵 LISTENING...", text_color=CYAN)
            self.is_listening = True
        else:
            self.ai_status_lbl.configure(text="⚪ STANDBY", text_color=TEXT_SUB)
            self.is_listening = False

    def animate_waveform(self):
        self.wave_canvas.delete("all")
        width = self.wave_canvas.winfo_width()
        height = self.wave_canvas.winfo_height()
        if width > 10:
            mid_y = height / 2
            points = []
            amplitude = 20 if self.is_listening else 2
            frequency = 0.05
            for x in range(0, width, 5):
                y = mid_y + math.sin(x * frequency + self.wave_offset) * amplitude
                points.extend([x, y])
            if len(points) >= 4:
                self.wave_canvas.create_line(points, fill=CYAN, width=2, smooth=True)
            self.wave_offset += 0.2
        self.after(50, self.animate_waveform)

    # ==========================
    # CHAT MESSAGING
    # ==========================
    def add_message(self, text, sender="LEXA"):
        msg_container = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        msg_container.pack(fill="x", padx=10, pady=10)

        if sender == "USER":
            bubble_color = USER_BUBBLE
            align = "e"
            text_color = TEXT_MAIN
        elif sender == "SYSTEM":
            bubble_color = SIDEBAR_COLOR
            align = "center"
            text_color = PURPLE_ACCENT
        else:
            bubble_color = AI_BUBBLE
            align = "w"
            text_color = TEXT_MAIN

        bubble = ctk.CTkFrame(msg_container, fg_color=bubble_color, corner_radius=15)
        if align == "center":
            bubble.pack(anchor="center")
        elif align == "e":
            bubble.pack(side="right")
        else:
            bubble.pack(side="left")

        # Sender Name
        if align != "center":
            ctk.CTkLabel(bubble, text=sender, text_color=CYAN if sender=="LEXA" else TEXT_SUB, font=("Cascadia Code", 10, "bold")).pack(anchor=align, padx=15, pady=(5,0))

        lbl = ctk.CTkLabel(bubble, text="", text_color=text_color, font=("Consolas", 14), wraplength=600, justify="left")
        lbl.pack(padx=20, pady=(5, 10))

        # Quick Actions for AI
        if sender == "LEXA":
            actions_frame = ctk.CTkFrame(bubble, fg_color="transparent")
            actions_frame.pack(anchor="w", padx=15, pady=(0,5))
            ctk.CTkButton(actions_frame, text="📋 Copy", width=40, height=20, font=("Arial", 10), fg_color=SIDEBAR_COLOR, hover_color=ACCENT_COLOR, command=lambda t=text: pyperclip.copy(t)).pack(side="left", padx=2)
            ctk.CTkButton(actions_frame, text="🔄 Regenerate", width=40, height=20, font=("Arial", 10), fg_color=SIDEBAR_COLOR, hover_color=ACCENT_COLOR, command=lambda: self.process_and_respond(self.last_query)).pack(side="left", padx=2)

        def scroll(): self.chat_frame._parent_canvas.yview_moveto(1.0)

        if sender == "LEXA":
            def type_text(i=0):
                if i <= len(text):
                    lbl.configure(text=text[:i])
                    scroll()
                    lbl.after(10, type_text, i+1)
            type_text()
        else:
            lbl.configure(text=text)
            self.after(10, scroll)

        # Log
        with open(CHAT_HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now()}] {sender}: {text}\n")

    # ==========================
    # LOGIC & COMMANDS
    # ==========================
    def change_mode(self, new_mode):
        self.current_mode = new_mode
        self.add_message(f"Switched to {new_mode}.", "SYSTEM")

    def on_submit(self, event=None):
        query = self.entry.get().strip()
        if not query: return
        self.entry.delete(0, "end")
        self.play_sound()
        self.add_message(query, "USER")
        self.process_and_respond(query)

    def process_and_respond(self, query):
        self.last_query = query
        self.set_ai_status("thinking")
        threading.Thread(target=self._generate_response, args=(query,), daemon=True).start()

    def _generate_response(self, query):
        print(f"\n[DEBUG] Processing Query: '{query}'")
        query_lower = query.lower()

        # Step 1: Hybrid Intent Detection
        handled, local_response = self.detect_local_intent(query_lower)
        if handled:
            print(f"[DEBUG] Local Intent Detected. Response: {local_response}")
            self.chat_context.append({"role": "user", "content": query})
            self.chat_context.append({"role": "assistant", "content": local_response})
            self._finalize_response(local_response)
            return

        # Step 2: Pure LLM Conversation
        print("[DEBUG] No local intent matched. Routing to LLM Conversational Engine.")
        system_instructions = f"You are LEXA Core OS. Current mode: {self.current_mode}. User city: {self.user_city}. Keep answers concise and helpful."
        if self.current_mode == "Code Assistant": system_instructions += " You are an expert programmer."
        elif self.current_mode == "Study Mode": system_instructions += " You are a tutor."
        elif self.current_mode == "Fitness Mode": system_instructions += " You are a fitness coach."

        if len(self.chat_context) == 0 or self.chat_context[0]["role"] != "system":
            self.chat_context.insert(0, {"role": "system", "content": system_instructions})
        else:
            self.chat_context[0] = {"role": "system", "content": system_instructions}
            
        self.chat_context.append({"role": "user", "content": query})
        
        # Keep last 10 messages (1 system + 9 history)
        if len(self.chat_context) > 10:
            self.chat_context.pop(1)

        llm_response = ""
        try:
            res = requests.post("https://text.pollinations.ai/", json={"messages": self.chat_context}, timeout=15)
            if res.status_code == 200:
                llm_response = res.text
                print("[DEBUG] LLM Generated Response Successfully.")
            else:
                llm_response = f"API Error ({res.status_code}). I could not generate a response."
                print(f"[DEBUG] API Error: {res.status_code}")
        except Exception as e:
            llm_response = "Connection timeout. Please check your internet."
            print(f"[DEBUG] LLM Exception: {e}")

        self.chat_context.append({"role": "assistant", "content": llm_response})
        self._finalize_response(llm_response)

    def _finalize_response(self, text):
        self.after(500, lambda: self.set_ai_status("standby"))
        self.after(500, lambda: self.add_message(text, "LEXA"))
        threading.Thread(target=self.speak, args=(text,), daemon=True).start()

    # ==========================
    # FEATURES
    # ==========================
    def voice_input(self):
        def listen_thread():
            self.after(0, lambda: self.set_ai_status("listening"))
            self.speak("Listening")
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                try:
                    audio = recognizer.listen(source, timeout=5)
                    self.after(0, lambda: self.set_ai_status("thinking"))
                    query = recognizer.recognize_google(audio)
                    self.after(0, lambda: self.add_message(query, "USER"))
                    self.process_and_respond(query)
                except:
                    self.after(0, lambda: self.set_ai_status("standby"))
                    self.after(0, lambda: self.add_message("Voice signal lost.", "SYSTEM"))
        threading.Thread(target=listen_thread, daemon=True).start()

    def toggle_hands_free(self):
        self.autopilot_mode = not self.autopilot_mode
        if self.autopilot_mode:
            self.hands_free_btn.configure(text="▶️ Autopilot: ACTIVE", fg_color=CYAN, text_color="black")
            threading.Thread(target=self.wake_word_listener, daemon=True).start()
        else:
            self.hands_free_btn.configure(text="⏸️ Autopilot: OFF", fg_color=BG_COLOR, text_color=TEXT_MAIN)

    def wake_word_listener(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            while self.autopilot_mode:
                try:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                    text = recognizer.recognize_google(audio).lower()
                    if "hello" in text:
                        self.play_sound()
                        self.voice_input()
                except:
                    pass
                time.sleep(0.5)

    def upload_file(self):
        path = filedialog.askopenfilename()
        if not path: return
        self.add_message(f"File uploaded: {os.path.basename(path)}", "SYSTEM")
        def process_file():
            print(f"[DEBUG] Processing File: {path}")
            self.set_ai_status("thinking")
            extracted_text = ""
            ext = path.lower().split('.')[-1] if '.' in path else ""
            try:
                if ext == "pdf":
                    pdf_doc = fitz.open(path)
                    for page in pdf_doc: extracted_text += page.get_text()
                    pdf_doc.close()
                elif ext in ["docx", "doc"]:
                    import docx
                    doc = docx.Document(path)
                    extracted_text = "\n".join([para.text for para in doc.paragraphs])
                elif ext == "txt":
                    with open(path, "r", encoding="utf-8") as f:
                        extracted_text = f.read()
                elif ext in ["png", "jpg", "jpeg"]:
                    extracted_text = pytesseract.image_to_string(Image.open(path))
                else:
                    raise ValueError(f"Unsupported file type: .{ext}. Please upload PDF, DOCX, TXT, or Image.")

                if extracted_text.strip():
                    with open(EXTRACTED_FILE, "w", encoding="utf-8") as f: f.write(extracted_text)
                    summary = extracted_text[:200] + "..." if len(extracted_text)>200 else extracted_text
                    self._finalize_response(f"Data extracted to '{EXTRACTED_FILE}'.\n\nPreview:\n{summary}")
                else:
                    self._finalize_response("Scan complete: No textual data found.")
            except Exception as e:
                print(f"[DEBUG] File Error: {e}")
                self._finalize_response(f"Extraction error: {e}")
        threading.Thread(target=process_file, daemon=True).start()

    def show_command_palette(self, event=None):
        palette = Toplevel(self)
        palette.geometry("600x60")
        palette.configure(bg=SIDEBAR_COLOR)
        palette.overrideredirect(True) # Remove borders
        palette.eval(f'tk::PlaceWindow {str(palette)} center')
        
        entry = ctk.CTkEntry(palette, font=("Cascadia Code", 18), fg_color=SIDEBAR_COLOR, text_color=CYAN, border_width=1, border_color=CYAN)
        entry.pack(fill="both", expand=True, padx=5, pady=5)
        entry.focus()
        
        def execute_cmd(e):
            cmd = entry.get()
            palette.destroy()
            if cmd:
                self.add_message(cmd, "USER")
                self.process_and_respond(cmd)
                
        entry.bind("<Return>", execute_cmd)
        entry.bind("<Escape>", lambda e: palette.destroy())

if __name__ == "__main__":
    if not authenticate_user():
        root = Tk()
        root.withdraw()
        messagebox.showerror("Auth Failed", "Access Denied.")
        exit()
    app = LexaCoreApp()
    app.mainloop()

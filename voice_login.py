import speech_recognition as sr
import time
import re
import tkinter as tk
from tkinter import simpledialog

MAX_ATTEMPTS = 3
VOICE_ATTEMPTS = 2
PASSPHRASES = ["hello"]
PASSWORD = "lexa"

def gui_password_prompt():
    root = tk.Tk()
    root.withdraw()
    password = simpledialog.askstring("LEXA Security", "Voice failed or timeout.\nEnter fallback password (leave blank to retry voice):", show='*')
    root.destroy()
    return password if password is not None else ""

def authenticate_user():
    recognizer = sr.Recognizer()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        # Voice tries
        for voice_try in range(1, VOICE_ATTEMPTS + 1):
            
            # Create a visual listening prompt
            voice_root = tk.Tk()
            voice_root.title("LEXA Lock")
            voice_root.geometry("350x150")
            voice_root.configure(bg="#F4F8FB")
            # Center the window
            voice_root.eval('tk::PlaceWindow . center')
            
            tk.Label(voice_root, text="🎤 Voice Authentication", font=("Cascadia Code", 14, "bold"), bg="#F4F8FB", fg="#00AEEF").pack(pady=(20, 10))
            tk.Label(voice_root, text=f"Listening... Say 'hello' to unlock.\n(Attempt {voice_try} of {VOICE_ATTEMPTS})", font=("Consolas", 12), bg="#F4F8FB", fg="#1C2833").pack()
            
            # Force update the GUI before blocking with listen()
            voice_root.update()

            success = False
            with sr.Microphone() as source:
                try:
                    audio = recognizer.listen(source, timeout=4)
                    text = recognizer.recognize_google(audio).strip().lower()
                    text_clean = re.sub(r'[^\w\s]', '', text)
                    if any(phrase == text_clean for phrase in PASSPHRASES) or any(phrase in text_clean for phrase in PASSPHRASES):
                        success = True
                except Exception as e:
                    pass
            
            voice_root.destroy()
            
            if success:
                return True

        # PASSWORD fallback always as GUI dialog
        password = gui_password_prompt().strip()
        if password == "":
            continue  # try voice again in next main attempt
        if password.lower() == PASSWORD:
            return True
        time.sleep(0.5)
        
    return False

# For standalone testing
if __name__ == "__main__":
    if authenticate_user():
        print("Access Granted!")
    else:
        print("Access Denied.")

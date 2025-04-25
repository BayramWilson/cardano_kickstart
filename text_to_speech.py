import pyttsx3
from config import TTS_ENABLED, TTS_RATE

class TextToSpeech:
    def __init__(self):
        self.enabled = TTS_ENABLED
        
        if self.enabled:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', TTS_RATE)
                print("Text-to-Speech Engine initialisiert.")
            except Exception as e:
                print(f"Fehler bei der Initialisierung der Text-to-Speech Engine: {e}")
                self.enabled = False
    
    def speak(self, text):
        """Gibt den Text als Sprache aus."""
        if not self.enabled:
            print(f"TTS (deaktiviert): {text}")
            return
        
        try:
            print(f"TTS: {text}")
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Fehler bei der Sprachausgabe: {e}")
            print(f"Text: {text}")
    
    def set_rate(self, rate):
        """Ändert die Sprechgeschwindigkeit."""
        if not self.enabled:
            return
        
        try:
            self.engine.setProperty('rate', rate)
        except Exception as e:
            print(f"Fehler beim Ändern der Sprechgeschwindigkeit: {e}") 
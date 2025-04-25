import os
import tempfile
import speech_recognition as sr
import openai
import pyaudio
import wave
from config import OPENAI_API_KEY, AUDIO_RECORDING_TIMEOUT, AUDIO_SAMPLE_RATE, AUDIO_CHANNELS

# OpenAI API-Key setzen
openai.api_key = OPENAI_API_KEY

class AudioProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        
        # Hintergrundgeräusche kalibrieren
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source)
        print("Mikrofon kalibriert und bereit.")
        
    def record_audio(self, timeout=AUDIO_RECORDING_TIMEOUT):
        """Nimmt Audio über das Mikrofon auf und gibt den Dateipfad zurück."""
        print(f"Aufnahme startet... (Sprechen Sie jetzt - {timeout} Sekunden)")
        
        # Temp-Datei für die Audioaufnahme erstellen
        temp_file = tempfile.mktemp(suffix=".wav")
        
        # Aufnahme-Parameter
        chunk = 1024
        format = pyaudio.paInt16
        channels = AUDIO_CHANNELS
        rate = AUDIO_SAMPLE_RATE
        
        # PyAudio-Instanz erstellen
        p = pyaudio.PyAudio()
        
        # Stream öffnen
        stream = p.open(format=format,
                        channels=channels,
                        rate=rate,
                        input=True,
                        frames_per_buffer=chunk)
        
        frames = []
        
        # Aufnahme für die angegebene Zeit
        for _ in range(0, int(rate / chunk * timeout)):
            data = stream.read(chunk)
            frames.append(data)
        
        print("Aufnahme beendet.")
        
        # Stream beenden
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Aufnahme in Datei speichern
        wf = wave.open(temp_file, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(format))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        return temp_file
    
    def transcribe_with_whisper(self, audio_file_path):
        """Transkribiert die Audiodatei mit OpenAI Whisper API."""
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcription = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file
                )
            
            return transcription["text"]
        except Exception as e:
            print(f"Fehler bei der Transkription: {e}")
            return None
        finally:
            # Temporäre Audiodatei löschen
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
    
    def listen_and_transcribe(self):
        """Nimmt Audio auf und transkribiert es."""
        try:
            audio_file = self.record_audio()
            
            if audio_file:
                print("Transkribiere Audio...")
                transcription = self.transcribe_with_whisper(audio_file)
                
                if transcription:
                    print(f"Transkription: {transcription}")
                    return transcription
                else:
                    print("Transkription fehlgeschlagen.")
                    return None
        except Exception as e:
            print(f"Fehler bei der Audio-Verarbeitung: {e}")
            return None 
import os
import tempfile
import openai
from config import OPENAI_API_KEY

# OpenAI API-Key setzen
openai.api_key = OPENAI_API_KEY

class TelegramAudioProcessor:
    def __init__(self):
        pass
        
    async def process_voice_message(self, voice_file):
        """
        Verarbeitet eine Telegram-Sprachnachricht und gibt die Transkription zurück.
        
        :param voice_file: Pfad zur temporären Sprachdatei
        :return: Transkription als Text
        """
        try:
            print(f"Transkribiere Sprachnachricht...")
            
            with open(voice_file, "rb") as audio_file:
                transcription = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file
                )
            
            transcript_text = transcription.get("text", "")
            print(f"Transkription: {transcript_text}")
            return transcript_text
            
        except Exception as e:
            print(f"Fehler bei der Transkription: {e}")
            return None
        finally:
            # Temporäre Datei löschen
            if os.path.exists(voice_file):
                try:
                    os.remove(voice_file)
                except:
                    pass
                
    async def download_voice_message(self, voice_message):
        """
        Lädt eine Sprachnachricht von Telegram herunter.
        
        :param voice_message: Telegram Voice-Objekt
        :return: Pfad zur lokalen Datei
        """
        try:
            # Temporäre Datei erstellen
            temp_file = tempfile.mktemp(suffix=".ogg")
            
            # Datei herunterladen
            voice_file = await voice_message.get_file()
            await voice_file.download_to_drive(temp_file)
            
            print(f"Sprachnachricht heruntergeladen nach {temp_file}")
            return temp_file
            
        except Exception as e:
            print(f"Fehler beim Herunterladen der Sprachnachricht: {e}")
            return None 
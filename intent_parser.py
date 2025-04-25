import re
import openai
from config import OPENAI_API_KEY

# OpenAI API-Key setzen
openai.api_key = OPENAI_API_KEY

class IntentParser:
    def __init__(self):
        # Reguläre Ausdrücke für einfache Intent-Erkennung
        self.patterns = {
            'send_ada': r'sende|schicke|überweise|transfer|übertrage|transferiere.*\b(\d+(?:\.\d+)?)\s*ada\b.*\ban\b.*\b([a-zA-Z0-9]+)',
            'check_balance': r'(wie\s+viel|wieviel|welchen\s+betrag|balance|guthaben|kontostand|bestand).*\b(ada)\b',
            'help': r'hilfe|helfen|befehle|kommandos|was\s+kannst\s+du',
        }
    
    def extract_intent_regex(self, text):
        """Extrahiert Intents und Entitäten aus dem Text mittels Regex."""
        text = text.lower()
        
        # Überprüfe auf Senden von ADA
        send_match = re.search(self.patterns['send_ada'], text)
        if send_match:
            amount = float(send_match.group(1))
            # Adresse könnte unvollständig oder falsch erkannt sein
            address = send_match.group(2)
            return {
                'intent': 'send_ada',
                'entities': {
                    'amount': amount,
                    'recipient_address': address
                }
            }
        
        # Überprüfe auf Kontostandsabfrage
        if re.search(self.patterns['check_balance'], text):
            return {
                'intent': 'check_balance',
                'entities': {}
            }
        
        # Überprüfe auf Hilfe-Anfrage
        if re.search(self.patterns['help'], text):
            return {
                'intent': 'help',
                'entities': {}
            }
        
        # Wenn kein bekanntes Muster gefunden wurde
        return {
            'intent': 'unknown',
            'entities': {}
        }
    
    def parse_with_openai(self, text):
        """Nutzt OpenAI, um Intents und Entitäten zu extrahieren."""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": """
                    Du bist ein Sprachassistent für Cardano-Kryptowährungstransaktionen.
                    Extrahiere die Benutzerabsicht (Intent) und relevante Entitäten aus dem Text.
                    Mögliche Intents:
                    - send_ada: Senden von ADA an eine Adresse
                    - check_balance: Kontostand abfragen
                    - help: Hilfe anfordern
                    - unknown: Unbekannte Anfrage
                    
                    Gib das Ergebnis als JSON zurück mit den Feldern 'intent' und 'entities'.
                    Bei send_ada müssen 'amount' und 'recipient_address' in entities enthalten sein.
                    """}, 
                    {"role": "user", "content": text}
                ]
            )
            
            result = response.choices[0].message.content
            # Extrahiere JSON aus der Antwort
            import json
            try:
                # Versuche JSON zu finden und zu parsen
                json_match = re.search(r'```json\n(.*?)\n```', result, re.DOTALL)
                if json_match:
                    result = json_match.group(1)
                return json.loads(result)
            except:
                # Fallback auf einfaches Regex-Parsing
                return self.extract_intent_regex(text)
            
        except Exception as e:
            print(f"Fehler bei der OpenAI-Verarbeitung: {e}")
            # Fallback auf einfaches Regex-Parsing
            return self.extract_intent_regex(text)
    
    def parse(self, text):
        """Parst den Text und gibt Intent und Entitäten zurück."""
        # Versuche zuerst mit OpenAI
        try:
            result = self.parse_with_openai(text)
            if result and result.get('intent') != 'unknown':
                return result
        except:
            pass
        
        # Fallback auf Regex
        return self.extract_intent_regex(text) 
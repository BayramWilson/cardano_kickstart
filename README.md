# Cardano Sprachassistent-Bot

Ein Telegram-Bot, der Sprachbefehle entgegennimmt, diese mit OpenAI transkribiert und basierend auf dem Inhalt automatisch Cardano-Transaktionen ausführt.

## Funktionen

- Empfangen von Sprach- und Textnachrichten über Telegram
- Transkription von Sprachnachrichten mit OpenAI Whisper
- Interpretation der Befehle mittels Regex und/oder GPT-4
- Ausführen von Cardano-Transaktionen über Blockfrost API
- Kontostandsabfrage
- Benutzerauthentifizierung für sicheren Zugriff

## Voraussetzungen

- Python 3.8+
- OpenAI API-Schlüssel
- Blockfrost API-Schlüssel
- Telegram Bot-Token
- Cardano Wallet (Adresse und Signing Key)

## Installation

1. Repository klonen oder Dateien herunterladen
2. Abhängigkeiten installieren:
   ```
   pip install -r requirements.txt
   ```
3. Konfigurationsdatei erstellen:
   ```
   cp .env.example .env
   ```
4. Konfigurationsdatei `.env` mit deinen eigenen Werten bearbeiten

## Konfiguration

Folgende Umgebungsvariablen müssen in der `.env`-Datei definiert werden:

- `OPENAI_API_KEY`: Dein OpenAI API-Schlüssel
- `BLOCKFROST_PROJECT_ID`: Deine Blockfrost Projekt-ID
- `BLOCKFROST_NETWORK`: Das Cardano-Netzwerk (`mainnet` oder `testnet`)
- `WALLET_ADDRESS`: Die Adresse deines Cardano Wallets
- `WALLET_SIGNING_KEY_PATH`: Pfad zu deinem Signing Key
- `TELEGRAM_BOT_TOKEN`: Das Token deines Telegram-Bots
- `AUTHORIZED_USERS`: Kommagetrennte Liste von Telegram-User-IDs, die den Bot nutzen dürfen

## Verwendung

1. Bot starten:
   ```
   python main.py
   ```

2. Den Bot in Telegram öffnen und mit `/start` beginnen

3. Verfügbare Sprachbefehle:
   - "Wie viel ADA habe ich?"
   - "Zeige meinen Kontostand"
   - "Sende 10 ADA an Adresse abc123..."
   - "Überweise 5 ADA an xyz789..."
   - "Hilfe"

4. Der Bot kann sowohl Text- als auch Sprachnachrichten verarbeiten

## Sicherheitshinweise

- Verwende den Bot nur auf vertrauenswürdigen Geräten
- Aktiviere die Benutzerauthentifizierung (AUTHORIZED_USERS)
- Speichere den Signing Key sicher
- Für produktive Umgebungen empfehlen wir zusätzliche Sicherheitsmaßnahmen

## Modulare Struktur

- `main.py`: Der Haupt-Bot, der alle Komponenten verbindet
- `telegram_audio.py`: Verarbeitung von Telegram-Sprachnachrichten
- `intent_parser.py`: Interpretation der Befehle (Natural Language Processing)
- `cardano_transaction.py`: Ausführung von Cardano-Transaktionen
- `config.py`: Konfigurationsvariablen
- `text_to_speech.py`: Optionales Modul für Sprachausgabe 
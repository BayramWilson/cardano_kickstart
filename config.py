import os
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus .env-Datei
load_dotenv()

# OpenAI API-Konfiguration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Blockfrost API-Konfiguration
BLOCKFROST_PROJECT_ID_TESTNET = os.getenv("BLOCKFROST_PROJECT_ID_TESTNET")
BLOCKFROST_PROJECT_ID_MAINNET = os.getenv("BLOCKFROST_PROJECT_ID_MAINNET")
DEFAULT_NETWORK = os.getenv("DEFAULT_NETWORK", "testnet")  # Default: testnet

# Basispfad für Benutzerdaten (Wallets)
USER_DATA_DIR = os.getenv("USER_DATA_DIR", "user_wallets")

# Audio-Konfiguration
AUDIO_RECORDING_TIMEOUT = 5  # Sekunden
AUDIO_SAMPLE_RATE = 44100
AUDIO_CHANNELS = 1

# Text-to-Speech Konfiguration
TTS_ENABLED = True
TTS_RATE = 150  # Sprechgeschwindigkeit

# Telegram Bot Konfiguration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUTHORIZED_USERS = [int(id.strip()) for id in os.getenv("AUTHORIZED_USERS", "").split(",") if id.strip()] 
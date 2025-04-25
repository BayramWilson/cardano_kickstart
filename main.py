#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

from config import TELEGRAM_BOT_TOKEN, AUTHORIZED_USERS
from intent_parser import IntentParser
from cardano_transaction import CardanoTransactionManager
from telegram_audio import TelegramAudioProcessor

# Logging einrichten
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Konversationsstatus
CONFIRM = 1

class CardanoVoiceAssistant:
    def __init__(self):
        self.intent_parser = IntentParser()
        self.cardano_manager = CardanoTransactionManager()
        self.audio_processor = TelegramAudioProcessor()
        
        # Transaktion die auf Bestätigung wartet
        self.pending_transaction = {}
        
    async def start(self, update: Update, context: CallbackContext) -> None:
        """Startet den Bot und sendet eine Begrüßungsnachricht."""
        user_id = update.effective_user.id
        
        if AUTHORIZED_USERS and user_id not in AUTHORIZED_USERS:
            await update.message.reply_text(
                "Sie sind nicht berechtigt, diesen Bot zu verwenden."
            )
            return
        
        await update.message.reply_text(
            f"Willkommen zum Cardano Sprachassistenten, {update.effective_user.first_name}!\n\n"
            "Ich kann Ihnen helfen, Cardano-Transaktionen per Sprachbefehl auszuführen.\n\n"
            "Hier sind einige Dinge, die Sie sagen können:\n"
            "- \"Wie viel ADA habe ich?\"\n"
            "- \"Sende 5 ADA an Adresse abc123...\"\n"
            "- \"Hilfe\"\n\n"
            "Sie können mir eine Textnachricht senden oder eine Sprachnachricht aufnehmen."
        )
        
    async def help_command(self, update: Update, context: CallbackContext) -> None:
        """Hilfebefehl"""
        user_id = update.effective_user.id
        
        if AUTHORIZED_USERS and user_id not in AUTHORIZED_USERS:
            return
            
        await update.message.reply_text(
            "Ich verstehe folgende Befehle:\n\n"
            "1. Kontostand abfragen:\n"
            "   \"Wie viel ADA habe ich?\"\n"
            "   \"Zeige meinen Kontostand\"\n\n"
            "2. ADA senden:\n"
            "   \"Sende 10 ADA an Adresse abc123...\"\n"
            "   \"Überweise 5 ADA an xyz789...\"\n\n"
            "Sie können mir eine Textnachricht senden oder eine Sprachnachricht aufnehmen."
        )
        
    async def balance_command(self, update: Update, context: CallbackContext) -> None:
        """Zeigt den Kontostand an."""
        user_id = update.effective_user.id
        
        if AUTHORIZED_USERS and user_id not in AUTHORIZED_USERS:
            return
            
        await update.message.reply_text("Prüfe deinen Kontostand...")
        
        balance_info = self.cardano_manager.check_wallet_balance()
        
        if "error" in balance_info:
            await update.message.reply_text(f"Fehler: {balance_info['error']}")
            return
            
        await update.message.reply_text(
            f"Dein Kontostand:\n\n"
            f"🏦 *{balance_info['balance_ada']:.6f} ADA*\n"
            f"📝 Adresse: `{balance_info['address']}`",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_text(self, update: Update, context: CallbackContext) -> None:
        """Verarbeitet Textnachrichten."""
        user_id = update.effective_user.id
        
        if AUTHORIZED_USERS and user_id not in AUTHORIZED_USERS:
            return
            
        text = update.message.text
        await self.process_command(update, context, text)
    
    async def handle_voice(self, update: Update, context: CallbackContext) -> None:
        """Verarbeitet Sprachnachrichten."""
        user_id = update.effective_user.id
        
        if AUTHORIZED_USERS and user_id not in AUTHORIZED_USERS:
            return
        
        await update.message.reply_text("Verarbeite deine Sprachnachricht...")
        
        # Sprachnachricht herunterladen
        voice_file = await self.audio_processor.download_voice_message(update.message.voice)
        
        if not voice_file:
            await update.message.reply_text("Fehler beim Herunterladen der Sprachnachricht.")
            return
            
        # Sprachnachricht transkribieren
        transcript = await self.audio_processor.process_voice_message(voice_file)
        
        if not transcript:
            await update.message.reply_text("Konnte deine Sprachnachricht nicht verstehen.")
            return
            
        await update.message.reply_text(f"Ich habe verstanden: \"{transcript}\"")
        
        # Befehl verarbeiten
        await self.process_command(update, context, transcript)
    
    async def process_command(self, update: Update, context: CallbackContext, text: str) -> int:
        """Verarbeitet einen Befehl (Text oder transkribierte Sprache)."""
        parsed_intent = self.intent_parser.parse(text)
        
        intent = parsed_intent.get('intent')
        entities = parsed_intent.get('entities', {})
        
        if intent == 'check_balance':
            await self.balance_command(update, context)
            
        elif intent == 'help':
            await self.help_command(update, context)
            
        elif intent == 'send_ada':
            amount = entities.get('amount')
            recipient = entities.get('recipient_address')
            
            if not amount or not recipient:
                await update.message.reply_text(
                    "Ich konnte entweder den Betrag oder die Empfängeradresse nicht verstehen. "
                    "Bitte versuche es noch einmal."
                )
                return ConversationHandler.END
                
            # Transaktion zur Bestätigung speichern
            self.pending_transaction = {
                'user_id': update.effective_user.id,
                'amount': amount,
                'recipient': recipient
            }
            
            # Bestätigung anfordern
            await update.message.reply_text(
                f"Möchtest du *{amount} ADA* an die Adresse `{recipient}` senden?\n\n"
                f"Antworte mit 'ja' oder 'nein'.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            return CONFIRM
            
        elif intent == 'unknown':
            await update.message.reply_text(
                "Entschuldigung, ich habe deine Anfrage nicht verstanden. "
                "Versuche es bitte mit einem anderen Befehl oder frage nach Hilfe."
            )
            
        return ConversationHandler.END
    
    async def confirm_transaction(self, update: Update, context: CallbackContext) -> int:
        """Bestätigt eine Transaktion."""
        user_id = update.effective_user.id
        
        if not self.pending_transaction or self.pending_transaction.get('user_id') != user_id:
            await update.message.reply_text("Keine ausstehende Transaktion gefunden.")
            return ConversationHandler.END
            
        text = update.message.text.lower()
        
        if text in ['ja', 'yes', 'y', 'bestätigen', 'bestätige']:
            amount = self.pending_transaction.get('amount')
            recipient = self.pending_transaction.get('recipient')
            
            await update.message.reply_text(f"Führe Transaktion aus: {amount} ADA an {recipient}...")
            
            # Transaktion ausführen
            result = self.cardano_manager.send_ada(recipient, amount)
            
            if "error" in result:
                await update.message.reply_text(f"❌ Fehler: {result['error']}")
            else:
                await update.message.reply_text(
                    f"✅ *Transaktion erfolgreich*\n\n"
                    f"🔸 Betrag: *{amount} ADA*\n"
                    f"🔸 Empfänger: `{recipient}`\n\n"
                    f"_Netzwerk: {result['transaction_details']['network']}_",
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            await update.message.reply_text("Transaktion abgebrochen.")
            
        # Transaktion zurücksetzen
        self.pending_transaction = {}
        
        return ConversationHandler.END
    
    async def cancel(self, update: Update, context: CallbackContext) -> int:
        """Bricht den Konversationsstatus ab."""
        await update.message.reply_text("Vorgang abgebrochen.")
        return ConversationHandler.END
        
    def run(self):
        """Startet den Bot."""
        # Create the Updater and pass it your bot's token.
        updater = Updater(TELEGRAM_BOT_TOKEN)

        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher

        # Gespräch zur Transaktionsbestätigung
        conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(Filters.text & ~Filters.command, self.handle_text),
                MessageHandler(Filters.voice, self.handle_voice),
            ],
            states={
                CONFIRM: [MessageHandler(Filters.text & ~Filters.command, self.confirm_transaction)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        # Befehle registrieren
        dispatcher.add_handler(CommandHandler("start", self.start))
        dispatcher.add_handler(CommandHandler("help", self.help_command))
        dispatcher.add_handler(CommandHandler("balance", self.balance_command))
        dispatcher.add_handler(conv_handler)

        # Starte den Bot
        updater.start_polling()
        updater.idle()


def main():
    """Hauptfunktion."""
    # Prüfe, ob Telegram-Bot-Token konfiguriert ist
    if not TELEGRAM_BOT_TOKEN:
        print("FEHLER: Telegram-Bot-Token ist nicht konfiguriert.")
        print("Bitte setze die Umgebungsvariable TELEGRAM_BOT_TOKEN.")
        return
        
    # Prüfe, ob OpenAI API-Key konfiguriert ist
    if not os.getenv("OPENAI_API_KEY"):
        print("FEHLER: OpenAI API-Key ist nicht konfiguriert.")
        print("Bitte setze die Umgebungsvariable OPENAI_API_KEY.")
        return
        
    # Prüfe, ob Blockfrost-Projekt-ID konfiguriert ist
    if not os.getenv("BLOCKFROST_PROJECT_ID"):
        print("WARNUNG: Blockfrost-Projekt-ID ist nicht konfiguriert.")
        print("Cardano-Transaktionen werden nicht funktionieren.")

    print("Starte Cardano Voice Assistant Bot...")
    assistant = CardanoVoiceAssistant()
    assistant.run()


if __name__ == '__main__':
    main() 
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler

from config import TELEGRAM_BOT_TOKEN, AUTHORIZED_USERS, DEFAULT_NETWORK
from intent_parser import IntentParser
from cardano_transaction import CardanoTransactionManager
from cardano_wallet import CardanoWalletManager
from telegram_audio import TelegramAudioProcessor

# Logging einrichten
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Konversationsstatus
CONFIRM = 1
CREATE_WALLET = 2
SELECT_NETWORK = 3

class CardanoVoiceAssistant:
    def __init__(self):
        self.intent_parser = IntentParser()
        self.cardano_manager = CardanoTransactionManager(DEFAULT_NETWORK)
        self.wallet_manager = CardanoWalletManager()
        self.audio_processor = TelegramAudioProcessor()
        
        # Transaktion die auf Bestätigung wartet
        self.pending_transaction = {}
        
        # Benutzereinstellungen
        self.user_settings = {}
        
    def get_user_network(self, user_id):
        """Gibt das aktuelle Netzwerk für einen Benutzer zurück."""
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {"network": DEFAULT_NETWORK}
        return self.user_settings[user_id]["network"]
    
    def set_user_network(self, user_id, network):
        """Setzt das Netzwerk für einen Benutzer."""
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {}
        self.user_settings[user_id]["network"] = network
        
    async def start(self, update: Update, context: CallbackContext) -> None:
        """Startet den Bot und sendet eine Begrüßungsnachricht."""
        user_id = update.effective_user.id
        
        if AUTHORIZED_USERS and user_id not in AUTHORIZED_USERS:
            await update.message.reply_text(
                "Sie sind nicht berechtigt, diesen Bot zu verwenden."
            )
            return
        
        # Standardnetzwerk setzen
        self.set_user_network(user_id, DEFAULT_NETWORK)
        
        await update.message.reply_text(
            f"Willkommen zum Cardano Sprachassistenten, {update.effective_user.first_name}!\n\n"
            "Ich kann Ihnen helfen, Cardano-Transaktionen per Sprachbefehl auszuführen.\n\n"
            "Hier sind einige Dinge, die Sie sagen können:\n"
            "- \"Wie viel ADA habe ich?\"\n"
            "- \"Sende 5 ADA an Adresse abc123...\"\n"
            "- \"Hilfe\"\n\n"
            "Sie können mir eine Textnachricht senden oder eine Sprachnachricht aufnehmen.\n\n"
            "Befehle:\n"
            "/wallet - Wallet-Verwaltung\n"
            "/network - Netzwerk wechseln\n"
            "/balance - Kontostand abfragen"
        )
        
    async def help_command(self, update: Update, context: CallbackContext) -> None:
        """Hilfebefehl"""
        user_id = update.effective_user.id
        
        if AUTHORIZED_USERS and user_id not in AUTHORIZED_USERS:
            return
            
        network = self.get_user_network(user_id)
        
        await update.message.reply_text(
            "Ich verstehe folgende Befehle:\n\n"
            "1. Kontostand abfragen:\n"
            "   \"Wie viel ADA habe ich?\"\n"
            "   \"Zeige meinen Kontostand\"\n\n"
            "2. ADA senden:\n"
            "   \"Sende 10 ADA an Adresse abc123...\"\n"
            "   \"Überweise 5 ADA an xyz789...\"\n\n"
            "Verfügbare Befehle:\n"
            "/wallet - Wallet-Verwaltung\n"
            "/network - Netzwerk wechseln (aktuell: " + network + ")\n"
            "/balance - Kontostand abfragen\n\n"
            "Sie können mir eine Textnachricht senden oder eine Sprachnachricht aufnehmen."
        )
        
    async def wallet_command(self, update: Update, context: CallbackContext) -> None:
        """Wallet-Verwaltung."""
        user_id = update.effective_user.id
        
        if AUTHORIZED_USERS and user_id not in AUTHORIZED_USERS:
            return
        
        network = self.get_user_network(user_id)
        
        # Vorhandene Wallets anzeigen
        wallets = self.wallet_manager.get_user_wallets(user_id, network)
        
        keyboard = [
            [InlineKeyboardButton("➕ Neue Wallet erstellen", callback_data="create_wallet")]
        ]
        
        for wallet in wallets:
            wallet_name = wallet["name"]
            keyboard.append([InlineKeyboardButton(
                f"🔑 {wallet_name} - {wallet['address'][:8]}...{wallet['address'][-8:]}",
                callback_data=f"select_wallet_{wallet_name}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Wallet-Verwaltung ({network}):\n\n"
            f"Sie haben {len(wallets)} Wallet(s) für dieses Netzwerk.\n"
            "Wählen Sie eine Option:",
            reply_markup=reply_markup
        )
        
    async def network_command(self, update: Update, context: CallbackContext) -> None:
        """Netzwerk wechseln."""
        user_id = update.effective_user.id
        
        if AUTHORIZED_USERS and user_id not in AUTHORIZED_USERS:
            return
        
        current_network = self.get_user_network(user_id)
        
        keyboard = [
            [InlineKeyboardButton("🔵 Testnet", callback_data="network_testnet")],
            [InlineKeyboardButton("🔴 Mainnet", callback_data="network_mainnet")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Aktuelles Netzwerk: *{current_network}*\n\n"
            "Wählen Sie das gewünschte Netzwerk:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    async def balance_command(self, update: Update, context: CallbackContext) -> None:
        """Zeigt den Kontostand an."""
        user_id = update.effective_user.id
        
        if AUTHORIZED_USERS and user_id not in AUTHORIZED_USERS:
            return
        
        network = self.get_user_network(user_id)
        
        # Setze das richtige Netzwerk
        if self.cardano_manager.network != network:
            self.cardano_manager.connect_to_network(network)
        
        # Hole die Standard-Wallet für den Benutzer
        wallet = self.wallet_manager.get_default_wallet(user_id, network)
        
        if not wallet:
            await update.message.reply_text(
                f"Sie haben noch keine Wallet für {network}.\n"
                "Erstellen Sie zuerst eine Wallet mit /wallet"
            )
            return
            
        await update.message.reply_text(f"Prüfe deinen Kontostand auf {network}...")
        
        balance_info = self.cardano_manager.check_wallet_balance(wallet["address"])
        
        if "error" in balance_info:
            await update.message.reply_text(f"Fehler: {balance_info['error']}")
            return
            
        await update.message.reply_text(
            f"Dein Kontostand ({network}):\n\n"
            f"🏦 *{balance_info['balance_ada']:.6f} ADA*\n"
            f"🔑 Wallet: *{wallet['name']}*\n"
            f"📝 Adresse: `{wallet['address']}`",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def button_callback(self, update: Update, context: CallbackContext) -> int:
        """Callback für Inline-Buttons."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == "create_wallet":
            await query.edit_message_text(
                "Geben Sie einen Namen für Ihre neue Wallet ein (oder 'abbrechen'):"
            )
            return CREATE_WALLET
        
        elif data.startswith("select_wallet_"):
            wallet_name = data[14:]  # Extrahiere den Wallet-Namen
            network = self.get_user_network(user_id)
            wallet = self.wallet_manager.get_wallet(user_id, network, wallet_name)
            
            if not wallet:
                await query.edit_message_text(f"Wallet {wallet_name} nicht gefunden.")
                return ConversationHandler.END
            
            # Setze das richtige Netzwerk
            if self.cardano_manager.network != network:
                self.cardano_manager.connect_to_network(network)
            
            balance_info = self.cardano_manager.check_wallet_balance(wallet["address"])
            
            if "error" in balance_info:
                balance_text = "Kontostand konnte nicht abgerufen werden."
            else:
                balance_text = f"{balance_info['balance_ada']:.6f} ADA"
            
            await query.edit_message_text(
                f"Wallet: *{wallet_name}*\n"
                f"Netzwerk: *{network}*\n"
                f"Adresse: `{wallet['address']}`\n"
                f"Kontostand: *{balance_text}*",
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif data.startswith("network_"):
            new_network = data[8:]  # testnet oder mainnet
            old_network = self.get_user_network(user_id)
            
            if new_network != old_network:
                self.set_user_network(user_id, new_network)
                success = self.cardano_manager.connect_to_network(new_network)
                
                if success:
                    await query.edit_message_text(
                        f"Netzwerk auf *{new_network}* umgestellt.\n\n"
                        f"Verwenden Sie /wallet, um Ihre Wallets für dieses Netzwerk zu verwalten.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await query.edit_message_text(
                        f"Fehler beim Verbinden mit {new_network}.\n"
                        f"Stellen Sie sicher, dass Sie einen Blockfrost API-Schlüssel für {new_network} konfiguriert haben."
                    )
            else:
                await query.edit_message_text(
                    f"Sie sind bereits mit *{new_network}* verbunden.",
                    parse_mode=ParseMode.MARKDOWN
                )
        
        return ConversationHandler.END
    
    async def create_wallet_conversation(self, update: Update, context: CallbackContext) -> int:
        """Verarbeitet den Wallet-Namen bei der Erstellung."""
        user_id = update.effective_user.id
        wallet_name = update.message.text.strip()
        
        if wallet_name.lower() == 'abbrechen':
            await update.message.reply_text("Wallet-Erstellung abgebrochen.")
            return ConversationHandler.END
        
        network = self.get_user_network(user_id)
        
        # Erstelle die Wallet
        result = self.wallet_manager.create_wallet(user_id, network, wallet_name)
        
        if result["success"]:
            wallet = result["wallet"]
            await update.message.reply_text(
                f"✅ Wallet *{wallet_name}* erfolgreich erstellt!\n\n"
                f"Netzwerk: *{network}*\n"
                f"Adresse: `{wallet['address']}`\n\n"
                f"Verwenden Sie /balance, um Ihren Kontostand zu prüfen.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                f"❌ Fehler bei der Wallet-Erstellung: {result.get('error', 'Unbekannter Fehler')}"
            )
        
        return ConversationHandler.END
    
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
        user_id = update.effective_user.id
        network = self.get_user_network(user_id)
        
        # Stelle sicher, dass wir das richtige Netzwerk verwenden
        if self.cardano_manager.network != network:
            self.cardano_manager.connect_to_network(network)
        
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
            
            # Hole die Standard-Wallet für den Benutzer
            wallet = self.wallet_manager.get_default_wallet(user_id, network)
            
            if not wallet:
                await update.message.reply_text(
                    f"Sie haben noch keine Wallet für {network}.\n"
                    "Erstellen Sie zuerst eine Wallet mit /wallet"
                )
                return ConversationHandler.END
                
            # Transaktion zur Bestätigung speichern
            self.pending_transaction = {
                'user_id': update.effective_user.id,
                'wallet': wallet,
                'amount': amount,
                'recipient': recipient,
                'network': network
            }
            
            # Bestätigung anfordern
            await update.message.reply_text(
                f"Möchtest du *{amount} ADA* von Wallet *{wallet['name']}* an die Adresse `{recipient}` senden?\n\n"
                f"Netzwerk: *{network}*\n\n"
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
            wallet = self.pending_transaction.get('wallet')
            amount = self.pending_transaction.get('amount')
            recipient = self.pending_transaction.get('recipient')
            network = self.pending_transaction.get('network')
            
            # Stelle sicher, dass wir das richtige Netzwerk verwenden
            if self.cardano_manager.network != network:
                self.cardano_manager.connect_to_network(network)
            
            await update.message.reply_text(
                f"Führe Transaktion aus: {amount} ADA an {recipient}...\n"
                f"Netzwerk: {network}"
            )
            
            # Transaktion ausführen
            result = self.cardano_manager.send_ada(wallet, recipient, amount)
            
            if "error" in result:
                await update.message.reply_text(f"❌ Fehler: {result['error']}")
            else:
                await update.message.reply_text(
                    f"✅ *Transaktion erfolgreich*\n\n"
                    f"🔸 Betrag: *{amount} ADA*\n"
                    f"🔸 Von Wallet: *{wallet['name']}*\n"
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

        # Transaktions-Konversationshandler
        transaction_handler = ConversationHandler(
            entry_points=[
                MessageHandler(Filters.text & ~Filters.command, self.handle_text),
                MessageHandler(Filters.voice, self.handle_voice),
            ],
            states={
                CONFIRM: [MessageHandler(Filters.text & ~Filters.command, self.confirm_transaction)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        
        # Wallet-Erstellungs-Konversationshandler
        wallet_creation_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.button_callback, pattern=r'^create_wallet$')],
            states={
                CREATE_WALLET: [MessageHandler(Filters.text & ~Filters.command, self.create_wallet_conversation)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        # Befehle registrieren
        dispatcher.add_handler(CommandHandler("start", self.start))
        dispatcher.add_handler(CommandHandler("help", self.help_command))
        dispatcher.add_handler(CommandHandler("balance", self.balance_command))
        dispatcher.add_handler(CommandHandler("wallet", self.wallet_command))
        dispatcher.add_handler(CommandHandler("network", self.network_command))
        
        # Button-Callbacks
        dispatcher.add_handler(CallbackQueryHandler(self.button_callback, pattern=r'^(select_wallet_|network_)'))
        
        # Konversationshandler registrieren
        dispatcher.add_handler(wallet_creation_handler)
        dispatcher.add_handler(transaction_handler)

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
        
    # Prüfe, ob Blockfrost-Projekt-IDs konfiguriert sind
    if not os.getenv("BLOCKFROST_PROJECT_ID_TESTNET") and not os.getenv("BLOCKFROST_PROJECT_ID_MAINNET"):
        print("WARNUNG: Keine Blockfrost-Projekt-IDs konfiguriert.")
        print("Cardano-Transaktionen werden nicht funktionieren.")

    print("Starte Cardano Voice Assistant Bot...")
    assistant = CardanoVoiceAssistant()
    assistant.run()


if __name__ == '__main__':
    main() 
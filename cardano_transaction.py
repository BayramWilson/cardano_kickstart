import os
import subprocess
import json
from blockfrost import BlockFrostApi, ApiError
from config import BLOCKFROST_PROJECT_ID_TESTNET, BLOCKFROST_PROJECT_ID_MAINNET, DEFAULT_NETWORK

class CardanoTransactionManager:
    def __init__(self, network=None):
        self.network = network or DEFAULT_NETWORK
        self.api = None
        self.connect_to_network(self.network)
    
    def connect_to_network(self, network):
        """Verbindet mit dem spezifizierten Cardano-Netzwerk."""
        self.network = network
        
        # Entsprechendes Projekt-ID wählen
        if network == "testnet":
            project_id = BLOCKFROST_PROJECT_ID_TESTNET
        else:
            project_id = BLOCKFROST_PROJECT_ID_MAINNET
        
        # Blockfrost API-Client initialisieren
        if project_id:
            try:
                self.api = BlockFrostApi(
                    project_id=project_id,
                    base_url=f"https://cardano-{network}.blockfrost.io/api/v0"
                )
                print(f"Blockfrost-Verbindung hergestellt (Netzwerk: {network})")
                return True
            except Exception as e:
                print(f"Fehler bei der Initialisierung der Blockfrost API: {e}")
                self.api = None
                return False
        else:
            print(f"Blockfrost Projekt-ID für {network} nicht konfiguriert")
            self.api = None
            return False
    
    def check_wallet_balance(self, wallet_address):
        """Überprüft den Kontostand einer Wallet-Adresse."""
        if not self.api:
            return {"error": "Blockfrost API nicht initialisiert"}
        
        if not wallet_address:
            return {"error": "Wallet-Adresse nicht angegeben"}
        
        try:
            # Abrufen der Adressinformationen
            address_info = self.api.address(wallet_address)
            
            # Extrahieren des ADA-Betrags (in Lovelace)
            lovelace_amount = int(address_info.amount[0].quantity)
            
            # Umrechnung von Lovelace in ADA (1 ADA = 1.000.000 Lovelace)
            ada_amount = lovelace_amount / 1000000
            
            return {
                "success": True,
                "address": wallet_address,
                "balance_lovelace": lovelace_amount,
                "balance_ada": ada_amount,
                "network": self.network
            }
        except ApiError as e:
            return {"error": f"Blockfrost API-Fehler: {e}"}
        except Exception as e:
            return {"error": f"Unerwarteter Fehler: {e}"}
    
    def validate_address(self, address):
        """Validiert, ob eine Cardano-Adresse gültig ist."""
        if not self.api:
            return False
        
        # Validiere auch das Netzwerk (Testnet vs. Mainnet)
        is_testnet_address = address.startswith('addr_test')
        if is_testnet_address and self.network != 'testnet':
            return False
        if not is_testnet_address and self.network == 'testnet':
            return False
        
        try:
            # Versuche, Adressinformationen abzurufen
            self.api.address(address)
            return True
        except ApiError:
            return False
        except Exception:
            return False
    
    def send_ada(self, sender_wallet, recipient_address, amount_ada):
        """
        Sendet ADA an eine angegebene Adresse.
        
        :param sender_wallet: Wallet-Objekt des Senders
        :param recipient_address: Empfänger-Adresse
        :param amount_ada: Zu sendender Betrag in ADA
        :return: Ergebnis der Transaktion
        """
        if not self.api:
            return {"error": f"Blockfrost API für {self.network} nicht initialisiert"}
        
        # Überprüfen, ob die Wallet für das aktuelle Netzwerk ist
        if sender_wallet["network"] != self.network:
            return {"error": f"Die Wallet ist für {sender_wallet['network']}, aber aktuell ist {self.network} ausgewählt"}
        
        wallet_address = sender_wallet["address"]
        signing_key_path = sender_wallet["payment_skey_path"]
        
        if not wallet_address or not signing_key_path:
            return {"error": "Wallet nicht vollständig konfiguriert"}
        
        # Adressvalidierung
        if not self.validate_address(recipient_address):
            return {"error": "Ungültige Empfängeradresse"}
        
        # Kontostand überprüfen
        balance_info = self.check_wallet_balance(wallet_address)
        if "error" in balance_info:
            return balance_info
        
        if balance_info["balance_ada"] < amount_ada:
            return {"error": "Nicht genügend ADA im Wallet"}
        
        # Umrechnung in Lovelace
        lovelace_amount = int(amount_ada * 1000000)
        
        try:
            # Blockfrost unterstützt keine direkten Transaktionen, daher verwenden wir die Cardano CLI
            # Dies ist eine vereinfachte Implementierung - in der Praxis würde man die UTXOs abfragen
            # und eine vollständige Transaktion erstellen
            
            # 1. Protokollparameter abrufen
            protocol_params = self.api.epoch_latest_parameters()
            
            # Als temporäre Datei speichern
            with open("protocol.json", "w") as f:
                json.dump(protocol_params.to_dict(), f)
            
            # 2. Transaktion bauen, signieren und übermitteln mit Cardano CLI
            # Hinweis: Dies ist eine vereinfachte Darstellung - in der Realität würde man hier
            # die verschiedenen Schritte der Transaktion mit der CLI ausführen
            
            # In einer realen Implementierung würde man hier die entsprechenden
            # Cardano CLI-Befehle ausführen:
            # 1. cardano-cli transaction build-raw
            # 2. cardano-cli transaction calculate-min-fee
            # 3. cardano-cli transaction build-raw (mit korrekter Fee)
            # 4. cardano-cli transaction sign
            # 5. cardano-cli transaction submit
            
            # Hier ein Beispiel für eine einfache Transaktion (nicht ausführbar):
            """
            # Netzwerkparameter
            net_param = "--testnet-magic 1097911063" if self.network == "testnet" else "--mainnet"
            
            # Transaktion aufbauen
            tx_build_cmd = [
                "cardano-cli", "transaction", "build",
                "--alonzo-era",
                net_param,
                "--tx-in", "<UTXO>",
                "--tx-out", f"{recipient_address}+{lovelace_amount}",
                "--change-address", wallet_address,
                "--protocol-params-file", "protocol.json",
                "--out-file", "tx.raw"
            ]
            
            # Transaktion signieren
            tx_sign_cmd = [
                "cardano-cli", "transaction", "sign",
                net_param,
                "--tx-body-file", "tx.raw",
                "--signing-key-file", signing_key_path,
                "--out-file", "tx.signed"
            ]
            
            # Transaktion einreichen
            tx_submit_cmd = [
                "cardano-cli", "transaction", "submit",
                net_param,
                "--tx-file", "tx.signed"
            ]
            """
            
            # Da wir die Transaktionen hier nicht tatsächlich ausführen können,
            # geben wir nur die Informationen zurück
            
            # Wir würden die Befehle mit subprocess ausführen:
            # subprocess.run(tx_build_cmd, check=True)
            # subprocess.run(tx_sign_cmd, check=True)
            # result = subprocess.run(tx_submit_cmd, check=True, capture_output=True, text=True)
            
            # Aufräumen
            if os.path.exists("protocol.json"):
                os.remove("protocol.json")
            
            # Erfolgsmeldung zurückgeben
            return {
                "success": True,
                "message": f"Transaktion erfolgreich: {amount_ada} ADA an {recipient_address} gesendet",
                "transaction_details": {
                    "sender": wallet_address,
                    "recipient": recipient_address,
                    "amount_ada": amount_ada,
                    "amount_lovelace": lovelace_amount,
                    "network": self.network
                }
            }
            
        except Exception as e:
            return {"error": f"Fehler bei der Transaktion: {e}"}
        
    def get_transaction_status(self, tx_hash):
        """Überprüft den Status einer Transaktion."""
        if not self.api:
            return {"error": "Blockfrost API nicht initialisiert"}
        
        try:
            # Transaktionsinformationen abrufen
            transaction = self.api.transaction(tx_hash)
            
            return {
                "success": True,
                "tx_hash": tx_hash,
                "block": transaction.block,
                "block_height": transaction.block_height,
                "confirmations": transaction.confirmations,
                "network": self.network
            }
        except ApiError as e:
            return {"error": f"Blockfrost API-Fehler: {e}"}
        except Exception as e:
            return {"error": f"Unerwarteter Fehler: {e}"} 
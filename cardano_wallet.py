import os
import json
import subprocess
import random
import string
from pathlib import Path
from config import USER_DATA_DIR

class CardanoWalletManager:
    def __init__(self):
        """Initialisiert den Wallet-Manager und erstellt das Basisverzeichnis."""
        self.user_data_dir = Path(USER_DATA_DIR)
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_user_dir(self, user_id):
        """Gibt das Verzeichnis für einen bestimmten Benutzer zurück."""
        user_dir = self.user_data_dir / str(user_id)
        user_dir.mkdir(exist_ok=True)
        return user_dir
    
    def _get_network_dir(self, user_id, network):
        """Gibt das Verzeichnis für das Netzwerk eines Benutzers zurück."""
        network_dir = self._get_user_dir(user_id) / network
        network_dir.mkdir(exist_ok=True)
        return network_dir
    
    def get_user_wallets(self, user_id, network):
        """
        Gibt alle Wallets eines Benutzers für ein bestimmtes Netzwerk zurück.
        
        :param user_id: Telegram-Benutzer-ID
        :param network: 'testnet' oder 'mainnet'
        :return: Liste der verfügbaren Wallets
        """
        network_dir = self._get_network_dir(user_id, network)
        wallets = []
        
        try:
            wallet_files = list(network_dir.glob("*.wallet"))
            for wallet_file in wallet_files:
                try:
                    with open(wallet_file, 'r') as f:
                        wallet_data = json.load(f)
                        wallets.append(wallet_data)
                except (json.JSONDecodeError, IOError):
                    continue
        except Exception as e:
            print(f"Fehler beim Lesen der Wallets: {e}")
        
        return wallets
    
    def create_wallet(self, user_id, network, wallet_name=None):
        """
        Erstellt eine neue Cardano-Wallet für einen Benutzer.
        
        :param user_id: Telegram-Benutzer-ID
        :param network: 'testnet' oder 'mainnet'
        :param wallet_name: Optionaler Name für die Wallet
        :return: Wallet-Daten oder Fehler
        """
        network_dir = self._get_network_dir(user_id, network)
        
        # Generiere einen zufälligen Namen, wenn keiner angegeben ist
        if not wallet_name:
            rand_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            wallet_name = f"wallet_{rand_suffix}"
        
        # Sanitize wallet_name
        wallet_name = ''.join(c for c in wallet_name if c.isalnum() or c in '-_')
        
        # Pfade für die Wallet-Dateien
        payment_vkey = network_dir / f"{wallet_name}.payment.vkey"
        payment_skey = network_dir / f"{wallet_name}.payment.skey"
        payment_addr = network_dir / f"{wallet_name}.payment.addr"
        wallet_file = network_dir / f"{wallet_name}.wallet"
        
        try:
            # Simulieren wir hier die Erstellung einer Cardano-Wallet
            # In einer echten Implementierung würden wir cardano-cli verwenden
            
            # Im Produktionseinsatz würde man cardano-cli Befehle ausführen:
            # 1. Zahlungsschlüsselpaar generieren
            # cmd = [
            #     "cardano-cli", "address", "key-gen",
            #     "--verification-key-file", str(payment_vkey),
            #     "--signing-key-file", str(payment_skey)
            # ]
            # subprocess.run(cmd, check=True)
            
            # 2. Zahlungsadresse generieren
            # net_param = "--testnet-magic 1097911063" if network == "testnet" else "--mainnet"
            # cmd = [
            #     "cardano-cli", "address", "build",
            #     "--payment-verification-key-file", str(payment_vkey),
            #     net_param,
            #     "--out-file", str(payment_addr)
            # ]
            # subprocess.run(cmd, check=True)
            
            # 3. Adresse aus der Datei lesen
            # with open(payment_addr, 'r') as f:
            #     address = f.read().strip()
            
            # Für Demonstrationszwecke erstellen wir simulierte Schlüsseldateien
            with open(payment_vkey, 'w') as f:
                f.write(json.dumps({"type": "PaymentVerificationKeyShelley_ed25519", 
                                   "description": "Payment Verification Key", 
                                   "cborHex": "5820" + "".join(random.choices("0123456789abcdef", k=64))}))
            
            with open(payment_skey, 'w') as f:
                f.write(json.dumps({"type": "PaymentSigningKeyShelley_ed25519", 
                                   "description": "Payment Signing Key", 
                                   "cborHex": "5820" + "".join(random.choices("0123456789abcdef", k=64))}))
            
            # Generiere eine simulierte Adresse
            if network == "testnet":
                prefix = "addr_test1"
            else:
                prefix = "addr1"
                
            # Simulierte Adresse - in der realen Implementierung wird die tatsächliche Adresse verwendet
            address = prefix + "".join(random.choices("qpzry9x8gf2tvdw0s3jn54khce6mua7l", k=50))
            
            with open(payment_addr, 'w') as f:
                f.write(address)
            
            # Wallet-Metadaten speichern
            wallet_data = {
                "name": wallet_name,
                "network": network,
                "address": address,
                "payment_vkey_path": str(payment_vkey),
                "payment_skey_path": str(payment_skey),
                "payment_addr_path": str(payment_addr),
                "balance": 0,  # Anfangsstand (in Lovelace)
                "created_at": str(Path.ctime(Path.cwd()))
            }
            
            with open(wallet_file, 'w') as f:
                json.dump(wallet_data, f, indent=2)
            
            return {
                "success": True,
                "wallet": wallet_data
            }
            
        except Exception as e:
            print(f"Fehler bei der Wallet-Erstellung: {e}")
            # Aufräumen im Fehlerfall
            for file in [payment_vkey, payment_skey, payment_addr, wallet_file]:
                if file.exists():
                    file.unlink()
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_wallet(self, user_id, network, wallet_name):
        """
        Gibt Informationen zu einer spezifischen Wallet zurück.
        
        :param user_id: Telegram-Benutzer-ID
        :param network: 'testnet' oder 'mainnet'
        :param wallet_name: Name der Wallet
        :return: Wallet-Daten oder None, wenn nicht gefunden
        """
        network_dir = self._get_network_dir(user_id, network)
        wallet_file = network_dir / f"{wallet_name}.wallet"
        
        if not wallet_file.exists():
            return None
        
        try:
            with open(wallet_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Lesen der Wallet {wallet_name}: {e}")
            return None
    
    def get_default_wallet(self, user_id, network):
        """
        Gibt die Standard-Wallet für einen Benutzer zurück oder erstellt eine, falls keine existiert.
        
        :param user_id: Telegram-Benutzer-ID
        :param network: 'testnet' oder 'mainnet'
        :return: Standard-Wallet oder neu erstellte Wallet
        """
        wallets = self.get_user_wallets(user_id, network)
        
        if wallets:
            # Verwende die erste Wallet als Standard
            return wallets[0]
        else:
            # Erstelle eine neue Wallet, wenn keine existiert
            result = self.create_wallet(user_id, network, "default")
            if result["success"]:
                return result["wallet"]
            else:
                return None
    
    def delete_wallet(self, user_id, network, wallet_name):
        """
        Löscht eine Wallet eines Benutzers.
        
        :param user_id: Telegram-Benutzer-ID
        :param network: 'testnet' oder 'mainnet'
        :param wallet_name: Name der Wallet
        :return: Erfolg oder Fehler
        """
        network_dir = self._get_network_dir(user_id, network)
        
        try:
            # Lösche alle Wallet-bezogenen Dateien
            for ext in [".wallet", ".payment.vkey", ".payment.skey", ".payment.addr"]:
                file_path = network_dir / f"{wallet_name}{ext}"
                if file_path.exists():
                    file_path.unlink()
            
            return {
                "success": True,
                "message": f"Wallet {wallet_name} erfolgreich gelöscht"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Fehler beim Löschen der Wallet: {e}"
            } 
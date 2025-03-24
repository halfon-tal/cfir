from pqcrypto.kem.kyber512 import generate_keypair, encrypt, decrypt
import base64

class QuantumEncryption:
    @staticmethod
    def generate_kyber_keypair():
        """Generate a Kyber public/private key pair."""
        public_key, private_key = generate_keypair()
        return {
            'public_key': base64.b64encode(public_key).decode('utf-8'),
            'private_key': base64.b64encode(private_key).decode('utf-8')
        }

    @staticmethod
    def encrypt_data(public_key: str, plaintext: str):
        """Encrypt data using Kyber public key."""
        decoded_public_key = base64.b64decode(public_key)
        ciphertext, shared_secret = encrypt(decoded_public_key)
        return {
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'shared_secret': base64.b64encode(shared_secret).decode('utf-8')
        }

    @staticmethod
    def decrypt_data(private_key: str, ciphertext: str):
        """Decrypt data using Kyber private key."""
        decoded_private_key = base64.b64decode(private_key)
        decoded_ciphertext = base64.b64decode(ciphertext)
        return decrypt(decoded_private_key, decoded_ciphertext) 
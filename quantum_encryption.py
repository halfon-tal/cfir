from pqcrypto.kem.kyber512 import generate_keypair, encrypt, decrypt
import base64

class QuantumEncryption:
    @staticmethod
    def generate_kyber_keypair():
        """Generate a Kyber public/private key pair."""
        try:
            public_key, private_key = generate_keypair()
            # Convert keys to base64 for easier storage/transmission
            return {
                'public_key': base64.b64encode(public_key).decode('utf-8'),
                'private_key': base64.b64encode(private_key).decode('utf-8')
            }
        except Exception as e:
            raise Exception(f"Failed to generate keypair: {str(e)}")

    @staticmethod
    def encrypt_data(public_key, plaintext):
        """
        Encrypt data using Kyber public key.
        
        Args:
            public_key (str): Base64 encoded public key
            plaintext (str): Data to encrypt
        
        Returns:
            dict: Contains ciphertext and shared_secret
        """
        try:
            # Decode the base64 public key
            decoded_public_key = base64.b64decode(public_key)
            
            # Convert plaintext to bytes if it's not already
            if isinstance(plaintext, str):
                plaintext = plaintext.encode('utf-8')
            
            # Generate ciphertext and shared secret
            ciphertext, shared_secret = encrypt(decoded_public_key)
            
            return {
                'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
                'shared_secret': base64.b64encode(shared_secret).decode('utf-8')
            }
        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")

    @staticmethod
    def decrypt_data(private_key, ciphertext):
        """
        Decrypt data using Kyber private key.
        
        Args:
            private_key (str): Base64 encoded private key
            ciphertext (str): Base64 encoded ciphertext
            
        Returns:
            bytes: Decrypted shared secret
        """
        try:
            # Decode the base64 private key and ciphertext
            decoded_private_key = base64.b64decode(private_key)
            decoded_ciphertext = base64.b64decode(ciphertext)
            
            # Decrypt to get shared secret
            shared_secret = decrypt(decoded_private_key, decoded_ciphertext)
            
            return base64.b64encode(shared_secret).decode('utf-8')
        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}") 
from quantum_encryption import QuantumEncryption

def main():
    # Generate keypair
    keys = QuantumEncryption.generate_kyber_keypair()
    print("Generated Keys:")
    print(f"Public Key: {keys['public_key'][:32]}...")
    print(f"Private Key: {keys['private_key'][:32]}...")

    # Example data to encrypt
    message = "Secret quantum data"
    
    # Encrypt the data
    encrypted = QuantumEncryption.encrypt_data(keys['public_key'], message)
    print("\nEncrypted Data:")
    print(f"Ciphertext: {encrypted['ciphertext'][:32]}...")
    print(f"Shared Secret: {encrypted['shared_secret'][:32]}...")

    # Decrypt the data
    decrypted_secret = QuantumEncryption.decrypt_data(
        keys['private_key'], 
        encrypted['ciphertext']
    )
    print("\nDecrypted Shared Secret:")
    print(f"Secret: {decrypted_secret[:32]}...")

if __name__ == "__main__":
    main() 
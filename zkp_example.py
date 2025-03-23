import logging
import time
from zkp_auth import (
    Entity, 
    ZeroKnowledgeAuthenticator,
    AuthenticationError,
    RateLimitExceeded,
    ChallengeExpired
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configure audit logging
audit_logger = logging.getLogger("zkp_audit")
audit_handler = logging.FileHandler("zkp_audit.log")
audit_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
)
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)

def demonstrate_successful_auth():
    """Demonstrate successful ZKP authentication."""
    try:
        # Create an entity with a secret credential
        entity = Entity(
            "Alice", 
            "secret_password_123",
            max_attempts=5,
            attempt_window=300
        )
        
        # Create verifier
        verifier = ZeroKnowledgeAuthenticator(
            "different_secret",
            max_attempts=5,
            attempt_window=300,
            challenge_timeout=30
        )
        
        print("\nSuccessful Authentication Demo:")
        
        # Get entity's public commitment
        public_commitment = entity.get_public_commitment()
        print(f"Public Commitment: {public_commitment[:16]}...")
        
        # Simulate client IP
        client_ip = "192.168.1.100"
        
        # Verifier generates challenge
        challenge = verifier.generate_challenge(client_ip)
        print(f"Challenge Number: {challenge.challenge_number}")
        
        # Entity generates proof
        proof = entity.prove_identity(challenge)
        print(f"Generated Proof: {proof.proof_hash[:16]}...")
        
        # Verify the proof
        is_valid = verifier.verify_proof(
            proof, 
            challenge, 
            public_commitment,
            client_ip
        )
        print(f"Proof Verified: {is_valid}")
        
    except AuthenticationError as e:
        print(f"Authentication failed: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

def demonstrate_rate_limiting():
    """Demonstrate rate limiting."""
    entity = Entity("Bob", "test_password", max_attempts=3, attempt_window=5)
    verifier = ZeroKnowledgeAuthenticator(
        "verifier_secret",
        max_attempts=3,
        attempt_window=5
    )
    
    print("\nRate Limiting Demo:")
    client_ip = "192.168.1.101"
    
    try:
        # Attempt multiple authentications quickly
        for i in range(4):
            print(f"\nAttempt {i + 1}:")
            challenge = verifier.generate_challenge(client_ip)
            proof = entity.prove_identity(challenge)
            verifier.verify_proof(
                proof,
                challenge,
                entity.get_public_commitment(),
                client_ip
            )
            
    except RateLimitExceeded as e:
        print(f"Rate limit working as expected: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

def demonstrate_challenge_expiry():
    """Demonstrate challenge expiry."""
    entity = Entity("Charlie", "test_password")
    verifier = ZeroKnowledgeAuthenticator(
        "verifier_secret",
        challenge_timeout=2
    )
    
    print("\nChallenge Expiry Demo:")
    client_ip = "192.168.1.102"
    
    try:
        challenge = verifier.generate_challenge(client_ip)
        print("Waiting for challenge to expire...")
        time.sleep(3)
        
        proof = entity.prove_identity(challenge)
        verifier.verify_proof(
            proof,
            challenge,
            entity.get_public_commitment(),
            client_ip
        )
        
    except ChallengeExpired as e:
        print(f"Challenge expiry working as expected: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

def main():
    demonstrate_successful_auth()
    demonstrate_rate_limiting()
    demonstrate_challenge_expiry()

if __name__ == "__main__":
    main() 
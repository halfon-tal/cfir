import hashlib
import random
import secrets
import time
from typing import Dict, Tuple, Optional
import logging
from dataclasses import dataclass
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidKey
import base64
from datetime import datetime, timedelta
from collections import defaultdict

@dataclass
class ProofChallenge:
    """Challenge data for ZKP verification."""
    challenge_number: int
    nonce: str
    timestamp: float
    expiry: float  # Challenge expiry time in seconds

@dataclass
class ProofResponse:
    """Response data containing proof."""
    proof_hash: str
    nonce: str
    timestamp: float

class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    pass

class RateLimitExceeded(AuthenticationError):
    """Raised when rate limit is exceeded."""
    pass

class ChallengeExpired(AuthenticationError):
    """Raised when challenge has expired."""
    pass

class ZeroKnowledgeAuthenticator:
    def __init__(
        self, 
        secret_credential: str,
        max_attempts: int = 5,
        attempt_window: int = 300,  # 5 minutes
        challenge_timeout: int = 30  # 30 seconds
    ):
        """
        Initialize ZKP authenticator with enhanced security.
        
        Args:
            secret_credential: The secret credential
            max_attempts: Maximum authentication attempts per window
            attempt_window: Time window for rate limiting (seconds)
            challenge_timeout: Challenge expiry time (seconds)
        """
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"static_salt",  # In production, use a unique salt per user
            iterations=100000,
        )
        self.secret_key = base64.b64encode(
            kdf.derive(secret_credential.encode())
        )
        
        # Create public commitment
        self.commitment = self._hash(self.secret_key)
        
        # Rate limiting
        self.max_attempts = max_attempts
        self.attempt_window = attempt_window
        self.challenge_timeout = challenge_timeout
        self.attempt_log = defaultdict(list)  # IP -> list of timestamps
        
        # Audit logging
        self.logger = logging.getLogger(__name__)
        self.audit_logger = logging.getLogger("zkp_audit")
        
        # Challenge tracking
        self.active_challenges: Dict[str, ProofChallenge] = {}
        
    def _hash(self, *values: bytes) -> str:
        """
        Create a cryptographically secure hash.
        
        Args:
            values: Values to hash together
            
        Returns:
            str: Resulting hash
        """
        hasher = hashlib.blake2b(digest_size=32)
        for value in values:
            if isinstance(value, str):
                value = value.encode()
            hasher.update(value)
        return base64.b64encode(hasher.digest()).decode()
        
    def _check_rate_limit(self, ip_address: str) -> None:
        """
        Check if rate limit is exceeded for an IP.
        
        Args:
            ip_address: IP address to check
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        now = time.time()
        recent_attempts = [
            t for t in self.attempt_log[ip_address] 
            if t > now - self.attempt_window
        ]
        
        if len(recent_attempts) >= self.max_attempts:
            self.audit_logger.warning(
                f"Rate limit exceeded for IP: {ip_address}"
            )
            raise RateLimitExceeded(
                f"Maximum attempts ({self.max_attempts}) exceeded. "
                f"Please try again in {self.attempt_window} seconds."
            )
            
        self.attempt_log[ip_address] = recent_attempts + [now]
        
    def generate_challenge(self, ip_address: str) -> ProofChallenge:
        """
        Generate a time-limited challenge for verification.
        
        Args:
            ip_address: IP address requesting the challenge
            
        Returns:
            ProofChallenge: Challenge data
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        self._check_rate_limit(ip_address)
        
        now = time.time()
        challenge = ProofChallenge(
            challenge_number=random.randint(1, 1000000),
            nonce=secrets.token_urlsafe(32),
            timestamp=now,
            expiry=now + self.challenge_timeout
        )
        
        self.active_challenges[challenge.nonce] = challenge
        self.audit_logger.info(
            f"Challenge generated for IP: {ip_address}"
        )
        
        return challenge
        
    def generate_proof(self, challenge: ProofChallenge) -> ProofResponse:
        """
        Generate a proof response to the challenge.
        
        Args:
            challenge: The challenge to respond to
            
        Returns:
            ProofResponse: The proof response
            
        Raises:
            ChallengeExpired: If the challenge has expired
        """
        now = time.time()
        if now > challenge.expiry:
            raise ChallengeExpired("Challenge has expired")
            
        # Combine secret key with challenge to create proof
        proof_hash = self._hash(
            self.secret_key,
            str(challenge.challenge_number).encode(),
            challenge.nonce.encode()
        )
        
        self.logger.debug("Generated proof for challenge")
        return ProofResponse(
            proof_hash=proof_hash,
            nonce=challenge.nonce,
            timestamp=now
        )
        
    def verify_proof(
        self, 
        proof: ProofResponse, 
        challenge: ProofChallenge,
        public_commitment: str,
        ip_address: str
    ) -> bool:
        """
        Verify a proof with enhanced security checks.
        
        Args:
            proof: The proof to verify
            challenge: The original challenge
            public_commitment: The public commitment hash
            ip_address: IP address making the verification request
            
        Returns:
            bool: True if proof is valid
            
        Raises:
            AuthenticationError: If verification fails
            RateLimitExceeded: If rate limit is exceeded
        """
        try:
            self._check_rate_limit(ip_address)
            
            # Verify challenge exists and hasn't expired
            stored_challenge = self.active_challenges.get(proof.nonce)
            if not stored_challenge or stored_challenge != challenge:
                raise AuthenticationError("Invalid challenge")
                
            now = time.time()
            if now > challenge.expiry:
                raise ChallengeExpired("Challenge has expired")
                
            # Verify proof timestamp is within acceptable range
            if abs(proof.timestamp - now) > 5:  # 5 second tolerance
                raise AuthenticationError("Proof timestamp out of range")
                
            # Verify commitment matches
            if public_commitment != self.commitment:
                raise AuthenticationError("Public commitment mismatch")
                
            # Clean up used challenge
            del self.active_challenges[proof.nonce]
            
            self.audit_logger.info(
                f"Successful verification for IP: {ip_address}"
            )
            return True
            
        except AuthenticationError as e:
            self.audit_logger.warning(
                f"Verification failed for IP {ip_address}: {str(e)}"
            )
            raise
            
        finally:
            # Cleanup expired challenges periodically
            self._cleanup_expired_challenges()
            
    def _cleanup_expired_challenges(self) -> None:
        """Remove expired challenges from storage."""
        now = time.time()
        expired = [
            nonce for nonce, challenge in self.active_challenges.items()
            if now > challenge.expiry
        ]
        for nonce in expired:
            del self.active_challenges[nonce]

class Entity:
    def __init__(
        self, 
        name: str, 
        secret_credential: str,
        max_attempts: int = 5,
        attempt_window: int = 300
    ):
        """
        Initialize an entity with enhanced ZKP capabilities.
        
        Args:
            name: Entity name
            secret_credential: Secret credential for authentication
            max_attempts: Maximum authentication attempts per window
            attempt_window: Time window for rate limiting (seconds)
        """
        self.name = name
        self.authenticator = ZeroKnowledgeAuthenticator(
            secret_credential,
            max_attempts=max_attempts,
            attempt_window=attempt_window
        )
        
    def get_public_commitment(self) -> str:
        """Get the public commitment hash."""
        return self.authenticator.commitment
        
    def prove_identity(
        self, 
        challenge: ProofChallenge
    ) -> ProofResponse:
        """
        Generate proof of identity for a challenge.
        
        Args:
            challenge: The challenge to respond to
            
        Returns:
            ProofResponse: The proof response
            
        Raises:
            ChallengeExpired: If the challenge has expired
        """
        return self.authenticator.generate_proof(challenge) 
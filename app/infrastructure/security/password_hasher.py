"""Password hashing using bcrypt with cost factor >= 12 (BR-SEC-01).

This module provides secure password hashing and verification
following the security requirements in BR-SEC-01..03.
"""

import re
import secrets
import string
from typing import Optional, Tuple

import bcrypt


# Minimum password length per BR-SEC-02
PASSWORD_MIN_LENGTH = 8

# Bcrypt cost factor - must be >= 12 per BR-SEC-01
BCRYPT_COST = 12

# Lockout configuration per BR-SEC-05
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


class PasswordHasher:
    """Handles password hashing and verification using bcrypt."""

    def __init__(self, cost: int = BCRYPT_COST):
        """Initialize with bcrypt cost factor.
        
        Args:
            cost: Bcrypt cost factor (must be >= 12 per BR-SEC-01).
        """
        if cost < 12:
            raise ValueError("Bcrypt cost factor must be >= 12 (BR-SEC-01)")
        self.cost = cost

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt.
        
        Args:
            password: Plain text password.
            
        Returns:
            Bcrypt hash string.
        """
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=self.cost)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against a bcrypt hash.
        
        Args:
            password: Plain text password to verify.
            hashed: Bcrypt hash to verify against.
            
        Returns:
            True if password matches hash, False otherwise.
        """
        try:
            password_bytes = password.encode("utf-8")
            hashed_bytes = hashed.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            # Log potential attack attempt here (BR-SEC-04)
            return False

    def generate_random_password(self, length: int = 12) -> str:
        """Generate a random password meeting security requirements.
        
        Generates a password with:
        - At least 2 uppercase letters
        - At least 2 lowercase letters  
        - At least 2 digits
        - At least 2 special characters
        
        Args:
            length: Total password length (minimum 12 for security).
            
        Returns:
            Random secure password string.
        """
        if length < 12:
            length = 12

        # Character sets
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        special = "!@#$%^&*"

        # Ensure at least 2 of each type
        password = [
            secrets.choice(uppercase),
            secrets.choice(uppercase),
            secrets.choice(lowercase),
            secrets.choice(lowercase),
            secrets.choice(digits),
            secrets.choice(digits),
            secrets.choice(special),
            secrets.choice(special),
        ]

        # Fill remaining with random choices from all sets
        all_chars = uppercase + lowercase + digits + special
        for _ in range(length - 8):
            password.append(secrets.choice(all_chars))

        # Shuffle to avoid predictable positions
        secrets.SystemRandom().shuffle(password)
        return "".join(password)


class PasswordValidator:
    """Validates password strength per BR-SEC-02.
    
    BR-SEC-02: Mật khẩu mới phải có ≥ 8 ký tự, 
    có ít nhất 1 chữ và 1 số.
    """

    def __init__(
        self,
        min_length: int = PASSWORD_MIN_LENGTH,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = False,
    ):
        """Initialize password validator.
        
        Args:
            min_length: Minimum password length (default 8 per BR-SEC-02).
            require_uppercase: Require at least one uppercase letter.
            require_lowercase: Require at least one lowercase letter.
            require_digit: Require at least one digit.
            require_special: Require at least one special character.
        """
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special

    def validate(self, password: str) -> Tuple[bool, Optional[str]]:
        """Validate password strength.
        
        Args:
            password: Password to validate.
            
        Returns:
            Tuple of (is_valid, error_message).
            error_message is None if valid.
        """
        errors = []

        # Check minimum length
        if len(password) < self.min_length:
            errors.append(f"Mật khẩu phải có ít nhất {self.min_length} ký tự")

        # Check uppercase
        if self.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Mật khẩu phải chứa ít nhất 1 chữ in hoa")

        # Check lowercase
        if self.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("Mật khẩu phải chứa ít nhất 1 chữ in thường")

        # Check digit
        if self.require_digit and not re.search(r"\d", password):
            errors.append("Mật khẩu phải chứa ít nhất 1 số")

        # Check special characters
        if self.require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Mật khẩu phải chứa ít nhất 1 ký tự đặc biệt")

        if errors:
            return False, "; ".join(errors)
        return True, None

    def get_strength_score(self, password: str) -> int:
        """Calculate password strength score (0-100).
        
        Args:
            password: Password to score.
            
        Returns:
            Strength score from 0 (weakest) to 100 (strongest).
        """
        score = 0

        # Length scoring (up to 40 points)
        score += min(40, len(password) * 3)

        # Character variety scoring (up to 60 points)
        if re.search(r"[a-z]", password):
            score += 10
        if re.search(r"[A-Z]", password):
            score += 10
        if re.search(r"\d", password):
            score += 10
        if re.search(r"[!@#$%^&*()_\-+=\[\]{}|;':\",./<>?]", password):
            score += 15

        # Bonus for length beyond minimum
        if len(password) > self.min_length:
            score += min(15, (len(password) - self.min_length) * 3)

        return min(100, score)


# Global instances
password_hasher = PasswordHasher()
password_validator = PasswordValidator()

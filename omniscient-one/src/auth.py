"""
Authentication and User Management System
Handles user registration, login, JWT tokens, and security
"""

import streamlit as st
import jwt
import bcrypt
import uuid
from datetime import datetime, timedelta
import hashlib
import secrets
from typing import Dict, Optional, Union
import os

class AuthManager:
    """Complete authentication and user management system"""
    
    def __init__(self):
        # Load secret from environment or Streamlit secrets
        self.jwt_secret = st.secrets.get("JWT_SECRET", os.getenv("JWT_SECRET", "production-secret-key-change-me"))
        self.token_expiry_days = 30
        
        # Initialize database connection
        from .database import DatabaseManager
        self.db = DatabaseManager()
        
        # Initialize session state
        self._init_session()
    
    def _init_session(self):
        """Initialize session state variables"""
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'token' not in st.session_state:
            st.session_state.token = None
    
    def hash_password(self, password: str) -> str:
        """Securely hash a password"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False
    
    def create_user(self, email: str, username: str, password: str) -> Dict:
        """Create a new user account"""
        
        # Validate inputs
        if not self._validate_email(email):
            return {"success": False, "error": "Invalid email format"}
        
        if not self._validate_username(username):
            return {"success": False, "error": "Username must be 3-20 characters, letters and numbers only"}
        
        if not self._validate_password(password):
            return {"success": False, "error": "Password must be at least 8 characters"}
        
        # Check if user exists
        if self.db.user_exists(email, username):
            return {"success": False, "error": "User already exists"}
        
        # Create user in database
        user_data = {
            "user_id": str(uuid.uuid4()),
            "email": email.lower(),
            "username": username,
            "password_hash": self.hash_password(password),
            "subscription_tier": "free",
            "subscription_expiry": (datetime.now() + timedelta(days=14)).isoformat(),  # 14-day trial
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "api_key": self._generate_api_key(username),
            "settings": {
                "theme": "dark",
                "notifications": True,
                "default_portfolio": 10000,
                "watchlist": ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL"]
            }
        }
        
        # Save to database
        success = self.db.create_user(user_data)
        
        if success:
            # Create default portfolio
            portfolio_data = {
                "user_id": user_data["user_id"],
                "portfolio_id": str(uuid.uuid4()),
                "name": "My Portfolio",
                "holdings": {},
                "total_value": 10000.0,
                "created_at": datetime.now().isoformat()
            }
            self.db.create_portfolio(portfolio_data)
            
            # Send welcome email (async)
            self._send_welcome_email(email, username)
            
            return {
                "success": True,
                "user": {
                    "user_id": user_data["user_id"],
                    "username": username,
                    "email": email,
                    "subscription_tier": "free",
                    "api_key": user_data["api_key"]
                }
            }
        else:
            return {"success": False, "error": "Database error"}
    
    def authenticate_user(self, identifier: str, password: str) -> Dict:
        """Authenticate a user with email/username and password"""
        
        # Get user from database
        user = self.db.get_user_by_identifier(identifier)
        
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Verify password
        if not self.verify_password(password, user["password_hash"]):
            return {"success": False, "error": "Invalid password"}
        
        # Update last login
        self.db.update_last_login(user["user_id"])
        
        # Create JWT token
        token = self.create_token(user)
        
        # Update session state
        st.session_state.user = {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "subscription_tier": user["subscription_tier"],
            "api_key": user["api_key"]
        }
        st.session_state.authenticated = True
        st.session_state.token = token
        
        return {
            "success": True,
            "token": token,
            "user": st.session_state.user
        }
    
    def create_token(self, user_data: Dict) -> str:
        """Create JWT token for authenticated user"""
        payload = {
            "sub": user_data["user_id"],
            "username": user_data["username"],
            "email": user_data["email"],
            "tier": user_data["subscription_tier"],
            "exp": datetime.utcnow() + timedelta(days=self.token_expiry_days),
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return payload if valid"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def logout(self):
        """Log out current user"""
        st.session_state.user = None
        st.session_state.authenticated = False
        st.session_state.token = None
    
    def get_current_user(self) -> Optional[Dict]:
        """Get current authenticated user"""
        if st.session_state.authenticated and st.session_state.user:
            return st.session_state.user
        return None
    
    def require_auth(self):
        """Decorator to require authentication for functions"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                if not st.session_state.authenticated:
                    st.error("Authentication required")
                    st.info("Please login to access this feature")
                    return None
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _validate_username(self, username: str) -> bool:
        """Validate username format"""
        import re
        pattern = r'^[a-zA-Z0-9_]{3,20}$'
        return bool(re.match(pattern, username))
    
    def _validate_password(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False
        # Add more password rules as needed
        return True
    
    def _generate_api_key(self, username: str) -> str:
        """Generate unique API key for user"""
        timestamp = str(int(datetime.now().timestamp()))
        random_str = secrets.token_urlsafe(16)
        base_str = f"{username}_{timestamp}_{random_str}"
        return hashlib.sha256(base_str.encode()).hexdigest()[:32]
    
    def _send_welcome_email(self, email: str, username: str):
        """Send welcome email to new user (async)"""
        # In production, integrate with email service like SendGrid
        # For now, just log
        print(f"Welcome email would be sent to {email} for user {username}")
    
    def update_subscription(self, user_id: str, tier: str, expiry_days: int = 30):
        """Update user's subscription tier"""
        expiry_date = datetime.now() + timedelta(days=expiry_days)
        return self.db.update_subscription(user_id, tier, expiry_date.isoformat())
    
    def reset_password_request(self, email: str):
        """Initiate password reset process"""
        user = self.db.get_user_by_email(email)
        if user:
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            self.db.save_reset_token(user["user_id"], reset_token)
            
            # Send reset email (in production)
            print(f"Password reset token for {email}: {reset_token}")
            return True
        return False
    
    def reset_password(self, token: str, new_password: str):
        """Reset password using reset token"""
        user_id = self.db.get_user_by_reset_token(token)
        if user_id:
            new_hash = self.hash_password(new_password)
            success = self.db.update_password(user_id, new_hash)
            if success:
                self.db.clear_reset_token(user_id)
                return True
        return False

# Create singleton instance
auth_manager = None

def get_auth_manager():
    """Get or create singleton AuthManager instance"""
    global auth_manager
    if auth_manager is None:
        auth_manager = AuthManager()
    return auth_manager
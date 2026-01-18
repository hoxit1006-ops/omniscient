"""
Database Management System
Handles all data persistence for users, portfolios, trades, and settings
"""

import json
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import streamlit as st
import os
import pandas as pd

class DatabaseManager:
    """Complete database management system with SQLite/PostgreSQL support"""
    
    def __init__(self, db_type: str = "sqlite"):
        """
        Initialize database manager
        
        Args:
            db_type: "sqlite" (default) or "postgresql"
        """
        self.db_type = db_type
        self.db_path = "data/omniscient.db"
        self.lock = threading.Lock()
        
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _get_connection(self):
        """Get database connection"""
        if self.db_type == "sqlite":
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        elif self.db_type == "postgresql":
            # PostgreSQL connection (for production)
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            # Get connection string from secrets
            db_url = st.secrets.get("DATABASE_URL", os.getenv("DATABASE_URL"))
            if db_url:
                return psycopg2.connect(db_url, cursor_factory=RealDictCursor)
            else:
                raise Exception("PostgreSQL DATABASE_URL not configured")
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def _init_database(self):
        """Initialize database tables"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                subscription_tier TEXT DEFAULT 'free',
                subscription_expiry TEXT,
                created_at TEXT NOT NULL,
                last_login TEXT,
                api_key TEXT UNIQUE,
                settings TEXT,
                reset_token TEXT,
                reset_token_expiry TEXT,
                is_active INTEGER DEFAULT 1
            )
            ''')
            
            # Portfolios table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                portfolio_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                holdings TEXT,
                total_value REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''')
            
            # Trades table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                portfolio_id TEXT,
                ticker TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                total REAL NOT NULL,
                timestamp TEXT NOT NULL,
                status TEXT DEFAULT 'completed',
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (portfolio_id) REFERENCES portfolios (portfolio_id)
            )
            ''')
            
            # Watchlists table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlists (
                watchlist_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT DEFAULT 'Default',
                tickers TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''')
            
            # Alerts table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                ticker TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                condition TEXT NOT NULL,
                threshold REAL NOT NULL,
                triggered INTEGER DEFAULT 0,
                triggered_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''')
            
            # Market data cache
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data_cache (
                cache_id TEXT PRIMARY KEY,
                ticker TEXT NOT NULL,
                data_type TEXT NOT NULL,
                data TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                expiry TEXT NOT NULL
            )
            ''')
            
            # API usage tracking
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                usage_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''')
            
            conn.commit()
            conn.close()
    
    def create_user(self, user_data: Dict) -> bool:
        """Create a new user in database"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO users (
                    user_id, email, username, password_hash,
                    subscription_tier, subscription_expiry, created_at,
                    api_key, settings
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_data["user_id"],
                    user_data["email"],
                    user_data["username"],
                    user_data["password_hash"],
                    user_data["subscription_tier"],
                    user_data["subscription_expiry"],
                    user_data["created_at"],
                    user_data["api_key"],
                    json.dumps(user_data.get("settings", {}))
                ))
                
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def get_user_by_identifier(self, identifier: str) -> Optional[Dict]:
        """Get user by email or username"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM users 
                WHERE (email = ? OR username = ?) AND is_active = 1
                ''', (identifier.lower(), identifier))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return self._row_to_dict(row)
                return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM users WHERE email = ? AND is_active = 1
                ''', (email.lower(),))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return self._row_to_dict(row)
                return None
        except Exception:
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by user_id"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM users WHERE user_id = ? AND is_active = 1
                ''', (user_id,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return self._row_to_dict(row)
                return None
        except Exception:
            return None
    
    def user_exists(self, email: str, username: str) -> bool:
        """Check if user with given email or username exists"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT COUNT(*) as count FROM users 
                WHERE (email = ? OR username = ?) AND is_active = 1
                ''', (email.lower(), username))
                
                result = cursor.fetchone()
                conn.close()
                
                return result["count"] > 0
        except Exception:
            return False
    
    def update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                UPDATE users SET last_login = ? WHERE user_id = ?
                ''', (datetime.now().isoformat(), user_id))
                
                conn.commit()
                conn.close()
        except Exception:
            pass
    
    def update_subscription(self, user_id: str, tier: str, expiry: str) -> bool:
        """Update user's subscription"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                UPDATE users 
                SET subscription_tier = ?, subscription_expiry = ?
                WHERE user_id = ?
                ''', (tier, expiry, user_id))
                
                conn.commit()
                conn.close()
                return True
        except Exception:
            return False
    
    def create_portfolio(self, portfolio_data: Dict) -> bool:
        """Create a new portfolio"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO portfolios (
                    portfolio_id, user_id, name, holdings,
                    total_value, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    portfolio_data["portfolio_id"],
                    portfolio_data["user_id"],
                    portfolio_data["name"],
                    json.dumps(portfolio_data.get("holdings", {})),
                    portfolio_data.get("total_value", 0.0),
                    portfolio_data["created_at"],
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                conn.close()
                return True
        except Exception:
            return False
    
    def get_user_portfolios(self, user_id: str) -> List[Dict]:
        """Get all portfolios for a user"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM portfolios WHERE user_id = ?
                ''', (user_id,))
                
                rows = cursor.fetchall()
                conn.close()
                
                return [self._row_to_dict(row) for row in rows]
        except Exception:
            return []
    
    def update_portfolio(self, portfolio_id: str, updates: Dict) -> bool:
        """Update portfolio data"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Build update query dynamically
                set_clause = []
                values = []
                
                for key, value in updates.items():
                    if key in ["holdings"]:
                        value = json.dumps(value)
                    set_clause.append(f"{key} = ?")
                    values.append(value)
                
                # Add updated_at timestamp
                set_clause.append("updated_at = ?")
                values.append(datetime.now().isoformat())
                
                values.append(portfolio_id)
                
                query = f'''
                UPDATE portfolios 
                SET {', '.join(set_clause)}
                WHERE portfolio_id = ?
                '''
                
                cursor.execute(query, tuple(values))
                conn.commit()
                conn.close()
                return True
        except Exception:
            return False
    
    def create_trade(self, trade_data: Dict) -> bool:
        """Record a new trade"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO trades (
                    trade_id, user_id, portfolio_id, ticker,
                    action, quantity, price, total, timestamp, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade_data.get("trade_id", f"trade_{datetime.now().timestamp()}"),
                    trade_data["user_id"],
                    trade_data.get("portfolio_id"),
                    trade_data["ticker"],
                    trade_data["action"],
                    trade_data["quantity"],
                    trade_data["price"],
                    trade_data["total"],
                    trade_data.get("timestamp", datetime.now().isoformat()),
                    trade_data.get("status", "completed"),
                    trade_data.get("notes", "")
                ))
                
                conn.commit()
                conn.close()
                return True
        except Exception:
            return False
    
    def get_user_trades(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get recent trades for a user"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM trades 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
                ''', (user_id, limit))
                
                rows = cursor.fetchall()
                conn.close()
                
                return [self._row_to_dict(row) for row in rows]
        except Exception:
            return []
    
    def save_watchlist(self, user_id: str, tickers: List[str], name: str = "Default") -> bool:
        """Save user's watchlist"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Check if watchlist exists
                cursor.execute('''
                SELECT watchlist_id FROM watchlists 
                WHERE user_id = ? AND name = ?
                ''', (user_id, name))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing
                    cursor.execute('''
                    UPDATE watchlists 
                    SET tickers = ?, created_at = ?
                    WHERE watchlist_id = ?
                    ''', (
                        json.dumps(tickers),
                        datetime.now().isoformat(),
                        existing["watchlist_id"]
                    ))
                else:
                    # Create new
                    cursor.execute('''
                    INSERT INTO watchlists (
                        watchlist_id, user_id, name, tickers, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    ''', (
                        f"watchlist_{user_id}_{name}",
                        user_id,
                        name,
                        json.dumps(tickers),
                        datetime.now().isoformat()
                    ))
                
                conn.commit()
                conn.close()
                return True
        except Exception:
            return False
    
    def get_watchlist(self, user_id: str, name: str = "Default") -> List[str]:
        """Get user's watchlist"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT tickers FROM watchlists 
                WHERE user_id = ? AND name = ?
                ''', (user_id, name))
                
                row = cursor.fetchone()
                conn.close()
                
                if row and row["tickers"]:
                    return json.loads(row["tickers"])
                return []
        except Exception:
            return []
    
    def create_alert(self, alert_data: Dict) -> bool:
        """Create a new price alert"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO alerts (
                    alert_id, user_id, ticker, alert_type,
                    condition, threshold, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert_data.get("alert_id", f"alert_{datetime.now().timestamp()}"),
                    alert_data["user_id"],
                    alert_data["ticker"],
                    alert_data["alert_type"],
                    json.dumps(alert_data.get("condition", {})),
                    alert_data["threshold"],
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                conn.close()
                return True
        except Exception:
            return False
    
    def get_user_alerts(self, user_id: str) -> List[Dict]:
        """Get all alerts for a user"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM alerts 
                WHERE user_id = ? 
                ORDER BY created_at DESC
                ''', (user_id,))
                
                rows = cursor.fetchall()
                conn.close()
                
                return [self._row_to_dict(row) for row in rows]
        except Exception:
            return []
    
    def save_reset_token(self, user_id: str, token: str) -> bool:
        """Save password reset token"""
        try:
            expiry = (datetime.now() + timedelta(hours=24)).isoformat()
            
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                UPDATE users 
                SET reset_token = ?, reset_token_expiry = ?
                WHERE user_id = ?
                ''', (token, expiry, user_id))
                
                conn.commit()
                conn.close()
                return True
        except Exception:
            return False
    
    def get_user_by_reset_token(self, token: str) -> Optional[str]:
        """Get user_id by reset token (if valid)"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT user_id FROM users 
                WHERE reset_token = ? AND reset_token_expiry > ?
                ''', (token, datetime.now().isoformat()))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return row["user_id"]
                return None
        except Exception:
            return None
    
    def clear_reset_token(self, user_id: str) -> bool:
        """Clear reset token after use"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                UPDATE users 
                SET reset_token = NULL, reset_token_expiry = NULL
                WHERE user_id = ?
                ''', (user_id,))
                
                conn.commit()
                conn.close()
                return True
        except Exception:
            return False
    
    def update_password(self, user_id: str, new_hash: str) -> bool:
        """Update user's password hash"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                UPDATE users 
                SET password_hash = ?
                WHERE user_id = ?
                ''', (new_hash, user_id))
                
                conn.commit()
                conn.close()
                return True
        except Exception:
            return False
    
    def cache_market_data(self, ticker: str, data_type: str, data: Any, ttl_minutes: int = 60):
        """Cache market data to reduce API calls"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cache_id = f"{ticker}_{data_type}"
                expiry = (datetime.now() + timedelta(minutes=ttl_minutes)).isoformat()
                
                cursor.execute('''
                INSERT OR REPLACE INTO market_data_cache
                (cache_id, ticker, data_type, data, timestamp, expiry)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    cache_id,
                    ticker,
                    data_type,
                    json.dumps(data),
                    datetime.now().isoformat(),
                    expiry
                ))
                
                conn.commit()
                conn.close()
        except Exception:
            pass
    
    def get_cached_market_data(self, ticker: str, data_type: str) -> Optional[Any]:
        """Get cached market data if not expired"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cache_id = f"{ticker}_{data_type}"
                
                cursor.execute('''
                SELECT data, expiry FROM market_data_cache 
                WHERE cache_id = ?
                ''', (cache_id,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    expiry = datetime.fromisoformat(row["expiry"])
                    if datetime.now() < expiry:
                        return json.loads(row["data"])
            return None
        except Exception:
            return None
    
    def track_api_usage(self, user_id: str, endpoint: str):
        """Track API usage for rate limiting"""
        try:
            date = datetime.now().strftime("%Y-%m-%d")
            
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Check if entry exists for today
                cursor.execute('''
                SELECT usage_id, count FROM api_usage 
                WHERE user_id = ? AND endpoint = ? AND date = ?
                ''', (user_id, endpoint, date))
                
                row = cursor.fetchone()
                
                if row:
                    # Update existing
                    cursor.execute('''
                    UPDATE api_usage 
                    SET count = count + 1 
                    WHERE usage_id = ?
                    ''', (row["usage_id"],))
                else:
                    # Create new
                    cursor.execute('''
                    INSERT INTO api_usage (usage_id, user_id, endpoint, count, date)
                    VALUES (?, ?, ?, 1, ?)
                    ''', (
                        f"usage_{user_id}_{endpoint}_{date}",
                        user_id,
                        endpoint,
                        date
                    ))
                
                conn.commit()
                conn.close()
        except Exception:
            pass
    
    def get_api_usage(self, user_id: str, endpoint: str, date: str = None) -> int:
        """Get API usage count for a user"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT count FROM api_usage 
                WHERE user_id = ? AND endpoint = ? AND date = ?
                ''', (user_id, endpoint, date))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return row["count"]
                return 0
        except Exception:
            return 0
    
    def backup_database(self, backup_path: str = None) -> bool:
        """Create a backup of the database"""
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backups/omniscient_backup_{timestamp}.db"
            
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            with self.lock:
                conn = self._get_connection()
                backup_conn = sqlite3.connect(backup_path)
                
                conn.backup(backup_conn)
                
                backup_conn.close()
                conn.close()
            
            return True
        except Exception as e:
            print(f"Backup failed: {e}")
            return False
    
    def _row_to_dict(self, row) -> Dict:
        """Convert database row to dictionary"""
        if hasattr(row, "keys"):  # Already a dict-like object
            return dict(row)
        else:  # SQLite Row object
            return {description[0]: value for description, value in zip(row.description, row)}
    
    def export_user_data(self, user_id: str) -> Dict:
        """Export all user data for GDPR compliance"""
        try:
            user_data = self.get_user_by_id(user_id)
            if not user_data:
                return {}
            
            # Remove sensitive data
            user_data.pop("password_hash", None)
            user_data.pop("reset_token", None)
            user_data.pop("reset_token_expiry", None)
            
            # Get all related data
            portfolios = self.get_user_portfolios(user_id)
            trades = self.get_user_trades(user_id, limit=1000)
            watchlist = self.get_watchlist(user_id)
            alerts = self.get_user_alerts(user_id)
            
            return {
                "user": user_data,
                "portfolios": portfolios,
                "trades": trades,
                "watchlist": watchlist,
                "alerts": alerts,
                "exported_at": datetime.now().isoformat()
            }
        except Exception:
            return {}
    
    def delete_user_data(self, user_id: str) -> bool:
        """Delete all user data (GDPR right to be forgotten)"""
        try:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Anonymize user data instead of deleting (for legal compliance)
                anonymized_email = f"deleted_{user_id}@deleted.com"
                anonymized_username = f"deleted_{user_id}"
                
                cursor.execute('''
                UPDATE users 
                SET email = ?, username = ?, password_hash = ?, 
                    api_key = NULL, settings = '{}', is_active = 0
                WHERE user_id = ?
                ''', (anonymized_email, anonymized_username, "deleted", user_id))
                
                conn.commit()
                conn.close()
                return True
        except Exception:
            return False

# Create singleton instance
db_manager = None

def get_database_manager():
    """Get or create singleton DatabaseManager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager
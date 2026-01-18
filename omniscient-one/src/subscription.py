"""
Subscription and Payment Management System
Handles subscription plans, payments, billing, and account upgrades
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os
import uuid

# Try to import Stripe for payment processing
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None

class SubscriptionManager:
    """Complete subscription and payment management system"""
    
    def __init__(self):
        # Initialize Stripe if available
        self.stripe_enabled = False
        if STRIPE_AVAILABLE:
            stripe_key = st.secrets.get("STRIPE_SECRET_KEY", os.getenv("STRIPE_SECRET_KEY"))
            if stripe_key:
                stripe.api_key = stripe_key
                self.stripe_enabled = True
                print("✅ Stripe payment processing enabled")
            else:
                print("⚠️ Stripe secret key not found - payment processing disabled")
        
        # Define subscription plans
        self.plans = {
            "free": {
                "name": "Free",
                "price_monthly": 0,
                "price_yearly": 0,
                "stripe_price_id_monthly": "",
                "stripe_price_id_yearly": "",
                "features": [
                    "Basic Dashboard",
                    "Delayed Market Data (15-min)",
                    "5 Stock Watchlist",
                    "Basic Technical Analysis",
                    "Email Support"
                ],
                "limits": {
                    "max_portfolios": 1,
                    "max_alerts": 5,
                    "daily_scans": 3,
                    "api_calls_per_day": 100,
                    "data_refresh_interval": 15,  # minutes
                    "real_time_data": False,
                    "advanced_indicators": False,
                    "ai_predictions": False,
                    "whale_detection": False,
                    "automated_trading": False,
                    "api_access": False
                },
                "trial_days": 0
            },
            "basic": {
                "name": "Basic",
                "price_monthly": 29.99,
                "price_yearly": 299.99,  # ~$25/month with annual discount
                "stripe_price_id_monthly": "price_basic_monthly",
                "stripe_price_id_yearly": "price_basic_yearly",
                "features": [
                    "Everything in Free",
                    "Real-time Market Data",
                    "Unlimited Watchlist",
                    "AI Price Predictions",
                    "Basic Trade Signals",
                    "Email & SMS Alerts",
                    "Priority Support"
                ],
                "limits": {
                    "max_portfolios": 3,
                    "max_alerts": 20,
                    "daily_scans": 10,
                    "api_calls_per_day": 500,
                    "data_refresh_interval": 1,  # minute
                    "real_time_data": True,
                    "advanced_indicators": True,
                    "ai_predictions": True,
                    "whale_detection": False,
                    "automated_trading": False,
                    "api_access": False
                },
                "trial_days": 7
            },
            "premium": {
                "name": "Premium",
                "price_monthly": 99.99,
                "price_yearly": 999.99,  # ~$83/month with annual discount
                "stripe_price_id_monthly": "price_premium_monthly",
                "stripe_price_id_yearly": "price_premium_yearly",
                "features": [
                    "Everything in Basic",
                    "Absolute Best Scanner",
                    "Advanced AI Predictions",
                    "Whale Detection",
                    "Portfolio Optimizer",
                    "Market Narratives",
                    "Advanced Technical Indicators",
                    "API Access",
                    "Discord Community",
                    "Weekly Strategy Reports"
                ],
                "limits": {
                    "max_portfolios": 10,
                    "max_alerts": 100,
                    "daily_scans": 50,
                    "api_calls_per_day": 2000,
                    "data_refresh_interval": 1,  # minute
                    "real_time_data": True,
                    "advanced_indicators": True,
                    "ai_predictions": True,
                    "whale_detection": True,
                    "automated_trading": False,
                    "api_access": True
                },
                "trial_days": 14
            },
            "ultimate": {
                "name": "Ultimate",
                "price_monthly": 199.99,
                "price_yearly": 1999.99,  # ~$166/month with annual discount
                "stripe_price_id_monthly": "price_ultimate_monthly",
                "stripe_price_id_yearly": "price_ultimate_yearly",
                "features": [
                    "Everything in Premium",
                    "Automated Trading",
                    "Institutional Grade Data",
                    "Custom Indicators",
                    "Dedicated Account Manager",
                    "Weekly 1-on-1 Strategy Sessions",
                    "White Label Solutions",
                    "Priority API Access",
                    "24/7 Phone Support",
                    "Custom Development"
                ],
                "limits": {
                    "max_portfolios": 50,
                    "max_alerts": 500,
                    "daily_scans": 1000,
                    "api_calls_per_day": 10000,
                    "data_refresh_interval": 1,  # minute
                    "real_time_data": True,
                    "advanced_indicators": True,
                    "ai_predictions": True,
                    "whale_detection": True,
                    "automated_trading": True,
                    "api_access": True
                },
                "trial_days": 30
            }
        }
    
    def get_plan(self, plan_id: str) -> Optional[Dict]:
        """Get plan details by ID"""
        return self.plans.get(plan_id)
    
    def get_all_plans(self) -> Dict[str, Dict]:
        """Get all available plans"""
        return self.plans
    
    def create_checkout_session(self, user_email: str, user_id: str, 
                               plan_id: str, period: str = "monthly") -> Optional[str]:
        """
        Create Stripe checkout session
        
        Returns:
            Checkout session URL or None if failed
        """
        if not self.stripe_enabled:
            st.error("Payment processing is not configured")
            return None
        
        plan = self.get_plan(plan_id)
        if not plan:
            st.error("Invalid plan selected")
            return None
        
        if plan_id == "free":
            return None  # Free plan doesn't need checkout
        
        try:
            # Get Stripe price ID
            price_id_key = f"stripe_price_id_{period}"
            price_id = plan.get(price_id_key, "")
            
            if not price_id:
                st.error("Price not configured for this plan")
                return None
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{self._get_app_url()}/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{self._get_app_url()}/cancel",
                customer_email=user_email,
                client_reference_id=user_id,
                metadata={
                    'plan': plan_id,
                    'period': period,
                    'user_id': user_id
                }
            )
            
            return session.url
            
        except Exception as e:
            st.error(f"Payment error: {str(e)}")
            return None
    
    def handle_webhook(self, payload: bytes, sig_header: str) -> Tuple[bool, str]:
        """Handle Stripe webhook events"""
        if not self.stripe_enabled:
            return False, "Stripe not configured"
        
        try:
            webhook_secret = st.secrets.get("STRIPE_WEBHOOK_SECRET", 
                                           os.getenv("STRIPE_WEBHOOK_SECRET", ""))
            
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            # Handle the event
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                self._handle_successful_payment(session)
                
            elif event['type'] == 'customer.subscription.updated':
                subscription = event['data']['object']
                self._handle_subscription_update(subscription)
                
            elif event['type'] == 'customer.subscription.deleted':
                subscription = event['data']['object']
                self._handle_subscription_cancellation(subscription)
            
            return True, "Webhook processed successfully"
            
        except ValueError as e:
            return False, f"Invalid payload: {str(e)}"
        except stripe.error.SignatureVerificationError as e:
            return False, f"Invalid signature: {str(e)}"
        except Exception as e:
            return False, f"Webhook error: {str(e)}"
    
    def _handle_successful_payment(self, session: Dict):
        """Handle successful payment"""
        from .database import get_database_manager
        db = get_database_manager()
        
        user_id = session.get('metadata', {}).get('user_id')
        plan_id = session.get('metadata', {}).get('plan')
        period = session.get('metadata', {}).get('period')
        
        if not user_id or not plan_id:
            return
        
        # Calculate expiry date
        if period == "yearly":
            expiry_days = 365
        else:
            expiry_days = 30
        
        expiry_date = datetime.now() + timedelta(days=expiry_days)
        
        # Update user's subscription in database
        db.update_subscription(user_id, plan_id, expiry_date.isoformat())
        
        # Send confirmation email (in production)
        print(f"Payment successful: User {user_id} upgraded to {plan_id}")
    
    def _handle_subscription_update(self, subscription: Dict):
        """Handle subscription updates"""
        # This would update the subscription in your database
        # based on the subscription object from Stripe
        pass
    
    def _handle_subscription_cancellation(self, subscription: Dict):
        """Handle subscription cancellations"""
        # This would downgrade the user to free tier
        # or handle the cancellation logic
        pass
    
    def _get_app_url(self) -> str:
        """Get application URL for redirects"""
        return st.secrets.get("APP_URL", os.getenv("APP_URL", "https://omniscient-one.streamlit.app"))
    
    def get_user_plan_info(self, user_tier: str) -> Dict:
        """Get user's current plan information"""
        plan = self.get_plan(user_tier)
        if not plan:
            return {}
        
        return {
            "name": plan["name"],
            "tier": user_tier,
            "price_monthly": plan["price_monthly"],
            "price_yearly": plan["price_yearly"],
            "features": plan["features"],
            "limits": plan["limits"]
        }
    
    def can_user_access_feature(self, user_tier: str, feature_name: str) -> bool:
        """Check if user can access a specific feature"""
        plan = self.get_plan(user_tier)
        if not plan:
            return False
        
        # Map feature names to limit keys
        feature_map = {
            "real_time_data": "real_time_data",
            "ai_predictions": "ai_predictions",
            "whale_detection": "whale_detection",
            "portfolio_optimizer": "advanced_indicators",
            "automated_trading": "automated_trading",
            "api_access": "api_access"
        }
        
        limit_key = feature_map.get(feature_name)
        if limit_key:
            return plan["limits"].get(limit_key, False)
        
        return True  # Default to True for unspecified features
    
    def get_upgrade_recommendation(self, current_tier: str, usage_stats: Dict) -> str:
        """
        Recommend a plan upgrade based on usage
        
        Args:
            current_tier: Current subscription tier
            usage_stats: Dictionary with usage statistics
            
        Returns:
            Recommended tier or "none" if current is sufficient
        """
        current_plan = self.get_plan(current_tier)
        if not current_plan:
            return "none"
        
        # Analyze usage
        alerts_used = usage_stats.get("alerts_used", 0)
        alerts_limit = current_plan["limits"]["max_alerts"]
        
        scans_used = usage_stats.get("scans_used", 0)
        scans_limit = current_plan["limits"]["daily_scans"]
        
        api_calls_used = usage_stats.get("api_calls_used", 0)
        api_calls_limit = current_plan["limits"]["api_calls_per_day"]
        
        # Check if user is hitting limits
        if (alerts_used >= alerts_limit * 0.8 or 
            scans_used >= scans_limit * 0.8 or 
            api_calls_used >= api_calls_limit * 0.8):
            
            # Recommend next tier
            tier_order = ["free", "basic", "premium", "ultimate"]
            current_index = tier_order.index(current_tier)
            
            if current_index < len(tier_order) - 1:
                return tier_order[current_index + 1]
        
        return "none"
    
    def calculate_savings(self, current_tier: str, target_tier: str) -> Dict:
        """Calculate potential savings from upgrading"""
        current_plan = self.get_plan(current_tier)
        target_plan = self.get_plan(target_tier)
        
        if not current_plan or not target_plan:
            return {"monthly_savings": 0, "yearly_savings": 0}
        
        # Compare feature value
        current_features = set(current_plan["features"])
        target_features = set(target_plan["features"])
        new_features = target_features - current_features
        
        # Calculate monetary value of new features
        feature_value = len(new_features) * 20  # Approx $20 per feature
        
        monthly_savings = feature_value - (target_plan["price_monthly"] - current_plan["price_monthly"])
        yearly_savings = (feature_value * 12) - (target_plan["price_yearly"] - current_plan["price_yearly"])
        
        return {
            "monthly_savings": max(0, monthly_savings),
            "yearly_savings": max(0, yearly_savings),
            "new_features": list(new_features)
        }
    
    def create_coupon_code(self, discount_percent: float, max_redemptions: int = 100, 
                          duration: str = "once") -> Optional[Dict]:
        """Create a discount coupon code"""
        if not self.stripe_enabled:
            return None
        
        try:
            coupon = stripe.Coupon.create(
                percent_off=discount_percent,
                duration=duration,
                max_redemptions=max_redemptions,
                name=f"{discount_percent}% Off Omniscient One"
            )
            
            return {
                "id": coupon.id,
                "percent_off": coupon.percent_off,
                "duration": coupon.duration,
                "max_redemptions": coupon.max_redemptions
            }
        except Exception:
            return None
    
    def generate_invoice(self, user_id: str, amount: float, description: str) -> Optional[Dict]:
        """Generate an invoice for a user"""
        if not self.stripe_enabled:
            return None
        
        try:
            # This would require having the user's Stripe customer ID
            # For now, return mock data
            invoice_id = f"inv_{uuid.uuid4().hex[:8]}"
            
            return {
                "invoice_id": invoice_id,
                "amount": amount,
                "description": description,
                "status": "draft",
                "created_at": datetime.now().isoformat(),
                "due_date": (datetime.now() + timedelta(days=30)).isoformat()
            }
        except Exception:
            return None
    
    def get_billing_history(self, user_id: str) -> List[Dict]:
        """Get user's billing history"""
        # In production, this would fetch from Stripe or your database
        # For now, return mock data
        return [
            {
                "date": "2024-01-15",
                "description": "Premium Subscription",
                "amount": 99.99,
                "status": "paid"
            },
            {
                "date": "2023-12-15",
                "description": "Premium Subscription",
                "amount": 99.99,
                "status": "paid"
            }
        ]
    
    def cancel_subscription(self, user_id: str) -> bool:
        """Cancel user's subscription"""
        # In production, this would cancel via Stripe API
        # For now, update in database
        from .database import get_database_manager
        db = get_database_manager()
        
        # Set expiry to yesterday to effectively cancel
        expiry_date = (datetime.now() - timedelta(days=1)).isoformat()
        return db.update_subscription(user_id, "free", expiry_date)
    
    def is_subscription_active(self, user_tier: str, expiry_date: str) -> bool:
        """Check if subscription is still active"""
        if user_tier == "free":
            return True  # Free tier is always active
        
        try:
            expiry = datetime.fromisoformat(expiry_date)
            return datetime.now() < expiry
        except Exception:
            return False

# Create singleton instance
subscription_manager = None

def get_subscription_manager():
    """Get or create singleton SubscriptionManager instance"""
    global subscription_manager
    if subscription_manager is None:
        subscription_manager = SubscriptionManager()
    return subscription_manager
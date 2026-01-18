# deploy.py - UPDATED WITH DATA DIRECTORY SETUP
#!/usr/bin/env python3
"""
COMPLETE DEPLOYMENT SCRIPT FOR OMNISCIENT ONE
Run this script to set up everything for deployment
"""

import os
import subprocess
import sys
import shutil

def setup_complete_deployment():
    """Complete deployment setup with data directory"""
    
    print("=" * 60)
    print("🚀 OMNISCIENT ONE - COMPLETE DEPLOYMENT SETUP")
    print("=" * 60)
    
    # Check Python version
    print(f"📦 Python version: {sys.version}")
    
    # Create necessary directories
    print("\n📁 Creating directory structure...")
    os.makedirs(".streamlit", exist_ok=True)
    os.makedirs("src", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/backups", exist_ok=True)
    
    print("✅ Directory structure created")
    
    # Create requirements.txt if not exists
    if not os.path.exists("requirements.txt"):
        print("\n📦 Creating requirements.txt...")
        requirements = """streamlit==1.28.0
pandas==2.0.3
numpy==1.24.3
plotly==5.17.0
yfinance==0.2.33
boto3==1.29.0
python-dotenv==1.0.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
bcrypt==4.1.2
pyjwt==2.8.0
stripe==7.6.0"""
        
        with open("requirements.txt", "w") as f:
            f.write(requirements)
        print("✅ Created requirements.txt")
    
    # Create config.toml
    print("\n⚙️ Creating Streamlit config...")
    config_content = """[theme]
primaryColor = "#00FF88"
backgroundColor = "#0A0A0A"
secondaryBackgroundColor = "#1A1A1A"
textColor = "#FFFFFF"
font = "sans serif"

[server]
port = 8501
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200

[browser]
gatherUsageStats = false

[runner]
magicEnabled = false

[client]
showErrorDetails = false
"""
    
    with open(".streamlit/config.toml", "w") as f:
        f.write(config_content)
    print("✅ Created .streamlit/config.toml")
    
    # Create secrets.toml template
    print("\n🔐 Creating secrets template...")
    secrets_content = """# ============================================================================
# OMNISCIENT ONE - PRODUCTION SECRETS
# ============================================================================
# IMPORTANT: DO NOT SHARE THIS FILE
# Add these secrets in Streamlit Cloud dashboard
# ============================================================================

# YOUR S3 CREDENTIALS (From Massive)
S3_ACCESS_KEY = "b01b8718-ba6d-427a-a2a0-b87073733267"
S3_SECRET_KEY = "j8MipbM0xg_ksF2SZmBwZo7w5kFAy_2A"
S3_ENDPOINT = "https://files.massive.com"
S3_BUCKET = "flatfiles"

# Authentication
JWT_SECRET = "your-super-secret-key-change-this-123"

# Stripe Payments (Optional)
STRIPE_SECRET_KEY = ""
STRIPE_PUBLIC_KEY = ""

# Database (Optional - for PostgreSQL)
DATABASE_URL = ""
"""
    
    with open(".streamlit/secrets.toml", "w") as f:
        f.write(secrets_content)
    print("✅ Created .streamlit/secrets.toml")
    print("⚠️  IMPORTANT: Keep this file secret!")
    
    # Check if source modules already exist
    print("\n📁 Checking source modules...")
    
    # Create __init__.py if not exists
    if not os.path.exists("src/__init__.py"):
        with open("src/__init__.py", "w") as f:
            f.write('"""Omniscient One Source Modules"""\n')
        print("✅ Created src/__init__.py")
    
    # Copy source modules if they don't exist
    source_files = ["auth.py", "database.py", "subscription.py"]
    for file in source_files:
        src_path = f"src/{file}"
        if not os.path.exists(src_path):
            print(f"⚠️  {file} not found in src/ directory")
            print(f"   Please create src/{file} with the provided code")
    
    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETE!")
    print("=" * 60)
    
    print("\n📋 NEXT STEPS:")
    print("1. 📁 Create the source modules (auth.py, database.py, subscription.py) in src/")
    print("2. 🚀 Test locally: streamlit run app.py")
    print("3. 💾 Commit to GitHub: git add . && git commit -m 'Deployment ready' && git push")
    print("4. ☁️  Deploy on Streamlit Cloud:")
    print("   - Go to https://share.streamlit.io")
    print("   - Click 'New app'")
    print("   - Select your repository: omniscient-one")
    print("   - Branch: main")
    print("   - Main file path: app.py")
    print("   - Click 'Advanced settings'")
    print("   - Add secrets from .streamlit/secrets.toml")
    print("   - Click 'Deploy!'")
    
    print("\n🔧 TROUBLESHOOTING:")
    print("- If modules fail to import: Make sure src/ directory exists")
    print("- If S3 connection fails: Check your S3 credentials")
    print("- If database errors: Check if data/ directory is writable")
    
    print("\n🚀 YOUR TRADING PLATFORM IS READY FOR DEPLOYMENT!")

def test_installation():
    """Test if all dependencies are installed"""
    print("\n🧪 Testing installation...")
    
    dependencies = [
        ("streamlit", "Streamlit"),
        ("pandas", "Pandas"),
        ("plotly", "Plotly"),
        ("yfinance", "Yahoo Finance"),
        ("boto3", "AWS Boto3"),
        ("sqlalchemy", "SQLAlchemy")
    ]
    
    all_ok = True
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"✅ {name} installed")
        except ImportError:
            print(f"❌ {name} NOT installed")
            all_ok = False
    
    if not all_ok:
        print("\n⚠️  Some dependencies missing. Install with:")
        print("pip install -r requirements.txt")
    
    return all_ok

if __name__ == "__main__":
    setup_complete_deployment()
    test_installation()
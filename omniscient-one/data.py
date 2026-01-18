# setup_data.py
"""
Setup script to create the data directory structure
Run this once before starting the app
"""

import os
import sys

def create_data_structure():
    """Create the necessary data directory structure"""
    
    print("=" * 60)
    print("📁 CREATING DATA DIRECTORY STRUCTURE")
    print("=" * 60)
    
    # Create main directories
    directories = [
        "data",
        "data/backups",
        "data/logs",
        "data/exports",
        "data/cache"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except Exception as e:
            print(f"❌ Failed to create {directory}: {e}")
    
    # Create required files
    files = {
        "data/README.md": "# Data Directory\n\nThis directory contains all user data, backups, and logs.",
        "data/.gitignore": "# Ignore all files in data directory\n*\n!.gitignore\n!README.md",
        "data/logs/README.md": "# Logs Directory\n\nApplication logs are stored here.",
        "data/backups/README.md": "# Backups Directory\n\nDatabase backups are stored here."
    }
    
    for file_path, content in files.items():
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Created file: {file_path}")
        except Exception as e:
            print(f"❌ Failed to create {file_path}: {e}")
    
    # Set permissions (Unix-like systems)
    if sys.platform != "win32":
        try:
            # Make data directory readable/writable
            os.chmod("data", 0o755)
            print("✅ Set directory permissions")
        except:
            pass
    
    print("\n" + "=" * 60)
    print("✅ DATA STRUCTURE CREATED SUCCESSFULLY")
    print("=" * 60)
    print("\n📋 Directory structure:")
    print("data/")
    print("├── backups/     # Database backups")
    print("├── logs/        # Application logs")
    print("├── exports/     # Data exports (CSV, Excel)")
    print("├── cache/       # Cached market data")
    print("├── .gitignore   # Ignore data files in git")
    print("└── README.md    # Documentation")
    
    print("\n🚀 Your data directory is ready!")
    print("The database will be automatically created when you run the app.")

if __name__ == "__main__":
    create_data_structure()
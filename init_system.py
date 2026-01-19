#!/usr/bin/env python3
"""
Industrace System Initialization Script
========================================

This script provides a clean way to initialize the Industrace system with:
- Database setup and migrations
- Default tenant and roles
- Admin accounts with @example.com emails
- Demo data pre-population

Usage:
    python init_system.py [--clean] [--demo-only]

Options:
    --clean      Clean database and start fresh
    --demo-only  Only populate demo data (assumes system already initialized)
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Add the backend app directory to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def check_docker():
    """Check if Docker is running"""
    print("🔍 Checking Docker...")
    try:
        subprocess.run(["docker", "info"], check=True, capture_output=True)
        print("✅ Docker is running")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not running or not available")
        return False

def clean_database():
    """Clean the database completely"""
    print("🧹 Cleaning database...")
    
    # Stop containers
    if not run_command("docker-compose -f docker-compose.dev.yml down", "Stopping containers"):
        return False
    
    # Remove volumes
    if not run_command("docker volume rm industrace_industrace_postgres_data", "Removing database volume"):
        print("   Note: Volume might not exist, continuing...")
    
    print("✅ Database cleaned")
    return True

def start_services():
    """Start the services"""
    print("🚀 Starting services...")
    
    # Build and start services
    if not run_command("docker-compose -f docker-compose.dev.yml up -d", "Starting services"):
        return False
    
    # Wait for services to be ready
    print("⏳ Waiting for services to be ready...")
    import time
    time.sleep(15)
    
    return True

def run_migrations():
    """Run database migrations"""
    print("📊 Running database migrations...")
    
    # Run Alembic migrations
    if not run_command("docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head", "Running migrations"):
        return False
    
    return True

def initialize_system():
    """Initialize the system with default data"""
    print("🔧 Initializing system...")
    
    # Run system setup
    if not run_command("docker-compose -f docker-compose.dev.yml exec backend python -c \"from app.setup_system import setup_system; setup_system()\"", "Setting up system"):
        return False
    
    return True

def populate_demo_data():
    """Populate demo data"""
    print("🌱 Populating demo data...")
    
    # Run demo data seeding
    if not run_command("docker-compose -f docker-compose.dev.yml exec backend python -c \"from app.init_demo_data import seed_demo_data; seed_demo_data()\"", "Seeding demo data"):
        return False
    
    return True

def verify_system():
    """Verify the system is working"""
    print("🔍 Verifying system...")
    
    # Test API health
    import time
    time.sleep(5)  # Give API time to start
    
    try:
        import requests
        response = requests.get("http://localhost:8000/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ API is responding")
        else:
            print(f"⚠️  API returned status {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not verify API: {e}")
    
    # Test login
    try:
        response = requests.post(
            "http://localhost:8000/login",
            data={"email": "admin@example.com", "password": "Admin@123456!"},
            timeout=10
        )
        if response.status_code == 200:
            print("✅ Login test successful")
        else:
            print(f"⚠️  Login test failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not test login: {e}")

def print_credentials():
    """Print login credentials"""
    print("\n" + "="*60)
    print("🎉 SYSTEM INITIALIZATION COMPLETED!")
    print("="*60)
    print("\n📋 Login Credentials:")
    print("   Admin:   admin@example.com / Admin@123456!")
    print("   Editor:  editor@example.com / Editor@123456!")
    print("   Viewer:  viewer@example.com / Viewer@123456!")
    print("\n🌐 Access URLs:")
    print("   Frontend: http://localhost:5173")
    print("   Backend API: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("\n📊 Demo Data Included:")
    print("   • 3 Sites (Production Plant, R&D Center, Warehouse)")
    print("   • 12 Areas (Assembly Lines, Labs, Control Rooms)")
    print("   • 4 Manufacturers (Siemens, Rockwell, Schneider, ABB)")
    print("   • 4 Suppliers and 6 Contacts")
    print("   • 3 Assets (PLC, HMI, Robot)")
    print("\n" + "="*60)

def main():
    parser = argparse.ArgumentParser(description="Initialize Industrace system")
    parser.add_argument("--clean", action="store_true", help="Clean database and start fresh")
    parser.add_argument("--demo-only", action="store_true", help="Only populate demo data")
    
    args = parser.parse_args()
    
    print("🏭 Industrace System Initialization")
    print("="*50)
    
    # Check Docker
    if not check_docker():
        sys.exit(1)
    
    if args.demo_only:
        # Only populate demo data
        print("\n📝 Demo-only mode: Populating demo data only...")
        if not populate_demo_data():
            sys.exit(1)
        print_credentials()
        return
    
    if args.clean:
        # Clean start
        print("\n🧹 Clean mode: Starting fresh...")
        if not clean_database():
            sys.exit(1)
    
    # Start services
    if not start_services():
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        sys.exit(1)
    
    # Initialize system
    if not initialize_system():
        sys.exit(1)
    
    # Populate demo data
    if not populate_demo_data():
        sys.exit(1)
    
    # Verify system
    verify_system()
    
    # Print credentials
    print_credentials()

if __name__ == "__main__":
    main() 
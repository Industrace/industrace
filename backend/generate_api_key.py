#!/usr/bin/env python3

"""
Script to generate API keys for external APIs of Industrace

Usage:
  python generate_api_key.py create <name> <email> [scopes] [rate_limit] [expires_days]
  python generate_api_key.py list <email>

Examples:
  python generate_api_key.py create 'Test API' admin@example.com
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ApiKey, User
from app.services.auth import get_password_hash
from app.config import settings


def generate_api_key(
    name: str,
    user_email: str,
    scopes: list = None,
    rate_limit: str = "100/hour",
    expires_days: int = 365,
):
    """Generates a new API Key"""

    # Default configuration
    if scopes is None:
        scopes = ["read"]

    # Calculate expiration date
    expires_at = datetime.utcnow() + timedelta(days=expires_days)

    # Generate the key
    api_key_value = f"ind_{uuid.uuid4().hex[:32]}"

    # Hash the key for the database
    hashed_key = get_password_hash(api_key_value)

    # Find the user
    db = next(get_db())
    user = db.query(User).filter(User.email == user_email).first()

    if not user:
        # print(f"User {user_email} not found")
        return None

    # Create the API Key
    api_key = ApiKey(
        name=name,
        key_hash=hashed_key,
        user_id=user.id,
        tenant_id=user.tenant_id,
        scopes=scopes,
        rate_limit=rate_limit,
        expires_at=expires_at,
        is_active=True,
    )

    try:
        db.add(api_key)
        db.commit()
        db.refresh(api_key)

        # print("API Key generated successfully!")
        # print(f"Name: {name}")
        # print(f"API Key: {api_key_value}")
        # print(f"User: {user_email}")
        # print(f"Tenant: {user.tenant_id}")
        # print(f"Scopes: {', '.join(scopes)}")
        # print(f"Rate Limit: {rate_limit}")
        # print(f"Expiration: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        # print(f"ID: {api_key.id}")

        return api_key_value

    except Exception as e:
        # print(f"Error creating API Key: {e}")
        db.rollback()
        return None
    finally:
        db.close()


def list_api_keys(user_email: str):
    """List all API Keys for a user"""
    db = next(get_db())
    user = db.query(User).filter(User.email == user_email).first()

    if not user:
        # print(f"User {user_email} not found")
        return

    api_keys = db.query(ApiKey).filter(ApiKey.user_id == user.id).all()

    if not api_keys:
        # print("No API Keys found")
        return

    # print(f"API Keys for {user_email}:")
    # print("-" * 80)

    for key in api_keys:
        status = "Active" if key.is_active else "Inactive"
        expires = (
            key.expires_at.strftime("%Y-%m-%d %H:%M:%S") if key.expires_at else "Never"
        )

        # print(f"ID: {key.id}")
        # print(f"Name: {key.name}")
        # print(f"Scopes: {', '.join(key.scopes)}")
        # print(f"Rate Limit: {key.rate_limit}")
        # print(f"Expiration: {expires}")
        # print(f"Status: {status}")
        # print(f"Created: {key.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        # print("-" * 80)


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print(
            "  python generate_api_key.py create <name> <email> [scopes] [rate_limit] [expires_days]"
        )
        print("  python generate_api_key.py list <email>")
        print("")
        print("Examples:")
        print("  python generate_api_key.py create 'Test API' admin@example.com")
        print(
            "  python generate_api_key.py create 'Read Only' user@example.com read 50/hour 30"
        )
        print("  python generate_api_key.py list admin@example.com")
        return

    command = sys.argv[1]

    if command == "create":
        if len(sys.argv) < 4:
            print("Command create requires: name, email")
            return

        name = sys.argv[2]
        email = sys.argv[3]
        scopes = sys.argv[4].split(",") if len(sys.argv) > 4 else ["read"]
        rate_limit = sys.argv[5] if len(sys.argv) > 5 else "100/hour"
        expires_days = int(sys.argv[6]) if len(sys.argv) > 6 else 365

        generate_api_key(name, email, scopes, rate_limit, expires_days)

    elif command == "list":
        if len(sys.argv) < 3:
            print("Command list requires: email")
            return

        email = sys.argv[2]
        list_api_keys(email)

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()

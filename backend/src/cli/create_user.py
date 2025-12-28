"""CLI utility to create a new user in the database."""

import argparse
import sys
import uuid
from datetime import datetime, timezone

# Add the project root to the path if needed
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.src.database.connection import init_database, get_db_session_context
from backend.src.models.user import User
from backend.src.core.security import hash_password

def create_user(email, password, full_name, tier="Basic"):
    """Create a new user in the database."""
    init_database()
    
    with get_db_session_context() as session:
        # Check if user already exists
        existing_user = session.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"Error: User with email '{email}' already exists.")
            return False

        # Create new user
        new_user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            subscription_tier=tier,
            is_active=True
        )
        
        session.add(new_user)
        print(f"Successfully created user: {full_name} ({email})")
        return True

def main():
    parser = argparse.ArgumentParser(description="Create a new user for FNA Platform")
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument("--password", required=True, help="User password")
    parser.add_argument("--name", required=True, help="User full name")
    parser.add_argument("--tier", default="Enterprise", choices=["Basic", "Pro", "Enterprise"], help="Subscription tier")

    args = parser.parse_args()
    
    try:
        if create_user(args.email, args.password, args.name, args.tier):
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"Failed to create user: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
Cyber Raksha AI - Admin User Setup & Management CLI
Run this script to create or update an administrator account for the SOC Control Room.
Usage:
    python create_admin.py
    python create_admin.py --username myadmin --password MySecurePassword123! --email admin@example.com
"""
import sys
import argparse
from datetime import datetime, timezone

from app.database.session import SessionLocal
from app.models.user import User
from app.core.auth_utils import hash_password


def create_or_update_admin(username: str, password: str, email: str, full_name: str = "SOC Administrator"):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            user.hashed_password = hash_password(password)
            user.email = email
            user.full_name = full_name
            user.role = "admin"
            user.is_active = True
            user.is_superuser = True
            db.commit()
            print(f"[SUCCESS] Updated existing administrator '{username}' successfully.")
        else:
            new_user = User(
                email=email,
                username=username,
                hashed_password=hash_password(password),
                full_name=full_name,
                role="admin",
                is_active=True,
                is_superuser=True,
                is_email_verified=True,
                is_mobile_verified=True,
                consent_given=True,
                consent_timestamp=datetime.now(timezone.utc)
            )
            db.add(new_user)
            db.commit()
            print(f"[SUCCESS] Created new administrator '{username}' ({email}) successfully.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to create or update administrator: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create or update Cyber Raksha AI SOC administrator.")
    parser.add_argument("--username", default="admin", help="Administrator username (default: admin)")
    parser.add_argument("--password", default="CyberRaksha@Admin2026!", help="Administrator password")
    parser.add_argument("--email", default="admin@cyberraksha.ai", help="Administrator email")
    parser.add_argument("--name", default="SOC Administrator", help="Administrator full name")

    args = parser.parse_args()
    create_or_update_admin(
        username=args.username,
        password=args.password,
        email=args.email,
        full_name=args.name
    )

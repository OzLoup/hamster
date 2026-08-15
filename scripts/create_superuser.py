"""One-off bootstrap: create a platform superuser (not tied to any business).

Usage:
    python -m scripts.create_superuser --email you@example.com --full-name "Your Name" --password "..."

If --password is omitted, you'll be prompted (hidden input) via getpass.
"""

import argparse
import getpass
import sys

from app.core.security import hash_password
from app.database.database import SessionLocal
from app.models.user import User


def create_superuser(email: str, full_name: str, password: str) -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing is not None:
            print(f"A user with email '{email}' already exists (id={existing.id}).", file=sys.stderr)
            sys.exit(1)

        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=None,
            business_id=None,
            is_superuser=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Superuser created: id={user.id} email={user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--full-name", required=True)
    parser.add_argument("--password", default=None, help="If omitted, you'll be prompted.")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Password: ")
    if len(password) < 8:
        print("Password must be at least 8 characters.", file=sys.stderr)
        sys.exit(1)

    create_superuser(args.email, args.full_name, password)

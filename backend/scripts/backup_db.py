"""
backend/scripts/backup_db.py
Database Backup Utility for Cyber Raksha AI.
Stage 8: Reliability & Data Consistency

Usage:
    python backend/scripts/backup_db.py
"""
import os
import shutil
import sqlite3
import hashlib
from datetime import datetime, timezone


def backup_database():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    db_file = os.path.join(base_dir, "cyber_raksha.db")
    backup_dir = os.path.join(base_dir, "backend", "backups")

    if not os.path.exists(db_file):
        print(f"[ERROR] Database file not found at: {db_file}")
        return False

    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_filename = f"cyber_raksha_backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)

    # Use SQLite Online Backup API for consistent snapshot
    print(f"[*] Starting backup from {db_file}...")
    try:
        source_conn = sqlite3.connect(db_file)
        dest_conn = sqlite3.connect(backup_path)
        with dest_conn:
            source_conn.backup(dest_conn, pages=100)
        dest_conn.close()
        source_conn.close()
    except Exception as e:
        print(f"[ERROR] Backup failed: {e}")
        return False

    # Verify integrity of the backup file
    try:
        check_conn = sqlite3.connect(backup_path)
        cursor = check_conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        status = cursor.fetchone()[0]
        check_conn.close()
        if status != "ok":
            print(f"[ERROR] Backup integrity check failed: {status}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to verify backup integrity: {e}")
        return False

    # Compute SHA256
    with open(backup_path, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()

    file_size_kb = os.path.getsize(backup_path) / 1024
    print(f"[SUCCESS] Backup created successfully!")
    print(f"  Location: {backup_path}")
    print(f"  Size:     {file_size_kb:.1f} KB")
    print(f"  SHA256:   {sha256}")
    print(f"  Integrity: OK")
    return True


if __name__ == "__main__":
    success = backup_database()
    exit(0 if success else 1)


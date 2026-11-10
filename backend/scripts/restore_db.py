"""
backend/scripts/restore_db.py
Database Restore Utility for Cyber Raksha AI.
Stage 8: Reliability & Data Consistency

Usage:
    python backend/scripts/restore_db.py [optional_backup_filepath]
"""
import os
import sys
import shutil
import sqlite3
import hashlib


def restore_database(backup_filepath=None):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    db_file = os.path.join(base_dir, "cyber_raksha.db")
    backup_dir = os.path.join(base_dir, "backend", "backups")

    # If no specific backup provided, find the most recent
    if not backup_filepath:
        if not os.path.exists(backup_dir):
            print(f"[ERROR] No backups directory found at: {backup_dir}")
            return False
        backups = [f for f in os.listdir(backup_dir) if f.startswith("cyber_raksha_backup_") and f.endswith(".db")]
        if not backups:
            print("[ERROR] No backup files found in backup directory.")
            return False
        backups.sort()
        backup_filepath = os.path.join(backup_dir, backups[-1])

    if not os.path.exists(backup_filepath):
        print(f"[ERROR] Specified backup file does not exist: {backup_filepath}")
        return False

    # 1. Verify backup integrity before touching destination
    print(f"[*] Verifying source backup integrity: {backup_filepath}...")
    try:
        check_conn = sqlite3.connect(backup_filepath)
        cursor = check_conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        status = cursor.fetchone()[0]
        check_conn.close()
        if status != "ok":
            print(f"[ERROR] Source backup is corrupted: {status}")
            return False
    except Exception as e:
        print(f"[ERROR] Cannot open source backup: {e}")
        return False

    # 2. Safety copy of current database if exists
    if os.path.exists(db_file):
        safety_path = db_file + ".pre_restore_safety"
        print(f"[*] Creating pre-restore safety copy at: {safety_path}...")
        shutil.copy2(db_file, safety_path)

    # 3. Restore using SQLite Online Backup API
    print(f"[*] Restoring database to {db_file}...")
    try:
        source_conn = sqlite3.connect(backup_filepath)
        dest_conn = sqlite3.connect(db_file)
        with dest_conn:
            source_conn.backup(dest_conn, pages=100)
        dest_conn.close()
        source_conn.close()
    except Exception as e:
        print(f"[ERROR] Restore operation failed: {e}")
        return False

    # 4. Final verification
    try:
        final_conn = sqlite3.connect(db_file)
        cursor = final_conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        status = cursor.fetchone()[0]
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]
        final_conn.close()
        if status != "ok":
            print(f"[ERROR] Restored database integrity check failed: {status}")
            return False
        print(f"[SUCCESS] Database successfully restored from: {backup_filepath}")
        print(f"  Integrity: OK")
        print(f"  Tables:    {len(tables)} tables verified")
        return True
    except Exception as e:
        print(f"[ERROR] Failed final integrity check: {e}")
        return False


if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else None
    success = restore_database(filepath)
    exit(0 if success else 1)


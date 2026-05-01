import sqlite3
import random
import string
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / 'data.db'


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(cursor, table, column, definition):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingame_name TEXT NOT NULL,
            discord_user_id TEXT,
            age_group TEXT NOT NULL,
            country TEXT NOT NULL,
            highest_rank TEXT NOT NULL,
            highest_trophies TEXT NOT NULL,
            club_member TEXT NOT NULL,
            profile_image TEXT,
            privacy_opened TEXT DEFAULT 'false',
            privacy_scrolled TEXT DEFAULT 'false',
            status TEXT DEFAULT 'pending',
            link_code TEXT UNIQUE,
            announced_to_discord INTEGER DEFAULT 0
        )
        '''
    )
    _ensure_column(cursor, 'submissions', 'announced_to_discord', 'INTEGER DEFAULT 0')
    conn.commit()
    conn.close()


def generate_link_code(length=6):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def save_submission(ingame_name, age_group, country, highest_rank, highest_trophies, club_member, profile_image, privacy_opened, privacy_scrolled):
    conn = get_connection()
    cursor = conn.cursor()
    link_code = generate_link_code()

    cursor.execute(
        '''
        INSERT INTO submissions (
            ingame_name, age_group, country, highest_rank, highest_trophies,
            club_member, profile_image, privacy_opened, privacy_scrolled, status, link_code,
            announced_to_discord
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            ingame_name,
            age_group,
            country,
            highest_rank,
            highest_trophies,
            club_member,
            profile_image,
            privacy_opened,
            privacy_scrolled,
            'pending',
            link_code,
            0,
        )
    )

    conn.commit()
    conn.close()
    return link_code


def link_discord_account(link_code, discord_user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        UPDATE submissions
        SET discord_user_id = ?, status = 'linked'
        WHERE link_code = ? AND discord_user_id IS NULL
        ''',
        (str(discord_user_id), link_code)
    )
    conn.commit()
    changed = cursor.rowcount
    conn.close()
    return changed > 0


def get_submission(submission_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_unannounced_submissions(limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM submissions WHERE announced_to_discord = 0 ORDER BY id ASC LIMIT ?',
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def mark_submission_announced(submission_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE submissions SET announced_to_discord = 1 WHERE id = ?',
        (submission_id,),
    )
    conn.commit()
    conn.close()


def get_recent_submission_ids(limit=100):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM submissions ORDER BY id DESC LIMIT ?', (limit,))
    ids = [row['id'] for row in cursor.fetchall()]
    conn.close()
    return ids  
    hgcb

import sqlite3
import pandas as pd
from config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with open('schema.sql', 'r') as f:
        conn = get_connection()
        conn.executescript(f.read())
        conn.commit()
        conn.close()

def add_user(telegram_id, username=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)",
                   (telegram_id, username))
    conn.commit()
    conn.close()

def log_day(telegram_id, mood, work_hours, sleep_hours, comment='', date=None):
    from datetime import date as dt
    if date is None:
        date = dt.today().isoformat()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем ID пользователя
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    if not user:
        add_user(telegram_id)
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user = cursor.fetchone()
    
    user_id = user['id']
    
    cursor.execute("""
        INSERT INTO daily_logs (user_id, mood, work_hours, sleep_hours, comment, date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, mood, work_hours, sleep_hours, comment, date))
    
    conn.commit()
    conn.close()
    return True

def get_weekly_stats(telegram_id):
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT * FROM daily_logs 
        JOIN users ON daily_logs.user_id = users.id 
        WHERE users.telegram_id = ? 
        AND date >= date('now', '-7 days')
        ORDER BY date DESC
    """, conn, params=(telegram_id,))
    conn.close()
    return df

def get_monthly_stats(telegram_id):
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT * FROM daily_logs 
        JOIN users ON daily_logs.user_id = users.id 
        WHERE users.telegram_id = ? 
        AND date >= date('now', '-30 days')
        ORDER BY date DESC
    """, conn, params=(telegram_id,))
    conn.close()
    return df

def get_insights(telegram_id):
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT mood, AVG(work_hours) as avg_work, AVG(sleep_hours) as avg_sleep
        FROM daily_logs 
        JOIN users ON daily_logs.user_id = users.id 
        WHERE users.telegram_id = ?
        GROUP BY mood
        ORDER BY mood
    """, conn, params=(telegram_id,))
    conn.close()
    return df

def clear_user_data(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM daily_logs WHERE user_id IN (SELECT id FROM users WHERE telegram_id = ?)", (telegram_id,))
    conn.commit()
    conn.close()
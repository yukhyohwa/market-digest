
import sqlite3
import os
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
DB_DIR = DATA_DIR  # Move DB to data directory
DB_NAME = 'finance_data.db'
DB_PATH = os.path.join(DB_DIR, DB_NAME)

def get_db_connection():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Bond Issuance Table (New Bonds)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bond_issuance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bond_code TEXT,
            bond_name TEXT,
            subscription_date TEXT,
            listing_date TEXT,
            details TEXT,
            date TEXT,
            timestamp DATETIME
        )
    ''')
    
    # Forex Rates Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forex_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            currency TEXT,
            bank TEXT,
            spot_buy REAL,
            cash_buy REAL,
            spot_sell REAL,
            cash_sell REAL,
            date TEXT,
            timestamp DATETIME
        )
    ''')

    # Market Indices Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_indices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            name TEXT,
            price REAL,
            change REAL,
            change_pct REAL,
            prev_close REAL,
            date TEXT,
            timestamp DATETIME
        )
    ''')

    # Commodities Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commodities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            name TEXT,
            price REAL,
            change REAL,
            change_pct REAL,
            date TEXT,
            timestamp DATETIME
        )
    ''')

    # Fund OTC Limits Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fund_otc_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fund_id TEXT,
            fund_name TEXT,
            nav REAL,
            apply_status TEXT,
            date TEXT,
            timestamp DATETIME
        )
    ''')

    # Important Economic Events (remaining in the current week, including today)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS economic_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_time TEXT,
            country TEXT,
            impact TEXT,
            title TEXT,
            forecast TEXT,
            previous TEXT,
            date TEXT,
            timestamp DATETIME
        )
    ''')

    # Preserve the distinction between no matching events and source failure.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS economic_calendar_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ok INTEGER,
            records INTEGER,
            error TEXT,
            date TEXT,
            timestamp DATETIME
        )
    ''')
    
    conn.commit()
    conn.close()

def clear_todays_data(table_name):
    """
    Removes data for the current date to ensure idempotency (latest data only).
    """
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE date = ?", (today,))
    conn.commit()
    deleted_count = cursor.rowcount
    conn.close()
    if deleted_count > 0:
        print(f"Cleared {deleted_count} old records from {table_name} for today ({today}).")
    return today

def save_data(table_name, records):
    """
    Saves a list of dictionaries to the specified table.
    Assumes records have keys matching column names (except id, date, timestamp).
    """
    if not records:
        print(f"No records to save for {table_name}.")
        return

    init_db()
    today = clear_todays_data(table_name)
    timestamp = datetime.now().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if not records: return
    
    processed_records = []
    for r in records:
        r_copy = r.copy()
        r_copy['date'] = today
        r_copy['timestamp'] = timestamp
        processed_records.append(r_copy)
    
    columns = list(processed_records[0].keys())
    placeholders = ', '.join(['?' for _ in columns])
    col_names = ', '.join(columns)
    
    values = [tuple(r[c] for c in columns) for r in processed_records]
    
    query = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
    
    try:
        cursor.executemany(query, values)
        conn.commit()
        print(f"Saved {len(records)} records to {table_name}.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

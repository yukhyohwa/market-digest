
import sqlite3
from app.core.db import get_db_connection

def fetch_daily_data(table_name, date_str, columns="*"):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT {columns} FROM {table_name} WHERE date = ?", (date_str,))
        rows = cursor.fetchall()
        # Get column names
        col_names = [description[0] for description in cursor.description]
        return rows, col_names
    except sqlite3.Error as e:
        print(f"Error reading {table_name}: {e}")
        return [], []
    finally:
        conn.close()

def fetch_daily_status(table_name, date_str):
    """Fetch the latest collector status row for a report date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"SELECT ok, records, error FROM {table_name} WHERE date = ? ORDER BY id DESC LIMIT 1",
            (date_str,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {"ok": bool(row[0]), "records": row[1], "error": row[2]}
    except sqlite3.Error as e:
        print(f"Error reading {table_name}: {e}")
        return None
    finally:
        conn.close()

def get_previous_otc_status(fund_id, today_str):
    """Fetches the most recent OTC status for a fund before today, ideally 7 days ago."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Find the latest date before today
        cursor.execute("SELECT apply_status FROM fund_otc_limits WHERE fund_id = ? AND date <= date(?, '-7 days') ORDER BY date DESC LIMIT 1", (fund_id, today_str))
        row = cursor.fetchone()
        if row: return row[0]
        
        # If no data from 7+ days ago, just get the oldest/latest available before today
        cursor.execute("SELECT apply_status FROM fund_otc_limits WHERE fund_id = ? AND date < ? ORDER BY date DESC LIMIT 1", (fund_id, today_str))
        row = cursor.fetchone()
        if row: return row[0]
        return None
    except sqlite3.Error as e:
        print(f"Error reading historical OTC status: {e}")
        return None
    finally:
        conn.close()

def format_table(rows, headers, alignments=None):
    if not rows:
        return "*No data available for today.*"
        
    header_line = "| " + " | ".join(headers) + " |"
    
    align_map = {'left': ':---', 'right': '---:', 'center': ':---:'}
    if not alignments:
        alignments = ['left'] * len(headers)
    
    separator_line = "| " + " | ".join([align_map.get(a, ':---') for a in alignments]) + " |"
    
    body = ""
    for row in rows:
        row_str = [str(x).replace('|', '\\|') for x in row]
        body += "| " + " | ".join(row_str) + " |\n"
        
    return f"{header_line}\n{separator_line}\n{body}"

import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone

import requests

from app.core.db import clear_todays_data, get_db_connection, init_db, save_data


JSON_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
XML_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
TIMEOUT = 20
IMPORTANT_COUNTRIES = {"CNY", "USD", "JPY", "GBP"}
IMPORTANT_IMPACTS = {"High", "Medium"}
CHINA_TZ = timezone(timedelta(hours=8))


def _fetch_source_rows():
    """Return calendar rows and timezone-aware source timestamps."""
    try:
        response = requests.get(JSON_URL, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        return [
            (row, datetime.fromisoformat(row["date"]))
            for row in response.json()
        ], None
    except Exception as json_error:
        response = requests.get(XML_URL, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        source_rows = []
        for node in root.findall(".//event"):
            row = {child.tag: (child.text or "").strip() for child in node}
            # The XML feed exposes a UTC clock time without an explicit offset.
            event_time = datetime.strptime(
                f"{row['date']} {row['time']}", "%m-%d-%Y %I:%M%p"
            ).replace(tzinfo=timezone.utc)
            source_rows.append((row, event_time))
        return source_rows, f"JSON source failed; used XML fallback: {json_error}"


def fetch_economic_calendar(today=None):
    """Fetch important events remaining in the source's current week."""
    today = today or datetime.now(CHINA_TZ).date()
    source_rows, fallback_note = _fetch_source_rows()

    events = []
    for row, source_time in source_rows:
        if row.get("country") not in IMPORTANT_COUNTRIES:
            continue
        if row.get("impact") not in IMPORTANT_IMPACTS:
            continue

        event_time = source_time.astimezone(CHINA_TZ)
        if event_time.date() >= today:
            events.append(
                {
                    "event_time": event_time.strftime("%Y-%m-%d %H:%M"),
                    "country": row.get("country") or "-",
                    "impact": row.get("impact") or "-",
                    "title": row.get("title") or "-",
                    "forecast": row.get("forecast") or "-",
                    "previous": row.get("previous") or "-",
                }
            )

    events.sort(key=lambda item: item["event_time"])
    return events, fallback_note


def _save_status(ok, records, error=None):
    today = datetime.now(CHINA_TZ).date().isoformat()
    timestamp = datetime.now(CHINA_TZ).isoformat()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM economic_calendar_status WHERE date = ?", (today,))
        cursor.execute(
            """
            INSERT INTO economic_calendar_status (ok, records, error, date, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (1 if ok else 0, records, error, today, timestamp),
        )
        conn.commit()
    finally:
        conn.close()


def main():
    print("Starting Important Economic Calendar Collector...")
    init_db()
    try:
        events, fallback_note = fetch_economic_calendar()
        if events:
            save_data("economic_calendar", events)
        else:
            clear_todays_data("economic_calendar")
        _save_status(True, len(events), fallback_note)
        print(f"Found {len(events)} important economic events remaining this week (including today).")
        if fallback_note:
            print(f"[WARN] {fallback_note}")
    except Exception as exc:
        clear_todays_data("economic_calendar")
        _save_status(False, 0, str(exc))
        print(f"[ERROR] Economic calendar source failed: {exc}")
    print("Economic Calendar Task Complete.")


if __name__ == "__main__":
    main()

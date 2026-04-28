"""
Govee H5140 data collector — appends a reading to data/readings.json.

Usage:
    python collect_20260426.py            # fetch and append
    python collect_20260426.py --dry-run  # print reading without writing

Requires:
    GOVEE_API_KEY in .env (local) or environment (CI).
    pip install requests python-dotenv
"""

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

DEVICE_SKU = "H5140"
DEVICE_ID = "53:8C:0C:4E:A0:DA:0C:0C"
API_URL = "https://openapi.api.govee.com/router/api/v1/device/state"
DATA_FILE = Path(__file__).parent / "data" / "readings.json"


def _load_env() -> None:
    """Load .env if present (local dev). No-op if dotenv is not installed."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def _get_api_key() -> str:
    key = os.environ.get("GOVEE_API_KEY", "").strip()
    if not key:
        print("ERROR: GOVEE_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)
    return key


def fetch_reading() -> dict:
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(1, max_retries + 1):
        try:
            payload = {
                "requestId": str(uuid.uuid4()),
                "payload": {"sku": DEVICE_SKU, "device": DEVICE_ID},
            }
            headers = {
                "Govee-API-Key": _get_api_key(),
                "Content-Type": "application/json",
            }
            response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            body = response.json()

            if body.get("code") != 200:
                print(f"ERROR: API returned code {body.get('code')}: {body.get('msg')}", file=sys.stderr)
                if attempt < max_retries:
                    print(f"Retrying in {retry_delay}s... (attempt {attempt}/{max_retries})", file=sys.stderr)
                    time.sleep(retry_delay)
                    continue
                sys.exit(1)

            caps = {c["instance"]: c["state"]["value"] for c in body["payload"]["capabilities"]}

            return {
                "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "co2": caps.get("carbonDioxideConcentration"),
                "temp_f": caps.get("sensorTemperature"),
                "humidity": caps.get("sensorHumidity"),
                "online": caps.get("online", False),
            }
        except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError) as e:
            print(f"Attempt {attempt}/{max_retries} failed: {type(e).__name__}: {e}", file=sys.stderr)
            if attempt < max_retries:
                print(f"Retrying in {retry_delay}s...", file=sys.stderr)
                time.sleep(retry_delay)
            else:
                print(f"ERROR: Failed after {max_retries} attempts.", file=sys.stderr)
                sys.exit(1)


def append_reading(reading: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        existing = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    else:
        existing = []
    existing.append(reading)
    DATA_FILE.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    print(f"Appended reading: {reading}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect a Govee H5140 reading.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch but do not write.")
    args = parser.parse_args()

    _load_env()
    reading = fetch_reading()
    print(f"Reading: {json.dumps(reading)}")

    if args.dry_run:
        print("(dry-run: not written to disk)")
        return

    append_reading(reading)


if __name__ == "__main__":
    main()

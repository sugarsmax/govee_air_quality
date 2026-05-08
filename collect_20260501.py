"""
Govee multi-device air quality collector — appends readings to data/readings.json.

Each reading is tagged with a 'device' label so data from multiple sensors can be
distinguished in analysis and visualization.

Usage:
    python collect_20260501.py            # fetch all devices and append
    python collect_20260501.py --dry-run  # print readings without writing

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

# ---------------------------------------------------------------------------
# Device registry — add / remove entries here as sensors change.
# Each dict must have: label (unique short name), sku, device (MAC-style ID).
# ---------------------------------------------------------------------------
DEVICES = [
    {
        "label": "basement",
        "sku": "H5140",
        "device": "53:8C:0C:4E:A0:DA:0C:0C",
    },
    {
        "label": "upstairs",
        "sku": "H5140",
        "device": "17:A0:3C:0F:02:26:96:00",
    },
]

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


def fetch_reading(sku: str, device_id: str, api_key: str, max_retries: int = 3) -> dict:
    """POST to the Govee Open API and return a parsed sensor reading.

    Retries up to max_retries times with exponential backoff on network errors.
    """
    headers = {
        "Govee-API-Key": api_key,
        "Content-Type": "application/json",
    }
    last_exc: Exception = RuntimeError("No attempts made")
    for attempt in range(1, max_retries + 1):
        try:
            payload = {
                "requestId": str(uuid.uuid4()),
                "payload": {"sku": sku, "device": device_id},
            }
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            body = response.json()

            if body.get("code") != 200:
                raise RuntimeError(f"API returned code {body.get('code')}: {body.get('msg')}")

            caps = {c["instance"]: c["state"]["value"] for c in body["payload"]["capabilities"]}

            return {
                "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "co2": caps.get("carbonDioxideConcentration"),
                "temp_f": caps.get("sensorTemperature"),
                "humidity": caps.get("sensorHumidity"),
                "online": caps.get("online", False),
            }
        except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError) as exc:
            last_exc = exc
            if attempt < max_retries:
                delay = 2 ** attempt
                print(f"  attempt {attempt}/{max_retries} failed ({exc}), retrying in {delay}s…", file=sys.stderr)
                time.sleep(delay)
    raise last_exc


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
    parser = argparse.ArgumentParser(
        description="Collect Govee air quality readings from all configured devices."
    )
    parser.add_argument("--dry-run", action="store_true", help="Fetch but do not write.")
    args = parser.parse_args()

    _load_env()
    api_key = _get_api_key()

    readings = []
    for dev in DEVICES:
        label = dev["label"]
        try:
            reading = fetch_reading(dev["sku"], dev["device"], api_key)
            reading["device"] = label
            readings.append(reading)
            print(f"Reading [{label}]: {json.dumps(reading)}")
        except Exception as exc:
            print(f"ERROR fetching {label}: {exc}", file=sys.stderr)

    if not readings:
        print("ERROR: No readings collected.", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print("(dry-run: not written to disk)")
        return

    for reading in readings:
        append_reading(reading)


if __name__ == "__main__":
    main()

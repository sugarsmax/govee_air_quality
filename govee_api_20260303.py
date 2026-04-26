"""
Govee Developer API client — air quality meter exploration.

Usage:
    python govee_api_20260303.py --list                     # List all devices
    python govee_api_20260303.py --state <MAC> <MODEL>      # Query device state
    python govee_api_20260303.py --list --dry-run           # Show request without sending

Requires:
    GOVEE_API_KEY set in a .env file (copy .env.example) or as an environment variable.
    pip install requests python-dotenv
"""

import argparse
import json
import os
import sys
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://developer-api.govee.com"
DEVICE_LIST_ENDPOINT = "/v1/devices"
APPLIANCE_LIST_ENDPOINT = "/v1/appliance/devices"
DEVICE_STATE_ENDPOINT = "/v1/devices/state"


def _get_api_key() -> str:
    key = os.environ.get("GOVEE_API_KEY", "")
    if not key:
        print("ERROR: GOVEE_API_KEY is not set. Copy .env.example to .env and add your key.")
        sys.exit(1)
    return key


def _headers() -> dict:
    return {
        "Govee-API-Key": _get_api_key(),
        "Content-Type": "application/json",
    }


def _print_response(response: requests.Response) -> None:
    print(f"Status: {response.status_code}")
    rate_headers = [
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "API-RateLimit-Limit",
        "API-RateLimit-Remaining",
        "API-RateLimit-Reset",
    ]
    for h in rate_headers:
        if h in response.headers:
            print(f"  {h}: {response.headers[h]}")
    try:
        print(json.dumps(response.json(), indent=2))
    except ValueError:
        print(response.text)


def list_devices(dry_run: bool = False) -> None:
    """Fetch all devices from both the lights/plugs and appliances endpoints."""
    endpoints = [
        ("Lights / Plugs / Switches", BASE_URL + DEVICE_LIST_ENDPOINT),
        ("Appliances", BASE_URL + APPLIANCE_LIST_ENDPOINT),
    ]
    for label, url in endpoints:
        print(f"\n--- {label} ---")
        print(f"GET {url}")
        if dry_run:
            print("(dry-run: request not sent)")
            continue
        try:
            response = requests.get(url, headers=_headers(), timeout=10)
            _print_response(response)
        except requests.RequestException as exc:
            print(f"Request failed: {exc}")


def get_device_state(mac: str, model: str, dry_run: bool = False) -> None:
    """Query the current state of a specific device."""
    params = urlencode({"device": mac, "model": model})
    url = f"{BASE_URL}{DEVICE_STATE_ENDPOINT}?{params}"
    print(f"\n--- Device State ---")
    print(f"GET {url}")
    if dry_run:
        print("(dry-run: request not sent)")
        return
    try:
        response = requests.get(url, headers=_headers(), timeout=10)
        _print_response(response)
    except requests.RequestException as exc:
        print(f"Request failed: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Govee Developer API client — explore air quality meter data."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all devices bound to the account.",
    )
    parser.add_argument(
        "--state",
        nargs=2,
        metavar=("MAC", "MODEL"),
        help="Query state for a device. Example: --state '99:E5:A4:C1:38:29:DA:7B' H5106",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the request details without making any HTTP calls.",
    )

    args = parser.parse_args()

    if not args.list and not args.state:
        parser.print_help()
        sys.exit(0)

    if args.list:
        list_devices(dry_run=args.dry_run)

    if args.state:
        mac, model = args.state
        get_device_state(mac, model, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

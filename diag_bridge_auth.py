#!/usr/bin/env python3
"""
Bridge Sandbox Auth Diagnostic
- Loads .env
- Prints masked key info
- Attempts POST /v0/customers and prints status, headers, and response body
"""

import os
import uuid
import json
import sys
import requests

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

def mask(s: str, show: int = 6) -> str:
    if not s:
        return "<empty>"
    return s[:show] + "…" + s[-2:]

def main():
    # Load .env
    if load_dotenv:
        load_dotenv()
    
    api_key = os.getenv("BRIDGE_API_KEY")
    base_url = os.getenv("BRIDGE_API_URL", "https://api.bridge.xyz/v0")

    print("Bridge Auth Diagnostic")
    print("-"*60)
    print(f"BRIDGE_API_URL: {base_url}")
    print(f"BRIDGE_API_KEY: {mask(api_key)} (len={len(api_key) if api_key else 0})")

    if not api_key:
        print("ERROR: BRIDGE_API_KEY not set. Add it to .env and retry.")
        sys.exit(1)

    headers = {
        "Api-Key": api_key,
        "Content-Type": "application/json",
        "Idempotency-Key": str(uuid.uuid4()),
    }

    # Minimal valid-ish customer payload per docs (may vary by tenant)
    payload = {
        "type": "individual",
        "first_name": "Walta",
        "last_name": "Agent",
        "email": f"walta+{uuid.uuid4().hex[:8]}@example.com"
    }

    url = f"{base_url}/customers"
    print(f"\nPOST {url}")
    print(f"Headers: {{'Api-Key': '{mask(api_key)}', 'Content-Type': 'application/json', 'Idempotency-Key': '<uuid>'}}")
    print(f"Body: {json.dumps(payload)}")

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        print(f"\nStatus: {resp.status_code}")
        print("Response headers:")
        for k, v in resp.headers.items():
            print(f"  {k}: {v}")
        print("\nResponse body:")
        print(resp.text)
        resp.raise_for_status()
        data = resp.json()
        print("\nSUCCESS: Customer created:", data.get("id"))
        sys.exit(0)
    except requests.HTTPError as e:
        print(f"\nHTTPError: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate Google Ads credentials before running reports."""
import os
import sys


REQUIRED = [
    "GOOGLE_ADS_DEVELOPER_TOKEN",
    "GOOGLE_ADS_CLIENT_ID",
    "GOOGLE_ADS_CLIENT_SECRET",
    "GOOGLE_ADS_REFRESH_TOKEN",
    "GOOGLE_ADS_CUSTOMER_ID",
]


def main():
    missing = []
    for key in REQUIRED:
        val = (os.environ.get(key) or "").strip()
        if not val:
            missing.append(key)
        else:
            os.environ[key] = val

    if missing:
        print("ERROR: Missing secrets:", ", ".join(missing), file=sys.stderr)
        sys.exit(1)

    client_id = os.environ["GOOGLE_ADS_CLIENT_ID"]
    if not client_id.endswith(".apps.googleusercontent.com"):
        print("ERROR: GOOGLE_ADS_CLIENT_ID format looks wrong.", file=sys.stderr)
        sys.exit(1)

    if not os.environ["GOOGLE_ADS_CLIENT_SECRET"].startswith("GOCSPX-"):
        print("ERROR: GOOGLE_ADS_CLIENT_SECRET should start with GOCSPX-", file=sys.stderr)
        sys.exit(1)

    if not os.environ["GOOGLE_ADS_REFRESH_TOKEN"].startswith("1//"):
        print("ERROR: GOOGLE_ADS_REFRESH_TOKEN format looks wrong.", file=sys.stderr)
        sys.exit(1)

    try:
        from google.ads.googleads.client import GoogleAdsClient

        GoogleAdsClient.load_from_dict({
            "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
            "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
            "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
            "use_proto_plus": True,
        })
        print("OK: OAuth credentials accepted.")
    except Exception as exc:
        msg = str(exc)
        print(f"ERROR: Credential check failed: {msg}", file=sys.stderr)
        if "invalid_client" in msg:
            print(
                "HINT: Re-save GOOGLE_ADS_CLIENT_ID and GOOGLE_ADS_CLIENT_SECRET "
                "(no spaces). Use the icd8t5h5... client, not the old nsk1rhr... one.",
                file=sys.stderr,
            )
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate Google Ads credentials with a real API call."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from google_ads_config import REQUIRED_ENV, test_api_access  # noqa: E402


def main():
    missing = [k for k in REQUIRED_ENV if not (os.environ.get(k) or "").strip()]
    if missing:
        print("ERROR: Missing secrets:", ", ".join(missing), file=sys.stderr)
        sys.exit(1)

    client_id = os.environ["GOOGLE_ADS_CLIENT_ID"].strip()
    if not client_id.endswith(".apps.googleusercontent.com"):
        print("ERROR: GOOGLE_ADS_CLIENT_ID format looks wrong.", file=sys.stderr)
        sys.exit(1)

    if not os.environ["GOOGLE_ADS_CLIENT_SECRET"].strip().startswith("GOCSPX-"):
        print("ERROR: GOOGLE_ADS_CLIENT_SECRET should start with GOCSPX-", file=sys.stderr)
        sys.exit(1)

    if not os.environ["GOOGLE_ADS_REFRESH_TOKEN"].strip().startswith("1//"):
        print("ERROR: GOOGLE_ADS_REFRESH_TOKEN format looks wrong.", file=sys.stderr)
        sys.exit(1)

    try:
        name = test_api_access()
        print(f"OK: API access verified for account '{name}'.")
    except Exception as exc:
        msg = str(exc)
        print(f"ERROR: API check failed: {msg}", file=sys.stderr)
        if "invalid_client" in msg:
            print(
                "HINT: GOOGLE_ADS_CLIENT_ID / CLIENT_SECRET 불일치. "
                "icd8t5h5... 클라이언트 + GOCSPX-... 시크릿 다시 저장.",
                file=sys.stderr,
            )
        elif "invalid_grant" in msg:
            print(
                "HINT: GOOGLE_ADS_REFRESH_TOKEN 만료/무효. oauth_setup.py 로 재발급.",
                file=sys.stderr,
            )
        sys.exit(1)


if __name__ == "__main__":
    main()

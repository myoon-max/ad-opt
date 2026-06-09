#!/usr/bin/env python3
"""Generate Google Ads OAuth refresh token."""
import json
import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/adwords"]
STATE_FILE = Path(os.environ.get("OAUTH_STATE_FILE", "/workspace/.oauth_state.json"))


def client_config():
    return {
        "installed": {
            "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [
                "urn:ietf:wg:oauth:2.0:oob",
                "http://localhost",
            ],
        }
    }


def new_flow(redirect_uri: str) -> InstalledAppFlow:
    flow = InstalledAppFlow.from_client_config(client_config(), scopes=SCOPES)
    flow.redirect_uri = redirect_uri
    return flow


def save_state(flow: InstalledAppFlow, redirect_uri: str, state: str) -> None:
    payload = {
        "redirect_uri": redirect_uri,
        "state": state,
        "code_verifier": getattr(flow.oauth2session, "code_verifier", None),
    }
    STATE_FILE.write_text(json.dumps(payload))


def load_state() -> dict:
    if not STATE_FILE.exists():
        raise SystemExit(
            "OAuth state not found. Run without OAUTH_CODE first to generate AUTH_URL."
        )
    return json.loads(STATE_FILE.read_text())


def exchange_code(code: str) -> str:
    saved = load_state()
    flow = new_flow(saved["redirect_uri"])
    if saved.get("code_verifier"):
        flow.oauth2session.code_verifier = saved["code_verifier"]
    flow.fetch_token(code=code)
    STATE_FILE.unlink(missing_ok=True)
    return flow.credentials.refresh_token


def main():
    code = os.environ.get("OAUTH_CODE", "").strip()
    if code:
        token = exchange_code(code)
        print("REFRESH_TOKEN:")
        print(token)
        return

    redirect_uri = os.environ.get(
        "OAUTH_REDIRECT_URI", "urn:ietf:wg:oauth:2.0:oob"
    )
    flow = new_flow(redirect_uri)
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    save_state(flow, redirect_uri, state)
    print("1) 아래 URL 접속 → Google Ads 권한 승인")
    print("2) 표시된 인증 코드를 복사")
    print("3) OAUTH_CODE=<코드> python3 scripts/oauth_setup.py 실행")
    print()
    print("AUTH_URL:")
    print(auth_url)


if __name__ == "__main__":
    main()

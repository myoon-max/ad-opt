#!/usr/bin/env python3
"""Generate Google Ads OAuth refresh token."""
import os
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/adwords"]
REDIRECT_PORT = int(os.environ.get("OAUTH_REDIRECT_PORT", "8080"))


def client_config():
    return {
        "installed": {
            "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [
                f"http://localhost:{REDIRECT_PORT}/",
                "http://localhost",
                "urn:ietf:wg:oauth:2.0:oob",
            ],
        }
    }


def exchange_code(code: str) -> str:
    flow = InstalledAppFlow.from_client_config(client_config(), scopes=SCOPES)
    flow.redirect_uri = f"http://localhost:{REDIRECT_PORT}/"
    flow.fetch_token(code=code)
    return flow.credentials.refresh_token


def main():
    code = os.environ.get("OAUTH_CODE", "").strip()
    if code:
        token = exchange_code(code)
        print("REFRESH_TOKEN:")
        print(token)
        return

    flow = InstalledAppFlow.from_client_config(client_config(), scopes=SCOPES)
    flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    print("1) 아래 URL 접속 → Google Ads 권한 승인")
    print("2) 표시된 인증 코드를 복사")
    print("3) OAUTH_CODE=<코드> python3 scripts/oauth_setup.py 실행")
    print()
    print("AUTH_URL:")
    print(auth_url)


if __name__ == "__main__":
    main()

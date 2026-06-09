#!/usr/bin/env python3
"""Generate Google Ads OAuth refresh token."""
import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/adwords"]

client_config = {
    "installed": {
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"],
    }
}

flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
auth_url, _ = flow.authorization_url(
    access_type="offline",
    include_granted_scopes="true",
    prompt="consent",
)
print("AUTH_URL:")
print(auth_url)
print()
code = os.environ.get("OAUTH_CODE", "").strip()
if code:
    flow.fetch_token(code=code)
    print("REFRESH_TOKEN:")
    print(flow.credentials.refresh_token)

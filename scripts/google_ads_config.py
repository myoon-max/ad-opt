"""Shared Google Ads client config with env sanitization."""
import os

from google.ads.googleads.client import GoogleAdsClient

REQUIRED_ENV = [
    "GOOGLE_ADS_DEVELOPER_TOKEN",
    "GOOGLE_ADS_CLIENT_ID",
    "GOOGLE_ADS_CLIENT_SECRET",
    "GOOGLE_ADS_REFRESH_TOKEN",
    "GOOGLE_ADS_CUSTOMER_ID",
]


def sanitize_env():
    for key in REQUIRED_ENV:
        if key in os.environ:
            os.environ[key] = os.environ[key].strip()


def customer_id():
    sanitize_env()
    return os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "4937153045").replace("-", "")


def make_client():
    sanitize_env()
    return GoogleAdsClient.load_from_dict({
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    })


def test_api_access():
    """Force OAuth refresh + one API query."""
    cid = customer_id()
    ga = make_client().get_service("GoogleAdsService")
    rows = list(ga.search(
        customer_id=cid,
        query="SELECT customer.id, customer.descriptive_name FROM customer LIMIT 1",
    ))
    return rows[0].customer.descriptive_name if rows else "unknown"

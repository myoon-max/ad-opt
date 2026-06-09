#!/usr/bin/env python3
"""Quick Google Ads API connectivity check."""
import os
import sys

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


def client(login_customer_id=None):
    config = {
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    }
    if login_customer_id:
        config["login_customer_id"] = login_customer_id.replace("-", "")
    return GoogleAdsClient.load_from_dict(config)


def probe(customer_id, login_customer_id=None):
    cid = customer_id.replace("-", "")
    c = client(login_customer_id)
    ga = c.get_service("CustomerService")
    try:
        accessible = c.get_service("CustomerService").list_accessible_customers()
        names = list(accessible.resource_names)
    except GoogleAdsException as ex:
        names = [ex.failure.errors[0].message]

    try:
        ga_service = c.get_service("GoogleAdsService")
        query = "SELECT customer.id, customer.descriptive_name, customer.manager FROM customer LIMIT 1"
        rows = list(ga_service.search(customer_id=cid, query=query))
        if rows:
            cust = rows[0].customer
            return {
                "status": "ok",
                "accessible": names,
                "name": cust.descriptive_name,
                "manager": cust.manager,
            }
        return {"status": "ok", "accessible": names, "rows": 0}
    except GoogleAdsException as ex:
        return {
            "status": "error",
            "accessible": names,
            "error": ex.failure.errors[0].message,
            "code": ex.failure.errors[0].error_code.__class__.__name__,
        }


if __name__ == "__main__":
    customer_id = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "4937153045")
    login_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    print("=== Direct access (no MCC header) ===")
    print(probe(customer_id, None))
    if login_id:
        print("=== Via MCC header ===")
        print(probe(customer_id, login_id))

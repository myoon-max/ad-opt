#!/usr/bin/env python3
"""Fix sign-up / purchase conversion settings (mutable fields only)."""
import json
import os
import sys

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.protobuf import field_mask_pb2

CUSTOMER_ID = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "4937153045").replace("-", "")
CAMPAIGN_ID = 23843241063
SIGNUP_ID = 7418047105
SIGNUP_VALUE = 1770.0


def client():
    return GoogleAdsClient.load_from_dict({
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    })


def fix_signup_value(c):
    svc = c.get_service("ConversionActionService")
    op = c.get_type("ConversionActionOperation")
    ca = op.update
    ca.resource_name = svc.conversion_action_path(CUSTOMER_ID, SIGNUP_ID)
    ca.value_settings.default_value = SIGNUP_VALUE
    ca.value_settings.always_use_default_value = True
    op.update_mask = field_mask_pb2.FieldMask(paths=[
        "value_settings.default_value",
        "value_settings.always_use_default_value",
    ])
    return svc.mutate_conversion_actions(customer_id=CUSTOMER_ID, operations=[op])


def fix_customer_goals(c):
    svc = c.get_service("CustomerConversionGoalService")
    ops = []
    for category, origin, biddable in [
        ("SIGNUP", "WEBSITE", True),
        ("PURCHASE", "WEBSITE", False),
        ("PAGE_VIEW", "WEBSITE", False),
    ]:
        op = c.get_type("CustomerConversionGoalOperation")
        g = op.update
        g.resource_name = f"customers/{CUSTOMER_ID}/customerConversionGoals/{category}~{origin}"
        g.biddable = biddable
        op.update_mask = field_mask_pb2.FieldMask(paths=["biddable"])
        ops.append(op)
    return svc.mutate_customer_conversion_goals(customer_id=CUSTOMER_ID, operations=ops)


def fix_campaign_goals(c):
    svc = c.get_service("CampaignConversionGoalService")
    ops = []
    for category, origin, biddable in [
        ("SIGNUP", "WEBSITE", True),
        ("PURCHASE", "WEBSITE", False),
        ("PAGE_VIEW", "WEBSITE", False),
    ]:
        op = c.get_type("CampaignConversionGoalOperation")
        g = op.update
        g.resource_name = (
            f"customers/{CUSTOMER_ID}/campaignConversionGoals/"
            f"{CAMPAIGN_ID}~{category}~{origin}"
        )
        g.biddable = biddable
        op.update_mask = field_mask_pb2.FieldMask(paths=["biddable"])
        ops.append(op)
    return svc.mutate_campaign_conversion_goals(customer_id=CUSTOMER_ID, operations=ops)


def main():
    c = client()
    try:
        r1 = fix_signup_value(c)
        r2 = fix_customer_goals(c)
        r3 = fix_campaign_goals(c)
        print(json.dumps({
            "status": "ok",
            "signup_value": r1.results[0].resource_name,
            "customer_goals": [x.resource_name for x in r2.results],
            "campaign_goals": [x.resource_name for x in r3.results],
            "note": (
                "include_in_conversions_metric is UI-only (API immutable). "
                "Bidding uses campaign_conversion_goal SIGNUP biddable=true."
            ),
        }, indent=2, ensure_ascii=False))
    except GoogleAdsException as ex:
        print(json.dumps({
            "status": "error",
            "message": ex.failure.errors[0].message,
        }, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

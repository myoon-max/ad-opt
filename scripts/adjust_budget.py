#!/usr/bin/env python3
"""Adjust PMax daily budget within promo cap."""
import os
from google.ads.googleads.client import GoogleAdsClient
from google.protobuf import field_mask_pb2

CUSTOMER_ID = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "4937153045").replace("-", "")
BUDGET_ID = 15577823193
PROMO_TOTAL_KRW = 100_000
DAILY_BUDGET_KRW = int(os.environ.get("DAILY_BUDGET_KRW", "6000"))


def main():
    c = GoogleAdsClient.load_from_dict({
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    })
    ga = c.get_service("GoogleAdsService")
    spent = 0
    for row in ga.search(customer_id=CUSTOMER_ID, query="""
        SELECT metrics.cost_micros FROM campaign WHERE campaign.id = 23843241063
    """):
        spent = row.metrics.cost_micros / 1_000_000

    remaining = PROMO_TOTAL_KRW - spent
    print(f"spent={spent:.0f} remaining={remaining:.0f} daily_set={DAILY_BUDGET_KRW}")

    bs = c.get_service("CampaignBudgetService")
    op = c.get_type("CampaignBudgetOperation")
    b = op.update
    b.resource_name = f"customers/{CUSTOMER_ID}/campaignBudgets/{BUDGET_ID}"
    # CUSTOM period budget: only total_amount_micros (daily unset).
    # Google auto-paces spend toward end_date_time.
    b.total_amount_micros = PROMO_TOTAL_KRW * 1_000_000
    op.update_mask = field_mask_pb2.FieldMask(paths=["total_amount_micros"])
    resp = bs.mutate_campaign_budgets(customer_id=CUSTOMER_ID, operations=[op])
    print("updated", resp.results[0].resource_name)


if __name__ == "__main__":
    main()

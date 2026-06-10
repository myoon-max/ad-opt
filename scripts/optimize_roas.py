#!/usr/bin/env python3
"""Apply ROAS-focused optimizations to Google Ads account."""
import json
import os
import sys

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.protobuf import field_mask_pb2


def get_client():
    config = {
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    }
    return GoogleAdsClient.load_from_dict(config)


def get_enabled_pmax_campaign(client, customer_id):
    ga = client.get_service("GoogleAdsService")
    cid = customer_id.replace("-", "")
    query = """
        SELECT
          campaign.id,
          campaign.name,
          campaign.resource_name,
          campaign.bidding_strategy_type,
          campaign.geo_target_type_setting.positive_geo_target_type,
          campaign.maximize_conversion_value.target_roas,
          campaign_budget.id,
          campaign_budget.resource_name,
          campaign_budget.amount_micros
        FROM campaign
        WHERE campaign.status = 'ENABLED'
          AND campaign.advertising_channel_type = 'PERFORMANCE_MAX'
    """
    rows = list(ga.search(customer_id=cid, query=query))
    return rows[0] if rows else None


def apply_optimizations(customer_id, dry_run=False):
    client = get_client()
    cid = customer_id.replace("-", "")
    row = get_enabled_pmax_campaign(client, cid)
    if not row:
        return {"error": "No enabled Performance Max campaign found"}

    campaign = row.campaign
    budget = row.campaign_budget
    campaign_id = campaign.id
    budget_id = budget.id

    changes = []
    operations = []

    # 1) Target ROAS via Maximize Conversion Value
    target_roas = float(os.environ.get("TARGET_ROAS", "1.2"))
    current_target = row.campaign.maximize_conversion_value.target_roas
    if campaign.bidding_strategy_type.name != "MAXIMIZE_CONVERSION_VALUE" or (
        current_target and abs(current_target - target_roas) > 0.01
    ):
        camp_op = client.get_type("CampaignOperation")
        camp = camp_op.update
        camp.resource_name = campaign.resource_name
        camp.maximize_conversion_value = client.get_type("MaximizeConversionValue")
        camp.maximize_conversion_value.target_roas = target_roas
        camp_op.update_mask.paths.append("maximize_conversion_value.target_roas")
        operations.append(("campaign_bidding", camp_op))
        changes.append(
            f"입찰 → tROAS {target_roas:.0%} (전환가치/ROAS 극대화)"
        )

    # 2) Geo: Presence only (reduce wasted interest-based traffic)
    if campaign.geo_target_type_setting.positive_geo_target_type.name != "PRESENCE":
        camp_op = client.get_type("CampaignOperation")
        camp = camp_op.update
        camp.resource_name = campaign.resource_name
        camp.geo_target_type_setting.positive_geo_target_type = (
            client.enums.PositiveGeoTargetTypeEnum.PRESENCE
        )
        camp_op.update_mask.paths.append("geo_target_type_setting.positive_geo_target_type")
        operations.append(("campaign_geo", camp_op))
        changes.append("지역 타겟: 관심도+위치 → 위치만 (한국 실거주/접속자)")

    # 3) Daily budget — only if campaign uses daily budget (amount_micros > 0)
    target_budget_micros = int(float(os.environ.get("TARGET_DAILY_BUDGET_KRW", "30000")) * 1_000_000)
    current_budget = budget.amount_micros or 0
    if current_budget > 0 and current_budget < target_budget_micros:
        budget_op = client.get_type("CampaignBudgetOperation")
        b = budget_op.update
        b.resource_name = budget.resource_name
        b.amount_micros = target_budget_micros
        budget_op.update_mask.paths.append("amount_micros")
        operations.append(("budget", budget_op))
        changes.append(
            f"일예산 {current_budget/1e6:,.0f}원 → {target_budget_micros/1e6:,.0f}원"
        )

    result = {
        "campaign": campaign.name,
        "campaign_id": campaign_id,
        "planned_changes": changes,
        "dry_run": dry_run,
        "applied": [],
    }

    if dry_run or not operations:
        return result

    campaign_service = client.get_service("CampaignService")
    budget_service = client.get_service("CampaignBudgetService")

    for kind, op in operations:
        try:
            if kind == "budget":
                resp = budget_service.mutate_campaign_budgets(
                    customer_id=cid, operations=[op]
                )
                result["applied"].append(
                    {"type": kind, "resource": resp.results[0].resource_name}
                )
            else:
                resp = campaign_service.mutate_campaigns(
                    customer_id=cid, operations=[op]
                )
                result["applied"].append(
                    {"type": kind, "resource": resp.results[0].resource_name}
                )
        except GoogleAdsException as ex:
            err = ex.failure.errors[0]
            result.setdefault("errors", []).append(
                {"type": kind, "message": err.message, "code": str(err.error_code)}
            )

    return result


if __name__ == "__main__":
    dry = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")
    cid = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "4937153045")
    print(json.dumps(apply_optimizations(cid, dry_run=dry), indent=2, ensure_ascii=False))

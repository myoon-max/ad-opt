#!/usr/bin/env python3
"""Google Ads account audit script for ROAS optimization."""
import json
import os
import sys
from datetime import datetime, timedelta

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


def get_client():
    config = {
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ.get("GOOGLE_ADS_REFRESH_TOKEN", ""),
        "use_proto_plus": True,
    }
    login = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "").strip()
    if login:
        config["login_customer_id"] = login
    return GoogleAdsClient.load_from_dict(config)


def run_query(client, customer_id, query):
    ga_service = client.get_service("GoogleAdsService")
    cid = customer_id.replace("-", "")
    rows = []
    try:
        stream = ga_service.search_stream(customer_id=cid, query=query)
        for batch in stream:
            for row in batch.results:
                rows.append(row)
    except GoogleAdsException as ex:
        print(f"API Error: {ex.failure.errors[0].message}", file=sys.stderr)
        for err in ex.failure.errors:
            print(f"  {err.error_code}: {err.message}", file=sys.stderr)
        raise
    return rows


def audit_account(customer_id):
    client = get_client()
    cid = customer_id.replace("-", "")

    results = {"customer_id": customer_id, "audited_at": datetime.utcnow().isoformat()}

    # Account info
    q = """
        SELECT
          customer.id,
          customer.descriptive_name,
          customer.currency_code,
          customer.time_zone,
          customer.auto_tagging_enabled,
          customer.tracking_url_template,
          customer.final_url_suffix
        FROM customer
        LIMIT 1
    """
    rows = run_query(client, cid, q)
    if rows:
        c = rows[0].customer
        results["account"] = {
            "id": c.id,
            "name": c.descriptive_name,
            "currency": c.currency_code,
            "timezone": c.time_zone,
            "auto_tagging": c.auto_tagging_enabled,
        }

    # Conversion actions
    q = """
        SELECT
          conversion_action.id,
          conversion_action.name,
          conversion_action.status,
          conversion_action.type,
          conversion_action.category,
          conversion_action.primary_for_goal,
          conversion_action.include_in_conversions_metric,
          conversion_action.value_settings.default_value,
          conversion_action.value_settings.default_currency_code,
          conversion_action.counting_type
        FROM conversion_action
        WHERE conversion_action.status != 'REMOVED'
    """
    rows = run_query(client, cid, q)
    results["conversion_actions"] = []
    for row in rows:
        ca = row.conversion_action
        results["conversion_actions"].append({
            "id": ca.id,
            "name": ca.name,
            "status": ca.status.name,
            "type": ca.type_.name,
            "category": ca.category.name,
            "primary_for_goal": ca.primary_for_goal,
            "include_in_conversions": ca.include_in_conversions_metric,
            "default_value": ca.value_settings.default_value,
            "counting_type": ca.counting_type.name,
        })

    # Campaigns last 30 days performance
    q = """
        SELECT
          campaign.id,
          campaign.name,
          campaign.status,
          campaign.advertising_channel_type,
          campaign.bidding_strategy_type,
          campaign_budget.amount_micros,
          campaign.target_roas.target_roas,
          campaign.maximize_conversion_value.target_roas,
          metrics.impressions,
          metrics.clicks,
          metrics.cost_micros,
          metrics.conversions,
          metrics.conversions_value,
          metrics.all_conversions,
          metrics.all_conversions_value
        FROM campaign
        WHERE segments.date DURING LAST_30_DAYS
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
    """
    rows = run_query(client, cid, q)
    results["campaigns_30d"] = []
    total_cost = 0
    total_conv_value = 0
    total_conversions = 0
    for row in rows:
        m = row.metrics
        cost = m.cost_micros / 1_000_000
        conv_val = m.conversions_value
        total_cost += cost
        total_conv_value += conv_val
        total_conversions += m.conversions
        roas = (conv_val / cost) if cost > 0 else 0
        c = row.campaign
        target_roas = None
        if c.target_roas.target_roas:
            target_roas = c.target_roas.target_roas
        elif c.maximize_conversion_value.target_roas:
            target_roas = c.maximize_conversion_value.target_roas

        results["campaigns_30d"].append({
            "id": c.id,
            "name": c.name,
            "status": c.status.name,
            "channel": c.advertising_channel_type.name,
            "bidding": c.bidding_strategy_type.name,
            "budget_daily": row.campaign_budget.amount_micros / 1_000_000,
            "target_roas": target_roas,
            "impressions": m.impressions,
            "clicks": m.clicks,
            "cost": round(cost, 2),
            "conversions": round(m.conversions, 2),
            "conv_value": round(conv_val, 2),
            "roas": round(roas, 2),
        })

    results["summary_30d"] = {
        "total_cost": round(total_cost, 2),
        "total_conversions": round(total_conversions, 2),
        "total_conv_value": round(total_conv_value, 2),
        "overall_roas": round(total_conv_value / total_cost, 2) if total_cost > 0 else 0,
    }

    # Active campaigns settings (no date segment)
    q = """
        SELECT
          campaign.id,
          campaign.name,
          campaign.status,
          campaign.advertising_channel_type,
          campaign.bidding_strategy_type,
          campaign.network_settings.target_google_search,
          campaign.network_settings.target_search_network,
          campaign.network_settings.target_content_network,
          campaign.geo_target_type_setting.positive_geo_target_type,
          campaign_budget.amount_micros
        FROM campaign
        WHERE campaign.status = 'ENABLED'
    """
    rows = run_query(client, cid, q)
    results["active_campaigns"] = []
    for row in rows:
        c = row.campaign
        ns = c.network_settings
        results["active_campaigns"].append({
            "id": c.id,
            "name": c.name,
            "channel": c.advertising_channel_type.name,
            "bidding": c.bidding_strategy_type.name,
            "budget_daily": row.campaign_budget.amount_micros / 1_000_000,
            "search": ns.target_google_search,
            "search_partners": ns.target_search_network,
            "display": ns.target_content_network,
            "geo_target_type": c.geo_target_type_setting.positive_geo_target_type.name,
        })

    return results


if __name__ == "__main__":
    customer_id = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "4937153045")
    try:
        data = audit_account(customer_id)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e), "type": type(e).__name__}), file=sys.stderr)
        sys.exit(1)

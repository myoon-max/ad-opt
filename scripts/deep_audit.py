#!/usr/bin/env python3
"""Deep Google Ads audit for ROAS optimization."""
import json
import os
import sys

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


def get_client():
    config = {
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    }
    login = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "")
    if login and os.environ.get("USE_MCC_HEADER", "").lower() in ("1", "true", "yes"):
        config["login_customer_id"] = login
    return GoogleAdsClient.load_from_dict(config)


def run_query(client, customer_id, query):
    ga = client.get_service("GoogleAdsService")
    cid = customer_id.replace("-", "")
    rows = []
    stream = ga.search_stream(customer_id=cid, query=query)
    for batch in stream:
        for row in batch.results:
            rows.append(row)
    return rows


def deep_audit(customer_id):
    client = get_client()
    cid = customer_id.replace("-", "")
    out = {}

    queries = {
        "search_terms": """
            SELECT
              search_term_view.search_term,
              campaign.name,
              ad_group.name,
              metrics.impressions,
              metrics.clicks,
              metrics.cost_micros,
              metrics.conversions,
              metrics.conversions_value
            FROM search_term_view
            WHERE segments.date DURING LAST_30_DAYS
              AND metrics.impressions > 0
            ORDER BY metrics.cost_micros DESC
            LIMIT 100
        """,
        "keywords": """
            SELECT
              ad_group_criterion.keyword.text,
              ad_group_criterion.keyword.match_type,
              ad_group_criterion.status,
              campaign.name,
              ad_group.name,
              metrics.impressions,
              metrics.clicks,
              metrics.cost_micros,
              metrics.conversions,
              metrics.conversions_value
            FROM keyword_view
            WHERE segments.date DURING LAST_30_DAYS
              AND ad_group_criterion.status != 'REMOVED'
            ORDER BY metrics.cost_micros DESC
            LIMIT 100
        """,
        "ad_groups": """
            SELECT
              campaign.name,
              ad_group.id,
              ad_group.name,
              ad_group.status,
              metrics.impressions,
              metrics.clicks,
              metrics.cost_micros,
              metrics.conversions,
              metrics.conversions_value
            FROM ad_group
            WHERE segments.date DURING LAST_30_DAYS
              AND ad_group.status != 'REMOVED'
            ORDER BY metrics.cost_micros DESC
            LIMIT 50
        """,
        "ads": """
            SELECT
              campaign.name,
              ad_group.name,
              ad_group_ad.ad.id,
              ad_group_ad.status,
              ad_group_ad.ad.type,
              metrics.impressions,
              metrics.clicks,
              metrics.cost_micros,
              metrics.conversions,
              metrics.conversions_value
            FROM ad_group_ad
            WHERE segments.date DURING LAST_30_DAYS
              AND ad_group_ad.status != 'REMOVED'
            ORDER BY metrics.cost_micros DESC
            LIMIT 50
        """,
        "device": """
            SELECT
              campaign.name,
              segments.device,
              metrics.impressions,
              metrics.clicks,
              metrics.cost_micros,
              metrics.conversions,
              metrics.conversions_value
            FROM campaign
            WHERE segments.date DURING LAST_30_DAYS
        """,
        "geo": """
            SELECT
              campaign.name,
              geographic_view.country_criterion_id,
              metrics.impressions,
              metrics.clicks,
              metrics.cost_micros,
              metrics.conversions,
              metrics.conversions_value
            FROM geographic_view
            WHERE segments.date DURING LAST_30_DAYS
            ORDER BY metrics.cost_micros DESC
            LIMIT 30
        """,
        "budgets": """
            SELECT
              campaign.id,
              campaign.name,
              campaign.status,
              campaign_budget.id,
              campaign_budget.name,
              campaign_budget.amount_micros,
              campaign_budget.explicitly_shared,
              campaign.bidding_strategy_type,
              campaign.target_roas.target_roas,
              campaign.maximize_conversion_value.target_roas
            FROM campaign
            WHERE campaign.status != 'REMOVED'
        """,
    }

    for key, query in queries.items():
        try:
            rows = run_query(client, cid, query)
            out[key] = []
            for row in rows:
                item = {}
                if key == "search_terms":
                    m = row.metrics
                    cost = m.cost_micros / 1e6
                    item = {
                        "term": row.search_term_view.search_term,
                        "campaign": row.campaign.name,
                        "ad_group": row.ad_group.name,
                        "cost": round(cost, 2),
                        "clicks": m.clicks,
                        "conversions": round(m.conversions, 2),
                        "conv_value": round(m.conversions_value, 2),
                        "roas": round(m.conversions_value / cost, 2) if cost else 0,
                    }
                elif key == "keywords":
                    m = row.metrics
                    cost = m.cost_micros / 1e6
                    kw = row.ad_group_criterion.keyword
                    item = {
                        "keyword": kw.text,
                        "match_type": kw.match_type.name,
                        "status": row.ad_group_criterion.status.name,
                        "campaign": row.campaign.name,
                        "cost": round(cost, 2),
                        "conversions": round(m.conversions, 2),
                        "conv_value": round(m.conversions_value, 2),
                        "roas": round(m.conversions_value / cost, 2) if cost else 0,
                    }
                elif key == "ad_groups":
                    m = row.metrics
                    cost = m.cost_micros / 1e6
                    item = {
                        "campaign": row.campaign.name,
                        "id": row.ad_group.id,
                        "name": row.ad_group.name,
                        "status": row.ad_group.status.name,
                        "cost": round(cost, 2),
                        "conversions": round(m.conversions, 2),
                        "conv_value": round(m.conversions_value, 2),
                        "roas": round(m.conversions_value / cost, 2) if cost else 0,
                    }
                elif key == "ads":
                    m = row.metrics
                    cost = m.cost_micros / 1e6
                    item = {
                        "campaign": row.campaign.name,
                        "ad_group": row.ad_group.name,
                        "ad_id": row.ad_group_ad.ad.id,
                        "status": row.ad_group_ad.status.name,
                        "type": row.ad_group_ad.ad.type_.name,
                        "cost": round(cost, 2),
                        "conversions": round(m.conversions, 2),
                        "roas": round(m.conversions_value / cost, 2) if cost else 0,
                    }
                elif key == "device":
                    m = row.metrics
                    cost = m.cost_micros / 1e6
                    item = {
                        "campaign": row.campaign.name,
                        "device": row.segments.device.name,
                        "cost": round(cost, 2),
                        "conversions": round(m.conversions, 2),
                        "conv_value": round(m.conversions_value, 2),
                        "roas": round(m.conversions_value / cost, 2) if cost else 0,
                    }
                elif key == "geo":
                    m = row.metrics
                    cost = m.cost_micros / 1e6
                    item = {
                        "campaign": row.campaign.name,
                        "country_id": row.geographic_view.country_criterion_id,
                        "cost": round(cost, 2),
                        "conversions": round(m.conversions, 2),
                        "roas": round(m.conversions_value / cost, 2) if cost else 0,
                    }
                elif key == "budgets":
                    c = row.campaign
                    b = row.campaign_budget
                    target_roas = None
                    if c.target_roas.target_roas:
                        target_roas = c.target_roas.target_roas
                    elif c.maximize_conversion_value.target_roas:
                        target_roas = c.maximize_conversion_value.target_roas
                    item = {
                        "campaign_id": c.id,
                        "campaign": c.name,
                        "status": c.status.name,
                        "budget_id": b.id,
                        "budget_daily": b.amount_micros / 1e6,
                        "bidding": c.bidding_strategy_type.name,
                        "target_roas": target_roas,
                    }
                out[key].append(item)
        except GoogleAdsException as ex:
            out[key] = {"error": ex.failure.errors[0].message}

    return out


if __name__ == "__main__":
    cid = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "4937153045")
    print(json.dumps(deep_audit(cid), indent=2, ensure_ascii=False))

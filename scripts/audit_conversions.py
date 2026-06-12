#!/usr/bin/env python3
"""Audit sign-up / purchase tracking and device performance."""
import json
import os
import sys

from google.ads.googleads.client import GoogleAdsClient

CUSTOMER_ID = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "4937153045").replace("-", "")
CAMPAIGN_ID = 23843241063
SIGNUP_ID = 7418047105
PURCHASE_ID = 7418248014


def client():
    return GoogleAdsClient.load_from_dict({
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    })


def q(query):
    ga = client().get_service("GoogleAdsService")
    rows = []
    for batch in ga.search_stream(customer_id=CUSTOMER_ID, query=query):
        for row in batch.results:
            rows.append(row)
    return rows


def main():
    out = {}

    out["conversion_actions"] = [{
        "id": r.conversion_action.id,
        "name": r.conversion_action.name,
        "status": r.conversion_action.status.name,
        "type": r.conversion_action.type_.name,
        "category": r.conversion_action.category.name,
        "origin": r.conversion_action.origin.name,
        "primary_for_goal": r.conversion_action.primary_for_goal,
        "include_in_conversions_metric": r.conversion_action.include_in_conversions_metric,
        "counting_type": r.conversion_action.counting_type.name,
        "default_value": r.conversion_action.value_settings.default_value,
        "always_default": r.conversion_action.value_settings.always_use_default_value,
        "tag_snippets": [
            {
                "type": s.type_.name,
                "page_format": s.page_format.name,
                "global_site_tag": s.global_site_tag[:80] + "..." if s.global_site_tag else None,
                "event_snippet": (s.event_snippet or "")[:120] + "..." if s.event_snippet else None,
            }
            for s in r.conversion_action.tag_snippets
        ],
    } for r in q("""
        SELECT conversion_action.id, conversion_action.name, conversion_action.status,
               conversion_action.type, conversion_action.category, conversion_action.origin,
               conversion_action.primary_for_goal,
               conversion_action.include_in_conversions_metric,
               conversion_action.counting_type,
               conversion_action.value_settings.default_value,
               conversion_action.value_settings.always_use_default_value,
               conversion_action.tag_snippets
        FROM conversion_action
        WHERE conversion_action.status != 'REMOVED'
          AND conversion_action.name IN ('Sign-up', 'Purchase')
    """)]

    out["conversion_goals"] = [{
        "category": r.customer_conversion_goal.category.name,
        "origin": r.customer_conversion_goal.origin.name,
        "biddable": r.customer_conversion_goal.biddable,
    } for r in q("""
        SELECT customer_conversion_goal.category, customer_conversion_goal.origin,
               customer_conversion_goal.biddable
        FROM customer_conversion_goal
        WHERE customer_conversion_goal.category IN ('SIGNUP', 'PURCHASE', 'PAGE_VIEW')
    """)]

    out["action_performance_30d"] = [{
        "action": r.segments.conversion_action_name,
        "device": r.segments.device.name,
        "conversions": r.metrics.conversions,
        "all_conversions": r.metrics.all_conversions,
        "conv_value": r.metrics.conversions_value,
        "all_conv_value": r.metrics.all_conversions_value,
    } for r in q(f"""
        SELECT segments.conversion_action_name, segments.device,
               metrics.conversions, metrics.all_conversions,
               metrics.conversions_value, metrics.all_conversions_value
        FROM campaign
        WHERE campaign.id = {CAMPAIGN_ID}
          AND segments.date DURING LAST_30_DAYS
    """)]

    out["action_performance_lifetime"] = [{
        "action": r.segments.conversion_action_name,
        "device": r.segments.device.name,
        "conversions": r.metrics.conversions,
        "all_conversions": r.metrics.all_conversions,
    } for r in q(f"""
        SELECT segments.conversion_action_name, segments.device,
               metrics.conversions, metrics.all_conversions
        FROM campaign
        WHERE campaign.id = {CAMPAIGN_ID}
    """)]

    out["device_cost_30d"] = [{
        "device": r.segments.device.name,
        "cost": round(r.metrics.cost_micros / 1e6, 0),
        "clicks": r.metrics.clicks,
        "conversions": r.metrics.conversions,
        "all_conversions": r.metrics.all_conversions,
    } for r in q(f"""
        SELECT segments.device, metrics.cost_micros, metrics.clicks,
               metrics.conversions, metrics.all_conversions
        FROM campaign
        WHERE campaign.id = {CAMPAIGN_ID}
          AND segments.date DURING LAST_30_DAYS
    """)]

    out["device_bid_modifiers"] = [{
        "device": r.campaign_criterion.device.type_.name,
        "bid_modifier": r.campaign_criterion.bid_modifier,
    } for r in q(f"""
        SELECT campaign_criterion.device.type, campaign_criterion.bid_modifier
        FROM campaign_criterion
        WHERE campaign.id = {CAMPAIGN_ID}
          AND campaign_criterion.type = 'DEVICE'
    """)]

    out["ga4_links"] = [{
        "product": r.product_link.type.name,
        "status": r.product_link.product_link_id if hasattr(r.product_link, "product_link_id") else None,
    } for r in q("""
        SELECT product_link.type, product_link.product_link_id
        FROM product_link
    """)]

    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

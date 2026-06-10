#!/usr/bin/env python3
"""Comprehensive Google Ads account analysis."""
import json
import os
from collections import defaultdict

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


def client():
    return GoogleAdsClient.load_from_dict({
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    })


def q(cid, query):
    ga = client().get_service("GoogleAdsService")
    rows = []
    for batch in ga.search_stream(customer_id=cid, query=query):
        for row in batch.results:
            rows.append(row)
    return rows


def safe(rows, fn):
    return [fn(r) for r in rows]


def main():
    cid = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "4937153045").replace("-", "")
    out = {}

    # All campaigns status
    out["campaigns_all"] = safe(q(cid, """
        SELECT campaign.id, campaign.name, campaign.status,
               campaign.advertising_channel_type, campaign.bidding_strategy_type,
               campaign_budget.amount_micros, campaign_budget.total_amount_micros,
               campaign.maximize_conversion_value.target_roas,
               campaign.geo_target_type_setting.positive_geo_target_type,
               metrics.impressions, metrics.clicks, metrics.cost_micros,
               metrics.conversions, metrics.conversions_value,
               metrics.all_conversions, metrics.all_conversions_value
        FROM campaign
        WHERE segments.date DURING LAST_30_DAYS
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
    """), lambda r: {
        "id": r.campaign.id, "name": r.campaign.name, "status": r.campaign.status.name,
        "channel": r.campaign.advertising_channel_type.name,
        "bidding": r.campaign.bidding_strategy_type.name,
        "target_roas": r.campaign.maximize_conversion_value.target_roas or None,
        "geo": r.campaign.geo_target_type_setting.positive_geo_target_type.name,
        "budget_daily": (r.campaign_budget.amount_micros or 0) / 1e6,
        "budget_total": (getattr(r.campaign_budget, "total_amount_micros", 0) or 0) / 1e6,
        "cost": r.metrics.cost_micros / 1e6,
        "clicks": r.metrics.clicks, "impressions": r.metrics.impressions,
        "conversions": r.metrics.conversions, "conv_value": r.metrics.conversions_value,
        "all_conversions": r.metrics.all_conversions,
        "roas": round(r.metrics.conversions_value / (r.metrics.cost_micros / 1e6), 2) if r.metrics.cost_micros else 0,
    })

    # Conversion actions config
    out["conversion_actions"] = safe(q(cid, """
        SELECT conversion_action.id, conversion_action.name, conversion_action.status,
               conversion_action.type, conversion_action.category,
               conversion_action.primary_for_goal, conversion_action.include_in_conversions_metric,
               conversion_action.value_settings.default_value,
               conversion_action.value_settings.always_use_default_value,
               conversion_action.counting_type, conversion_action.click_through_lookback_window_days,
               conversion_action.view_through_lookback_window_days
        FROM conversion_action
        WHERE conversion_action.status != 'REMOVED'
    """), lambda r: {
        "id": r.conversion_action.id, "name": r.conversion_action.name,
        "status": r.conversion_action.status.name, "type": r.conversion_action.type_.name,
        "category": r.conversion_action.category.name,
        "primary_for_goal": r.conversion_action.primary_for_goal,
        "in_conversions_col": r.conversion_action.include_in_conversions_metric,
        "default_value": r.conversion_action.value_settings.default_value,
        "always_default": r.conversion_action.value_settings.always_use_default_value,
        "counting": r.conversion_action.counting_type.name,
        "click_window_days": r.conversion_action.click_through_lookback_window_days,
    })

    # Per conversion action performance (30d)
    try:
        out["conversion_performance_30d"] = safe(q(cid, """
            SELECT segments.conversion_action_name, segments.conversion_action_category,
                   campaign.name, segments.device,
                   metrics.conversions, metrics.conversions_value,
                   metrics.all_conversions, metrics.all_conversions_value
            FROM campaign
            WHERE segments.date DURING LAST_30_DAYS
              AND campaign.status = 'ENABLED'
        """), lambda r: {
            "action": r.segments.conversion_action_name,
            "category": r.segments.conversion_action_category.name,
            "campaign": r.campaign.name,
            "device": r.segments.device.name,
            "conversions": r.metrics.conversions,
            "conv_value": r.metrics.conversions_value,
            "all_conversions": r.metrics.all_conversions,
        })
    except GoogleAdsException as e:
        out["conversion_performance_30d"] = {"error": e.failure.errors[0].message}

    # Device breakdown
    out["device_30d"] = safe(q(cid, """
        SELECT campaign.name, segments.device,
               metrics.impressions, metrics.clicks, metrics.cost_micros,
               metrics.conversions, metrics.conversions_value, metrics.ctr, metrics.average_cpc
        FROM campaign
        WHERE segments.date DURING LAST_30_DAYS AND campaign.status = 'ENABLED'
    """), lambda r: {
        "campaign": r.campaign.name, "device": r.segments.device.name,
        "cost": round(r.metrics.cost_micros / 1e6, 0),
        "clicks": r.metrics.clicks, "impressions": r.metrics.impressions,
        "conversions": r.metrics.conversions, "conv_value": r.metrics.conversions_value,
        "ctr": round(r.metrics.ctr * 100, 2), "avg_cpc": round(r.metrics.average_cpc / 1e6, 0),
        "roas": round(r.metrics.conversions_value / (r.metrics.cost_micros / 1e6), 2) if r.metrics.cost_micros else 0,
    })

    # Day of week
    out["day_of_week_30d"] = safe(q(cid, """
        SELECT segments.day_of_week, metrics.cost_micros, metrics.conversions,
               metrics.conversions_value, metrics.clicks
        FROM campaign
        WHERE segments.date DURING LAST_30_DAYS AND campaign.status = 'ENABLED'
    """), lambda r: {
        "day": r.segments.day_of_week.name,
        "cost": round(r.metrics.cost_micros / 1e6, 0),
        "conversions": r.metrics.conversions, "conv_value": r.metrics.conversions_value,
        "clicks": r.metrics.clicks,
    })

    # Hour
    out["hour_30d"] = safe(q(cid, """
        SELECT segments.hour, metrics.cost_micros, metrics.conversions, metrics.clicks
        FROM campaign
        WHERE segments.date DURING LAST_30_DAYS AND campaign.status = 'ENABLED'
    """), lambda r: {
        "hour": r.segments.hour,
        "cost": round(r.metrics.cost_micros / 1e6, 0),
        "conversions": r.metrics.conversions, "clicks": r.metrics.clicks,
    })

    # PMax search terms
    try:
        out["pmax_search_terms"] = safe(q(cid, """
            SELECT campaign_search_term_view.search_term,
                   campaign.name, metrics.impressions, metrics.clicks,
                   metrics.cost_micros, metrics.conversions, metrics.conversions_value
            FROM campaign_search_term_view
            WHERE segments.date DURING LAST_30_DAYS
            ORDER BY metrics.cost_micros DESC
            LIMIT 50
        """), lambda r: {
            "term": r.campaign_search_term_view.search_term,
            "campaign": r.campaign.name,
            "cost": round(r.metrics.cost_micros / 1e6, 0),
            "clicks": r.metrics.clicks, "conversions": r.metrics.conversions,
            "conv_value": r.metrics.conversions_value,
        })
    except GoogleAdsException as e:
        out["pmax_search_terms"] = {"error": e.failure.errors[0].message}

    # Asset group + strength
    out["asset_groups"] = safe(q(cid, """
        SELECT campaign.name, asset_group.id, asset_group.name, asset_group.status,
               asset_group.final_urls, asset_group.path1, asset_group.path2,
               asset_group.ad_strength
        FROM asset_group
        WHERE campaign.status = 'ENABLED'
    """), lambda r: {
        "campaign": r.campaign.name, "id": r.asset_group.id,
        "name": r.asset_group.name, "status": r.asset_group.status.name,
        "urls": list(r.asset_group.final_urls),
        "path1": r.asset_group.path1, "path2": r.asset_group.path2,
        "ad_strength": r.asset_group.ad_strength.name,
    })

    # Assets in asset group
    try:
        out["assets"] = safe(q(cid, """
            SELECT asset_group.name, asset.type, asset.text_asset.text,
                   asset.image_asset.full_size.url, asset_group_asset.field_type,
                   asset_group_asset.status, asset_group_asset.performance_label
            FROM asset_group_asset
            WHERE campaign.status = 'ENABLED'
              AND asset_group_asset.status != 'REMOVED'
        """), lambda r: {
            "group": r.asset_group.name,
            "type": r.asset.type_.name,
            "field": r.asset_group_asset.field_type.name,
            "text": r.asset.text_asset.text if r.asset.text_asset.text else None,
            "image": r.asset.image_asset.full_size.url if r.asset.image_asset.full_size.url else None,
            "perf": r.asset_group_asset.performance_label.name,
            "status": r.asset_group_asset.status.name,
        })
    except GoogleAdsException as e:
        out["assets"] = {"error": e.failure.errors[0].message}

    # Audience signals
    try:
        out["audience_signals"] = safe(q(cid, """
            SELECT asset_group.name, asset_group_signal.audience.audience,
                   asset_group_signal.resource_name
            FROM asset_group_signal
            WHERE campaign.status = 'ENABLED'
        """), lambda r: {
            "group": r.asset_group.name,
            "audience": r.asset_group_signal.audience.audience,
        })
    except GoogleAdsException as e:
        out["audience_signals"] = {"error": e.failure.errors[0].message}

    # Landing pages
    try:
        out["landing_pages"] = safe(q(cid, """
            SELECT landing_page_view.unexpanded_final_url,
                   metrics.impressions, metrics.clicks, metrics.cost_micros,
                   metrics.conversions, metrics.conversions_value
            FROM landing_page_view
            WHERE segments.date DURING LAST_30_DAYS
            ORDER BY metrics.cost_micros DESC
            LIMIT 20
        """), lambda r: {
            "url": r.landing_page_view.unexpanded_final_url,
            "cost": round(r.metrics.cost_micros / 1e6, 0),
            "clicks": r.metrics.clicks, "conversions": r.metrics.conversions,
            "conv_value": r.metrics.conversions_value,
        })
    except GoogleAdsException as e:
        out["landing_pages"] = {"error": e.failure.errors[0].message}

    # 90 day trend
    out["campaign_90d"] = safe(q(cid, """
        SELECT segments.month, metrics.cost_micros, metrics.conversions,
               metrics.conversions_value, metrics.clicks, metrics.impressions
        FROM campaign
        WHERE segments.date DURING LAST_90_DAYS AND campaign.status = 'ENABLED'
        ORDER BY segments.month
    """), lambda r: {
        "month": r.segments.month,
        "cost": round(r.metrics.cost_micros / 1e6, 0),
        "conversions": r.metrics.conversions, "conv_value": r.metrics.conversions_value,
        "clicks": r.metrics.clicks,
    })

    # Network (PMax channels)
    try:
        out["ad_network"] = safe(q(cid, """
            SELECT segments.ad_network_type, metrics.cost_micros, metrics.conversions,
                   metrics.conversions_value, metrics.clicks, metrics.impressions
            FROM campaign
            WHERE segments.date DURING LAST_30_DAYS AND campaign.status = 'ENABLED'
        """), lambda r: {
            "network": r.segments.ad_network_type.name,
            "cost": round(r.metrics.cost_micros / 1e6, 0),
            "conversions": r.metrics.conversions,
            "conv_value": r.metrics.conversions_value,
            "clicks": r.metrics.clicks,
        })
    except GoogleAdsException as e:
        out["ad_network"] = {"error": e.failure.errors[0].message}

    # Age range
    try:
        out["age_range"] = safe(q(cid, """
            SELECT ad_group_criterion.age_range.type, metrics.cost_micros,
                   metrics.conversions, metrics.clicks
            FROM age_range_view
            WHERE segments.date DURING LAST_30_DAYS
            ORDER BY metrics.cost_micros DESC
        """), lambda r: {
            "age": r.ad_group_criterion.age_range.type_.name,
            "cost": round(r.metrics.cost_micros / 1e6, 0),
            "conversions": r.metrics.conversions, "clicks": r.metrics.clicks,
        })
    except GoogleAdsException as e:
        out["age_range"] = {"error": e.failure.errors[0].message}

    # Gender
    try:
        out["gender"] = safe(q(cid, """
            SELECT ad_group_criterion.gender.type, metrics.cost_micros,
                   metrics.conversions, metrics.clicks
            FROM gender_view
            WHERE segments.date DURING LAST_30_DAYS
        """), lambda r: {
            "gender": r.ad_group_criterion.gender.type_.name,
            "cost": round(r.metrics.cost_micros / 1e6, 0),
            "conversions": r.metrics.conversions,
        })
    except GoogleAdsException as e:
        out["gender"] = {"error": e.failure.errors[0].message}

    # Sign-up specific - all conversions by action name (using conversion_action segment)
    try:
        out["all_conv_by_action"] = safe(q(cid, """
            SELECT segments.conversion_action, segments.conversion_action_name,
                   segments.device, metrics.all_conversions, metrics.all_conversions_value
            FROM campaign
            WHERE segments.date DURING LAST_30_DAYS
              AND campaign.status = 'ENABLED'
        """), lambda r: {
            "action_id": r.segments.conversion_action,
            "action_name": r.segments.conversion_action_name,
            "device": r.segments.device.name,
            "all_conversions": r.metrics.all_conversions,
            "all_conv_value": r.metrics.all_conversions_value,
        })
    except GoogleAdsException as e:
        out["all_conv_by_action"] = {"error": e.failure.errors[0].message}

    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

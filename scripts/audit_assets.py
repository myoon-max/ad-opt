#!/usr/bin/env python3
"""Audit PMax asset inventory and per-asset performance."""
import json
import os
import sys
from collections import defaultdict

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

CUSTOMER_ID = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "4937153045").replace("-", "")
PMAX_ID = 23843241063


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

    out["asset_groups"] = [{
        "id": r.asset_group.id,
        "name": r.asset_group.name,
        "ad_strength": r.asset_group.ad_strength.name,
        "final_urls": list(r.asset_group.final_urls),
        "status": r.asset_group.status.name,
    } for r in q(f"""
        SELECT asset_group.id, asset_group.name, asset_group.ad_strength,
               asset_group.final_urls, asset_group.status
        FROM asset_group WHERE campaign.id = {PMAX_ID}
    """)]

    # Inventory + Google performance label
    assets = []
    for r in q(f"""
        SELECT asset.id, asset.name, asset.type,
               asset.text_asset.text,
               asset.image_asset.full_size.url,
               asset.youtube_video_asset.youtube_video_id,
               asset.youtube_video_asset.youtube_video_title,
               asset_group_asset.field_type,
               asset_group_asset.status,
               asset_group_asset.performance_label,
               asset_group_asset.policy_summary.approval_status
        FROM asset_group_asset
        WHERE campaign.id = {PMAX_ID}
          AND asset_group_asset.status != 'REMOVED'
    """):
        a = r.asset
        aga = r.asset_group_asset
        entry = {
            "asset_id": a.id,
            "name": a.name,
            "type": a.type_.name,
            "field": aga.field_type.name,
            "status": aga.status.name,
            "performance_label": aga.performance_label.name,
            "approval": aga.policy_summary.approval_status.name,
        }
        if a.text_asset.text:
            entry["text"] = a.text_asset.text
        if a.image_asset.full_size.url:
            entry["image_url"] = a.image_asset.full_size.url
        if a.youtube_video_asset.youtube_video_id:
            entry["youtube_id"] = a.youtube_video_asset.youtube_video_id
            entry["youtube_title"] = a.youtube_video_asset.youtube_video_title
        assets.append(entry)
    out["assets"] = assets

    # Metrics by asset (30d) where available
    metrics = []
    try:
        for r in q(f"""
            SELECT asset.id, asset.name, asset.type,
                   asset_group_asset.field_type,
                   asset_group_asset.performance_label,
                   metrics.impressions, metrics.clicks, metrics.cost_micros,
                   metrics.conversions, metrics.all_conversions
            FROM asset_group_asset
            WHERE campaign.id = {PMAX_ID}
              AND segments.date DURING LAST_30_DAYS
              AND asset_group_asset.status != 'REMOVED'
        """):
            cost = r.metrics.cost_micros / 1e6
            metrics.append({
                "asset_id": r.asset.id,
                "name": r.asset.name,
                "type": r.asset.type_.name,
                "field": r.asset_group_asset.field_type.name,
                "label": r.asset_group_asset.performance_label.name,
                "impressions": r.metrics.impressions,
                "clicks": r.metrics.clicks,
                "cost": round(cost, 0),
                "conversions": r.metrics.conversions,
                "all_conversions": r.metrics.all_conversions,
            })
    except GoogleAdsException as ex:
        metrics = {"error": ex.failure.errors[0].message}
    out["asset_metrics_30d"] = metrics

    # Summary counts by label
    by_label = defaultdict(list)
    for a in assets:
        by_label[a["performance_label"]].append(a)

    out["summary"] = {
        "total_assets": len(assets),
        "by_performance_label": {k: len(v) for k, v in by_label.items()},
        "low_assets": [
            {k: a[k] for k in ("asset_id", "field", "text", "youtube_id", "name")}
            for a in assets if a["performance_label"] == "LOW"
        ],
        "best_assets": [
            {k: a[k] for k in ("asset_id", "field", "text", "youtube_id", "name")}
            for a in assets if a["performance_label"] == "BEST"
        ],
        "headline_count": sum(1 for a in assets if a["field"] == "HEADLINE"),
        "description_count": sum(1 for a in assets if a["field"] == "DESCRIPTION"),
        "image_count": sum(1 for a in assets if "IMAGE" in a["field"]),
        "video_count": sum(1 for a in assets if a["field"] == "YOUTUBE_VIDEO"),
    }

    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

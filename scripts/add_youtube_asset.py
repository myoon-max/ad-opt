#!/usr/bin/env python3
"""Link a YouTube video to PMax asset group."""
import argparse
import os
import sys

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

CUSTOMER_ID = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "4937153045").replace("-", "")
ASSET_GROUP_ID = 6712854804


def client():
    return GoogleAdsClient.load_from_dict({
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-id", required=True, help="YouTube video ID")
    args = parser.parse_args()

    c = client()
    asset_svc = c.get_service("AssetService")
    op = c.get_type("AssetOperation")
    asset = op.create
    asset.name = f"youtube_{args.video_id}"
    asset.youtube_video_asset.youtube_video_id = args.video_id
    resp = asset_svc.mutate_assets(customer_id=CUSTOMER_ID, operations=[op])
    asset_rn = resp.results[0].resource_name

    aga_svc = c.get_service("AssetGroupAssetService")
    aga_op = c.get_type("AssetGroupAssetOperation")
    link = aga_op.create
    link.asset = asset_rn
    link.asset_group = f"customers/{CUSTOMER_ID}/assetGroups/{ASSET_GROUP_ID}"
    link.field_type = c.enums.AssetFieldTypeEnum.YOUTUBE_VIDEO
    aga_resp = aga_svc.mutate_asset_group_assets(customer_id=CUSTOMER_ID, operations=[aga_op])
    print(f"OK: {aga_resp.results[0].resource_name}")


if __name__ == "__main__":
    try:
        main()
    except GoogleAdsException as ex:
        print(ex.failure.errors[0].message, file=sys.stderr)
        sys.exit(1)

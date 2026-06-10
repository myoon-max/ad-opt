#!/usr/bin/env python3
"""Upload new creatives and apply proactive PMax improvements."""
import json
import os
import sys

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.protobuf import field_mask_pb2

CUSTOMER_ID = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "4937153045").replace("-", "")
ASSET_GROUP_ID = 6712854804
BROKEN_SITELINK_ASSET_ID = 317867075534

NEW_HEADLINES = [
    "3분 만에 AI 자소서 첨삭",
    "지금 무료로 합격 진단",
]

NEW_DESCRIPTIONS = [
    "자소서 붙여넣고 3분 첨삭. hapgyuk.com/start 지금 시작.",
]

IMAGE_UPLOADS = [
    ("/workspace/creatives/pmax_portrait_960x1200.png", "PORTRAIT_MARKETING_IMAGE"),
    ("/workspace/creatives/pmax_square_1200x1200.png", "SQUARE_MARKETING_IMAGE"),
]

# Replace oldest auto-added square/portrait if at asset limit
REPLACE_ASSET_GROUP_ASSETS = [
    "customers/4937153045/assetGroupAssets/6712854804~312239202681~SQUARE_MARKETING_IMAGE",
    "customers/4937153045/assetGroupAssets/6712854804~368307957490~PORTRAIT_MARKETING_IMAGE",
    "customers/4937153045/assetGroupAssets/6712854804~368221804781~HEADLINE",
    "customers/4937153045/assetGroupAssets/6712854804~368221804778~HEADLINE",
    "customers/4937153045/assetGroupAssets/6712854804~345980173556~DESCRIPTION",
]


def client():
    return GoogleAdsClient.load_from_dict({
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    })


def upload_image(c, path, field_type_name):
    if not os.path.exists(path):
        return None, f"missing file {path}"
    with open(path, "rb") as f:
        data = f.read()
    asset_service = c.get_service("AssetService")
    op = c.get_type("AssetOperation")
    asset = op.create
    asset.name = os.path.basename(path)
    asset.image_asset.data = data
    asset.image_asset.file_size = len(data)
    asset.image_asset.mime_type = c.enums.MimeTypeEnum.IMAGE_PNG
    resp = asset_service.mutate_assets(customer_id=CUSTOMER_ID, operations=[op])
    asset_rn = resp.results[0].resource_name

    aga_service = c.get_service("AssetGroupAssetService")
    aga_op = c.get_type("AssetGroupAssetOperation")
    link = aga_op.create
    link.asset = asset_rn
    link.asset_group = f"customers/{CUSTOMER_ID}/assetGroups/{ASSET_GROUP_ID}"
    link.field_type = getattr(c.enums.AssetFieldTypeEnum, field_type_name)
    aga_resp = aga_service.mutate_asset_group_assets(
        customer_id=CUSTOMER_ID, operations=[aga_op]
    )
    return aga_resp.results[0].resource_name, None


def add_text_assets(c, texts, field_type_name):
    asset_service = c.get_service("AssetService")
    aga_service = c.get_service("AssetGroupAssetService")
    field_type = getattr(c.enums.AssetFieldTypeEnum, field_type_name)
    added = []
    for text in texts:
        op = c.get_type("AssetOperation")
        asset = op.create
        asset.name = f"auto_{field_type_name}_{text[:12]}"
        asset.text_asset.text = text
        resp = asset_service.mutate_assets(customer_id=CUSTOMER_ID, operations=[op])
        asset_rn = resp.results[0].resource_name

        aga_op = c.get_type("AssetGroupAssetOperation")
        link = aga_op.create
        link.asset = asset_rn
        link.asset_group = f"customers/{CUSTOMER_ID}/assetGroups/{ASSET_GROUP_ID}"
        link.field_type = field_type
        aga_resp = aga_service.mutate_asset_group_assets(
            customer_id=CUSTOMER_ID, operations=[aga_op]
        )
        added.append({"text": text, "resource": aga_resp.results[0].resource_name})
    return added


def remove_asset_group_links(c, resource_names):
    aga = c.get_service("AssetGroupAssetService")
    ops = []
    for rn in resource_names:
        op = c.get_type("AssetGroupAssetOperation")
        op.remove = rn
        ops.append(op)
    if not ops:
        return []
    resp = aga.mutate_asset_group_assets(customer_id=CUSTOMER_ID, operations=ops)
    return [r.resource_name for r in resp.results]


def add_start_sitelink(c):
    asset_service = c.get_service("AssetService")
    op = c.get_type("AssetOperation")
    asset = op.create
    asset.name = "sitelink_start_signup"
    asset.final_urls.append("https://hapgyuk.com/start")
    sl = asset.sitelink_asset
    sl.link_text = "지금 무료 시작"
    sl.description1 = "3분 AI 자소서 첨삭"
    sl.description2 = "가입 후 바로 진단"
    resp = asset_service.mutate_assets(customer_id=CUSTOMER_ID, operations=[op])
    asset_rn = resp.results[0].resource_name

    ca_service = c.get_service("CustomerAssetService")
    cop = c.get_type("CustomerAssetOperation")
    link = cop.create
    link.asset = asset_rn
    link.field_type = c.enums.AssetFieldTypeEnum.SITELINK
    resp2 = ca_service.mutate_customer_assets(customer_id=CUSTOMER_ID, operations=[cop])
    return resp2.results[0].resource_name


def main():
    c = client()
    results = {}
    try:
        results["replaced_old_images"] = remove_asset_group_links(
            c, REPLACE_ASSET_GROUP_ASSETS
        )
    except GoogleAdsException as ex:
        results["replaced_old_images"] = ex.failure.errors[0].message

    for path, ftype in IMAGE_UPLOADS:
        try:
            rn, err = upload_image(c, path, ftype)
            results[f"image_{ftype}"] = rn if rn else err
        except GoogleAdsException as ex:
            results[f"image_{ftype}"] = ex.failure.errors[0].message

    try:
        results["headlines"] = add_text_assets(c, NEW_HEADLINES, "HEADLINE")
    except GoogleAdsException as ex:
        results["headlines"] = ex.failure.errors[0].message

    try:
        results["descriptions"] = add_text_assets(c, NEW_DESCRIPTIONS, "DESCRIPTION")
    except GoogleAdsException as ex:
        results["descriptions"] = ex.failure.errors[0].message

    try:
        results["add_start_sitelink"] = add_start_sitelink(c)
    except GoogleAdsException as ex:
        results["add_start_sitelink"] = ex.failure.errors[0].message

    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Mobile spend control for PMax.

PMax does not allow device bid modifiers via API. This script:
1. Confirms network/device waste (mobile YouTube is main leak)
2. Creates a desktop-only Search campaign for high-intent capture
"""
import json
import os
import sys

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.protobuf import field_mask_pb2

CUSTOMER_ID = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "4937153045").replace("-", "")
PMAX_CAMPAIGN_ID = 23843241063
SEARCH_BUDGET_KRW = int(os.environ.get("DESKTOP_SEARCH_BUDGET_KRW", "15000"))
SEARCH_CAMPAIGN_NAME = "검색-데스크톱-가입"

KEYWORDS = [
    "ai 자소서 첨삭", "자소서 ai", "자소서 첨삭", "자기소개서 첨삭 ai",
    "자소서 첨삭 추천", "ai 자기소개서 첨삭", "자소서 ai 첨삭",
]


def client():
    return GoogleAdsClient.load_from_dict({
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    })


def network_breakdown(c):
    ga = c.get_service("GoogleAdsService")
    q = f"""
        SELECT segments.ad_network_type, segments.device,
               metrics.cost_micros, metrics.conversions, metrics.all_conversions
        FROM campaign WHERE campaign.id = {PMAX_CAMPAIGN_ID}
          AND segments.date DURING LAST_30_DAYS
    """
    rows = []
    for batch in ga.search_stream(customer_id=CUSTOMER_ID, query=q):
        for row in batch.results:
            rows.append({
                "network": row.segments.ad_network_type.name,
                "device": row.segments.device.name,
                "cost": round(row.metrics.cost_micros / 1e6, 0),
                "conversions": row.metrics.conversions,
                "all_conversions": row.metrics.all_conversions,
            })
    return rows


def find_existing_search(c):
    ga = c.get_service("GoogleAdsService")
    q = f"""
        SELECT campaign.id, campaign.name, campaign.status
        FROM campaign
        WHERE campaign.name = '{SEARCH_CAMPAIGN_NAME}'
          AND campaign.status != 'REMOVED'
    """
    for batch in ga.search_stream(customer_id=CUSTOMER_ID, query=q):
        for row in batch.results:
            return row.campaign.id
    return None


def set_device_modifiers(c, campaign_id):
    cs = c.get_service("CampaignCriterionService")
    campaign_rn = c.get_service("CampaignService").campaign_path(CUSTOMER_ID, campaign_id)
    ga = c.get_service("GoogleAdsService")
    q = f"""
        SELECT campaign_criterion.criterion_id, campaign_criterion.device.type
        FROM campaign_criterion
        WHERE campaign.id = {campaign_id} AND campaign_criterion.type = 'DEVICE'
    """
    existing = {}
    for batch in ga.search_stream(customer_id=CUSTOMER_ID, query=q):
        for row in batch.results:
            existing[row.campaign_criterion.device.type_.name] = row.campaign_criterion.criterion_id

    targets = {"MOBILE": 0.0, "TABLET": 0.0, "DESKTOP": 1.3}
    ops = []
    for device, modifier in targets.items():
        op = c.get_type("CampaignCriterionOperation")
        if device in existing:
            crit = op.update
            crit.resource_name = cs.campaign_criterion_path(
                CUSTOMER_ID, campaign_id, existing[device]
            )
            crit.bid_modifier = modifier
            op.update_mask.paths.append("bid_modifier")
        else:
            crit = op.create
            crit.campaign = campaign_rn
            crit.device.type_ = c.enums.DeviceEnum[device]
            crit.bid_modifier = modifier
        ops.append(op)
    return cs.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=ops)


def create_desktop_search(c):
    existing = find_existing_search(c)
    if existing:
        resp = set_device_modifiers(c, existing)
        return {
            "action": "updated_existing",
            "campaign_id": existing,
            "devices": [r.resource_name for r in resp.results],
        }

    budget_svc = c.get_service("CampaignBudgetService")
    bop = c.get_type("CampaignBudgetOperation")
    budget = bop.create
    budget.name = f"{SEARCH_CAMPAIGN_NAME} budget"
    budget.amount_micros = max(SEARCH_BUDGET_KRW // 30, 500) * 1_000_000
    budget.delivery_method = c.enums.BudgetDeliveryMethodEnum.STANDARD
    budget.explicitly_shared = False
    budget_resp = budget_svc.mutate_campaign_budgets(
        customer_id=CUSTOMER_ID, operations=[bop]
    )
    budget_rn = budget_resp.results[0].resource_name

    camp_svc = c.get_service("CampaignService")
    cop = c.get_type("CampaignOperation")
    camp = cop.create
    camp.name = SEARCH_CAMPAIGN_NAME
    camp.advertising_channel_type = c.enums.AdvertisingChannelTypeEnum.SEARCH
    camp.status = c.enums.CampaignStatusEnum.ENABLED
    camp.campaign_budget = budget_rn
    camp.maximize_conversions = c.get_type("MaximizeConversions")
    camp.geo_target_type_setting.positive_geo_target_type = (
        c.enums.PositiveGeoTargetTypeEnum.PRESENCE
    )
    camp.geo_target_type_setting.negative_geo_target_type = (
        c.enums.NegativeGeoTargetTypeEnum.PRESENCE
    )
    camp.contains_eu_political_advertising = (
        c.enums.EuPoliticalAdvertisingStatusEnum.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING
    )
    camp.network_settings.target_google_search = True
    camp.network_settings.target_search_network = False
    camp.network_settings.target_content_network = False
    camp.network_settings.target_partner_search_network = False
    camp_resp = camp_svc.mutate_campaigns(customer_id=CUSTOMER_ID, operations=[cop])
    campaign_id = int(camp_resp.results[0].resource_name.split("/")[-1])

    # Korea geo target 2410
    crit_svc = c.get_service("CampaignCriterionService")
    campaign_rn = camp_svc.campaign_path(CUSTOMER_ID, campaign_id)
    geo_op = c.get_type("CampaignCriterionOperation")
    geo = geo_op.create
    geo.campaign = campaign_rn
    geo.location.geo_target_constant = "geoTargetConstants/2410"
    crit_svc.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=[geo_op])

    set_device_modifiers(c, campaign_id)

    ag_svc = c.get_service("AdGroupService")
    ag_op = c.get_type("AdGroupOperation")
    ag = ag_op.create
    ag.name = "핵심 키워드"
    ag.campaign = campaign_rn
    ag.status = c.enums.AdGroupStatusEnum.ENABLED
    ag_resp = ag_svc.mutate_ad_groups(customer_id=CUSTOMER_ID, operations=[ag_op])
    ag_rn = ag_resp.results[0].resource_name

    agc_svc = c.get_service("AdGroupCriterionService")
    kw_ops = []
    for text in KEYWORDS:
        op = c.get_type("AdGroupCriterionOperation")
        crit = op.create
        crit.ad_group = ag_rn
        crit.status = c.enums.AdGroupCriterionStatusEnum.ENABLED
        crit.keyword.text = text
        crit.keyword.match_type = c.enums.KeywordMatchTypeEnum.PHRASE
        kw_ops.append(op)
    agc_svc.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=kw_ops)

    ad_svc = c.get_service("AdGroupAdService")
    ad_op = c.get_type("AdGroupAdOperation")
    ad_group_ad = ad_op.create
    ad_group_ad.ad_group = ag_rn
    ad_group_ad.status = c.enums.AdGroupAdStatusEnum.ENABLED
    ad = ad_group_ad.ad
    ad.final_urls.append("https://hapgyuk.com/start")
    rsa = ad.responsive_search_ad
    for h in [
        "AI 자소서 첨삭 3분 완성", "합격닷컴 AI 자소서", "지금 무료로 합격 진단",
        "자소서 첨삭 AI 추천", "3분 만에 AI 자소서 첨삭",
    ]:
        asset = c.get_type("AdTextAsset")
        asset.text = h
        rsa.headlines.append(asset)
    for d in [
        "AI가 3분 만에 자소서를 첨삭합니다. 지금 무료로 시작하세요.",
        "합격률 높은 자소서 작성. AI 진단 후 바로 첨삭 받으세요.",
    ]:
        asset = c.get_type("AdTextAsset")
        asset.text = d
        rsa.descriptions.append(asset)
    ad_svc.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=[ad_op])

    return {
        "action": "created",
        "campaign_id": campaign_id,
        "budget_krw": SEARCH_BUDGET_KRW,
        "keywords": KEYWORDS,
        "devices": "mobile/tablet excluded, desktop +30%",
    }


def main():
    c = client()
    breakdown = network_breakdown(c)
    try:
        result = create_desktop_search(c)
        print(json.dumps({
            "status": "ok",
            "pmax_network_breakdown": breakdown,
            "desktop_search": result,
            "pmax_note": "PMax device bid modifiers not supported by API",
        }, indent=2, ensure_ascii=False))
    except GoogleAdsException as ex:
        print(json.dumps({
            "status": "error",
            "message": ex.failure.errors[0].message,
            "pmax_network_breakdown": breakdown,
        }, indent=2, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

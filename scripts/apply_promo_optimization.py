#!/usr/bin/env python3
"""Apply promo-period optimizations for hapgyuk.com Google Ads."""
import json
import os
import sys

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.protobuf import field_mask_pb2

CUSTOMER_ID = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "4937153045").replace("-", "")
CAMPAIGN_ID = 23843241063
ASSET_GROUP_ID = 6712854804
BUDGET_ID = 15577823193
SIGNUP_ACTION_ID = 7418047105
PURCHASE_ACTION_ID = 7418248014
PROMO_TOTAL_KRW = 100_000
PROMO_END_DATE = "2026-06-30"
SIGNUP_VALUE_KRW = 1770  # 5900 * 30%

# From 검색 광고 ad group negatives (phrase match)
NEGATIVE_KEYWORDS = [
    "pdf", "doc", "hwp", "ppt", "무료", "공짜", "다운로드", "전화번호",
    "고객센터", "로그인", "환불", "양식", "샘플", "예시", "베끼기", "복붙",
    "자소서 샘플", "자소서 예시", "자소서 쓰는법", "자소서 양식", "자소서 작성법",
    "합격닷컴", "합격 닷컴", "hapgyuk", "합격닷컴.com",
    "링커리어", "잡코리아", "사람인", "크몽", "코멘토",
    "대필", "표절 검사 무료", "무료 첨삭", "gpt", "챗gpt", "챗지피티",
    "모의면접", "인적성", "역량검사",
]

# High-intent themes from historical search term winners
NEW_SEARCH_THEMES = [
    "ai 자소서 첨삭", "자소서 첨삭 ai", "자소서 ai", "자소서 ai 첨삭",
    "ai 자소서", "자기소개서 첨삭 ai", "ai 자기소개서 첨삭",
    "자소서 첨삭", "자기소개서 첨삭", "자소서 첨삭 사이트",
    "자소서 첨삭 추천", "AI 자소서 첨삭", "자소서 첨삭 ai 추천",
    "취업 자소서 첨삭", "공기업 자소서 첨삭", "자소서 ai 추천",
    "자소서 코칭", "자소서 첨삭 서비스", "ATS 자소서",
    "자소서 합격 진단", "서류 합격 자소서",
]

# Low-intent themes to remove (partial match on resource names via query)
REMOVE_THEME_KEYWORDS = [
    "맞춤법", "글자수", "학원", "잡코리아", "링커리어", "예시", "샘플",
    "지원동기 예시", "성장과정", "사람인", "소제목", "꿀팁", "프롬프트",
    "모의 면접", "인적성", "역량", "대행", "플랫폼",
]


def client():
    return GoogleAdsClient.load_from_dict({
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    })


def run(name, fn):
    try:
        result = fn()
        print(json.dumps({"step": name, "status": "ok", "result": result}, ensure_ascii=False))
        return result
    except GoogleAdsException as ex:
        err = ex.failure.errors[0]
        print(json.dumps({
            "step": name, "status": "error",
            "message": err.message, "code": str(err.error_code),
        }, ensure_ascii=False), file=sys.stderr)
        return None


def update_signup_conversion(c):
    svc = c.get_service("ConversionActionService")
    op = c.get_type("ConversionActionOperation")
    ca = op.update
    ca.resource_name = svc.conversion_action_path(CUSTOMER_ID, SIGNUP_ACTION_ID)
    ca.include_in_conversions_metric = True
    ca.value_settings.default_value = float(SIGNUP_VALUE_KRW)
    ca.value_settings.always_use_default_value = True
    op.update_mask = field_mask_pb2.FieldMask(paths=[
        "include_in_conversions_metric",
        "value_settings.default_value", "value_settings.always_use_default_value",
    ])
    resp = svc.mutate_conversion_actions(customer_id=CUSTOMER_ID, operations=[op])
    return resp.results[0].resource_name


def update_purchase_secondary(c):
    svc = c.get_service("ConversionActionService")
    op = c.get_type("ConversionActionOperation")
    ca = op.update
    ca.resource_name = svc.conversion_action_path(CUSTOMER_ID, PURCHASE_ACTION_ID)
    ca.primary_for_goal = False
    op.update_mask = field_mask_pb2.FieldMask(paths=["primary_for_goal"])
    resp = svc.mutate_conversion_actions(customer_id=CUSTOMER_ID, operations=[op])
    return resp.results[0].resource_name


def update_conversion_goals(c):
    svc = c.get_service("CustomerConversionGoalService")
    ops = []
    for category, origin, biddable in [
        ("SIGNUP", "WEBSITE", True),
        ("PURCHASE", "WEBSITE", False),
        ("PAGE_VIEW", "WEBSITE", False),
    ]:
        op = c.get_type("CustomerConversionGoalOperation")
        g = op.update
        g.resource_name = (
            f"customers/{CUSTOMER_ID}/customerConversionGoals/{category}~{origin}"
        )
        g.biddable = biddable
        op.update_mask = field_mask_pb2.FieldMask(paths=["biddable"])
        ops.append(op)
    resp = svc.mutate_customer_conversion_goals(customer_id=CUSTOMER_ID, operations=ops)
    return [r.resource_name for r in resp.results]


def update_budget_and_end_date(c):
    bs = c.get_service("CampaignBudgetService")
    bop = c.get_type("CampaignBudgetOperation")
    b = bop.update
    b.resource_name = f"customers/{CUSTOMER_ID}/campaignBudgets/{BUDGET_ID}"
    b.total_amount_micros = PROMO_TOTAL_KRW * 1_000_000
    bop.update_mask = field_mask_pb2.FieldMask(paths=["total_amount_micros"])
    bs.mutate_campaign_budgets(customer_id=CUSTOMER_ID, operations=[bop])

    cs = c.get_service("CampaignService")
    cop = c.get_type("CampaignOperation")
    camp = cop.update
    camp.resource_name = f"customers/{CUSTOMER_ID}/campaigns/{CAMPAIGN_ID}"
    camp.end_date_time = f"{PROMO_END_DATE} 23:59:59"
    cop.update_mask = field_mask_pb2.FieldMask(paths=["end_date_time"])
    resp = cs.mutate_campaigns(customer_id=CUSTOMER_ID, operations=[cop])
    return {"budget_cap_krw": PROMO_TOTAL_KRW, "end_date": PROMO_END_DATE,
            "campaign": resp.results[0].resource_name}


def update_bidding_maximize_conversions(c):
    cs = c.get_service("CampaignService")
    op = c.get_type("CampaignOperation")
    camp = op.update
    camp.resource_name = f"customers/{CUSTOMER_ID}/campaigns/{CAMPAIGN_ID}"
    camp.maximize_conversions = c.get_type("MaximizeConversions")
    op.update_mask = field_mask_pb2.FieldMask(paths=["maximize_conversions.target_cpa_micros"])
    # Clear tROAS by setting maximize_conversions - use target_cpa unset
    try:
        resp = cs.mutate_campaigns(customer_id=CUSTOMER_ID, operations=[op])
        return resp.results[0].resource_name
    except GoogleAdsException:
        camp2 = op.update
        camp2.maximize_conversions = c.get_type("MaximizeConversions")
        op.update_mask = field_mask_pb2.FieldMask(paths=["maximize_conversions"])
        resp = cs.mutate_campaigns(customer_id=CUSTOMER_ID, operations=[op])
        return resp.results[0].resource_name


def update_landing_url(c):
    ags = c.get_service("AssetGroupService")
    op = c.get_type("AssetGroupOperation")
    ag = op.update
    ag.resource_name = f"customers/{CUSTOMER_ID}/assetGroups/{ASSET_GROUP_ID}"
    ag.final_urls.append("https://hapgyuk.com/start")
    op.update_mask = field_mask_pb2.FieldMask(paths=["final_urls"])
    resp = ags.mutate_asset_groups(customer_id=CUSTOMER_ID, operations=[op])
    return resp.results[0].resource_name


def add_negative_keywords(c):
    campaign_service = c.get_service("CampaignService")
    campaign_rn = campaign_service.campaign_path(CUSTOMER_ID, CAMPAIGN_ID)
    ops = []
    for kw in NEGATIVE_KEYWORDS:
        op = c.get_type("CampaignCriterionOperation")
        crit = op.create
        crit.campaign = campaign_rn
        crit.negative = True
        crit.keyword.text = kw
        crit.keyword.match_type = c.enums.KeywordMatchTypeEnum.PHRASE
        ops.append(op)
    # Batch in chunks of 20
    added = []
    cs = c.get_service("CampaignCriterionService")
    for i in range(0, len(ops), 20):
        chunk = ops[i:i+20]
        resp = cs.mutate_campaign_criteria(customer_id=CUSTOMER_ID, operations=chunk)
        added.extend([r.resource_name for r in resp.results])
    return {"count": len(added)}


def refresh_search_themes(c):
    ga = c.get_service("GoogleAdsService")
    ags = c.get_service("AssetGroupSignalService")

    # Remove low-intent themes
    existing = []
    q = """
        SELECT asset_group_signal.resource_name, asset_group_signal.search_theme.text
        FROM asset_group_signal
        WHERE campaign.id = {}
    """.format(CAMPAIGN_ID)
    for batch in ga.search_stream(customer_id=CUSTOMER_ID, query=q):
        for row in batch.results:
            text = row.asset_group_signal.search_theme.text
            if any(k in text for k in REMOVE_THEME_KEYWORDS):
                existing.append(row.asset_group_signal.resource_name)

    removed = []
    for rn in existing:
        op = c.get_type("AssetGroupSignalOperation")
        op.remove = rn
        ags.mutate_asset_group_signals(customer_id=CUSTOMER_ID, operations=[op])
        removed.append(rn)

    # Add new high-intent themes (skip duplicates)
    current_themes = set()
    q2 = """
        SELECT asset_group_signal.search_theme.text
        FROM asset_group_signal WHERE campaign.id = {}
    """.format(CAMPAIGN_ID)
    for batch in ga.search_stream(customer_id=CUSTOMER_ID, query=q2):
        for row in batch.results:
            current_themes.add(row.asset_group_signal.search_theme.text)

    ag_rn = f"customers/{CUSTOMER_ID}/assetGroups/{ASSET_GROUP_ID}"
    added = []
    for theme in NEW_SEARCH_THEMES:
        if theme in current_themes:
            continue
        op = c.get_type("AssetGroupSignalOperation")
        sig = op.create
        sig.asset_group = ag_rn
        sig.search_theme.text = theme
        resp = ags.mutate_asset_group_signals(customer_id=CUSTOMER_ID, operations=[op])
        added.append(theme)

    return {"removed": len(removed), "added": added}


def main():
    c = client()
    steps = [
        ("signup_conversion", lambda: update_signup_conversion(c)),
        ("purchase_secondary", lambda: update_purchase_secondary(c)),
        ("conversion_goals", lambda: update_conversion_goals(c)),
        ("budget_end_date", lambda: update_budget_and_end_date(c)),
        ("bidding_maximize_conversions", lambda: update_bidding_maximize_conversions(c)),
        ("landing_url", lambda: update_landing_url(c)),
        ("negative_keywords", lambda: add_negative_keywords(c)),
        ("search_themes", lambda: refresh_search_themes(c)),
    ]
    for name, fn in steps:
        run(name, fn)


if __name__ == "__main__":
    main()

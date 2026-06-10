#!/usr/bin/env python3
"""Daily Google Ads performance report (KST)."""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

from google.ads.googleads.errors import GoogleAdsException

from google_ads_config import customer_id, make_client, test_api_access

KST = timezone(timedelta(hours=9))
CUSTOMER_ID = customer_id()
CAMPAIGN_ID = 23843241063
PROMO_TOTAL = 100_000
PROMO_END = datetime(2026, 6, 30, tzinfo=KST)


def search(query):
    ga = make_client().get_service("GoogleAdsService")
    rows = []
    for batch in ga.search_stream(customer_id=CUSTOMER_ID, query=query):
        for row in batch.results:
            rows.append(row)
    return rows


def money(micros):
    return round((micros or 0) / 1_000_000, 0)


def build_report():
    now = datetime.now(KST)
    days_left = max((PROMO_END.date() - now.date()).days, 0)

    camp_rows = search(f"""
        SELECT campaign.name, campaign.status, campaign.bidding_strategy_type,
               campaign.end_date_time, campaign_budget.amount_micros,
               campaign_budget.total_amount_micros,
               metrics.cost_micros, metrics.clicks, metrics.impressions,
               metrics.conversions, metrics.conversions_value,
               metrics.cost_per_conversion, metrics.ctr
        FROM campaign
        WHERE campaign.id = {CAMPAIGN_ID}
          AND segments.date DURING LAST_7_DAYS
    """)

    lifetime = search(f"""
        SELECT metrics.cost_micros, metrics.conversions, metrics.conversions_value,
               metrics.clicks
        FROM campaign WHERE campaign.id = {CAMPAIGN_ID}
    """)

    yesterday = search(f"""
        SELECT metrics.cost_micros, metrics.clicks, metrics.conversions,
               metrics.conversions_value, segments.device
        FROM campaign
        WHERE campaign.id = {CAMPAIGN_ID}
          AND segments.date DURING YESTERDAY
    """)

    by_action = search(f"""
        SELECT segments.conversion_action_name, segments.device,
               metrics.conversions, metrics.all_conversions
        FROM campaign
        WHERE campaign.id = {CAMPAIGN_ID}
          AND segments.date DURING LAST_7_DAYS
    """)

    devices = search(f"""
        SELECT segments.device, metrics.cost_micros, metrics.conversions,
               metrics.conversions_value
        FROM campaign
        WHERE campaign.id = {CAMPAIGN_ID}
          AND segments.date DURING LAST_7_DAYS
    """)

    total_spend = money(lifetime[0].metrics.cost_micros) if lifetime else 0
    remaining = PROMO_TOTAL - total_spend
    daily_needed = round(remaining / days_left, 0) if days_left else remaining

    y_cost, y_clicks, y_conv, y_value = 0, 0, 0, 0
    for r in yesterday:
        y_cost += money(r.metrics.cost_micros)
        y_clicks += r.metrics.clicks
        y_conv += r.metrics.conversions
        y_value += r.metrics.conversions_value

    d7_cost, d7_conv, d7_value, d7_clicks = 0, 0, 0, 0
    for r in camp_rows:
        d7_cost += money(r.metrics.cost_micros)
        d7_conv += r.metrics.conversions
        d7_value += r.metrics.conversions_value
        d7_clicks += r.metrics.clicks

    device_data = {}
    for r in devices:
        d = r.segments.device.name
        device_data[d] = {
            "cost": device_data.get(d, {}).get("cost", 0) + money(r.metrics.cost_micros),
            "conv": device_data.get(d, {}).get("conv", 0) + r.metrics.conversions,
        }

    actions = {}
    for r in by_action:
        name = r.segments.conversion_action_name
        actions[name] = actions.get(name, 0) + r.metrics.all_conversions

    roas_7d = round(d7_value / d7_cost, 2) if d7_cost else 0
    cpa_7d = round(d7_cost / d7_conv, 0) if d7_conv else 0
    signup_7d = actions.get("Sign-up", 0)
    purchase_7d = actions.get("Purchase", 0)

    alerts = []
    if remaining <= 0:
        alerts.append("프로모션 예산 소진")
    if days_left <= 5 and remaining > 10000:
        alerts.append(f"종료 {days_left}일 전 — 잔여 ₩{remaining:,.0f} 긴급 소진 필요")
    if y_cost == 0 and now.hour >= 12:
        alerts.append("어제/오늘 지출 0 — 캠페인 상태 점검")
    if device_data.get("MOBILE", {}).get("cost", 0) > device_data.get("DESKTOP", {}).get("cost", 0) and device_data.get("MOBILE", {}).get("conv", 0) == 0:
        alerts.append("모바일 지출 > 데스크톱, 모바일 전환 0")
    if signup_7d < 2 and d7_cost > 5000:
        alerts.append("7일 가입 2건 미만 — 소재/랜딩/테마 재검토")
    if purchase_7d == 0 and d7_cost > 15000:
        alerts.append("7일 결제 0건 — 가입→결제 퍼널 점검")

    on_track = signup_7d >= max(days_left * 0.5, 3) or (signup_7d >= 1 and days_left > 14)

    report = {
        "generated_at_kst": now.strftime("%Y-%m-%d %H:%M KST"),
        "promo": {
            "total_budget": PROMO_TOTAL,
            "spent": total_spend,
            "remaining": remaining,
            "days_left": days_left,
            "daily_needed_to_burn": daily_needed,
            "end_date": "2026-06-30",
        },
        "yesterday": {
            "cost": y_cost, "clicks": y_clicks,
            "conversions": round(y_conv, 1), "value": round(y_value, 0),
        },
        "last_7_days": {
            "cost": d7_cost, "clicks": d7_clicks,
            "signups": round(signup_7d, 1),
            "purchases": round(purchase_7d, 1),
            "roas": roas_7d, "cpa": cpa_7d,
        },
        "devices_7d": device_data,
        "alerts": alerts,
        "on_track": on_track,
        "bidding": camp_rows[0].campaign.bidding_strategy_type.name if camp_rows else "UNKNOWN",
    }
    return report


def format_markdown(r):
    p = r["promo"]
    y = r["yesterday"]
    w = r["last_7_days"]
    lines = [
        f"# 합격닷컴 일일 광고 리포트",
        f"**생성:** {r['generated_at_kst']}",
        "",
        "## 프로모션 예산",
        f"| 항목 | 값 |",
        f"|------|-----|",
        f"| 총 한도 | ₩{p['total_budget']:,} |",
        f"| 사용 | ₩{p['spent']:,} |",
        f"| 잔여 | ₩{p['remaining']:,} |",
        f"| D-day | {p['days_left']}일 (6/30 마감) |",
        f"| 일평균 필요 소진 | ₩{p['daily_needed_to_burn']:,} |",
        "",
        "## 어제",
        f"- 지출 ₩{y['cost']:,} / 클릭 {y['clicks']} / 전환 {y['conversions']} / 가치 ₩{y['value']:,}",
        "",
        "## 최근 7일",
        f"- 지출 ₩{w['cost']:,} / 가입 {w['signups']} / 결제 {w['purchases']}",
        f"- ROAS {w['roas']} / CPA ₩{w['cpa']:,}",
        f"- 입찰: {r['bidding']}",
        "",
        "## 디바이스 (7일)",
    ]
    for d, v in r["devices_7d"].items():
        lines.append(f"- {d}: ₩{v['cost']:,} / 전환 {v['conv']}")
    if r["alerts"]:
        lines += ["", "## ⚠️ 알림"]
        for a in r["alerts"]:
            lines.append(f"- {a}")
    status = "정상 궤도" if r["on_track"] else "목표 미달 — 조치 검토 중"
    lines += ["", f"**판정:** {status}"]
    return "\n".join(lines)


if __name__ == "__main__":
    try:
        test_api_access()
        report = build_report()
        md = format_markdown(report)
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out_dir = os.environ.get("REPORT_DIR", os.path.join(root, "reports"))
        os.makedirs(out_dir, exist_ok=True)
        date_str = datetime.now(KST).strftime("%Y-%m-%d")
        with open(f"{out_dir}/{date_str}.md", "w") as f:
            f.write(md)
        with open(f"{out_dir}/{date_str}.json", "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(md)
    except GoogleAdsException as ex:
        print(ex.failure.errors[0].message, file=sys.stderr)
        sys.exit(1)

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
        # all_conversions: 태그 실제 발생 수 (conversions 컬럼은 설정에 따라 0일 수 있음)
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


def progress_bar(spent, total, width=20):
    pct = min(spent / total, 1.0) if total else 0
    filled = round(pct * width)
    return f"[{'█' * filled}{'░' * (width - filled)}] {pct * 100:.0f}%"


def format_markdown(r):
    p = r["promo"]
    y = r["yesterday"]
    w = r["last_7_days"]
    status = "✅ 정상 궤도" if r["on_track"] else "⚠️ 목표 미달 — 조치 검토 중"
    bar = progress_bar(p["spent"], p["total_budget"])
    lines = [
        "# 합격닷컴 일일 광고 리포트",
        f"**생성:** {r['generated_at_kst']}",
        "",
        f"## {status}",
        "",
        "## 프로모션 예산",
        f"```",
        f"{bar}  ₩{p['spent']:,} / ₩{p['total_budget']:,}",
        f"```",
        "",
        "| 항목 | 값 |",
        "|------|-----|",
        f"| 사용 | ₩{p['spent']:,} |",
        f"| 잔여 | ₩{p['remaining']:,} |",
        f"| D-day | **{p['days_left']}일** (6/30 마감) |",
        f"| 일평균 필요 소진 | ₩{p['daily_needed_to_burn']:,} |",
        "",
        "## 어제",
        f"| 지출 | 클릭 | 전환 | 가치 |",
        f"|------|------|------|------|",
        f"| ₩{y['cost']:,} | {y['clicks']} | {y['conversions']} | ₩{y['value']:,} |",
        "",
        "## 최근 7일",
        f"| 지출 | 가입 | 결제 | ROAS | CPA |",
        f"|------|------|------|------|-----|",
        f"| ₩{w['cost']:,} | {w['signups']} | {w['purchases']} | {w['roas']} | ₩{w['cpa']:,} |",
        f"| 입찰 | {r['bidding']} | | | |",
        "",
        "## 디바이스 (7일)",
        "| 디바이스 | 지출 | 전환 |",
        "|----------|------|------|",
    ]
    for d, v in r["devices_7d"].items():
        lines.append(f"| {d} | ₩{v['cost']:,} | {v['conv']} |")
    if r["alerts"]:
        lines += ["", "## ⚠️ 알림"]
        for a in r["alerts"]:
            lines.append(f"- {a}")
    return "\n".join(lines)


def format_html(r):
    p = r["promo"]
    y = r["yesterday"]
    w = r["last_7_days"]
    status = "정상 궤도" if r["on_track"] else "목표 미달"
    status_color = "#16a34a" if r["on_track"] else "#dc2626"
    pct = min(p["spent"] / p["total_budget"] * 100, 100) if p["total_budget"] else 0
    alerts_html = ""
    if r["alerts"]:
        items = "".join(f"<li>{a}</li>" for a in r["alerts"])
        alerts_html = f'<div class="alerts"><h2>⚠️ 알림</h2><ul>{items}</ul></div>'
    devices_rows = "".join(
        f"<tr><td>{d}</td><td>₩{v['cost']:,}</td><td>{v['conv']}</td></tr>"
        for d, v in r["devices_7d"].items()
    )
    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>합격닷컴 광고 리포트 {r['generated_at_kst']}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:720px;margin:0 auto;padding:24px;background:#f8fafc;color:#0f172a}}
.card{{background:#fff;border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
h1{{font-size:1.4rem;margin:0 0 4px}}
.meta{{color:#64748b;font-size:.9rem;margin-bottom:16px}}
.badge{{display:inline-block;padding:6px 12px;border-radius:999px;color:#fff;font-weight:600;background:{status_color}}}
.bar{{height:12px;background:#e2e8f0;border-radius:6px;overflow:hidden;margin:8px 0}}
.bar-fill{{height:100%;background:linear-gradient(90deg,#3b82f6,#6366f1);width:{pct:.0f}%}}
table{{width:100%;border-collapse:collapse;font-size:.95rem}}
th,td{{padding:8px 10px;text-align:left;border-bottom:1px solid #e2e8f0}}
th{{color:#64748b;font-weight:500}}
.alerts{{background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:12px 16px}}
.stat-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}
.stat{{background:#f1f5f9;border-radius:8px;padding:12px}}
.stat-label{{font-size:.8rem;color:#64748b}}
.stat-value{{font-size:1.2rem;font-weight:700}}
</style></head><body>
<div class="card">
<h1>합격닷컴 일일 광고 리포트</h1>
<div class="meta">{r['generated_at_kst']}</div>
<span class="badge">{status}</span>
</div>
<div class="card">
<h2>프로모션 예산</h2>
<div class="bar"><div class="bar-fill"></div></div>
<p>₩{p['spent']:,} / ₩{p['total_budget']:,} ({pct:.0f}%) · 잔여 ₩{p['remaining']:,}</p>
<div class="stat-grid">
<div class="stat"><div class="stat-label">D-day</div><div class="stat-value">{p['days_left']}일</div></div>
<div class="stat"><div class="stat-label">일평균 필요</div><div class="stat-value">₩{p['daily_needed_to_burn']:,}</div></div>
</div>
</div>
<div class="card"><h2>어제</h2>
<table><tr><th>지출</th><th>클릭</th><th>전환</th><th>가치</th></tr>
<tr><td>₩{y['cost']:,}</td><td>{y['clicks']}</td><td>{y['conversions']}</td><td>₩{y['value']:,}</td></tr></table></div>
<div class="card"><h2>최근 7일</h2>
<table><tr><th>지출</th><th>가입</th><th>결제</th><th>ROAS</th><th>CPA</th></tr>
<tr><td>₩{w['cost']:,}</td><td>{w['signups']}</td><td>{w['purchases']}</td><td>{w['roas']}</td><td>₩{w['cpa']:,}</td></tr></table>
<p style="color:#64748b;margin-top:8px">입찰: {r['bidding']}</p></div>
<div class="card"><h2>디바이스 (7일)</h2>
<table><tr><th>디바이스</th><th>지출</th><th>전환</th></tr>{devices_rows}</table></div>
{alerts_html}
</body></html>"""


def write_outputs(report, md, html, out_dir, date_str):
    daily_dir = os.path.join(out_dir, "daily")
    os.makedirs(daily_dir, exist_ok=True)
    paths = {
        "daily_md": os.path.join(daily_dir, f"{date_str}.md"),
        "daily_json": os.path.join(daily_dir, f"{date_str}.json"),
        "latest_md": os.path.join(out_dir, "latest.md"),
        "latest_html": os.path.join(out_dir, "latest.html"),
        "latest_json": os.path.join(out_dir, "latest.json"),
    }
    with open(paths["daily_md"], "w") as f:
        f.write(md)
    with open(paths["daily_json"], "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    for key in ("latest_md", "latest_html", "latest_json"):
        if key.endswith("_html"):
            with open(paths[key], "w") as f:
                f.write(html)
        elif key.endswith("_md"):
            with open(paths[key], "w") as f:
                f.write(md)
        else:
            with open(paths[key], "w") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a") as f:
            f.write(md)
            f.write("\n")
    return paths


if __name__ == "__main__":
    try:
        test_api_access()
        report = build_report()
        md = format_markdown(report)
        html = format_html(report)
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out_dir = os.environ.get("REPORT_DIR", os.path.join(root, "reports"))
        os.makedirs(out_dir, exist_ok=True)
        date_str = datetime.now(KST).strftime("%Y-%m-%d")
        write_outputs(report, md, html, out_dir, date_str)
        print(md)
    except GoogleAdsException as ex:
        print(ex.failure.errors[0].message, file=sys.stderr)
        sys.exit(1)

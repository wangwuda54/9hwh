from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = ROOT / "data" / "content-assets" / "daily_publish_report.json"
DEFAULT_SITE_URL = "https://www.9hwh.com"
WEBHOOK_ENV_KEYS = ("WECOM_WEBHOOK", "WECHAT_WEBHOOK_URL")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send 9HWH daily publish notifications to WeCom.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT_PATH), help="Path to daily publish report JSON.")
    parser.add_argument("--status", choices=["success", "failure", "no_changes"], required=True, help="Notification status.")
    parser.add_argument("--site-url", default=DEFAULT_SITE_URL, help="Public site URL.")
    parser.add_argument("--dry-run", action="store_true", help="Print notification content without sending.")
    return parser.parse_args()


def load_report(path: Path) -> dict:
    if not path.exists():
        return {
            "status": "failure",
            "run_date": "",
            "published_count": 0,
            "total_published": 0,
            "published_items": [],
            "message": f"Report not found: {path}",
            "errors": [f"Report not found: {path}"],
        }
    return json.loads(path.read_text(encoding="utf-8-sig"))


def now_text() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


def build_full_url(site_url: str, item: dict) -> str:
    if item.get("full_url"):
        return item["full_url"]
    target_url = item.get("target_url", "")
    return urljoin(site_url.rstrip("/") + "/", target_url.lstrip("/"))


def build_success_content(report: dict, site_url: str, run_url: str) -> str:
    items = report.get("published_items") or []
    if not items and report.get("selected_items") and report.get("dry_run"):
        items = report.get("selected_items", [])
    display_count = report.get("published_count", 0)
    if report.get("dry_run") and not report.get("published_items"):
        display_count = report.get("selected_count", display_count)
    lines = [
        "【9HWH 自动发布成功】",
        f"时间：{report.get('generated_at') or now_text()}",
        f"本次发布：{display_count} 篇",
        f"当前 published：{report.get('total_published', 0)} 篇",
        "",
        "链接：",
    ]
    if items:
        for index, item in enumerate(items, start=1):
            lines.extend(
                [
                    f"{index}. {item.get('title', '')}",
                    build_full_url(site_url, item),
                    "",
                ]
            )
    else:
        lines.append("-")
        lines.append("")
    lines.extend([f"站点：{site_url}", f"Actions：{run_url or '-'}"])
    return "\n".join(lines)


def build_no_changes_content(report: dict, site_url: str, run_url: str) -> str:
    return "\n".join(
        [
            "【9HWH 自动发布无新增】",
            "今天没有可发布 reviewed 内容，或发布队列为空。",
            f"当前 published：{report.get('total_published', 0)} 篇",
            f"站点：{site_url}",
            f"Actions：{run_url or '-'}",
        ]
    )


def build_failure_content(report: dict, site_url: str, run_url: str) -> str:
    errors = report.get("errors") or []
    summary = errors[0] if errors else "请检查 GitHub Actions 日志"
    return "\n".join(
        [
            "【9HWH 自动发布失败】",
            "状态：failure",
            f"摘要：{summary}",
            f"站点：{site_url}",
            "请检查 GitHub Actions 日志：",
            run_url or "-",
        ]
    )


def build_content(status: str, report: dict, site_url: str, run_url: str) -> tuple[str, str]:
    if status == "failure":
        return "ERROR", build_failure_content(report, site_url, run_url)
    if status == "no_changes":
        return "INFO", build_no_changes_content(report, site_url, run_url)
    return "INFO", build_success_content(report, site_url, run_url)


def get_webhook() -> str:
    for key in WEBHOOK_ENV_KEYS:
        value = os.environ.get(key, "").strip()
        if value:
            return value
    return ""


def send_text(webhook: str, level: str, content: str) -> None:
    payload = {"msgtype": "text", "text": {"content": f"[{level}] {content}"}}
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(webhook, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=5) as response:
        response.read()


def main() -> int:
    args = parse_args()
    report = load_report(Path(args.report))
    run_url = os.environ.get("GITHUB_RUN_URL", "").strip()
    level, content = build_content(args.status, report, args.site_url.rstrip("/"), run_url)

    if args.dry_run:
        print(f"[DRY-RUN] WeCom notification level={level}")
        print(content)
        return 0

    webhook = get_webhook()
    if not webhook:
        print("[WARN] WeCom webhook is not configured; set WECOM_WEBHOOK or WECHAT_WEBHOOK_URL.")
        return 0

    try:
        send_text(webhook, level, content)
    except (OSError, URLError) as exc:
        print(f"[WARN] WeCom notification failed: {exc}")
        return 0

    print("[OK] WeCom notification sent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS_PATH = ROOT / "data" / "seo" / "outreach_tasks.json"
REPORT_JSON_PATH = ROOT / "data" / "seo" / "outreach_tasks_report.json"
REPORT_MD_PATH = ROOT / "docs" / "outreach-tasks-report.md"


def make_task(
    task_id: str,
    task_type: str,
    platform: str,
    target_page: str,
    anchor: str,
    angle: str,
    priority: str,
    risk_level: str = "low",
) -> dict:
    return {
        "task_id": task_id,
        "type": task_type,
        "platform": platform,
        "target_page": target_page,
        "suggested_anchor_text": anchor,
        "content_angle": angle,
        "priority": priority,
        "status": "planned",
        "risk_level": risk_level,
        "notes": "Manual outreach only. No spam links, no PBN, no bulk directories, no automated comments, no hidden links.",
    }


def build_owned_profile_tasks() -> list[dict]:
    rows = [
        ("wechat-about", "WeChat", "/", "9HWH 海外推广官网", "在品牌介绍页补官网入口，指向首页"),
        ("wechat-service-card", "WeChat", "/services/", "海外推广服务", "把服务总页放在账号服务导航"),
        ("wechat-contact", "WeChat", "/contact/", "联系 9HWH", "在商务联系入口补联系页"),
        ("douyin-bio-home", "Douyin", "/", "9HWH 官网", "把官网首页放进账号简介"),
        ("douyin-pinned-services", "Douyin", "/services/", "海外推广服务总览", "置顶内容介绍服务总页"),
        ("douyin-topic-crypto", "Douyin", "/topics/crypto-promotion/", "加密推广专题", "面向相关视频补专题承接页"),
        ("bilibili-profile-home", "Bilibili", "/", "9HWH", "账号简介放品牌主页"),
        ("bilibili-description-topics", "Bilibili", "/topics/", "推广专题页", "视频简介按主题分流到专题总页"),
        ("youtube-about-home", "YouTube", "/", "9HWH official site", "About 页面补官网"),
        ("youtube-description-services", "YouTube", "/services/overseas-promotion/", "overseas promotion service", "视频简介导向核心服务页"),
        ("youtube-description-platforms", "YouTube", "/platforms/", "traffic channels overview", "渠道解说视频链接平台总页"),
        ("linkedin-company-home", "LinkedIn", "/", "9HWH website", "公司主页官网入口"),
        ("linkedin-featured-services", "LinkedIn", "/services/ad-campaign-support/", "ad campaign support", "精选区链接服务页"),
        ("x-profile-home", "X", "/", "9HWH 官网", "简介保留品牌官网"),
        ("x-pinned-contact", "X", "/contact/", "联系 9HWH", "置顶贴文引导到联系页"),
    ]
    return [make_task(f"owned-profile-{task_id}", "owned_profile", platform, target, anchor, angle, "high") for task_id, platform, target, anchor, angle in rows]


def build_external_article_tasks() -> list[dict]:
    rows = [
        ("launch-checklist-1", "Marketing Blog", "/topics/", "海外推广准备清单", "投稿一篇面向出海团队的准备清单"),
        ("launch-checklist-2", "Performance Blog", "/services/traffic-acquisition/", "流量获取准备", "围绕流量获取前置准备做经验文章"),
        ("launch-checklist-3", "Growth Newsletter", "/services/ad-campaign-support/", "广告投放准备", "讲创意、落地页和审核准备"),
        ("channel-compare-1", "Industry Media", "/platforms/", "TK FB Google 渠道对比", "做渠道对比综述内容"),
        ("channel-compare-2", "Paid Media Blog", "/platforms/fb/", "Facebook 获客路径", "聚焦 Facebook 渠道适配性"),
        ("channel-compare-3", "Paid Media Blog", "/platforms/google/", "Google 获客路径", "聚焦 Google 搜索与展示渠道"),
        ("channel-compare-4", "Creator Newsletter", "/platforms/tk/", "TikTok 推广思路", "聚焦 TikTok 引流承接"),
        ("crypto-checklist-1", "Web3 Content Hub", "/topics/crypto-promotion/", "加密推广准备", "写合规边界与投放准备"),
        ("dating-checklist-1", "App Growth Blog", "/topics/dating-traffic/", "交友流量准备", "讲注册拉新和素材承接"),
        ("game-checklist-1", "Gaming UA Blog", "/topics/game-promotion/", "游戏推广准备", "讲海外买量和素材测试"),
        ("insurance-checklist-1", "Lead Gen Blog", "/topics/insurance-leads/", "保险线索准备", "讲线索型页面承接逻辑"),
        ("loan-checklist-1", "Lead Gen Blog", "/topics/loan-leads/", "贷款线索准备", "讲高风险主题的内容边界"),
        ("immigration-checklist-1", "Lead Gen Blog", "/topics/immigration-leads/", "移民线索准备", "讲咨询前问题筛选"),
        ("creative-checklist-1", "Creative Ops Blog", "/services/media-buying/", "投放素材检查表", "围绕素材制作与复盘"),
        ("service-angle-1", "Agency Directory Blog", "/services/overseas-promotion/", "海外推广服务边界", "解释服务协作边界，不做夸大承诺"),
    ]
    return [make_task(f"external-article-{task_id}", "external_article", platform, target, anchor, angle, "medium") for task_id, platform, target, anchor, angle in rows]


def build_community_answer_tasks() -> list[dict]:
    rows = [
        ("quora-crypto", "Quora", "/topics/crypto-promotion/", "crypto promotion checklist", "回答加密推广前的渠道准备问题"),
        ("quora-dating", "Quora", "/topics/dating-traffic/", "dating traffic planning", "回答交友流量搭建问题"),
        ("quora-game", "Quora", "/topics/game-promotion/", "game promotion planning", "回答游戏买量准备问题"),
        ("quora-services", "Quora", "/services/", "performance marketing services", "回答服务范围问题"),
        ("reddit-growth", "Reddit", "/platforms/", "channel comparison guide", "在真实经验讨论里补渠道对比资源"),
        ("reddit-creative", "Reddit", "/services/media-buying/", "creative review checklist", "围绕素材评审经验补参考链接"),
        ("zhihu-services", "Zhihu", "/services/overseas-promotion/", "海外推广怎么协作", "回答服务协作流程问题"),
        ("zhihu-contact", "Zhihu", "/contact/", "联系咨询前准备", "回答咨询前要准备什么"),
        ("zhihu-fb", "Zhihu", "/platforms/fb/", "Facebook 获客路径", "回答 Facebook 承接路径"),
        ("zhihu-google", "Zhihu", "/platforms/google/", "Google 获客路径", "回答 Google 推广路径"),
        ("zhihu-tk", "Zhihu", "/platforms/tk/", "TikTok 获客路径", "回答 TikTok 渠道承接"),
        ("facebook-group-1", "Facebook Group", "/topics/game-promotion/", "海外游戏推广准备", "在群组讨论里给出公开资源页"),
        ("facebook-group-2", "Facebook Group", "/topics/insurance-leads/", "保险线索页准备", "讨论线索型页面承接"),
        ("discord-community-1", "Discord", "/topics/crypto-promotion/", "exchange acquisition planning", "回答交易所拉新准备问题"),
        ("slack-community-1", "Slack Community", "/services/ad-campaign-support/", "ad launch readiness", "回答广告上量前检查项"),
    ]
    return [make_task(f"community-answer-{task_id}", "community_answer", platform, target, anchor, angle, "medium") for task_id, platform, target, anchor, angle in rows]


def build_partner_link_tasks() -> list[dict]:
    rows = [
        ("partner-page-1", "Partner Site", "/services/overseas-promotion/", "海外推广合作页", "合作页自然提到联合服务能力"),
        ("partner-page-2", "Partner Site", "/services/traffic-acquisition/", "流量获取合作", "合作页面介绍流量协同"),
        ("partner-page-3", "Partner Site", "/services/media-buying/", "媒体购买支持", "合作页介绍素材与投放支持"),
        ("partner-page-4", "Partner Site", "/services/ad-campaign-support/", "广告投放支持", "合作页讲投放准备能力"),
        ("interview-1", "Interview", "/topics/", "推广专题参考", "访谈页链接专题总页"),
        ("interview-2", "Interview", "/topics/game-promotion/", "游戏推广专题", "访谈页链接游戏专题"),
        ("interview-3", "Interview", "/topics/crypto-promotion/", "加密推广专题", "访谈页链接加密专题"),
        ("resource-1", "Resource Center", "/contact/", "联系 9HWH", "资源页补商务联系入口"),
        ("resource-2", "Resource Center", "/services/", "9HWH 服务总览", "资源页补服务总页"),
        ("resource-3", "Resource Center", "/platforms/", "投放渠道总览", "资源页补平台总页"),
    ]
    return [make_task(f"partner-link-{task_id}", "partner_link", platform, target, anchor, angle, "medium") for task_id, platform, target, anchor, angle in rows]


def build_resource_page_tasks() -> list[dict]:
    rows = [
        ("resource-page-1", "Glossary", "/topics/", "海外推广资源", "资源目录页收录专题总页"),
        ("resource-page-2", "Checklist Library", "/services/ad-campaign-support/", "投放准备检查表", "清单库页收录投放准备服务页"),
        ("resource-page-3", "Template Library", "/services/media-buying/", "素材制作资源", "模板页收录素材制作支持页"),
        ("resource-page-4", "Operator Wiki", "/platforms/", "渠道总览", "知识库页收录平台总页"),
        ("resource-page-5", "Agency Resource List", "/services/overseas-promotion/", "海外推广服务", "行业资源页收录服务页"),
    ]
    return [make_task(f"resource-page-{task_id}", "resource_page", platform, target, anchor, angle, "low") for task_id, platform, target, anchor, angle in rows]


def main() -> int:
    tasks = (
        build_owned_profile_tasks()
        + build_external_article_tasks()
        + build_community_answer_tasks()
        + build_partner_link_tasks()
        + build_resource_page_tasks()
    )
    counts = Counter(task["type"] for task in tasks)
    report = {
        "status": "pass",
        "task_count": len(tasks),
        "counts_by_type": dict(counts),
        "policy": {
            "allow": ["manual outreach", "real partnerships", "real communities", "owned profiles"],
            "forbid": ["spam links", "PBN", "bulk directories", "automated comments", "hidden links", "same-content multi-domain cross-linking"],
        },
        "tasks": tasks,
    }

    TASKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    TASKS_PATH.write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    REPORT_JSON_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    rows = [
        "# Outreach Tasks Report",
        "",
        f"- task_count: {len(tasks)}",
        f"- owned_profile: {counts['owned_profile']}",
        f"- external_article: {counts['external_article']}",
        f"- community_answer: {counts['community_answer']}",
        f"- partner_link: {counts['partner_link']}",
        f"- resource_page: {counts['resource_page']}",
        "",
        "## Guardrails",
        "",
        "- No spam links",
        "- No PBN",
        "- No bulk directories",
        "- No automated comments",
        "- No hidden links",
        "- No same-content multi-domain cross-linking",
        "",
        "## Task Preview",
        "",
        "| task_id | type | platform | target_page | priority |",
        "| --- | --- | --- | --- | --- |",
    ]
    for task in tasks:
        rows.append(
            f"| {task['task_id']} | {task['type']} | {task['platform']} | {task['target_page']} | {task['priority']} |"
        )
    REPORT_MD_PATH.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] outreach tasks built: total={len(tasks)} owned_profile={counts['owned_profile']} external_article={counts['external_article']} community_answer={counts['community_answer']} partner_link={counts['partner_link']} resource_page={counts['resource_page']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

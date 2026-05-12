from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOPICS_PATH = ROOT / "site_src" / "data" / "topics.json"


TOPIC_COPY: dict[str, dict[str, object]] = {
    "crypto-promotion": {
        "description": "虚拟币推广与币圈引流主题页，覆盖加密货币推广、交易所拉新、社群承接、内容曝光和获客路径梳理。",
        "summary": "说明虚拟币推广、币圈引流、加密货币推广和交易所拉新怎么开始做获客测试。",
        "preparation": [
            "项目介绍和目标市场",
            "落地页、注册路径或社群承接入口",
            "素材方向、内容角度和预算区间",
            "已有社群、历史流量或注册数据"
        ],
        "cta": "如果你需要做虚拟币推广或币圈引流，可以先发项目介绍、目标市场、落地页和预算范围。",
        "cta_text": "如果你需要做虚拟币推广或币圈引流，可以先发项目介绍、目标市场、落地页和预算范围。",
        "assessment_title": "虚拟币推广怎么开始测试",
        "assessment_items": [
            "先确认项目类型、目标市场、落地页、注册路径和社群承接方式，再判断适合先做搜索、社交流量还是内容曝光。",
            "第一轮重点看点击、注册、社群进入、私聊咨询和用户质量，不只看曝光量。",
            "如果已有社群或历史推广数据，可以先复盘用户来源、注册反馈和素材表现，再安排下一轮渠道测试。"
        ]
    },
    "dating-traffic": {
        "description": "交友项目引流主题页，覆盖交友引流、交友 App 注册、真人交友、交友私聊、社交流量和注册拉新。",
        "summary": "交友项目引流适合交友 App 注册、真人交友、交友私聊和社交流量增长等方向。",
        "preparation": [
            "产品定位和目标用户",
            "目标国家或地区",
            "注册路径、落地页和客服承接方式",
            "短视频、图片或文案素材方向"
        ],
        "cta": "如果你需要交友引流或交友 App 注册增长，可以先发目标用户、市场、注册路径和素材方向。",
        "cta_text": "如果你需要交友引流或交友 App 注册增长，可以先发目标用户、市场、注册路径和素材方向。",
        "assessment_title": "交友引流怎么开始测试",
        "assessment_items": [
            "先确认交友产品形态、目标地区、注册路径和素材方向，再判断适合先测 TK、FB 还是其他社交流量渠道。",
            "测试时重点看注册成本、私聊进入率、用户质量和后续留存，不只看点击和曝光。",
            "如果点击不错但注册弱，优先检查落地页、注册步骤、表单字段和客服承接。"
        ]
    },
    "game-promotion": {
        "description": "游戏推广主题页，覆盖游戏推广、游戏买量、游戏拉新、线上娱乐推广、素材测试和注册转化。",
        "summary": "游戏推广适合需要做游戏买量、游戏拉新、线上娱乐推广和海外用户测试的项目。",
        "preparation": [
            "游戏类型和目标市场",
            "视频素材、图片素材和核心卖点",
            "落地页、下载页或应用商店页面",
            "测试预算、周期和转化目标"
        ],
        "cta": "如果你需要做游戏推广或游戏买量，可以先发游戏类型、目标市场、素材和测试预算。",
        "cta_text": "如果你需要做游戏推广或游戏买量，可以先发游戏类型、目标市场、素材和测试预算。",
        "assessment_title": "游戏买量怎么开始测试",
        "assessment_items": [
            "先确认游戏类型、目标地区、素材方向、下载页或落地页，再规划第一轮渠道和预算。",
            "测试时重点看点击、安装、注册、留存和付费反馈，判断素材和人群是否匹配。",
            "如果已有历史买量数据，可以先复盘素材、渠道、注册成本和留存，再调整下一轮测试。"
        ]
    },
    "finance-leads": {
        "description": "金融咨询获客主题页，覆盖金融咨询获客、理财获客、投资咨询推广、搜索流量、社交流量和咨询线索承接。",
        "summary": "金融咨询获客适合需要做理财获客、投资咨询推广和海外咨询引流的项目。",
        "preparation": [
            "服务范围和目标地区",
            "目标人群和咨询流程",
            "落地页、表单和客服承接方式",
            "广告文案、素材方向和预算区间"
        ],
        "cta": "如果你需要金融咨询获客，可以先发服务范围、目标地区、落地页和咨询承接方式。",
        "cta_text": "如果你需要金融咨询获客，可以先发服务范围、目标地区、落地页和咨询承接方式。",
        "assessment_title": "金融咨询获客怎么开始",
        "assessment_items": [
            "先确认服务范围、目标地区、咨询流程和落地页，再判断适合先做 Google 搜索、FB 人群还是内容渠道。",
            "第一轮重点看搜索词、表单、私聊、电话或 WhatsApp 线索质量，不只看点击量。",
            "如果线索多但质量弱，优先调整关键词、人群、表单字段和客服筛选话术。"
        ]
    },
    "loan-leads": {
        "description": "贷款获客主题页，覆盖贷款获客、贷款推广、贷款咨询引流、搜索流量、表单承接和咨询线索获取。",
        "summary": "贷款获客页面用于说明贷款推广、贷款咨询引流和海外获客测试怎么开始。",
        "preparation": [
            "服务地区和产品类型",
            "落地页、表单字段和咨询流程",
            "目标人群、关键词方向和预算区间",
            "已有账户、历史投放或线索反馈"
        ],
        "cta": "如果你需要贷款获客或贷款咨询引流，可以先发服务地区、产品类型、落地页和预算范围。",
        "cta_text": "如果你需要贷款获客或贷款咨询引流，可以先发服务地区、产品类型、落地页和预算范围。",
        "assessment_title": "贷款获客怎么开始测试",
        "assessment_items": [
            "先确认服务地区、产品类型、落地页、表单字段和咨询路径，再判断适合先做搜索流量还是社交流量。",
            "测试时重点看搜索词、点击、表单提交、私聊进入和线索质量，避免只按点击量判断。",
            "如果已有历史数据，可以先复盘关键词、表单转化、无效线索和客服反馈，再调整下一轮获客方向。"
        ]
    },
    "insurance-leads": {
        "description": "保险获客主题页，覆盖保险获客、保险推广、保险咨询引流、目标人群测试、表单承接和线索筛选。",
        "summary": "保险获客适合需要做保险推广、保险咨询引流和多地区客户获取的项目。",
        "preparation": [
            "服务地区、险种类型和目标人群",
            "落地页、表单和咨询流程",
            "素材方向、关键词方向和预算区间",
            "客服承接方式和线索筛选标准"
        ],
        "cta": "如果你需要保险获客，可以先发服务地区、险种类型、落地页和咨询承接路径。",
        "cta_text": "如果你需要保险获客，可以先发服务地区、险种类型、落地页和咨询承接路径。",
        "assessment_title": "保险获客怎么开始测试",
        "assessment_items": [
            "先确认服务地区、险种类型、目标人群、落地页和表单路径，再判断先测搜索还是社交流量。",
            "第一轮重点看搜索词、表单、私聊、电话咨询和客户匹配度，不只看曝光和点击。",
            "如果咨询量有了但成交弱，优先回看表单字段、页面信任信息和客服筛选流程。"
        ]
    },
    "immigration-leads": {
        "description": "移民咨询获客主题页，覆盖移民获客、移民咨询推广、留学移民线索、搜索流量和咨询承接。",
        "summary": "移民咨询获客适合需要做移民咨询推广、海外咨询引流和线索获取的项目。",
        "preparation": [
            "服务国家、项目类型和目标人群",
            "落地页、案例内容和咨询入口",
            "关键词方向、素材方向和预算区间",
            "客服承接方式和线索筛选标准"
        ],
        "cta": "如果你需要移民咨询获客，可以先发服务国家、项目类型、落地页和咨询流程。",
        "cta_text": "如果你需要移民咨询获客，可以先发服务国家、项目类型、落地页和咨询流程。",
        "assessment_title": "移民咨询获客怎么开始",
        "assessment_items": [
            "先确认服务国家、项目类型、目标人群和落地页内容，再判断先做搜索流量、内容渠道还是社交流量。",
            "测试时重点看搜索词、咨询入口、表单质量和客服沟通反馈，不只看页面访问量。",
            "如果已有咨询数据，可以先复盘来源、问题类型和有效线索比例，再调整关键词和页面内容。"
        ]
    },
    "online-work-leads": {
        "description": "网赚与兼职获客主题页，覆盖在线项目推广、兼职获客、注册拉新、咨询承接和预算测试。",
        "summary": "网赚与兼职获客适合在线项目、兼职项目、注册拉新和咨询线索测试。",
        "preparation": [
            "项目内容、目标用户和目标地区",
            "落地页、注册路径和咨询入口",
            "素材方向、费用说明和预算区间",
            "客服承接方式和线索筛选标准"
        ],
        "cta": "如果你需要在线项目或兼职获客，可以先发项目内容、目标地区、落地页和预算范围。",
        "cta_text": "如果你需要在线项目或兼职获客，可以先发项目内容、目标地区、落地页和预算范围。",
        "assessment_title": "在线项目获客怎么开始测试",
        "assessment_items": [
            "先确认项目内容、目标用户、注册路径和咨询入口，再判断适合先测短视频、社交流量还是搜索流量。",
            "第一轮重点看点击、注册、私聊、表单和有效用户比例，不只看曝光量。",
            "如果反馈不稳定，优先调整素材角度、落地页说明、注册路径和客服承接方式。"
        ]
    }
}

DROP_KEYS = {
    "boundaries",
    "service_fit",
    "risk_notes",
}

REPLACE_TERMS = {
    "合规边界确认": "获客路径梳理",
    "合规评估材料和页面表达信息": "素材、落地页和页面信息",
    "投放地区、资质材料和页面表达说明": "目标地区、素材和页面信息",
    "服务资质、投放地区和页面表达说明": "服务范围、目标地区和页面信息",
    "费用和免责声明边界": "费用说明和咨询流程",
    "素材表达边界": "素材方向",
    "如果你需要评估": "如果你需要做",
    "评估重点": "怎么开始测试",
}


def scrub_text(value: str) -> str:
    text = value
    for old, new in REPLACE_TERMS.items():
        text = text.replace(old, new)
    return text


def scrub_value(value):
    if isinstance(value, str):
        return scrub_text(value)
    if isinstance(value, list):
        return [scrub_value(item) for item in value]
    if isinstance(value, dict):
        return {key: scrub_value(item) for key, item in value.items()}
    return value


def main() -> int:
    topics = json.loads(TOPICS_PATH.read_text(encoding="utf-8-sig"))
    changed = 0
    untouched: list[str] = []

    for topic in topics:
        slug = topic.get("slug", "")
        for key in DROP_KEYS:
            topic.pop(key, None)

        topic_copy = TOPIC_COPY.get(slug)
        if not topic_copy:
            untouched.append(slug)
            topic.update({key: scrub_value(value) for key, value in topic.items()})
            continue

        topic.update(topic_copy)
        topic.update({key: scrub_value(value) for key, value in topic.items()})
        changed += 1

    TOPICS_PATH.write_text(json.dumps(topics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] refocused {changed} topic records")
    if untouched:
        print("[WARN] no explicit topic copy for: " + ", ".join(untouched))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path


BODY_SECTIONS = [
    "核心判断",
    "关键争议与主线取舍",
    "行业拆解框架",
    "国内市场：需求与品类分层",
    "海外市场：区域分层与竞争机会",
    "结构性机会与受益方向",
    "风险与证伪",
]

APPENDIX_SECTIONS = [
    "Source Register",
    "Key Claim Map",
    "Core Numbers Table",
    "Assumption List",
]

DOMESTIC_DEMAND_GROUPS = {
    "地产": ["地产", "房地产", "房建", "商品房"],
    "基建": ["基建", "基础设施", "水利", "市政"],
    "采矿": ["采矿", "矿山", "资源开发", "煤矿"],
    "更新": ["更新替换", "更新需求", "设备更新", "以旧换新", "存量设备"],
}

PRODUCT_GROUPS = {
    "挖掘机": ["挖掘机", "挖机", "大挖", "中挖", "小挖"],
    "装载机": ["装载机", "电动装载机", "电装"],
    "起重机": ["起重机", "汽车起重机", "塔机", "塔式起重机"],
    "混凝土": ["混凝土", "泵车", "搅拌", "混凝土机械"],
    "高机": ["高机", "高空", "高空作业", "高空作业平台"],
    "矿机": ["矿机", "矿山机械", "宽体车", "矿用"],
}

OVERSEAS_GROUPS = {
    "高端成熟": ["高端成熟", "成熟市场", "高端市场", "欧洲", "北美", "澳洲", "日本"],
    "机会市场": ["机会市场", "中东", "非洲", "拉美"],
    "稳增长市场": ["稳增长", "稳定成长", "印度", "印尼", "东南亚"],
}

COMPANY_NAMES = ["三一", "三一重工", "徐工", "徐工机械", "柳工", "中联重科", "山推"]
BENEFICIARY_TRAITS = ["品类暴露", "区域布局", "海外渠道", "本地化", "后市场", "服务能力", "产品结构", "矿山", "电动化", "渠道"]
COMPARISON_CUES = ["相比", "相较", "不同于", "区别在于", "一方面", "另一方面", "优于", "弱于", "分化", "而不是"]
CONCLUSION_CUES = ["我认为", "核心判断", "本报告判断", "结论是", "最大的变化", "主线是", "不是", "而是"]
VALUATION_TERMS = ["估值", "倍数", "PE", "PB", "EV", "DCF", "目标价", "相对估值"]
RISK_TERMS = ["风险", "证伪", "如果", "若", "一旦", "不成立", "削弱", "下修"]
IMPLICATION_CUES = ["因此", "所以", "意味着", "对应到", "映射到", "更受益", "受益方向", "最受益", "应关注", "对应公司特征", "能力更重要"]
COUNTER_CUES = ["反方", "另一种看法", "替代框架", "悲观", "市场可能会认为", "也可以理解为", "如果只看", "若只看", "另一条逻辑"]
REJECT_CUES = ["但这不足以", "但不足以", "但不能", "并不能", "仍然认为", "最终仍", "因此不采纳", "所以不采纳", "不是主线", "不能推翻"]
LOW_TIER = {"D", "E", "F"}
TIER_SCORE = {"A": 1.0, "B": 0.85, "C": 0.7, "D": 0.45, "E": 0.2, "F": 0.0}
ANALYTIC_NUMERIC_RE = re.compile(
    r"((?:\d+\.\d+|\d+)\s*(?:%|个百分点|倍|x)|"
    r"同比\s*(?:增长|下滑|提升|下降)?\s*(?:\d+\.\d+|\d+)\s*%|"
    r"占比\s*(?:达|超过|提升至|为)?\s*(?:\d+\.\d+|\d+)\s*%|"
    r"市占率\s*(?:达|为)?\s*(?:\d+\.\d+|\d+)\s*%|"
    r"毛利率\s*(?:高于|达|为)?\s*(?:\d+\.\d+|\d+)\s*%?)"
)


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def extract_ids(text: str):
    return re.findall(r"\[(R\d{2,3})\]", text)


def has_citation(text: str) -> bool:
    return bool(extract_ids(text))


def has_analytic_numeric_anchor(text: str) -> bool:
    return bool(ANALYTIC_NUMERIC_RE.search(text))


def extract_section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"(?ms)^###\s+{re.escape(heading)}\s*$\n(.*?)(?=^###\s+|\Z)"
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


def body_text(text: str) -> str:
    m = re.search(r"(?ms)^##\s+正文\s*$\n(.*?)(?=^##\s+审计附录\s*$|\Z)", text)
    return m.group(1).strip() if m else text


def paragraphs(text: str):
    out = []
    for p in re.split(r"\n\s*\n", text):
        p = p.strip()
        if not p:
            continue
        if p.startswith("|"):
            continue
        out.append(p)
    return out


def split_sentences(text: str):
    parts = re.split(r"(?<=[。！？!?\n])", text)
    return [p.strip() for p in parts if p.strip()]


def parse_markdown_table(section_text: str):
    rows = []
    for line in section_text.splitlines():
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) < 2:
            continue
        bare = "".join(parts).replace(" ", "")
        if set(bare) <= {"-", ":"}:
            continue
        rows.append(parts)
    if len(rows) <= 1:
        return []
    return rows[1:]


def source_register(text: str):
    rows = parse_markdown_table(extract_section(text, "Source Register"))
    out = {}
    for row in rows:
        if not row:
            continue
        sid = row[0]
        if not re.fullmatch(r"R\d{2,3}", sid):
            continue
        out[sid] = {
            "sid": sid,
            "title": row[1] if len(row) > 1 else "",
            "source_type": row[2] if len(row) > 2 else "",
            "url": row[3] if len(row) > 3 else "",
            "tier": row[4] if len(row) > 4 else "",
            "source_depth": row[5] if len(row) > 5 else "",
            "used_for": row[6] if len(row) > 6 else "",
        }
    return out


def key_claim_rows(text: str):
    rows = parse_markdown_table(extract_section(text, "Key Claim Map"))
    out = []
    for row in rows:
        claim = row[0] if len(row) > 0 else ""
        kind = row[1] if len(row) > 1 else ""
        supports = row[2] if len(row) > 2 else ""
        out.append({"claim": claim, "kind": kind, "supports": extract_ids(supports)})
    return out


def core_number_rows(text: str):
    rows = parse_markdown_table(extract_section(text, "Core Numbers Table"))
    out = []
    for row in rows:
        out.append({
            "metric": row[0] if len(row) > 0 else "",
            "period": row[1] if len(row) > 1 else "",
            "value": row[2] if len(row) > 2 else "",
            "source": row[3] if len(row) > 3 else "",
        })
    return out


def body_sections_present_ratio(text: str):
    count = sum(1 for name in BODY_SECTIONS if extract_section(text, name))
    return count / len(BODY_SECTIONS)


def appendix_sections_present_ratio(text: str):
    count = sum(1 for name in APPENDIX_SECTIONS if extract_section(text, name))
    return count / len(APPENDIX_SECTIONS)


def core_judgment_present_near_top(text: str):
    sec = extract_section(text, "核心判断")
    paras = paragraphs(sec)
    if not paras:
        return False
    first = paras[0]
    return len(re.sub(r"\s+", "", first)) >= 40 and any(c in first for c in CONCLUSION_CUES)


def priority_variable_count_between_1_and_2(text: str):
    sec = extract_section(text, "核心判断")
    explicit = len(re.findall(r"第[一二两]个结构变量", sec))
    if 1 <= explicit <= 2:
        return True
    count = len(re.findall(r"结构变量", sec))
    return 1 <= count <= 2


def priority_explanation_present(text: str):
    sec = extract_section(text, "核心判断")
    return bool(re.search(r"(更重要|更关键|核心在于|不是.*而是|意味着|决定了|主导)", sec))


def alternative_frame_rejected_present(text: str):
    sec = extract_section(text, "关键争议与主线取舍") or body_text(text)
    if re.search(r"不是.{0,20}而是", sec):
        return True
    has_counter = any(c in sec for c in COUNTER_CUES)
    has_reject = any(c in sec for c in REJECT_CUES)
    return has_counter and has_reject


def keyword_group_count(text: str, groups: dict):
    count = 0
    for keywords in groups.values():
        if any(k in text for k in keywords):
            count += 1
    return count


def domestic_product_differentiation_present(text: str):
    sec = extract_section(text, "国内市场：需求与品类分层")
    positive = bool(re.search(r"(先改善|率先|止跌|转正|修复|受益|增长)", sec))
    weak = bool(re.search(r"(仍弱|偏弱|滞后|承压|拖累|下降|偏慢)", sec))
    return positive and weak


def overseas_region_difference_explained(text: str):
    sec = extract_section(text, "海外市场：区域分层与竞争机会")
    categories = [
        ["空间", "需求"],
        ["增速", "增长"],
        ["竞争", "份额"],
        ["壁垒", "准入", "渠道", "服务"],
    ]
    hit = 0
    for group in categories:
        if any(k in sec for k in group):
            hit += 1
    return hit >= 2


def layered_overseas_logic_present(text: str):
    sec = extract_section(text, "海外市场：区域分层与竞争机会")
    return keyword_group_count(sec, OVERSEAS_GROUPS) >= 2 and len(paragraphs(sec)) >= 3


def comparison_blocks(text: str):
    blocks = []
    for p in paragraphs(body_text(text)):
        if not any(c in p for c in COMPARISON_CUES):
            continue
        entity_hit = 0
        entity_hit += sum(1 for kws in OVERSEAS_GROUPS.values() if any(k in p for k in kws))
        entity_hit += sum(1 for kws in PRODUCT_GROUPS.values() if any(k in p for k in kws))
        entity_hit += sum(1 for name in COMPANY_NAMES if name in p)
        if entity_hit >= 2:
            blocks.append(p)
    return blocks


def comparison_with_numeric_anchor_present(text: str):
    for p in comparison_blocks(text):
        if re.search(r"\d", p):
            return True
    return False


def comparison_relevant_to_mainline(text: str):
    blocks = comparison_blocks(text)
    if not blocks:
        return False
    keywords = ["国内", "海外", "需求", "品类", "区域", "受益", "渠道", "矿山", "电动化"]
    return any(sum(1 for k in keywords if k in p) >= 2 for p in blocks)


def comparison_investment_link_present(text: str):
    sec = body_text(text)
    for p in paragraphs(sec):
        if not any(c in p for c in COMPARISON_CUES):
            continue
        if any(c in p for c in IMPLICATION_CUES):
            return True
    return False


def beneficiary_mapping_present(text: str):
    sec = extract_section(text, "结构性机会与受益方向")
    return bool(re.search(r"(受益方向|更受益|最受益|公司特征|能力更强|受益公司|系统性受益|能力特征|优先受益)", sec))


def beneficiary_mapping_specificity_present(text: str):
    sec = extract_section(text, "结构性机会与受益方向")
    return sum(1 for t in BENEFICIARY_TRAITS if t in sec) >= 1


def beneficiary_mapping_has_reason_chain(text: str):
    sec = extract_section(text, "结构性机会与受益方向")
    return bool(re.search(r"(因为|因此|对应|意味着|所以|传导到|投资意义在于|共同特征是|共同指向)", sec)) and has_citation(sec)


def beneficiary_company_paragraphs(text: str):
    sec = extract_section(text, "结构性机会与受益方向")
    out = []
    for p in paragraphs(sec):
        if any(name in p for name in COMPANY_NAMES):
            out.append(p)
    return out


def beneficiary_company_analytic_numeric_paragraph_count(text: str):
    count = 0
    for p in beneficiary_company_paragraphs(text):
        if has_analytic_numeric_anchor(p) and has_citation(p):
            count += 1
    return count


def beneficiary_company_numeric_analysis_gte_2(text: str):
    return beneficiary_company_analytic_numeric_paragraph_count(text) >= 2


def beneficiary_company_mapping_data_thin_detected(text: str):
    company_paras = beneficiary_company_paragraphs(text)
    return len(company_paras) >= 3 and beneficiary_company_analytic_numeric_paragraph_count(text) < 2


def full_mechanism_chain_present(text: str):
    body = body_text(text)
    for p in paragraphs(body):
        if not has_citation(p):
            continue
        demand = any(k in p for kws in DOMESTIC_DEMAND_GROUPS.values() for k in kws)
        region = any(k in p for kws in OVERSEAS_GROUPS.values() for k in kws)
        product = any(k in p for kws in PRODUCT_GROUPS.values() for k in kws)
        beneficiary = any(k in p for k in BENEFICIARY_TRAITS + ["受益", "盈利", "利润率", "现金流", "份额"])
        causal = bool(re.search(r"(因此|所以|意味着|对应|传导到|从而)", p))
        if (demand or region) and product and beneficiary and causal:
            return True
    return False


def multi_paragraph_deep_dive_present(text: str):
    body = body_text(text)
    paras = paragraphs(body)
    themes = ["挖掘机", "装载机", "矿山", "电动化", "印度", "印尼", "欧洲", "北美", "后市场", "渠道"]
    for i in range(len(paras) - 1):
        p1, p2 = paras[i], paras[i + 1]
        shared = [t for t in themes if t in p1 and t in p2]
        if not shared:
            continue
        joined = p1 + "\n\n" + p2
        if len(re.sub(r"\s+", "", joined)) >= 220 and has_citation(joined):
            return True
    return False


def beneficiary_long_shallow_detected(text: str):
    sec = extract_section(text, "结构性机会与受益方向")
    sec_paras = paragraphs(sec)
    company_paras = beneficiary_company_paragraphs(text)
    return len(sec_paras) >= 5 and len(company_paras) >= 3 and beneficiary_company_analytic_numeric_paragraph_count(text) < 2


def alpha_over_beta_explanation_present(text: str):
    body = body_text(text)
    return bool(re.search(r"(不是所有|并非所有|不是平均受益|行业 beta|行业beta|公司特征|产品结构|渠道能力)", body))


def why_now_explanation_present(text: str):
    body = body_text(text)
    timing = ["为什么是现在", "为什么是当前", "当前时点", "此时", "当下", "现在", "阶段性", "2024", "Q4", "拐点", "筑底", "复苏"]
    causal = ["因为", "意味着", "因此", "所以", "传导", "不是长期而是当前", "交易意义", "验证", "边际变化"]
    for p in paragraphs(body):
        if any(t in p for t in timing) and any(c in p for c in causal):
            return True
    return False


def numeric_and_fact_citation_coverage(text: str):
    body = body_text(text)
    sentences = split_sentences(body)
    target = []
    for s in sentences:
        if re.search(r"\d", s):
            target.append(s)
            continue
        if any(name in s for name in COMPANY_NAMES) and any(k in s for k in ["收入", "增速", "份额", "占比", "销量", "海外"]):
            target.append(s)
    if not target:
        return 1.0
    cited = sum(1 for s in target if has_citation(s))
    return cited / len(target)


def source_quality_score(text: str, register: dict):
    cited_ids = [sid for sid in extract_ids(body_text(text)) if sid in register]
    if not cited_ids:
        return 0.0
    scores = [TIER_SCORE.get(register[sid]["tier"], 0.0) for sid in cited_ids]
    return sum(scores) / len(scores)


def a_thick_source_count(text: str, register: dict):
    cited_ids = {sid for sid in extract_ids(body_text(text)) if sid in register}
    return sum(1 for sid in cited_ids if register[sid]["tier"] == "A" and register[sid]["source_depth"] == "thick")


def counterargument_count_gte_2(text: str):
    sec = extract_section(text, "风险与证伪")
    items = [p for p in paragraphs(sec) if any(k in p for k in ["风险", "反方", "拖累", "削弱", "不利"])]
    return len(items) >= 2


def falsification_condition_count_gte_2(text: str):
    sec = extract_section(text, "风险与证伪")
    count = 0
    for p in paragraphs(sec):
        if re.search(r"(如果|若|一旦|若是)", p) and re.search(r"(则|需要|应当|意味着|下修|重新判断)", p):
            count += 1
    return count >= 2


def counterargument_rejected_with_reason_present(text: str):
    sec = extract_section(text, "关键争议与主线取舍")
    if not sec:
        return False
    paras = paragraphs(sec)
    for p in paras:
        has_counter = any(c in p for c in COUNTER_CUES) or "不是" in p
        has_reject = any(c in p for c in REJECT_CUES) or re.search(r"不是.{0,20}而是", p)
        has_reason = bool(re.search(r"(因为|原因|一方面|另一方面|意味着|传导到|对应到|数字|份额|增速|\d)", p))
        if has_counter and has_reject and has_reason:
            return True
    joined = "\n".join(paras)
    return any(c in joined for c in COUNTER_CUES) and any(c in joined for c in REJECT_CUES) and bool(re.search(r"\d|因为|意味着|传导到|对应到", joined))


def key_claim_low_tier_only_detected(text: str, register: dict):
    for row in key_claim_rows(text):
        ids = [sid for sid in row["supports"] if sid in register]
        if not ids:
            continue
        if all(register[sid]["tier"] in LOW_TIER for sid in ids):
            return True
    return False


def major_numeric_or_valuation_uncited_detected(text: str):
    body = body_text(text)
    sentences = split_sentences(body)
    numeric_target = [s for s in sentences if re.search(r"\d", s)]
    valuation_target = [s for s in sentences if any(t in s for t in VALUATION_TERMS)]
    numeric_uncited = numeric_target and sum(1 for s in numeric_target if has_citation(s)) / len(numeric_target) < 0.6
    valuation_uncited = valuation_target and any(not has_citation(s) for s in valuation_target)
    return bool(numeric_uncited or valuation_uncited)


def company_name_dropping_without_mapping_detected(text: str):
    body = body_text(text)
    company_mentions = sum(body.count(name) for name in COMPANY_NAMES)
    if company_mentions < 3:
        return False
    return not beneficiary_mapping_has_reason_chain(text)


def industry_overview_drift_detected(text: str):
    body = body_text(text)
    para_count = len(paragraphs(body))
    if para_count < 8:
        return False
    return comparison_relevant_to_mainline(text) is False or multi_paragraph_deep_dive_present(text) is False


def citation_register_inconsistency_detected(text: str, register: dict):
    cited = set(extract_ids(text))
    claim_ids = {sid for row in key_claim_rows(text) for sid in row["supports"]}
    missing = [sid for sid in cited.union(claim_ids) if sid not in register]
    return bool(missing)


def evaluate(report_text: str, rubric: dict):
    text = normalize(report_text)
    register = source_register(text)
    metrics = {
        "body_sections_present_ratio": body_sections_present_ratio(text),
        "appendix_sections_present_ratio": appendix_sections_present_ratio(text),
        "reference_id_format_present": bool(re.search(r"\[R\d{2,3}\]", text)),
        "core_judgment_present_near_top": core_judgment_present_near_top(text),
        "priority_variable_count_between_1_and_2": priority_variable_count_between_1_and_2(text),
        "priority_explanation_present": priority_explanation_present(text),
        "alternative_frame_rejected_present": alternative_frame_rejected_present(text),
        "domestic_demand_dimension_count_gte_2": keyword_group_count(extract_section(text, "国内市场：需求与品类分层"), DOMESTIC_DEMAND_GROUPS) >= 2,
        "domestic_product_dimension_count_gte_2": keyword_group_count(extract_section(text, "国内市场：需求与品类分层"), PRODUCT_GROUPS) >= 2,
        "domestic_product_differentiation_present": domestic_product_differentiation_present(text),
        "overseas_region_group_count_gte_2": keyword_group_count(extract_section(text, "海外市场：区域分层与竞争机会"), OVERSEAS_GROUPS) >= 2,
        "overseas_region_difference_explained": overseas_region_difference_explained(text),
        "layered_overseas_logic_present": layered_overseas_logic_present(text),
        "comparison_block_count_gte_2": len(comparison_blocks(text)) >= 2,
        "comparison_with_numeric_anchor_present": comparison_with_numeric_anchor_present(text),
        "comparison_relevant_to_mainline": comparison_relevant_to_mainline(text),
        "comparison_investment_link_present": comparison_investment_link_present(text),
        "beneficiary_mapping_present": beneficiary_mapping_present(text),
        "beneficiary_mapping_specificity_present": beneficiary_mapping_specificity_present(text),
        "beneficiary_mapping_has_reason_chain": beneficiary_mapping_has_reason_chain(text),
        "beneficiary_company_numeric_analysis_gte_2": beneficiary_company_numeric_analysis_gte_2(text),
        "full_mechanism_chain_present": full_mechanism_chain_present(text),
        "multi_paragraph_deep_dive_present": multi_paragraph_deep_dive_present(text),
        "alpha_over_beta_explanation_present": alpha_over_beta_explanation_present(text),
        "why_now_explanation_present": why_now_explanation_present(text),
        "source_register_count_gte_8": len(register) >= 8,
        "key_claim_count_gte_5": len(key_claim_rows(text)) >= 5,
        "core_numbers_count_gte_8": len(core_number_rows(text)) >= 8,
        "numeric_and_fact_citation_coverage": numeric_and_fact_citation_coverage(text),
        "source_quality_score": source_quality_score(text, register),
        "a_thick_source_count": a_thick_source_count(text, register),
        "counterargument_count_gte_2": counterargument_count_gte_2(text),
        "falsification_condition_count_gte_2": falsification_condition_count_gte_2(text),
        "counterargument_rejected_with_reason_present": counterargument_rejected_with_reason_present(text),
        "key_claim_low_tier_only_detected": key_claim_low_tier_only_detected(text, register),
        "major_numeric_or_valuation_uncited_detected": major_numeric_or_valuation_uncited_detected(text),
        "company_name_dropping_without_mapping_detected": company_name_dropping_without_mapping_detected(text),
        "industry_overview_drift_detected": industry_overview_drift_detected(text),
        "beneficiary_company_mapping_data_thin_detected": beneficiary_company_mapping_data_thin_detected(text),
        "beneficiary_long_shallow_detected": beneficiary_long_shallow_detected(text),
        "citation_register_inconsistency_detected": citation_register_inconsistency_detected(text, register),
    }

    criteria = []
    positive_total = 0
    positive_hit = 0
    negative_penalty = 0
    net = 0

    for c in rubric["criteria"]:
        passed = False
        signal = c["runner_signal"]
        value = metrics.get(signal)
        if c["polarity"] == "positive":
            positive_total += c["weight"]
            if signal.endswith("_ratio"):
                passed = value >= 0.999 if "sections_present" in signal else value >= c.get("threshold", 0.75)
            elif signal == "source_quality_score":
                passed = value >= c.get("threshold", 0.65) and metrics["a_thick_source_count"] >= 2
            else:
                passed = bool(value)
            if passed:
                positive_hit += c["weight"]
                net += c["weight"]
        else:
            passed = bool(value)
            if passed:
                negative_penalty += abs(c["weight"])
                net += c["weight"]
        criteria.append({
            "id": c["id"],
            "category": c["category"],
            "polarity": c["polarity"],
            "weight": c["weight"],
            "criterion": c["criterion"],
            "runner_signal": signal,
            "signal_value": value,
            "passed_or_triggered": passed,
        })

    score = round(max(net / positive_total, 0.0), 4) if positive_total else 0.0
    return {
        "score": score,
        "net": net,
        "positive_total": positive_total,
        "positive_hit": positive_hit,
        "negative_penalty": negative_penalty,
        "metrics": metrics,
        "criteria": criteria,
    }


def main():
    if len(sys.argv) != 4:
        print("Usage: construction_machinery_eval_runner_v0_1.py RUBRIC_JSON REPORT_MD OUT_JSON", file=sys.stderr)
        sys.exit(1)
    rubric = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    report = Path(sys.argv[2]).read_text(encoding="utf-8")
    out_path = Path(sys.argv[3])
    result = evaluate(report, rubric)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"score": result["score"], "net": result["net"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

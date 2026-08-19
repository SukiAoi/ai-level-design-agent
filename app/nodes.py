"""Agent 节点实现：每一步都返回 (更新字段, 分步记录)，供可视化展示

每个节点返回 dict，LangGraph 会合并进 State；其中 steps 字段为累积追加。
"""
import re

from .llm import get_llm
from .rag import retrieve_design_sections
from .state import LevelDesignState

# ---------- 节点 Prompt（面向面试官可讲清"为什么"） ----------

READ_DOC_PROMPT = (
    "你是 OnlyUp! 游戏设计文档检索助手。\n"
    "任务：从设计文档中提取与关卡描述相关的章节片段，供后续分析使用。\n"
    "只返回文档原文摘录，不要评价。"
)

ANALYZE_DIFFICULTY_PROMPT = (
    "你是资深 3D 平台跳跃游戏关卡设计师。\n"
    "任务：基于 OnlyUp! 设计文档，分析给定关卡描述的【难度曲线】。\n"
    "请结合设计文档中的攀爬系统参数（跳跃高度、坠落速度、体力消耗、状态机过渡等），\n"
    "按以下结构输出分析：\n"
    "  1) 挑战点拆解：列出关卡中的关键挑战点，每个挑战点说明它依赖哪个游戏机制；\n"
    "  2) 难度评估：给每个挑战点打难度分（1-5），说明理由（引用参数，如跳跃高度/平台间距/坠落惩罚）；\n"
    "  3) 难度曲线：描述整体难度走向（如陡升/平滑/断崖式），点出可能的挫败感峰值；\n"
    "  4) 一句话总结：该关卡的难度定位。\n"
    "请用中文，分点输出。"
)

SUGGEST_PROMPT = (
    "你是资深 3D 平台跳跃游戏关卡设计师。\n"
    "任务：基于难度曲线分析，给出可落地的【改关建议】。\n"
    "要求：\n"
    "  - 每条建议必须给出具体参数（如平台间距、检查点位置、体力补给、坠落惩罚回调）；\n"
    "  - 说明建议对难度曲线的影响（提升/降低/平滑哪一段）；\n"
    "  - 控制在 3-5 条，按优先级排序。\n"
    "请用中文，分点输出。"
)

SELF_CHECK_PROMPT = (
    "你是关卡设计质量评审专家。\n"
    "任务：对上面的【改关建议】做合理性【自检】。\n"
    "要求：\n"
    "  - 检查建议是否与设计文档的机制参数冲突（如建议的平台间距与跳跃高度是否匹配）；\n"
    "  - 指出建议可能引入的新问题（如难度失衡、挫败感、节奏拖沓）；\n"
    "  - 给出修正意见；\n"
    "  - 最终结论：建议整体是否可行（可行 / 需修正）。\n"
    "请用中文，分点输出。\n"
    "最后必须单独输出一行，二选一：\n"
    "【结论】可行\n"
    "【结论】需修正"
)

REPORT_PROMPT = (
    "你是 AI 关卡设计 Agent 的输出汇总员。\n"
    "任务：把分析、建议、自检汇总成一份【最终关卡设计报告】。\n"
    "报告结构：\n"
    "  # 关卡设计报告\n"
    "  ## 1. 关卡概述（复述原始关卡描述）\n"
    "  ## 2. 难度曲线分析（要点摘要）\n"
    "  ## 3. 改关建议（要点摘要）\n"
    "  ## 4. 自检结论（要点摘要）\n"
    "  ## 5. 下一步（给开发者的一句话行动建议）\n"
    "请用中文，Markdown 格式输出。"
)


def _record(node: str, output_key: str, summary: str) -> dict:
    """构造分步记录"""
    return {"node": node, "output_key": output_key, "summary": summary}


# ---------- 节点 1：读设计文档 ----------

def read_design_doc(state: LevelDesignState) -> dict:
    """根据关卡描述关键词，从设计文档检索相关片段"""
    desc = state["level_description"]
    sections = retrieve_design_sections(desc)
    return {
        "design_doc": sections,
        "steps": [
            _record(
                "read_design_doc", "design_doc",
                f"检索到 {len(sections.splitlines())} 行相关设计文档片段",
            )
        ],
    }


# ---------- 节点 2：分析难度曲线 ----------

def analyze_difficulty(state: LevelDesignState) -> dict:
    """基于关卡描述 + 设计文档，用 LLM 分析难度曲线"""
    llm = get_llm()
    prompt = (
        f"{ANALYZE_DIFFICULTY_PROMPT}\n\n"
        f"【关卡描述】\n{state['level_description']}\n\n"
        f"【设计文档相关片段】\n{state['design_doc']}"
    )
    analysis = llm.invoke(prompt).content
    return {
        "difficulty_analysis": analysis,
        "steps": [_record("analyze_difficulty", "difficulty_analysis", "LLM 完成难度曲线分析")],
    }


# ---------- 节点 3：生成改关建议 ----------

def generate_suggestions(state: LevelDesignState) -> dict:
    llm = get_llm()
    prompt = (
        f"{SUGGEST_PROMPT}\n\n"
        f"【关卡描述】\n{state['level_description']}\n\n"
        f"【难度曲线分析】\n{state['difficulty_analysis']}"
    )
    # 回炉场景：带上上一轮自检意见，要求逐条修正后重新输出
    prev_check = state.get("self_check", "")
    is_retry = state.get("retry_count", 0) > 0
    if is_retry and prev_check:
        prompt += (
            "\n\n【上一轮自检意见】（必须逐条回应，修正后重新输出完整建议）\n"
            f"{prev_check}"
        )
    suggestions = llm.invoke(prompt).content
    summary = "LLM 生成改关建议" + ("（按自检意见回炉修正）" if is_retry else "")
    return {
        "suggestions": suggestions,
        "steps": [_record("generate_suggestions", "suggestions", summary)],
    }


# ---------- 节点 4：自检合理性 ----------

def _parse_verdict(text: str) -> bool:
    """从自检文本解析最终判定

    优先解析明确的结论行「【结论】可行/需修正/不可行/不通过」；
    无结论行时回退全文：含「需修正/不可行/不通过」→ 需修正(False)，否则视为可行(True)。
    解析失败时默认通过，避免判定异常导致流程卡死。
    """
    m = re.search(r"【结论】\s*(可行|需修正|不可行|不通过)", text)
    if m:
        return m.group(1) == "可行"
    return not bool(re.search(r"需修正|不可行|不通过", text))


def self_check(state: LevelDesignState) -> dict:
    llm = get_llm()
    prompt = (
        f"{SELF_CHECK_PROMPT}\n\n"
        f"【关卡描述】\n{state['level_description']}\n\n"
        f"【设计文档相关片段】\n{state['design_doc']}\n\n"
        f"【改关建议】\n{state['suggestions']}"
    )
    # 回炉后的再次自检：聚焦"上一轮核心冲突是否已解决"，避免无限评审
    if state.get("retry_count", 0) > 0:
        prompt += (
            "\n\n（注意：本建议已按你上一轮的自检意见修正过。本次自检请聚焦评估："
            "上一轮指出的核心冲突是否已解决？\n"
            "  - 若核心冲突已解决：结论必须写【结论】可行（可保留少量非阻塞优化建议，"
            "但结论行不得写「需修正」）；\n"
            "  - 若核心冲突仍未解决：结论写【结论】需修正。）"
        )
    check = llm.invoke(prompt).content
    passed = _parse_verdict(check)
    retry_count = state.get("retry_count", 0) + 1
    verdict = "✅ 可行" if passed else "🔄 需修正"
    return {
        "self_check": check,
        "self_check_passed": passed,
        "retry_count": retry_count,
        "steps": [
            _record("self_check", "self_check", f"LLM 完成建议合理性自检，判定：{verdict}")
        ],
    }


# ---------- 节点 5：输出报告 ----------

def write_report(state: LevelDesignState) -> dict:
    llm = get_llm()
    prompt = (
        f"{REPORT_PROMPT}\n\n"
        f"【关卡描述】\n{state['level_description']}\n\n"
        f"【难度曲线分析】\n{state['difficulty_analysis']}\n\n"
        f"【改关建议】\n{state['suggestions']}\n\n"
        f"【自检结论】\n{state['self_check']}"
    )
    report = llm.invoke(prompt).content
    return {
        "final_report": report,
        "steps": [_record("write_report", "final_report", "LLM 汇总输出最终报告")],
    }

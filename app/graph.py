"""LangGraph StateGraph 编排（线性链 + 自检条件分支）

流程：
    START
      ↓
    read_design_doc   读设计文档（关键词检索相关章节）
      ↓
    analyze_difficulty  分析难度曲线（LLM）
      ↓
    generate_suggestions 生成改关建议（LLM）
      ↓
    self_check         建议合理性自检（LLM，输出【结论】可行/需修正）
      ↓  ┌─ 不通过且未超限 → 回到 generate_suggestions（带自检意见回炉修正）
      ↓  └─ 通过 / 超限 → write_report
    write_report       汇总输出报告（LLM）
      ↓
    END
"""
from langgraph.graph import END, START, StateGraph

from .nodes import (
    analyze_difficulty,
    generate_suggestions,
    read_design_doc,
    self_check,
    write_report,
)
from .state import LevelDesignState

# 自检不通过时，最多回炉重做次数（防死循环）
MAX_RETRIES = 2


def _route_after_self_check(state: LevelDesignState) -> str:
    """自检后的条件路由：
    - 不通过 且 未超过回炉上限 → "regenerate"（回炉重生成建议）
    - 通过 或 已超限 → "report"（输出报告）
    """
    if not state.get("self_check_passed", True) and state.get("retry_count", 0) < MAX_RETRIES:
        return "regenerate"
    return "report"


def build_graph():
    """构建并编译 StateGraph"""
    graph = StateGraph(LevelDesignState)

    # 注册节点
    graph.add_node("read_design_doc", read_design_doc)
    graph.add_node("analyze_difficulty", analyze_difficulty)
    graph.add_node("generate_suggestions", generate_suggestions)
    graph.add_node("self_check", self_check)
    graph.add_node("write_report", write_report)

    # 定义边：主线线性链
    graph.add_edge(START, "read_design_doc")
    graph.add_edge("read_design_doc", "analyze_difficulty")
    graph.add_edge("analyze_difficulty", "generate_suggestions")
    graph.add_edge("generate_suggestions", "self_check")

    # 条件分支：自检不通过 → 回炉重生成建议（携带自检意见）；通过 → 输出报告
    graph.add_conditional_edges(
        "self_check",
        _route_after_self_check,
        {"regenerate": "generate_suggestions", "report": "write_report"},
    )

    graph.add_edge("write_report", END)

    return graph.compile()


# 模块级单例（供 Streamlit / demo 复用）
app = build_graph()

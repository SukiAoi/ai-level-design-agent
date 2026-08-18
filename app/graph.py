"""LangGraph StateGraph 骨架编排

流程（线性链，先跑通一条链）：
    START
      ↓
    read_design_doc   读设计文档（关键词检索相关章节）
      ↓
    analyze_difficulty  分析难度曲线（LLM）
      ↓
    generate_suggestions 生成改关建议（LLM）
      ↓
    self_check         建议合理性自检（LLM）
      ↓
    write_report       汇总输出报告（LLM）
      ↓
    END

以后可在任意两个节点间插入条件分支（conditional_edges），
例如 self_check 不通过时回到 generate_suggestions 重做——当前先保持线性。
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


def build_graph():
    """构建并编译 StateGraph"""
    graph = StateGraph(LevelDesignState)

    # 注册节点
    graph.add_node("read_design_doc", read_design_doc)
    graph.add_node("analyze_difficulty", analyze_difficulty)
    graph.add_node("generate_suggestions", generate_suggestions)
    graph.add_node("self_check", self_check)
    graph.add_node("write_report", write_report)

    # 定义边：线性链
    graph.add_edge(START, "read_design_doc")
    graph.add_edge("read_design_doc", "analyze_difficulty")
    graph.add_edge("analyze_difficulty", "generate_suggestions")
    graph.add_edge("generate_suggestions", "self_check")
    graph.add_edge("self_check", "write_report")
    graph.add_edge("write_report", END)

    return graph.compile()


# 模块级单例（供 Streamlit / demo 复用）
app = build_graph()

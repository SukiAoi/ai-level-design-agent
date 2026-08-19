"""LangGraph State 定义：AI 关卡设计 Agent 的完整流程状态

流程链：
    输入关卡描述 → 读设计文档 → 分析难度曲线 → 生成改关建议 → 自检
        → （不通过则回炉重生成建议，最多 MAX_RETRIES 次）→ 输出报告
"""
from typing import Annotated, TypedDict


def _append_step(current: list[dict] | None, new: list[dict]) -> list[dict]:
    """steps 字段的累积归约器：每次节点返回的 step 追加到列表尾部"""
    return (current or []) + new


class LevelDesignState(TypedDict, total=False):
    # 输入
    level_description: str                 # 用户输入的关卡描述

    # 中间产物（每一步节点的输出）
    design_doc: str                        # 读设计文档节点：检索到的相关文档片段
    difficulty_analysis: str               # 分析难度曲线节点：难度分析
    suggestions: str                       # 生成建议节点：改关建议
    self_check: str                        # 自检节点：合理性检查结论（含最终判定行）
    final_report: str                      # 输出报告节点：最终报告

    # 自检控制（条件分支用）
    self_check_passed: bool                # 自检是否通过（决定是否回炉重做建议）
    retry_count: int                       # 已回炉次数（self_check 每执行一次 +1，防死循环）

    # 分步记录（供 Streamlit / demo 可视化，展示 Agent 每一步在做什么、为什么）
    steps: Annotated[list[dict], _append_step]

"""Streamlit 可视化入口：展示 Agent 分步推理过程 + LangGraph 图

启动：  streamlit run app/ui.py
"""
import sys
from pathlib import Path

# 确保项目根目录在 sys.path（无论从哪个目录启动 streamlit）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from app.graph import MAX_RETRIES, app
from app.state import LevelDesignState

st.set_page_config(page_title="AI 关卡设计 Agent", page_icon="🎮", layout="wide")

# ---------- 头部 ----------
st.title("🎮 AI 关卡设计 Agent")
st.caption("LangGraph StateGraph 多步推理 · DeepSeek · 读设计文档 → 分析难度 → 建议 → 自检 → 报告")

with st.expander("📐 LangGraph 流程图（Mermaid）", expanded=True):
    st.code(app.get_graph().draw_mermaid(), language="mermaid")
    st.caption(
        "完整流程：线性链 + 自检条件分支。"
        "self_check 判定「需修正」时，携带自检意见回到 generate_suggestions 回炉重做，"
        "最多回炉 2 次；通过或超限后进入 write_report。"
        "右侧「本轮执行路径」会高亮本次实际走过的节点。"
    )

# ---------- 输入 ----------
level = st.text_area(
    "关卡描述",
    value=(
        "第二关：废弃工厂。开局是一段垂直墙面攀爬（约 20m），"
        "中段是移动平台+间隔跳跃（平台间距约 3m），"
        "末尾是一段需要精准跳跃越过间隙的绳索横渡，之后到达检查点。"
    ),
    height=120,
    help="描述你想分析的关卡：地形、平台间距、跳跃、坠落惩罚、检查点等。",
)

if st.button("🚀 运行 Agent", type="primary"):
    if not level.strip():
        st.warning("请先输入关卡描述")
    else:
        with st.spinner("Agent 正在分步推理..."):
            result: dict = app.invoke(
                {"level_description": level}  # type: ignore[arg-type]
            )

        node_icons = {
            "read_design_doc": "📖",
            "analyze_difficulty": "📊",
            "generate_suggestions": "🛠️",
            "self_check": "🔍",
            "write_report": "📄",
        }
        steps = result["steps"]

        # ---------- 本轮执行路径 ----------
        st.subheader("🛤️ 本轮执行路径")
        path_display = "  →  ".join(
            f"{node_icons.get(s['node'], '➡️')} {s['node']}" for s in steps
        )
        st.markdown(f"**{path_display}**")

        # ---------- 自检结论徽章 ----------
        retry_count = int(result.get("retry_count", 0) or 0)
        passed = bool(result.get("self_check_passed", True))
        if passed:
            if retry_count <= 1:
                st.success(f"✅ 自检判定：**建议整体可行**（自检 {retry_count} 次，无需回炉）")
            else:
                st.success(
                    f"✅ 自检判定：**修正后可行**（共自检 {retry_count} 次，"
                    f"回炉修正 {retry_count - 1} 次后通过）"
                )
        else:
            st.warning(
                f"⚠️ 自检判定：**仍为需修正**，已达回炉上限（{MAX_RETRIES} 次），"
                "按当前版本建议输出报告"
            )

        # ---------- 分步可视化 ----------
        st.subheader("🪜 分步推理过程")
        for i, step in enumerate(steps, 1):
            icon = node_icons.get(step["node"], "➡️")
            with st.status(f"{icon} 步骤 {i}：{step['node']} — {step['summary']}", expanded=False):
                st.write(step["summary"])

        # ---------- 中间产物 ----------
        st.subheader("🧩 各节点产物")
        tabs = st.tabs(["📊 难度分析", "🛠️ 改关建议", "🔍 自检", "📄 最终报告"])
        with tabs[0]:
            st.markdown(result.get("difficulty_analysis", "（无）"))
        with tabs[1]:
            st.markdown(result.get("suggestions", "（无）"))
        with tabs[2]:
            st.markdown(result.get("self_check", "（无）"))
        with tabs[3]:
            st.markdown(result.get("final_report", "（无）"))

        # ---------- 设计文档引用 ----------
        with st.expander("📚 读到的设计文档片段"):
            st.text(result.get("design_doc", "（无）"))

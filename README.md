# AI 关卡设计 Agent 🧠

基于 **LangGraph（StateGraph）+ DeepSeek** 的多步推理 Agent：输入关卡描述，Agent 分步完成「读设计文档 → 分析难度曲线 → 生成改关建议 → 自检合理性 → 输出报告」，全程可视化。

A multi-step reasoning agent built with **LangGraph (StateGraph) + DeepSeek**: given a level description, it walks through *read design doc → analyze difficulty curve → suggest changes → self-check → output report*, with full step-by-step visualization.

## 特性 / Features

- 🧠 **LangGraph StateGraph 编排**：5 个节点组成线性链，每步状态可在图中查看
- 📖 **读设计文档**：轻量关键词检索，按章节切块打分（无外部向量库，原理可讲清）
- 📊 **难度曲线分析**：结合 GDD 参数（跳跃高度 / 坠落速度 / 体力 / 状态机）拆解挑战点、打分、描绘难度走向
- 🛠️ **改关建议**：每条建议带具体参数（平台间距 / 检查点 / 体力补给），说明对难度曲线的影响
- 🔍 **自检合理性**：检查建议与机制参数是否冲突，给出修正意见
- 📄 **最终报告**：Markdown 汇总输出
- 🖥️ **Streamlit 可视化**：逐步展示 Agent 在做什么、为什么（验收标准 ✓）

## 流程 / Pipeline

```mermaid
graph TD
    A[输入关卡描述] --> B[read_design_doc 读设计文档]
    B --> C[analyze_difficulty 分析难度曲线]
    C --> D[generate_suggestions 生成改关建议]
    D --> E[self_check 自检合理性]
    E --> F[write_report 输出报告]
    F --> G[最终报告]
```

## 目录结构 / Structure

```
ai-level-design-agent/
├── app/
│   ├── graph.py      # StateGraph 骨架编排（节点 + 边）
│   ├── nodes.py      # 5 个节点实现（含 Prompt 设计）
│   ├── state.py      # State 定义（流程状态 + 分步记录）
│   ├── rag.py        # 轻量设计文档检索（章节分块 + 关键词打分）
│   ├── llm.py        # DeepSeek LLM 封装（OpenAI 兼容协议）
│   ├── config.py     # 配置（API Key、路径、检索参数）
│   └── ui.py         # Streamlit 可视化入口
├── data/
│   └── onlyup_design.txt   # OnlyUp! 游戏设计文档（Agent 知识源）
├── demo.py           # 命令行演示（跑通一条链）
├── requirements.txt
├── .env.example      # 环境变量模板
└── .streamlit/       # Streamlit 主题配置
```

## 快速开始 / Quick Start

```bash
# 1. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key
copy .env.example .env        # 填入 DEEPSEEK_API_KEY

# 4. 命令行跑通一条链
python demo.py

# 5. Streamlit 可视化（能看到分步推理过程）
streamlit run app/ui.py
```

## 效果示例 / Demo

命令行输出会依次展示：关卡描述 → 分步推理过程（每步节点名 + 摘要）→ 难度曲线分析 → 改关建议 → 自检结论 → 最终报告。

Streamlit 界面展示：
1. 📐 **LangGraph 流程图**（Mermaid，`app.get_graph().draw_mermaid()`）
2. 🪜 **分步推理过程**（每个节点一个状态卡片）
3. 🧩 **各节点产物**（Tab 切换查看分析 / 建议 / 自检 / 报告）

## 验收标准 / Acceptance Criteria

- [x] 能看到 Agent 的分步推理过程（LangGraph 可视化 + Streamlit 步骤卡片）
- [x] 输出建议合理（结合 GDD 参数，可落地）
- [x] 能讲清楚每一步为什么（每步节点名、输入输出、Prompt 设计均可解释）

## Roadmap / 计划

- [x] StateGraph 骨架 + 读设计文档节点 + 分析难度曲线节点 —— **一条链跑通** ✅
- [x] 生成建议 / 自检 / 输出报告节点
- [ ] self_check 不通过时条件分支（conditional_edges）回炉重做
- [ ] 接入 ChromaDB 向量检索（替代轻量关键词检索）
- [ ] 更多游戏设计文档入库

## 说明 / Notes

- DeepSeek 通过 OpenAI 兼容协议接入（`langchain-openai`）。
- 检索为轻量关键词打分，启动阶段刻意不引入向量库；详见 `app/rag.py`。
- 踩坑记录见 [PITFALLS.md](PITFALLS.md)。

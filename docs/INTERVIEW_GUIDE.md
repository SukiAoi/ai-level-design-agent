# 🎯 AI 关卡设计 Agent — 面试指南（INTERVIEW GUIDE）

> 本文档用于：面试前复习项目架构、梳理知识点、准备高频问题。
> 目标：让你能**讲清楚项目**，并且**经得起追问**。

---

## 一、架构总览

```
输入：关卡描述（level_description）
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│           LangGraph StateGraph（编译后的可执行图）        │
│                                                         │
│   read_design_doc ─► analyze_difficulty ─►              │
│   generate_suggestions ─► self_check ─► write_report    │
│                                                         │
│   （线性链，每步是独立节点，State 在节点间流转）          │
└─────────────────────────────────────────────────────────┘
         │
         ▼
输出：final_report（Markdown 报告）
```

**一句话定位**：这是一个 **Workflow（多步骤工作流）型 Agent**，不是 ReAct 循环型 Agent——执行路径固定、可预测，每一步可观测、可解释。

### 五个节点职责表

| 节点 | 类型 | 职责 | 是否调 LLM |
|------|------|------|-----------|
| `read_design_doc` | 检索 | 按关键词从设计文档取相关章节 | ❌（纯 Python） |
| `analyze_difficulty` | 推理 | 拆解挑战点 + 打分 + 描绘难度曲线 | ✅ |
| `generate_suggestions` | 推理 | 给出带参数的改关建议 | ✅ |
| `self_check` | 推理 | 检查建议与机制参数是否冲突，给修正 | ✅ |
| `write_report` | 推理 | 汇总成 Markdown 最终报告 | ✅ |

### 对应代码文件

```
app/graph.py      StateGraph 骨架编排（节点 + 边 + compile）
app/nodes.py      5 个节点实现（含每节点的 Prompt 设计）
app/state.py      State 定义（流程状态 + steps 分步记录）
app/rag.py        轻量关键词检索（章节分块 + 打分）
app/llm.py        DeepSeek LLM 封装（OpenAI 兼容协议）
app/config.py     配置（API Key / 路径 / 检索参数）
app/ui.py         Streamlit 可视化入口
demo.py           命令行跑通一条链
```

---

## 二、核心设计要点（面试要能讲出来）

### 1. State 驱动 —— 状态"单例流动"，节点是"纯函数"

```python
class LevelDesignState(TypedDict, total=False):
    level_description: str          # 输入
    design_doc: str                 # 检索结果
    difficulty_analysis: str        # 分析
    suggestions: str                # 建议
    self_check: str                 # 自检
    final_report: str               # 报告
    steps: Annotated[list[dict], _append_step]   # ← 关键设计
```

每个节点是"输入 State → 输出部分字段"的纯函数，LangGraph 自动把返回值**合并**进 State，下一个节点读取。输入输出清晰、可测、可替换。

### 2. `Annotated[list, reducer]` —— 归约器（高频考点）

```python
def _append_step(current: list[dict] | None, new: list[dict]) -> list[dict]:
    return (current or []) + new
```

- LangGraph 的 State 默认是**覆盖语义**：节点返回什么就替换什么。
- `steps` 要累积，普通 list 会被覆盖只剩最后一步。
- 用 reducer 后每次返回**追加**，最终拿到完整分步记录（用于可视化）。
- 与 Chatbot 里消息列表累积（`operator.add`）是同一机制。

### 3. 白盒可观测性

- 每节点返回 `steps` 记录 `{node, output_key, summary}`。
- Streamlit 把每步渲染成状态卡片 + Mermaid 流程图。
- 能看到 Agent "卡在哪一步、每一步输出了什么"——这是工程化 Agent 与"一把梭调 API"的本质区别。

### 4. 关注点分离（单一职责）

检索 / 分析 / 建议 / 自检 / 报告各自独立成节点 + 独立 Prompt：
- 每步可单独测试、单独替换
- 一个环节升级（检索换向量库）不影响其他环节

### 5. 刻意用"轻量检索"而非向量库（有意识的技术选型）

- 设计文档只有 ~5KB，关键词检索足够。
- 不引入 ChromaDB/Embedding 复杂度，跑通快、原理透明。
- 检索封装在 `rag.py` 一个模块，后续换向量库只改一个模块。
- Roadmap 已规划升级为 ChromaDB 向量检索。

### 6. 每节点独立 Prompt 工程

- 分析难度节点：要求"引用 GDD 参数（跳跃高度/坠落速度/体力）打分"。
- 自检节点：要求"检查与机制参数冲突，给修正意见"。
- 提示词本身就是面试素材，体现 Prompt 工程能力。

---

## 三、知识点清单（简历/面试关键词）

### 框架层
- **LangGraph**：`StateGraph`、节点、边、`START`/`END`、`compile()`
- **State 机制**：TypedDict、`Annotated` + 归约器（reducer）、状态合并语义
- **图可视化**：`app.get_graph().draw_mermaid()`
- **Workflow vs Agent**：固定流程 vs ReAct 工具循环

### LLM / Prompt 层
- **OpenAI 兼容协议**：DeepSeek 通过 `ChatOpenAI` 接入
- **Prompt Engineering**：系统提示词、角色设定、结构化输出、few-shot 思路
- **温度参数**：`temperature=0.3`（任务偏确定性）
- **多步推理 vs 单次调用**：拆步骤，每步聚焦，质量更可控

### 检索层（与 RAG 项目呼应）
- 分块（chunking）、关键词检索、Top-K
- 进阶：BM25 + 向量 + RRF 融合 + LLM ReRank（RAG Agent 已实现）

### 工程层
- 包结构、`dotenv` 配置管理、`sys.path` 处理
- Streamlit 可视化、Mermaid
- 可观测性设计（步骤记录）

---

## 四、面试高频问题 + 参考回答

### Q1：为什么用 LangGraph 而不是直接按顺序调 5 次 LLM？
> ① **状态管理**：LangGraph 统一管理中间结果流转，不用手动传参；② **可观测**：图结构 + Mermaid 可视化，方便调试演示；③ **可扩展**：加条件分支、加节点、加并行只需改图定义；④ **工程规范**：企业级 Agent 编排的行业做法。

### Q2：Workflow 和 ReAct Agent 的区别？为什么这个项目选 Workflow？
> ReAct 是"Agent 自己决定下一步调哪个工具"，灵活但不可控、token 高；Workflow 是固定流程，**可预测、可控、每步可解释**。本项目"关卡设计分析"步骤明确，适合 Workflow。若是"用户随机提问、Agent 自己判断要不要查文档"，则适合 ReAct（RAG Agent 用的就是 `create_agent` 工具调用）。**两种模式都有实践，能按场景选型**。

### Q3：`Annotated[list, reducer]` 是干嘛的？LangGraph 状态更新机制？
> 默认节点返回的 State 字段是"覆盖"。`steps` 要累积，需用 reducer（自定义 `_append_step` 或 `operator.add`）实现**追加**。这是 LangGraph 处理列表类状态的标准做法。

### Q4：怎么保证输出质量？会不会胡说？
> 三层：① **检索给事实依据**——分析必须基于设计文档片段；② **Prompt 约束**——要求引用参数、分点输出；③ **自检节点**——检查建议与机制参数冲突，主动修正。实测 Agent 自己否决了"二段跳"方案（与 FSM 状态机冲突）。

### Q5：为什么用关键词检索不用向量库？
> 文档小 + 启动阶段求快，关键词检索足够且原理透明。检索封装在 `rag.py` 单模块，预留替换点。另一个 RAG 项目已实现 BM25+向量+RRF+ReRank 混合检索。

### Q6：如果自检不通过怎么办？现在只是"输出结论"吧？
> 目前是线性链，自检结论只记录在报告。Roadmap 规划用 `conditional_edges` 判断自检结果，不通过就回 `generate_suggestions` **回炉重做**（最多 N 次），形成反思循环。可主动讲这个演进方向。

### Q7：Agent 怎么调试？出问题怎么定位？
> 靠 `steps` 分步记录 + 图可视化，卡在哪步一目了然；每个节点是独立函数，可单独写单测喂假数据。可观测性设计是工程化核心。

### Q8：多步推理的代价？延迟和成本？
> 5 次 LLM 串行，完整推理约 1 分钟，成本约为单次 5 倍。**权衡**：换每步质量可控、可解释。优化：① 可并行节点并行化；② 流式输出（`stream_mode`）；③ 简单关卡走"快速通道"少调几步。

### Q9：这个项目最大的亮点？
> ① 完整多步推理 Agent，非 demo 级；② **自检机制**有自我修正能力（实测主动否决冲突方案）；③ 全程可视化可解释；④ 与 RAG 项目互补，覆盖 **Workflow + ReAct 两种范式**。

### Q10：有哪些不足？怎么改进？
> ① 检索关键词级，可升级混合检索；② 自检不驱动流程（可加条件分支回炉）；③ Prompt 可配置化 + few-shot；④ 可加评估集量化改进。**主动讲不足 + 方案是加分项。**

---

## 五、30 秒「讲项目」话术

> "我做了两个 Agent 项目。**RAG Agent** 是 ReAct 范式——LLM 自己决定调工具（查文档/算数学），用了 BM25+向量+RRF+ReRank 混合检索。**AI 关卡设计 Agent** 是 Workflow 范式——用 LangGraph StateGraph 把'读文档→分析难度→给建议→自检→出报告'编排成 5 个可观测节点，每个节点单一职责、独立 Prompt，自检节点能主动发现并修正与游戏机制冲突的建议，Streamlit 全程可视化。两个项目让我对 Agent 的两种编排范式都有实践，也知道怎么选型。"

---

## 六、追问应对（纵深问题）

准备方向：
1. **手写核心概念**：能写 `StateGraph` 最小示例、reducer 写法、`conditional_edges` 分支。
2. **数据流细节**：State 合并语义、节点返回结构、`steps` 如何累积。
3. **工程边界**：如何测单个节点、如何 mock LLM、如何加并行、如何做流式。
4. **对比延伸**：LangGraph vs LangChain Agent vs 自己手写循环；RAG 混合检索细节。

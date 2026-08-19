# PITFALLS · 踩坑记录

> 记录开发过程中踩过的坑与结论，方便自己复盘、也方便面试时讲「我踩过什么坑、怎么解决的」。

## 1. Streamlit 里展示 LangGraph Mermaid 图
- **现象**：想用 `pygraphviz` 渲染 PNG 失败。
- **原因**：`draw_mermaid_png()` 依赖系统级 `graphviz` 二进制，Windows 安装麻烦。
- **解决**：改用 `app.get_graph().draw_mermaid()` 得到 Mermaid 源码，配合较新版 Streamlit 的 `st.code(..., language="mermaid")` 直接渲染；也可粘贴到 <https://mermaid.live> 查看。

## 2. State 里列表字段的累积
- **现象**：每个节点返回 `{"steps": [...]}`，但下一步节点读不到之前的步骤。
- **原因**：LangGraph 的 State 默认是「覆盖」语义，节点返回什么就替换什么。
- **解决**：用 `Annotated[list, reducer]` 声明累积归约器（见 `app/state.py` 的 `_append_step`），节点每次只追加自己那一步。

## 3. DeepSeek 没有 Embedding API
- 与 OnlyUp! RAG Agent 相同：DeepSeek 目前不提供向量化接口。
- 本项目启动阶段用轻量关键词检索绕开该问题；后续接入 ChromaDB 用本地 ONNX 模型向量化。

## 4. 自检「需修正」判定过严 → 条件分支几乎总是回炉
- **现象**：评审 LLM 习惯性输出「修正后可行 / 需修正后实施」，全文正则一匹配「需修正」就判为不通过，导致条件分支几乎每次都回炉，且第二轮也常判「需修正」直到上限。
- **原因**：
  1. 判定用的全文正则太宽松（`需修正` 出现在正文任意处都会命中）；
  2. 评审 prompt 没有「已修正过则放行」的终止条件，LLM 永远能找到新改进点。
- **解决**：
  1. 让 `self_check` 强制输出独立的结论行 `【结论】可行 / 【结论】需修正`，`_parse_verdict` 优先解析结论行，再回退全文匹配；
  2. 回炉后的再次自检在 prompt 中追加终止条件：聚焦「上一轮核心冲突是否已解决」，若已解决必须写 `【结论】可行`；
  3. `MAX_RETRIES = 2` 兜底，防死循环。

## 5. State 新增布尔/计数字段的归约
- **现象**：`self_check_passed` / `retry_count` 想在多次回炉间保留，若用覆盖语义，每轮自检返回新值即可（self_check 每次自增 retry_count），无需自定义 reducer。
- **结论**：只有「累积追加」型字段（如 `steps`）才需要 `Annotated[list, reducer]`；标量判断字段用覆盖语义即可，条件路由读取的是最新一次自检的判定。

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

"""全局配置：路径 / API Key / 模型 / 检索参数"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------- 路径 ----------
# 项目根目录（ai-level-design-agent/）
BASE_DIR = Path(__file__).resolve().parent.parent
# 原始设计文档目录
DATA_DIR = BASE_DIR / "data"
# OnlyUp! 游戏设计文档（Agent 的知识源）
DESIGN_DOC_PATH = DATA_DIR / "onlyup_design.txt"

# ---------- LLM（DeepSeek，OpenAI 兼容协议） ----------
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# ---------- 文档检索参数（轻量关键词检索，无外部向量库） ----------
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "3"))  # 返回给 LLM 的相关片段数

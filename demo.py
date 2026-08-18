"""命令行演示：跑通一条链（AI 关卡设计 Agent）

用法：
    python demo.py
    python demo.py "描述一个关卡..."
"""
import sys
from pathlib import Path

# 确保项目根目录在 sys.path（无论从哪个目录运行）
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.graph import app
from app.state import LevelDesignState

DEFAULT_LEVEL = (
    "第二关：废弃工厂。开局是一段垂直墙面攀爬（约 20m），"
    "中段是移动平台+间隔跳跃（平台间距约 3m），"
    "末尾是一段需要精准跳跃越过间隙的绳索横渡，之后到达检查点。"
)


def run(level_description: str) -> dict:
    """运行 Agent，返回完整 State"""
    state: LevelDesignState = {"level_description": level_description}
    return app.invoke(state)


def main() -> None:
    level = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LEVEL
    print("=" * 60)
    print("🎮 AI 关卡设计 Agent — 多步推理演示")
    print("=" * 60)
    print(f"【关卡描述】\n{level}\n")

    result = run(level)

    print("-" * 60)
    print("🪜 分步推理过程")
    for i, step in enumerate(result["steps"], 1):
        print(f"  [{i}] {step['node']:<20} → {step['summary']}")

    for key, title in [
        ("difficulty_analysis", "📊 难度曲线分析"),
        ("suggestions", "🛠️ 改关建议"),
        ("self_check", "🔍 自检结论"),
        ("final_report", "📄 最终报告"),
    ]:
        print("\n" + "=" * 60)
        print(title)
        print("=" * 60)
        print(result.get(key, "（未生成）"))


if __name__ == "__main__":
    main()

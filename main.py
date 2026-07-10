"""教师个人科研查询器 — 启动入口"""
import uvicorn
from pathlib import Path
import sys

# 确保项目根目录在 Python 路径中
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "agent"))


def main():
    print("=" * 50)
    print("  教师个人科研查询器 v0.2.0")
    print("  http://127.0.0.1:8000/docs  — API 文档")
    print("  http://127.0.0.1:8000/api/teacher/GH20200001/overview")
    print("=" * 50)

    uvicorn.run(
        "data_service.api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,          # 开发模式：代码改动自动重载
        log_level="info",
    )


if __name__ == "__main__":
    main()

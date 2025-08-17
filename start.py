import uvicorn
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("正在启动 Chat Config API 服务...")
    print("=" * 50)
    print("API 文档地址: http://localhost:8000/docs")
    print("ReDoc 文档地址: http://localhost:8000/redoc")
    print("健康检查: http://localhost:8000/health")
    print("=" * 50)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )

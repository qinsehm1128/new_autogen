from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import asyncio

from database import create_tables
from api import api_keys_router, prompts_router, common_router
from api.chat import router as chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):

    await create_tables()

    yield

#
app = FastAPI(
    title="Chat Config API",
    description="聊天配置管理系统API",
    version="1.0.0",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_keys_router)
app.include_router(prompts_router)
app.include_router(common_router)
app.include_router(chat_router)



@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": f"内部服务器错误: {str(exc)}",
            "data": None
        }
    )


# 根路径
@app.get("/")
async def root():
    return {
        "code": 200,
        "message": "Chat Config API 服务运行正常",
        "data": {
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


# 健康检查
@app.get("/health")
async def health_check():
    return {
        "code": 200,
        "message": "服务健康",
        "data": {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }





if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

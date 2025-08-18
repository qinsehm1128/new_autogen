import json
import os
import asyncio
from typing import Any

import aiofiles
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from autogen_ext.models.openai import OpenAIChatCompletionClient

# 创建FastAPI应用实例
app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="."), name="")

# 配置文件路径
state_path = "agent_state.json"

# 全局变量存储活跃连接
active_connections: dict[WebSocket, asyncio.Task] = {}


@app.get("/")
async def root():
    """返回聊天界面HTML文件"""
    return FileResponse("app_agent.html")


async def get_agent() -> AssistantAgent:
    """获取助手代理"""
    api_key = "sk-yLCZLIlIrSK2V06h5502RshRIMyiwgIoSFTWiCtfPC4QpfwR"
    base_url = "https://api.001hao.com/v1"

    openai_model_client = OpenAIChatCompletionClient(
        model="gpt-4",
        api_key=api_key,
        base_url=base_url
    )

    agent = AssistantAgent(
        name="assistant",
        model_client=openai_model_client,
        model_client_stream=True,
        system_message="你是一个有用的AI助手。请用中文回答用户的问题，提供周到和有帮助的回复。",
    )
    
    # 加载状态
    if os.path.exists(state_path):
        try:
            async with aiofiles.open(state_path, "r") as file:
                state = json.loads(await file.read())
            await agent.load_state(state)
        except:
            pass
    
    return agent


async def send_message(websocket: WebSocket, message_type: str, content: str = "", **kwargs):
    """发送消息到WebSocket"""
    try:
        message = {"type": message_type, "content": content, "source": "assistant", **kwargs}
        await websocket.send_text(json.dumps(message))
    except:
        pass  # 连接可能已关闭


async def handle_chat(websocket: WebSocket, user_message: str):
    """处理聊天消息"""
    try:
        agent = await get_agent()
        full_response = ""
        
        # 发送开始信号
        await send_message(websocket, "response_start")
        
        # 流式处理
        async for chunk in agent.run_stream(task=user_message):
            # 检查连接是否还活跃
            if websocket not in active_connections:
                return
            
            # 提取内容
            content = ""
            if hasattr(chunk, 'content'):
                content = chunk.content
            elif hasattr(chunk, 'chat_message') and chunk.chat_message:
                content = getattr(chunk.chat_message, 'content', '')
            
            if content and content.strip():
                await send_message(websocket, "chunk", content)
                full_response += content
        
        # 发送完成信号
        if websocket in active_connections:
            await send_message(websocket, "response_complete", full_response,
                             token_count=len(full_response.split()),
                             character_count=len(full_response))
            
            # 保存状态
            try:
                state = await agent.save_state()
                async with aiofiles.open(state_path, "w") as file:
                    await file.write(json.dumps(state))
            except:
                pass
                
    except asyncio.CancelledError:
        await send_message(websocket, "terminated", "响应生成已被取消。")
    except Exception as e:
        await send_message(websocket, "error", f"错误: {str(e)}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点"""
    await websocket.accept()
    active_connections[websocket] = None
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # 处理终止请求
            if message_data.get("type") == "terminate":
                if websocket in active_connections and active_connections[websocket]:
                    active_connections[websocket].cancel()
                await send_message(websocket, "system", "终止信号已发送。")
                continue
            
            # 取消之前的任务
            if websocket in active_connections and active_connections[websocket]:
                active_connections[websocket].cancel()
            
            # 发送用户消息确认
            user_content = message_data["content"]
            await send_message(websocket, "user_message", user_content, source="user")
            
            # 创建新任务
            task = asyncio.create_task(handle_chat(websocket, user_content))
            active_connections[websocket] = task
            
            # 等待任务完成
            try:
                await task
            except asyncio.CancelledError:
                pass
                
    except WebSocketDisconnect:
        pass
    finally:
        # 清理连接
        if websocket in active_connections:
            if active_connections[websocket]:
                active_connections[websocket].cancel()
            del active_connections[websocket]


@app.post("/terminate")
async def terminate_all_chats():
    """终止所有聊天"""
    for websocket, task in active_connections.items():
        if task:
            task.cancel()
    return {"status": "终止信号已发送给所有活跃连接"}


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动精简版AutoGen WebSocket聊天应用...")
    print("📱 前端界面: http://localhost:8001")
    print("🔌 WebSocket端点: ws://localhost:8001/ws")
    print("⛔ 终止端点: POST http://localhost:8001/terminate")
    print("\n按 Ctrl+C 停止服务器")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
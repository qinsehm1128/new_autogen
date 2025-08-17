import json
import os
from typing import Any, AsyncIterator
import asyncio

import aiofiles
import yaml
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_core.models import ChatCompletionClient
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from autogen_ext.models.openai import OpenAIChatCompletionClient

# 创建FastAPI应用实例
app = FastAPI()

# 添加CORS中间件，允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="."), name="")


@app.get("/")
async def root():
    """返回聊天界面HTML文件"""
    return FileResponse("app_agent.html")

# 配置文件路径
model_config_path = "model_config.yaml"
state_path = "agent_state.json"
history_path = "agent_history.json"


# 简化的WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []  # 活跃的WebSocket连接列表
        self.active_tasks: dict[WebSocket, asyncio.Task] = {}  # 每个连接对应的活跃任务
        self.should_continue: dict[WebSocket, bool] = {}  # 每个连接是否应该继续的标志

    async def connect(self, websocket: WebSocket):
        """接受新的WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.should_continue[websocket] = True

    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接，清理相关资源"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        # 取消该连接的任务
        self.cancel_task(websocket)
        # 清理标志
        if websocket in self.should_continue:
            del self.should_continue[websocket]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """向特定WebSocket连接发送消息"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            # 连接可能已关闭，移除它
            self.disconnect(websocket)

    def set_task(self, websocket: WebSocket, task: asyncio.Task):
        """为特定连接设置活跃任务"""
        self.active_tasks[websocket] = task
        self.should_continue[websocket] = True

    def cancel_task(self, websocket: WebSocket):
        """取消特定连接的任务"""
        # 设置停止标志
        self.should_continue[websocket] = False

        # 取消异步任务
        if websocket in self.active_tasks:
            task = self.active_tasks[websocket]
            if not task.done():
                task.cancel()
            del self.active_tasks[websocket]

    def should_task_continue(self, websocket: WebSocket) -> bool:
        """检查特定连接的任务是否应该继续"""
        return self.should_continue.get(websocket, False)


# 创建全局连接管理器实例
manager = ConnectionManager()


async def get_agent() -> AssistantAgent:
    """获取助手代理，从文件加载状态"""
    # 从配置获取模型客户端
    api_key = "sk-yLCZLIlIrSK2V06h5502RshRIMyiwgIoSFTWiCtfPC4QpfwR"
    base_url = "https://api.001hao.com/v1"

    openai_model_client = OpenAIChatCompletionClient(
        model="gpt-4",
        api_key=api_key,
        base_url=base_url
    )

    # 创建启用流式响应的助手代理
    agent = AssistantAgent(
        name="assistant",
        model_client=openai_model_client,
        model_client_stream=True,  # 启用流式响应
        system_message="你是一个有用的AI助手。请用中文回答用户的问题，提供周到和有帮助的回复。",
    )
    # 从文件加载状态
    if not os.path.exists(state_path):
        return agent  # 如果状态文件不存在，返回新代理
    try:
        async with aiofiles.open(state_path, "r") as file:
            state = json.loads(await file.read())
        await agent.load_state(state)
    except:
        pass  # 忽略状态加载错误
    return agent


async def get_history() -> list[dict[str, Any]]:
    """从文件获取聊天历史"""
    if not os.path.exists(history_path):
        return []
    try:
        async with aiofiles.open(history_path, "r") as file:
            return json.loads(await file.read())
    except:
        return []


async def handle_streaming_response(agent: AssistantAgent, message: str, websocket: WebSocket):
    """处理流式响应，支持适当的取消机制"""
    full_response = ""
    response_started = False

    try:
        # 开始流式生成
        async for chunk in agent.run_stream(task=message):
            # 在每次迭代时检查是否应该继续
            if not manager.should_task_continue(websocket):
                await manager.send_personal_message({
                    "type": "terminated",
                    "content": "响应生成已被终止。",
                    "source": "system"
                }, websocket)
                return ""

            # 调试信息
            # print(f"收到chunk: {chunk}")

            # 处理数据块 - 更宽松的条件检查
            content = None
            if hasattr(chunk, 'content'):
                content = chunk.content
            elif hasattr(chunk, 'chat_message') and chunk.chat_message and hasattr(chunk.chat_message, 'content'):
                content = chunk.chat_message.content

            if content and content.strip():
                if not response_started:
                    # 发送开始信号
                    await manager.send_personal_message({
                        "type": "response_start",
                        "source": "assistant"
                    }, websocket)
                    response_started = True

                # 发送数据块
                await manager.send_personal_message({
                    "type": "chunk",
                    "content": content,
                    "source": "assistant"
                }, websocket)

                full_response += content

            # 小延迟
            await asyncio.sleep(0.1)

            # 再次检查是否应该继续
            if not manager.should_task_continue(websocket):
                await manager.send_personal_message({
                    "type": "terminated",
                    "content": "响应生成已被终止。",
                    "source": "system"
                }, websocket)
                return ""

        # 只有在未取消的情况下才发送完成信号
        if manager.should_task_continue(websocket) and response_started:
            await manager.send_personal_message({
                "type": "response_complete",
                "content": full_response,
                "source": "assistant",
                "token_count": len(full_response.split()),  # 简单的令牌估算
                "character_count": len(full_response)
            }, websocket)

        return full_response

    except asyncio.CancelledError:
        # 任务被取消
        await manager.send_personal_message({
            "type": "terminated",
            "content": "响应生成已被取消。",
            "source": "system"
        }, websocket)
        return ""
    except Exception as e:
        await manager.send_personal_message({
            "type": "error",
            "content": f"流式响应过程中出错: {str(e)}",
            "source": "system"
        }, websocket)
        return ""


@app.get("/history")
async def history() -> list[dict[str, Any]]:
    """获取聊天历史的HTTP端点"""
    try:
        return await get_history()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点，处理实时聊天通信"""
    await manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # 移除WebSocket终止处理，现在使用HTTP API进行终止
            if message_data.get("type") == "terminate":
                # 忽略通过WebSocket发送的终止信号，因为现在使用HTTP API
                continue

            # 从接收到的数据创建文本消息
            user_message = TextMessage(
                content=message_data["content"],
                source=message_data.get("source", "user")
            )

            # 发送用户消息确认
            await manager.send_personal_message({
                "type": "user_message",
                "content": user_message.content,
                "source": user_message.source
            }, websocket)

            # 取消该WebSocket的任何现有任务
            manager.cancel_task(websocket)

            try:
                # 获取代理
                agent = await get_agent()

                # 创建并启动流式任务
                async def streaming_task():
                    try:
                        full_response = await handle_streaming_response(
                            agent, user_message.content, websocket
                        )

                        # 如果未取消，保存代理状态到文件
                        if manager.should_task_continue(websocket):
                            try:
                                state = await agent.save_state()
                                async with aiofiles.open(state_path, "w") as file:
                                    await file.write(json.dumps(state))
                            except:
                                pass  # 忽略保存错误

                        return full_response
                    except asyncio.CancelledError:
                        # 任务被取消，清理
                        await manager.send_personal_message({
                            "type": "terminated",
                            "content": "响应生成已被取消。",
                            "source": "system"
                        }, websocket)
                        raise
                    except Exception as e:
                        await manager.send_personal_message({
                            "type": "error",
                            "content": f"错误: {str(e)}",
                            "source": "system"
                        }, websocket)
                        raise

                # 启动任务
                task = asyncio.create_task(streaming_task())
                manager.set_task(websocket, task)

                # 等待任务完成
                await task

            except asyncio.CancelledError:
                # 任务被取消，这是预期的
                pass
            except Exception as e:
                await manager.send_personal_message({
                    "type": "error",
                    "content": f"意外错误: {str(e)}",
                    "source": "system"
                }, websocket)

    except Exception:
        manager.disconnect(websocket)


@app.post("/terminate")
async def terminate_all_chats():
    """终止所有正在进行的聊天操作的HTTP端点"""
    print(f"🛑 收到HTTP终止请求，当前活跃连接数: {len(manager.active_connections)}")
    print(f"🛑 当前活跃任务数: {len(manager.active_tasks)}")

    # 取消所有活跃任务
    terminated_count = 0
    for websocket in list(manager.active_connections):
        if websocket in manager.active_tasks:
            manager.cancel_task(websocket)
            terminated_count += 1
            print(f"🛑 已终止连接的任务")

    message = f"终止信号已发送给 {terminated_count} 个活跃连接"
    print(f"🛑 {message}")
    return {"status": message}


# 主程序入口
if __name__ == "__main__":
    import uvicorn

    print("🚀 启动AutoGen WebSocket聊天应用...")
    print("📱 前端界面: http://localhost:8001")
    print("🔌 WebSocket端点: ws://localhost:8001/ws")
    print("⛔ 终止端点: POST http://localhost:8001/terminate")
    print("\n功能特性:")
    print("✅ WebSocket实时通信")
    print("✅ 流式响应显示")
    print("✅ 令牌计数统计")
    print("✅ 即时终止控制")
    print("✅ 自动重连机制")
    print("\n按 Ctrl+C 停止服务器")

    uvicorn.run(app, host="0.0.0.0", port=8001)

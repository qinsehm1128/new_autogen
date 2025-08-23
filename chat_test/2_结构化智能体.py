import asyncio
import time
from typing import Literal, Optional, Dict, Any
from datetime import datetime

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import StructuredMessage
from pydantic import BaseModel, ValidationError


class AgentResponse(BaseModel):
    success: Literal["yes", "no"]
    reason: str
    client_id: int


def validate_structured_response(result) -> tuple[bool, Optional[AgentResponse], str]:
    """验证结构化响应的完整性和正确性"""
    try:
        if not result.messages:
            return False, None, "没有返回任何消息"

        last_message = result.messages[-1]

        if not isinstance(last_message, StructuredMessage):
            return False, None, f"不是结构化消息: {type(last_message).__name__}"

        if not isinstance(last_message.content, AgentResponse):
            return False, None, f"内容类型错误: {type(last_message.content).__name__}"

        response_data = last_message.content

        # 验证必需字段
        if response_data.success not in ["yes", "no"]:
            return False, None, f"success字段无效: {response_data.success}"

        if not response_data.reason or not response_data.reason.strip():
            return False, None, "reason字段为空"

        if not isinstance(response_data.client_id, int):
            return False, None, f"client_id类型错误: {type(response_data.client_id)}"

        return True, response_data, "验证成功"

    except ValidationError as e:
        return False, None, f"验证错误: {str(e)}"
    except Exception as e:
        return False, None, f"未知错误: {str(e)}"


async def get_structured_response_with_retry(agent: AssistantAgent, query: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    带重试机制的结构化响应获取

    Returns:
        Dict: 包含所有尝试记录的字典
    """
    session_record = {
        "query": query,
        "start_time": datetime.now().isoformat(),
        "max_retries": max_retries,
        "attempts": [],
        "final_success": False,
        "final_result": None,
        "total_duration": 0
    }

    start_time = time.time()

    for attempt in range(max_retries):
        attempt_record = {
            "attempt_number": attempt + 1,
            "start_time": datetime.now().isoformat(),
            "success": False,
            "error_message": "",
            "response_data": None,
            "duration": 0,
            "timeout": False
        }
        
        attempt_start = time.time()

        try:
            # 设置超时时间（30秒）
            result = await asyncio.wait_for(
                agent.run(task=query),
                timeout=30.0
            )

            # 验证结构化响应
            is_valid, response_data, message = validate_structured_response(result)

            attempt_record["duration"] = time.time() - attempt_start

            if is_valid:
                attempt_record["success"] = True
                attempt_record["response_data"] = {
                    "success": response_data.success,
                    "reason": response_data.reason,
                    "client_id": response_data.client_id
                }
                attempt_record["error_message"] = message

                # 成功获取结构化响应
                session_record["final_success"] = True
                session_record["final_result"] = attempt_record["response_data"]
                session_record["attempts"].append(attempt_record)
                break
            else:
                attempt_record["error_message"] = message

        except asyncio.TimeoutError:
            attempt_record["duration"] = time.time() - attempt_start
            attempt_record["timeout"] = True
            attempt_record["error_message"] = "请求超时"

        except Exception as e:
            attempt_record["duration"] = time.time() - attempt_start
            attempt_record["error_message"] = f"执行异常: {str(e)}"

        session_record["attempts"].append(attempt_record)

        # 如果不是最后一次尝试，等待1秒后重试
        if attempt < max_retries - 1:
            await asyncio.sleep(1)

    session_record["total_duration"] = time.time() - start_time
    session_record["end_time"] = datetime.now().isoformat()

    return session_record


def print_session_summary(session_record: Dict[str, Any]):
    """打印会话摘要"""
    print(f"\n查询: {session_record['query']}")
    print(f"最终结果: {'✅ 成功' if session_record['final_success'] else '❌ 失败'}")
    print(f"总耗时: {session_record['total_duration']:.2f}秒")
    print(f"尝试次数: {len(session_record['attempts'])}/{session_record['max_retries']}")

    if session_record['final_success']:
        result = session_record['final_result']
        print(f"Success: {result['success']}")
        print(f"Reason: {result['reason']}")
        print(f"Client ID: {result['client_id']}")
    else:
        print("所有尝试均失败")


def print_detailed_attempts(session_record: Dict[str, Any]):
    """打印详细的尝试记录"""
    print(f"\n详细尝试记录:")
    for attempt in session_record['attempts']:
        status = "✅ 成功" if attempt['success'] else "❌ 失败"
        timeout_info = " (超时)" if attempt.get('timeout') else ""
        print(f"  尝试 {attempt['attempt_number']}: {status}{timeout_info} - {attempt['duration']:.2f}秒")
        print(f"    错误信息: {attempt['error_message']}")
        if attempt['success'] and attempt['response_data']:
            data = attempt['response_data']
            print(f"    结果: success={data['success']}, client_id={data['client_id']}")


def save_conversation_log(conversation_record: Dict[str, Any], log_file: str = "conversation_log.json"):
    """
    可选功能：保存对话记录到JSON文件
    """
    import json
    import os

    try:
        # 如果文件存在，读取现有记录
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []

        # 添加新记录
        logs.append(conversation_record)

        # 保存到文件
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

        print(f"📝 对话记录已保存到 {log_file}")

    except Exception as e:
        print(f"⚠️ 保存日志失败: {str(e)}")


def analyze_conversation_metrics(conversation_record: Dict[str, Any]):
    """
    可选功能：分析对话指标
    """
    attempts = conversation_record['attempts']
    total_attempts = len(attempts)
    successful_attempts = sum(1 for a in attempts if a['success'])
    timeout_attempts = sum(1 for a in attempts if a.get('timeout', False))

    metrics = {
        "total_attempts": total_attempts,
        "successful_attempts": successful_attempts,
        "timeout_attempts": timeout_attempts,
        "success_rate": successful_attempts / total_attempts if total_attempts > 0 else 0,
        "average_duration": sum(a['duration'] for a in attempts) / total_attempts if total_attempts > 0 else 0,
        "final_success": conversation_record['final_success'],
        "total_duration": conversation_record['total_duration']
    }

    return metrics







from autogen_ext.models.openai import OpenAIChatCompletionClient
import warnings
warnings.filterwarnings("ignore", message="Resolved model mismatch:.*")

api_key = "sk-yLCZLIlIrSK2V06h5502RshRIMyiwgIoSFTWiCtfPC4QpfwR"
base_url="https://api.001hao.com/v1"


openai_model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=api_key,
    base_url=base_url
    )

streaming_assistant = AssistantAgent(
    name="assistant",
    model_client=openai_model_client,
    output_content_type=AgentResponse,
    system_message="""
    你是一个智能体，你需要用户提供的系统中的用户列表,和某用户的交易信息,来判断属于哪个用户,并将结果结构化输出,
    如果判定成功success为yes,否则为no,置信度要大于80%才可以判定为成功,判定成功或者失败都要使用中文表达reason,并且只能返回唯一的用户id,
    """,
)




async def main():
    print("🤖 结构化输出智能体已启动 (带重试机制)")
    print("💡 输入 'quit' 或 'exit' 退出程序")
    print("💡 输入 'detail' 切换详细模式")
    print("💡 输入 'log' 切换日志记录")
    print("=" * 50)


    show_details = False
    enable_logging = False
    
    while True:
        try:
            data = input("\n请输入问题: ")

            # 检查特殊命令
            if data.lower() in ['quit', 'exit', '退出']:
                print("👋 再见!")
                break
            elif data.lower() == 'detail':
                show_details = not show_details
                print(f"详细模式: {'开启' if show_details else '关闭'}")
                continue
            elif data.lower() == 'log':
                enable_logging = not enable_logging
                print(f"日志记录: {'开启' if enable_logging else '关闭'}")
                continue

            if not data.strip():
                print("⚠️ 请输入有效的问题")
                continue

            print("\n🔄 正在处理 (最多重试3次)...")

            # 为当前对话创建记录，包含重试机制
            current_conversation_record = await get_structured_response_with_retry(
                streaming_assistant,
                data,
                max_retries=3
            )

            # 打印当前对话的结果摘要
            print_session_summary(current_conversation_record)

            # 如果开启详细模式，显示当前对话的所有尝试记录
            if show_details:
                print_detailed_attempts(current_conversation_record)

            # current_conversation_record 字典包含了此次对话的完整记录：
            # {
            #   "query": "用户输入的问题",
            #   "start_time": "开始时间",
            #   "max_retries": 3,
            #   "attempts": [
            #     {
            #       "attempt_number": 1,
            #       "success": True/False,
            #       "error_message": "错误信息或成功信息",
            #       "response_data": {...} 或 None,
            #       "duration": 1.23,
            #       "timeout": False
            #     },
            #     ...
            #   ],
            #   "final_success": True/False,
            #   "final_result": {...} 或 None,
            #   "total_duration": 3.45,
            #   "end_time": "结束时间"
            # }

            # 根据用户设置处理当前对话记录
            if enable_logging:
                save_conversation_log(current_conversation_record)

            # 分析对话指标
            metrics = analyze_conversation_metrics(current_conversation_record)
            if not current_conversation_record['final_success']:
                print(f"📊 本次对话指标: 尝试{metrics['total_attempts']}次, "
                      f"成功率{metrics['success_rate']:.1%}, "
                      f"平均耗时{metrics['average_duration']:.2f}秒")

        except KeyboardInterrupt:
            print("\n\n� 程序被用户中断，再见!")
            break
        except Exception as e:
            print(f"\n❌ 发生未预期错误: {str(e)}")
            print("🔄 程序继续运行，请重试...")


if __name__ == "__main__":
    asyncio.run(main())

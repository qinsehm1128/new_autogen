import logging
import asyncio
import sys

from autogen_agentchat.agents import AssistantAgent



from typing import Literal

from autogen_agentchat.messages import StructuredMessage
from pydantic import BaseModel


# The response format for the agent as a Pydantic base model.
class AgentResponse(BaseModel):
    
    sucess: Literal["yes", "no"]
    reason: str
    clinet_id: int







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
    如果判定成功sucess为yes,否则为no,置信度要大于80%才可以判定为成功,判定成功或者失败都要使用中文表达reason,并且只能返回唯一的用户id,
    """,
)




async def main():
    while True:
        try:
            data = input("请输入问题:")
            # async for message in streaming_assistant.run(task=data):  # type: ignore
            #     print(message)
            result = await streaming_assistant.run(task=data)
            assert isinstance(result.messages[-1], StructuredMessage)
            assert isinstance(result.messages[-1].content, AgentResponse)
            print("sucess: ", result.messages[-1].content.sucess)
            print("reason: ", result.messages[-1].content.reason)
            print("clinet_id: ", result.messages[-1].content.clinet_id)
        except Exception as e:
            print(e)
            sys.exit(1)
asyncio.run(main())

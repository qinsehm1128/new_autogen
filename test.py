import logging
import asyncio
import sys

from autogen_agentchat.agents import AssistantAgent
from autogen_core import EVENT_LOGGER_NAME
from autogen_core.models import UserMessage
# logging.basicConfig(level=logging.WARNING)
# logger = logging.getLogger(EVENT_LOGGER_NAME)
# logger.addHandler(logging.StreamHandler())
# logger.setLevel(logging.INFO)


from autogen_ext.models.openai import OpenAIChatCompletionClient
import warnings
warnings.filterwarnings("ignore", message="Resolved model mismatch:.*")

api_key = ""
base_url="https://api.001hao.com/v1"


openai_model_client = OpenAIChatCompletionClient(
    model="gpt-4",
    api_key=api_key,
    base_url=base_url
    )

streaming_assistant = AssistantAgent(
    name="assistant",
    model_client=openai_model_client,
    model_client_stream=True,
)




async def main():
    while True:
        try:
            data = input("请输入问题:")
            async for message in streaming_assistant.run_stream(task=data):  # type: ignore
                print(message)
            # result = await streaming_assistant.run(task=data)
            # print(type(result))

            print(result.messages)
        except :
            sys.exit(1)
asyncio.run(main())

import json
import uuid
import asyncio
from typing import Dict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from database import get_db
from models import ApiKey, Prompt, Conversation, Message, ChatGroup
from schemas.common import BaseResponse
from schemas.conversation import (
    ConversationCreate, ConversationUpdate, ConversationResponse, ConversationListQuery,
    MessageCreate, MessageResponse, MessageListQuery, MessageEdit, MessageRegenerate,
    ChatGroupCreate, ChatGroupUpdate, ChatGroupResponse, ChatGroupListQuery,
    MoveChatToGroup, BatchMoveChatToGroup, BatchDeleteChats,
    ExportChatRequest, BatchExportChatsRequest,
    SearchQuery, ChatSettings, GenerateTitleRequest,
    ChatStatisticsQuery
)

# 创建路由器
router = APIRouter(prefix="/chat", tags=["聊天"])

# 全局变量存储SSE任务
active_sse_tasks: Dict[str, asyncio.Task] = {}  # 存储SSE任务，key为任务ID


async def get_api_key_by_id(db: AsyncSession, api_key_id: int) -> ApiKey:
    """根据ID获取API密钥"""
    result = await db.execute(select(ApiKey).where(ApiKey.id == api_key_id, ApiKey.status == "active"))
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API密钥不存在或已禁用")
    return api_key


async def get_prompt_by_id(db: AsyncSession, prompt_id: int) -> Prompt:
    """根据ID获取提示词"""
    result = await db.execute(select(Prompt).where(Prompt.id == prompt_id))
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")
    return prompt


async def get_conversation_by_uuid(db: AsyncSession, conversation_uuid: str) -> Conversation:
    """根据UUID获取对话"""
    result = await db.execute(select(Conversation).where(Conversation.uuid == conversation_uuid))
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    return conversation


async def get_conversation_by_id(db: AsyncSession, conversation_id: int) -> Conversation:
    """根据ID获取对话"""
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    return conversation


async def get_message_by_uuid(db: AsyncSession, message_uuid: str) -> Message:
    """根据UUID获取消息"""
    result = await db.execute(select(Message).where(Message.uuid == message_uuid))
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    return message


async def get_chat_group_by_id(db: AsyncSession, group_id: int) -> ChatGroup:
    """根据ID获取分组"""
    result = await db.execute(select(ChatGroup).where(ChatGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    return group


async def get_default_group(db: AsyncSession) -> ChatGroup:
    """获取默认分组"""
    result = await db.execute(select(ChatGroup).where(ChatGroup.is_default == 1))
    group = result.scalar_one_or_none()
    if not group:
        # 创建默认分组
        group = ChatGroup(
            name="默认分组",
            description="系统默认分组",
            is_default=1
        )
        db.add(group)
        await db.commit()
        await db.refresh(group)
    return group


async def create_agent(api_key: ApiKey, prompt: Prompt, agent_state: Dict = None) -> AssistantAgent:
    """创建AutoGen代理"""
    # 创建模型客户端
    openai_model_client = OpenAIChatCompletionClient(
        model=api_key.model_name,
        api_key=api_key.api_key,
        base_url=api_key.model_url
    )

    # 创建代理
    agent = AssistantAgent(
        name="assistant",
        model_client=openai_model_client,
        model_client_stream=True,
        system_message=prompt.content,
    )

    # 如果有状态，加载它
    if agent_state:
        try:
            await agent.load_state(agent_state)
        except Exception as e:
            print(f"加载代理状态失败: {e}")

    return agent


# ==================== 对话管理接口 ====================

@router.get("/conversations/list", response_model=BaseResponse)
async def get_conversation_list(
    query: ConversationListQuery = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """获取对话列表"""
    try:
        # 构建查询条件
        conditions = [Conversation.status == "active"]

        if query.keyword:
            conditions.append(
                or_(
                    Conversation.title.contains(query.keyword),
                    Conversation.description.contains(query.keyword)
                )
            )

        if query.group_id:
            conditions.append(Conversation.group_id == query.group_id)

        if query.begin_time:
            conditions.append(Conversation.created_at >= query.begin_time)

        if query.end_time:
            conditions.append(Conversation.created_at <= query.end_time)

        # 计算总数
        count_result = await db.execute(
            select(func.count(Conversation.id)).where(and_(*conditions))
        )
        total = count_result.scalar()

        # 分页查询
        offset = (query.pageNum - 1) * query.pageSize
        result = await db.execute(
            select(Conversation)
            .where(and_(*conditions))
            .order_by(desc(Conversation.updated_at))
            .offset(offset)
            .limit(query.pageSize)
        )
        conversations = result.scalars().all()

        return BaseResponse(
            code=200,
            message="获取对话列表成功",
            data={
                "list": [
                    {
                        "id": conv.id,
                        "uuid": conv.uuid,
                        "title": conv.title,
                        "description": conv.description,
                        "group_id": conv.group_id,
                        "message_count": conv.message_count,
                        "status": conv.status,
                        "created_at": conv.created_at.isoformat(),
                        "updated_at": conv.updated_at.isoformat()
                    }
                    for conv in conversations
                ],
                "total": total,
                "pageNum": query.pageNum,
                "pageSize": query.pageSize
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话列表失败: {str(e)}")


@router.get("/conversations/{chat_id}", response_model=BaseResponse)
async def get_conversation_detail(chat_id: str, db: AsyncSession = Depends(get_db)):
    """获取对话详情"""
    try:
        conversation = await get_conversation_by_uuid(db, chat_id)

        return BaseResponse(
            code=200,
            message="获取对话详情成功",
            data={
                "id": conversation.id,
                "uuid": conversation.uuid,
                "title": conversation.title,
                "description": conversation.description,
                "group_id": conversation.group_id,
                "config": conversation.config,
                "message_count": conversation.message_count,
                "status": conversation.status,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话详情失败: {str(e)}")


@router.post("/conversations", response_model=BaseResponse)
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新对话"""
    try:
        # 验证API密钥和提示词是否存在
        if data.api_key_id:
            await get_api_key_by_id(db, data.api_key_id)
        if data.prompt_id:
            await get_prompt_by_id(db, data.prompt_id)

        # 如果没有指定分组，使用默认分组
        group_id = data.group_id
        if not group_id:
            default_group = await get_default_group(db)
            group_id = default_group.id

        # 创建对话
        conversation_uuid = str(uuid.uuid4())
        conversation = Conversation(
            uuid=conversation_uuid,
            api_key_id=data.api_key_id,
            prompt_id=data.prompt_id,
            group_id=group_id,
            title=data.title or "新对话",
            description=data.description,
            config=data.config
        )

        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

        return BaseResponse(
            code=200,
            message="对话创建成功",
            data={
                "id": conversation.id,
                "uuid": conversation.uuid,
                "title": conversation.title,
                "group_id": conversation.group_id,
                "created_at": conversation.created_at.isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建对话失败: {str(e)}")


@router.put("/conversations/{chat_id}", response_model=BaseResponse)
async def update_conversation(
    chat_id: str,
    data: ConversationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新对话信息"""
    try:
        conversation = await get_conversation_by_uuid(db, chat_id)

        # 更新字段
        if data.title is not None:
            conversation.title = data.title
        if data.description is not None:
            conversation.description = data.description
        if data.group_id is not None:
            conversation.group_id = data.group_id
        if data.config is not None:
            conversation.config = data.config

        await db.commit()
        await db.refresh(conversation)

        return BaseResponse(
            code=200,
            message="对话更新成功",
            data={
                "id": conversation.id,
                "uuid": conversation.uuid,
                "title": conversation.title,
                "updated_at": conversation.updated_at.isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新对话失败: {str(e)}")


@router.delete("/conversations/{chat_id}", response_model=BaseResponse)
async def delete_conversation(chat_id: str, db: AsyncSession = Depends(get_db)):
    """删除对话"""
    try:
        conversation = await get_conversation_by_uuid(db, chat_id)
        conversation.status = "deleted"

        await db.commit()

        return BaseResponse(
            code=200,
            message="对话删除成功",
            data=None
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除对话失败: {str(e)}")


@router.delete("/conversations/batch", response_model=BaseResponse)
async def batch_delete_conversations(
    data: BatchDeleteChats,
    db: AsyncSession = Depends(get_db)
):
    """批量删除对话"""
    try:
        # 更新状态为删除
        await db.execute(
            select(Conversation)
            .where(Conversation.uuid.in_(data.ids))
            .update({"status": "deleted"}, synchronize_session=False)
        )

        await db.commit()

        return BaseResponse(
            code=200,
            message=f"成功删除 {len(data.ids)} 个对话",
            data=None
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"批量删除对话失败: {str(e)}")


@router.delete("/conversations/{chat_id}/messages", response_model=BaseResponse)
async def clear_conversation_messages(chat_id: str, db: AsyncSession = Depends(get_db)):
    """清空对话消息"""
    try:
        conversation = await get_conversation_by_uuid(db, chat_id)

        # 删除所有消息
        await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .update({"status": "deleted"}, synchronize_session=False)
        )

        # 重置消息计数和代理状态
        conversation.message_count = 0
        conversation.agent_state = None

        await db.commit()

        return BaseResponse(
            code=200,
            message="对话消息清空成功",
            data=None
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"清空对话消息失败: {str(e)}")


@router.put("/conversations/{chat_id}/move", response_model=BaseResponse)
async def move_conversation_to_group(
    chat_id: str,
    data: MoveChatToGroup,
    db: AsyncSession = Depends(get_db)
):
    """移动对话到分组"""
    try:
        conversation = await get_conversation_by_uuid(db, chat_id)
        await get_chat_group_by_id(db, data.group_id)  # 验证分组存在

        conversation.group_id = data.group_id
        await db.commit()

        return BaseResponse(
            code=200,
            message="对话移动成功",
            data=None
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"移动对话失败: {str(e)}")


@router.put("/conversations/batch/move", response_model=BaseResponse)
async def batch_move_conversations_to_group(
    data: BatchMoveChatToGroup,
    db: AsyncSession = Depends(get_db)
):
    """批量移动对话到分组"""
    try:
        await get_chat_group_by_id(db, data.target_group_id)  # 验证分组存在

        # 批量更新分组
        await db.execute(
            select(Conversation)
            .where(Conversation.uuid.in_(data.chat_ids))
            .update({"group_id": data.target_group_id}, synchronize_session=False)
        )

        await db.commit()

        return BaseResponse(
            code=200,
            message=f"成功移动 {len(data.chat_ids)} 个对话",
            data=None
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"批量移动对话失败: {str(e)}")


# ==================== 消息管理接口 ====================

@router.get("/conversations/{chat_id}/messages", response_model=BaseResponse)
async def get_conversation_messages(
    chat_id: str,
    query: MessageListQuery = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """获取对话消息列表"""
    try:
        conversation = await get_conversation_by_uuid(db, chat_id)

        # 构建查询条件
        conditions = [
            Message.conversation_id == conversation.id,
            Message.status == "active"
        ]

        if query.message_type:
            conditions.append(Message.message_type == query.message_type)

        # 计算总数
        count_result = await db.execute(
            select(func.count(Message.id)).where(and_(*conditions))
        )
        total = count_result.scalar()

        # 分页查询
        offset = (query.pageNum - 1) * query.pageSize
        result = await db.execute(
            select(Message)
            .where(and_(*conditions))
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(query.pageSize)
        )
        messages = result.scalars().all()

        return BaseResponse(
            code=200,
            message="获取消息列表成功",
            data={
                "list": [
                    {
                        "id": msg.id,
                        "uuid": msg.uuid,
                        "role": msg.role,
                        "content": msg.content,
                        "message_type": msg.message_type,
                        "message_metadata": msg.message_metadata,
                        "token_count": msg.token_count,
                        "character_count": msg.character_count,
                        "created_at": msg.created_at.isoformat(),
                        "updated_at": msg.updated_at.isoformat()
                    }
                    for msg in messages
                ],
                "total": total,
                "pageNum": query.pageNum,
                "pageSize": query.pageSize
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取消息列表失败: {str(e)}")


@router.post("/messages", response_model=BaseResponse)
async def send_chat_message(
    data: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """发送消息"""
    try:
        conversation = await get_conversation_by_uuid(db, data.chat_id)

        # 创建用户消息
        user_message_uuid = str(uuid.uuid4())
        user_message = Message(
            uuid=user_message_uuid,
            conversation_id=conversation.id,
            role="user",
            content=data.content,
            message_type=data.message_type,
            message_metadata=data.message_metadata,
            character_count=len(data.content)
        )

        db.add(user_message)
        await db.flush()

        # 如果不是流式响应，直接生成回复
        if not data.stream:
            # 这里可以添加非流式的AI回复逻辑
            # 暂时返回用户消息
            await db.commit()

            return BaseResponse(
                code=200,
                message="消息发送成功",
                data={
                    "message_id": user_message.uuid,
                    "content": user_message.content,
                    "created_at": user_message.created_at.isoformat()
                }
            )
        else:
            # 流式响应需要通过WebSocket处理
            await db.commit()
            return BaseResponse(
                code=200,
                message="请使用WebSocket进行流式对话",
                data={"message_id": user_message.uuid}
            )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")


@router.delete("/messages/{message_id}", response_model=BaseResponse)
async def delete_message(message_id: str, db: AsyncSession = Depends(get_db)):
    """删除消息"""
    try:
        message = await get_message_by_uuid(db, message_id)
        message.status = "deleted"

        await db.commit()

        return BaseResponse(
            code=200,
            message="消息删除成功",
            data=None
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除消息失败: {str(e)}")


@router.put("/messages/{message_id}", response_model=BaseResponse)
async def edit_message(
    message_id: str,
    data: MessageEdit,
    db: AsyncSession = Depends(get_db)
):
    """编辑消息"""
    try:
        message = await get_message_by_uuid(db, message_id)

        message.content = data.content
        message.character_count = len(data.content)

        await db.commit()
        await db.refresh(message)

        return BaseResponse(
            code=200,
            message="消息编辑成功",
            data={
                "message_id": message.uuid,
                "content": message.content,
                "updated_at": message.updated_at.isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"编辑消息失败: {str(e)}")





@router.post("/terminate")
async def terminate_all_chats():
    """终止所有SSE流式任务"""
    cancelled_count = 0
    for task_id, task in list(active_sse_tasks.items()):
        if task and not task.cancelled():
            task.cancel()
            cancelled_count += 1
        del active_sse_tasks[task_id]

    return BaseResponse(
        code=200,
        message=f"已终止 {cancelled_count} 个活跃的流式任务",
        data={"cancelled_count": cancelled_count}
    )


# ==================== 对话分组管理接口 ====================

@router.get("/groups", response_model=BaseResponse)
async def get_chat_groups(
    query: ChatGroupListQuery = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """获取对话分组列表"""
    try:
        # 查询分组
        result = await db.execute(
            select(ChatGroup)
            .where(ChatGroup.status == "active")
            .order_by(ChatGroup.sort.asc(), ChatGroup.created_at.asc())
        )
        groups = result.scalars().all()

        group_data = []
        for group in groups:
            group_info = {
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "color": group.color,
                "sort": group.sort,
                "is_default": group.is_default,
                "created_at": group.created_at.isoformat(),
                "updated_at": group.updated_at.isoformat()
            }

            # 如果需要包含对话列表
            if query.include_chats:
                conv_result = await db.execute(
                    select(Conversation)
                    .where(
                        Conversation.group_id == group.id,
                        Conversation.status == "active"
                    )
                    .order_by(desc(Conversation.updated_at))
                )
                conversations = conv_result.scalars().all()

                group_info["conversations"] = [
                    {
                        "id": conv.id,
                        "uuid": conv.uuid,
                        "title": conv.title,
                        "message_count": conv.message_count,
                        "created_at": conv.created_at.isoformat(),
                        "updated_at": conv.updated_at.isoformat()
                    }
                    for conv in conversations
                ]

            group_data.append(group_info)

        return BaseResponse(
            code=200,
            message="获取分组列表成功",
            data=group_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分组列表失败: {str(e)}")


@router.post("/groups", response_model=BaseResponse)
async def create_chat_group(
    data: ChatGroupCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建对话分组"""
    try:
        group = ChatGroup(
            name=data.name,
            description=data.description,
            color=data.color,
            sort=data.sort
        )

        db.add(group)
        await db.commit()
        await db.refresh(group)

        return BaseResponse(
            code=200,
            message="分组创建成功",
            data={
                "id": group.id,
                "name": group.name,
                "created_at": group.created_at.isoformat()
            }
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建分组失败: {str(e)}")


@router.put("/groups/{group_id}", response_model=BaseResponse)
async def update_chat_group(
    group_id: int,
    data: ChatGroupUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新对话分组"""
    try:
        group = await get_chat_group_by_id(db, group_id)

        if data.name is not None:
            group.name = data.name
        if data.description is not None:
            group.description = data.description
        if data.color is not None:
            group.color = data.color
        if data.sort is not None:
            group.sort = data.sort

        await db.commit()
        await db.refresh(group)

        return BaseResponse(
            code=200,
            message="分组更新成功",
            data={
                "id": group.id,
                "name": group.name,
                "updated_at": group.updated_at.isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新分组失败: {str(e)}")


@router.delete("/groups/{group_id}", response_model=BaseResponse)
async def delete_chat_group(
    group_id: int,
    delete_chats: bool = Query(default=False, description="是否同时删除分组内的对话"),
    db: AsyncSession = Depends(get_db)
):
    """删除对话分组"""
    try:
        group = await get_chat_group_by_id(db, group_id)

        # 检查是否为默认分组
        if group.is_default:
            raise HTTPException(status_code=400, detail="不能删除默认分组")

        if delete_chats:
            # 删除分组内的所有对话
            await db.execute(
                select(Conversation)
                .where(Conversation.group_id == group_id)
                .update({"status": "deleted"}, synchronize_session=False)
            )
        else:
            # 将对话移动到默认分组
            default_group = await get_default_group(db)
            await db.execute(
                select(Conversation)
                .where(Conversation.group_id == group_id)
                .update({"group_id": default_group.id}, synchronize_session=False)
            )

        # 删除分组
        group.status = "deleted"
        await db.commit()

        return BaseResponse(
            code=200,
            message="分组删除成功",
            data=None
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除分组失败: {str(e)}")





# ==================== 搜索接口 ====================

@router.get("/search", response_model=BaseResponse)
async def search_chats(
    query: SearchQuery = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """搜索对话和消息"""
    try:
        results = {"conversations": [], "messages": []}

        if query.type in ["all", "chat"]:
            # 搜索对话
            conditions = [Conversation.status == "active"]

            if query.keyword:
                conditions.append(
                    or_(
                        Conversation.title.contains(query.keyword),
                        Conversation.description.contains(query.keyword)
                    )
                )

            if query.group_id:
                conditions.append(Conversation.group_id == query.group_id)

            if query.begin_time:
                conditions.append(Conversation.created_at >= query.begin_time)

            if query.end_time:
                conditions.append(Conversation.created_at <= query.end_time)

            # 分页查询对话
            offset = (query.pageNum - 1) * query.pageSize
            conv_result = await db.execute(
                select(Conversation)
                .where(and_(*conditions))
                .order_by(desc(Conversation.updated_at))
                .offset(offset)
                .limit(query.pageSize)
            )
            conversations = conv_result.scalars().all()

            results["conversations"] = [
                {
                    "id": conv.id,
                    "uuid": conv.uuid,
                    "title": conv.title,
                    "description": conv.description,
                    "group_id": conv.group_id,
                    "message_count": conv.message_count,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat()
                }
                for conv in conversations
            ]

        if query.type in ["all", "message"]:
            # 搜索消息
            conditions = [Message.status == "active"]

            if query.keyword:
                conditions.append(Message.content.contains(query.keyword))

            # 分页查询消息
            offset = (query.pageNum - 1) * query.pageSize
            msg_result = await db.execute(
                select(Message)
                .where(and_(*conditions))
                .order_by(desc(Message.created_at))
                .offset(offset)
                .limit(query.pageSize)
            )
            messages = msg_result.scalars().all()

            results["messages"] = [
                {
                    "id": msg.id,
                    "uuid": msg.uuid,
                    "conversation_id": msg.conversation_id,
                    "role": msg.role,
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]

        return BaseResponse(
            code=200,
            message="搜索完成",
            data=results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")




# ==================== 实用工具接口 ====================

@router.post("/utils/generate-title", response_model=BaseResponse)
async def generate_chat_title(data: GenerateTitleRequest):
    """生成对话标题"""
    try:
        # 简单的标题生成逻辑
        content = data.content[:data.max_length]
        if len(data.content) > data.max_length:
            content += "..."

        # 移除换行符和多余空格
        title = " ".join(content.split())

        return BaseResponse(
            code=200,
            message="标题生成成功",
            data={"title": title}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成标题失败: {str(e)}")






@router.post("/messages/regenerate", response_model=BaseResponse)
async def regenerate_message(
    data: MessageRegenerate,
    db: AsyncSession = Depends(get_db)
):
    """重新生成消息"""
    try:
        conversation = await get_conversation_by_uuid(db, data.chat_id)
        message = await get_message_by_uuid(db, data.message_id)

        # 验证消息属于该对话
        if message.conversation_id != conversation.id:
            raise HTTPException(status_code=400, detail="消息不属于该对话")

        # 这里可以添加实际的重新生成逻辑
        # 暂时返回成功响应
        return BaseResponse(
            code=200,
            message="消息重新生成成功",
            data={
                "message_id": message.uuid,
                "new_content": "重新生成的内容",
                "regenerated_at": datetime.now().isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新生成消息失败: {str(e)}")


@router.post("/messages/stream")
async def stream_message(
    data: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """流式消息接口（Server-Sent Events）"""
    try:
        conversation = await get_conversation_by_uuid(db, data.chat_id)

        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 创建用户消息
        user_message_uuid = str(uuid.uuid4())
        user_message = Message(
            uuid=user_message_uuid,
            conversation_id=conversation.id,
            role="user",
            content=data.content,
            message_type=data.message_type,
            message_metadata=data.message_metadata,
            character_count=len(data.content)
        )

        db.add(user_message)
        await db.flush()

        # 创建助手消息
        assistant_message_uuid = str(uuid.uuid4())
        assistant_message = Message(
            uuid=assistant_message_uuid,
            conversation_id=conversation.id,
            role="assistant",
            content="",
            message_type="text",
            character_count=0
        )

        db.add(assistant_message)
        await db.flush()
        

        # 先提交用户消息和初始助手消息
        await db.commit()

        async def generate():
            # 在生成器内部创建新的数据库会话
            from database import AsyncSessionLocal
            async with AsyncSessionLocal() as gen_db:
                try:
                    # 重新获取对话和消息对象
                    conversation_obj = await get_conversation_by_uuid(gen_db, data.chat_id)
                    assistant_msg_result = await gen_db.execute(
                        select(Message).where(Message.uuid == assistant_message_uuid)
                    )
                    assistant_message_obj = assistant_msg_result.scalar_one()
                    
                    # 发送用户消息确认
                    yield f"data: {json.dumps({'type': 'user_message', 'content': data.content, 'message_id': user_message_uuid})}\n\n"

                    # 发送助手消息开始标识
                    yield f"data: {json.dumps({'type': 'assistant_start', 'message_id': assistant_message_uuid})}\n\n"

                    # 获取API密钥和提示词
                    api_key = await get_api_key_by_id(gen_db, conversation_obj.api_key_id)
                    prompt = await get_prompt_by_id(gen_db, conversation_obj.prompt_id)

                    # 创建代理
                    agent = await create_agent(api_key, prompt, conversation_obj.agent_state)

                    # 流式生成回复
                    full_content = ""
                    async for chunk in agent.run_stream(task=data.content):
                        # 检查是否被取消
                        if task_id in active_sse_tasks:
                            current_task = active_sse_tasks[task_id]
                            if current_task.cancelled():
                                yield f"data: {json.dumps({'type': 'cancelled', 'message': '生成已被取消'})}\n\n"
                                break

                        if hasattr(chunk, 'content') and chunk.content and chunk.type == "ModelClientStreamingChunkEvent":
                            content_chunk = chunk.content
                            full_content += content_chunk
                            yield f"data: {json.dumps({'type': 'chunk', 'content': content_chunk, 'message_id': assistant_message_uuid})}\n\n"

                    # 更新助手消息内容
                    assistant_message_obj.content = full_content
                    assistant_message_obj.character_count = len(full_content)

                    # 更新对话消息计数
                    conversation_obj.message_count += 1  # 只增加1，因为用户消息已经计数了

                    # 保存代理状态
                    try:
                        state = await agent.save_state()
                        print(f"代理状态: {state}")
                        conversation_obj.agent_state = state
                    except Exception as e:
                        print(f"保存代理状态失败: {e}")
                        # 即使状态保存失败，也要保存消息内容

                    # 提交所有更改
                    await gen_db.commit()
                    print(f"数据库提交成功，消息内容长度: {len(full_content)}")

                    # 发送完成信号
                    yield f"data: {json.dumps({'type': 'complete', 'message_id': assistant_message_uuid, 'content': full_content})}\n\n"
                    
                except asyncio.CancelledError:
                    yield f"data: {json.dumps({'type': 'cancelled', 'message': '生成已被取消'})}\n\n"
                    raise
                except Exception as e:
                    print(f"生成失败: {str(e)}")
                    await db.rollback()
                    yield f"data: {json.dumps({'type': 'error', 'message': f'生成失败: {str(e)}'})}\n\n"
                finally:
                    # 清理任务
                    if task_id in active_sse_tasks:
                        del active_sse_tasks[task_id]

        # 创建并存储任务
        task = asyncio.create_task(generate().__anext__())
        active_sse_tasks[task_id] = task

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "X-Task-ID": task_id  # 返回任务ID给前端
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"流式消息失败: {str(e)}")


@router.post("/messages/stream/cancel")
async def cancel_stream_message(
    task_id: str = Query(..., description="任务ID")
):
    """取消流式消息生成"""
    try:
        if task_id in active_sse_tasks:
            task = active_sse_tasks[task_id]
            task.cancel()
            del active_sse_tasks[task_id]

            return BaseResponse(
                code=200,
                message="流式生成已取消",
                data={"task_id": task_id}
            )
        else:
            return BaseResponse(
                code=404,
                message="任务不存在或已完成",
                data={"task_id": task_id}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消流式消息失败: {str(e)}")
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ConversationBase(BaseModel):
    """对话基础模型"""
    title: Optional[str] = Field(None, description="对话标题")
    description: Optional[str] = Field(None, description="对话描述")
    group_id: Optional[int] = Field(None, description="分组ID")
    config: Optional[Dict[str, Any]] = Field(None, description="对话配置")


class ConversationCreate(ConversationBase):
    """创建对话模型"""
    api_key_id: Optional[int] = Field(None, description="API密钥ID")
    prompt_id: Optional[int] = Field(None, description="提示词ID")


class ConversationUpdate(ConversationBase):
    """更新对话模型"""
    model_id: Optional[str] = Field(None, description="模型ID")


class ConversationResponse(ConversationBase):
    """对话响应模型"""
    id: int
    uuid: str
    message_count: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationListQuery(BaseModel):
    """对话列表查询模型"""
    pageNum: int = Field(default=1, ge=1, description="页码")
    pageSize: int = Field(default=20, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(None, description="搜索关键词")
    group_id: Optional[int] = Field(None, description="分组ID筛选")
    model_id: Optional[str] = Field(None, description="模型ID筛选")
    begin_time: Optional[str] = Field(None, description="开始时间")
    end_time: Optional[str] = Field(None, description="结束时间")


class MessageBase(BaseModel):
    """消息基础模型"""
    content: str = Field(..., description="消息内容")
    message_type: str = Field(default="text", description="消息类型")
    message_metadata: Optional[Dict[str, Any]] = Field(None, description="消息元数据")


class MessageCreate(MessageBase):
    """创建消息模型"""
    chat_id: str = Field(..., description="对话ID")
    stream: bool = Field(default=False, description="是否流式响应")


class MessageResponse(MessageBase):
    """消息响应模型"""
    id: int
    uuid: str
    role: str
    token_count: int
    character_count: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageListQuery(BaseModel):
    """消息列表查询模型"""
    pageNum: int = Field(default=1, ge=1, description="页码")
    pageSize: int = Field(default=50, ge=1, le=100, description="每页数量")
    message_type: Optional[str] = Field(None, description="消息类型筛选")


class MessageEdit(BaseModel):
    """编辑消息模型"""
    content: str = Field(..., description="新的消息内容")


class MessageRegenerate(BaseModel):
    """重新生成消息模型"""
    chat_id: str = Field(..., description="对话ID")
    message_id: str = Field(..., description="消息ID")
    config: Optional[Dict[str, Any]] = Field(None, description="生成配置")


class ChatGroupBase(BaseModel):
    """分组基础模型"""
    name: str = Field(..., description="分组名称")
    description: Optional[str] = Field(None, description="分组描述")
    color: Optional[str] = Field(None, description="分组颜色")
    sort: Optional[int] = Field(default=0, description="排序值")


class ChatGroupCreate(ChatGroupBase):
    """创建分组模型"""
    pass


class ChatGroupUpdate(ChatGroupBase):
    """更新分组模型"""
    name: Optional[str] = Field(None, description="分组名称")


class ChatGroupResponse(ChatGroupBase):
    """分组响应模型"""
    id: int
    is_default: int
    status: str
    created_at: datetime
    updated_at: datetime
    conversations: Optional[List[ConversationResponse]] = Field(None, description="对话列表")

    class Config:
        from_attributes = True


class ChatGroupListQuery(BaseModel):
    """分组列表查询模型"""
    include_chats: bool = Field(default=True, description="是否包含对话列表")


class MoveChatToGroup(BaseModel):
    """移动对话到分组模型"""
    group_id: int = Field(..., description="目标分组ID")


class BatchMoveChatToGroup(BaseModel):
    """批量移动对话到分组模型"""
    chat_ids: List[str] = Field(..., description="对话ID数组")
    target_group_id: int = Field(..., description="目标分组ID")


class BatchDeleteChats(BaseModel):
    """批量删除对话模型"""
    ids: List[str] = Field(..., description="对话ID数组")





class ExportChatRequest(BaseModel):
    """导出对话请求模型"""
    chat_id: str = Field(..., description="对话ID")
    format: str = Field(default="json", description="导出格式")
    include_system_messages: bool = Field(default=False, description="是否包含系统消息")


class BatchExportChatsRequest(BaseModel):
    """批量导出对话请求模型"""
    chat_ids: List[str] = Field(..., description="对话ID数组")
    format: str = Field(default="json", description="导出格式")
    include_system_messages: bool = Field(default=False, description="是否包含系统消息")


class SearchQuery(BaseModel):
    """搜索查询模型"""
    keyword: str = Field(..., description="搜索关键词")
    type: str = Field(default="all", description="搜索类型")
    group_id: Optional[int] = Field(None, description="分组ID筛选")
    model_id: Optional[str] = Field(None, description="模型ID筛选")
    begin_time: Optional[str] = Field(None, description="开始时间")
    end_time: Optional[str] = Field(None, description="结束时间")
    pageNum: int = Field(default=1, ge=1, description="页码")
    pageSize: int = Field(default=20, ge=1, le=100, description="每页数量")


class ChatSettings(BaseModel):
    """聊天设置模型"""
    preferences: Optional[Dict[str, Any]] = Field(None, description="用户偏好设置")
    default_config: Optional[Dict[str, Any]] = Field(None, description="默认对话配置")
    auto_save: bool = Field(default=True, description="是否自动保存对话")
    theme: str = Field(default="light", description="主题设置")


class GenerateTitleRequest(BaseModel):
    """生成标题请求模型"""
    content: str = Field(..., description="对话内容")
    max_length: int = Field(default=50, description="最大长度")





class ChatStatisticsQuery(BaseModel):
    """对话统计查询模型"""
    time_range: str = Field(default="day", description="时间范围")
    group_id: Optional[int] = Field(None, description="分组ID筛选")

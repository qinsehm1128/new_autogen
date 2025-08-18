from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True, comment="对话唯一标识")
    api_key_id = Column(Integer, nullable=False, comment="使用的API密钥ID")
    prompt_id = Column(Integer, nullable=False, comment="使用的提示词ID")
    group_id = Column(Integer, ForeignKey("chat_groups.id"), nullable=True, comment="分组ID")
    title = Column(String(200), comment="对话标题")
    description = Column(Text, comment="对话描述")
    config = Column(JSON, comment="对话配置")
    agent_state = Column(JSON, comment="Agent状态数据")
    message_count = Column(Integer, default=0, comment="消息数量")
    status = Column(String(20), default="active", comment="状态：active/archived/deleted")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    group = relationship("ChatGroup", back_populates="conversations")

    def __repr__(self):
        return f"<Conversation(id={self.id}, uuid={self.uuid}, status={self.status})>"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True, comment="消息唯一标识")
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, comment="对话ID")
    role = Column(String(20), nullable=False, comment="角色：user/assistant/system")
    content = Column(Text, nullable=False, comment="消息内容")
    message_type = Column(String(20), default="text", comment="消息类型：text/image/file")
    message_metadata = Column(JSON, comment="消息元数据")
    token_count = Column(Integer, default=0, comment="Token数量")
    character_count = Column(Integer, default=0, comment="字符数量")
    status = Column(String(20), default="active", comment="状态：active/deleted")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, uuid={self.uuid}, role={self.role})>"


class ChatGroup(Base):
    __tablename__ = "chat_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="分组名称")
    description = Column(Text, comment="分组描述")
    color = Column(String(20), comment="分组颜色")
    sort = Column(Integer, default=0, comment="排序值")
    is_default = Column(Integer, default=0, comment="是否默认分组：0否/1是")
    status = Column(String(20), default="active", comment="状态：active/deleted")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    conversations = relationship("Conversation", back_populates="group")

    def __repr__(self):
        return f"<ChatGroup(id={self.id}, name={self.name})>"



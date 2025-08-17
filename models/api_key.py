from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    api_key = Column(String(500), nullable=False, comment="API密钥")
    model_name = Column(String(100), nullable=False, comment="模型名称")
    model_url = Column(String(500), nullable=False, comment="模型地址")
    description = Column(Text, comment="描述")
    status = Column(String(20), default="active", comment="状态：active/inactive")
    provider = Column(String(50), comment="提供商：openai/anthropic/google等")
    config = Column(JSON, comment="额外配置")
    max_tokens = Column(Integer, comment="最大Token数")
    timeout = Column(Integer, comment="超时时间（秒）")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<ApiKey(id={self.id}, model_name={self.model_name}, status={self.status})>"

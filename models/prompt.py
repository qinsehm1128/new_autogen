from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from database import Base


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="提示词标题")
    category = Column(String(50), nullable=False, comment="分类：system/role/creative/code/other")
    content = Column(Text, nullable=False, comment="提示词内容")
    description = Column(Text, comment="描述")
    tags = Column(JSON, comment="标签数组")
    is_public = Column(Boolean, default=False, comment="是否公开")
    variables = Column(JSON, comment="变量定义")
    config = Column(JSON, comment="额外配置")
    sort = Column(Integer, default=0, comment="排序值")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Prompt(id={self.id}, title={self.title}, category={self.category})>"

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class PromptBase(BaseModel):
    title: str = Field(..., description="提示词标题")
    category: str = Field(..., description="分类：system/role/creative/code/other")
    content: str = Field(..., description="提示词内容")
    description: Optional[str] = Field(None, description="描述")
    tags: Optional[List[str]] = Field(None, description="标签数组")
    is_public: bool = Field(default=False, description="是否公开")
    variables: Optional[Dict[str, Any]] = Field(None, description="变量定义")
    config: Optional[Dict[str, Any]] = Field(None, description="额外配置")
    sort: Optional[int] = Field(default=0, description="排序值")


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    id: int = Field(..., description="提示词ID")
    title: Optional[str] = Field(None, description="提示词标题")
    category: Optional[str] = Field(None, description="分类")
    content: Optional[str] = Field(None, description="提示词内容")
    description: Optional[str] = Field(None, description="描述")
    tags: Optional[List[str]] = Field(None, description="标签数组")
    is_public: Optional[bool] = Field(None, description="是否公开")
    variables: Optional[Dict[str, Any]] = Field(None, description="变量定义")
    config: Optional[Dict[str, Any]] = Field(None, description="额外配置")
    sort: Optional[int] = Field(None, description="排序值")


class PromptResponse(PromptBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromptListQuery(BaseModel):
    pageNum: int = Field(default=1, ge=1, description="页码")
    pageSize: int = Field(default=10, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(None, description="搜索关键词")
    category: Optional[str] = Field(None, description="分类筛选")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    beginTime: Optional[str] = Field(None, description="开始时间")
    endTime: Optional[str] = Field(None, description="结束时间")


class PromptListResponse(BaseModel):
    total: int
    items: List[PromptResponse]
    pageNum: int
    pageSize: int


class PromptBatchDelete(BaseModel):
    ids: List[int] = Field(..., description="提示词ID数组")


class PromptTest(BaseModel):
    content: str = Field(..., description="提示词内容")
    variables: Optional[Dict[str, Any]] = Field(None, description="变量值")
    testInput: str = Field(..., description="测试输入")


class PromptTestResponse(BaseModel):
    success: bool
    message: str
    result: Optional[str] = None


class PromptCategory(BaseModel):
    value: str
    label: str
    count: int


class PromptTag(BaseModel):
    name: str
    count: int

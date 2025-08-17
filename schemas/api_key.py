from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ApiKeyBase(BaseModel):
    api_key: str = Field(..., description="API密钥")
    model_name: str = Field(..., description="模型名称")
    model_url: str = Field(..., description="模型地址")
    description: Optional[str] = Field(None, description="描述")
    status: str = Field(default="active", description="状态：active/inactive")
    provider: Optional[str] = Field(None, description="提供商：openai/anthropic/google等")
    config: Optional[Dict[str, Any]] = Field(None, description="额外配置")
    max_tokens: Optional[int] = Field(None, description="最大Token数")
    timeout: Optional[int] = Field(None, description="超时时间（秒）")


class ApiKeyCreate(ApiKeyBase):
    pass


class ApiKeyUpdate(BaseModel):
    id: int = Field(..., description="API Key ID")
    api_key: Optional[str] = Field(None, description="API密钥")
    model_name: Optional[str] = Field(None, description="模型名称")
    model_url: Optional[str] = Field(None, description="模型地址")
    description: Optional[str] = Field(None, description="描述")
    status: Optional[str] = Field(None, description="状态：active/inactive")
    provider: Optional[str] = Field(None, description="提供商")
    config: Optional[Dict[str, Any]] = Field(None, description="额外配置")
    max_tokens: Optional[int] = Field(None, description="最大Token数")
    timeout: Optional[int] = Field(None, description="超时时间（秒）")


class ApiKeyResponse(ApiKeyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApiKeyListQuery(BaseModel):
    pageNum: int = Field(default=1, ge=1, description="页码")
    pageSize: int = Field(default=10, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(None, description="搜索关键词")
    status: Optional[str] = Field(None, description="状态筛选")
    modelName: Optional[str] = Field(None, description="模型名称筛选")
    beginTime: Optional[str] = Field(None, description="开始时间")
    endTime: Optional[str] = Field(None, description="结束时间")


class ApiKeyListResponse(BaseModel):
    total: int
    items: list[ApiKeyResponse]
    pageNum: int
    pageSize: int


class ApiKeyBatchDelete(BaseModel):
    ids: list[int] = Field(..., description="API Key ID数组")


class ApiKeyBatchStatus(BaseModel):
    ids: list[int] = Field(..., description="API Key ID数组")
    status: str = Field(..., description="目标状态")


class ApiKeyTest(BaseModel):
    id: Optional[int] = Field(None, description="API Key ID")
    api_key: Optional[str] = Field(None, description="API密钥")
    model_url: Optional[str] = Field(None, description="模型地址")
    model_name: Optional[str] = Field(None, description="模型名称")


class ApiKeyTestResponse(BaseModel):
    success: bool
    message: str
    response_time: Optional[float] = None


class ApiKeyStats(BaseModel):
    total: int
    active: int
    inactive: int
    providers: Dict[str, int]

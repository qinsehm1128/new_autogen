from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime


class BaseResponse(BaseModel):
    """基础响应模型"""
    code: int = Field(default=200, description="响应状态码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")


class PaginationQuery(BaseModel):
    """分页查询基础模型"""
    pageNum: int = Field(default=1, ge=1, description="页码")
    pageSize: int = Field(default=10, ge=1, le=100, description="每页数量")


class TimeRangeQuery(BaseModel):
    """时间范围查询基础模型"""
    beginTime: Optional[str] = Field(None, description="开始时间")
    endTime: Optional[str] = Field(None, description="结束时间")




class SystemConfig(BaseModel):
    """系统配置模型"""
    apiKeyConfig: Optional[Dict[str, Any]] = Field(None, description="API Key配置")
    promptConfig: Optional[Dict[str, Any]] = Field(None, description="提示词配置")


class StatisticsQuery(BaseModel):
    """统计查询模型"""
    type: str = Field(..., description="统计类型：overview/apikeys/rules/prompts")
    timeRange: str = Field(default="day", description="时间范围：day/week/month/year")


class OverviewStats(BaseModel):
    """概览统计模型"""
    apiKeyCount: int = Field(..., description="API Key总数")
    activeApiKeyCount: int = Field(..., description="活跃API Key数量")
    promptCount: int = Field(..., description="提示词总数")
    publicPromptCount: int = Field(..., description="公开提示词数量")


class StatisticsResponse(BaseModel):
    """统计响应模型"""
    overview: Optional[OverviewStats] = Field(None, description="概览统计")
    charts: Optional[Dict[str, Any]] = Field(None, description="图表数据")
    trends: Optional[Dict[str, Any]] = Field(None, description="趋势数据")


class BatchOperation(BaseModel):
    """批量操作基础模型"""
    ids: List[int] = Field(..., description="操作对象ID数组")


class SuccessResponse(BaseResponse):
    """成功响应模型"""
    code: int = Field(default=200)
    message: str = Field(default="操作成功")


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    code: int = Field(default=400)
    message: str = Field(default="操作失败")


class ValidationError(BaseModel):
    """验证错误模型"""
    field: str = Field(..., description="字段名")
    message: str = Field(..., description="错误消息")


class DetailErrorResponse(BaseResponse):
    """详细错误响应模型"""
    code: int = Field(default=400)
    message: str = Field(default="验证失败")
    errors: List[ValidationError] = Field(..., description="验证错误列表")

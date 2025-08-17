from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from typing import Optional, List
from datetime import datetime, timedelta

from database import get_db
from models.api_key import ApiKey
from models.prompt import Prompt
from schemas import (
    SystemConfig,
    StatisticsQuery,
    OverviewStats,
    StatisticsResponse,
    BaseResponse,
    SuccessResponse
)

router = APIRouter(prefix="/chat", tags=["公共接口"])


@router.get("/config", response_model=BaseResponse)
async def get_system_config():
    """获取系统配置"""
    try:
        # 默认系统配置
        config = SystemConfig(
            apiKeyConfig={
                "defaultTimeout": 30,
                "maxRetries": 3,
                "supportedProviders": ["openai", "anthropic", "google", "azure", "other"]
            },
            promptConfig={
                "supportedCategories": ["system", "role", "creative", "code", "other"],
                "defaultPublic": False,
                "maxVariables": 20
            }
        )

        return BaseResponse(data=config)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.put("/config", response_model=BaseResponse)
async def update_system_config(config_data: SystemConfig):
    """更新系统配置"""
    try:
        # 这里可以实现配置的持久化存储
        # 目前只是简单返回成功响应
        return SuccessResponse(message="系统配置更新成功")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.get("/statistics", response_model=BaseResponse)
async def get_statistics(
    type: str = "overview",
    timeRange: str = "day",
    db: AsyncSession = Depends(get_db)
):
    """获取数据统计"""
    try:
        if type == "overview":
            # 概览统计
            api_key_count_stmt = select(func.count(ApiKey.id))
            api_key_count_result = await db.execute(api_key_count_stmt)
            api_key_count = api_key_count_result.scalar()

            active_api_key_count_stmt = select(func.count(ApiKey.id)).where(ApiKey.status == "active")
            active_api_key_count_result = await db.execute(active_api_key_count_stmt)
            active_api_key_count = active_api_key_count_result.scalar()

            prompt_count_stmt = select(func.count(Prompt.id))
            prompt_count_result = await db.execute(prompt_count_stmt)
            prompt_count = prompt_count_result.scalar()

            public_prompt_count_stmt = select(func.count(Prompt.id)).where(Prompt.is_public == True)
            public_prompt_count_result = await db.execute(public_prompt_count_stmt)
            public_prompt_count = public_prompt_count_result.scalar()

            overview = OverviewStats(
                apiKeyCount=api_key_count,
                activeApiKeyCount=active_api_key_count,
                promptCount=prompt_count,
                publicPromptCount=public_prompt_count
            )

            # 根据时间范围获取趋势数据
            now = datetime.now()
            if timeRange == "day":
                start_time = now - timedelta(days=7)
                date_format = "%Y-%m-%d"
            elif timeRange == "week":
                start_time = now - timedelta(weeks=12)
                date_format = "%Y-%W"
            elif timeRange == "month":
                start_time = now - timedelta(days=365)
                date_format = "%Y-%m"
            else:
                start_time = now - timedelta(days=30)
                date_format = "%Y-%m-%d"

            # 获取创建趋势
            api_key_trend_stmt = (
                select(
                    func.strftime(date_format, ApiKey.created_at).label('date'),
                    func.count(ApiKey.id).label('count')
                )
                .where(ApiKey.created_at >= start_time)
                .group_by('date')
            )
            api_key_trend_result = await db.execute(api_key_trend_stmt)
            api_key_trend = api_key_trend_result.all()

            prompt_trend_stmt = (
                select(
                    func.strftime(date_format, Prompt.created_at).label('date'),
                    func.count(Prompt.id).label('count')
                )
                .where(Prompt.created_at >= start_time)
                .group_by('date')
            )
            prompt_trend_result = await db.execute(prompt_trend_stmt)
            prompt_trend = prompt_trend_result.all()

            trends = {
                "apiKeys": [{"date": item.date, "count": item.count} for item in api_key_trend],
                "prompts": [{"date": item.date, "count": item.count} for item in prompt_trend]
            }

            # 分类统计
            charts = {
                "apiKeysByProvider": [],
                "promptsByCategory": []
            }

            # API Key按提供商统计
            provider_stats_stmt = (
                select(ApiKey.provider, func.count(ApiKey.id).label('count'))
                .group_by(ApiKey.provider)
            )
            provider_stats_result = await db.execute(provider_stats_stmt)
            provider_stats = provider_stats_result.all()
            charts["apiKeysByProvider"] = [
                {"name": item.provider or "未知", "value": item.count}
                for item in provider_stats
            ]

            # 提示词按分类统计
            prompt_category_stats_stmt = (
                select(Prompt.category, func.count(Prompt.id).label('count'))
                .group_by(Prompt.category)
            )
            prompt_category_stats_result = await db.execute(prompt_category_stats_stmt)
            prompt_category_stats = prompt_category_stats_result.all()
            charts["promptsByCategory"] = [
                {"name": item.category, "value": item.count}
                for item in prompt_category_stats
            ]

            response_data = StatisticsResponse(
                overview=overview,
                charts=charts,
                trends=trends
            )

            return BaseResponse(data=response_data)

        else:
            raise HTTPException(status_code=400, detail="不支持的统计类型")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")

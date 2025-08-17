from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, func, delete, update
from sqlalchemy.orm import selectinload
from typing import Optional, List
import httpx
import time
from datetime import datetime

from database import get_db
from models.api_key import ApiKey
from schemas import (
    ApiKeyCreate,
    ApiKeyUpdate,
    ApiKeyResponse,
    ApiKeyListQuery,
    ApiKeyListResponse,
    ApiKeyBatchDelete,
    ApiKeyBatchStatus,
    ApiKeyTest,
    ApiKeyTestResponse,
    ApiKeyStats,
    BaseResponse,
    SuccessResponse
)

router = APIRouter(prefix="/chat/api-keys", tags=["API Key管理"])


@router.get("/list", response_model=BaseResponse)
async def list_api_keys(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态筛选"),
    modelName: Optional[str] = Query(None, description="模型名称筛选"),
    beginTime: Optional[str] = Query(None, description="开始时间"),
    endTime: Optional[str] = Query(None, description="结束时间"),
    db: AsyncSession = Depends(get_db)
):
    """获取API Key列表"""
    try:
        # 构建查询条件
        conditions = []

        # 关键词搜索
        if keyword:
            conditions.append(
                or_(
                    ApiKey.api_key.contains(keyword),
                    ApiKey.model_name.contains(keyword),
                    ApiKey.description.contains(keyword)
                )
            )

        # 状态筛选
        if status:
            conditions.append(ApiKey.status == status)

        # 模型名称筛选
        if modelName:
            conditions.append(ApiKey.model_name.contains(modelName))

        # 时间范围筛选
        if beginTime:
            conditions.append(ApiKey.created_at >= datetime.fromisoformat(beginTime))
        if endTime:
            conditions.append(ApiKey.created_at <= datetime.fromisoformat(endTime))

        # 构建查询语句
        where_clause = and_(*conditions) if conditions else True

        # 获取总数
        count_stmt = select(func.count(ApiKey.id)).where(where_clause)
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()

        # 分页查询
        offset = (pageNum - 1) * pageSize
        query_stmt = (
            select(ApiKey)
            .where(where_clause)
            .order_by(ApiKey.created_at.desc())
            .offset(offset)
            .limit(pageSize)
        )

        result = await db.execute(query_stmt)
        items = result.scalars().all()

        # 构造响应数据
        response_data = ApiKeyListResponse(
            total=total,
            items=[ApiKeyResponse.from_orm(item) for item in items],
            pageNum=pageNum,
            pageSize=pageSize
        )

        return BaseResponse(data=response_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/{api_key_id}", response_model=BaseResponse)
async def get_api_key(api_key_id: int, db: AsyncSession = Depends(get_db)):
    """获取API Key详情"""
    stmt = select(ApiKey).where(ApiKey.id == api_key_id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=404, detail="API Key不存在")

    return BaseResponse(data=ApiKeyResponse.from_orm(api_key))


@router.post("", response_model=BaseResponse)
async def create_api_key(api_key_data: ApiKeyCreate, db: AsyncSession = Depends(get_db)):
    """新增API Key"""
    try:
        # 检查API Key是否已存在
        existing_stmt = select(ApiKey).where(ApiKey.api_key == api_key_data.api_key)
        existing_result = await db.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()

        if existing:
            raise HTTPException(status_code=400, detail="该API Key已存在")

        # 创建新的API Key
        db_api_key = ApiKey(**api_key_data.dict())
        db.add(db_api_key)
        await db.commit()
        await db.refresh(db_api_key)

        return BaseResponse(
            message="API Key创建成功",
            data=ApiKeyResponse.from_orm(db_api_key)
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.put("", response_model=BaseResponse)
async def update_api_key(api_key_data: ApiKeyUpdate, db: AsyncSession = Depends(get_db)):
    """修改API Key"""
    try:
        stmt = select(ApiKey).where(ApiKey.id == api_key_data.id)
        result = await db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise HTTPException(status_code=404, detail="API Key不存在")

        # 更新字段
        update_data = api_key_data.dict(exclude_unset=True, exclude={"id"})
        for field, value in update_data.items():
            setattr(api_key, field, value)

        await db.commit()
        await db.refresh(api_key)

        return BaseResponse(
            message="API Key更新成功",
            data=ApiKeyResponse.from_orm(api_key)
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/{api_key_id}", response_model=BaseResponse)
async def delete_api_key(api_key_id: int, db: AsyncSession = Depends(get_db)):
    """删除API Key"""
    try:
        stmt = select(ApiKey).where(ApiKey.id == api_key_id)
        result = await db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise HTTPException(status_code=404, detail="API Key不存在")

        await db.delete(api_key)
        await db.commit()

        return SuccessResponse(message="API Key删除成功")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.delete("/batch", response_model=BaseResponse)
async def batch_delete_api_keys(batch_data: ApiKeyBatchDelete, db: AsyncSession = Depends(get_db)):
    """批量删除API Key"""
    try:
        stmt = delete(ApiKey).where(ApiKey.id.in_(batch_data.ids))
        result = await db.execute(stmt)
        deleted_count = result.rowcount
        await db.commit()

        return SuccessResponse(message=f"成功删除 {deleted_count} 个API Key")

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"批量删除失败: {str(e)}")


@router.put("/batch/status", response_model=BaseResponse)
async def batch_update_api_key_status(batch_data: ApiKeyBatchStatus, db: AsyncSession = Depends(get_db)):
    """批量修改API Key状态"""
    try:
        stmt = (
            update(ApiKey)
            .where(ApiKey.id.in_(batch_data.ids))
            .values(status=batch_data.status)
        )
        result = await db.execute(stmt)
        updated_count = result.rowcount
        await db.commit()

        return SuccessResponse(message=f"成功更新 {updated_count} 个API Key状态")

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"批量更新失败: {str(e)}")


@router.post("/test", response_model=BaseResponse)
async def test_api_key(test_data: ApiKeyTest, db: AsyncSession = Depends(get_db)):
    """测试API Key连接"""
    try:
        api_key = None
        model_url = None
        model_name = None
        key_value = None

        # 如果提供了ID，从数据库获取信息
        if test_data.id:
            stmt = select(ApiKey).where(ApiKey.id == test_data.id)
            result = await db.execute(stmt)
            api_key_obj = result.scalar_one_or_none()

            if not api_key_obj:
                raise HTTPException(status_code=404, detail="API Key不存在")

            key_value = api_key_obj.api_key
            model_url = api_key_obj.model_url
            model_name = api_key_obj.model_name
        else:
            # 使用提供的测试数据
            key_value = test_data.api_key
            model_url = test_data.model_url
            model_name = test_data.model_name

        if not all([key_value, model_url, model_name]):
            raise HTTPException(status_code=400, detail="缺少必要的测试参数")

        # 测试API连接
        start_time = time.time()

        headers = {
            "Authorization": f"Bearer {key_value}",
            "Content-Type": "application/json"
        }

        test_payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(model_url, headers=headers, json=test_payload)

        response_time = time.time() - start_time

        if response.status_code == 200:
            return BaseResponse(
                data=ApiKeyTestResponse(
                    success=True,
                    message="API Key测试成功",
                    response_time=response_time
                )
            )
        else:
            return BaseResponse(
                data=ApiKeyTestResponse(
                    success=False,
                    message=f"API Key测试失败: {response.status_code} - {response.text}",
                    response_time=response_time
                )
            )

    except httpx.TimeoutException:
        return BaseResponse(
            data=ApiKeyTestResponse(
                success=False,
                message="API Key测试超时"
            )
        )
    except Exception as e:
        return BaseResponse(
            data=ApiKeyTestResponse(
                success=False,
                message=f"API Key测试失败: {str(e)}"
            )
        )


@router.get("/stats", response_model=BaseResponse)
async def get_api_key_stats(db: AsyncSession = Depends(get_db)):
    """获取API Key统计信息"""
    try:
        # 总数统计
        total_stmt = select(func.count(ApiKey.id))
        total_result = await db.execute(total_stmt)
        total = total_result.scalar()

        # 活跃数量统计
        active_stmt = select(func.count(ApiKey.id)).where(ApiKey.status == "active")
        active_result = await db.execute(active_stmt)
        active = active_result.scalar()

        # 非活跃数量统计
        inactive_stmt = select(func.count(ApiKey.id)).where(ApiKey.status == "inactive")
        inactive_result = await db.execute(inactive_stmt)
        inactive = inactive_result.scalar()

        # 按提供商统计
        provider_stmt = (
            select(ApiKey.provider, func.count(ApiKey.id))
            .group_by(ApiKey.provider)
        )
        provider_result = await db.execute(provider_stmt)
        provider_stats = provider_result.all()

        providers = {}
        for provider, count in provider_stats:
            providers[provider or "unknown"] = count

        stats = ApiKeyStats(
            total=total,
            active=active,
            inactive=inactive,
            providers=providers
        )

        return BaseResponse(data=stats)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

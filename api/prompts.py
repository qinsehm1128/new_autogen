from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, func, delete, update
from typing import Optional, List
import json
from datetime import datetime

from database import get_db
from models.prompt import Prompt
from schemas import (
    PromptCreate,
    PromptUpdate,
    PromptResponse,
    PromptListQuery,
    PromptListResponse,
    PromptBatchDelete,
    PromptTest,
    PromptTestResponse,
    PromptCategory,
    PromptTag,
    BaseResponse,
    SuccessResponse
)

router = APIRouter(prefix="/chat/prompts", tags=["提示词管理"])


@router.get("/list", response_model=BaseResponse)
async def list_prompts(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类筛选"),
    tags: Optional[str] = Query(None, description="标签筛选"),
    beginTime: Optional[str] = Query(None, description="开始时间"),
    endTime: Optional[str] = Query(None, description="结束时间"),
    db: AsyncSession = Depends(get_db)
):
    """获取提示词列表"""
    try:
        # 构建查询条件
        conditions = []

        # 关键词搜索
        if keyword:
            conditions.append(
                or_(
                    Prompt.title.contains(keyword),
                    Prompt.content.contains(keyword),
                    Prompt.description.contains(keyword)
                )
            )

        # 分类筛选
        if category:
            conditions.append(Prompt.category == category)

        # 标签筛选
        if tags:
            tag_list = tags.split(",")
            for tag in tag_list:
                # 由于SQLite对JSON查询的限制，这里使用简单的字符串包含查询
                conditions.append(Prompt.tags.contains(tag.strip()))

        # 时间范围筛选
        if beginTime:
            conditions.append(Prompt.created_at >= datetime.fromisoformat(beginTime))
        if endTime:
            conditions.append(Prompt.created_at <= datetime.fromisoformat(endTime))

        # 构建查询语句
        where_clause = and_(*conditions) if conditions else True

        # 获取总数
        count_stmt = select(func.count(Prompt.id)).where(where_clause)
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()

        # 分页查询
        offset = (pageNum - 1) * pageSize
        query_stmt = (
            select(Prompt)
            .where(where_clause)
            .order_by(Prompt.sort.desc(), Prompt.created_at.desc())
            .offset(offset)
            .limit(pageSize)
        )

        result = await db.execute(query_stmt)
        items = result.scalars().all()

        # 构造响应数据
        response_data = PromptListResponse(
            total=total,
            items=[PromptResponse.from_orm(item) for item in items],
            pageNum=pageNum,
            pageSize=pageSize
        )

        return BaseResponse(data=response_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/categories", response_model=BaseResponse)
async def get_prompt_categories(db: AsyncSession = Depends(get_db)):
    """获取提示词分类列表"""
    try:
        # 预定义的分类
        predefined_categories = [
            {"value": "system", "label": "系统提示", "count": 0},
            {"value": "role", "label": "角色扮演", "count": 0},
            {"value": "creative", "label": "创意写作", "count": 0},
            {"value": "code", "label": "代码相关", "count": 0},
            {"value": "other", "label": "其他", "count": 0}
        ]

        # 统计每个分类的数量
        category_stmt = (
            select(Prompt.category, func.count(Prompt.id))
            .group_by(Prompt.category)
        )
        result = await db.execute(category_stmt)
        category_stats = result.all()

        category_counts = dict(category_stats)

        # 更新计数
        for category in predefined_categories:
            category["count"] = category_counts.get(category["value"], 0)

        categories = [PromptCategory(**cat) for cat in predefined_categories]
        return BaseResponse(data=categories)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类失败: {str(e)}")


@router.get("/tags", response_model=BaseResponse)
async def get_prompt_tags(db: AsyncSession = Depends(get_db)):
    """获取提示词标签列表"""
    try:
        # 获取所有提示词的标签
        stmt = select(Prompt).where(Prompt.tags.isnot(None))
        result = await db.execute(stmt)
        prompts = result.scalars().all()

        tag_counts = {}
        for prompt in prompts:
            if prompt.tags:
                tags = prompt.tags if isinstance(prompt.tags, list) else []
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # 按使用频率排序
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

        tags = [PromptTag(name=tag, count=count) for tag, count in sorted_tags]
        return BaseResponse(data=tags)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取标签失败: {str(e)}")


@router.get("/{prompt_id}", response_model=BaseResponse)
async def get_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
    """获取提示词详情"""
    stmt = select(Prompt).where(Prompt.id == prompt_id)
    result = await db.execute(stmt)
    prompt = result.scalar_one_or_none()

    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")

    return BaseResponse(data=PromptResponse.from_orm(prompt))


@router.post("", response_model=BaseResponse)
async def create_prompt(prompt_data: PromptCreate, db: AsyncSession = Depends(get_db)):
    """新增提示词"""
    try:
        # 检查提示词标题是否已存在
        existing_stmt = select(Prompt).where(Prompt.title == prompt_data.title)
        existing_result = await db.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()

        if existing:
            raise HTTPException(status_code=400, detail="该提示词标题已存在")

        # 创建新提示词
        db_prompt = Prompt(**prompt_data.dict())
        db.add(db_prompt)
        await db.commit()
        await db.refresh(db_prompt)

        return BaseResponse(
            message="提示词创建成功",
            data=PromptResponse.from_orm(db_prompt)
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.put("", response_model=BaseResponse)
async def update_prompt(prompt_data: PromptUpdate, db: AsyncSession = Depends(get_db)):
    """修改提示词"""
    try:
        stmt = select(Prompt).where(Prompt.id == prompt_data.id)
        result = await db.execute(stmt)
        prompt = result.scalar_one_or_none()

        if not prompt:
            raise HTTPException(status_code=404, detail="提示词不存在")

        # 检查标题是否与其他提示词重复
        if prompt_data.title and prompt_data.title != prompt.title:
            existing_stmt = select(Prompt).where(
                and_(Prompt.title == prompt_data.title, Prompt.id != prompt_data.id)
            )
            existing_result = await db.execute(existing_stmt)
            existing = existing_result.scalar_one_or_none()

            if existing:
                raise HTTPException(status_code=400, detail="该提示词标题已存在")

        # 更新字段
        update_data = prompt_data.dict(exclude_unset=True, exclude={"id"})
        for field, value in update_data.items():
            setattr(prompt, field, value)

        await db.commit()
        await db.refresh(prompt)

        return BaseResponse(
            message="提示词更新成功",
            data=PromptResponse.from_orm(prompt)
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/{prompt_id}", response_model=BaseResponse)
async def delete_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
    """删除提示词"""
    try:
        stmt = select(Prompt).where(Prompt.id == prompt_id)
        result = await db.execute(stmt)
        prompt = result.scalar_one_or_none()

        if not prompt:
            raise HTTPException(status_code=404, detail="提示词不存在")

        await db.delete(prompt)
        await db.commit()

        return SuccessResponse(message="提示词删除成功")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.delete("/batch", response_model=BaseResponse)
async def batch_delete_prompts(batch_data: PromptBatchDelete, db: AsyncSession = Depends(get_db)):
    """批量删除提示词"""
    try:
        stmt = delete(Prompt).where(Prompt.id.in_(batch_data.ids))
        result = await db.execute(stmt)
        deleted_count = result.rowcount
        await db.commit()

        return SuccessResponse(message=f"成功删除 {deleted_count} 个提示词")

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"批量删除失败: {str(e)}")


@router.post("/{prompt_id}/copy", response_model=BaseResponse)
async def copy_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
    """复制提示词"""
    try:
        stmt = select(Prompt).where(Prompt.id == prompt_id)
        result = await db.execute(stmt)
        source_prompt = result.scalar_one_or_none()

        if not source_prompt:
            raise HTTPException(status_code=404, detail="源提示词不存在")

        # 生成新的标题
        new_title = f"{source_prompt.title} - 副本"
        counter = 1
        while True:
            check_stmt = select(Prompt).where(Prompt.title == new_title)
            check_result = await db.execute(check_stmt)
            if not check_result.scalar_one_or_none():
                break
            counter += 1
            new_title = f"{source_prompt.title} - 副本({counter})"

        # 创建副本
        new_prompt = Prompt(
            title=new_title,
            category=source_prompt.category,
            content=source_prompt.content,
            description=source_prompt.description,
            tags=source_prompt.tags,
            is_public=False,  # 默认设为私有
            variables=source_prompt.variables,
            config=source_prompt.config,
            sort=source_prompt.sort
        )

        db.add(new_prompt)
        await db.commit()
        await db.refresh(new_prompt)

        return BaseResponse(
            message="提示词复制成功",
            data=PromptResponse.from_orm(new_prompt)
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"复制失败: {str(e)}")


@router.post("/test", response_model=BaseResponse)
async def test_prompt(test_data: PromptTest):
    """测试提示词"""
    try:
        content = test_data.content
        variables = test_data.variables or {}
        test_input = test_data.testInput

        # 简单的变量替换测试
        result_content = content
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            result_content = result_content.replace(placeholder, str(var_value))

        # 组合测试输入
        final_result = f"{result_content}\n\n用户输入: {test_input}"

        response_data = PromptTestResponse(
            success=True,
            message="提示词测试成功",
            result=final_result
        )

        return BaseResponse(data=response_data)

    except Exception as e:
        response_data = PromptTestResponse(
            success=False,
            message=f"提示词测试失败: {str(e)}",
            result=None
        )
        return BaseResponse(data=response_data)

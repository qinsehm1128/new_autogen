# 聊天API接口文档

本文档描述了新增的聊天相关API接口，这些接口完全对应前端 `web/src/api/chat.js` 中定义的接口需求。

## 新增模型

### 1. 数据库模型

- **Conversation**: 对话模型（已扩展）
  - 新增字段：`group_id`（分组ID）、`description`（描述）、`config`（配置）

- **Message**: 消息模型（新增）
  - 存储对话中的所有消息
  - 支持不同角色：user/assistant/system
  - 支持多种消息类型：text/image/file

- **ChatGroup**: 对话分组模型（新增）
  - 管理对话的分组和分类
  - 支持默认分组



### 2. Schema模型

所有接口的请求和响应模型都定义在 `schemas/conversation.py` 中，包括：
- 对话相关：ConversationCreate, ConversationUpdate, ConversationResponse 等
- 消息相关：MessageCreate, MessageEdit, MessageResponse 等
- 分组相关：ChatGroupCreate, ChatGroupUpdate, ChatGroupResponse 等
- 其他：搜索、导出、设置等相关模型

## API接口列表

### 对话管理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/chat/conversations/list` | 获取对话列表（支持分页、搜索、筛选） |
| GET | `/chat/conversations/{chat_id}` | 获取对话详情 |
| POST | `/chat/conversations` | 创建新对话 |
| PUT | `/chat/conversations/{chat_id}` | 更新对话信息 |
| DELETE | `/chat/conversations/{chat_id}` | 删除对话 |
| DELETE | `/chat/conversations/batch` | 批量删除对话 |
| DELETE | `/chat/conversations/{chat_id}/messages` | 清空对话消息 |
| PUT | `/chat/conversations/{chat_id}/move` | 移动对话到分组 |
| PUT | `/chat/conversations/batch/move` | 批量移动对话到分组 |

### 消息管理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/chat/conversations/{chat_id}/messages` | 获取对话消息列表 |
| POST | `/chat/messages` | 发送消息 |
| DELETE | `/chat/messages/{message_id}` | 删除消息 |
| PUT | `/chat/messages/{message_id}` | 编辑消息 |
| POST | `/chat/messages/regenerate` | 重新生成消息 |
| POST | `/chat/messages/stream` | 流式消息接口（SSE） |
| POST | `/chat/messages/stream/cancel` | 取消流式消息生成 |

### 对话分组管理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/chat/groups` | 获取对话分组列表 |
| POST | `/chat/groups` | 创建对话分组 |
| PUT | `/chat/groups/{group_id}` | 更新对话分组 |
| DELETE | `/chat/groups/{group_id}` | 删除对话分组 |



### 搜索接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/chat/search` | 搜索对话和消息 |



### 设置接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/chat/settings` | 获取用户聊天设置 |
| PUT | `/chat/settings` | 更新用户聊天设置 |

### 导出导入接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/chat/export` | 导出对话 |
| POST | `/chat/export/batch` | 批量导出对话 |
| POST | `/chat/import` | 导入对话 |

### 实用工具接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/chat/utils/generate-title` | 生成对话标题 |
| GET | `/chat/statistics` | 获取对话统计信息 |

### 流式接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/chat/messages/stream` | SSE流式消息接口（替代WebSocket） |
| POST | `/chat/messages/stream/cancel` | 取消流式消息生成 |

## 数据库迁移

### 运行迁移

```bash
python run_migration.py
```

这个脚本会：
1. 创建新的表：`chat_groups`、`messages`
2. 为 `conversations` 表添加新字段
3. 创建必要的索引
4. 插入默认分组
5. 更新现有对话的分组关联

### 迁移文件

- `migrations/add_chat_models.sql`: 包含所有数据库结构变更的SQL语句

## 测试

### 运行API测试

```bash
python test_chat_api.py
```

这个脚本会测试所有新增的API接口，包括：
- 分组管理
- 对话管理
- 消息管理
- 搜索功能
- 模型管理
- 设置管理
- 实用工具

## 使用示例

### 创建对话分组

```python
import requests

# 创建分组
response = requests.post("http://localhost:8000/chat/groups", json={
    "name": "工作对话",
    "description": "与工作相关的对话",
    "color": "#2196F3",
    "sort": 1
})
```

### 创建对话

```python
# 创建对话
response = requests.post("http://localhost:8000/chat/conversations", json={
    "title": "项目讨论",
    "description": "关于新项目的讨论",
    "model_id": "gpt-3.5-turbo",
    "group_id": 1
})
```

### 发送消息

```python
# 发送消息
response = requests.post("http://localhost:8000/chat/messages", json={
    "chat_id": "conversation-uuid",
    "content": "你好，请帮我分析一下这个项目的可行性",
    "message_type": "text"
})
```

### 发送流式消息

```python
# 发送流式消息
response = requests.post("http://localhost:8000/chat/messages/stream", json={
    "chat_id": "conversation-uuid",
    "content": "你好，请帮我分析一下这个项目的可行性",
    "message_type": "text"
})

# 获取任务ID
task_id = response.headers.get('X-Task-ID')

# 取消流式生成
requests.post("http://localhost:8000/chat/messages/stream/cancel", params={
    "task_id": task_id
})
```

### 搜索对话

```python
# 搜索对话
response = requests.get("http://localhost:8000/chat/search", params={
    "keyword": "项目",
    "type": "all",
    "pageNum": 1,
    "pageSize": 10
})
```

## 注意事项

1. **数据库兼容性**: 新的模型结构向后兼容，不会影响现有数据
2. **流式响应**: 使用SSE（Server-Sent Events）替代WebSocket，支持任务取消功能
3. **任务管理**: 每个流式请求都有唯一的任务ID，可以通过API取消正在进行的生成
4. **错误处理**: 所有接口都包含完整的错误处理和验证
5. **分页支持**: 列表接口都支持分页查询
6. **软删除**: 删除操作使用软删除，数据不会真正从数据库中移除

## 后续扩展

这个API框架为以下功能预留了扩展空间：
- 消息的富文本支持
- 对话模板管理
- 用户权限管理
- 对话分享功能
- 更复杂的搜索和筛选
- 实时协作功能

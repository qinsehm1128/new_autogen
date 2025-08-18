-- PostgreSQL数据库结构
-- 基于API目录下的所有模型定义
-- 创建时间: 2024年

-- 删除已存在的表（按依赖关系逆序）
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS chat_groups CASCADE;
DROP TABLE IF EXISTS prompts CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;

-- 创建扩展（如果需要UUID支持）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. API密钥表
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    api_key VARCHAR(500) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_url VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    provider VARCHAR(50),
    config JSONB,
    max_tokens INTEGER,
    timeout INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 为api_keys表添加注释
COMMENT ON TABLE api_keys IS 'API密钥管理表';
COMMENT ON COLUMN api_keys.id IS '主键ID';
COMMENT ON COLUMN api_keys.api_key IS 'API密钥';
COMMENT ON COLUMN api_keys.model_name IS '模型名称';
COMMENT ON COLUMN api_keys.model_url IS '模型地址';
COMMENT ON COLUMN api_keys.description IS '描述';
COMMENT ON COLUMN api_keys.status IS '状态：active/inactive';
COMMENT ON COLUMN api_keys.provider IS '提供商：openai/anthropic/google等';
COMMENT ON COLUMN api_keys.config IS '额外配置';
COMMENT ON COLUMN api_keys.max_tokens IS '最大Token数';
COMMENT ON COLUMN api_keys.timeout IS '超时时间（秒）';
COMMENT ON COLUMN api_keys.created_at IS '创建时间';
COMMENT ON COLUMN api_keys.updated_at IS '更新时间';

-- 2. 提示词表
CREATE TABLE prompts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('system', 'role', 'creative', 'code', 'other')),
    content TEXT NOT NULL,
    description TEXT,
    tags JSONB,
    is_public BOOLEAN DEFAULT FALSE,
    variables JSONB,
    config JSONB,
    sort INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 为prompts表添加注释
COMMENT ON TABLE prompts IS '提示词管理表';
COMMENT ON COLUMN prompts.id IS '主键ID';
COMMENT ON COLUMN prompts.title IS '提示词标题';
COMMENT ON COLUMN prompts.category IS '分类：system/role/creative/code/other';
COMMENT ON COLUMN prompts.content IS '提示词内容';
COMMENT ON COLUMN prompts.description IS '描述';
COMMENT ON COLUMN prompts.tags IS '标签数组';
COMMENT ON COLUMN prompts.is_public IS '是否公开';
COMMENT ON COLUMN prompts.variables IS '变量定义';
COMMENT ON COLUMN prompts.config IS '额外配置';
COMMENT ON COLUMN prompts.sort IS '排序值';
COMMENT ON COLUMN prompts.created_at IS '创建时间';
COMMENT ON COLUMN prompts.updated_at IS '更新时间';

-- 3. 对话分组表
CREATE TABLE chat_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    color VARCHAR(20),
    sort INTEGER DEFAULT 0,
    is_default INTEGER DEFAULT 0 CHECK (is_default IN (0, 1)),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'deleted')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 为chat_groups表添加注释
COMMENT ON TABLE chat_groups IS '对话分组表';
COMMENT ON COLUMN chat_groups.id IS '主键ID';
COMMENT ON COLUMN chat_groups.name IS '分组名称';
COMMENT ON COLUMN chat_groups.description IS '分组描述';
COMMENT ON COLUMN chat_groups.color IS '分组颜色';
COMMENT ON COLUMN chat_groups.sort IS '排序值';
COMMENT ON COLUMN chat_groups.is_default IS '是否默认分组：0否/1是';
COMMENT ON COLUMN chat_groups.status IS '状态：active/deleted';
COMMENT ON COLUMN chat_groups.created_at IS '创建时间';
COMMENT ON COLUMN chat_groups.updated_at IS '更新时间';

-- 4. 对话表
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    api_key_id INTEGER NOT NULL,
    prompt_id INTEGER NOT NULL,
    group_id INTEGER REFERENCES chat_groups(id) ON DELETE SET NULL,
    title VARCHAR(200),
    description TEXT,
    config JSONB,
    agent_state JSONB,
    message_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 为conversations表添加注释
COMMENT ON TABLE conversations IS '对话表';
COMMENT ON COLUMN conversations.id IS '主键ID';
COMMENT ON COLUMN conversations.uuid IS '对话唯一标识';
COMMENT ON COLUMN conversations.api_key_id IS '使用的API密钥ID';
COMMENT ON COLUMN conversations.prompt_id IS '使用的提示词ID';
COMMENT ON COLUMN conversations.group_id IS '分组ID';
COMMENT ON COLUMN conversations.title IS '对话标题';
COMMENT ON COLUMN conversations.description IS '对话描述';
COMMENT ON COLUMN conversations.config IS '对话配置';
COMMENT ON COLUMN conversations.agent_state IS 'Agent状态数据';
COMMENT ON COLUMN conversations.message_count IS '消息数量';
COMMENT ON COLUMN conversations.status IS '状态：active/archived/deleted';
COMMENT ON COLUMN conversations.created_at IS '创建时间';
COMMENT ON COLUMN conversations.updated_at IS '更新时间';

-- 5. 消息表
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text' CHECK (message_type IN ('text', 'image', 'file')),
    message_metadata JSONB,
    token_count INTEGER DEFAULT 0,
    character_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'deleted')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 为messages表添加注释
COMMENT ON TABLE messages IS '消息表';
COMMENT ON COLUMN messages.id IS '主键ID';
COMMENT ON COLUMN messages.uuid IS '消息唯一标识';
COMMENT ON COLUMN messages.conversation_id IS '对话ID';
COMMENT ON COLUMN messages.role IS '角色：user/assistant/system';
COMMENT ON COLUMN messages.content IS '消息内容';
COMMENT ON COLUMN messages.message_type IS '消息类型：text/image/file';
COMMENT ON COLUMN messages.message_metadata IS '消息元数据';
COMMENT ON COLUMN messages.token_count IS 'Token数量';
COMMENT ON COLUMN messages.character_count IS '字符数量';
COMMENT ON COLUMN messages.status IS '状态：active/deleted';
COMMENT ON COLUMN messages.created_at IS '创建时间';
COMMENT ON COLUMN messages.updated_at IS '更新时间';

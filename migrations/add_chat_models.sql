-- 添加聊天相关的新表和字段

-- 1. 创建聊天分组表
CREATE TABLE IF NOT EXISTS chat_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL COMMENT '分组名称',
    description TEXT COMMENT '分组描述',
    color VARCHAR(20) COMMENT '分组颜色',
    sort INTEGER DEFAULT 0 COMMENT '排序值',
    is_default INTEGER DEFAULT 0 COMMENT '是否默认分组：0否/1是',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态：active/deleted',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间'
);

-- 2. 创建消息表
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid VARCHAR(36) UNIQUE NOT NULL COMMENT '消息唯一标识',
    conversation_id INTEGER NOT NULL COMMENT '对话ID',
    role VARCHAR(20) NOT NULL COMMENT '角色：user/assistant/system',
    content TEXT NOT NULL COMMENT '消息内容',
    message_type VARCHAR(20) DEFAULT 'text' COMMENT '消息类型：text/image/file',
    message_metadata JSON COMMENT '消息元数据',
    token_count INTEGER DEFAULT 0 COMMENT 'Token数量',
    character_count INTEGER DEFAULT 0 COMMENT '字符数量',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态：active/deleted',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);



-- 4. 修改conversations表，添加新字段
ALTER TABLE conversations ADD COLUMN group_id INTEGER COMMENT '分组ID';
ALTER TABLE conversations ADD COLUMN description TEXT COMMENT '对话描述';
ALTER TABLE conversations ADD COLUMN config JSON COMMENT '对话配置';

-- 5. 创建索引
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_uuid ON messages(uuid);
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);



CREATE INDEX IF NOT EXISTS idx_conversations_group_id ON conversations(group_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at);

CREATE INDEX IF NOT EXISTS idx_chat_groups_status ON chat_groups(status);
CREATE INDEX IF NOT EXISTS idx_chat_groups_sort ON chat_groups(sort);

-- 6. 插入默认分组
INSERT OR IGNORE INTO chat_groups (name, description, is_default, sort) 
VALUES ('默认分组', '系统默认分组', 1, 0);

-- 7. 更新现有对话的分组ID为默认分组
UPDATE conversations 
SET group_id = (SELECT id FROM chat_groups WHERE is_default = 1 LIMIT 1)
WHERE group_id IS NULL;

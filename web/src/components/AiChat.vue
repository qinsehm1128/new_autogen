<template>
    <div class="ai-chat">
        <!-- 左侧会话列表（提取为组件） -->
        <ChatSidebar
            v-model:activeGroups="activeGroups"
            :chatGroups="chatGroups"
            :currentChatId="currentChatId"
            :loadingStates="loadingStates"
            :formatTime="formatTime"
            @new-chat="handleNewChat"
            @group-command="handleGroupCommand"
            @select-chat="selectChat"
            @chat-command="
                ({ command, chat }) => handleChatCommand(command, chat)
            "
        />

        <!-- 右侧对话区域（提取为组件） -->
        <ChatMain
            ref="chatMainRef"
            :currentChat="currentChat"
            :currentMessages="currentMessages"
            :availableModels="availableModels"
            :availablePrompts="availablePrompts"
            :selectedModel="selectedModel"
            :selectedPrompt="selectedPrompt"
            :selectedModelName="selectedModelName"
            :isLoading="loadingStates.sending"
            :hasStreamingMessage="hasStreamingMessage"
            :hasWaitingMessage="hasWaitingMessage"
            :isSendingMessage="isSendingMessage"
            :loadingStates="loadingStates"
            placeholder="输入你的问题..."
            :formatTime="formatTime"
            @new-chat="handleNewChat"
            @model-change="handleModelChange"
            @prompt-change="(promptId) => selectedPrompt = promptId"
            @clear-chat="handleClearChat"
            @export-chat="handleExportChat"
            @send-message="handleSendMessage"
            @cancel-request="handleCancelRequest"
            @copy-message="copyMessage"
            @regenerate-response="regenerateResponse"
        />

        <!-- 管理相关对话框（提取为组件） -->
        <ChatManagementDialogs
            v-model:groupDialogVisible="groupDialogVisible"
            v-model:renameDialogVisible="renameDialogVisible"
            v-model:moveDialogVisible="moveDialogVisible"
            v-model:newGroupName="newGroupName"
            v-model:newChatTitle="newChatTitle"
            v-model:targetGroupId="targetGroupId"
            :chatGroups="chatGroups"
            @create-group="handleCreateGroup"
            @rename-chat="handleRenameChat"
            @move-chat="handleMoveChat"
        />
    </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import ChatMain from "./chat/ChatMain.vue";
import ChatManagementDialogs from "./chat/ChatManagementDialogs.vue";
import ChatSidebar from "./chat/ChatSidebar.vue";
import {
    Plus,
    FolderOpened,
    Folder,
    Setting,
    MoreFilled,
    Delete,
    Download,
    ChatRound,
    User,
    Service,
    CopyDocument,
    Refresh,
} from "@element-plus/icons-vue";
import { MdPreview } from "md-editor-v3";
import "md-editor-v3/lib/preview.css";

// 导入API接口
import {
    getChatList,
    getChatDetail,
    createChat,
    updateChat,
    deleteChat,
    getChatMessages,
    sendStreamMessage,
    cancelStreamMessage,
    clearChatMessages,
    getChatGroups,
    createChatGroup,
    updateChatGroup,
    deleteChatGroup
} from "@/api/chat";
import { listApiKeys, listPrompts } from "@/api/chat_config";

// 响应式数据
const editorRef = ref();
const chatMainRef = ref(null);
const isLoading = ref(false);
const currentChatId = ref(null);
const selectedModel = ref("");
const selectedPrompt = ref(null);
const activeGroups = ref(["default"]);

// 流式消息控制
const streamController = ref(null);
const currentTaskId = ref(null);

// 加载状态
const loadingStates = reactive({
    groups: false,
    models: false,
    prompts: false,
    messages: false,
    sending: false
});

// 对话框控制
const groupDialogVisible = ref(false);
const renameDialogVisible = ref(false);
const moveDialogVisible = ref(false);
const newGroupName = ref("");
const newChatTitle = ref("");
const targetGroupId = ref("");
const currentOperatingChat = ref(null);

// 真实数据
const availableModels = ref([]);
const availablePrompts = ref([]);
const chatGroups = ref([]);
const messages = ref({});

// 计算属性
const currentChat = computed(() => {
    if (!currentChatId.value) return null;

    for (const group of chatGroups.value) {
        const chat = group.chats.find((c) => c.id === currentChatId.value);
        if (chat) return chat;
    }
    return null;
});

const currentMessages = computed(() => {
    if (!currentChatId.value) return [];
    return messages.value[currentChatId.value] || [];
});

const selectedModelName = computed(() => {
    const model = availableModels.value.find(
        (m) => m.id === selectedModel.value,
    );
    return model ? model.name : "";
});

// 是否存在正在流式输出的助手消息（用于控制加载占位显示）
const hasStreamingMessage = computed(() => {
    const list = currentMessages.value || [];
    return list.some((m) => m.role === "assistant" && m.streaming);
});

// 是否有等待中的消息
const hasWaitingMessage = computed(() => {
    const list = currentMessages.value || [];
    return list.some((m) => m.role === "assistant" && m.waiting);
});

// 是否正在发送消息（包括等待和流式）
const isSendingMessage = computed(() => {
    return loadingStates.sending || hasStreamingMessage.value || hasWaitingMessage.value;
});

// 方法
const formatTime = (timestamp) => {
    const now = new Date().getTime();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (days > 0) return `${days}天前`;
    if (hours > 0) return `${hours}小时前`;
    if (minutes > 0) return `${minutes}分钟前`;
    return "刚刚";
};

const formatMessage = (content) => {
    // 简单的markdown渲染
    return content
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>")
        .replace(/`(.*?)`/g, "<code>$1</code>")
        .replace(/\n/g, "<br>");
};

const selectChat = (chat) => {
    currentChatId.value = chat.id;
    selectedModel.value = chat.modelId || availableModels.value[0]?.id;
    nextTick(() => {
        scrollToBottom();
    });
};

const scrollToBottom = () => {
    if (
        chatMainRef.value &&
        typeof chatMainRef.value.scrollToBottom === "function"
    ) {
        chatMainRef.value.scrollToBottom();
    }
};

// ==================== 数据加载方法 ====================

/**
 * 加载可用模型列表
 */
const loadAvailableModels = async () => {
    try {
        loadingStates.models = true;
        const response = await listApiKeys({ status: 'active' });
        if (response.code === 200) {
            availableModels.value = response.data.items.map(item => ({
                id: item.id,                    // API Key ID (数字)
                name: item.model_name,          // 模型名称显示
                provider: item.provider,
                status: item.status
            }));

            // 设置默认选中的模型（使用API Key ID）
            if (availableModels.value.length > 0 && !selectedModel.value) {
                selectedModel.value = availableModels.value[0].id;
            }
        }
    } catch (error) {
        console.error('加载模型列表失败:', error);
        ElMessage.error('加载模型列表失败');
    } finally {
        loadingStates.models = false;
    }
};

/**
 * 加载可用提示词列表
 */
const loadAvailablePrompts = async () => {
    try {
        loadingStates.prompts = true;
        const response = await listPrompts({ status: 'active' });
        if (response.code === 200) {
            availablePrompts.value = response.data.items;

            // 设置默认选中的提示词
            if (availablePrompts.value.length > 0 && !selectedPrompt.value) {
                selectedPrompt.value = availablePrompts.value[0].id;
            }
        }
    } catch (error) {
        console.error('加载提示词列表失败:', error);
        ElMessage.error('加载提示词列表失败');
    } finally {
        loadingStates.prompts = false;
    }
};

/**
 * 加载对话分组和对话列表
 */
const loadChatGroups = async () => {
    try {
        loadingStates.groups = true;
        const response = await getChatGroups({ include_chats: true });
        if (response.code === 200) {
            chatGroups.value = response.data.map(group => ({
                id: group.id,
                name: group.name,
                description: group.description,
                color: group.color,
                chats: (group.conversations || []).map(chat => ({
                    id: chat.uuid,
                    title: chat.title,
                    lastMessage: '', // 需要从最后一条消息获取
                    updateTime: new Date(chat.updated_at).getTime(),
                    modelId: chat.api_key_id,
                    messageCount: chat.message_count
                }))
            }));
        }
    } catch (error) {
        console.error('加载对话分组失败:', error);
        ElMessage.error('加载对话分组失败');
    } finally {
        loadingStates.groups = false;
    }
};

/**
 * 加载指定对话的消息历史
 */
const loadChatMessages = async (chatId) => {
    try {
        loadingStates.messages = true;
        const response = await getChatMessages(chatId, { pageSize: 100 });
        if (response.code === 200) {
            messages.value[chatId] = response.data.list.map(msg => ({
                id: msg.uuid,
                role: msg.role,
                content: msg.content,
                timestamp: new Date(msg.created_at).getTime(),
                messageType: msg.message_type
            }));
        }
    } catch (error) {
        console.error('加载消息历史失败:', error);
        ElMessage.error('加载消息历史失败');
    } finally {
        loadingStates.messages = false;
    }
};

/**
 * 初始化数据
 */
const initializeData = async () => {
    await Promise.all([
        loadAvailableModels(),
        loadAvailablePrompts(),
        loadChatGroups()
    ]);
};

// ==================== 对话操作方法 ====================

const handleNewChat = async () => {
    try {
        if (!selectedModel.value) {
            ElMessage.warning('请先选择一个模型');
            return;
        }

        if (!selectedPrompt.value) {
            ElMessage.warning('请先选择一个提示词');
            return;
        }

        const chatData = {
            title: "新对话",
            api_key_id: selectedModel.value,      // 使用API Key ID（数字）
            prompt_id: selectedPrompt.value,
            group_id: chatGroups.value[0]?.id     // 默认分组
        };

        const response = await createChat(chatData);
        if (response.code === 200) {
            const newChat = {
                id: response.data.uuid,
                title: response.data.title,
                lastMessage: "",
                updateTime: new Date(response.data.created_at).getTime(),
                modelId: selectedModel.value,
                messageCount: 0
            };

            // 添加到默认分组
            if (chatGroups.value.length > 0) {
                chatGroups.value[0].chats.unshift(newChat);
            }

            messages.value[newChat.id] = [];
            currentChatId.value = newChat.id;

            ElMessage.success('新对话创建成功');
        }
    } catch (error) {
        console.error('创建对话失败:', error);
        ElMessage.error('创建对话失败');
    }
};

const handleSendMessage = async (payload) => {
    if (!currentChatId.value || !selectedModel.value) {
        ElMessage.warning("请先选择模型");
        return;
    }

    if (loadingStates.sending) {
        ElMessage.warning("正在发送消息，请稍候");
        return;
    }

    // 准备消息数据
    const messageData = {
        chat_id: currentChatId.value,
        content: payload.text,
        message_type: "text",
        message_metadata: {}
    };

    // 创建用户消息显示
    const userMessage = {
        id: `msg-${Date.now()}`,
        role: "user",
        content: payload.text,
        timestamp: new Date().getTime(),
    };

    // 添加用户消息到界面
    if (!messages.value[currentChatId.value]) {
        messages.value[currentChatId.value] = [];
    }
    messages.value[currentChatId.value].push(userMessage);

    // 创建助手消息占位符
    const assistantMessage = reactive({
        id: `msg-${Date.now() + 1}`,
        role: "assistant",
        content: "",
        timestamp: new Date().getTime(),
        streaming: true,
        waiting: true,  // 新增：等待SSE数据状态
    });
    messages.value[currentChatId.value].push(assistantMessage);

    loadingStates.sending = true;

    try {
        // 发送流式消息
        const { taskId, cancel } = await sendStreamMessage(
            messageData,
            (data) => {
                // 处理流式数据
                if (data.type === 'chunk') {
                    // 收到第一个chunk时，取消等待状态
                    if (assistantMessage.waiting) {
                        assistantMessage.waiting = false;
                    }
                    assistantMessage.content += data.content;
                } else if (data.type === 'user_message') {
                    // 用户消息确认，可以更新消息ID
                    userMessage.id = data.message_id;
                } else if (data.type === 'assistant_start') {
                    // 助手消息开始，更新消息ID
                    assistantMessage.id = data.message_id;
                    // 收到assistant_start时，也取消等待状态
                    if (assistantMessage.waiting) {
                        assistantMessage.waiting = false;
                    }
                }
            },
            (error) => {
                console.error('流式消息错误:', error);
                ElMessage.error('发送消息失败');
                assistantMessage.content = '抱歉，消息发送失败，请重试。';
                assistantMessage.streaming = false;
                assistantMessage.waiting = false;  // 清理等待状态
            },
            (data) => {
                // 流式完成
                assistantMessage.streaming = false;
                assistantMessage.waiting = false;  // 清理等待状态
                if (data && data.content) {
                    assistantMessage.content = data.content;
                }

                // 更新对话信息
                const chat = currentChat.value;
                if (chat) {
                    if (chat.title === "新对话" && payload.text.length > 0) {
                        chat.title = payload.text.substring(0, 20) +
                                   (payload.text.length > 20 ? "..." : "");
                    }
                    chat.lastMessage = payload.text;
                    chat.updateTime = new Date().getTime();
                }
            }
        );

        // 保存流控制器和任务ID
        streamController.value = cancel;
        currentTaskId.value = taskId;

    } catch (error) {
        console.error('发送消息失败:', error);
        ElMessage.error("发送消息失败");
        assistantMessage.content = '抱歉，消息发送失败，请重试。';
        assistantMessage.streaming = false;
        assistantMessage.waiting = false;  // 清理等待状态
    } finally {
        loadingStates.sending = false;
    }

    nextTick(() => {
        scrollToBottom();
    });
};

const handleCancelRequest = async () => {
    try {
        if (currentTaskId.value) {
            await cancelStreamMessage(currentTaskId.value);
            ElMessage.info('已取消消息生成');
        }

        if (streamController.value) {
            streamController.value();
        }

        // 清理状态
        currentTaskId.value = null;
        streamController.value = null;
        loadingStates.sending = false;

    } catch (error) {
        console.error('取消消息失败:', error);
        ElMessage.error('取消消息失败');
    }
};

const handleModelChange = (modelId) => {
    if (currentChat.value) {
        currentChat.value.modelId = modelId;
    }
};

const handleClearChat = async () => {
    try {
        await ElMessageBox.confirm("确定要清空当前对话吗？", "清空对话", {
            confirmButtonText: "确定",
            cancelButtonText: "取消",
            type: "warning",
        });

        if (currentChatId.value) {
            // 调用API清空对话消息
            const response = await clearChatMessages(currentChatId.value);
            if (response.code === 200) {
                messages.value[currentChatId.value] = [];
                if (currentChat.value) {
                    currentChat.value.lastMessage = "";
                    currentChat.value.messageCount = 0;
                }
                ElMessage.success("对话已清空");
            }
        }
    } catch (error) {
        if (error !== 'cancel') {
            console.error('清空对话失败:', error);
            ElMessage.error('清空对话失败');
        }
    }
};

const handleExportChat = () => {
    if (!currentChat.value || !currentMessages.value.length) {
        ElMessage.warning("没有可导出的对话内容");
        return;
    }

    const exportData = {
        title: currentChat.value.title,
        model: selectedModelName.value,
        exportTime: new Date().toLocaleString(),
        messages: currentMessages.value,
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: "application/json",
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${currentChat.value.title}-${Date.now()}.json`;
    link.click();
    window.URL.revokeObjectURL(url);

    ElMessage.success("对话已导出");
};

const copyMessage = async (content) => {
    try {
        await navigator.clipboard.writeText(content);
        ElMessage.success("内容已复制到剪贴板");
    } catch {
        ElMessage.error("复制失败");
    }
};

const regenerateResponse = (message) => {
    // 重新生成响应的逻辑
    ElMessage.info("重新生成功能开发中...");
};

// 分组管理
const handleGroupCommand = (command) => {
    switch (command) {
        case "new-group":
            groupDialogVisible.value = true;
            newGroupName.value = "";
            break;
        case "manage-groups":
            ElMessage.info("分组管理功能开发中...");
            break;
    }
};

const handleCreateGroup = async () => {
    if (!newGroupName.value.trim()) {
        ElMessage.warning("请输入分组名称");
        return;
    }

    try {
        const groupData = {
            name: newGroupName.value,
            description: `用户创建的分组：${newGroupName.value}`
        };

        const response = await createChatGroup(groupData);
        if (response.code === 200) {
            const newGroup = {
                id: response.data.id,
                name: response.data.name,
                description: response.data.description,
                chats: [],
            };

            chatGroups.value.push(newGroup);
            groupDialogVisible.value = false;
            ElMessage.success("分组创建成功");
        }
    } catch (error) {
        console.error('创建分组失败:', error);
        ElMessage.error('创建分组失败');
    }
};

// 对话管理
const handleChatCommand = (command, chat) => {
    currentOperatingChat.value = chat;

    switch (command) {
        case "rename":
            newChatTitle.value = chat.title;
            renameDialogVisible.value = true;
            break;
        case "move":
            targetGroupId.value = "";
            moveDialogVisible.value = true;
            break;
        case "delete":
            handleDeleteChat(chat);
            break;
    }
};

const handleRenameChat = async () => {
    if (!newChatTitle.value.trim()) {
        ElMessage.warning("请输入对话标题");
        return;
    }

    if (!currentOperatingChat.value) return;

    try {
        // 调用API更新对话标题
        const response = await updateChat(currentOperatingChat.value.id, { title: newChatTitle.value });
        if (response.code === 200) {
            currentOperatingChat.value.title = newChatTitle.value;
            renameDialogVisible.value = false;
            ElMessage.success("重命名成功");
        }
    } catch (error) {
        console.error('重命名对话失败:', error);
        ElMessage.error('重命名对话失败');
    }
};

const handleMoveChat = async () => {
    if (!targetGroupId.value) {
        ElMessage.warning("请选择目标分组");
        return;
    }

    const chat = currentOperatingChat.value;
    if (!chat) return;

    try {
        // 调用API移动对话
        const response = await updateChat(chat.id, { group_id: targetGroupId.value });
        if (response.code === 200) {
            // 从原分组移除
            for (const group of chatGroups.value) {
                const index = group.chats.findIndex((c) => c.id === chat.id);
                if (index > -1) {
                    group.chats.splice(index, 1);
                    break;
                }
            }

            // 添加到目标分组
            const targetGroup = chatGroups.value.find(
                (g) => g.id === targetGroupId.value,
            );
            if (targetGroup) {
                targetGroup.chats.unshift(chat);
            }

            moveDialogVisible.value = false;
            ElMessage.success("移动成功");
        }
    } catch (error) {
        console.error('移动对话失败:', error);
        ElMessage.error('移动对话失败');
    }
};

const handleDeleteChat = async (chat) => {
    try {
        await ElMessageBox.confirm(
            `确定要删除对话"${chat.title}"吗？`,
            "删除确认",
            {
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                type: "warning",
            },
        );

        // 调用API删除对话
        const response = await deleteChat(chat.id);
        if (response.code === 200) {
            // 从分组中移除
            for (const group of chatGroups.value) {
                const index = group.chats.findIndex((c) => c.id === chat.id);
                if (index > -1) {
                    group.chats.splice(index, 1);
                    break;
                }
            }

            // 删除消息记录
            delete messages.value[chat.id];

            // 如果删除的是当前对话，清空选中状态
            if (currentChatId.value === chat.id) {
                currentChatId.value = null;
            }

            ElMessage.success("对话已删除");
        }
    } catch (error) {
        if (error !== 'cancel') {
            console.error('删除对话失败:', error);
            ElMessage.error('删除对话失败');
        }
    }
};

// 监听当前对话变化，加载消息历史
watch(currentChatId, async (newChatId, oldChatId) => {
    if (newChatId && newChatId !== oldChatId) {
        // 如果消息还没有加载过，则加载
        if (!messages.value[newChatId]) {
            await loadChatMessages(newChatId);
        }

        // 滚动到底部
        nextTick(() => {
            scrollToBottom();
        });
    }
});

// 监听消息变化，自动滚动到底部
watch(
    currentMessages,
    () => {
        nextTick(() => {
            scrollToBottom();
        });
    },
    { deep: true },
);

// 初始化
onMounted(async () => {
    // 初始化数据
    await initializeData();

    // 如果有对话，选择第一个
    if (chatGroups.value.length > 0) {
        for (const group of chatGroups.value) {
            if (group.chats && group.chats.length > 0) {
                currentChatId.value = group.chats[0].id;
                break;
            }
        }
    }
});
</script>

<style scoped>
.ai-chat {
    display: flex;
    height: 100%;
    background-color: #f5f5f5;
}

/* 左侧边栏 */
.chat-sidebar {
    width: 320px;
    background-color: #fff;
    border-right: 1px solid #e4e7ed;
    display: flex;
    flex-direction: column;
}

.sidebar-header {
    padding: 20px;
    border-bottom: 1px solid #e4e7ed;
    display: flex;
    gap: 10px;
    align-items: center;
}

.new-chat-btn {
    flex: 1;
}

.group-btn {
    padding: 8px;
}

/* 分组列表外层：只允许纵向滚动，禁止横向 */
.chat-groups {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden; /* 新增 */
    /* 移除 width: 100%; 如无必要 */
}

.group-title {
    display: flex;
    align-items: center;
    gap: 8px;
    /* 移除 width: 100%; */
    flex: 1; /* 新增：让其占据剩余空间 */
    min-width: 0; /* 新增：避免内容把宽度撑爆 */
    box-sizing: border-box; /* 新增：宽度计算包含 padding */
}
.chat-count {
    color: #909399;
    font-size: 12px;
}

.chat-list {
    padding: 0 16px;
}

.chat-item {
    display: flex;
    align-items: center;
    padding: 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s;
    margin-bottom: 4px;
}

.chat-item:hover {
    background-color: #f5f7fa;
}

.chat-item.active {
    background-color: #409eff;
    color: white;
}

.chat-info {
    flex: 1;
    min-width: 0;
}

.chat-title {
    font-weight: 500;
    font-size: 14px;
    margin-bottom: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.chat-preview {
    font-size: 12px;
    color: #909399;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-bottom: 4px;
}

.chat-item.active .chat-preview {
    color: rgba(255, 255, 255, 0.8);
}

.chat-time {
    font-size: 11px;
    color: #c0c4cc;
}

.chat-item.active .chat-time {
    color: rgba(255, 255, 255, 0.6);
}

.chat-menu {
    opacity: 0;
    transition: opacity 0.3s;
}

.chat-item:hover .chat-menu {
    opacity: 1;
}

/* 右侧主区域 */
.chat-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    background-color: #fff;
}
</style>

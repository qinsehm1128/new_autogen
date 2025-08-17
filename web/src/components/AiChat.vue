<template>
    <div class="ai-chat">
        <!-- 左侧会话列表（提取为组件） -->
        <ChatSidebar
            v-model:activeGroups="activeGroups"
            :chatGroups="chatGroups"
            :currentChatId="currentChatId"
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
            :selectedModel="selectedModel"
            :selectedModelName="selectedModelName"
            :isLoading="isLoading"
            :hasStreamingMessage="hasStreamingMessage"
            placeholder="输入你的问题..."
            :formatTime="formatTime"
            @new-chat="handleNewChat"
            @model-change="handleModelChange"
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
    Paperclip,
} from "@element-plus/icons-vue";
import { MdPreview } from "md-editor-v3";
import "md-editor-v3/lib/preview.css";

// 响应式数据
const editorRef = ref();
const chatMainRef = ref(null);
const isLoading = ref(false);
const currentChatId = ref(null);
const selectedModel = ref("");
const activeGroups = ref(["default"]);
// 流式中止与当前助手消息引用
const cancelStreaming = ref(false);
const currentAssistantMessage = ref(null);

// 对话框控制
const groupDialogVisible = ref(false);
const renameDialogVisible = ref(false);
const moveDialogVisible = ref(false);
const newGroupName = ref("");
const newChatTitle = ref("");
const targetGroupId = ref("");
const currentOperatingChat = ref(null);

// 模拟数据
const availableModels = ref([
    { id: "gpt-4", name: "GPT-4", status: "active" },
    { id: "gpt-3.5-turbo", name: "GPT-3.5 Turbo", status: "active" },
    { id: "claude-3", name: "Claude-3", status: "inactive" },
    { id: "gemini-pro", name: "Gemini Pro", status: "active" },
]);

const chatGroups = ref([
    {
        id: "default",
        name: "默认分组",
        chats: [
            {
                id: "chat-1",
                title: "关于Vue3的问题",
                lastMessage: "请解释Vue3的响应式原理",
                updateTime: new Date().getTime() - 3600000,
                modelId: "gpt-4",
            },
            {
                id: "chat-2",
                title: "前端开发讨论",
                lastMessage: "如何优化页面性能？",
                updateTime: new Date().getTime() - 7200000,
                modelId: "gpt-3.5-turbo",
            },
        ],
    },
    {
        id: "work",
        name: "工作相关",
        chats: [
            {
                id: "chat-3",
                title: "项目架构设计",
                lastMessage: "微服务架构的优缺点",
                updateTime: new Date().getTime() - 86400000,
                modelId: "gpt-4",
            },
        ],
    },
]);

const messages = ref({
    "chat-1": [
        {
            id: "msg-1",
            role: "user",
            content: "请解释Vue3的响应式原理",
            timestamp: new Date().getTime() - 3600000,
        },
        {
            id: "msg-2",
            role: "assistant",
            content:
                "Vue3的响应式系统基于Proxy代理实现，相比Vue2的Object.defineProperty有更好的性能和功能...",
            timestamp: new Date().getTime() - 3550000,
        },
    ],
    "chat-2": [
        {
            id: "msg-3",
            role: "user",
            content: "如何优化页面性能？",
            timestamp: new Date().getTime() - 7200000,
        },
    ],
});

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

const handleNewChat = () => {
    const newChatId = `chat-${Date.now()}`;
    const newChat = {
        id: newChatId,
        title: "新对话",
        lastMessage: "",
        updateTime: new Date().getTime(),
        modelId: selectedModel.value || availableModels.value[0]?.id,
    };

    chatGroups.value[0].chats.unshift(newChat);
    messages.value[newChatId] = [];
    currentChatId.value = newChatId;

    if (!selectedModel.value) {
        selectedModel.value = availableModels.value[0]?.id;
    }
};

const handleSendMessage = async (payload) => {
    if (!currentChatId.value || !selectedModel.value) {
        ElMessage.warning("请先选择模型");
        return;
    }

    const userMessage = {
        id: `msg-${Date.now()}`,
        role: "user",
        content: payload.text,
        timestamp: new Date().getTime(),
    };

    // 添加用户消息
    if (!messages.value[currentChatId.value]) {
        messages.value[currentChatId.value] = [];
    }
    messages.value[currentChatId.value].push(userMessage);

    // 更新聊天标题和最后消息
    const chat = currentChat.value;
    if (chat) {
        if (chat.title === "新对话" && payload.text.length > 0) {
            chat.title =
                payload.text.substring(0, 20) +
                (payload.text.length > 20 ? "..." : "");
        }
        chat.lastMessage = payload.text;
        chat.updateTime = new Date().getTime();
    }

    isLoading.value = true;
    cancelStreaming.value = false; // 开始新一轮流式前重置取消标志

    try {
        // 模拟AI响应
        await simulateAiResponse(payload.text);
    } catch (error) {
        ElMessage.error("发送消息失败");
    } finally {
        isLoading.value = false;
    }

    nextTick(() => {
        scrollToBottom();
    });
};

const simulateAiResponse = async (userInput) => {
    // 模拟流式响应
    const responses = [
        "### 基于当前的上下文，我建议 \n\n...基于当前的上下文，我建议...基于当前的上下文，我建议...基于当前的上下文，我建议...基于当前的上下文，我建议...基于当前的上下文，我建议...基于当前的上下文，我建议...基于当前的上下文，我建议...基于当前的上下文，我建议...基于当前的上下文，我建议...基于当前的上下文，我建议...基于当前的上下文，我建议...基于当前的上下文，我建议...基于当前的上下文，我建议...基于当前的上下文，我建议...",
    ];

    const response = responses[Math.floor(Math.random() * responses.length)];

    const assistantMessage = reactive({
        id: `msg-${Date.now()}`,
        role: "assistant",
        content: "",
        timestamp: new Date().getTime(),
        streaming: true,
    });

    messages.value[currentChatId.value].push(assistantMessage);
    // 确保插入的新节点先渲染出来，再开始逐字更新
    await nextTick();
    currentAssistantMessage.value = assistantMessage;

    // 模拟打字效果（每约60ms渲染一次）
    let buffer = "";
    let lastFlush = performance.now();
    for (let i = 0; i < response.length; i++) {
        // 生成字符的节奏，可适当更小以保证总体流畅度
        await new Promise((resolve) => setTimeout(resolve, 10));
        if (cancelStreaming.value) {
            // 取消时补渲未刷新的缓冲，避免丢字符
            if (buffer) {
                assistantMessage.content += buffer;
                buffer = "";
                await nextTick();
            }
            assistantMessage.streaming = false;
            currentAssistantMessage.value = null;
            return;
        }
        buffer += response[i];
        const now = performance.now();
        const isLast = i === response.length - 1;
        if (now - lastFlush >= 60 || isLast) {
            assistantMessage.content += buffer;
            buffer = "";
            lastFlush = now;
            await nextTick();
            scrollToBottom();
        }
    }

    assistantMessage.streaming = false;
    await nextTick();
    scrollToBottom();
};

const handleCancelRequest = () => {
    // 标记取消，让流式循环立即退出
    cancelStreaming.value = true;
    // 若当前有助手消息处于流式状态，立刻将其标记为完成以切换视图
    if (
        currentAssistantMessage.value &&
        currentAssistantMessage.value.streaming
    ) {
        currentAssistantMessage.value.streaming = false;
    }
    currentAssistantMessage.value = null;
    isLoading.value = false;
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
            messages.value[currentChatId.value] = [];
            if (currentChat.value) {
                currentChat.value.lastMessage = "";
            }
        }

        ElMessage.success("对话已清空");
    } catch {
        // 用户取消
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

const handleCreateGroup = () => {
    if (!newGroupName.value.trim()) {
        ElMessage.warning("请输入分组名称");
        return;
    }

    const newGroup = {
        id: `group-${Date.now()}`,
        name: newGroupName.value,
        chats: [],
    };

    chatGroups.value.push(newGroup);
    groupDialogVisible.value = false;
    ElMessage.success("分组创建成功");
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

const handleRenameChat = () => {
    if (!newChatTitle.value.trim()) {
        ElMessage.warning("请输入对话标题");
        return;
    }

    if (currentOperatingChat.value) {
        currentOperatingChat.value.title = newChatTitle.value;
        renameDialogVisible.value = false;
        ElMessage.success("重命名成功");
    }
};

const handleMoveChat = () => {
    if (!targetGroupId.value) {
        ElMessage.warning("请选择目标分组");
        return;
    }

    const chat = currentOperatingChat.value;
    if (!chat) return;

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
    } catch {
        // 用户取消
    }
};

// 初始化
onMounted(() => {
    // 默认选择第一个可用模型
    if (availableModels.value.length > 0) {
        selectedModel.value =
            availableModels.value.find((m) => m.status === "active")?.id ||
            availableModels.value[0].id;
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

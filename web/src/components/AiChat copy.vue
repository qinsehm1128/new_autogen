<template>
    <div class="ai-chat">
        <!-- 左侧会话列表 -->
        <div class="chat-sidebar">
            <div class="sidebar-header">
                <el-button
                    type="primary"
                    @click="handleNewChat"
                    class="new-chat-btn"
                >
                    <el-icon><Plus /></el-icon>
                    新建对话
                </el-button>
                <el-dropdown @command="handleGroupCommand" trigger="click">
                    <el-button text class="group-btn">
                        <el-icon><FolderOpened /></el-icon>
                    </el-button>
                    <template #dropdown>
                        <el-dropdown-menu>
                            <el-dropdown-item command="new-group">
                                <el-icon><Plus /></el-icon>
                                新建分组
                            </el-dropdown-item>
                            <el-dropdown-item command="manage-groups">
                                <el-icon><Setting /></el-icon>
                                管理分组
                            </el-dropdown-item>
                        </el-dropdown-menu>
                    </template>
                </el-dropdown>
            </div>

            <div class="chat-groups">
                <el-collapse v-model="activeGroups" accordion>
                    <el-collapse-item
                        v-for="group in chatGroups"
                        :key="group.id"
                        :title="group.name"
                        :name="group.id"
                    >
                        <template #title>
                            <div class="group-title">
                                <el-icon><Folder /></el-icon>
                                <span>{{ group.name }}</span>
                                <span class="chat-count"
                                    >({{ group.chats.length }})</span
                                >
                            </div>
                        </template>

                        <div class="chat-list">
                            <div
                                v-for="chat in group.chats"
                                :key="chat.id"
                                class="chat-item"
                                :class="{ active: currentChatId === chat.id }"
                                @click="selectChat(chat)"
                            >
                                <div class="chat-info">
                                    <div class="chat-title">
                                        {{ chat.title }}
                                    </div>
                                    <div class="chat-preview">
                                        {{ chat.lastMessage }}
                                    </div>
                                    <div class="chat-time">
                                        {{ formatTime(chat.updateTime) }}
                                    </div>
                                </div>
                                <el-dropdown
                                    @command="
                                        (command) =>
                                            handleChatCommand(command, chat)
                                    "
                                    trigger="click"
                                    @click.stop
                                >
                                    <el-button
                                        text
                                        size="small"
                                        class="chat-menu"
                                    >
                                        <el-icon><MoreFilled /></el-icon>
                                    </el-button>
                                    <template #dropdown>
                                        <el-dropdown-menu>
                                            <el-dropdown-item command="rename"
                                                >重命名</el-dropdown-item
                                            >
                                            <el-dropdown-item command="move"
                                                >移动到分组</el-dropdown-item
                                            >
                                            <el-dropdown-item
                                                command="delete"
                                                divided
                                                >删除</el-dropdown-item
                                            >
                                        </el-dropdown-menu>
                                    </template>
                                </el-dropdown>
                            </div>
                        </div>
                    </el-collapse-item>
                </el-collapse>
            </div>
        </div>

        <!-- 右侧对话区域 -->
        <div class="chat-main">
            <!-- 顶部工具栏 -->
            <div class="chat-header">
                <div class="chat-title-area">
                    <h3 v-if="currentChat">{{ currentChat.title }}</h3>
                    <span v-else class="no-chat-text"
                        >选择一个对话开始聊天</span
                    >
                </div>

                <div class="chat-controls">
                    <!-- 模型选择 -->
                    <el-select
                        v-model="selectedModel"
                        placeholder="选择模型"
                        style="width: 200px"
                        @change="handleModelChange"
                    >
                        <el-option
                            v-for="model in availableModels"
                            :key="model.id"
                            :label="model.name"
                            :value="model.id"
                        >
                            <div class="model-option">
                                <span class="model-name">{{ model.name }}</span>
                                <el-tag
                                    v-if="model.status === 'active'"
                                    type="success"
                                    size="small"
                                    >可用</el-tag
                                >
                                <el-tag v-else type="danger" size="small"
                                    >不可用</el-tag
                                >
                            </div>
                        </el-option>
                    </el-select>

                    <el-button
                        @click="handleClearChat"
                        :disabled="!currentChat"
                    >
                        <el-icon><Delete /></el-icon>
                        清空对话
                    </el-button>

                    <el-button
                        @click="handleExportChat"
                        :disabled="!currentChat"
                    >
                        <el-icon><Download /></el-icon>
                        导出
                    </el-button>
                </div>
            </div>

            <!-- 消息列表 -->
            <div class="chat-messages" ref="messagesContainer">
                <div v-if="!currentChat" class="welcome-area">
                    <div class="welcome-content">
                        <el-icon class="welcome-icon"><ChatRound /></el-icon>
                        <h2>AI 助手</h2>
                        <p>选择一个对话或创建新对话开始聊天</p>
                        <div class="quick-actions">
                            <el-button type="primary" @click="handleNewChat">
                                <el-icon><Plus /></el-icon>
                                开始新对话
                            </el-button>
                        </div>
                    </div>
                </div>

                <div v-else class="messages-list">
                    <div
                        v-for="message in currentMessages"
                        :key="message.id"
                        class="message-item"
                        :class="{
                            'user-message': message.role === 'user',
                            'assistant-message': message.role === 'assistant',
                        }"
                    >
                        <div class="message-avatar">
                            <el-avatar
                                v-if="message.role === 'user'"
                                :size="32"
                            >
                                <el-icon><User /></el-icon>
                            </el-avatar>
                            <el-avatar v-else :size="32" class="ai-avatar">
                                <el-icon><Service /></el-icon>
                            </el-avatar>
                        </div>

                        <div class="message-content">
                            <div class="message-header">
                                <span class="message-role">{{
                                    message.role === "user"
                                        ? "你"
                                        : selectedModelName || "AI助手"
                                }}</span>
                                <span class="message-time">{{
                                    formatTime(message.timestamp)
                                }}</span>
                            </div>

                            <div class="message-text">
                                <div>
                                    <MdPreview :modelValue="message.content" />
                                    <span
                                        v-if="
                                            message.role === 'assistant' &&
                                            message.streaming
                                        "
                                        class="cursor"
                                        >|</span
                                    >
                                </div>
                            </div>

                            <div
                                v-if="message.role === 'assistant'"
                                class="message-actions"
                            >
                                <el-button
                                    text
                                    size="small"
                                    @click="copyMessage(message.content)"
                                >
                                    <el-icon><CopyDocument /></el-icon>
                                    复制
                                </el-button>
                                <el-button
                                    text
                                    size="small"
                                    @click="regenerateResponse(message)"
                                >
                                    <el-icon><Refresh /></el-icon>
                                    重新生成
                                </el-button>
                            </div>
                        </div>
                    </div>

                    <!-- 加载状态 -->
                    <div
                        v-if="isLoading && !hasStreamingMessage"
                        class="message-item assistant-message"
                    >
                        <div class="message-avatar">
                            <el-avatar :size="32" class="ai-avatar">
                                <el-icon><Service /></el-icon>
                            </el-avatar>
                        </div>
                        <div class="message-content">
                            <div class="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 输入区域 -->
            <div class="chat-input" v-if="currentChat">
                <EditorSender
                    ref="editorRef"
                    placeholder="输入你的问题..."
                    :loading="isLoading"
                    :disabled="!selectedModel"
                    @submit="handleSendMessage"
                    @cancel="handleCancelRequest"
                >
                    <template #prefix>
                        <div class="input-prefix">
                            <el-tooltip content="附件" placement="top">
                                <el-button round plain size="small">
                                    <el-icon><Paperclip /></el-icon>
                                </el-button>
                            </el-tooltip>
                        </div>
                    </template>
                </EditorSender>
            </div>
        </div>

        <!-- 新建分组对话框 -->
        <el-dialog v-model="groupDialogVisible" title="新建分组" width="400px">
            <el-form @submit.prevent="handleCreateGroup">
                <el-form-item label="分组名称">
                    <el-input
                        v-model="newGroupName"
                        placeholder="请输入分组名称"
                    />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="groupDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="handleCreateGroup"
                    >确定</el-button
                >
            </template>
        </el-dialog>

        <!-- 重命名对话框 -->
        <el-dialog
            v-model="renameDialogVisible"
            title="重命名对话"
            width="400px"
        >
            <el-form @submit.prevent="handleRenameChat">
                <el-form-item label="对话标题">
                    <el-input
                        v-model="newChatTitle"
                        placeholder="请输入对话标题"
                    />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="renameDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="handleRenameChat"
                    >确定</el-button
                >
            </template>
        </el-dialog>

        <!-- 移动对话框 -->
        <el-dialog v-model="moveDialogVisible" title="移动到分组" width="400px">
            <el-form @submit.prevent="handleMoveChat">
                <el-form-item label="目标分组">
                    <el-select v-model="targetGroupId" placeholder="选择分组">
                        <el-option
                            v-for="group in chatGroups"
                            :key="group.id"
                            :label="group.name"
                            :value="group.id"
                        />
                    </el-select>
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="moveDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="handleMoveChat"
                    >确定</el-button
                >
            </template>
        </el-dialog>
    </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { EditorSender } from "vue-element-plus-x";
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
const messagesContainer = ref();
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
    if (messagesContainer.value) {
        messagesContainer.value.scrollTop =
            messagesContainer.value.scrollHeight;
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

.chat-header {
    padding: 20px;
    border-bottom: 1px solid #e4e7ed;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.chat-title-area h3 {
    margin: 0;
    color: #303133;
}

.no-chat-text {
    color: #909399;
    font-size: 16px;
}

.chat-controls {
    display: flex;
    gap: 12px;
    align-items: center;
}

.model-option {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
}

.model-name {
    flex: 1;
}

/* 消息区域 */
.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
}

.welcome-area {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
}

.welcome-content {
    text-align: center;
    color: #909399;
}

.welcome-icon {
    font-size: 64px;
    color: #409eff;
    margin-bottom: 20px;
}

.welcome-content h2 {
    margin: 0 0 10px 0;
    color: #303133;
}

.welcome-content p {
    margin: 0 0 20px 0;
}

.quick-actions {
    margin-top: 20px;
}

.messages-list {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.message-item {
    display: flex;
    gap: 12px;
    align-items: flex-start;
}

.user-message {
    flex-direction: row-reverse;
}

.message-avatar {
    flex-shrink: 0;
}

.ai-avatar {
    background-color: #409eff;
    color: white;
}

.message-content {
    display: flex;
    flex-direction: column;
    flex: 1 1 auto; /* 允许按可用空间增长，避免按最小内容收缩 */
    max-width: 70%; /* 统一控制单条消息可用宽度 */
    min-width: 0; /* 防止内容把行撑爆 */
}

.user-message .message-content {
    text-align: left;
    align-items: flex-end; /* 让内部气泡靠右 */
}

.message-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    font-size: 12px;
    color: #909399;
}

.user-message .message-header {
    flex-direction: row-reverse;
}

.message-role {
    font-weight: 500;
    color: #606266;
}

.message-text {
    display: inline-block; /* 按内容决定宽度 */
    flex: 0 0 auto; /* 禁止被 flex 拉伸 */
    max-width: 100%; /* 在父容器范围内渲染，避免过早换行 */
    background-color: #f5f7fa;
    padding: 12px 16px;
    border-radius: 12px;
    line-height: 1.6;
    /* 文本换行与长单词/URL（避免过于激进的任意断行） */
    word-break: break-word;
    overflow-wrap: break-word;
    box-sizing: border-box;
}

.user-message .message-text {
    background-color: #d3e9ff;
    color: rgb(26, 26, 26);
    align-self: flex-start; /* 靠右 */
    margin-left: auto;
}

/* 助手气泡靠左对齐（可选加强） */
.assistant-message .message-text {
    align-self: flex-start;
    margin-right: auto;
}

.streaming-text {
    display: flex;
    align-items: center;
}

.cursor {
    animation: blink 1s infinite;
    margin-left: 2px;
}

@keyframes blink {
    0%,
    50% {
        opacity: 1;
    }
    51%,
    100% {
        opacity: 0;
    }
}

.message-actions {
    margin-top: 8px;
    display: flex;
    gap: 8px;
    opacity: 0;
    transition: opacity 0.3s;
}

.message-item:hover .message-actions {
    opacity: 1;
}

.typing-indicator {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 12px 16px;
    background-color: #f5f7fa;
    border-radius: 12px;
}

.typing-indicator span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #909399;
    animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
    animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes typing {
    0%,
    60%,
    100% {
        transform: translateY(0);
    }
    30% {
        transform: translateY(-10px);
    }
}

/* 输入区域 */
.chat-input {
    padding: 20px;
    border-top: 1px solid #e4e7ed;
    background-color: #fff;
}

.input-prefix {
    display: flex;
    align-items: center;
    gap: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .ai-chat {
        flex-direction: column;
    }

    .chat-sidebar {
        width: 100%;
        height: 200px;
        border-right: none;
        border-bottom: 1px solid #e4e7ed;
    }

    .chat-main {
        flex: 1;
    }

    .chat-header {
        padding: 10px;
        flex-direction: column;
        align-items: stretch;
        gap: 10px;
    }

    .chat-controls {
        justify-content: space-between;
    }

    .message-content {
        max-width: 85%;
    }

    .chat-input {
        padding: 10px;
    }
}

/* 滚动条样式 */
.chat-groups::-webkit-scrollbar,
.chat-messages::-webkit-scrollbar {
    width: 6px;
}

.chat-groups::-webkit-scrollbar-track,
.chat-messages::-webkit-scrollbar-track {
    background: transparent;
}

.chat-groups::-webkit-scrollbar-thumb,
.chat-messages::-webkit-scrollbar-thumb {
    background: #c0c4cc;
    border-radius: 3px;
}

.chat-groups::-webkit-scrollbar-thumb:hover,
.chat-messages::-webkit-scrollbar-thumb:hover {
    background: #909399;
}
:deep(.el-collapse-item__title) {
    /* 删除 width: 100%; 或者至少加上： */
    box-sizing: border-box; /* 防止 padding 导致溢出 */
}
/* Element Plus 组件样式覆盖 */
:deep(.el-collapse-item__header) {
    padding-left: 16px;
    padding-right: 16px;
    background-color: #f8f9fa;
    border: none;
}

:deep(.el-collapse-item__content) {
    padding: 0;
    border: none;
}

:deep(.el-dialog__body) {
    padding: 20px;
}

:deep(.el-select .el-input__wrapper) {
    border-radius: 6px;
}

/* 代码块样式 */
.message-text code {
    background-color: rgba(0, 0, 0, 0.1);
    padding: 2px 4px;
    border-radius: 4px;
    font-family: "Courier New", monospace;
    font-size: 0.9em;
}

.user-message .message-text code {
    background-color: rgba(255, 255, 255, 0.2);
}

/* 加载动画 */
.loading-dots {
    display: inline-block;
}

.loading-dots::after {
    content: "";
    animation: loading 2s infinite;
}

.md-editor {
    --md-bk-color: transparent !important;
}
@keyframes loading {
    0% {
        content: "";
    }
    25% {
        content: ".";
    }
    50% {
        content: "..";
    }
    75% {
        content: "...";
    }
    100% {
        content: "";
    }
}
</style>

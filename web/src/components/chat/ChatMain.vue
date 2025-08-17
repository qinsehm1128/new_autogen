<template>
    <div class="chat-main">
        <!-- 顶部工具栏 -->
        <div class="chat-header">
            <div class="chat-title-area">
                <h3 v-if="currentChat">{{ currentChat.title }}</h3>
                <span v-else class="no-chat-text">选择一个对话开始聊天</span>
            </div>

            <div class="chat-controls">
                <!-- 模型选择 -->
                <el-select
                    v-model="localSelectedModel"
                    placeholder="选择模型"
                    style="width: 200px"
                    @change="(v) => emit('model-change', v)"
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

                <!-- 提示词选择 -->
                <el-select
                    v-model="localSelectedPrompt"
                    placeholder="选择提示词"
                    style="width: 200px"
                    clearable
                    @change="(v) => emit('prompt-change', v)"
                >
                    <el-option
                        v-for="prompt in availablePrompts"
                        :key="prompt.id"
                        :label="prompt.title"
                        :value="prompt.id"
                    >
                        <div class="prompt-option">
                            <span class="prompt-title">{{ prompt.title }}</span>
                            <el-tag size="small" type="info">{{
                                prompt.category
                            }}</el-tag>
                        </div>
                    </el-option>
                </el-select>

                <el-button @click="emit('clear-chat')" :disabled="!currentChat">
                    <el-icon><Delete /></el-icon>
                    清空对话
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
                        <el-button type="primary" @click="$emit('new-chat')">
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
                        <el-avatar v-if="message.role === 'user'" :size="32">
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
                                @click="emit('copy-message', message.content)"
                            >
                                <el-icon><CopyDocument /></el-icon>
                                复制
                            </el-button>
                            <el-button
                                text
                                size="small"
                                @click="emit('regenerate-response', message)"
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
                :placeholder="placeholder"
                :loading="isLoading"
                :disabled="!localSelectedModel"
                @submit="(p) => emit('send-message', p)"
                @cancel="() => emit('cancel-request')"
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
</template>

<script setup>
import { ref, watch, defineExpose, nextTick } from "vue";
import { EditorSender } from "vue-element-plus-x";
import { MdPreview } from "md-editor-v3";
import "md-editor-v3/lib/preview.css";
import {
    Plus,
    Delete,
    ChatRound,
    User,
    Service,
    CopyDocument,
    Refresh,
    Paperclip,
} from "@element-plus/icons-vue";

const props = defineProps({
    currentChat: { type: Object, default: null },
    currentMessages: { type: Array, default: () => [] },
    availableModels: { type: Array, default: () => [] },
    availablePrompts: { type: Array, default: () => [] },
    selectedModel: { type: String, default: "" },
    selectedModelName: { type: String, default: "" },
    selectedPrompt: { type: String, default: "" },
    isLoading: { type: Boolean, default: false },
    hasStreamingMessage: { type: Boolean, default: false },
    placeholder: { type: String, default: "输入你的问题..." },
    formatTime: { type: Function, required: true },
});

const emit = defineEmits([
    "new-chat",
    "model-change",
    "prompt-change",
    "clear-chat",
    "send-message",
    "cancel-request",
    "copy-message",
    "regenerate-response",
]);

const localSelectedModel = ref(props.selectedModel);
const localSelectedPrompt = ref(props.selectedPrompt);

watch(
    () => props.selectedModel,
    (v) => (localSelectedModel.value = v),
);
watch(
    () => props.selectedPrompt,
    (v) => (localSelectedPrompt.value = v),
);

watch(localSelectedModel, (v) => emit("model-change", v));
watch(localSelectedPrompt, (v) => emit("prompt-change", v));

// 滚动控制，供父组件调用
const messagesContainer = ref(null);
async function scrollToBottom() {
    await nextTick();
    const el = messagesContainer.value;
    if (el) {
        el.scrollTop = el.scrollHeight;
    }
}
defineExpose({ scrollToBottom });
</script>

<style scoped>
/* 布局 */
.chat-main {
    flex: 1;
    display: flex;
    flex-direction: column;
}
.chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 16px;
    background-color: #fff;
    border-bottom: 1px solid #e4e7ed;
}
.chat-title-area h3 {
    margin: 0;
    font-weight: 600;
}
.no-chat-text {
    color: #909399;
}
.chat-controls {
    display: flex;
    align-items: center;
    gap: 10px;
}

/* 消息列表 */
.chat-messages {
    flex: 1;
    overflow: auto;
    padding: 16px;
    background-color: #f5f5f5;
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
    flex: 1 1 auto;
    max-width: 70%;
    min-width: 0;
}
.user-message .message-content {
    text-align: left;
    align-items: flex-end;
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
    display: inline-block;
    flex: 0 0 auto;
    max-width: 100%;
    background-color: #f5f7fa;
    padding: 12px 16px;
    border-radius: 12px;
    line-height: 1.6;
    word-break: break-word;
    overflow-wrap: break-word;
    box-sizing: border-box;
}
.user-message .message-text {
    background-color: #d3e9ff;
    color: rgb(26, 26, 26);
    align-self: flex-start;
    margin-left: auto;
}
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

/* 代码块样式（保留与父级一致） */
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
.md-editor {
    --md-bk-color: transparent !important;
}

/* 加载状态气泡 */
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

/* 滚动条样式（消息区） */
.chat-messages::-webkit-scrollbar {
    width: 6px;
}
.chat-messages::-webkit-scrollbar-track {
    background: transparent;
}
.chat-messages::-webkit-scrollbar-thumb {
    background: #c0c4cc;
    border-radius: 3px;
}
.chat-messages::-webkit-scrollbar-thumb:hover {
    background: #909399;
}

/* 响应式 */
@media (max-width: 768px) {
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
}
</style>

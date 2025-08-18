<template>
  <div class="chat-sidebar">
    <div class="sidebar-header">
      <el-button type="primary" @click="$emit('new-chat')" class="new-chat-btn">
        <el-icon><Plus /></el-icon>
        新建对话
      </el-button>
      <el-dropdown @command="(cmd)=>$emit('group-command', cmd)" trigger="click">
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
      <!-- 加载状态 -->
      <div v-if="loadingStates.groups" class="loading-container">
        <el-skeleton :rows="3" animated />
      </div>

      <!-- 分组列表 -->
      <el-collapse v-else v-model="modelActiveGroups">
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
              <span class="chat-count">({{ group.chats.length }})</span>
            </div>
          </template>

          <div class="chat-list">
            <div
              v-for="chat in group.chats"
              :key="chat.id"
              class="chat-item"
              :class="{ active: currentChatId === chat.id }"
              @click="$emit('select-chat', chat)"
            >
              <div class="chat-info">
                <div class="chat-title">{{ chat.title }}</div>
                <div class="chat-preview">{{ chat.lastMessage }}</div>
                <div class="chat-time">{{ formatTime(chat.updateTime) }}</div>
              </div>
              <el-dropdown
                @command="(command) => $emit('chat-command', { command, chat })"
                trigger="click"
                @click.stop
              >
                <el-button text size="small" class="chat-menu">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="rename">重命名</el-dropdown-item>
                    <el-dropdown-item command="move">移动到分组</el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Plus, FolderOpened, Folder, Setting, MoreFilled } from '@element-plus/icons-vue'

const props = defineProps({
  chatGroups: { type: Array, required: true },
  activeGroups: { type: Array, required: true },
  currentChatId: { type: [String, Number, null], default: null },
  loadingStates: { type: Object, default: () => ({}) },
  formatTime: { type: Function, required: true }
})

const emit = defineEmits([
  'new-chat',
  'group-command',
  'select-chat',
  'chat-command',
  'update:activeGroups'
])

// v-model:active-groups 支持
const modelActiveGroups = computed({
  get: () => props.activeGroups,
  set: (val) => emit('update:activeGroups', val)
})
</script>

<style scoped>
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

.new-chat-btn { flex: 1; }
.group-btn { padding: 8px; }

.chat-groups {
  padding: 10px 0;
  overflow: auto;
  flex: 1;
}

.group-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.chat-count { color: #909399; font-size: 12px; }

.chat-list { display: flex; flex-direction: column; gap: 8px; padding: 8px; }

.chat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
}
.chat-item.active { background-color: #409eff; color: #fff; }

.chat-info { flex: 1; min-width: 0; }
.chat-title { font-weight: 500; font-size: 14px; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chat-preview { font-size: 12px; color: #909399; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 4px; }
.chat-item.active .chat-preview { color: rgba(255,255,255,0.8); }
.chat-time { font-size: 11px; color: #c0c4cc; }
.chat-item.active .chat-time { color: rgba(255,255,255,0.6); }

/* Element Plus 折叠面板覆盖 */
:deep(.el-collapse-item__title){
  box-sizing: border-box;
}
:deep(.el-collapse-item__header) {
  padding-left: 16px;
  padding-right: 16px;
  background-color: #f8f9fa;
  border: none;
}
:deep(.el-collapse-item__content) { padding: 0; border: none; }

/* 滚动条样式（侧边栏） */
.chat-groups::-webkit-scrollbar { width: 6px; }
.chat-groups::-webkit-scrollbar-track { background: transparent; }
.chat-groups::-webkit-scrollbar-thumb { background: #c0c4cc; border-radius: 3px; }
.chat-groups::-webkit-scrollbar-thumb:hover { background: #909399; }

/* 加载状态 */
.loading-container {
  padding: 16px;
}

/* 响应式：窄屏时侧边栏置顶且减少高度 */
@media (max-width: 768px) {
  .chat-sidebar {
    width: 100%;
    height: 200px;
    border-right: none;
    border-bottom: 1px solid #e4e7ed;
  }
}
</style>

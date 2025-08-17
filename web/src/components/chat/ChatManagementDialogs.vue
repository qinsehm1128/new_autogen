<template>
  <!-- 新建分组对话框 -->
  <el-dialog v-model="modelGroupVisible" title="新建分组" width="400px">
    <el-form @submit.prevent="$emit('create-group')">
      <el-form-item label="分组名称">
        <el-input v-model="modelNewGroupName" placeholder="请输入分组名称" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="modelGroupVisible = false">取消</el-button>
      <el-button type="primary" @click="$emit('create-group')">确定</el-button>
    </template>
  </el-dialog>

  <!-- 重命名对话框 -->
  <el-dialog v-model="modelRenameVisible" title="重命名对话" width="400px">
    <el-form @submit.prevent="$emit('rename-chat')">
      <el-form-item label="对话标题">
        <el-input v-model="modelNewChatTitle" placeholder="请输入对话标题" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="modelRenameVisible = false">取消</el-button>
      <el-button type="primary" @click="$emit('rename-chat')">确定</el-button>
    </template>
  </el-dialog>

  <!-- 移动对话框 -->
  <el-dialog v-model="modelMoveVisible" title="移动到分组" width="400px">
    <el-form @submit.prevent="$emit('move-chat')">
      <el-form-item label="目标分组">
        <el-select v-model="modelTargetGroupId" placeholder="选择分组">
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
      <el-button @click="modelMoveVisible = false">取消</el-button>
      <el-button type="primary" @click="$emit('move-chat')">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  groupDialogVisible: { type: Boolean, default: false },
  renameDialogVisible: { type: Boolean, default: false },
  moveDialogVisible: { type: Boolean, default: false },
  newGroupName: { type: String, default: '' },
  newChatTitle: { type: String, default: '' },
  targetGroupId: { type: [String, Number, null], default: null },
  chatGroups: { type: Array, default: () => [] },
})

const emit = defineEmits([
  'update:groupDialogVisible',
  'update:renameDialogVisible',
  'update:moveDialogVisible',
  'update:newGroupName',
  'update:newChatTitle',
  'update:targetGroupId',
  'create-group',
  'rename-chat',
  'move-chat',
])

// v-model 适配
const modelGroupVisible = computed({
  get: () => props.groupDialogVisible,
  set: v => emit('update:groupDialogVisible', v)
})
const modelRenameVisible = computed({
  get: () => props.renameDialogVisible,
  set: v => emit('update:renameDialogVisible', v)
})
const modelMoveVisible = computed({
  get: () => props.moveDialogVisible,
  set: v => emit('update:moveDialogVisible', v)
})

const modelNewGroupName = computed({
  get: () => props.newGroupName,
  set: v => emit('update:newGroupName', v)
})
const modelNewChatTitle = computed({
  get: () => props.newChatTitle,
  set: v => emit('update:newChatTitle', v)
})
const modelTargetGroupId = computed({
  get: () => props.targetGroupId,
  set: v => emit('update:targetGroupId', v)
})
</script>

<style scoped>
/* 弹窗样式覆盖（独立于父组件） */
:deep(.el-dialog__body) { padding: 20px; }
:deep(.el-select .el-input__wrapper) { border-radius: 6px; }
</style>

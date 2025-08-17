<template>
    <div class="prompts-manager">
        <el-card class="box-card">
            <template #header>
                <div class="card-header">
                    <span class="title">提示词管理</span>
                    <el-button type="primary" @click="handleAddPrompt">
                        <el-icon><Plus /></el-icon>
                        新增提示词
                    </el-button>
                </div>
            </template>

            <div class="prompts-content">
                <div class="content-container">
                    <!-- 左侧列表区域 -->
                    <div class="left-panel">
                        <div class="panel-header">
                            <el-input
                                v-model="promptSearch"
                                placeholder="搜索提示词..."
                                size="small"
                                clearable
                                @input="handleSearch"
                            >
                                <template #prefix>
                                    <el-icon><Search /></el-icon>
                                </template>
                            </el-input>
                            <el-select
                                v-model="categoryFilter"
                                placeholder="分类筛选"
                                size="small"
                                clearable
                                @change="handleSearch"
                            >
                                <el-option
                                    v-for="cat in categories"
                                    :key="cat.value"
                                    :label="cat.label"
                                    :value="cat.value"
                                />
                            </el-select>
                        </div>

                        <div class="list-container">
                            <el-scrollbar
                                height="calc(100vh - 350px)"
                                v-loading="listLoading"
                            >
                                <div
                                    v-for="prompt in prompts"
                                    :key="prompt.id"
                                    class="list-item"
                                    :class="{
                                        active:
                                            selectedPrompt?.id === prompt.id,
                                    }"
                                    @click="selectPrompt(prompt)"
                                >
                                    <div class="item-header">
                                        <span class="item-title">{{
                                            prompt.title
                                        }}</span>
                                        <div class="item-actions">
                                            <el-button
                                                type="text"
                                                size="small"
                                                @click.stop="
                                                    handleCopyPrompt(prompt)
                                                "
                                            >
                                                <el-icon
                                                    ><DocumentCopy
                                                /></el-icon>
                                            </el-button>
                                            <el-button
                                                type="text"
                                                size="small"
                                                @click.stop="
                                                    handleDeletePrompt(prompt)
                                                "
                                            >
                                                <el-icon><Delete /></el-icon>
                                            </el-button>
                                        </div>
                                    </div>
                                    <div class="item-meta">
                                        <el-tag size="small" type="primary">{{
                                            getCategoryLabel(prompt.category)
                                        }}</el-tag>
                                        <el-tag
                                            v-if="prompt.is_public"
                                            size="small"
                                            type="success"
                                        >
                                            公开
                                        </el-tag>
                                        <span class="item-time">{{
                                            formatDate(prompt.updated_at)
                                        }}</span>
                                    </div>
                                    <div class="item-preview">
                                        {{ prompt.content.substring(0, 50) }}...
                                    </div>
                                    <div
                                        class="item-tags"
                                        v-if="prompt.tags && prompt.tags.length"
                                    >
                                        <el-tag
                                            v-for="tag in prompt.tags.slice(
                                                0,
                                                3,
                                            )"
                                            :key="tag"
                                            size="small"
                                            type="info"
                                        >
                                            {{ tag }}
                                        </el-tag>
                                    </div>
                                </div>

                                <!-- 分页 -->
                                <div
                                    class="pagination-mini"
                                    v-if="pagination.total > 0"
                                >
                                    <el-pagination
                                        v-model:current-page="
                                            pagination.pageNum
                                        "
                                        v-model:page-size="pagination.pageSize"
                                        :page-sizes="[10, 20, 50]"
                                        layout="prev, pager, next"
                                        small
                                        :total="pagination.total"
                                        @size-change="handleSizeChange"
                                        @current-change="handleCurrentChange"
                                    />
                                </div>
                            </el-scrollbar>
                        </div>
                    </div>

                    <!-- 右侧编辑区域 -->
                    <div class="right-panel">
                        <div v-if="selectedPrompt" class="editor-container">
                            <div class="editor-header">
                                <el-input
                                    v-model="selectedPrompt.title"
                                    placeholder="提示词标题"
                                    size="large"
                                    class="title-input"
                                />
                                <div class="editor-actions">
                                    <el-button @click="resetPromptEditor"
                                        >取消</el-button
                                    >
                                    <el-button
                                        type="success"
                                        @click="handleTestPrompt"
                                        :loading="testLoading"
                                        >测试</el-button
                                    >
                                    <el-button
                                        type="primary"
                                        @click="savePrompt"
                                        :loading="saving"
                                        >保存</el-button
                                    >
                                </div>
                            </div>

                            <div class="editor-meta">
                                <el-row :gutter="20">
                                    <el-col :span="8">
                                        <el-select
                                            v-model="selectedPrompt.category"
                                            placeholder="选择分类"
                                            size="small"
                                        >
                                            <el-option
                                                v-for="cat in categories"
                                                :key="cat.value"
                                                :label="cat.label"
                                                :value="cat.value"
                                            />
                                        </el-select>
                                    </el-col>
                                    <el-col :span="8">
                                        <el-switch
                                            v-model="selectedPrompt.is_public"
                                            active-text="公开"
                                            inactive-text="私有"
                                        />
                                    </el-col>
                                    <el-col :span="8">
                                        <el-input-number
                                            v-model="selectedPrompt.sort"
                                            :min="0"
                                            size="small"
                                            placeholder="排序值"
                                        />
                                    </el-col>
                                </el-row>
                            </div>

                            <div class="editor-content">
                                <el-tabs v-model="activeTab">
                                    <el-tab-pane
                                        label="内容编辑"
                                        name="content"
                                    >
                                        <el-input
                                            v-model="selectedPrompt.content"
                                            type="textarea"
                                            :rows="12"
                                            placeholder="请输入提示词内容..."
                                        />
                                    </el-tab-pane>
                                    <el-tab-pane
                                        label="描述"
                                        name="description"
                                    >
                                        <el-input
                                            v-model="selectedPrompt.description"
                                            type="textarea"
                                            :rows="4"
                                            placeholder="请输入提示词描述..."
                                        />
                                    </el-tab-pane>
                                    <el-tab-pane label="标签" name="tags">
                                        <el-select
                                            v-model="selectedPrompt.tags"
                                            multiple
                                            filterable
                                            allow-create
                                            default-first-option
                                            placeholder="选择或输入标签"
                                            style="width: 100%"
                                        >
                                            <el-option
                                                v-for="tag in availableTags"
                                                :key="tag.name"
                                                :label="tag.name"
                                                :value="tag.name"
                                            />
                                        </el-select>
                                    </el-tab-pane>
                                    <el-tab-pane label="变量" name="variables">
                                        <div class="variables-editor">
                                            <el-button
                                                type="primary"
                                                size="small"
                                                @click="addVariable"
                                            >
                                                添加变量
                                            </el-button>
                                            <div
                                                v-for="(
                                                    variable, index
                                                ) in variablesList"
                                                :key="index"
                                                class="variable-item"
                                            >
                                                <el-input
                                                    v-model="variable.name"
                                                    placeholder="变量名"
                                                    size="small"
                                                />
                                                <el-input
                                                    v-model="
                                                        variable.description
                                                    "
                                                    placeholder="描述"
                                                    size="small"
                                                />
                                                <el-button
                                                    type="danger"
                                                    size="small"
                                                    @click="
                                                        removeVariable(index)
                                                    "
                                                >
                                                    删除
                                                </el-button>
                                            </div>
                                        </div>
                                    </el-tab-pane>
                                </el-tabs>
                            </div>
                        </div>
                        <div v-else class="empty-editor">
                            <el-empty
                                description="请选择一个提示词进行编辑或创建新的提示词"
                            />
                        </div>
                    </div>
                </div>
            </div>
        </el-card>

        <!-- 测试对话框 -->
        <el-dialog v-model="testDialogVisible" title="测试提示词" width="600px">
            <el-form label-width="80px">
                <el-form-item label="测试输入">
                    <el-input
                        v-model="testInput"
                        type="textarea"
                        :rows="3"
                        placeholder="请输入测试内容..."
                    />
                </el-form-item>
                <el-form-item label="变量值" v-if="variablesList.length > 0">
                    <div
                        v-for="variable in variablesList"
                        :key="variable.name"
                        class="variable-input"
                    >
                        <label>{{ variable.name }}:</label>
                        <el-input
                            v-model="testVariables[variable.name]"
                            :placeholder="variable.description"
                            size="small"
                        />
                    </div>
                </el-form-item>
            </el-form>
            <div class="test-result" v-if="testResult">
                <h4>测试结果:</h4>
                <el-input
                    :value="testResult"
                    type="textarea"
                    :rows="6"
                    readonly
                />
            </div>
            <template #footer>
                <el-button @click="testDialogVisible = false">关闭</el-button>
                <el-button
                    type="primary"
                    @click="runTest"
                    :loading="testLoading"
                >
                    执行测试
                </el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Search, DocumentCopy, Delete } from "@element-plus/icons-vue";
import {
    listPrompts,
    getPrompt,
    addPrompt,
    updatePrompt,
    delPrompt,
    copyPrompt,
    testPrompt,
    getPromptCategories,
    getPromptTags,
} from "@/api/chat_config";

// 响应式数据
const listLoading = ref(false);
const saving = ref(false);
const testLoading = ref(false);
const testDialogVisible = ref(false);
const activeTab = ref("content");

// 提示词相关
const promptSearch = ref("");
const categoryFilter = ref("");
const selectedPrompt = ref(null);
const prompts = ref([]);
const categories = ref([]);
const availableTags = ref([]);

// 分页
const pagination = reactive({
    pageNum: 1,
    pageSize: 20,
    total: 0,
});

// 测试相关
const testInput = ref("");
const testVariables = reactive({});
const testResult = ref("");

// 变量列表 - 改为响应式数据而不是计算属性
const variablesList = ref([]);

// 方法
const formatDate = (dateString) => {
    if (!dateString) return "";
    return new Date(dateString).toLocaleString("zh-CN");
};

const getCategoryLabel = (category) => {
    const cat = categories.value.find((c) => c.value === category);
    return cat ? cat.label : category;
};

const fetchPrompts = async () => {
    listLoading.value = true;
    try {
        const params = {
            pageNum: pagination.pageNum,
            pageSize: pagination.pageSize,
            keyword: promptSearch.value,
            category: categoryFilter.value,
        };

        const response = await listPrompts(params);
        console.log(response);
        if (response.data && response.data.items) {
            const result = response.data;
            prompts.value = result.items || [];
            pagination.total = result.total || 0;
        }
    } catch (error) {
        console.error("获取提示词列表失败:", error);
        ElMessage.error(
            "获取数据失败: " + (error.response?.data?.message || error.message),
        );
    } finally {
        listLoading.value = false;
    }
};

const fetchCategories = async () => {
    try {
        const response = await getPromptCategories();
        console.log(response);
        if (response.data && response.data) {
            categories.value = response.data.map((cat) => ({
                value: cat.value,
                label: cat.label,
            }));
        }
    } catch (error) {
        console.error("获取分类失败:", error);
        // 使用默认分类
        categories.value = [
            { value: "system", label: "系统提示" },
            { value: "role", label: "角色扮演" },
            { value: "creative", label: "创意写作" },
            { value: "code", label: "代码相关" },
            { value: "other", label: "其他" },
        ];
    }
};

const fetchTags = async () => {
    try {
        const response = await getPromptTags();
        if (response.data && response.data) {
            availableTags.value = response.data || [];
        }
    } catch (error) {
        console.error("获取标签失败:", error);
        availableTags.value = [];
    }
};

const handleAddPrompt = () => {
    const newPrompt = {
        id: null,
        title: "新提示词",
        category: "other",
        content: "",
        description: "",
        tags: [],
        is_public: false,
        variables: {},
        sort: 0,
    };
    selectedPrompt.value = newPrompt;
    variablesList.value = [];
    activeTab.value = "content";
};

const selectPrompt = async (prompt) => {
    if (selectedPrompt.value?.id === prompt.id) return;

    try {
        const response = await getPrompt(prompt.id);
        if (response.data && response.data) {
            selectedPrompt.value = { ...response.data };
            // 更新变量列表
            updateVariablesList();
            activeTab.value = "content";
        }
    } catch (error) {
        console.error("获取提示词详情失败:", error);
        ElMessage.error("获取提示词详情失败");
    }
};

const resetPromptEditor = () => {
    selectedPrompt.value = null;
    variablesList.value = [];
    testResult.value = "";
};

const savePrompt = async () => {
    if (!selectedPrompt.value.title.trim()) {
        ElMessage.error("请输入提示词标题");
        return;
    }

    if (!selectedPrompt.value.content.trim()) {
        ElMessage.error("请输入提示词内容");
        return;
    }

    saving.value = true;
    try {
        // 转换变量格式
        const variables = {};
        variablesList.value.forEach((v) => {
            if (v.name && v.name.trim()) {
                variables[v.name.trim()] = v.description || "";
            }
        });
        selectedPrompt.value.variables = variables;

        if (selectedPrompt.value.id) {
            // 更新
            await updatePrompt(selectedPrompt.value);
            ElMessage.success("更新成功");
        } else {
            // 创建
            const { id, created_at, updated_at, ...createData } =
                selectedPrompt.value;
            const response = await addPrompt(createData);
            if (response.data && response.data.items) {
                selectedPrompt.value = response.items;
                updateVariablesList();
            }
            ElMessage.success("创建成功");
        }

        await fetchPrompts();
    } catch (error) {
        console.error("保存失败:", error);
        ElMessage.error(
            "保存失败: " + (error.response?.data?.message || error.message),
        );
    } finally {
        saving.value = false;
    }
};

const handleCopyPrompt = async (prompt) => {
    try {
        await copyPrompt(prompt.id);
        ElMessage.success("复制成功");
        await fetchPrompts();
    } catch (error) {
        console.error("复制失败:", error);
        ElMessage.error(
            "复制失败: " + (error.response?.data?.message || error.message),
        );
    }
};

const handleDeletePrompt = async (prompt) => {
    try {
        await ElMessageBox.confirm(
            `确定要删除提示词 "${prompt.title}" 吗？`,
            "删除确认",
            {
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                type: "warning",
            },
        );

        await delPrompt(prompt.id);
        ElMessage.success("删除成功");

        if (selectedPrompt.value?.id === prompt.id) {
            selectedPrompt.value = null;
        }

        await fetchPrompts();
    } catch (error) {
        if (error !== "cancel") {
            console.error("删除失败:", error);
            ElMessage.error(
                "删除失败: " + (error.response?.data?.message || error.message),
            );
        }
    }
};

const handleTestPrompt = () => {
    if (!selectedPrompt.value.content.trim()) {
        ElMessage.error("请先输入提示词内容");
        return;
    }
    testDialogVisible.value = true;
    testInput.value = "";
    testResult.value = "";

    // 初始化测试变量
    Object.keys(testVariables).forEach((key) => {
        delete testVariables[key];
    });
    variablesList.value.forEach((v) => {
        if (v.name) {
            testVariables[v.name] = "";
        }
    });
};

const runTest = async () => {
    if (!testInput.value.trim()) {
        ElMessage.error("请输入测试内容");
        return;
    }

    testLoading.value = true;
    try {
        const response = await testPrompt({
            content: selectedPrompt.value.content,
            variables: testVariables,
            testInput: testInput.value,
        });

        if (response.data && response.data.items) {
            testResult.value = response.items.result || "测试完成";
        }
    } catch (error) {
        console.error("测试失败:", error);
        ElMessage.error(
            "测试失败: " + (error.response?.data?.message || error.message),
        );
    } finally {
        testLoading.value = false;
    }
};

const addVariable = () => {
    variablesList.value.push({
        name: `变量${variablesList.value.length + 1}`,
        description: "",
    });
};

const removeVariable = (index) => {
    variablesList.value.splice(index, 1);
};

// 更新变量列表的辅助函数
const updateVariablesList = () => {
    if (!selectedPrompt.value?.variables) {
        variablesList.value = [];
        return;
    }
    variablesList.value = Object.entries(selectedPrompt.value.variables).map(
        ([name, description]) => ({
            name,
            description: description || "",
        }),
    );
};

const handleSearch = () => {
    pagination.pageNum = 1;
    fetchPrompts();
};

const handleSizeChange = (val) => {
    pagination.pageSize = val;
    pagination.pageNum = 1;
    fetchPrompts();
};

const handleCurrentChange = (val) => {
    pagination.pageNum = val;
    fetchPrompts();
};

// 监听变量列表变化，同步到测试变量中
watch(
    variablesList,
    (newList) => {
        // 清理测试变量，只保留当前变量列表中的变量
        Object.keys(testVariables).forEach((key) => {
            delete testVariables[key];
        });
        newList.forEach((v) => {
            if (v.name && v.name.trim()) {
                testVariables[v.name.trim()] =
                    testVariables[v.name.trim()] || "";
            }
        });
    },
    { deep: true },
);

// 初始化
onMounted(async () => {
    await fetchCategories();
    await fetchTags();
    await fetchPrompts();
});
</script>

<style scoped>
.prompts-manager {
    padding: 0;
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
}

.box-card {
    height: 100%;
    border: none;
    border-radius: 0;
    box-shadow: none;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.title {
    font-size: 18px;
    font-weight: bold;
    color: #303133;
}

.content-container {
    display: flex;
    height: calc(100vh - 180px);
    gap: 20px;
    flex: 1;
    padding: 20px;
}

.left-panel {
    width: 450px;
    min-width: 450px;
    border-right: 1px solid #e4e7ed;
    padding-right: 20px;
    display: flex;
    flex-direction: column;
}

.panel-header {
    margin-bottom: 15px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.list-container {
    flex: 1;
    overflow: hidden;
}

.list-item {
    padding: 15px;
    border: 1px solid #e4e7ed;
    border-radius: 6px;
    margin-bottom: 10px;
    cursor: pointer;
    transition: all 0.3s;
    background-color: #fff;
}

.list-item:hover {
    border-color: #409eff;
    box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.list-item.active {
    border-color: #409eff;
    background-color: #f0f9ff;
}

.item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.item-title {
    font-weight: bold;
    color: #303133;
    font-size: 14px;
    flex: 1;
}

.item-actions {
    display: flex;
    gap: 4px;
}

.item-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    flex-wrap: wrap;
}

.item-time {
    font-size: 12px;
    color: #909399;
    margin-left: auto;
}

.item-preview {
    font-size: 12px;
    color: #606266;
    line-height: 1.4;
    margin-bottom: 8px;
}

.item-tags {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
}

.pagination-mini {
    margin-top: 15px;
    text-align: center;
}

.right-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.editor-container {
    display: flex;
    flex-direction: column;
    height: 100%;
}

.editor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid #e4e7ed;
}

.title-input {
    flex: 1;
    margin-right: 20px;
}

.editor-actions {
    display: flex;
    gap: 10px;
}

.editor-meta {
    margin-bottom: 20px;
}

.editor-content {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.variables-editor {
    padding: 10px 0;
}

.variable-item {
    display: flex;
    gap: 10px;
    margin: 10px 0;
    align-items: center;
}

.variable-input {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}

.variable-input label {
    min-width: 80px;
    font-weight: bold;
}

.test-result {
    margin-top: 20px;
}

.empty-editor {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #909399;
}

@media (max-width: 1200px) {
    .content-container {
        flex-direction: column;
        height: auto;
    }

    .left-panel {
        width: 100%;
        min-width: auto;
        border-right: none;
        border-bottom: 1px solid #e4e7ed;
        padding-right: 0;
        padding-bottom: 20px;
        margin-bottom: 20px;
    }

    .list-container {
        height: 300px;
    }
}

@media (max-width: 768px) {
    .prompts-manager {
        padding: 0;
    }

    .content-container {
        gap: 10px;
        padding: 10px;
    }
}
</style>

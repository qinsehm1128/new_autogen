<template>
    <div class="api-key-manager">
        <el-card class="box-card">
            <template #header>
                <div class="card-header">
                    <span class="title">API Key 管理</span>
                    <el-button type="primary" @click="handleAdd">
                        <el-icon><Plus /></el-icon>
                        新增 API Key
                    </el-button>
                </div>
            </template>

            <!-- 搜索区域 -->
            <div class="search-container">
                <el-row :gutter="20">
                    <el-col :span="6">
                        <el-input
                            v-model="searchForm.keyword"
                            placeholder="搜索API Key或模型名称"
                            @input="handleSearch"
                            clearable
                        >
                            <template #prefix>
                                <el-icon><Search /></el-icon>
                            </template>
                        </el-input>
                    </el-col>
                    <el-col :span="4">
                        <el-select
                            v-model="searchForm.status"
                            placeholder="状态筛选"
                            clearable
                        >
                            <el-option label="激活" value="active" />
                            <el-option label="禁用" value="inactive" />
                        </el-select>
                    </el-col>
                    <el-col :span="4">
                        <el-button type="primary" @click="handleSearch"
                            >搜索</el-button
                        >
                        <el-button @click="handleReset">重置</el-button>
                    </el-col>
                </el-row>
            </div>

            <!-- 表格区域 -->
            <div class="table-container">
                <el-table
                    :data="tableData"
                    v-loading="loading"
                    border
                    stripe
                    height="100%"
                    style="width: 100%"
                    @selection-change="handleSelectionChange"
                >
                    <el-table-column type="selection" width="55" />
                    <el-table-column prop="id" label="ID" width="80" />
                    <el-table-column
                        prop="api_key"
                        label="API Key"
                        min-width="200"
                    >
                        <template #default="scope">
                            <el-text
                                class="api-key-text"
                                :class="{ masked: !scope.row.showKey }"
                            >
                                {{
                                    scope.row.showKey
                                        ? scope.row.api_key
                                        : maskApiKey(scope.row.api_key)
                                }}
                            </el-text>
                            <el-button
                                type="text"
                                size="small"
                                @click="toggleApiKeyVisibility(scope.row)"
                                class="toggle-btn"
                            >
                                <el-icon>
                                    <View v-if="!scope.row.showKey" />
                                    <Hide v-else />
                                </el-icon>
                            </el-button>
                        </template>
                    </el-table-column>
                    <el-table-column
                        prop="model_name"
                        label="模型名称"
                        min-width="150"
                    />
                    <el-table-column
                        prop="model_url"
                        label="模型地址"
                        min-width="200"
                    />
                    <el-table-column
                        prop="description"
                        label="描述"
                        min-width="150"
                    />
                    <el-table-column
                        prop="provider"
                        label="提供商"
                        width="120"
                    />
                    <el-table-column prop="status" label="状态" width="100">
                        <template #default="scope">
                            <el-tag
                                :type="
                                    scope.row.status === 'active'
                                        ? 'success'
                                        : 'danger'
                                "
                            >
                                {{
                                    scope.row.status === "active"
                                        ? "激活"
                                        : "禁用"
                                }}
                            </el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column
                        prop="created_at"
                        label="创建时间"
                        width="180"
                    >
                        <template #default="scope">
                            {{ formatDate(scope.row.created_at) }}
                        </template>
                    </el-table-column>
                    <el-table-column label="操作" width="300" fixed="right">
                        <template #default="scope">
                            <el-button
                                type="primary"
                                size="small"
                                @click="handleEdit(scope.row)"
                            >
                                <el-icon><Edit /></el-icon>
                                编辑
                            </el-button>
                            <el-button
                                type="success"
                                size="small"
                                @click="handleTest(scope.row)"
                            >
                                <el-icon><Connection /></el-icon>
                                测试
                            </el-button>
                            <el-button
                                type="danger"
                                size="small"
                                @click="handleDelete(scope.row)"
                            >
                                <el-icon><Delete /></el-icon>
                                删除
                            </el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </div>

            <!-- 批量操作 -->
            <div class="batch-operations" v-if="selectedRows.length > 0">
                <el-alert
                    :title="`已选择 ${selectedRows.length} 项`"
                    type="info"
                    show-icon
                    :closable="false"
                />
                <div class="batch-buttons">
                    <el-button type="danger" @click="handleBatchDelete"
                        >批量删除</el-button
                    >
                    <el-button @click="handleBatchStatus('active')"
                        >批量激活</el-button
                    >
                    <el-button @click="handleBatchStatus('inactive')"
                        >批量禁用</el-button
                    >
                </div>
            </div>

            <!-- 分页 -->
            <div class="pagination-container">
                <el-pagination
                    v-model:current-page="pagination.pageNum"
                    v-model:page-size="pagination.pageSize"
                    :page-sizes="[10, 20, 50, 100]"
                    layout="total, sizes, prev, pager, next, jumper"
                    :total="pagination.total"
                    @size-change="handleSizeChange"
                    @current-change="handleCurrentChange"
                />
            </div>
        </el-card>

        <!-- 新增/编辑对话框 -->
        <el-dialog
            v-model="dialogVisible"
            :title="dialogTitle"
            width="600px"
            :before-close="handleDialogClose"
        >
            <el-form
                ref="formRef"
                :model="form"
                :rules="formRules"
                label-width="100px"
                @submit.prevent
            >
                <el-form-item label="API Key" prop="api_key">
                    <el-input
                        v-model="form.api_key"
                        placeholder="请输入API Key"
                        type="textarea"
                        :rows="2"
                    />
                </el-form-item>
                <el-form-item label="模型名称" prop="model_name">
                    <el-input
                        v-model="form.model_name"
                        placeholder="请输入模型名称"
                    />
                </el-form-item>
                <el-form-item label="模型地址" prop="model_url">
                    <el-input
                        v-model="form.model_url"
                        placeholder="请输入模型地址"
                    />
                </el-form-item>
                <el-form-item label="提供商" prop="provider">
                    <el-select
                        v-model="form.provider"
                        placeholder="请选择提供商"
                    >
                        <el-option label="OpenAI" value="openai" />
                        <el-option label="Anthropic" value="anthropic" />
                        <el-option label="Google" value="google" />
                        <el-option label="Azure" value="azure" />
                        <el-option label="其他" value="other" />
                    </el-select>
                </el-form-item>
                <el-form-item label="描述" prop="description">
                    <el-input
                        v-model="form.description"
                        type="textarea"
                        :rows="3"
                        placeholder="请输入描述信息"
                    />
                </el-form-item>
                <el-form-item label="最大Token" prop="max_tokens">
                    <el-input-number
                        v-model="form.max_tokens"
                        :min="1"
                        :max="100000"
                        placeholder="最大Token数"
                    />
                </el-form-item>
                <el-form-item label="超时时间(秒)" prop="timeout">
                    <el-input-number
                        v-model="form.timeout"
                        :min="1"
                        :max="300"
                        placeholder="超时时间"
                    />
                </el-form-item>
                <el-form-item label="状态" prop="status">
                    <el-radio-group v-model="form.status">
                        <el-radio value="active">激活</el-radio>
                        <el-radio value="inactive">禁用</el-radio>
                    </el-radio-group>
                </el-form-item>
            </el-form>
            <template #footer>
                <div class="dialog-footer">
                    <el-button @click="handleDialogClose">取消</el-button>
                    <el-button
                        type="primary"
                        @click="handleSubmit"
                        :loading="submitLoading"
                    >
                        确定
                    </el-button>
                </div>
            </template>
        </el-dialog>

        <!-- 测试结果对话框 -->
        <el-dialog
            v-model="testDialogVisible"
            title="API Key 测试结果"
            width="500px"
        >
            <div class="test-result">
                <el-result
                    :icon="testResult.success ? 'success' : 'error'"
                    :title="testResult.success ? '测试成功' : '测试失败'"
                    :sub-title="testResult.message"
                >
                    <template #extra v-if="testResult.response_time">
                        <p>
                            响应时间:
                            {{ testResult.response_time.toFixed(2) }}ms
                        </p>
                    </template>
                </el-result>
            </div>
        </el-dialog>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
    Plus,
    Search,
    Edit,
    Delete,
    View,
    Hide,
    Connection,
} from "@element-plus/icons-vue";
import {
    listApiKeys,
    addApiKey,
    updateApiKey,
    delApiKey,
    delApiKeys,
    batchUpdateApiKeyStatus,
    testApiKey,
} from "@/api/chat_config";

// 响应式数据
const loading = ref(false);
const submitLoading = ref(false);
const dialogVisible = ref(false);
const testDialogVisible = ref(false);
const dialogTitle = ref("");
const isEdit = ref(false);
const selectedRows = ref([]);
const formRef = ref();
const tableData = ref([]);

// 搜索表单
const searchForm = reactive({
    keyword: "",
    status: "",
});

// 分页
const pagination = reactive({
    pageNum: 1,
    pageSize: 10,
    total: 0,
});

// 表单数据
const form = reactive({
    id: null,
    api_key: "",
    model_name: "",
    model_url: "",
    description: "",
    provider: "",
    max_tokens: null,
    timeout: null,
    status: "active",
});

// 测试结果
const testResult = reactive({
    success: false,
    message: "",
    response_time: null,
});

// 表单验证规则
const formRules = {
    api_key: [
        { required: true, message: "请输入API Key", trigger: "blur" },
        { min: 10, message: "API Key长度不能少于10位", trigger: "blur" },
    ],
    model_name: [
        { required: true, message: "请输入模型名称", trigger: "blur" },
    ],
    model_url: [
        { required: true, message: "请输入模型地址", trigger: "blur" },
        { type: "url", message: "请输入正确的URL格式", trigger: "blur" },
    ],
};

// 方法
const maskApiKey = (apiKey) => {
    if (!apiKey || apiKey.length < 8) return apiKey;
    return (
        apiKey.substring(0, 8) +
        "*".repeat(Math.max(0, apiKey.length - 16)) +
        apiKey.substring(Math.max(8, apiKey.length - 8))
    );
};

const formatDate = (dateString) => {
    if (!dateString) return "";
    return new Date(dateString).toLocaleString("zh-CN");
};

const toggleApiKeyVisibility = (row) => {
    row.showKey = !row.showKey;
};

const fetchData = async () => {
    loading.value = true;
    try {
        const params = {
            pageNum: pagination.pageNum,
            pageSize: pagination.pageSize,
            ...searchForm,
        };

        const response = await listApiKeys(params);
        console.log(response);
        if (response.data && response.data.items) {
            const result = response.data.items;
            tableData.value = result.map((item) => ({
                ...item,
                showKey: false,
            }));
            pagination.total = result.total;
        }
    } catch (error) {
        console.error("获取API Key列表失败:", error);
        ElMessage.error(
            "获取数据失败: " + (error.response?.data?.message || error.message),
        );
    } finally {
        loading.value = false;
    }
};

const handleAdd = () => {
    dialogTitle.value = "新增 API Key";
    isEdit.value = false;
    resetForm();
    dialogVisible.value = true;
};

const handleEdit = (row) => {
    dialogTitle.value = "编辑 API Key";
    isEdit.value = true;
    Object.assign(form, {
        id: row.id,
        api_key: row.api_key,
        model_name: row.model_name,
        model_url: row.model_url,
        description: row.description,
        provider: row.provider,
        max_tokens: row.max_tokens,
        timeout: row.timeout,
        status: row.status,
    });
    dialogVisible.value = true;
};

const handleDelete = async (row) => {
    try {
        await ElMessageBox.confirm(
            `确定要删除 "${row.model_name}" 吗？`,
            "删除确认",
            {
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                type: "warning",
            },
        );

        await delApiKey(row.id);
        ElMessage.success("删除成功");
        await fetchData();
    } catch (error) {
        if (error !== "cancel") {
            console.error("删除失败:", error);
            ElMessage.error(
                "删除失败: " + (error.response?.data?.message || error.message),
            );
        }
    }
};

const handleTest = async (row) => {
    try {
        loading.value = true;
        const response = await testApiKey({ id: row.id });

        if (response.data && response.data.items) {
            Object.assign(testResult, response.data.items);
            testDialogVisible.value = true;
        }
    } catch (error) {
        console.error("测试失败:", error);
        ElMessage.error(
            "测试失败: " + (error.response?.data?.message || error.message),
        );
    } finally {
        loading.value = false;
    }
};

const handleSelectionChange = (selection) => {
    selectedRows.value = selection;
};

const handleBatchDelete = async () => {
    try {
        await ElMessageBox.confirm(
            `确定要删除选中的 ${selectedRows.value.length} 项吗？`,
            "批量删除确认",
            {
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                type: "warning",
            },
        );

        const ids = selectedRows.value.map((row) => row.id);
        await delApiKeys(ids);
        ElMessage.success("批量删除成功");
        selectedRows.value = [];
        await fetchData();
    } catch (error) {
        if (error !== "cancel") {
            console.error("批量删除失败:", error);
            ElMessage.error(
                "批量删除失败: " +
                    (error.response?.data?.message || error.message),
            );
        }
    }
};

const handleBatchStatus = async (status) => {
    try {
        const ids = selectedRows.value.map((row) => row.id);
        await batchUpdateApiKeyStatus({ ids, status });
        ElMessage.success(`批量${status === "active" ? "激活" : "禁用"}成功`);
        selectedRows.value = [];
        await fetchData();
    } catch (error) {
        console.error("批量操作失败:", error);
        ElMessage.error(
            "批量操作失败: " + (error.response?.data?.message || error.message),
        );
    }
};

const handleSearch = () => {
    pagination.pageNum = 1;
    fetchData();
};

const handleReset = () => {
    searchForm.keyword = "";
    searchForm.status = "";
    pagination.pageNum = 1;
    fetchData();
};

const handleSizeChange = (val) => {
    pagination.pageSize = val;
    pagination.pageNum = 1;
    fetchData();
};

const handleCurrentChange = (val) => {
    pagination.pageNum = val;
    fetchData();
};

const handleDialogClose = () => {
    dialogVisible.value = false;
    resetForm();
};

const resetForm = () => {
    Object.assign(form, {
        id: null,
        api_key: "",
        model_name: "",
        model_url: "",
        description: "",
        provider: "",
        max_tokens: null,
        timeout: null,
        status: "active",
    });
    formRef.value?.clearValidate();
};

const handleSubmit = async () => {
    try {
        await formRef.value?.validate();
        submitLoading.value = true;

        const formData = { ...form };

        if (isEdit.value) {
            await updateApiKey(formData);
            ElMessage.success("编辑成功");
        } else {
            delete formData.id;
            await addApiKey(formData);
            ElMessage.success("新增成功");
        }

        dialogVisible.value = false;
        resetForm();
        await fetchData();
    } catch (error) {
        console.error("提交失败:", error);
        ElMessage.error(
            "提交失败: " + (error.response?.data?.message || error.message),
        );
    } finally {
        submitLoading.value = false;
    }
};

// 初始化
onMounted(() => {
    fetchData();
});
</script>

<style scoped>
.api-key-manager {
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

.search-container {
    margin: 20px;
    margin-bottom: 20px;
    padding: 20px;
    background-color: #f8f9fa;
    border-radius: 6px;
}

.api-key-text {
    font-family: monospace;
    display: inline-block;
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.api-key-text.masked {
    color: #909399;
}

.toggle-btn {
    margin-left: 8px;
    padding: 0 !important;
}

.batch-operations {
    margin: 20px;
    margin-top: 0;
    margin-bottom: 20px;
    padding: 15px;
    background-color: #f0f9ff;
    border-radius: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.batch-buttons {
    display: flex;
    gap: 10px;
}

.pagination-container {
    margin: 20px;
    margin-top: 20px;
    display: flex;
    justify-content: center;
    flex-shrink: 0;
}

.table-container {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    min-height: 400px;
}

.dialog-footer {
    text-align: right;
}

.test-result {
    text-align: center;
}
</style>

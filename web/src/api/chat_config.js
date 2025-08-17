import request from "@/utils/request";

// ==================== API Key 管理接口 ====================

/**
 * 获取API Key列表
 * @param {Object} query - 查询参数
 * @param {number} query.pageNum - 页码，默认1
 * @param {number} query.pageSize - 每页数量，默认10
 * @param {string} query.keyword - 搜索关键词（API Key、模型名称）
 * @param {string} query.status - 状态筛选（active/inactive）
 * @param {string} query.modelName - 模型名称筛选
 * @param {string} query.beginTime - 开始时间
 * @param {string} query.endTime - 结束时间
 * @returns {Promise} 返回API Key列表
 */
export function listApiKeys(query) {
  return request({
    url: "/chat/api-keys/list",
    method: "get",
    params: query,
  });
}

/**
 * 获取API Key详情
 * @param {number|string} id - API Key ID
 * @returns {Promise} 返回API Key详情
 */
export function getApiKey(id) {
  return request({
    url: `/chat/api-keys/${id}`,
    method: "get",
  });
}

/**
 * 新增API Key
 * @param {Object} data - API Key数据
 * @param {string} data.apiKey - API Key（必填）
 * @param {string} data.modelName - 模型名称（必填）
 * @param {string} data.modelUrl - 模型地址（必填）
 * @param {string} data.description - 描述
 * @param {string} data.status - 状态（active/inactive，默认active）
 * @param {string} data.provider - 提供商（openai/anthropic/google等）
 * @param {Object} data.config - 额外配置（JSON对象）
 * @param {number} data.maxTokens - 最大Token数
 * @param {number} data.timeout - 超时时间（秒）
 * @returns {Promise} 返回创建结果
 */
export function addApiKey(data) {
  return request({
    url: "/chat/api-keys",
    method: "post",
    data: data,
  });
}

/**
 * 修改API Key
 * @param {Object} data - API Key数据
 * @param {number|string} data.id - API Key ID（必填）
 * @param {string} data.apiKey - API Key
 * @param {string} data.modelName - 模型名称
 * @param {string} data.modelUrl - 模型地址
 * @param {string} data.description - 描述
 * @param {string} data.status - 状态（active/inactive）
 * @param {string} data.provider - 提供商
 * @param {Object} data.config - 额外配置
 * @param {number} data.maxTokens - 最大Token数
 * @param {number} data.timeout - 超时时间（秒）
 * @returns {Promise} 返回修改结果
 */
export function updateApiKey(data) {
  return request({
    url: "/chat/api-keys",
    method: "put",
    data: data,
  });
}

/**
 * 删除API Key
 * @param {number|string} id - API Key ID
 * @returns {Promise} 返回删除结果
 */
export function delApiKey(id) {
  return request({
    url: `/chat/api-keys/${id}`,
    method: "delete",
  });
}

/**
 * 批量删除API Key
 * @param {Array<number|string>} ids - API Key ID数组
 * @returns {Promise} 返回删除结果
 */
export function delApiKeys(ids) {
  return request({
    url: "/chat/api-keys/batch",
    method: "delete",
    data: { ids },
  });
}

/**
 * 批量修改API Key状态
 * @param {Object} data - 批量操作数据
 * @param {Array<number|string>} data.ids - API Key ID数组
 * @param {string} data.status - 目标状态（active/inactive）
 * @returns {Promise} 返回操作结果
 */
export function batchUpdateApiKeyStatus(data) {
  return request({
    url: "/chat/api-keys/batch/status",
    method: "put",
    data: data,
  });
}

/**
 * 测试API Key连接
 * @param {Object} data - 测试数据
 * @param {number|string} data.id - API Key ID（可选，用于测试已存在的）
 * @param {string} data.apiKey - API Key（可选，用于测试新的）
 * @param {string} data.modelUrl - 模型地址（可选）
 * @param {string} data.modelName - 模型名称（可选）
 * @returns {Promise} 返回测试结果
 */
export function testApiKey(data) {
  return request({
    url: "/chat/api-keys/test",
    method: "post",
    data: data,
  });
}

/**
 * 获取API Key统计信息
 * @returns {Promise} 返回统计数据
 */
export function getApiKeyStats() {
  return request({
    url: "/chat/api-keys/stats",
    method: "get",
  });
}

// ==================== 提示词管理接口 ====================

/**
 * 获取提示词列表
 * @param {Object} query - 查询参数
 * @param {number} query.pageNum - 页码，默认1
 * @param {number} query.pageSize - 每页数量，默认10
 * @param {string} query.keyword - 搜索关键词（提示词标题、内容）
 * @param {string} query.category - 分类筛选（system/role/creative/code/other）
 * @param {Array<string>} query.tags - 标签筛选
 * @param {string} query.beginTime - 开始时间
 * @param {string} query.endTime - 结束时间
 * @returns {Promise} 返回提示词列表
 */
export function listPrompts(query) {
  return request({
    url: "/chat/prompts/list",
    method: "get",
    params: query,
  });
}

/**
 * 获取提示词详情
 * @param {number|string} id - 提示词ID
 * @returns {Promise} 返回提示词详情
 */
export function getPrompt(id) {
  return request({
    url: `/chat/prompts/${id}`,
    method: "get",
  });
}

/**
 * 新增提示词
 * @param {Object} data - 提示词数据
 * @param {string} data.title - 提示词标题（必填）
 * @param {string} data.category - 分类（必填：system/role/creative/code/other）
 * @param {string} data.content - 提示词内容（必填）
 * @param {string} data.description - 描述
 * @param {Array<string>} data.tags - 标签数组
 * @param {boolean} data.isPublic - 是否公开（默认false）
 * @param {Object} data.variables - 变量定义
 * @param {Object} data.config - 额外配置
 * @param {number} data.sort - 排序值
 * @returns {Promise} 返回创建结果
 */
export function addPrompt(data) {
  return request({
    url: "/chat/prompts",
    method: "post",
    data: data,
  });
}

/**
 * 修改提示词
 * @param {Object} data - 提示词数据
 * @param {number|string} data.id - 提示词ID（必填）
 * @param {string} data.title - 提示词标题
 * @param {string} data.category - 分类
 * @param {string} data.content - 提示词内容
 * @param {string} data.description - 描述
 * @param {Array<string>} data.tags - 标签数组
 * @param {boolean} data.isPublic - 是否公开
 * @param {Object} data.variables - 变量定义
 * @param {Object} data.config - 额外配置
 * @param {number} data.sort - 排序值
 * @returns {Promise} 返回修改结果
 */
export function updatePrompt(data) {
  return request({
    url: "/chat/prompts",
    method: "put",
    data: data,
  });
}

/**
 * 删除提示词
 * @param {number|string} id - 提示词ID
 * @returns {Promise} 返回删除结果
 */
export function delPrompt(id) {
  return request({
    url: `/chat/prompts/${id}`,
    method: "delete",
  });
}

/**
 * 批量删除提示词
 * @param {Array<number|string>} ids - 提示词ID数组
 * @returns {Promise} 返回删除结果
 */
export function delPrompts(ids) {
  return request({
    url: "/chat/prompts/batch",
    method: "delete",
    data: { ids },
  });
}

/**
 * 复制提示词
 * @param {number|string} id - 源提示词ID
 * @returns {Promise} 返回复制结果
 */
export function copyPrompt(id) {
  return request({
    url: `/chat/prompts/${id}/copy`,
    method: "post",
  });
}

/**
 * 测试提示词
 * @param {Object} data - 测试数据
 * @param {string} data.content - 提示词内容
 * @param {Object} data.variables - 变量值
 * @param {string} data.testInput - 测试输入
 * @returns {Promise} 返回测试结果
 */
export function testPrompt(data) {
  return request({
    url: "/chat/prompts/test",
    method: "post",
    data: data,
  });
}

/**
 * 获取提示词分类列表
 * @returns {Promise} 返回分类列表
 */
export function getPromptCategories() {
  return request({
    url: "/chat/prompts/categories",
    method: "get",
  });
}

/**
 * 获取提示词标签列表
 * @returns {Promise} 返回标签列表
 */
export function getPromptTags() {
  return request({
    url: "/chat/prompts/tags",
    method: "get",
  });
}

// ==================== 公共接口 ====================

/**
 * 获取系统配置
 * @returns {Promise} 返回系统配置
 */
export function getSystemConfig() {
  return request({
    url: "/chat/config",
    method: "get",
  });
}

/**
 * 更新系统配置
 * @param {Object} data - 配置数据
 * @param {Object} data.apiKeyConfig - API Key配置
 * @param {Object} data.promptConfig - 提示词配置
 * @returns {Promise} 返回更新结果
 */
export function updateSystemConfig(data) {
  return request({
    url: "/chat/config",
    method: "put",
    data: data,
  });
}

/**
 * 获取数据统计
 * @param {Object} query - 查询参数
 * @param {string} query.type - 统计类型（overview/apikeys/prompts）
 * @param {string} query.timeRange - 时间范围（day/week/month/year）
 * @returns {Promise} 返回统计数据
 */
export function getStatistics(query) {
  return request({
    url: "/chat/statistics",
    method: "get",
    params: query,
  });
}

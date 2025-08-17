import request from "@/utils/request";

// ==================== 对话管理接口 ====================

/**
 * 获取对话列表
 * @param {Object} query - 查询参数
 * @param {number} query.pageNum - 页码，默认1
 * @param {number} query.pageSize - 每页数量，默认20
 * @param {string} query.keyword - 搜索关键词（对话标题、内容）
 * @param {string} query.groupId - 分组ID筛选
 * @param {string} query.modelId - 模型ID筛选
 * @param {string} query.beginTime - 开始时间
 * @param {string} query.endTime - 结束时间
 * @returns {Promise} 返回对话列表
 */
export function getChatList(query) {
  return request({
    url: "/chat/conversations/list",
    method: "get",
    params: query,
  });
}

/**
 * 获取对话详情
 * @param {string} chatId - 对话ID
 * @returns {Promise} 返回对话详情
 */
export function getChatDetail(chatId) {
  return request({
    url: `/chat/conversations/${chatId}`,
    method: "get",
  });
}

/**
 * 创建新对话
 * @param {Object} data - 对话数据
 * @param {string} data.title - 对话标题（可选，默认"新对话"）
 * @param {string} data.groupId - 分组ID（可选，默认为默认分组）
 * @param {string} data.modelId - 模型ID（必填）
 * @param {Object} data.config - 对话配置（可选）
 * @param {string} data.description - 对话描述（可选）
 * @returns {Promise} 返回创建的对话信息
 */
export function createChat(data) {
  return request({
    url: "/chat/conversations",
    method: "post",
    data: data,
  });
}

/**
 * 更新对话信息
 * @param {Object} data - 对话数据
 * @param {string} data.id - 对话ID（必填）
 * @param {string} data.title - 对话标题
 * @param {string} data.groupId - 分组ID
 * @param {string} data.modelId - 模型ID
 * @param {Object} data.config - 对话配置
 * @param {string} data.description - 对话描述
 * @returns {Promise} 返回更新结果
 */
export function updateChat(data) {
  return request({
    url: `/chat/conversations/${data.id}`,
    method: "put",
    data: data,
  });
}

/**
 * 删除对话
 * @param {string} chatId - 对话ID
 * @returns {Promise} 返回删除结果
 */
export function deleteChat(chatId) {
  return request({
    url: `/chat/conversations/${chatId}`,
    method: "delete",
  });
}

/**
 * 批量删除对话
 * @param {Array<string>} chatIds - 对话ID数组
 * @returns {Promise} 返回删除结果
 */
export function batchDeleteChats(chatIds) {
  return request({
    url: "/chat/conversations/batch",
    method: "delete",
    data: { ids: chatIds },
  });
}

/**
 * 清空对话消息
 * @param {string} chatId - 对话ID
 * @returns {Promise} 返回清空结果
 */
export function clearChatMessages(chatId) {
  return request({
    url: `/chat/conversations/${chatId}/messages`,
    method: "delete",
  });
}

// ==================== 消息管理接口 ====================

/**
 * 获取对话消息列表
 * @param {string} chatId - 对话ID
 * @param {Object} query - 查询参数
 * @param {number} query.pageNum - 页码，默认1
 * @param {number} query.pageSize - 每页数量，默认50
 * @param {string} query.messageType - 消息类型筛选（text/image/file）
 * @returns {Promise} 返回消息列表
 */
export function getChatMessages(chatId, query = {}) {
  return request({
    url: `/chat/conversations/${chatId}/messages`,
    method: "get",
    params: query,
  });
}

/**
 * 发送消息
 * @param {Object} data - 消息数据
 * @param {string} data.chatId - 对话ID（必填）
 * @param {string} data.content - 消息内容（必填）
 * @param {string} data.type - 消息类型（text/image/file，默认text）
 * @param {Array} data.files - 附件列表（可选）
 * @param {Object} data.metadata - 消息元数据（可选）
 * @param {boolean} data.stream - 是否流式响应（默认false）
 * @returns {Promise} 返回发送结果
 */
export function sendMessage(data) {
  return request({
    url: "/chat/messages",
    method: "post",
    data: data,
  });
}

/**
 * 发送流式消息
 * @param {Object} data - 消息数据
 * @param {function} onMessage - 消息回调函数
 * @param {function} onError - 错误回调函数
 * @param {function} onComplete - 完成回调函数
 * @returns {Promise} 返回流式响应控制器
 */
export function sendStreamMessage(data, onMessage, onError, onComplete) {
  return new Promise((resolve, reject) => {
    const eventSource = new EventSource(
      `/api/chat/messages/stream?${new URLSearchParams(data)}`,
    );

    eventSource.onmessage = function (event) {
      try {
        const response = JSON.parse(event.data);
        if (onMessage) onMessage(response);
      } catch (error) {
        if (onError) onError(error);
      }
    };

    eventSource.onerror = function (error) {
      eventSource.close();
      if (onError) onError(error);
      reject(error);
    };

    eventSource.addEventListener("complete", function (event) {
      eventSource.close();
      if (onComplete) onComplete();
      resolve();
    });

    // 返回控制器，允许取消请求
    resolve({
      cancel: () => {
        eventSource.close();
      },
    });
  });
}

/**
 * 重新生成消息
 * @param {Object} data - 重新生成参数
 * @param {string} data.chatId - 对话ID
 * @param {string} data.messageId - 要重新生成的消息ID
 * @param {Object} data.config - 生成配置（可选）
 * @returns {Promise} 返回重新生成的消息
 */
export function regenerateMessage(data) {
  return request({
    url: "/chat/messages/regenerate",
    method: "post",
    data: data,
  });
}

/**
 * 删除消息
 * @param {string} messageId - 消息ID
 * @returns {Promise} 返回删除结果
 */
export function deleteMessage(messageId) {
  return request({
    url: `/chat/messages/${messageId}`,
    method: "delete",
  });
}

/**
 * 编辑消息
 * @param {Object} data - 消息数据
 * @param {string} data.messageId - 消息ID（必填）
 * @param {string} data.content - 新的消息内容（必填）
 * @returns {Promise} 返回编辑结果
 */
export function editMessage(data) {
  return request({
    url: `/chat/messages/${data.messageId}`,
    method: "put",
    data: { content: data.content },
  });
}

// ==================== 对话分组管理接口 ====================

/**
 * 获取对话分组列表
 * @param {Object} query - 查询参数
 * @param {boolean} query.includeChats - 是否包含对话列表（默认true）
 * @returns {Promise} 返回分组列表
 */
export function getChatGroups(query = {}) {
  return request({
    url: "/chat/groups",
    method: "get",
    params: query,
  });
}

/**
 * 创建对话分组
 * @param {Object} data - 分组数据
 * @param {string} data.name - 分组名称（必填）
 * @param {string} data.description - 分组描述（可选）
 * @param {string} data.color - 分组颜色（可选）
 * @param {number} data.sort - 排序值（可选）
 * @returns {Promise} 返回创建的分组信息
 */
export function createChatGroup(data) {
  return request({
    url: "/chat/groups",
    method: "post",
    data: data,
  });
}

/**
 * 更新对话分组
 * @param {Object} data - 分组数据
 * @param {string} data.id - 分组ID（必填）
 * @param {string} data.name - 分组名称
 * @param {string} data.description - 分组描述
 * @param {string} data.color - 分组颜色
 * @param {number} data.sort - 排序值
 * @returns {Promise} 返回更新结果
 */
export function updateChatGroup(data) {
  return request({
    url: `/chat/groups/${data.id}`,
    method: "put",
    data: data,
  });
}

/**
 * 删除对话分组
 * @param {string} groupId - 分组ID
 * @param {boolean} deleteChats - 是否同时删除分组内的对话（默认false，会将对话移动到默认分组）
 * @returns {Promise} 返回删除结果
 */
export function deleteChatGroup(groupId, deleteChats = false) {
  return request({
    url: `/chat/groups/${groupId}`,
    method: "delete",
    params: { deleteChats },
  });
}

/**
 * 移动对话到分组
 * @param {Object} data - 移动数据
 * @param {string} data.chatId - 对话ID
 * @param {string} data.targetGroupId - 目标分组ID
 * @returns {Promise} 返回移动结果
 */
export function moveChatToGroup(data) {
  return request({
    url: `/chat/conversations/${data.chatId}/move`,
    method: "put",
    data: { groupId: data.targetGroupId },
  });
}

/**
 * 批量移动对话到分组
 * @param {Object} data - 移动数据
 * @param {Array<string>} data.chatIds - 对话ID数组
 * @param {string} data.targetGroupId - 目标分组ID
 * @returns {Promise} 返回移动结果
 */
export function batchMoveChatToGroup(data) {
  return request({
    url: "/chat/conversations/batch/move",
    method: "put",
    data: data,
  });
}

// ==================== 模型管理接口 ====================

/**
 * 获取可用模型列表
 * @param {Object} query - 查询参数
 * @param {boolean} query.activeOnly - 是否只返回激活的模型（默认true）
 * @param {string} query.provider - 提供商筛选
 * @returns {Promise} 返回模型列表
 */
export function getAvailableModels(query = {}) {
  return request({
    url: "/chat/models/available",
    method: "get",
    params: query,
  });
}

/**
 * 测试模型连接
 * @param {Object} data - 测试数据
 * @param {string} data.modelId - 模型ID
 * @param {string} data.testMessage - 测试消息（可选，默认"Hello"）
 * @returns {Promise} 返回测试结果
 */
export function testModel(data) {
  return request({
    url: "/chat/models/test",
    method: "post",
    data: data,
  });
}

/**
 * 获取模型使用统计
 * @param {Object} query - 查询参数
 * @param {string} query.timeRange - 时间范围（day/week/month/year）
 * @param {string} query.modelId - 模型ID筛选
 * @returns {Promise} 返回统计数据
 */
export function getModelStats(query = {}) {
  return request({
    url: "/chat/models/stats",
    method: "get",
    params: query,
  });
}

// ==================== 文件上传接口 ====================

/**
 * 上传文件
 * @param {FormData} formData - 包含文件的FormData
 * @param {function} onProgress - 上传进度回调函数
 * @returns {Promise} 返回上传结果
 */
export function uploadFile(formData, onProgress) {
  return request({
    url: "/chat/upload",
    method: "post",
    data: formData,
    headers: {
      "Content-Type": "multipart/form-data",
    },
    onUploadProgress: onProgress,
  });
}

/**
 * 删除文件
 * @param {string} fileId - 文件ID
 * @returns {Promise} 返回删除结果
 */
export function deleteFile(fileId) {
  return request({
    url: `/chat/files/${fileId}`,
    method: "delete",
  });
}

/**
 * 获取文件信息
 * @param {string} fileId - 文件ID
 * @returns {Promise} 返回文件信息
 */
export function getFileInfo(fileId) {
  return request({
    url: `/chat/files/${fileId}`,
    method: "get",
  });
}

// ==================== 对话导入导出接口 ====================

/**
 * 导出对话
 * @param {Object} data - 导出参数
 * @param {string} data.chatId - 对话ID
 * @param {string} data.format - 导出格式（json/markdown/txt）
 * @param {boolean} data.includeSystemMessages - 是否包含系统消息（默认false）
 * @returns {Promise} 返回导出文件
 */
export function exportChat(data) {
  return request({
    url: "/chat/export",
    method: "post",
    data: data,
    responseType: "blob",
  });
}

/**
 * 批量导出对话
 * @param {Object} data - 导出参数
 * @param {Array<string>} data.chatIds - 对话ID数组
 * @param {string} data.format - 导出格式（json/markdown/txt）
 * @param {boolean} data.includeSystemMessages - 是否包含系统消息（默认false）
 * @returns {Promise} 返回导出文件
 */
export function batchExportChats(data) {
  return request({
    url: "/chat/export/batch",
    method: "post",
    data: data,
    responseType: "blob",
  });
}

/**
 * 导入对话
 * @param {FormData} formData - 包含文件的FormData
 * @param {string} groupId - 目标分组ID（可选）
 * @returns {Promise} 返回导入结果
 */
export function importChat(formData, groupId) {
  const url = groupId
    ? `/chat/import?groupId=${groupId}`
    : "/chat/import";

  return request({
    url: url,
    method: "post",
    data: formData,
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
}

// ==================== 搜索接口 ====================

/**
 * 搜索对话和消息
 * @param {Object} query - 搜索参数
 * @param {string} query.keyword - 搜索关键词（必填）
 * @param {string} query.type - 搜索类型（all/chat/message，默认all）
 * @param {string} query.groupId - 分组ID筛选
 * @param {string} query.modelId - 模型ID筛选
 * @param {string} query.beginTime - 开始时间
 * @param {string} query.endTime - 结束时间
 * @param {number} query.pageNum - 页码，默认1
 * @param {number} query.pageSize - 每页数量，默认20
 * @returns {Promise} 返回搜索结果
 */
export function searchChats(query) {
  return request({
    url: "/chat/search",
    method: "get",
    params: query,
  });
}

// ==================== 设置接口 ====================

/**
 * 获取用户聊天设置
 * @returns {Promise} 返回用户设置
 */
export function getChatSettings() {
  return request({
    url: "/chat/settings",
    method: "get",
  });
}

/**
 * 更新用户聊天设置
 * @param {Object} data - 设置数据
 * @param {Object} data.preferences - 用户偏好设置
 * @param {Object} data.defaultConfig - 默认对话配置
 * @param {boolean} data.autoSave - 是否自动保存对话
 * @param {string} data.theme - 主题设置
 * @returns {Promise} 返回更新结果
 */
export function updateChatSettings(data) {
  return request({
    url: "/chat/settings",
    method: "put",
    data: data,
  });
}

// ==================== 实用工具函数 ====================

/**
 * 生成对话标题
 * @param {Object} data - 生成参数
 * @param {string} data.content - 对话内容
 * @param {number} data.maxLength - 最大长度（默认50）
 * @returns {Promise} 返回生成的标题
 */
export function generateChatTitle(data) {
  return request({
    url: "/chat/utils/generate-title",
    method: "post",
    data: data,
  });
}

/**
 * 获取对话统计信息
 * @param {Object} query - 查询参数
 * @param {string} query.timeRange - 时间范围（day/week/month/year）
 * @param {string} query.groupId - 分组ID筛选
 * @returns {Promise} 返回统计信息
 */
export function getChatStatistics(query = {}) {
  return request({
    url: "/chat/statistics",
    method: "get",
    params: query,
  });
}

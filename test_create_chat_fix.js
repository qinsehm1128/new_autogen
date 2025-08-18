// 测试创建对话的数据类型修复
console.log('🧪 测试创建对话API数据类型修复...');

// 模拟API Key数据（从后端返回）
const mockApiKeyResponse = {
    code: 200,
    data: {
        items: [
            {
                id: 1,                    // 数字类型 - API Key ID
                model_name: "gpt-4",      // 字符串类型 - 模型名称
                provider: "openai",
                status: "active"
            },
            {
                id: 2,
                model_name: "gpt-3.5-turbo",
                provider: "openai", 
                status: "active"
            }
        ]
    }
};

// 前端处理后的模型数据
const processedModels = mockApiKeyResponse.data.items.map(item => ({
    id: item.id,                    // API Key ID (数字) - 用于选择器的value
    modelId: item.model_name,       // 模型名称 (字符串) - 用于后端API
    name: item.model_name,          // 显示名称
    provider: item.provider,
    status: item.status
}));

console.log('📊 处理后的模型数据:');
console.table(processedModels);

// 模拟用户选择
const selectedModel = 1; // 用户选择了第一个模型（API Key ID）
const selectedPrompt = 1; // 用户选择了第一个提示词

// 获取选中的模型信息
const selectedModelInfo = processedModels.find(m => m.id === selectedModel);

if (!selectedModelInfo) {
    console.error('❌ 选中的模型信息不存在');
} else {
    console.log('✅ 选中的模型信息:', selectedModelInfo);
    
    // 构造发送给后端的数据
    const chatData = {
        title: "新对话",
        model_id: selectedModelInfo.modelId,  // 字符串类型: "gpt-4"
        api_key_id: selectedModel,            // 数字类型: 1
        prompt_id: selectedPrompt,            // 数字类型: 1
        group_id: 1                          // 数字类型: 1
    };
    
    console.log('📤 发送给后端的数据:');
    console.log(JSON.stringify(chatData, null, 2));
    
    // 验证数据类型
    console.log('\n🔍 数据类型验证:');
    console.log(`model_id: ${typeof chatData.model_id} (期望: string) - ${typeof chatData.model_id === 'string' ? '✅' : '❌'}`);
    console.log(`api_key_id: ${typeof chatData.api_key_id} (期望: number) - ${typeof chatData.api_key_id === 'number' ? '✅' : '❌'}`);
    console.log(`prompt_id: ${typeof chatData.prompt_id} (期望: number) - ${typeof chatData.prompt_id === 'number' ? '✅' : '❌'}`);
    console.log(`group_id: ${typeof chatData.group_id} (期望: number) - ${typeof chatData.group_id === 'number' ? '✅' : '❌'}`);
    
    // 模拟后端验证
    const backendExpected = {
        model_id: 'string',
        api_key_id: 'number',
        prompt_id: 'number', 
        group_id: 'number'
    };
    
    let allTypesCorrect = true;
    for (const [field, expectedType] of Object.entries(backendExpected)) {
        const actualType = typeof chatData[field];
        if (actualType !== expectedType) {
            console.error(`❌ ${field}: 期望 ${expectedType}, 实际 ${actualType}`);
            allTypesCorrect = false;
        }
    }
    
    if (allTypesCorrect) {
        console.log('\n🎉 所有数据类型都正确！创建对话应该成功。');
    } else {
        console.log('\n💥 数据类型不匹配，会导致后端验证失败。');
    }
}

// 测试前后对比
console.log('\n📋 修复前后对比:');
console.log('修复前:');
console.log('  model_id: 1 (number) ❌');
console.log('  api_key_id: 1 (number) ✅');

console.log('修复后:');
console.log('  model_id: "gpt-4" (string) ✅');
console.log('  api_key_id: 1 (number) ✅');

console.log('\n✅ 创建对话数据类型修复测试完成！');

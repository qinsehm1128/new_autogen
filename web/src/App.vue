<template>
    <el-container class="app-container">
        <el-header class="app-header">
            <div class="header-content">
                <h1 class="app-title">AI 模型管理系统</h1>
                <el-menu
                    :default-active="$route.path"
                    mode="horizontal"
                    @select="handleMenuSelect"
                    class="header-menu"
                >
                    <el-menu-item index="/api-keys">
                        <el-icon><Key /></el-icon>
                        <span>API Key 管理</span>
                    </el-menu-item>
                    <el-menu-item index="/rules-prompts">
                        <el-icon><Document /></el-icon>
                        <span>规则和提示词</span>
                    </el-menu-item>
                    <el-menu-item index="/ai-chat">
                        <el-icon><ChatRound /></el-icon>
                        <span>AI 对话</span>
                    </el-menu-item>

                    <el-menu-item index="/ai-new-chat">
                        <el-icon><ChatRound /></el-icon>
                        <span>AI 对话</span>
                    </el-menu-item>
                </el-menu>
            </div>
        </el-header>

        <el-main class="app-main">
            <router-view />
        </el-main>
    </el-container>
</template>

<script setup>
import { useRouter } from "vue-router";
import { Key, Document, ChatRound } from "@element-plus/icons-vue";

const router = useRouter();

const handleMenuSelect = (index) => {
    router.push(index);
};
</script>

<style scoped>
.app-container {
    height: 100vh;
    background-color: #f5f5f5;
}

.app-header {
    background-color: #fff;
    border-bottom: 1px solid #e4e7ed;
    padding: 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 100%;
    padding: 0 20px;
    max-width: 1400px;
    margin: 0 auto;
    min-width: 600px;
}

.app-title {
    color: #409eff;
    font-size: 24px;
    font-weight: bold;
    margin: 0;
    flex-shrink: 0;
    margin-right: 20px;
}

.header-menu {
    border-bottom: none;
    flex-shrink: 0;
    min-width: 420px;
    overflow: visible;
}

.header-menu .el-menu-item {
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
    padding: 0 20px;
    min-width: 140px;
    justify-content: center;
}

.app-main {
    padding: 20px;
    margin: 0 auto;
    width: 100%;
}

/* 响应式布局 */
@media (max-width: 1024px) {
    .header-content {
        padding: 0 15px;
        min-width: 500px;
    }

    .app-title {
        font-size: 20px;
        margin-right: 15px;
    }

    .header-menu .el-menu-item {
        padding: 0 16px;
        min-width: 120px;
    }
}

@media (max-width: 768px) {
    .header-content {
        padding: 0 10px;
        min-width: 400px;
    }

    .app-title {
        font-size: 18px;
        margin-right: 10px;
    }

    .header-menu {
        min-width: 360px;
    }

    .header-menu .el-menu-item {
        padding: 0 12px;
        min-width: 100px;
        font-size: 14px;
    }

    .header-menu .el-menu-item span {
        display: none;
    }

    .header-menu .el-menu-item .el-icon {
        margin: 0;
    }
}

/* 全局样式 */
:global(.el-container) {
    min-height: 100vh;
}

:global(.el-main) {
    overflow: auto;
}
</style>

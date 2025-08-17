import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import ElementPlusX from "vue-element-plus-x";
import * as ElementPlusIconsVue from "@element-plus/icons-vue";

import App from "./App.vue";

// 导入页面组件
import ApiKeyManager from "./components/ApiKeyManager.vue";
import RulesPrompts from "./components/PromptsManager.vue";
import AiChat from "./components/AiChat.vue";

// 配置路由
const routes = [
  { path: "/", redirect: "/api-keys" },
  { path: "/api-keys", component: ApiKeyManager },
  { path: "/rules-prompts", component: RulesPrompts },
  { path: "/ai-chat", component: AiChat },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

const app = createApp(App);
const pinia = createPinia();

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

app.use(pinia);
app.use(ElementPlus);
app.use(ElementPlusX);
app.use(router);
app.mount("#app");

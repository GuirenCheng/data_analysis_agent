import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import zhCn from "element-plus/es/locale/lang/zh-cn";
import {
  ArrowLeft,
  DataAnalysis,
  FolderOpened,
  Lock,
  Monitor,
  Plus,
  Search,
  Setting,
  UploadFilled,
  User,
  VideoPlay,
} from "@element-plus/icons-vue";

import App from "./App.vue";
import router from "./router";

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.use(ElementPlus, { locale: zhCn });

// 全局注册本项目实际用到的图标（避免全量导入整个图标库）
const icons = {
  ArrowLeft,
  DataAnalysis,
  FolderOpened,
  Lock,
  Monitor,
  Plus,
  Search,
  Setting,
  UploadFilled,
  User,
  VideoPlay,
};
for (const [key, component] of Object.entries(icons)) {
  app.component(key, component);
}

app.mount("#app");

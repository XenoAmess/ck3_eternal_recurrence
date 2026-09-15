import { createApp } from 'vue'
import {
  ElAlert,
  ElButton,
  ElCollapse,
  ElCollapseItem,
  ElConfigProvider,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElOption,
  ElProgress,
  ElScrollbar,
  ElSelect,
  ElSpace,
  ElTabPane,
  ElTable,
  ElTableColumn,
  ElTabs,
  ElTag,
} from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import { registerCoatOfArmsServiceWorker } from './serviceWorkerRegistration'
import './styles.css'

const app = createApp(App)
for (const component of [
  ElAlert,
  ElButton,
  ElCollapse,
  ElCollapseItem,
  ElConfigProvider,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElOption,
  ElProgress,
  ElScrollbar,
  ElSelect,
  ElSpace,
  ElTabPane,
  ElTable,
  ElTableColumn,
  ElTabs,
  ElTag,
]) app.component(component.name!, component)
app.mount('#app')

if (import.meta.env.PROD && import.meta.env.VITE_DISABLE_SERVICE_WORKER !== 'true') {
  void registerCoatOfArmsServiceWorker().catch(() => {
    // Offline support is an enhancement; a registration failure must not
    // prevent the editor's fully local online flow from starting.
  })
}

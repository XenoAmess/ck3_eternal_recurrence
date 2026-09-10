<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { parseCoatOfArms } from './domain/parser'
import { serializeCoatOfArms } from './domain/serializer'
import {
  createCoatOfArms,
  createColoredEmblem,
  createInstance,
  type CoatOfArms,
  type Diagnostic,
} from './domain/types'

const sample = `coa = {
    pattern = "pattern_solid.dds"
    color1 = rgb { 32 64 160 }
    color2 = white
    color3 = red

    colored_emblem = {
        texture = "ce_martlet.dds"
        color1 = yellow
        color2 = red
        color3 = white
        mask = { 1 }

        instance = {
            position = { 0.30 0.50 }
            scale = { 0.35 0.35 }
            rotation = -20
            depth = 1.01
        }
        instance = {
            position = { 0.70 0.50 }
            scale = { -0.35 0.35 }
            rotation = 20
            depth = 2.01
        }
    }
}`

const source = ref(sample)
const coatOfArms = ref<CoatOfArms>(createCoatOfArms())
const diagnostics = ref<Diagnostic[]>([])
const selectedEmblem = ref(0)

const output = computed(() => serializeCoatOfArms(coatOfArms.value))
const activeEmblem = computed(() => coatOfArms.value.coloredEmblems[selectedEmblem.value])
const errorCount = computed(() => diagnostics.value.filter((item) => item.severity === 'error').length)

const namedColors: Record<string, string> = {
  black: '#22201e', blue: '#315b9a', green: '#497554', red: '#9b3c35',
  white: '#eee7d8', yellow: '#d2a84b', orange: '#bb6b38', purple: '#6b4b7e',
}

function cssColor(value: string): string {
  const normalized = value.trim().replaceAll('"', '').toLowerCase()
  if (namedColors[normalized]) return namedColors[normalized]
  const rgb = normalized.match(/^rgb\s*\{\s*(\d+)\s+(\d+)\s+(\d+)\s*}$/)
  if (rgb) return `rgb(${rgb[1]} ${rgb[2]} ${rgb[3]})`
  return '#6f6254'
}

function importSource() {
  const result = parseCoatOfArms(source.value)
  coatOfArms.value = result.coatOfArms
  diagnostics.value = result.diagnostics
  selectedEmblem.value = 0
  if (result.diagnostics.some((item) => item.severity === 'error')) {
    ElMessage.error('已解析，但存在阻止确定性导出的诊断')
  } else {
    ElMessage.success('已导入为结构化纹章')
  }
}

async function copyOutput() {
  await navigator.clipboard.writeText(output.value)
  ElMessage.success('CK3 纹章代码已复制；多行换行使用 CRLF')
}

function loadSample() {
  source.value = sample
  importSource()
}

function reset() {
  coatOfArms.value = createCoatOfArms()
  diagnostics.value = []
  selectedEmblem.value = 0
}

function addEmblem() {
  coatOfArms.value.coloredEmblems.push(createColoredEmblem())
  selectedEmblem.value = coatOfArms.value.coloredEmblems.length - 1
}

function removeEmblem(index: number) {
  coatOfArms.value.coloredEmblems.splice(index, 1)
  selectedEmblem.value = Math.max(0, Math.min(selectedEmblem.value, coatOfArms.value.coloredEmblems.length - 1))
}

function parseMask(value: string) {
  if (!activeEmblem.value) return
  activeEmblem.value.mask = value.split(/[\s,]+/).map(Number).filter(Number.isFinite)
}

importSource()
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">Crusader Kings III · MCP-first</p>
        <h1>家徽工坊</h1>
        <p class="subtitle">结构化编辑原版可导入的静态纹章数据，不执行任意 CK3 脚本。</p>
      </div>
      <div class="top-actions">
        <el-button @click="reset">重置</el-button>
        <el-button type="primary" :disabled="errorCount > 0" @click="copyOutput">复制 CK3 代码</el-button>
      </div>
    </header>

    <main class="workspace">
      <section class="source-pane panel">
        <div class="panel-title">
          <div>
            <span class="step">01</span>
            <h2>导入代码</h2>
          </div>
          <el-button text link type="primary" @click="loadSample">载入实机样例</el-button>
        </div>
        <el-input v-model="source" type="textarea" :rows="21" resize="none" spellcheck="false" class="code-input" />
        <el-button class="import-button" type="primary" @click="importSource">解析并载入</el-button>

        <div v-if="diagnostics.length" class="diagnostics">
          <div v-for="(item, index) in diagnostics" :key="index" :class="['diagnostic', item.severity]">
            <span>{{ item.severity.toUpperCase() }}</span>
            <p>{{ item.message }}<small v-if="item.line">（{{ item.line }}:{{ item.column }}）</small></p>
          </div>
        </div>
        <el-empty v-else description="没有解析诊断" :image-size="46" />
      </section>

      <section class="preview-pane panel">
        <div class="panel-title">
          <div><span class="step">02</span><h2>构图预览</h2></div>
          <el-tag effect="plain" type="warning">浏览器近似</el-tag>
        </div>
        <div class="preview-stage">
          <div class="shield" :style="{ '--shield-color': cssColor(coatOfArms.colors[0]) }">
            <div class="shield-light" :style="{ background: cssColor(coatOfArms.colors[1]) }" />
            <div
              v-for="(emblem, emblemIndex) in coatOfArms.coloredEmblems"
              :key="`${emblem.texture}-${emblemIndex}`"
              class="emblem-group"
            >
              <div
                v-for="(instance, instanceIndex) in emblem.instances"
                :key="instanceIndex"
                class="emblem-glyph"
                :style="{
                  left: `${instance.position[0] * 100}%`,
                  top: `${instance.position[1] * 100}%`,
                  color: cssColor(emblem.colors[0]),
                  transform: `translate(-50%, -50%) rotate(${instance.rotation}deg) scale(${instance.scale[0]}, ${instance.scale[1]})`,
                  zIndex: Math.round(instance.depth * 10),
                }"
                :title="emblem.texture"
              >✦</div>
            </div>
          </div>
        </div>
        <div class="preview-caption">
          <strong>{{ coatOfArms.pattern || '未指定 pattern' }}</strong>
          <span>{{ coatOfArms.coloredEmblems.length }} 个彩色图层 · {{ coatOfArms.coloredEmblems.reduce((sum, item) => sum + item.instances.length, 0) }} 个实例</span>
        </div>
        <el-alert type="info" :closable="false" show-icon>
          <template #title>真正的纹理、mask 和渲染结果以 CK3 原生 MCP 检测为准。</template>
        </el-alert>
      </section>

      <section class="editor-pane panel">
        <div class="panel-title"><div><span class="step">03</span><h2>结构化编辑</h2></div></div>
        <el-scrollbar height="690px">
          <el-form label-position="top">
            <div class="form-grid">
              <el-form-item label="Pattern 资源名">
                <el-input v-model="coatOfArms.pattern" />
              </el-form-item>
              <el-form-item v-for="index in 3" :key="index" :label="`底色 ${index}`">
                <el-input v-model="coatOfArms.colors[index - 1]" />
              </el-form-item>
            </div>

            <div class="section-heading">
              <h3>Colored emblems</h3>
              <el-button size="small" type="primary" plain @click="addEmblem">添加图层</el-button>
            </div>
            <el-tabs v-if="coatOfArms.coloredEmblems.length" v-model="selectedEmblem" type="card">
              <el-tab-pane v-for="(emblem, index) in coatOfArms.coloredEmblems" :key="index" :label="`图层 ${index + 1}`" :name="index" />
            </el-tabs>

            <template v-if="activeEmblem">
              <div class="form-grid">
                <el-form-item label="Texture 资源名" class="wide">
                  <el-input v-model="activeEmblem.texture" />
                </el-form-item>
                <el-form-item v-for="index in 3" :key="index" :label="`图案颜色 ${index}`">
                  <el-input v-model="activeEmblem.colors[index - 1]" />
                </el-form-item>
                <el-form-item label="Mask（空格分隔）">
                  <el-input :model-value="activeEmblem.mask.join(' ')" @update:model-value="parseMask" />
                </el-form-item>
              </div>

              <div class="instance-list">
                <div v-for="(instance, index) in activeEmblem.instances" :key="index" class="instance-card">
                  <div class="instance-title">
                    <strong>实例 {{ index + 1 }}</strong>
                    <el-button link type="danger" @click="activeEmblem.instances.splice(index, 1)">删除</el-button>
                  </div>
                  <div class="number-grid">
                    <el-form-item label="X"><el-input-number v-model="instance.position[0]" :step="0.05" /></el-form-item>
                    <el-form-item label="Y"><el-input-number v-model="instance.position[1]" :step="0.05" /></el-form-item>
                    <el-form-item label="Scale X"><el-input-number v-model="instance.scale[0]" :step="0.05" /></el-form-item>
                    <el-form-item label="Scale Y"><el-input-number v-model="instance.scale[1]" :step="0.05" /></el-form-item>
                    <el-form-item label="Rotation"><el-input-number v-model="instance.rotation" :step="5" /></el-form-item>
                    <el-form-item label="Depth"><el-input-number v-model="instance.depth" :step="0.01" /></el-form-item>
                  </div>
                </div>
              </div>
              <div class="row-actions">
                <el-button @click="activeEmblem.instances.push(createInstance())">添加实例</el-button>
                <el-button type="danger" plain @click="removeEmblem(selectedEmblem)">删除当前图层</el-button>
              </div>
            </template>
          </el-form>

          <div class="output-block">
            <div class="section-heading"><h3>确定性导出</h3><el-tag>CRLF</el-tag></div>
            <pre>{{ output }}</pre>
          </div>
        </el-scrollbar>
      </section>
    </main>
  </div>
</template>

<template>
  <aside class="bg-white border border-slate-200 rounded-lg shadow-sm p-5 space-y-6">
    <div class="flex items-center gap-2 border-b border-slate-200 pb-3">
      <Sliders class="w-5 h-5 text-slate-700" />
      <h2 class="text-base font-bold text-slate-900">Parámetros de Configuración</h2>
    </div>

    <!-- 1. Selección de Usuario Objetivo -->
    <div class="space-y-3">
      <div class="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
        <UserCheck class="w-4 h-4 text-slate-600" />
        <span>1. Selección de Usuario Objetivo</span>
      </div>

      <div class="space-y-2">
        <label class="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
          <input
            type="radio"
            value="catalog"
            v-model="selectionMode"
            @change="handleModeChange"
            class="text-slate-900 focus:ring-slate-800"
          />
          <span>Catálogo de usuarios registrados</span>
        </label>
        <label class="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
          <input
            type="radio"
            value="manual"
            v-model="selectionMode"
            @change="handleModeChange"
            class="text-slate-900 focus:ring-slate-800"
          />
          <span>Ingreso manual (Prueba Cold-Start)</span>
        </label>
      </div>

      <div v-if="selectionMode === 'catalog'" class="space-y-1">
        <label class="block text-xs font-medium text-slate-600">
          Identificador de usuario (userId):
        </label>
        <select
          v-model.number="localUserId"
          @change="emitRecommend"
          class="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm focus:border-slate-800 focus:outline-none"
        >
          <option v-for="uid in userIds" :key="uid" :value="uid">
            Usuario #{{ uid }}
          </option>
        </select>
      </div>

      <div v-else class="space-y-2">
        <label class="block text-xs font-medium text-slate-600">
          Ingrese un userId (ej. 99999 para usuario frío):
        </label>
        <div class="flex gap-2">
          <input
            type="number"
            min="1"
            max="999999"
            v-model.number="localUserId"
            @keyup.enter="emitRecommend"
            class="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-800 focus:border-slate-800 focus:outline-none"
          />
          <button
            type="button"
            @click="emitRecommend"
            class="px-3 py-1.5 bg-slate-800 text-white text-xs font-medium rounded-md hover:bg-slate-700 transition"
          >
            Consultar
          </button>
        </div>
      </div>
    </div>

    <hr class="border-slate-200" />

    <!-- 2. Hiperparámetros de Inferencia -->
    <div class="space-y-4">
      <div class="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
        <Cpu class="w-4 h-4 text-slate-600" />
        <span>2. Hiperparámetros de Inferencia</span>
      </div>

      <div class="space-y-1.5">
        <div class="flex justify-between text-xs">
          <span class="font-medium text-slate-700">Ponderación Híbrida (Alpha):</span>
          <span class="font-bold text-slate-900">{{ localAlpha.toFixed(2) }}</span>
        </div>
        <input
          type="range"
          min="0"
          max="1"
          step="0.05"
          v-model.number="localAlpha"
          @change="emitRecommend"
          class="w-full accent-slate-900 cursor-pointer"
        />
        <div class="flex justify-between text-[11px] text-slate-500">
          <span>0.00 (Contenido)</span>
          <span>0.50 (Híbrido)</span>
          <span>1.00 (Colaborativo)</span>
        </div>
      </div>

      <div class="space-y-1.5">
        <div class="flex justify-between text-xs">
          <span class="font-medium text-slate-700">Tamaño del Ranking (Top-N):</span>
          <span class="font-bold text-slate-900">{{ localTopN }} ítems</span>
        </div>
        <input
          type="range"
          min="5"
          max="20"
          step="1"
          v-model.number="localTopN"
          @change="emitRecommend"
          class="w-full accent-slate-900 cursor-pointer"
        />
        <div class="flex justify-between text-[11px] text-slate-500">
          <span>5</span>
          <span>10</span>
          <span>20</span>
        </div>
      </div>

      <div class="space-y-1.5">
        <div class="flex justify-between text-xs">
          <span class="font-medium text-slate-700">Vecindad Colaborativa (k-NN):</span>
          <span class="font-bold text-slate-900">k = {{ localK }}</span>
        </div>
        <input
          type="range"
          min="5"
          max="50"
          step="5"
          v-model.number="localK"
          @change="emitRecommend"
          class="w-full accent-slate-900 cursor-pointer"
        />
        <div class="flex justify-between text-[11px] text-slate-500">
          <span>k = 5</span>
          <span>k = 25</span>
          <span>k = 50</span>
        </div>
      </div>

      <button
        type="button"
        :disabled="loadingRecommend"
        @click="emitRecommend"
        class="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-md bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800 disabled:opacity-50 transition"
      >
        <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': loadingRecommend }" />
        <span>{{ loadingRecommend ? 'Calculando Inferencia...' : 'Actualizar Recomendaciones' }}</span>
      </button>
    </div>

    <hr class="border-slate-200" />

    <!-- 3. Protocolo de Validación Experimental -->
    <div class="space-y-4">
      <div class="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
        <FlaskConical class="w-4 h-4 text-slate-600" />
        <span>3. Validación Experimental</span>
      </div>

      <div class="space-y-1.5">
        <div class="flex justify-between text-xs">
          <span class="font-medium text-slate-700">Proporción de Prueba (Test Split):</span>
          <span class="font-bold text-blue-800">{{ localTestSize.toFixed(2) }} ({{ Math.round(localTestSize * 100) }}%)</span>
        </div>
        <input
          type="range"
          min="0.10"
          max="0.40"
          step="0.05"
          v-model.number="localTestSize"
          @input="emitTestSizePreview"
          class="w-full accent-blue-800 cursor-pointer"
        />
        <div class="flex justify-between text-[11px] text-slate-500">
          <span>0.10 (90/10)</span>
          <span>0.20 (80/20)</span>
          <span>0.40 (60/40)</span>
        </div>
      </div>

      <button
        type="button"
        :disabled="loadingEval"
        @click="emitEvaluation"
        class="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-md bg-blue-800 text-white text-xs font-semibold hover:bg-blue-900 disabled:opacity-50 transition shadow-sm"
      >
        <Play class="w-3.5 h-3.5" />
        <span>{{ loadingEval ? 'Ejecutando Partición...' : 'Ejecutar Validación Experimental' }}</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { ref, watch } from "vue";
import { Cpu, FlaskConical, Play, RefreshCw, Sliders, UserCheck } from "lucide-vue-next";

const props = defineProps({
  userIds: {
    type: Array,
    default: () => [1]
  },
  loadingRecommend: {
    type: Boolean,
    default: false
  },
  loadingEval: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(["update-recommend", "run-evaluation", "change-test-split"]);

const selectionMode = ref("catalog");
const localUserId = ref(1);
const localAlpha = ref(0.5);
const localTopN = ref(10);
const localK = ref(10);
const localTestSize = ref(0.2);

watch(
  () => props.userIds,
  (newIds) => {
    if (newIds && newIds.length > 0 && selectionMode.value === "catalog") {
      if (!newIds.includes(localUserId.value)) {
        localUserId.value = newIds[0];
      }
    }
  },
  { immediate: true }
);

function handleModeChange() {
  if (selectionMode.value === "manual") {
    localUserId.value = 99999;
  } else if (props.userIds.length > 0) {
    localUserId.value = props.userIds[0];
  }
  emitRecommend();
}

function emitRecommend() {
  if (!localUserId.value || localUserId.value < 1) {
    localUserId.value = 1;
  }
  emit("update-recommend", {
    user_id: localUserId.value,
    alpha: localAlpha.value,
    top_n: localTopN.value,
    k: localK.value
  });
}

function emitTestSizePreview() {
  emit("change-test-split", localTestSize.value);
}

function emitEvaluation() {
  emit("run-evaluation", localTestSize.value);
}
</script>
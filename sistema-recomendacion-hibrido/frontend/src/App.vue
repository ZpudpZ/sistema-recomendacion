<template>
  <div class="min-h-screen flex flex-col bg-slate-50 text-slate-800">
    <InstitutionalHeader :apiOnline="apiOnline" :catalogMetrics="catalogMetrics" />

    <!-- Notificación emergente de validación completada -->
    <div
      v-if="toastMessage"
      class="fixed bottom-5 right-5 z-50 max-w-md bg-slate-900 text-white border border-slate-700 rounded-md shadow-lg px-4 py-3 flex items-center gap-3 text-xs"
    >
      <CheckCircle2 class="w-4 h-4 text-emerald-400 shrink-0" />
      <span>{{ toastMessage }}</span>
    </div>

    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div
        v-if="errorMessage"
        class="mb-6 p-4 rounded-md bg-red-50 border border-red-300 text-red-900 text-xs font-medium"
      >
        {{ errorMessage }}
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <!-- Barra Lateral de Control -->
        <div class="lg:col-span-3 lg:sticky lg:top-6">
          <ControlPanel
            :userIds="userIds"
            :loadingRecommend="loadingRecommend"
            :loadingEval="loadingEval"
            @update-recommend="handleRecommendUpdate"
            @run-evaluation="handleRunEvaluation"
            @change-test-split="handleTestSplitPreview"
          />
        </div>

        <!-- Panel Principal de 3 Secciones -->
        <div class="lg:col-span-9 space-y-6">
          <UserProfileSection :profile="userProfile" :loading="loadingProfile" />

          <HybridRankingTable :recommendData="recommendData" :loading="loadingRecommend" />

          <EvaluationLab
            :evalData="evalData"
            :evalHistory="evalHistory"
            :pendingTestSize="pendingTestSize"
            :lastTimestamp="lastEvalTimestamp"
            :loading="loadingEval"
            @trigger-eval="handleRunEvaluation(pendingTestSize)"
          />
        </div>
      </div>
    </main>

    <footer class="bg-white border-t border-slate-200 py-4 mt-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row justify-between items-center text-xs text-slate-500 gap-2">
        <span>Universidad Nacional del Altiplano - Puno | Escuela Profesional de Ingeniería de Sistemas</span>
        <span>Arquitectura Híbrida MovieLens (FastAPI + Vue 3 + Docker)</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { CheckCircle2 } from "lucide-vue-next";
import InstitutionalHeader from "./components/InstitutionalHeader.vue";
import ControlPanel from "./components/ControlPanel.vue";
import UserProfileSection from "./components/UserProfileSection.vue";
import HybridRankingTable from "./components/HybridRankingTable.vue";
import EvaluationLab from "./components/EvaluationLab.vue";
import {
  checkHealth,
  getMetadata,
  getRecommendations,
  getUserProfile,
  runEvaluation
} from "./services/api";

const apiOnline = ref(false);
const userIds = ref([]);
const catalogMetrics = ref(null);

const userProfile = ref(null);
const recommendData = ref(null);
const evalData = ref(null);
const evalHistory = ref([]);

const pendingTestSize = ref(0.2);
const lastEvalTimestamp = ref("");

const loadingProfile = ref(false);
const loadingRecommend = ref(false);
const loadingEval = ref(false);

const errorMessage = ref("");
const toastMessage = ref("");

function showToast(msg) {
  toastMessage.value = msg;
  setTimeout(() => {
    toastMessage.value = "";
  }, 4500);
}

function formatNow() {
  const now = new Date();
  return now.toISOString().replace("T", " ").substring(0, 19);
}

async function handleRecommendUpdate(params) {
  errorMessage.value = "";
  loadingProfile.value = true;
  loadingRecommend.value = true;
  try {
    const [profileRes, recRes] = await Promise.all([
      getUserProfile(params.user_id),
      getRecommendations(params)
    ]);
    userProfile.value = profileRes;
    recommendData.value = recRes;
  } catch (err) {
    errorMessage.value = `Error al consultar inferencia para el usuario ${params.user_id}: ${err.message}`;
  } finally {
    loadingProfile.value = false;
    loadingRecommend.value = false;
  }
}

function handleTestSplitPreview(newVal) {
  pendingTestSize.value = Number(newVal);
}

async function handleRunEvaluation(testSizeVal, showNotification = true) {
  errorMessage.value = "";
  loadingEval.value = true;
  pendingTestSize.value = Number(testSizeVal);
  try {
    const res = await runEvaluation(testSizeVal);
    const ts = formatNow();
    evalData.value = res;
    lastEvalTimestamp.value = ts;

    const trainPct = Math.round((1 - res.test_size_ratio) * 100);
    const testPct = Math.round(res.test_size_ratio * 100);

    evalHistory.value.unshift({
      iteracion: evalHistory.value.length + 1,
      timestamp: ts,
      particion: `${trainPct}% / ${testPct}%`,
      train_samples: res.train_samples,
      test_samples: res.test_samples,
      rmse: res.rmse,
      mae: res.mae,
      tiempo_segundos: res.tiempo_segundos
    });

    if (showNotification) {
      showToast(
        `Validación completada en ${res.tiempo_segundos.toFixed(3)} s (Test Split = ${res.test_size_ratio.toFixed(2)}). Métricas actualizadas.`
      );
    }
  } catch (err) {
    errorMessage.value = `Error en la validación experimental: ${err.message}`;
  } finally {
    loadingEval.value = false;
  }
}

onMounted(async () => {
  try {
    const health = await checkHealth();
    apiOnline.value = health.status === "ok";

    const meta = await getMetadata();
    userIds.value = meta.user_ids;
    catalogMetrics.value = meta.metricas_catalogo;

    const initialUser = meta.user_ids.length > 0 ? meta.user_ids[0] : 1;
    await Promise.all([
      handleRecommendUpdate({
        user_id: initialUser,
        alpha: 0.5,
        top_n: 10,
        k: 10
      }),
      handleRunEvaluation(0.2, false)
    ]);
  } catch (err) {
    apiOnline.value = false;
    errorMessage.value = `No se pudo establecer conexión con el backend FastAPI: ${err.message}`;
  }
});
</script>
<template>
  <section class="bg-white border border-slate-200 rounded-lg shadow-sm p-5 space-y-5">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-200 pb-3">
      <div class="flex items-center gap-2">
        <Layers class="w-5 h-5 text-slate-700" />
        <h2 class="text-base font-bold text-slate-900">
          Sección B: Motor de Recomendación Híbrido
          <span v-if="recommendData" class="text-slate-500 font-medium">(Top-{{ recommendData.top_n }})</span>
        </h2>
      </div>
      <span v-if="recommendData" class="text-xs font-mono text-slate-500">
        Fusión Lineal Normalizada [0.0000 - 1.0000]
      </span>
    </div>

    <div v-if="loading" class="py-8 text-center text-sm text-slate-500">
      Ejecutando inferencia híbrida y ordenamiento matricial...
    </div>

    <template v-else-if="recommendData">
      <!-- Aviso de ajuste automático por Cold-Start -->
      <div
        v-if="recommendData.es_frio"
        class="flex items-start gap-3 p-3.5 rounded-md bg-blue-50 border border-blue-200 text-blue-950 text-xs sm:text-sm"
      >
        <Info class="w-5 h-5 text-blue-700 shrink-0 mt-0.5" />
        <p>
          <span class="font-semibold">Nota operativa:</span> Debido a la condición de arranque en frío del usuario consultado,
          el ponderador colaborativo se ajusta automáticamente a <span class="font-mono font-bold">Alpha = 0.0000</span>
          (Solicitado: {{ recommendData.alpha_solicitado.toFixed(2) }}).
        </p>
      </div>

      <!-- Indicadores de Balance -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="bg-slate-50 border border-slate-200 rounded-md p-4">
          <p class="text-xs font-medium text-slate-500 uppercase">Ponderación Colaborativa Efectiva (Alpha)</p>
          <p class="mt-1 text-2xl font-bold font-mono text-slate-900">
            {{ recommendData.alpha_efectivo.toFixed(4) }}
          </p>
        </div>

        <div class="bg-slate-50 border border-slate-200 rounded-md p-4">
          <p class="text-xs font-medium text-slate-500 uppercase">Ponderación de Contenido (1 - Alpha)</p>
          <p class="mt-1 text-2xl font-bold font-mono text-slate-900">
            {{ recommendData.peso_contenido.toFixed(4) }}
          </p>
        </div>

        <div class="bg-slate-50 border border-slate-200 rounded-md p-4">
          <p class="text-xs font-medium text-slate-500 uppercase">Vecindad Colaborativa Activa (k-NN)</p>
          <p class="mt-1 text-2xl font-bold font-mono text-slate-900">
            k = {{ recommendData.k }}
          </p>
        </div>
      </div>

      <!-- Tabla de Recomendaciones Top-N -->
      <div class="space-y-2">
        <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-600">
          Tabla de Ranking de Recomendaciones Generadas
        </h3>
        <div class="overflow-x-auto border border-slate-200 rounded-md">
          <table class="min-w-full divide-y divide-slate-200 text-xs">
            <thead class="bg-slate-100 text-slate-700 uppercase font-semibold">
              <tr>
                <th class="px-3 py-2.5 text-left">#</th>
                <th class="px-3 py-2.5 text-left">ID</th>
                <th class="px-3 py-2.5 text-left">Título</th>
                <th class="px-3 py-2.5 text-left">Géneros</th>
                <th class="px-3 py-2.5 text-right">Score Híbrido</th>
                <th class="px-3 py-2.5 text-right">Score Colaborativo</th>
                <th class="px-3 py-2.5 text-right">Score Contenido</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200 bg-white">
              <tr
                v-for="(item, index) in recommendData.recomendaciones"
                :key="item.movieId"
                class="hover:bg-slate-50"
              >
                <td class="px-3 py-2.5 font-mono font-semibold text-slate-500">{{ index + 1 }}</td>
                <td class="px-3 py-2.5 font-mono text-slate-600">{{ item.movieId }}</td>
                <td class="px-3 py-2.5 font-semibold text-slate-900">{{ item.title }}</td>
                <td class="px-3 py-2.5 text-slate-600">{{ item.genres.replaceAll('|', ', ') }}</td>
                <td class="px-3 py-2.5 text-right font-mono font-bold text-slate-900">
                  <div class="flex items-center justify-end gap-2">
                    <div class="w-16 bg-slate-200 h-1.5 rounded-full overflow-hidden hidden sm:block">
                      <div
                        class="bg-slate-900 h-full"
                        :style="{ width: `${Math.min(100, item.score_hibrido * 100)}%` }"
                      ></div>
                    </div>
                    <span>{{ item.score_hibrido.toFixed(4) }}</span>
                  </div>
                </td>
                <td class="px-3 py-2.5 text-right font-mono text-blue-800">
                  {{ item.score_colaborativo.toFixed(4) }}
                </td>
                <td class="px-3 py-2.5 text-right font-mono text-emerald-800">
                  {{ item.score_contenido.toFixed(4) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Gráfico Comparativo de Scores -->
      <div class="space-y-2 pt-2">
        <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-600">
          Análisis Gráfico Comparativo de Componentes de Puntuación (Escala Normalizada [0, 1])
        </h3>
        <div class="border border-slate-200 rounded-md p-4 bg-slate-50/50 h-80">
          <Bar v-if="chartData" :data="chartData" :options="chartOptions" />
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { Info, Layers } from "lucide-vue-next";
import { Bar } from "vue-chartjs";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Title,
  Tooltip
} from "chart.js";

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

const props = defineProps({
  recommendData: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
});

const chartData = computed(() => {
  if (!props.recommendData || !props.recommendData.recomendaciones) {
    return null;
  }
  const items = props.recommendData.recomendaciones.slice(0, 10);
  return {
    labels: items.map((i) => (i.title.length > 25 ? `${i.title.slice(0, 25)}...` : i.title)),
    datasets: [
      {
        label: "Score Híbrido",
        backgroundColor: "#0f172a",
        data: items.map((i) => i.score_hibrido)
      },
      {
        label: "Score Colaborativo",
        backgroundColor: "#1d4ed8",
        data: items.map((i) => i.score_colaborativo)
      },
      {
        label: "Score Contenido",
        backgroundColor: "#047857",
        data: items.map((i) => i.score_contenido)
      }
    ]
  };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: "top",
      labels: {
        font: { size: 11 }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      max: 1.0,
      ticks: {
        font: { size: 11 }
      }
    },
    x: {
      ticks: {
        font: { size: 10 }
      }
    }
  }
};
</script>
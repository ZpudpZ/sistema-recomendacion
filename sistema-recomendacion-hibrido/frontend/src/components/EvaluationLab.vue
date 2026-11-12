<template>
  <section class="bg-white border border-slate-200 rounded-lg shadow-sm p-5 space-y-5">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-200 pb-3">
      <div class="flex items-center gap-2">
        <BarChart3 class="w-5 h-5 text-slate-700" />
        <h2 class="text-base font-bold text-slate-900">
          Sección C: Panel de Evaluación y Validación Experimental
        </h2>
      </div>
      <span v-if="lastTimestamp" class="text-xs text-slate-500">
        Última ejecución: <span class="font-mono font-semibold text-slate-700">{{ lastTimestamp }}</span>
      </span>
    </div>

    <!-- Aviso de cambio pendiente en el slider Test Split -->
    <div
      v-if="evalData && Math.abs(pendingTestSize - evalData.test_size_ratio) > 0.001"
      class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-md bg-amber-50 border border-amber-300 text-amber-950 text-xs"
    >
      <div class="flex items-center gap-2">
        <AlertCircle class="w-4 h-4 text-amber-700 shrink-0" />
        <span>
          El control deslizante de partición se encuentra en <strong>{{ pendingTestSize.toFixed(2) }}</strong>,
          mientras que las métricas en pantalla corresponden a la proporción
          <strong>{{ evalData.test_size_ratio.toFixed(2) }}</strong>. Presione el botón de validación para recalcular.
        </span>
      </div>
      <button
        type="button"
        @click="$emit('trigger-eval')"
        class="px-3 py-1.5 rounded bg-amber-800 text-white font-semibold hover:bg-amber-900 shrink-0 transition"
      >
        Recalcular Ahora
      </button>
    </div>

    <div v-if="loading" class="py-8 text-center text-sm text-slate-500">
      Ejecutando partición Train/Test y calculando métricas de error RMSE y MAE...
    </div>

    <template v-else-if="evalData">
      <!-- 5 Tarjetas de Métricas Principales -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div class="bg-slate-50 border border-slate-200 rounded-md p-4">
          <p class="text-xs font-medium text-slate-500 uppercase">RMSE (Error Cuadrático)</p>
          <p class="mt-1 text-2xl font-bold font-mono text-slate-900">{{ evalData.rmse.toFixed(4) }}</p>
        </div>

        <div class="bg-slate-50 border border-slate-200 rounded-md p-4">
          <p class="text-xs font-medium text-slate-500 uppercase">MAE (Error Absoluto)</p>
          <p class="mt-1 text-2xl font-bold font-mono text-slate-900">{{ evalData.mae.toFixed(4) }}</p>
        </div>

        <div class="bg-slate-50 border border-slate-200 rounded-md p-4">
          <p class="text-xs font-medium text-slate-500 uppercase">Muestras Train</p>
          <p class="mt-1 text-2xl font-bold font-mono text-slate-900">
            {{ evalData.train_samples.toLocaleString() }}
          </p>
        </div>

        <div class="bg-slate-50 border border-slate-200 rounded-md p-4">
          <p class="text-xs font-medium text-slate-500 uppercase">Muestras Test</p>
          <p class="mt-1 text-2xl font-bold font-mono text-slate-900">
            {{ evalData.test_samples.toLocaleString() }}
          </p>
        </div>

        <div class="bg-slate-50 border border-slate-200 rounded-md p-4">
          <p class="text-xs font-medium text-slate-500 uppercase">Dispersión de Matriz</p>
          <p class="mt-1 text-2xl font-bold font-mono text-slate-900">
            {{ evalData.dispersion_pct.toFixed(2) }}%
          </p>
        </div>
      </div>

      <!-- Parámetros Técnicos y Formulación Matemática -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-2">
        <div class="lg:col-span-6 space-y-2">
          <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-600">
            Parámetros Técnicos de la Partición y del Catálogo
          </h3>
          <div class="border border-slate-200 rounded-md overflow-hidden">
            <table class="min-w-full divide-y divide-slate-200 text-xs">
              <thead class="bg-slate-100 text-slate-700 uppercase font-semibold">
                <tr>
                  <th class="px-3.5 py-2.5 text-left">Parámetro Experimental</th>
                  <th class="px-3.5 py-2.5 text-right">Valor Registrado</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-200 bg-white">
                <tr>
                  <td class="px-3.5 py-2 text-slate-700">Dimensiones de la Matriz Usuario-Ítem</td>
                  <td class="px-3.5 py-2 text-right font-mono font-medium text-slate-900">
                    {{ evalData.total_usuarios.toLocaleString() }} x {{ evalData.total_peliculas.toLocaleString() }}
                  </td>
                </tr>
                <tr>
                  <td class="px-3.5 py-2 text-slate-700">Total de Valoraciones Históricas</td>
                  <td class="px-3.5 py-2 text-right font-mono font-medium text-slate-900">
                    {{ evalData.total_valoraciones.toLocaleString() }}
                  </td>
                </tr>
                <tr>
                  <td class="px-3.5 py-2 text-slate-700">Relación de Partición (Train / Test)</td>
                  <td class="px-3.5 py-2 text-right font-mono font-medium text-slate-900">
                    {{ Math.round((1 - evalData.test_size_ratio) * 100) }}% / {{ Math.round(evalData.test_size_ratio * 100) }}%
                  </td>
                </tr>
                <tr>
                  <td class="px-3.5 py-2 text-slate-700">Densidad Observada en Matriz CSR</td>
                  <td class="px-3.5 py-2 text-right font-mono font-medium text-slate-900">
                    {{ evalData.densidad_pct.toFixed(4) }}%
                  </td>
                </tr>
                <tr>
                  <td class="px-3.5 py-2 text-slate-700">Índice de Dispersión (Sparsity)</td>
                  <td class="px-3.5 py-2 text-right font-mono font-medium text-slate-900">
                    {{ evalData.dispersion_pct.toFixed(4) }}%
                  </td>
                </tr>
                <tr>
                  <td class="px-3.5 py-2 text-slate-700">Tiempo de Cómputo de la Corrida</td>
                  <td class="px-3.5 py-2 text-right font-mono font-semibold text-blue-800">
                    {{ evalData.tiempo_segundos.toFixed(3) }} s
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="lg:col-span-6 space-y-2">
          <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-600">
            Formulación Matemática del Sistema
          </h3>
          <div class="border border-slate-200 rounded-md p-4 bg-slate-50 space-y-3 text-xs text-slate-800">
            <div>
              <p class="font-semibold text-slate-700 mb-1">1. Normalización Min-Max de vectores de puntuación:</p>
              <div class="bg-white border border-slate-200 rounded px-3 py-2 font-mono text-[11px] text-slate-900">
                S_norm(u, i) = [ S(u, i) - S_min(u) ] / [ S_max(u) - S_min(u) + 1e-8 ]
              </div>
            </div>
            <div>
              <p class="font-semibold text-slate-700 mb-1">2. Integración lineal híbrida ponderada:</p>
              <div class="bg-white border border-slate-200 rounded px-3 py-2 font-mono text-[11px] text-slate-900">
                Score_Híbrido(u, i) = Alpha * S_colab_norm(u, i) + (1 - Alpha) * S_cont_norm(u, i)
              </div>
            </div>
            <div>
              <p class="font-semibold text-slate-700 mb-1">3. Métricas de error de predicción sobre conjunto de prueba T:</p>
              <div class="bg-white border border-slate-200 rounded px-3 py-2 font-mono text-[11px] text-slate-900 space-y-1">
                <div>RMSE = sqrt( (1 / |T|) * sum_{ (u,i) in T } ( r_pred(u,i) - r_real(u,i) )^2 )</div>
                <div>MAE  = (1 / |T|) * sum_{ (u,i) in T } | r_pred(u,i) - r_real(u,i) |</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bitácora Histórica de Ejecuciones en la Sesión -->
      <div v-if="evalHistory.length > 0" class="space-y-2 pt-2">
        <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-600">
          Bitácora de Ejecuciones Experimentales en la Sesión Actual
        </h3>
        <div class="overflow-x-auto border border-slate-200 rounded-md">
          <table class="min-w-full divide-y divide-slate-200 text-xs">
            <thead class="bg-slate-100 text-slate-700 uppercase font-semibold">
              <tr>
                <th class="px-3 py-2 text-left">Iteración</th>
                <th class="px-3 py-2 text-left">Marca de Tiempo</th>
                <th class="px-3 py-2 text-left">Partición (Train / Test)</th>
                <th class="px-3 py-2 text-right">Muestras Train</th>
                <th class="px-3 py-2 text-right">Muestras Test</th>
                <th class="px-3 py-2 text-right">RMSE</th>
                <th class="px-3 py-2 text-right">MAE</th>
                <th class="px-3 py-2 text-right">Tiempo (s)</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200 bg-white">
              <tr v-for="row in evalHistory" :key="row.iteracion" class="hover:bg-slate-50">
                <td class="px-3 py-2 font-mono font-semibold text-slate-700">#{{ row.iteracion }}</td>
                <td class="px-3 py-2 font-mono text-slate-600">{{ row.timestamp }}</td>
                <td class="px-3 py-2 font-mono text-slate-800">{{ row.particion }}</td>
                <td class="px-3 py-2 text-right font-mono text-slate-700">{{ row.train_samples.toLocaleString() }}</td>
                <td class="px-3 py-2 text-right font-mono text-slate-700">{{ row.test_samples.toLocaleString() }}</td>
                <td class="px-3 py-2 text-right font-mono font-bold text-slate-900">{{ row.rmse.toFixed(4) }}</td>
                <td class="px-3 py-2 text-right font-mono font-bold text-slate-900">{{ row.mae.toFixed(4) }}</td>
                <td class="px-3 py-2 text-right font-mono text-blue-800">{{ row.tiempo_segundos.toFixed(3) }} s</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { AlertCircle, BarChart3 } from "lucide-vue-next";

defineProps({
  evalData: {
    type: Object,
    default: null
  },
  evalHistory: {
    type: Array,
    default: () => []
  },
  pendingTestSize: {
    type: Number,
    default: 0.2
  },
  lastTimestamp: {
    type: String,
    default: ""
  },
  loading: {
    type: Boolean,
    default: false
  }
});

defineEmits(["trigger-eval"]);
</script>
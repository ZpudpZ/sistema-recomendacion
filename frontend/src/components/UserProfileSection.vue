<template>
  <section class="bg-white border border-slate-200 rounded-lg shadow-sm p-5 space-y-5">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-200 pb-3">
      <div class="flex items-center gap-2">
        <User class="w-5 h-5 text-slate-700" />
        <h2 class="text-base font-bold text-slate-900">
          Sección A: Perfil e Historial del Usuario Objetivo
          <span v-if="profile" class="text-slate-500 font-medium">(userId = {{ profile.user_id }})</span>
        </h2>
      </div>
      <span
        v-if="profile"
        class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold"
        :class="
          profile.es_frio
            ? 'bg-amber-100 text-amber-900 border border-amber-300'
            : 'bg-slate-100 text-slate-800 border border-slate-300'
        "
      >
        <span>Estado: {{ profile.es_frio ? 'Arranque en Frío (Cold-Start)' : 'Usuario Histórico Activo' }}</span>
      </span>
    </div>

    <div v-if="loading" class="py-8 text-center text-sm text-slate-500">
      Cargando perfil y registros históricos del usuario...
    </div>

    <template v-else-if="profile">
      <!-- Alerta Técnica Cold-Start -->
      <div
        v-if="profile.es_frio"
        class="flex items-start gap-3 p-4 rounded-md bg-amber-50 border border-amber-300 text-amber-950 text-xs sm:text-sm"
      >
        <AlertTriangle class="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
        <div class="space-y-1">
          <p class="font-semibold">
            Estado: Usuario no registrado en matriz histórica.
          </p>
          <p class="text-amber-900">
            Activando protocolo de arranque en frío mediante proyección bayesiana y perfiles semánticos.
          </p>
        </div>
      </div>

      <!-- Tarjetas de Resumen de Perfil -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="bg-slate-50 border border-slate-200 rounded-md p-4">
          <p class="text-xs font-medium text-slate-500 uppercase">Total Valoraciones Registradas</p>
          <p class="mt-1 text-2xl font-bold text-slate-900">
            {{ profile.total_valoraciones.toLocaleString() }}
          </p>
        </div>

        <div class="bg-slate-50 border border-slate-200 rounded-md p-4">
          <p class="text-xs font-medium text-slate-500 uppercase">Promedio Histórico</p>
          <p class="mt-1 text-2xl font-bold text-slate-900">
            {{ profile.es_frio ? 'N/A' : `${profile.promedio_rating.toFixed(2)} / 5.0` }}
          </p>
        </div>

        <div class="bg-slate-50 border border-slate-200 rounded-md p-4">
          <p class="text-xs font-medium text-slate-500 uppercase">Balance Calificaciones Altas (&gt;= 3.0)</p>
          <p class="mt-1 text-2xl font-bold text-slate-900">
            {{ profile.calificaciones_altas.toLocaleString() }}
            <span class="text-sm font-medium text-slate-600">
              ({{ profile.porcentaje_altas.toFixed(1) }}%)
            </span>
          </p>
        </div>
      </div>

      <!-- Tabla de Historial y Distribución de Géneros -->
      <div v-if="!profile.es_frio" class="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-2">
        <div class="lg:col-span-7 space-y-2">
          <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-600">
            Registro de Películas Mejor Valoradas por el Usuario (Top 10 Histórico)
          </h3>
          <div class="overflow-x-auto border border-slate-200 rounded-md">
            <table class="min-w-full divide-y divide-slate-200 text-xs">
              <thead class="bg-slate-100 text-slate-700 uppercase font-semibold">
                <tr>
                  <th class="px-3 py-2.5 text-left">ID</th>
                  <th class="px-3 py-2.5 text-left">Título</th>
                  <th class="px-3 py-2.5 text-left">Géneros</th>
                  <th class="px-3 py-2.5 text-right">Calificación</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-200 bg-white">
                <tr v-for="item in profile.historial" :key="item.movieId" class="hover:bg-slate-50">
                  <td class="px-3 py-2 font-mono text-slate-600">{{ item.movieId }}</td>
                  <td class="px-3 py-2 font-medium text-slate-900">{{ item.title }}</td>
                  <td class="px-3 py-2 text-slate-600">{{ item.genres.replaceAll('|', ', ') }}</td>
                  <td class="px-3 py-2 text-right font-mono font-semibold text-slate-900 whitespace-nowrap">
                    {{ item.rating.toFixed(1) }} / 5.0
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="lg:col-span-5 space-y-2">
          <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-600">
            Distribución de Frecuencia de Géneros en el Historial (Top 8)
          </h3>
          <div class="border border-slate-200 rounded-md p-4 bg-slate-50/50 h-72">
            <Bar v-if="chartData" :data="chartData" :options="chartOptions" />
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { AlertTriangle, User } from "lucide-vue-next";
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
  profile: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
});

const chartData = computed(() => {
  if (!props.profile || !props.profile.generos_favoritos || props.profile.generos_favoritos.length === 0) {
    return null;
  }
  return {
    labels: props.profile.generos_favoritos.map((g) => g.genero),
    datasets: [
      {
        label: "Películas calificadas",
        backgroundColor: "#1e293b",
        borderRadius: 4,
        data: props.profile.generos_favoritos.map((g) => g.cantidad)
      }
    ]
  };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: "y",
  plugins: {
    legend: {
      display: false
    }
  },
  scales: {
    x: {
      beginAtZero: true,
      ticks: {
        precision: 0,
        font: { size: 11 }
      }
    },
    y: {
      ticks: {
        font: { size: 11 }
      }
    }
  }
};
</script>
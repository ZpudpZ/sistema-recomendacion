<template>
  <header class="bg-slate-900 text-white border-b border-slate-800 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div class="space-y-1">
          <div class="flex items-center gap-2 text-xs font-semibold tracking-wider uppercase text-slate-400">
            <Building2 class="w-4 h-4 text-blue-400 shrink-0" />
            <span>Universidad Nacional del Altiplano - Escuela Profesional de Ingeniería de Sistemas</span>
          </div>
          <h1 class="text-xl sm:text-2xl font-bold tracking-tight text-white">
            Laboratorio de Inteligencia Artificial: Sistema de Recomendación Híbrido
          </h1>
          <p class="text-xs sm:text-sm text-slate-300 max-w-3xl">
            Arquitectura de Fusión Lineal Ponderada basada en Filtrado Colaborativo (User-Based k-NN sobre Matriz Dispersa CSR)
            y Filtrado Basado en Contenido (Vectorización TF-IDF y Similitud Coseno).
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <div
            class="inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium border"
            :class="
              apiOnline
                ? 'bg-emerald-950/60 border-emerald-700/70 text-emerald-300'
                : 'bg-red-950/60 border-red-700/70 text-red-300'
            "
          >
            <Activity class="w-3.5 h-3.5" />
            <span>Servicio API: {{ apiOnline ? 'Operativo' : 'Sin conexión' }}</span>
          </div>

          <div
            v-if="catalogMetrics"
            class="hidden sm:flex items-center gap-4 bg-slate-800/90 border border-slate-700 px-3.5 py-1.5 rounded-md text-xs text-slate-200"
          >
            <div class="flex items-center gap-1.5">
              <Users class="w-3.5 h-3.5 text-blue-400" />
              <span class="text-slate-400">Usuarios:</span>
              <span class="font-semibold">{{ catalogMetrics.total_usuarios.toLocaleString() }}</span>
            </div>
            <span class="text-slate-600">|</span>
            <div class="flex items-center gap-1.5">
              <Film class="w-3.5 h-3.5 text-blue-400" />
              <span class="text-slate-400">Ítems:</span>
              <span class="font-semibold">{{ catalogMetrics.total_peliculas.toLocaleString() }}</span>
            </div>
            <span class="text-slate-600">|</span>
            <div class="flex items-center gap-1.5">
              <Database class="w-3.5 h-3.5 text-blue-400" />
              <span class="text-slate-400">Dispersión:</span>
              <span class="font-semibold">{{ catalogMetrics.dispersion_pct.toFixed(2) }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { Activity, Building2, Database, Film, Users } from "lucide-vue-next";

defineProps({
  apiOnline: {
    type: Boolean,
    default: false
  },
  catalogMetrics: {
    type: Object,
    default: null
  }
});
</script>
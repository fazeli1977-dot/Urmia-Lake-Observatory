export const ULO_COLORS = {
  watershedStroke: '#38bdf8',
  watershedFill: '#0284c7',
  subbasinStroke: '#94a3b8',
  subbasinFill: '#334155',
  lakeRefStroke: '#22d3ee',
  lakeRefFill: '#0891b2',
  activeWaterStroke: '#00f2fe',
  activeWaterFill: '#0284c7',
  desiccatedStroke: '#f59e0b',
  desiccatedFill: '#fde68a',
  hypsometryStroke: '#a78bfa',
  riverStroke: '#3b82f6',
  reservoirStroke: '#60a5fa',
  reservoirFill: '#1d4ed8',
  damFill: '#ef4444',
  damStroke: '#fee2e2',
  vegetationStroke: '#10b981',
  vegetationFill: '#059669',
  landmarkFill: '#f97316',
  landmarkStroke: '#fff7ed',
} as const;

export const URMIA_VIEWPORT = {
  // MapLibre GL uses [longitude, latitude]
  center: [45.52, 37.68] as [number, number],
  zoom: 7.4,
  minZoom: 5.5,
  maxZoom: 16,
};

export interface SpatialBookmark {
  id: string;
  labelFa: string;
  labelEn: string;
  center: [number, number];
  zoom: number;
}

export const SPATIAL_BOOKMARKS: SpatialBookmark[] = [
  {
    id: 'basin',
    labelFa: 'کل حوضه آبریز',
    labelEn: 'Full Basin',
    center: [45.85, 37.45],
    zoom: 6.9,
  },
  {
    id: 'lake',
    labelFa: 'پهنه دریاچه ارومیه',
    labelEn: 'Lake Urmia',
    center: [45.45, 37.65],
    zoom: 8.2,
  },
  {
    id: 'south_playa',
    labelFa: 'کفه نمکی جنوب و تالاب‌ها',
    labelEn: 'South Salt Playa & Wetlands',
    center: [45.58, 37.12],
    zoom: 9.5,
  },
  {
    id: 'causeway',
    labelFa: 'میانگذر شهید کلانتری',
    labelEn: 'Lake Causeway',
    center: [45.36, 37.79],
    zoom: 10.4,
  },
  {
    id: 'boukan_dam',
    labelFa: 'سد بوکان (زرینه‌رود)',
    labelEn: 'Boukan Reservoir',
    center: [46.165, 36.634],
    zoom: 10.6,
  },
];

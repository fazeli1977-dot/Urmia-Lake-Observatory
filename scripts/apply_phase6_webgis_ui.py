from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web-dashboard" / "src"

# 1. src/map/theme.ts
THEME_TS = """export const ULO_COLORS = {
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
    center: [46.12, 36.79],
    zoom: 10.6,
  },
];
"""

# 2. src/map/basemaps.ts
BASEMAPS_TS = """export interface BasemapOption {
  id: string;
  nameFa: string;
  nameEn: string;
  tiles: string[];
  attribution: string;
  maxZoom: number;
  tileSize: number;
}

export const BASEMAPS: BasemapOption[] = [
  {
    id: 'esri-imagery',
    nameFa: 'تصویر ماهواره‌ای واقعی (Esri World Imagery)',
    nameEn: 'Satellite Imagery (Esri World Imagery)',
    tiles: [
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    ],
    attribution: 'Tiles © Esri, Maxar, Earthstar Geographics, USDA, USGS',
    maxZoom: 18,
    tileSize: 256,
  },
  {
    id: 'carto-dark',
    nameFa: 'نقشه پایه تاریک علمی (CARTO Dark Matter)',
    nameEn: 'Scientific Dark Basemap (CARTO Dark)',
    tiles: [
      'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
      'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
    ],
    attribution: '© OpenStreetMap contributors © CARTO',
    maxZoom: 19,
    tileSize: 256,
  },
  {
    id: 'opentopomap',
    nameFa: 'توپوگرافی و ارتفاعات حوضه (OpenTopoMap)',
    nameEn: 'Topographic Relief (OpenTopoMap)',
    tiles: [
      'https://a.tile.opentopomap.org/{z}/{x}/{y}.png',
      'https://b.tile.opentopomap.org/{z}/{x}/{y}.png',
    ],
    attribution: '© OpenStreetMap contributors, SRTM | © OpenTopoMap',
    maxZoom: 16,
    tileSize: 256,
  },
  {
    id: 'osm-standard',
    nameFa: 'نقشه معابر و سکونتگاه‌ها (OpenStreetMap)',
    nameEn: 'Roads & Settlements (OpenStreetMap)',
    tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19,
    tileSize: 256,
  },
];
"""

# 3. src/map/layers.ts
LAYERS_TS = """import { ULO_COLORS } from './theme';

export type LayerKey =
  | 'watershed'
  | 'subbasins'
  | 'hypsometricContours'
  | 'lakeBoundary'
  | 'desiccatedZones'
  | 'activeWater'
  | 'shorelines'
  | 'riparianVegetation'
  | 'rivers'
  | 'reservoirs'
  | 'dams'
  | 'landmarks';

export type LayerCategory = 'lake_dynamics' | 'hydro_infra' | 'ecology' | 'basin_monitoring';

export type GeometryKind = 'polygon' | 'line' | 'point';

export interface GeoLayerMeta {
  key: LayerKey;
  category: LayerCategory;
  fileName: string;
  titleFa: string;
  titleEn: string;
  descriptionFa: string;
  descriptionEn: string;
  geometryKind: GeometryKind;
  defaultVisible: boolean;
  defaultOpacity: number;
  legendColor: string;
  strokeColor: string;
  fillColor?: string;
  fillOpacity?: number;
  strokeWidth: number;
  dashed?: boolean;
  pointRadius?: number;
}

export const LAYER_CATEGORIES: { id: LayerCategory; titleFa: string; titleEn: string }[] = [
  {
    id: 'lake_dynamics',
    titleFa: 'پویایی پهنه آبی، نمکزار و خطوط ساحلی',
    titleEn: 'Lake Dynamics, Salt Playa & Shorelines',
  },
  {
    id: 'hydro_infra',
    titleFa: 'رودخانه‌ها، مخازن و سدهای حوضه',
    titleEn: 'Rivers, Reservoirs & Basin Dams',
  },
  {
    id: 'ecology',
    titleFa: 'تالاب‌های اقماری و پوشش گیاهی حاشیه‌ای',
    titleEn: 'Satellite Wetlands & Riparian Vegetation',
  },
  {
    id: 'basin_monitoring',
    titleFa: 'مرزهای هیدرولوژیک و ایستگاه‌های پایش',
    titleEn: 'Hydrological Boundaries & Monitoring',
  },
];

// Ordered from bottom-most polygon to top-most point layer on MapLibre canvas
export const LAYER_CONFIGS: GeoLayerMeta[] = [
  {
    key: 'watershed',
    category: 'basin_monitoring',
    fileName: 'urmia_watershed.geojson',
    titleFa: 'مرز حوضه آبریز دریاچه ارومیه',
    titleEn: 'Urmia Endorheic Basin Boundary',
    descriptionFa: 'حوضه بسته به مساحت تقریبی ۵۱٬۸۷۶ کیلومتر مربع (HydroBASINS)',
    descriptionEn: 'Closed basin boundary (~51,876 km², HydroBASINS)',
    geometryKind: 'polygon',
    defaultVisible: true,
    defaultOpacity: 0.85,
    legendColor: ULO_COLORS.watershedStroke,
    strokeColor: ULO_COLORS.watershedStroke,
    fillColor: ULO_COLORS.watershedFill,
    fillOpacity: 0.06,
    strokeWidth: 2.2,
  },
  {
    key: 'subbasins',
    category: 'basin_monitoring',
    fileName: 'urmia_subbasins.geojson',
    titleFa: 'زیرحوضه‌های هیدرولوژیک',
    titleEn: 'Hydrological Sub-basins',
    descriptionFa: 'واحدهای زیرحوضه‌ای تغذیه‌کننده دریاچه (سطح ۷ Pfafstetter)',
    descriptionEn: 'Tributary sub-basins feeding Lake Urmia (Pfafstetter L7)',
    geometryKind: 'polygon',
    defaultVisible: false,
    defaultOpacity: 0.75,
    legendColor: ULO_COLORS.subbasinStroke,
    strokeColor: ULO_COLORS.subbasinStroke,
    fillColor: ULO_COLORS.subbasinFill,
    fillOpacity: 0.14,
    strokeWidth: 1.1,
    dashed: true,
  },
  {
    key: 'lakeBoundary',
    category: 'lake_dynamics',
    fileName: 'urmia_lake_boundary.geojson',
    titleFa: 'مرز تاریخی و تراز اکولوژیک دریاچه',
    titleEn: 'Historical Ecological Lake Extent',
    descriptionFa: 'پهنه مرجع دریاچه در تراز اکولوژیک ۱۲۷۴.۱ متر (~۵٬۴۷۵ km²)',
    descriptionEn: 'Reference extent at 1274.1 m ecological level (~5,475 km²)',
    geometryKind: 'polygon',
    defaultVisible: true,
    defaultOpacity: 0.85,
    legendColor: ULO_COLORS.lakeRefStroke,
    strokeColor: ULO_COLORS.lakeRefStroke,
    fillColor: ULO_COLORS.lakeRefFill,
    fillOpacity: 0.12,
    strokeWidth: 1.8,
    dashed: true,
  },
  {
    key: 'desiccatedZones',
    category: 'lake_dynamics',
    fileName: 'urmia_desiccated_zones.geojson',
    titleFa: 'پهنه‌های خشک‌شده و کانون‌های گردوغبار نمکی',
    titleEn: 'Desiccated Salt Playa & Dust Hotspots',
    descriptionFa: 'بسترهای تبخیری رخنمون‌یافته و کانون‌های بحرانی خیزش آئروسل نمکی',
    descriptionEn: 'Exposed hypersaline playa & critical salt-dust emission zones',
    geometryKind: 'polygon',
    defaultVisible: true,
    defaultOpacity: 0.78,
    legendColor: ULO_COLORS.desiccatedStroke,
    strokeColor: ULO_COLORS.desiccatedStroke,
    fillColor: ULO_COLORS.desiccatedFill,
    fillOpacity: 0.36,
    strokeWidth: 1.3,
  },
  {
    key: 'hypsometricContours',
    category: 'lake_dynamics',
    fileName: 'urmia_hypsometric_contours.geojson',
    titleFa: 'خطوط هم‌تراز باتیمتری و هیپسومتری بستر',
    titleEn: 'Bathymetric & Hypsometric Contours',
    descriptionFa: 'ترازهای ارتفاعی ۱۲۷۰.۰ تا ۱۲۷۶.۰ متر از سطح دریاهای آزاد',
    descriptionEn: 'Bed elevation contours from 1270.0 to 1276.0 m a.s.l.',
    geometryKind: 'line',
    defaultVisible: false,
    defaultOpacity: 0.85,
    legendColor: ULO_COLORS.hypsometryStroke,
    strokeColor: ULO_COLORS.hypsometryStroke,
    strokeWidth: 1.3,
    dashed: true,
  },
  {
    key: 'activeWater',
    category: 'lake_dynamics',
    fileName: 'urmia_active_water.geojson',
    titleFa: 'پهنه آبی فعلی دریاچه (شوری فوق‌اشباع)',
    titleEn: 'Current Active Water Extent',
    descriptionFa: 'پهنه آب سطحی و شورابه متمرکز در نیمه شمالی و گودال میانی (۲۰۲۶)',
    descriptionEn: 'Active brine water surface derived from optical water indices (2026)',
    geometryKind: 'polygon',
    defaultVisible: true,
    defaultOpacity: 0.9,
    legendColor: ULO_COLORS.activeWaterStroke,
    strokeColor: ULO_COLORS.activeWaterStroke,
    fillColor: ULO_COLORS.activeWaterFill,
    fillOpacity: 0.62,
    strokeWidth: 1.8,
  },
  {
    key: 'shorelines',
    category: 'lake_dynamics',
    fileName: 'urmia_shorelines.geojson',
    titleFa: 'خطوط ساحلی مقایسه‌ای چندزمانه (۱۹۹۵ تا ۲۰۲۶)',
    titleEn: 'Multi-Temporal Shorelines (1995–2026)',
    descriptionFa: 'مقایسه عقب‌نشینی خط ساحلی در سال‌های ۱۹۹۵، ۲۰۰۵، ۲۰۱۵، ۲۰۲۰ و ۲۰۲۶',
    descriptionEn: 'Shoreline retreat comparison across 1995, 2005, 2015, 2020 & 2026',
    geometryKind: 'line',
    defaultVisible: false,
    defaultOpacity: 0.92,
    legendColor: '#f472b6',
    strokeColor: '#f472b6',
    strokeWidth: 2.1,
  },
  {
    key: 'riparianVegetation',
    category: 'ecology',
    fileName: 'urmia_riparian_vegetation.geojson',
    titleFa: 'تالاب‌های اقماری و پوشش گیاهی حاشیه‌ای',
    titleEn: 'Satellite Wetlands & Halophytic Vegetation',
    descriptionFa: 'تالاب‌های رامسر (کانی‌برازان، قوری‌گل، یادگارلو)، نیزارهای دلتایی و هالوفیت‌ها',
    descriptionEn: 'Ramsar satellite wetlands, deltaic reedbeds & halophyte belts',
    geometryKind: 'polygon',
    defaultVisible: true,
    defaultOpacity: 0.85,
    legendColor: ULO_COLORS.vegetationStroke,
    strokeColor: ULO_COLORS.vegetationStroke,
    fillColor: ULO_COLORS.vegetationFill,
    fillOpacity: 0.45,
    strokeWidth: 1.6,
  },
  {
    key: 'rivers',
    category: 'hydro_infra',
    fileName: 'urmia_rivers.geojson',
    titleFa: 'شبکه رودخانه‌های ورودی حوضه',
    titleEn: 'Major Tributary Rivers',
    descriptionFa: 'زرینه‌رود، سیمینه‌رود، آجی‌چای، شهرچای، باراندوزچای، نازلوچای و گدارچای',
    descriptionEn: 'Zarrineh, Simineh, Aji Chai, Shahr Chai, Baranduz, Nazlu & Gadar',
    geometryKind: 'line',
    defaultVisible: true,
    defaultOpacity: 0.9,
    legendColor: ULO_COLORS.riverStroke,
    strokeColor: ULO_COLORS.riverStroke,
    strokeWidth: 2.2,
  },
  {
    key: 'reservoirs',
    category: 'hydro_infra',
    fileName: 'urmia_reservoirs.geojson',
    titleFa: 'پهنه مخازن سدهای بزرگ',
    titleEn: 'Major Dam Reservoir Polygons',
    descriptionFa: 'پهنه آبی دریاچه سدهای بوکان، مهاباد، شهرچای، حسنلو، نهند و ساروق',
    descriptionEn: 'Impounded water bodies behind major basin dams',
    geometryKind: 'polygon',
    defaultVisible: true,
    defaultOpacity: 0.88,
    legendColor: ULO_COLORS.reservoirStroke,
    strokeColor: ULO_COLORS.reservoirStroke,
    fillColor: ULO_COLORS.reservoirFill,
    fillOpacity: 0.55,
    strokeWidth: 1.6,
  },
  {
    key: 'dams',
    category: 'hydro_infra',
    fileName: 'urmia_dams.geojson',
    titleFa: 'موقعیت و مشخصات سدهای اصلی حوضه',
    titleEn: 'Major Dams & Hydraulic Infrastructure',
    descriptionFa: '۱۰ سد کلیدی حوضه به همراه ظرفیت مخزن، رودخانه و کاربری',
    descriptionEn: '10 major dams across tributary rivers with storage capacity metadata',
    geometryKind: 'point',
    defaultVisible: true,
    defaultOpacity: 0.95,
    legendColor: ULO_COLORS.damFill,
    strokeColor: ULO_COLORS.damStroke,
    fillColor: ULO_COLORS.damFill,
    strokeWidth: 1.8,
    pointRadius: 6.5,
  },
  {
    key: 'landmarks',
    category: 'basin_monitoring',
    fileName: 'urmia_monitoring_landmarks.geojson',
    titleFa: 'ایستگاه‌های شاخص پایش و نقاط کلیدی',
    titleEn: 'Monitoring Stations & Key Landmarks',
    descriptionFa: 'ایستگاه‌های هیدرومتری، میانگذر کلانتری، جزایر پارک ملی و شهرهای اطراف',
    descriptionEn: 'Hydrometric stations, lake causeway, national park islands & cities',
    geometryKind: 'point',
    defaultVisible: true,
    defaultOpacity: 0.95,
    legendColor: ULO_COLORS.landmarkFill,
    strokeColor: ULO_COLORS.landmarkStroke,
    fillColor: ULO_COLORS.landmarkFill,
    strokeWidth: 1.6,
    pointRadius: 5.5,
  },
];
"""

# 4. src/components/UrmiaMap.css
URMIA_MAP_CSS = """.ulo-map-wrapper {
  position: relative;
  width: 100%;
  height: 700px;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(56, 189, 248, 0.25);
  background: #020617;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
}

.ulo-map-canvas {
  width: 100%;
  height: 100%;
}

/* Top Quick Spatial Bookmarks Bar */
.ulo-bookmarks-bar {
  position: absolute;
  top: 14px;
  z-index: 10;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  max-width: calc(100% - 410px);
  padding: 6px 8px;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.86);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(148, 163, 184, 0.22);
}

.ulo-map-wrapper.is-rtl .ulo-bookmarks-bar {
  left: 52px;
}

.ulo-map-wrapper.is-ltr .ulo-bookmarks-bar {
  left: 52px;
}

.ulo-bookmark-btn {
  padding: 5px 10px;
  border-radius: 8px;
  border: 1px solid rgba(56, 189, 248, 0.24);
  background: rgba(30, 41, 59, 0.85);
  color: #e2e8f0;
  font-size: 0.74rem;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.16s ease;
  white-space: nowrap;
}

.ulo-bookmark-btn:hover {
  background: rgba(14, 116, 144, 0.55);
  border-color: #38bdf8;
  color: #ffffff;
}

/* Layer Control Drawer */
.ulo-layer-panel {
  position: absolute;
  top: 14px;
  z-index: 11;
  width: 340px;
  max-height: calc(100% - 28px);
  overflow-y: auto;
  padding: 13px 14px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(148, 163, 184, 0.24);
  color: #f8fafc;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
  scrollbar-width: thin;
  scrollbar-color: rgba(56, 189, 248, 0.4) transparent;
}

.ulo-layer-panel.is-collapsed {
  width: auto;
  max-width: 240px;
  padding: 9px 12px;
  overflow: hidden;
}

.ulo-map-wrapper.is-rtl .ulo-layer-panel {
  right: 14px;
  direction: rtl;
  text-align: right;
}

.ulo-map-wrapper.is-ltr .ulo-layer-panel {
  right: 14px;
  direction: ltr;
  text-align: left;
}

.ulo-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ulo-panel-title {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 700;
  color: #38bdf8;
}

.ulo-collapse-btn {
  padding: 4px 9px;
  border-radius: 7px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(30, 41, 59, 0.85);
  color: #cbd5e1;
  font-size: 0.72rem;
  font-family: inherit;
  cursor: pointer;
}

.ulo-collapse-btn:hover {
  border-color: #38bdf8;
  color: #ffffff;
}

.ulo-panel-body {
  margin-top: 10px;
}

.ulo-section-label {
  display: block;
  margin: 8px 0 5px;
  font-size: 0.72rem;
  font-weight: 600;
  color: #94a3b8;
}

.ulo-basemap-select {
  width: 100%;
  padding: 7px 10px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: #0f172a;
  color: #f1f5f9;
  font-size: 0.78rem;
  font-family: inherit;
  cursor: pointer;
}

.ulo-basemap-select:focus {
  outline: none;
  border-color: #38bdf8;
}

/* Quick layer preset actions */
.ulo-quick-actions {
  display: flex;
  gap: 6px;
  margin: 10px 0 6px;
}

.ulo-quick-btn {
  flex: 1;
  padding: 5px 6px;
  border-radius: 7px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  background: rgba(30, 41, 59, 0.75);
  color: #cbd5e1;
  font-size: 0.71rem;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.14s ease;
}

.ulo-quick-btn:hover {
  border-color: #38bdf8;
  color: #ffffff;
  background: rgba(14, 116, 144, 0.4);
}

/* Layer Category Group */
.ulo-category-group {
  margin-top: 8px;
  border-top: 1px solid rgba(148, 163, 184, 0.14);
  padding-top: 6px;
}

.ulo-category-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: transparent;
  border: none;
  padding: 4px 2px;
  color: #7dd3fc;
  font-size: 0.75rem;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
}

.ulo-category-items {
  margin-top: 4px;
}

.ulo-layer-card {
  padding: 6px 7px;
  border-radius: 8px;
  margin-bottom: 4px;
  background: rgba(30, 41, 59, 0.38);
  border: 1px solid transparent;
  transition: all 0.15s ease;
}

.ulo-layer-card.is-active {
  background: rgba(30, 41, 59, 0.72);
  border-color: rgba(56, 189, 248, 0.22);
}

.ulo-layer-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  cursor: pointer;
}

.ulo-layer-item input[type='checkbox'] {
  margin-top: 3px;
  accent-color: #38bdf8;
  cursor: pointer;
}

.ulo-legend-swatch {
  width: 13px;
  height: 13px;
  margin-top: 3px;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.35);
}

.ulo-layer-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.ulo-layer-name {
  font-size: 0.79rem;
  font-weight: 600;
  color: #f1f5f9;
  line-height: 1.3;
}

.ulo-layer-desc {
  font-size: 0.68rem;
  color: #94a3b8;
  line-height: 1.35;
}

.ulo-opacity-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 5px;
  padding-top: 4px;
  border-top: 1px dashed rgba(148, 163, 184, 0.15);
  font-size: 0.68rem;
  color: #94a3b8;
}

.ulo-opacity-slider {
  flex: 1;
  height: 4px;
  accent-color: #38bdf8;
  cursor: pointer;
}

/* Dynamic Shoreline Legend Pill */
.ulo-shoreline-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 5px;
  font-size: 0.66rem;
  color: #cbd5e1;
}

.ulo-shoreline-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(15, 23, 42, 0.75);
}

.ulo-shoreline-dot {
  width: 8px;
  height: 3px;
  border-radius: 2px;
}

.ulo-status-badge {
  margin-top: 9px;
  padding: 6px 9px;
  border-radius: 8px;
  font-size: 0.72rem;
  background: rgba(2, 132, 199, 0.18);
  color: #7dd3fc;
  border: 1px solid rgba(56, 189, 248, 0.25);
}

.ulo-error-box {
  margin-top: 8px;
  padding: 6px 9px;
  border-radius: 8px;
  font-size: 0.72rem;
  background: rgba(220, 38, 38, 0.2);
  color: #fca5a5;
  border: 1px solid rgba(248, 113, 113, 0.35);
}

.ulo-coords-bar {
  position: absolute;
  bottom: 12px;
  left: 12px;
  z-index: 10;
  padding: 5px 11px;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.88);
  border: 1px solid rgba(148, 163, 184, 0.24);
  color: #cbd5e1;
  font-size: 0.73rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  direction: ltr;
}

/* MapLibre Scientific Popup Styling */
.ulo-popup .maplibregl-popup-content {
  background: rgba(15, 23, 42, 0.96);
  color: #f8fafc;
  border: 1px solid rgba(56, 189, 248, 0.42);
  border-radius: 12px;
  padding: 12px 14px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.58);
  max-width: 340px;
}

.ulo-popup .maplibregl-popup-tip {
  border-top-color: rgba(15, 23, 42, 0.96) !important;
  border-bottom-color: rgba(15, 23, 42, 0.96) !important;
}

.ulo-popup .maplibregl-popup-close-button {
  color: #94a3b8;
  font-size: 18px;
  padding: 4px 8px;
}

.ulo-popup-body.is-rtl {
  direction: rtl;
  text-align: right;
}

.ulo-popup-body.is-ltr {
  direction: ltr;
  text-align: left;
}

.ulo-popup-title {
  font-weight: 700;
  font-size: 0.9rem;
  color: #38bdf8;
  margin-bottom: 3px;
  padding-inline-end: 16px;
}

.ulo-popup-layer {
  display: inline-block;
  font-size: 0.68rem;
  color: #cbd5e1;
  background: rgba(30, 41, 59, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 6px;
  padding: 2px 7px;
  margin-bottom: 8px;
}

.ulo-popup-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.74rem;
}

.ulo-popup-table td {
  padding: 4px 3px;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
  vertical-align: top;
}

.ulo-popup-key {
  color: #94a3b8;
  padding-inline-end: 8px;
  white-space: nowrap;
  font-weight: 500;
}

.ulo-popup-val {
  color: #f1f5f9;
  font-weight: 600;
}

@media (max-width: 900px) {
  .ulo-map-wrapper {
    height: 580px;
  }
  .ulo-bookmarks-bar {
    display: none;
  }
  .ulo-layer-panel {
    width: 280px;
    max-height: 56%;
  }
}
"""

# 5. src/components/UrmiaMap.tsx
URMIA_MAP_TSX = """import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import type {
  CircleLayerSpecification,
  FillLayerSpecification,
  GeoJSONSourceSpecification,
  LineLayerSpecification,
  Map as MapLibreMap,
  MapMouseEvent,
  Popup as MapLibrePopup,
  StyleSpecification,
} from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import './UrmiaMap.css';

import { BASEMAPS } from '../map/basemaps';
import { LAYER_CATEGORIES, LAYER_CONFIGS } from '../map/layers';
import type { GeoLayerMeta, LayerCategory, LayerKey } from '../map/layers';
import { SPATIAL_BOOKMARKS, ULO_COLORS, URMIA_VIEWPORT } from '../map/theme';
import type { SpatialBookmark } from '../map/theme';

export type MapLang = 'fa' | 'en';

interface UrmiaMapProps {
  lang: MapLang;
}

type LayerData = GeoJSONSourceSpecification['data'];

interface FeatureLike {
  geometry?: { coordinates?: unknown } | null;
}

interface BoundsAcc {
  minLng: number;
  minLat: number;
  maxLng: number;
  maxLat: number;
  any: boolean;
}

const INITIAL_VISIBILITY = LAYER_CONFIGS.reduce<Record<LayerKey, boolean>>((acc, cfg) => {
  acc[cfg.key] = cfg.defaultVisible;
  return acc;
}, {} as Record<LayerKey, boolean>);

const INITIAL_OPACITY = LAYER_CONFIGS.reduce<Record<LayerKey, number>>((acc, cfg) => {
  acc[cfg.key] = cfg.defaultOpacity;
  return acc;
}, {} as Record<LayerKey, number>);

const INITIAL_OPEN_GROUPS: Record<LayerCategory, boolean> = {
  lake_dynamics: true,
  hydro_infra: true,
  ecology: true,
  basin_monitoring: false,
};

const sourceId = (key: LayerKey) => 'ulo-src-' + key;
const fillId = (key: LayerKey) => 'ulo-fill-' + key;
const lineId = (key: LayerKey) => 'ulo-line-' + key;
const circleId = (key: LayerKey) => 'ulo-circle-' + key;

const FIELD_LABELS: Record<string, { fa: string; en: string; unitFa?: string; unitEn?: string }> = {
  year: { fa: 'سال مرجع', en: 'Reference Year' },
  observation_date: { fa: 'تاریخ مشاهده', en: 'Observation Date' },
  water_level_m: { fa: 'تراز سطح آب', en: 'Water Level', unitFa: 'متر', unitEn: 'm a.s.l.' },
  contour_elevation_m: { fa: 'تراز منحنی میزان', en: 'Contour Elevation', unitFa: 'متر', unitEn: 'm a.s.l.' },
  approx_area_km2: { fa: 'مساحت تقریبی پهنه', en: 'Approx. Area', unitFa: 'km²', unitEn: 'km²' },
  area_km2: { fa: 'مساحت', en: 'Area', unitFa: 'km²', unitEn: 'km²' },
  SUB_AREA: { fa: 'مساحت زیرحوضه', en: 'Sub-basin Area', unitFa: 'km²', unitEn: 'km²' },
  shoreline_length_km: { fa: 'طول خط ساحلی', en: 'Shoreline Length', unitFa: 'کیلومتر', unitEn: 'km' },
  salinity_g_l: { fa: 'شوری آب', en: 'Salinity', unitFa: 'گرم/لیتر', unitEn: 'g/L' },
  max_depth_m: { fa: 'حداکثر عمق', en: 'Max Depth', unitFa: 'متر', unitEn: 'm' },
  dust_hazard_index: { fa: 'شاخص مخاطره گردوغبار نمکی', en: 'Salt-Dust Hazard Index' },
  dominant_crust: { fa: 'پوسته تبخیری غالب', en: 'Dominant Salt Crust' },
  exposed_since: { fa: 'شروع رخنمون نمکی', en: 'Exposed Since' },
  river_fa: { fa: 'رودخانه', en: 'River' },
  river_en: { fa: 'River', en: 'River' },
  capacity_mcm: { fa: 'ظرفیت کل مخزن', en: 'Reservoir Capacity', unitFa: 'میلیون مترمکعب', unitEn: 'MCM' },
  commissioned_year: { fa: 'سال بهره‌برداری', en: 'Commissioned Year' },
  purpose_fa: { fa: 'کاربری سد', en: 'Purpose' },
  purpose_en: { fa: 'Purpose', en: 'Purpose' },
  eco_type: { fa: 'تیپ اکولوژیک', en: 'Ecological Type' },
  ndvi_summer_mean: { fa: 'میانگین شاخص گیاهی (NDVI)', en: 'Mean Summer NDVI' },
  protection_status: { fa: 'وضعیت حفاظتی', en: 'Protection Status' },
  water_source_fa: { fa: 'منبع تغذیه آبی', en: 'Water Source' },
  water_source_en: { fa: 'Water Source', en: 'Water Source' },
  regime: { fa: 'رژیم هیدرولوژیک', en: 'Hydrological Regime' },
  sensor_basis: { fa: 'مبنای سنجش از دور', en: 'Remote Sensing Basis' },
  category: { fa: 'دسته ایستگاه/نقطه', en: 'Landmark Category' },
  HYBAS_ID: { fa: 'شناسه هیدروبیسین', en: 'HydroBASINS ID' },
  PFAF_ID: { fa: 'کد فاف‌استتر', en: 'Pfafstetter Code' },
};

const HIDDEN_POPUP_KEYS = new Set([
  'id',
  'zone_id',
  'dam_id',
  'eco_id',
  'color_hint',
  'name_fa',
  'name_en',
  'river_name_fa',
  'river_name_en',
  'title_fa',
  'title_en',
]);

function escapeHtml(value: unknown): string {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function pickTitle(cfg: GeoLayerMeta, props: Record<string, unknown>, lang: MapLang): string {
  const candidates =
    lang === 'fa'
      ? ['name_fa', 'river_name_fa', 'subbasin_fa', 'title_fa', 'station_fa', 'name_en', 'name', 'HYBAS_ID', 'id']
      : ['name_en', 'river_name_en', 'subbasin_en', 'title_en', 'station_en', 'name', 'name_fa', 'HYBAS_ID', 'id'];

  for (const key of candidates) {
    const value = props[key];
    if ((typeof value === 'string' && value.trim() !== '') || typeof value === 'number') {
      return String(value);
    }
  }
  return lang === 'fa' ? cfg.titleFa : cfg.titleEn;
}

function buildPopupHtml(cfg: GeoLayerMeta, props: Record<string, unknown>, lang: MapLang): string {
  const isFa = lang === 'fa';
  const dirClass = isFa ? 'is-rtl' : 'is-ltr';
  const layerLabel = isFa ? cfg.titleFa : cfg.titleEn;

  const entries = Object.entries(props).filter(([key, value]) => {
    if (HIDDEN_POPUP_KEYS.has(key)) return false;
    if (value === null || value === undefined || value === '') return false;
    if (isFa && key.endsWith('_en') && props[key.replace(/_en$/, '_fa')]) return false;
    if (!isFa && key.endsWith('_fa') && props[key.replace(/_fa$/, '_en')]) return false;
    return true;
  });

  const rows = entries
    .slice(0, 10)
    .map(([key, value]) => {
      const meta = FIELD_LABELS[key];
      const label = meta ? (isFa ? meta.fa : meta.en) : key;
      const unit = meta ? (isFa ? meta.unitFa : meta.unitEn) : undefined;
      const formattedVal =
        typeof value === 'number'
          ? Number.isInteger(value)
            ? value.toLocaleString('en-US')
            : value.toLocaleString('en-US', { maximumFractionDigits: 2 })
          : String(value);

      return (
        '<tr><td class="ulo-popup-key">' +
        escapeHtml(label) +
        '</td><td class="ulo-popup-val">' +
        escapeHtml(formattedVal) +
        (unit ? ' ' + escapeHtml(unit) : '') +
        '</td></tr>'
      );
    })
    .join('');

  const noteText = isFa ? props.note_fa : props.note_en;

  return (
    '<div class="ulo-popup-body ' +
    dirClass +
    '">' +
    '<div class="ulo-popup-title">' +
    escapeHtml(pickTitle(cfg, props, lang)) +
    '</div>' +
    '<div class="ulo-popup-layer">' +
    escapeHtml(layerLabel) +
    '</div>' +
    (rows ? '<table class="ulo-popup-table">' + rows + '</table>' : '') +
    (typeof noteText === 'string' && noteText
      ? '<div style="margin-top:6px;font-size:0.7rem;color:#cbd5e1;">' + escapeHtml(noteText) + '</div>'
      : '') +
    '</div>'
  );
}

function buildStyle(
  tiles: string[],
  tileSize: number,
  maxZoom: number,
  attribution: string
): StyleSpecification {
  return {
    version: 8,
    sources: {
      'ulo-basemap': {
        type: 'raster',
        tiles,
        tileSize,
        maxzoom: maxZoom,
        attribution,
      },
    },
    layers: [{ id: 'ulo-basemap', type: 'raster', source: 'ulo-basemap' }],
  };
}

function collectBounds(coords: unknown, acc: BoundsAcc): void {
  if (!Array.isArray(coords) || coords.length === 0) return;

  if (typeof coords[0] === 'number' && typeof coords[1] === 'number') {
    const lng = coords[0] as number;
    const lat = coords[1] as number;
    if (!acc.any) {
      acc.minLng = lng;
      acc.maxLng = lng;
      acc.minLat = lat;
      acc.maxLat = lat;
      acc.any = true;
    } else {
      acc.minLng = Math.min(acc.minLng, lng);
      acc.maxLng = Math.max(acc.maxLng, lng);
      acc.minLat = Math.min(acc.minLat, lat);
      acc.maxLat = Math.max(acc.maxLat, lat);
    }
    return;
  }

  coords.forEach((child) => collectBounds(child, acc));
}

export default function UrmiaMap({ lang }: UrmiaMapProps) {
  const isFa = lang === 'fa';

  const [activeBasemap, setActiveBasemap] = useState<string>(BASEMAPS[0].id);
  const [visibleLayers, setVisibleLayers] = useState<Record<LayerKey, boolean>>(INITIAL_VISIBILITY);
  const [layerOpacity, setLayerOpacity] = useState<Record<LayerKey, number>>(INITIAL_OPACITY);
  const [openGroups, setOpenGroups] = useState<Record<LayerCategory, boolean>>(INITIAL_OPEN_GROUPS);
  const [panelCollapsed, setPanelCollapsed] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadErrors, setLoadErrors] = useState<string[]>([]);
  const [loadedCount, setLoadedCount] = useState<number>(0);
  const [coords, setCoords] = useState<{ lat: number; lng: number }>({
    lat: URMIA_VIEWPORT.center[1],
    lng: URMIA_VIEWPORT.center[0],
  });

  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const popupRef = useRef<MapLibrePopup | null>(null);
  const lastPopupArgsRef = useRef<{
    lngLat: { lng: number; lat: number };
    cfg: GeoLayerMeta;
    props: Record<string, unknown>;
  } | null>(null);
  const langRef = useRef<MapLang>(lang);
  const geoDataRef = useRef<Partial<Record<LayerKey, LayerData>>>({});
  const visibleRef = useRef<Record<LayerKey, boolean>>(INITIAL_VISIBILITY);
  const opacityRef = useRef<Record<LayerKey, number>>(INITIAL_OPACITY);
  const cfgByIdRef = useRef<Record<string, GeoLayerMeta>>({});
  const syncRef = useRef<(() => void) | null>(null);
  const appliedBasemapRef = useRef<string>(BASEMAPS[0].id);
  const didFitRef = useRef<boolean>(false);
  const lastMoveRef = useRef<number>(0);

  useEffect(() => {
    langRef.current = lang;
    if (popupRef.current && lastPopupArgsRef.current) {
      const { cfg, props } = lastPopupArgsRef.current;
      popupRef.current.setHTML(buildPopupHtml(cfg, props, lang));
    }
  }, [lang]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || mapRef.current) return;

    const first = BASEMAPS[0];
    const map = new maplibregl.Map({
      container,
      style: buildStyle(first.tiles, first.tileSize, first.maxZoom, first.attribution),
      center: URMIA_VIEWPORT.center,
      zoom: URMIA_VIEWPORT.zoom,
      minZoom: URMIA_VIEWPORT.minZoom,
      maxZoom: URMIA_VIEWPORT.maxZoom,
      attributionControl: false,
    });
    mapRef.current = map;

    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-left');
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 140, unit: 'metric' }), 'bottom-right');
    map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-left');

    const sync = () => {
      const activeMap = mapRef.current;
      if (!activeMap || !activeMap.isStyleLoaded()) return;

      LAYER_CONFIGS.forEach((cfg) => {
        const data = geoDataRef.current[cfg.key];
        const sId = sourceId(cfg.key);
        if (!data) return;

        if (!activeMap.getSource(sId)) {
          activeMap.addSource(sId, { type: 'geojson', data });
        }

        const visibility: 'visible' | 'none' = visibleRef.current[cfg.key] ? 'visible' : 'none';
        const userOpacity = opacityRef.current[cfg.key] ?? cfg.defaultOpacity;

        // 1. Polygon Fill Layer
        if (cfg.geometryKind === 'polygon') {
          const fId = fillId(cfg.key);
          const baseFillOpacity = (cfg.fillOpacity ?? 0.25) * userOpacity;

          let fillColorExpr: FillLayerSpecification['paint'] = {
            'fill-color': cfg.fillColor ?? ULO_COLORS.watershedFill,
            'fill-opacity': baseFillOpacity,
          };

          if (cfg.key === 'desiccatedZones') {
            fillColorExpr = {
              'fill-color': [
                'match',
                ['get', 'dust_hazard_index'],
                'critical',
                '#f59e0b',
                'very_high',
                '#fbbf24',
                '#fde68a',
              ],
              'fill-opacity': baseFillOpacity,
            };
          } else if (cfg.key === 'riparianVegetation') {
            fillColorExpr = {
              'fill-color': [
                'match',
                ['get', 'eco_type'],
                'satellite_freshwater_brackish_wetland',
                '#10b981',
                'riparian_deltaic_reedbed',
                '#22c55e',
                '#84cc16',
              ],
              'fill-opacity': baseFillOpacity,
            };
          }

          if (!activeMap.getLayer(fId)) {
            activeMap.addLayer({
              id: fId,
              type: 'fill',
              source: sId,
              layout: { visibility },
              paint: fillColorExpr,
            });
          } else {
            activeMap.setLayoutProperty(fId, 'visibility', visibility);
            activeMap.setPaintProperty(fId, 'fill-opacity', baseFillOpacity);
          }
          cfgByIdRef.current[fId] = cfg;
        }

        // 2. Line / Outline Layer (for polygons & lines)
        if (cfg.geometryKind === 'polygon' || cfg.geometryKind === 'line') {
          const lId = lineId(cfg.key);
          const lineOpacity = Math.min(1, userOpacity);

          const paint: NonNullable<LineLayerSpecification['paint']> = {
            'line-color':
              cfg.key === 'shorelines'
                ? [
                    'match',
                    ['get', 'year'],
                    1995,
                    '#38bdf8',
                    2005,
                    '#22d3ee',
                    2015,
                    '#facc15',
                    2020,
                    '#fb923c',
                    2026,
                    '#f43f5e',
                    cfg.strokeColor,
                  ]
                : cfg.strokeColor,
            'line-width': cfg.strokeWidth,
            'line-opacity': lineOpacity,
          };
          if (cfg.dashed) paint['line-dasharray'] = [4, 3];

          if (!activeMap.getLayer(lId)) {
            activeMap.addLayer({
              id: lId,
              type: 'line',
              source: sId,
              layout: { visibility, 'line-cap': 'round', 'line-join': 'round' },
              paint,
            });
          } else {
            activeMap.setLayoutProperty(lId, 'visibility', visibility);
            activeMap.setPaintProperty(lId, 'line-opacity', lineOpacity);
          }
          cfgByIdRef.current[lId] = cfg;
        }

        // 3. Point Circle Layer (Dams & Monitoring Landmarks)
        if (cfg.geometryKind === 'point') {
          const cId = circleId(cfg.key);
          const circlePaint: NonNullable<CircleLayerSpecification['paint']> = {
            'circle-radius':
              cfg.key === 'dams'
                ? [
                    'interpolate',
                    ['linear'],
                    ['coalesce', ['get', 'capacity_mcm'], 50],
                    20,
                    5.5,
                    200,
                    7.5,
                    800,
                    10.5,
                  ]
                : (cfg.pointRadius ?? 6),
            'circle-color': cfg.fillColor ?? ULO_COLORS.landmarkFill,
            'circle-stroke-color': cfg.strokeColor ?? ULO_COLORS.landmarkStroke,
            'circle-stroke-width': cfg.strokeWidth,
            'circle-opacity': Math.min(1, userOpacity),
            'circle-stroke-opacity': Math.min(1, userOpacity),
          };

          if (!activeMap.getLayer(cId)) {
            activeMap.addLayer({
              id: cId,
              type: 'circle',
              source: sId,
              layout: { visibility },
              paint: circlePaint,
            });
          } else {
            activeMap.setLayoutProperty(cId, 'visibility', visibility);
            activeMap.setPaintProperty(cId, 'circle-opacity', Math.min(1, userOpacity));
            activeMap.setPaintProperty(cId, 'circle-stroke-opacity', Math.min(1, userOpacity));
          }
          cfgByIdRef.current[cId] = cfg;
        }
      });

      if (!didFitRef.current) {
        const geo = geoDataRef.current.lakeBoundary ?? geoDataRef.current.watershed;
        if (geo && typeof geo === 'object') {
          const features = (geo as { features?: FeatureLike[] }).features ?? [];
          const acc: BoundsAcc = { minLng: 0, minLat: 0, maxLng: 0, maxLat: 0, any: false };
          features.forEach((feature) => collectBounds(feature.geometry?.coordinates, acc));

          if (acc.any) {
            didFitRef.current = true;
            activeMap.fitBounds(
              [
                [acc.minLng, acc.minLat],
                [acc.maxLng, acc.maxLat],
              ],
              { padding: { top: 65, bottom: 55, left: 60, right: 360 }, duration: 0 }
            );
          }
        }
      }
    };

    syncRef.current = sync;
    map.on('load', sync);
    map.on('style.load', sync);

    map.on('click', (event: MapMouseEvent) => {
      const features = map.queryRenderedFeatures(event.point);
      const target = features.find(
        (feature) => typeof feature.layer?.id === 'string' && cfgByIdRef.current[feature.layer.id]
      );
      if (!target || !target.layer) return;

      const cfg = cfgByIdRef.current[target.layer.id];
      const props = (target.properties ?? {}) as Record<string, unknown>;
      lastPopupArgsRef.current = { lngLat: event.lngLat, cfg, props };

      popupRef.current?.remove();
      const popup = new maplibregl.Popup({
        className: 'ulo-popup',
        maxWidth: '340px',
        closeButton: true,
      })
        .setLngLat(event.lngLat)
        .setHTML(buildPopupHtml(cfg, props, langRef.current))
        .addTo(map);

      popup.on('close', () => {
        if (popupRef.current === popup) {
          popupRef.current = null;
          lastPopupArgsRef.current = null;
        }
      });

      popupRef.current = popup;
    });

    map.on('mousemove', (event: MapMouseEvent) => {
      const now = Date.now();
      if (now - lastMoveRef.current > 85) {
        lastMoveRef.current = now;
        setCoords({ lat: event.lngLat.lat, lng: event.lngLat.lng });
      }

      const features = map.queryRenderedFeatures(event.point);
      const interactive = features.some(
        (feature) => typeof feature.layer?.id === 'string' && cfgByIdRef.current[feature.layer.id]
      );
      map.getCanvas().style.cursor = interactive ? 'pointer' : '';
    });

    return () => {
      popupRef.current?.remove();
      popupRef.current = null;
      lastPopupArgsRef.current = null;
      syncRef.current = null;
      cfgByIdRef.current = {};
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    const loadAll = async () => {
      setLoading(true);
      const errors: string[] = [];
      const loaded: Partial<Record<LayerKey, LayerData>> = {};

      await Promise.all(
        LAYER_CONFIGS.map(async (cfg) => {
          try {
            const response = await fetch('/geo/' + cfg.fileName);
            if (!response.ok) {
              throw new Error(cfg.fileName + ' (HTTP ' + response.status + ')');
            }
            loaded[cfg.key] = (await response.json()) as LayerData;
          } catch (error) {
            errors.push(error instanceof Error ? error.message : cfg.fileName);
          }
        })
      );

      if (cancelled) return;

      geoDataRef.current = loaded;
      setLoadedCount(Object.keys(loaded).length);
      setLoadErrors(errors);
      setLoading(false);
      syncRef.current?.();
    };

    loadAll();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (appliedBasemapRef.current === activeBasemap) return;

    const basemap = BASEMAPS.find((item) => item.id === activeBasemap);
    if (!basemap) return;

    appliedBasemapRef.current = basemap.id;
    map.setStyle(
      buildStyle(basemap.tiles, basemap.tileSize, basemap.maxZoom, basemap.attribution),
      { diff: false }
    );
  }, [activeBasemap]);

  useEffect(() => {
    visibleRef.current = visibleLayers;
    opacityRef.current = layerOpacity;
    syncRef.current?.();
  }, [visibleLayers, layerOpacity]);

  const toggleLayer = (key: LayerKey) => {
    setVisibleLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const changeOpacity = (key: LayerKey, value: number) => {
    setLayerOpacity((prev) => ({ ...prev, [key]: value }));
  };

  const toggleCategory = (cat: LayerCategory) => {
    setOpenGroups((prev) => ({ ...prev, [cat]: !prev[cat] }));
  };

  const applyPreset = (mode: 'default' | 'all' | 'minimal') => {
    const next = {} as Record<LayerKey, boolean>;
    LAYER_CONFIGS.forEach((cfg) => {
      if (mode === 'default') next[cfg.key] = cfg.defaultVisible;
      else if (mode === 'all') next[cfg.key] = true;
      else next[cfg.key] = cfg.key === 'activeWater' || cfg.key === 'lakeBoundary';
    });
    setVisibleLayers(next);
  };

  const flyToBookmark = (bm: SpatialBookmark) => {
    mapRef.current?.flyTo({
      center: bm.center,
      zoom: bm.zoom,
      duration: 1100,
      essential: true,
    });
  };

  const activeLayerCount = Object.values(visibleLayers).filter(Boolean).length;

  return (
    <div className={`ulo-map-wrapper ${isFa ? 'is-rtl' : 'is-ltr'}`}>
      <div ref={containerRef} className="ulo-map-canvas" />

      {/* Spatial Bookmarks Bar */}
      <div className="ulo-bookmarks-bar" role="toolbar" aria-label={isFa ? 'پرش سریع مکانی' : 'Spatial Bookmarks'}>
        {SPATIAL_BOOKMARKS.map((bm) => (
          <button
            key={bm.id}
            type="button"
            className="ulo-bookmark-btn"
            onClick={() => flyToBookmark(bm)}
          >
            {isFa ? bm.labelFa : bm.labelEn}
          </button>
        ))}
      </div>

      {/* Multi-Layer GIS Control Drawer */}
      <aside className={`ulo-layer-panel ${panelCollapsed ? 'is-collapsed' : ''}`}>
        <div className="ulo-panel-header">
          <h3 className="ulo-panel-title">
            {isFa ? 'کنترل لایه‌های مکانی (WebGIS)' : 'Spatial Layers (WebGIS)'}
          </h3>
          <button
            type="button"
            className="ulo-collapse-btn"
            onClick={() => setPanelCollapsed((prev) => !prev)}
          >
            {panelCollapsed
              ? isFa
                ? `باز کردن (${activeLayerCount})`
                : `Expand (${activeLayerCount})`
              : isFa
                ? 'جمع کردن'
                : 'Collapse'}
          </button>
        </div>

        {!panelCollapsed && (
          <div className="ulo-panel-body">
            <label className="ulo-section-label" htmlFor="ulo-basemap-select">
              {isFa ? 'نقشه پایه (Basemap)' : 'Basemap'}
            </label>
            <select
              id="ulo-basemap-select"
              className="ulo-basemap-select"
              value={activeBasemap}
              onChange={(event) => setActiveBasemap(event.target.value)}
            >
              {BASEMAPS.map((basemap) => (
                <option key={basemap.id} value={basemap.id}>
                  {isFa ? basemap.nameFa : basemap.nameEn}
                </option>
              ))}
            </select>

            <div className="ulo-quick-actions">
              <button type="button" className="ulo-quick-btn" onClick={() => applyPreset('default')}>
                {isFa ? 'حالت پیشنهادی' : 'Recommended'}
              </button>
              <button type="button" className="ulo-quick-btn" onClick={() => applyPreset('all')}>
                {isFa ? 'نمایش همه (۱۲)' : 'Show All (12)'}
              </button>
              <button type="button" className="ulo-quick-btn" onClick={() => applyPreset('minimal')}>
                {isFa ? 'فقط دریاچه' : 'Lake Only'}
              </button>
            </div>

            {LAYER_CATEGORIES.map((group) => {
              const items = LAYER_CONFIGS.filter((cfg) => cfg.category === group.id);
              const isOpen = openGroups[group.id];

              return (
                <div key={group.id} className="ulo-category-group">
                  <button
                    type="button"
                    className="ulo-category-btn"
                    onClick={() => toggleCategory(group.id)}
                  >
                    <span>{isFa ? group.titleFa : group.titleEn}</span>
                    <span>{isOpen ? '▾' : '▸'}</span>
                  </button>

                  {isOpen && (
                    <div className="ulo-category-items">
                      {items.map((cfg) => {
                        const isChecked = visibleLayers[cfg.key];
                        const op = layerOpacity[cfg.key] ?? cfg.defaultOpacity;

                        return (
                          <div
                            key={cfg.key}
                            className={`ulo-layer-card ${isChecked ? 'is-active' : ''}`}
                          >
                            <label className="ulo-layer-item">
                              <input
                                type="checkbox"
                                checked={isChecked}
                                onChange={() => toggleLayer(cfg.key)}
                              />
                              <span
                                className="ulo-legend-swatch"
                                style={{
                                  backgroundColor: cfg.legendColor,
                                  borderRadius: cfg.geometryKind === 'point' ? '50%' : '3px',
                                }}
                              />
                              <span className="ulo-layer-text">
                                <span className="ulo-layer-name">
                                  {isFa ? cfg.titleFa : cfg.titleEn}
                                </span>
                                <span className="ulo-layer-desc">
                                  {isFa ? cfg.descriptionFa : cfg.descriptionEn}
                                </span>
                              </span>
                            </label>

                            {isChecked && cfg.key === 'shorelines' && (
                              <div className="ulo-shoreline-legend" dir="ltr">
                                {[
                                  { yr: '1995', c: '#38bdf8' },
                                  { yr: '2005', c: '#22d3ee' },
                                  { yr: '2015', c: '#facc15' },
                                  { yr: '2020', c: '#fb923c' },
                                  { yr: '2026', c: '#f43f5e' },
                                ].map((item) => (
                                  <span key={item.yr} className="ulo-shoreline-chip">
                                    <span
                                      className="ulo-shoreline-dot"
                                      style={{ backgroundColor: item.c }}
                                    />
                                    {item.yr}
                                  </span>
                                ))}
                              </div>
                            )}

                            {isChecked && (
                              <div className="ulo-opacity-row">
                                <span>{isFa ? 'شفافیت:' : 'Opacity:'}</span>
                                <input
                                  type="range"
                                  className="ulo-opacity-slider"
                                  min={0.15}
                                  max={1}
                                  step={0.05}
                                  value={op}
                                  onChange={(e) => changeOpacity(cfg.key, Number(e.target.value))}
                                />
                                <span dir="ltr">{Math.round(op * 100)}%</span>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}

            <div className="ulo-status-badge">
              {loading
                ? isFa
                  ? 'در حال بارگذاری ۱۲ لایه مکانی GeoJSON ...'
                  : 'Loading 12 GeoJSON spatial layers...'
                : isFa
                  ? `${loadedCount} از ${LAYER_CONFIGS.length} لایه آماده | ${activeLayerCount} لایه فعال — برای مشاهده شناسنامه علمی روی عوارض نقشه کلیک کنید`
                  : `${loadedCount}/${LAYER_CONFIGS.length} layers loaded | ${activeLayerCount} active — click map features for scientific metadata`}
            </div>

            {loadErrors.length > 0 && (
              <div className="ulo-error-box">
                {isFa ? 'خطا در بارگذاری: ' : 'Load error: '}
                {loadErrors.join(isFa ? ' ، ' : ', ')}
              </div>
            )}
          </div>
        )}
      </aside>

      <div className="ulo-coords-bar">
        Lat: {coords.lat.toFixed(4)}° N | Lon: {coords.lng.toFixed(4)}° E
      </div>
    </div>
  );
}
"""

files_to_write = {
    WEB / "map" / "theme.ts": THEME_TS,
    WEB / "map" / "basemaps.ts": BASEMAPS_TS,
    WEB / "map" / "layers.ts": LAYERS_TS,
    WEB / "components" / "UrmiaMap.css": URMIA_MAP_CSS,
    WEB / "components" / "UrmiaMap.tsx": URMIA_MAP_TSX,
}

for path, content in files_to_write.items():
    path.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {path.relative_to(ROOT)}")

# Update map subtitle in App.tsx from 5 layers to 12 Phase-6 scientific layers
app_path = WEB / "App.tsx"
app_text = app_path.read_text(encoding="utf-8")

old_fa = "شامل ۵ لایه برداری علمی (مرز حوضه، زیرحوضه‌ها، پهنه مرجع اکولوژیک، رودخانه‌های اصلی و ایستگاه‌های پایش) با امکان روشن/خاموش کردن مجزا."
new_fa = "شامل ۱۲ لایه مکانی علمی (پهنه آبی فعلی، کانون‌های گردوغبار نمکی، خطوط ساحلی چندزمانه ۱۹۹۵ تا ۲۰۲۶، منحنی‌های هیپسومتری بستر، سدها و مخازن، تالاب‌های اقماری، رودخانه‌ها، زیرحوضه‌ها و ایستگاه‌های پایش) با کنترل شفافیت و شناسنامه تعاملی."

old_en = "Includes 5 toggleable GeoJSON layers (watershed boundary, sub-basins, ecological lake extent, major rivers, monitoring landmarks)."
new_en = "Includes 12 interactive GeoJSON layers (active brine water, desiccated salt-dust zones, 1995–2026 shorelines, bathymetric contours, dams & reservoirs, satellite wetlands, tributary rivers, sub-basins & monitoring stations) with opacity control."

if old_fa in app_text:
    app_text = app_text.replace(old_fa, new_fa)
if old_en in app_text:
    app_text = app_text.replace(old_en, new_en)

app_path.write_text(app_text, encoding="utf-8")
print("[OK] Updated map section description in web-dashboard/src/App.tsx")

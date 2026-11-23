import { ULO_COLORS } from './theme';

export type LayerKey = 'watershed' | 'subbasins' | 'lakeBoundary' | 'rivers' | 'landmarks';
export type GeometryKind = 'polygon' | 'line' | 'point';

export interface GeoLayerMeta {
  key: LayerKey;
  titleFa: string;
  titleEn: string;
  fileName: string;
  defaultVisible: boolean;
  geometryKind: GeometryKind;
  legendColor: string;
  strokeColor: string;
  strokeWidth: number;
  fillColor?: string;
  fillOpacity?: number;
  dashed?: boolean;
  descriptionFa: string;
  descriptionEn: string;
}

export const GEO_FILES: Record<LayerKey, string> = {
  watershed: 'urmia_watershed_basin.geojson',
  subbasins: 'urmia_subbasins.geojson',
  lakeBoundary: 'urmia_lake_boundary.geojson',
  rivers: 'urmia_major_rivers.geojson',
  landmarks: 'urmia_monitoring_landmarks.geojson',
};

export const LAYER_CONFIGS: GeoLayerMeta[] = [
  {
    key: 'watershed',
    titleFa: 'مرز حوضه آبریز دریاچه ارومیه',
    titleEn: 'Lake Urmia Watershed Boundary',
    fileName: GEO_FILES.watershed,
    defaultVisible: true,
    geometryKind: 'polygon',
    legendColor: ULO_COLORS.watershedStroke,
    strokeColor: ULO_COLORS.watershedStroke,
    strokeWidth: 2.2,
    fillColor: ULO_COLORS.watershedFill,
    fillOpacity: 0.1,
    dashed: true,
    descriptionFa: 'کد حوضه IR-30 - مساحت 51,709.81 کیلومتر مربع',
    descriptionEn: 'Basin Code IR-30 — Area: 51,709.81 km²',
  },
  {
    key: 'subbasins',
    titleFa: 'زیرحوضه‌های آبریز',
    titleEn: 'Hydrological Sub-basins',
    fileName: GEO_FILES.subbasins,
    defaultVisible: false,
    geometryKind: 'polygon',
    legendColor: ULO_COLORS.subbasinStroke,
    strokeColor: ULO_COLORS.subbasinStroke,
    strokeWidth: 1.2,
    fillColor: ULO_COLORS.subbasinFill,
    fillOpacity: 0.16,
    descriptionFa: 'تقسیم‌بندی هیدرولوژیک زیرحوضه‌ها',
    descriptionEn: 'Hydrological sub-catchment delineation',
  },
  {
    key: 'lakeBoundary',
    titleFa: 'پهنه مرجع اکولوژیک دریاچه (تراز 1274.1 متر)',
    titleEn: 'Ecological Reference Extent (1274.1 m a.s.l.)',
    fileName: GEO_FILES.lakeBoundary,
    defaultVisible: true,
    geometryKind: 'polygon',
    legendColor: ULO_COLORS.lakeBoundaryStroke,
    strokeColor: ULO_COLORS.lakeBoundaryStroke,
    strokeWidth: 2,
    fillColor: ULO_COLORS.lakeBoundaryFill,
    fillOpacity: 0.38,
    descriptionFa: 'مساحت پهنه مرجع 4,321.02 کیلومتر مربع',
    descriptionEn: 'Reference water surface area: 4,321.02 km²',
  },
  {
    key: 'rivers',
    titleFa: 'رودخانه‌های اصلی ورودی',
    titleEn: 'Major Tributary Rivers',
    fileName: GEO_FILES.rivers,
    defaultVisible: true,
    geometryKind: 'line',
    legendColor: ULO_COLORS.riverMain,
    strokeColor: ULO_COLORS.riverMain,
    strokeWidth: 2.4,
    descriptionFa: 'شبکه زهکشی اصلی تغذیه‌کننده دریاچه',
    descriptionEn: 'Primary drainage network feeding the lake',
  },
  {
    key: 'landmarks',
    titleFa: 'ایستگاه‌ها و نقاط شاخص پایش',
    titleEn: 'Monitoring Stations & Key Landmarks',
    fileName: GEO_FILES.landmarks,
    defaultVisible: true,
    geometryKind: 'point',
    legendColor: ULO_COLORS.landmarkFill,
    strokeColor: ULO_COLORS.landmarkStroke,
    strokeWidth: 1.6,
    descriptionFa: 'پل میانگذر شهید کلانتری و ایستگاه‌های پایش',
    descriptionEn: 'Shahid Kalantari Causeway & monitoring stations',
  },
];

export const LAYER_BY_KEY: Record<LayerKey, GeoLayerMeta> = LAYER_CONFIGS.reduce(
  (acc, cfg) => {
    acc[cfg.key] = cfg;
    return acc;
  },
  {} as Record<LayerKey, GeoLayerMeta>
);
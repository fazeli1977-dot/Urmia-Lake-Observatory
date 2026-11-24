import { ULO_COLORS } from './theme';

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
  | 'causeway'
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
    fileName: 'urmia_watershed_basin.geojson?v=real_osm_v3',
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
    fileName: 'urmia_subbasins.geojson?v=real_osm_v3',
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
    fileName: 'urmia_lake_boundary.geojson?v=real_osm_v3',
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
    fileName: 'urmia_desiccated_zones.geojson?v=real_osm_v3',
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
    fileName: 'urmia_hypsometric_contours.geojson?v=real_osm_v3',
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
    fileName: 'urmia_active_water.geojson?v=real_osm_v3',
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
    fileName: 'urmia_shorelines.geojson?v=real_osm_v3',
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
    fileName: 'urmia_riparian_vegetation.geojson?v=real_osm_v3',
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
    fileName: 'urmia_major_rivers.geojson?v=real_osm_v3',
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
    key: 'causeway',
    category: 'hydro_infra',
    fileName: 'urmia_causeway.geojson?v=real_osm_v3',
    titleFa: 'میان‌گذر شهید کلانتری (حقابه)',
    titleEn: 'Shahid Kalantari Causeway',
    descriptionFa: 'میان‌گذر سیمان‌ساز دو نیمه دریاچه ارومیه با beperه تبادل شورابه',
    descriptionEn: 'Shahid Kalantari Causeway connecting northern and southern lake basins',
    geometryKind: 'line',
    defaultVisible: true,
    defaultOpacity: 0.85,
    legendColor: ULO_COLORS.riverStroke,
    strokeColor: '#f59e0b',
    strokeWidth: 2.5,
  },
  {
    key: 'reservoirs',
    category: 'hydro_infra',
    fileName: 'urmia_reservoirs.geojson?v=real_osm_v3',
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
    fileName: 'urmia_dams.geojson?v=real_osm_v3',
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
    fileName: 'urmia_monitoring_landmarks.geojson?v=real_osm_v3',
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

export interface BasemapOption {
  id: string;
  nameFa: string;
  nameEn: string;
  tiles: string[];
  tileSize: number;
  maxZoom: number;
  attribution: string;
}

export const BASEMAPS: BasemapOption[] = [
  {
    id: 'esri-imagery',
    nameFa: 'تصویر ماهواره‌ای واقعی (Esri World Imagery)',
    nameEn: 'Satellite Imagery (Esri World Imagery)',
    tiles: [
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    ],
    tileSize: 256,
    maxZoom: 18,
    attribution: 'Tiles © Esri, Maxar, Earthstar Geographics, USDA, USGS',
  },
  {
    id: 'carto-dark',
    nameFa: 'نقشه پایه تاریک علمی (Esri Dark Gray Canvas)',
    nameEn: 'Scientific Dark Basemap (Esri Dark Gray)',
    tiles: [
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
    ],
    tileSize: 256,
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors © CARTO',
  },
  {
    id: 'osm-standard',
    nameFa: 'نقشه معابر و سکونتگاه‌ها (OpenStreetMap)',
    nameEn: 'Streets & Settlements (OpenStreetMap)',
    tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
    tileSize: 256,
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors',
  },
  {
    id: 'opentopomap',
    nameFa: 'توپوگرافی و ارتفاعات حوضه (OpenTopoMap)',
    nameEn: 'Basin Topography (OpenTopoMap)',
    tiles: [
      'https://a.tile.opentopomap.org/{z}/{x}/{y}.png',
      'https://b.tile.opentopomap.org/{z}/{x}/{y}.png',
    ],
    tileSize: 256,
    maxZoom: 17,
    attribution: 'Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap',
  },
];
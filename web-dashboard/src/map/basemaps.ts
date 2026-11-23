export interface BasemapConfig {
  id: string;
  nameFa: string;
  nameEn: string;
  tiles: string[];
  tileSize: number;
  maxZoom: number;
  attribution: string;
}

export const BASEMAPS: BasemapConfig[] = [
  {
    id: 'satellite',
    nameFa: 'تصویر ماهواره‌ای (Esri World Imagery)',
    nameEn: 'Satellite Imagery (Esri World Imagery)',
    tiles: [
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    ],
    tileSize: 256,
    maxZoom: 18,
    attribution: 'Tiles (c) Esri - Source: Esri, Maxar, Earthstar Geographics',
  },
  {
    id: 'dark',
    nameFa: 'نقشه پایه تاریک علمی (Esri Dark Gray Canvas)',
    nameEn: 'Scientific Dark Basemap (Esri Dark Gray Canvas)',
    tiles: [
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
    ],
    tileSize: 256,
    maxZoom: 16,
    attribution: 'Tiles (c) Esri - Esri, HERE, Garmin, OpenStreetMap contributors',
  },
  {
    id: 'topo',
    nameFa: 'توپوگرافی حوضه (OpenTopoMap)',
    nameEn: 'Basin Topography (OpenTopoMap)',
    tiles: [
      'https://a.tile.opentopomap.org/{z}/{x}/{y}.png',
      'https://b.tile.opentopomap.org/{z}/{x}/{y}.png',
      'https://c.tile.opentopomap.org/{z}/{x}/{y}.png',
    ],
    tileSize: 256,
    maxZoom: 17,
    attribution: 'Map data (c) OpenStreetMap contributors, SRTM | Style (c) OpenTopoMap (CC-BY-SA)',
  },
  {
    id: 'osm',
    nameFa: 'نقشه پایه معابر و شهرها (OpenStreetMap)',
    nameEn: 'Standard Reference Map (OpenStreetMap)',
    tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
    tileSize: 256,
    maxZoom: 19,
    attribution: '(c) OpenStreetMap contributors',
  },
];
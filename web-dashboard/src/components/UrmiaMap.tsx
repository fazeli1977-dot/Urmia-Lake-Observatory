import { useEffect, useRef, useState } from 'react';
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
import { fetchUrmiaLiveStacFeed } from '../map/liveStacFeed';
import type { LiveStacScene } from '../map/liveStacFeed';

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
  const liveEoEnabledRef = useRef<boolean>(false);
  const liveEoSourceRef = useRef<string>('ulo-src-live-eo');
  const liveEoLayerRef = useRef<string>('ulo-layer-live-eo');
  const [liveEoEnabled, setLiveEoEnabled] = useState<boolean>(false);
  const [liveEoScene, setLiveEoScene] = useState<LiveStacScene | null>(null);
  const [liveEoLoading, setLiveEoLoading] = useState<boolean>(false);
  const [liveEoBand] = useState<'true_color_webp' | 'ndwi_live_webp'>('true_color_webp');

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
                    ['to-number', ['get', 'capacity_mcm'], 50],
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

    // Live Sentinel-2 EO raster tile layer (optional, default off)
    let liveEoAbort: AbortController | null = null;
    const initLiveEo = async () => {
      const activeMap = mapRef.current;
      if (!activeMap) return;
      liveEoAbort = new AbortController();
      setLiveEoLoading(true);
      try {
        const feed = await fetchUrmiaLiveStacFeed(liveEoAbort.signal);
        if (!feed || !feed.latest_scene) {
          setLiveEoScene(null);
          return;
        }
        setLiveEoScene(feed.latest_scene);

        const tileUrl =
          liveEoBand === 'ndwi_live_webp'
            ? feed.latest_scene.tiles.ndwi_live_webp
            : feed.latest_scene.tiles.true_color_webp;

        if (!activeMap.getSource(liveEoSourceRef.current)) {
          activeMap.addSource(liveEoSourceRef.current, {
            type: 'raster',
            tiles: [tileUrl],
            tileSize: 256,
            minzoom: 6,
            maxzoom: 14,
            bounds: feed.mosaic_bounds ?? [44.80, 36.85, 46.15, 38.45],
            attribution: 'Sentinel-2 L2A / Copernicus',
          });
        }
        if (!activeMap.getLayer(liveEoLayerRef.current)) {
          const styleLayers = activeMap.getStyle().layers;
          const beforeId =
            styleLayers
              .map((l) => l.id)
              .find((id) => id !== 'ulo-basemap' && id !== liveEoLayerRef.current) ??
            undefined;
          activeMap.addLayer({
            id: liveEoLayerRef.current,
            type: 'raster',
            source: liveEoSourceRef.current,
            layout: { visibility: liveEoEnabledRef.current ? 'visible' : 'none' },
            paint: { 'raster-opacity': 0.85 },
          } as any, beforeId);
        } else {
          activeMap.setLayoutProperty(liveEoLayerRef.current, 'visibility', liveEoEnabledRef.current ? 'visible' : 'none');
        }
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          console.warn('[Live EO] Failed to load Sentinel-2 tiles:', err);
        }
        setLiveEoScene(null);
      } finally {
        setLiveEoLoading(false);
      }
    };
    initLiveEo();

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

  // Toggle live EO raster layer visibility
  useEffect(() => {
    liveEoEnabledRef.current = liveEoEnabled;
    const map = mapRef.current;
    if (!map) return;
    if (!map.getSource(liveEoSourceRef.current) || !map.getLayer(liveEoLayerRef.current)) return;
    map.setLayoutProperty(liveEoLayerRef.current, 'visibility', liveEoEnabled ? 'visible' : 'none');
  }, [liveEoEnabled]);

  // Retile when band changes (True Color <-> NDWI)
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (!liveEoScene) return;
    const tileUrl =
      liveEoBand === 'ndwi_live_webp'
        ? liveEoScene.tiles.ndwi_live_webp
        : liveEoScene.tiles.true_color_webp;
    const source = map.getSource(liveEoSourceRef.current);
    if (source && (source as any).setTiles) {
      (source as any).setTiles([tileUrl]);
    }
  }, [liveEoBand, liveEoScene]);

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

            {/* Live Sentinel-2 EO raster toggle (default off) */}
            <div className="ulo-eo-toggle">
              <label className="ulo-section-label" htmlFor="ulo-live-eo-toggle">
                {isFa ? 'لایه زنده Sentinel-2 (برPause است)' : 'Live Sentinel-2 EO (paused)'}
              </label>
              <button
                id="ulo-live-eo-toggle"
                type="button"
                className={`ulo-quick-btn ${liveEoEnabled ? 'is-active' : ''}`}
                onClick={() => setLiveEoEnabled((prev) => !prev)}
                disabled={liveEoLoading}
              >
                {liveEoLoading
                  ? isFa
                    ? 'در حال بارگذاری...'
                    : 'Loading...'
                  : liveEoEnabled
                  ? isFa
                    ? `غیرفعال کردن زنده (${liveEoBand === 'ndwi_live_webp' ? 'NDWI' : 'True Color'})`
                    : `Disable Live (${liveEoBand === 'ndwi_live_webp' ? 'NDWI' : 'True Color'})`
                  : isFa
                  ? 'فعال کردن لایه زنده'
                  : 'Enable Live Layer'}
              </button>
              {liveEoEnabled && liveEoScene && (
                <div className="ulo-eo-info">
                  <span dir="ltr">{liveEoScene.platform}</span>
                  <span>|</span>
                  <span dir="ltr">{liveEoScene.datetime}</span>
                  <span>|</span>
                  <span dir="ltr">{Math.round(liveEoScene.cloud_cover * 100)}% cloud</span>
                </div>
              )}
            </div>

            <div className="ulo-quick-actions">
              <button type="button" className="ulo-quick-btn" onClick={() => applyPreset('default')}>
                {isFa ? 'حالت پیشنهادی' : 'Recommended'}
              </button>
              <button type="button" className="ulo-quick-btn" onClick={() => applyPreset('all')}>
                {isFa ? 'نمایش همه (۱۳)' : 'Show All (13)'}
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
                  ? 'در حال بارگذاری ۱۳ لایه مکانی GeoJSON ...'
                  : 'Loading 13 GeoJSON spatial layers...'
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

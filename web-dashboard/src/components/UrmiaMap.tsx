import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import type {
  GeoJSONSourceSpecification,
  LayerSpecification,
  LineLayerSpecification,
  Map as MapLibreMap,
  MapMouseEvent,
  Popup as MapLibrePopup,
  StyleSpecification,
} from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import './UrmiaMap.css';

import { BASEMAPS } from '../map/basemaps';
import { LAYER_CONFIGS } from '../map/layers';
import type { GeoLayerMeta, LayerKey } from '../map/layers';
import { ULO_COLORS, URMIA_VIEWPORT } from '../map/theme';

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

const sourceId = (key: LayerKey) => 'ulo-src-' + key;
const fillId = (key: LayerKey) => 'ulo-fill-' + key;
const lineId = (key: LayerKey) => 'ulo-line-' + key;
const circleId = (key: LayerKey) => 'ulo-circle-' + key;

function escapeHtml(value: unknown): string {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function pickTitle(cfg: GeoLayerMeta, props: Record<string, unknown>, lang: MapLang): string {
  const candidates =
    lang === 'fa'
      ? ['name_fa', 'river_name_fa', 'subbasin_fa', 'title_fa', 'station_fa', 'name_en', 'name', 'id']
      : ['name_en', 'river_name_en', 'subbasin_en', 'title_en', 'station_en', 'name', 'name_fa', 'id'];

  for (const key of candidates) {
    const value = props[key];
    if (typeof value === 'string' && value.trim() !== '') return value;
  }
  return lang === 'fa' ? cfg.titleFa : cfg.titleEn;
}

function buildPopupHtml(cfg: GeoLayerMeta, props: Record<string, unknown>, lang: MapLang): string {
  const isFa = lang === 'fa';
  const dirClass = isFa ? 'is-rtl' : 'is-ltr';
  const layerLabel = isFa ? cfg.titleFa : cfg.titleEn;

  const rows = Object.entries(props)
    .filter(([, value]) => value !== null && value !== undefined && value !== '')
    .slice(0, 12)
    .map(
      ([key, value]) =>
        '<tr><td class="ulo-popup-key">' +
        escapeHtml(key) +
        '</td><td>' +
        escapeHtml(value) +
        '</td></tr>'
    )
    .join('');

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
    '<table class="ulo-popup-table">' +
    rows +
    '</table>' +
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

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-left');
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 130, unit: 'metric' }), 'bottom-right');
    map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-left');

    const sync = () => {
      const activeMap = mapRef.current;
      if (!activeMap) return;

      LAYER_CONFIGS.forEach((cfg) => {
        const data = geoDataRef.current[cfg.key];
        const sId = sourceId(cfg.key);
        if (!data) return;

        if (!activeMap.getSource(sId)) {
          activeMap.addSource(sId, { type: 'geojson', data });
        }

        const visibility: 'visible' | 'none' = visibleRef.current[cfg.key] ? 'visible' : 'none';

        if (cfg.geometryKind === 'polygon') {
          const fId = fillId(cfg.key);
          if (!activeMap.getLayer(fId)) {
            activeMap.addLayer({
              id: fId,
              type: 'fill',
              source: sId,
              layout: { visibility },
              paint: {
                'fill-color': cfg.fillColor ?? ULO_COLORS.watershedFill,
                'fill-opacity': cfg.fillOpacity ?? 0.15,
              },
            });
          } else {
            activeMap.setLayoutProperty(fId, 'visibility', visibility);
          }
          cfgByIdRef.current[fId] = cfg;
        }

        const lId = lineId(cfg.key);
        if (!activeMap.getLayer(lId)) {
          const paint: NonNullable<LineLayerSpecification['paint']> = {
            'line-color': cfg.strokeColor,
            'line-width': cfg.strokeWidth,
            'line-opacity': 0.92,
          };
          if (cfg.dashed) paint['line-dasharray'] = [4, 3];

          const spec: LayerSpecification = {
            id: lId,
            type: 'line',
            source: sId,
            layout: { visibility, 'line-cap': 'round', 'line-join': 'round' },
            paint,
          };
          activeMap.addLayer(spec);
        } else {
          activeMap.setLayoutProperty(lId, 'visibility', visibility);
        }
        cfgByIdRef.current[lId] = cfg;

        if (cfg.geometryKind === 'point') {
          const cId = circleId(cfg.key);
          if (!activeMap.getLayer(cId)) {
            activeMap.addLayer({
              id: cId,
              type: 'circle',
              source: sId,
              layout: { visibility },
              paint: {
                'circle-radius': 6,
                'circle-color': ULO_COLORS.landmarkFill,
                'circle-stroke-color': ULO_COLORS.landmarkStroke,
                'circle-stroke-width': 1.6,
                'circle-opacity': 0.95,
              },
            });
          } else {
            activeMap.setLayoutProperty(cId, 'visibility', visibility);
          }
          cfgByIdRef.current[cId] = cfg;
        }
      });

      if (!didFitRef.current) {
        const geo = geoDataRef.current.watershed ?? geoDataRef.current.lakeBoundary;
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
              { padding: 40, duration: 0 }
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
      if (now - lastMoveRef.current > 90) {
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
              throw new Error(cfg.fileName + ' - HTTP ' + response.status);
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
    syncRef.current?.();
  }, [visibleLayers]);

  const toggleLayer = (key: LayerKey) => {
    setVisibleLayers((previous) => ({ ...previous, [key]: !previous[key] }));
  };

  return (
    <div className={`ulo-map-wrapper ${isFa ? 'is-rtl' : 'is-ltr'}`}>
      <div ref={containerRef} className="ulo-map-canvas" />

      <div className="ulo-layer-panel">
        <h3 className="ulo-panel-title">
          {isFa ? 'لایه‌های مکانی دریاچه ارومیه' : 'Lake Urmia Spatial Layers'}
        </h3>

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

        <span className="ulo-section-label">
          {isFa ? 'لایه‌های علمی و هیدرولوژیک' : 'Scientific & Hydrological Layers'}
        </span>
        {LAYER_CONFIGS.map((cfg) => (
          <label key={cfg.key} className="ulo-layer-item">
            <input
              type="checkbox"
              checked={visibleLayers[cfg.key]}
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
              <span className="ulo-layer-name">{isFa ? cfg.titleFa : cfg.titleEn}</span>
              <span className="ulo-layer-desc">
                {isFa ? cfg.descriptionFa : cfg.descriptionEn}
              </span>
            </span>
          </label>
        ))}

        <div className="ulo-status-badge">
          {loading
            ? isFa
              ? 'در حال بارگذاری لایه‌های GeoJSON ...'
              : 'Loading GeoJSON spatial layers...'
            : isFa
              ? `${loadedCount} از ${LAYER_CONFIGS.length} لایه آماده نمایش`
              : `${loadedCount} of ${LAYER_CONFIGS.length} layers ready`}
        </div>

        {loadErrors.length > 0 && (
          <div className="ulo-error-box">
            {isFa ? 'خطا در بارگذاری: ' : 'Load error: '}
            {loadErrors.join(isFa ? ' ، ' : ', ')}
          </div>
        )}
      </div>

      <div className="ulo-coords-bar">
        Lat: {coords.lat.toFixed(4)}° N | Lon: {coords.lng.toFixed(4)}° E
      </div>
    </div>
  );
}
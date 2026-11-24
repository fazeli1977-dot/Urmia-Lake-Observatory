export interface LiveStacTileSet {
  true_color_webp: string;
  ndwi_live_webp: string;
}

export interface LiveStacScene {
  id: string;
  mgrs_tile?: string;
  datetime: string | null;
  cloud_cover: number;
  platform: string;
  bbox: [number, number, number, number];
  geometry: GeoJSON.Geometry;
  tiles: LiveStacTileSet;
}

export interface LiveStacFeedResponse {
  generated_at: string;
  basin: string;
  mosaic_search_id?: string;
  mosaic_bounds?: [number, number, number, number];
  benchmark: {
    stac_search_latency_ms: number;
    tiles_tested: number;
    tiles_succeeded: number;
    ndwi_probe_status?: number;
    ndwi_probe_ms?: number;
    tile_p50_ms: number;
    tile_p95_ms: number;
    avg_tile_size_kb: number;
    webp_optimized: boolean;
    ui_frame_budget_safe: boolean;
  };
  latest_scene: LiveStacScene;
  recent_scenes: LiveStacScene[];
}

let cachedFeed: LiveStacFeedResponse | null = null;

export async function fetchUrmiaLiveStacFeed(
  signal?: AbortSignal
): Promise<LiveStacFeedResponse | null> {
  if (cachedFeed) {
    return cachedFeed;
  }

  try {
    const res = await fetch(`${import.meta.env.BASE_URL}data/urmia_live_stac_feed.json?v=phase4_mosaic_v2`, {
      signal,
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      return null;
    }
    const data = (await res.json()) as LiveStacFeedResponse;
    cachedFeed = data;
    return data;
  } catch (err) {
    if ((err as Error).name !== 'AbortError') {
      console.warn('[TerraScope Live EO] Fallback to static layers:', err);
    }
    return null;
  }
}

export function scheduleIdleMapUpdate(callback: () => void): number {
  return window.requestAnimationFrame(() => {
    callback();
  });
}
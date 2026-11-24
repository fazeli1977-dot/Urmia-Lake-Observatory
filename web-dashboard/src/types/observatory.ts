export type Lang = 'fa' | 'en';

export type DataCategory =
  | 'satellite_observation'
  | 'model_reanalysis'
  | 'derived_index'
  | 'indirect_estimate'
  | 'ground_observation'
  | 'unavailable';

export interface WaterLevelPoint {
  date: string;
  water_level_m: number;
  area_km2: number;
  volume_km3: number;
  source: string;
}

export interface HypsometryPoint {
  elevation_m: number;
  area_km2: number;
  volume_km3: number;
}

export interface Era5MonthlyPoint {
  month: string;
  precip_mm: number;
  et0_mm: number;
  net_water_flux_mm: number;
  temp_mean_c: number;
}

export interface Era5DailyPoint {
  date: string;
  temp_mean_c: number;
  precip_mm: number;
  et0_mm: number;
}

export interface StacEndpointCheck {
  reachable?: boolean;
  latest_item_datetime?: string | null;
  item_id?: string | null;
  collection?: string;
  note?: string;
}

export interface LakeHydrologyDataset {
  schema_version: string;
  generated_at_utc: string;
  lake_name: string;
  identifiers: {
    cdse_clms_station_id?: string;
    hydroweb_id?: string;
    usda_grealm_id?: string;
  };
  data_provenance: {
    water_level_mode: string;
    stac_metadata_live: boolean;
    climate_era5_live: boolean;
    credentials_configured?: Record<string, boolean>;
  };
  current_status: {
    observation_date: string;
    water_level_m_asl: number;
    ecological_target_m_asl: number;
    ecological_deficit_m: number;
    estimated_area_km2: number;
    estimated_volume_km3: number;
    ecological_volume_deficit_km3: number;
    trailing_12m_precip_mm: number | null;
    trailing_12m_et0_mm: number | null;
  };
  stac_live_catalog?: {
    checked_at_utc?: string;
    cdse_clms_wl?: StacEndpointCheck;
    hydroweb_ope?: StacEndpointCheck;
  };
  hypsometry_curve: HypsometryPoint[];
  water_level_timeseries: WaterLevelPoint[];
  basin_climate_era5: {
    monthly_summary: Era5MonthlyPoint[];
    daily_tail_30d: Era5DailyPoint[];
  };
}

export interface TrendPeriodResult {
  start_date: string;
  end_date: string;
  mann_kendall: {
    n: number;
    s_statistic: number;
    var_s: number;
    z_score: number;
    p_value: number;
    kendall_tau: number;
    alpha: number;
    significant: boolean;
    trend: 'increasing' | 'decreasing' | 'no_significant_trend';
  };
  sens_slope_m: {
    slope_per_year: number;
    slope_per_decade: number;
    intercept: number;
  };
}

export interface LakeScientificAnalytics {
  schema_version: string;
  generated_at_utc: string;
  upstream_hydrology_schema: string;
  upstream_generated_at: string;
  station_metadata: {
    lake_name: string;
  };
  statistical_trends: {
    source_file: string;
    detected_columns: {
      date: string;
      level: string;
    };
    total_records: number;
    date_range: {
      start: string;
      end: string;
    };
    periods: {
      full_record: TrendPeriodResult;
      last_10_years?: TrendPeriodResult;
      last_5_years?: TrendPeriodResult;
    };
  };
  ecological_and_hazard_assessment: {
    ecological_benchmark: {
      target_level_m: number;
      target_area_km2: number;
      target_volume_km3: number;
      level_deficit_m: number;
      volume_deficit_km3: number;
      water_volume_retention_pct: number;
    };
    exposed_lakebed_playa: {
      current_wet_area_km2: number;
      exposed_salt_playa_vs_ecological_km2: number;
      exposed_bed_vs_max_historical_km2: number;
      desiccation_ratio_vs_ecological_pct: number;
    };
    salinity_and_biology: {
      estimated_salinity_g_l: number;
      halite_supersaturated: boolean;
      estimated_precipitated_salt_ratio: number;
      artemia_threshold_g_l: number;
      artemia_ecological_status: string;
    };
    climate_stress: {
      source_mode: string;
      annual_equiv_precip_mm: number | null;
      annual_equiv_evap_mm: number | null;
      mean_temp_c: number | null;
      p_to_e_ratio: number | null;
      climate_stress_score_0_100: number;
    };
    salt_dust_hazard: {
      index_0_100: number;
      hazard_tier: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
      primary_hotspot_zones: string[];
    };
  };
}
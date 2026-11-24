import {
  Waves,
  Maximize2,
  Droplets,
  TrendingDown,
  CloudRain,
  Thermometer,
  Sun,
  AlertTriangle,
  Sprout,
  Satellite,
  Clock,
  Activity
} from 'lucide-react';
import type {
  Lang,
  DataCategory,
  LakeHydrologyDataset,
  LakeScientificAnalytics
} from '../types/observatory';

interface KpiGridProps {
  lang: Lang;
  hydrology: LakeHydrologyDataset;
  analytics: LakeScientificAnalytics;
}

interface KpiItem {
  id: string;
  titleFa: string;
  titleEn: string;
  value: string;
  unitFa?: string;
  unitEn?: string;
  subtextFa: string;
  subtextEn: string;
  sourceFa: string;
  sourceEn: string;
  dateLabel: string;
  category: DataCategory;
  unavailable?: boolean;
  tone?: 'normal' | 'warning' | 'critical' | 'neutral';
  icon: JSX.Element;
}

const CATEGORY_LABELS: Record<DataCategory, { fa: string; en: string }> = {
  satellite_observation: { fa: 'مشاهده ماهواره‌ای', en: 'Satellite Observation' },
  model_reanalysis: { fa: 'بازتحلیل مدل‌محور', en: 'Model Reanalysis' },
  derived_index: { fa: 'شاخص مشتق‌شده علمی', en: 'Derived Scientific Index' },
  indirect_estimate: { fa: 'برآورد غیرمستقیم هیپسومتریک', en: 'Indirect Hypsometric Estimate' },
  ground_observation: { fa: 'مشاهده زمینی', en: 'Ground Observation' },
  unavailable: { fa: 'داده ناموجود', en: 'Unavailable Layer' }
};

export default function KpiGrid({ lang, hydrology, analytics }: KpiGridProps) {
  const isFa = lang === 'fa';
  const cur = hydrology.current_status;
  const eco = analytics.ecological_and_hazard_assessment;
  const trends = analytics.statistical_trends.periods;

  // Compute latest monthly water level / climate delta from verified series
  const wlSeries = hydrology.water_level_timeseries;
  const prevObs = wlSeries.length >= 2 ? wlSeries[wlSeries.length - 2] : null;
  const latestObs = wlSeries.length >= 1 ? wlSeries[wlSeries.length - 1] : null;
  const recentDeltaM =
    prevObs && latestObs ? Number((latestObs.water_level_m - prevObs.water_level_m).toFixed(3)) : null;

  const monthlyClimate = hydrology.basin_climate_era5?.monthly_summary ?? [];
  const lastMonthClimate =
    monthlyClimate.length > 0 ? monthlyClimate[monthlyClimate.length - 1] : null;

  const meanTemp12m =
    monthlyClimate.length >= 12
      ? Number(
          (
            monthlyClimate
              .slice(-12)
              .reduce((acc, item) => acc + item.temp_mean_c, 0) / 12
          ).toFixed(1)
        )
      : eco.climate_stress.mean_temp_c;

  const annualSlope = trends.last_5_years?.sens_slope_m.slope_per_year ?? trends.full_record.sens_slope_m.slope_per_year;
  const slopeWindow = trends.last_5_years ? '۵ ساله اخیر' : 'کل دوره';
  const slopeWindowEn = trends.last_5_years ? 'Last 5 Years' : 'Full Record';

  const stacDate =
    hydrology.stac_live_catalog?.cdse_clms_wl?.latest_item_datetime?.slice(0, 10) ||
    hydrology.stac_live_catalog?.checked_at_utc?.slice(0, 10) ||
    cur.observation_date;

  const unavailableText = isFa ? 'داده معتبر در دسترس نیست' : 'Data Unavailable';

  const items: KpiItem[] = [
    {
      id: 'water-level',
      titleFa: 'تراز فعلی سطح آب',
      titleEn: 'Current Water Level',
      value: cur.water_level_m_asl.toFixed(2),
      unitFa: 'متر از سطح دریا',
      unitEn: 'm a.s.l.',
      subtextFa: `کسری نسبت به تراز اکولوژیک (۱۲۷۴.۱ متر): ${cur.ecological_deficit_m.toFixed(2)} متر`,
      subtextEn: `Deficit vs. ecological target (1274.1 m): ${cur.ecological_deficit_m.toFixed(2)} m`,
      sourceFa: 'آلتیمتری ماهواره‌ای مرجع (Hydroweb / G-REALM / CLMS)',
      sourceEn: 'Satellite Radar Altimetry Benchmark (Hydroweb / CLMS)',
      dateLabel: cur.observation_date,
      category: 'satellite_observation',
      tone: 'critical',
      icon: <Waves size={20} />
    },
    {
      id: 'water-area',
      titleFa: 'پهنه مرطوب فعلی دریاچه',
      titleEn: 'Current Water Area',
      value: cur.estimated_area_km2.toFixed(1),
      unitFa: 'کیلومترمربع',
      unitEn: 'km²',
      subtextFa: `بستر نمکی خشک‌شده نسبت به تراز اکولوژیک: ${eco.exposed_lakebed_playa.exposed_salt_playa_vs_ecological_km2.toFixed(0)} کیلومترمربع`,
      subtextEn: `Exposed salt playa vs. ecological extent: ${eco.exposed_lakebed_playa.exposed_salt_playa_vs_ecological_km2.toFixed(0)} km²`,
      sourceFa: 'رابطه هیپسومتری کالیبره‌شده باتیمتری دریاچه',
      sourceEn: 'Calibrated Bathymetric Hypsometry Curve',
      dateLabel: cur.observation_date,
      category: 'indirect_estimate',
      tone: 'warning',
      icon: <Maximize2 size={20} />
    },
    {
      id: 'water-volume',
      titleFa: 'حجم آب برآوردی مخزن دریاچه',
      titleEn: 'Estimated Water Volume',
      value: cur.estimated_volume_km3.toFixed(2),
      unitFa: 'میلیارد مترمکعب (km³)',
      unitEn: 'km³ (BCM)',
      subtextFa: `تنها ${eco.ecological_benchmark.water_volume_retention_pct.toFixed(1)}٪ از حجم اکولوژیک (۱۴.۵ km³) باقی مانده است`,
      subtextEn: `Only ${eco.ecological_benchmark.water_volume_retention_pct.toFixed(1)}% of 14.5 km³ ecological volume retained`,
      sourceFa: 'انتگرال حجم-تراز هیپسومتری (عدم‌قطعیت ±۱۲٪)',
      sourceEn: 'Elevation-Volume Hypsometric Integral (±12% unc.)',
      dateLabel: cur.observation_date,
      category: 'indirect_estimate',
      tone: 'critical',
      icon: <Droplets size={20} />
    },
    {
      id: 'annual-change',
      titleFa: 'نرخ تغییر سالانه (شیب Sen)',
      titleEn: 'Annual Change Rate (Sen Slope)',
      value: `${annualSlope > 0 ? '+' : ''}${annualSlope.toFixed(3)}`,
      unitFa: 'متر در سال',
      unitEn: 'm / yr',
      subtextFa: `${slopeWindow}: ${annualSlope.toFixed(3)} متر بر سال`,
      subtextEn: `${slopeWindowEn}: ${annualSlope.toFixed(3)} m/yr`,
      sourceFa: 'آزمون ناپارامتریک Mann-Kendall + تخمین‌گر Sen',
      sourceEn: 'Non-parametric Mann-Kendall + Theil-Sen Estimator',
      dateLabel: `${trends.full_record.start_date} → ${trends.full_record.end_date}`,
      category: 'derived_index',
      tone: 'warning',
      icon: <TrendingDown size={20} />
    },
    {
      id: 'recent-step-change',
      titleFa: 'تغییر دو مشاهده متوالی اخیر',
      titleEn: 'Latest Observation Delta',
      value:
        recentDeltaM !== null
          ? `${recentDeltaM > 0 ? '+' : ''}${recentDeltaM.toFixed(2)}`
          : unavailableText,
      unitFa: recentDeltaM !== null ? 'متر' : undefined,
      unitEn: recentDeltaM !== null ? 'm' : undefined,
      subtextFa:
        prevObs && latestObs
          ? `از تاریخ ${prevObs.date} (${prevObs.water_level_m.toFixed(2)}m) تا ${latestObs.date}`
          : 'نیازمند حداقل دو مشاهده معتبر متوالی',
      subtextEn:
        prevObs && latestObs
          ? `From ${prevObs.date} (${prevObs.water_level_m.toFixed(2)} m) to ${latestObs.date}`
          : 'Requires at least two consecutive verified records',
      sourceFa: 'تفاضل مستقیم سری زمانی تراز دریاچه',
      sourceEn: 'Direct Sequential Altimetry Observation Delta',
      dateLabel: cur.observation_date,
      category: recentDeltaM !== null ? 'derived_index' : 'unavailable',
      unavailable: recentDeltaM === null,
      tone: 'normal',
      icon: <Activity size={20} />
    },
    {
      id: 'precip-12m',
      titleFa: 'بارش تجمعی ۱۲ ماه اخیر حوضه',
      titleEn: 'Trailing 12-Month Precipitation',
      value:
        cur.trailing_12m_precip_mm !== null
          ? cur.trailing_12m_precip_mm.toFixed(1)
          : unavailableText,
      unitFa: cur.trailing_12m_precip_mm !== null ? 'میلی‌متر' : undefined,
      unitEn: cur.trailing_12m_precip_mm !== null ? 'mm' : undefined,
      subtextFa: lastMonthClimate
        ? `آخرین ماه (${lastMonthClimate.month}): ${lastMonthClimate.precip_mm.toFixed(1)} میلی‌متر بارش`
        : 'برگرفته از سری بازتحلیل اقلیمی ERA5',
      subtextEn: lastMonthClimate
        ? `Latest month (${lastMonthClimate.month}): ${lastMonthClimate.precip_mm.toFixed(1)} mm precip`
        : 'Derived from ERA5 reanalysis series',
      sourceFa: 'بازتحلیل اقلیمی ECMWF ERA5 (Open-Meteo Archive)',
      sourceEn: 'ECMWF ERA5 Climate Reanalysis (Open-Meteo)',
      dateLabel: lastMonthClimate?.month ?? cur.observation_date,
      category: cur.trailing_12m_precip_mm !== null ? 'model_reanalysis' : 'unavailable',
      unavailable: cur.trailing_12m_precip_mm === null,
      tone: 'normal',
      icon: <CloudRain size={20} />
    },
    {
      id: 'temperature',
      titleFa: 'دمای میانگین سالانه حوضه',
      titleEn: 'Mean Annual Basin Temperature',
      value: meanTemp12m !== null ? `${meanTemp12m.toFixed(1)}°C` : unavailableText,
      subtextFa: lastMonthClimate
        ? `میانگین ماه ${lastMonthClimate.month}: ${lastMonthClimate.temp_mean_c.toFixed(1)} درجه سلسیوس`
        : 'میانگین دمای ۲ متری سطح زمین',
      subtextEn: lastMonthClimate
        ? `Month ${lastMonthClimate.month} mean: ${lastMonthClimate.temp_mean_c.toFixed(1)} °C`
        : '2-meter air temperature reanalysis',
      sourceFa: 'بازتحلیل اقلیمی ECMWF ERA5 (شبکه ۰.۲۵ درجه)',
      sourceEn: 'ECMWF ERA5 Reanalysis (2m Air Temp)',
      dateLabel: lastMonthClimate?.month ?? cur.observation_date,
      category: meanTemp12m !== null ? 'model_reanalysis' : 'unavailable',
      unavailable: meanTemp12m === null,
      tone: 'normal',
      icon: <Thermometer size={20} />
    },
    {
      id: 'evapotranspiration',
      titleFa: 'تبخیر-تعرق مرجع ۱۲ماهه (ET₀)',
      titleEn: 'Trailing 12-Month Reference ET₀',
      value:
        cur.trailing_12m_et0_mm !== null
          ? cur.trailing_12m_et0_mm.toFixed(0)
          : unavailableText,
      unitFa: cur.trailing_12m_et0_mm !== null ? 'میلی‌متر' : undefined,
      unitEn: cur.trailing_12m_et0_mm !== null ? 'mm' : undefined,
      subtextFa:
        eco.climate_stress.p_to_e_ratio !== null
          ? `نسبت خشکی (P/ET₀): ${eco.climate_stress.p_to_e_ratio.toFixed(2)} — تراز بیلان منفی شدید`
          : 'محاسبه به روش استاندارد FAO Penman-Monteith',
      subtextEn:
        eco.climate_stress.p_to_e_ratio !== null
          ? `Aridity ratio (P/ET₀): ${eco.climate_stress.p_to_e_ratio.toFixed(2)} — Severe moisture deficit`
          : 'FAO-56 Penman-Monteith ET₀ formulation',
      sourceFa: 'مدل FAO-56 بر روی داده‌های بازتحلیل ERA5',
      sourceEn: 'FAO-56 Penman-Monteith via ERA5 Reanalysis',
      dateLabel: lastMonthClimate?.month ?? cur.observation_date,
      category: cur.trailing_12m_et0_mm !== null ? 'model_reanalysis' : 'unavailable',
      unavailable: cur.trailing_12m_et0_mm === null,
      tone: 'warning',
      icon: <Sun size={20} />
    },
    {
      id: 'drought-dust-hazard',
      titleFa: 'ریسک گردوغبار نمکی و تنش خشکی',
      titleEn: 'Salt-Dust & Drought Hazard Index',
      value: `${eco.salt_dust_hazard.index_0_100.toFixed(1)} / 100`,
      unitFa: `سطح ${eco.salt_dust_hazard.hazard_tier}`,
      unitEn: `${eco.salt_dust_hazard.hazard_tier} TIER`,
      subtextFa: `شوری تخمینی شورابه: ${eco.salinity_and_biology.estimated_salinity_g_l.toFixed(0)} گرم بر لیتر (فوق‌اشباع هالیت)`,
      subtextEn: `Brine salinity: ${eco.salinity_and_biology.estimated_salinity_g_l.toFixed(0)} g/L (Halite supersaturation)`,
      sourceFa: 'مدل ترکیبی پلایا، کسری رطوبت و آستانه شوری فاز ۴',
      sourceEn: 'Phase 4 Playa Exposure & Halite Mass-Balance Model',
      dateLabel: analytics.generated_at_utc.slice(0, 10),
      category: 'derived_index',
      tone: 'critical',
      icon: <AlertTriangle size={20} />
    },
    {
      id: 'vegetation-ndvi',
      titleFa: 'وضعیت پوشش گیاهی حوضه (NDVI)',
      titleEn: 'Basin Vegetation Status (NDVI)',
      value: unavailableText,
      subtextFa:
        'رستر ماهواره‌ای Sentinel-2 / MODIS NDVI هنوز در پایپ‌لاین مکانی بارگذاری نشده است (عدم نمایش عدد فرضی)',
      subtextEn:
        'Verified Sentinel-2 / MODIS NDVI raster time series not yet ingested (no synthetic values shown)',
      sourceFa: 'در انتظار اتصال سرویس اپتیکی Sentinel-2 L2A / MODIS',
      sourceEn: 'Pending Sentinel-2 L2A / MODIS Optical Ingestion',
      dateLabel: '—',
      category: 'unavailable',
      unavailable: true,
      tone: 'neutral',
      icon: <Sprout size={20} />
    },
    {
      id: 'latest-satellite',
      titleFa: 'آخرین بررسی کاتالوگ ماهواره‌ای',
      titleEn: 'Latest Satellite Catalog Check',
      value: stacDate,
      subtextFa: `ایستگاه CLMS: ${hydrology.identifiers.cdse_clms_station_id ?? '—'} | Hydroweb: ${hydrology.identifiers.hydroweb_id ?? '—'}`,
      subtextEn: `CLMS ID: ${hydrology.identifiers.cdse_clms_station_id ?? '—'} | Hydroweb: ${hydrology.identifiers.hydroweb_id ?? '—'}`,
      sourceFa: 'کوئری زنده کاتالوگ STAC کوپرنیکوس و Hydroweb.next',
      sourceEn: 'Live STAC Endpoint Check (Copernicus CDSE & Hydroweb)',
      dateLabel: hydrology.stac_live_catalog?.checked_at_utc?.slice(0, 16).replace('T', ' ') + ' UTC' || stacDate,
      category: 'satellite_observation',
      tone: 'normal',
      icon: <Satellite size={20} />
    },
    {
      id: 'latest-system-update',
      titleFa: 'آخرین بروزرسانی موتور علمی',
      titleEn: 'Latest Scientific Engine Update',
      value: analytics.generated_at_utc.slice(0, 10),
      unitFa: analytics.generated_at_utc.slice(11, 16) + ' UTC',
      unitEn: analytics.generated_at_utc.slice(11, 16) + ' UTC',
      subtextFa: `نسخه اسکیما هیدرولوژی: v${hydrology.schema_version} | تحلیل آماری: v${analytics.schema_version}`,
      subtextEn: `Hydrology schema: v${hydrology.schema_version} | Analytics schema: v${analytics.schema_version}`,
      sourceFa: 'پایپ‌لاین خودکار Python رصدخانه دریاچه ارومیه',
      sourceEn: 'ULO Automated Python Science Engine Pipeline',
      dateLabel: analytics.generated_at_utc.slice(0, 10),
      category: 'derived_index',
      tone: 'normal',
      icon: <Clock size={20} />
    }
  ];

  return (
    <section aria-label={isFa ? 'شاخص‌های کلیدی علمی دریاچه ارومیه' : 'Key Scientific Performance Indicators'}>
      <div className="ulo-section-head">
        <div>
          <h2>
            {isFa
              ? 'شاخص‌های کلیدی پایش هیدرولوژیک، اقلیمی و اکولوژیک (KPI)'
              : 'Hydrological, Climatic & Ecological Key Indicators (KPIs)'}
          </h2>
          <p>
            {isFa
              ? 'تمامی مقادیر مستقیماً از خروجی‌های راستی‌آزمایی‌شده موتور علمی استخراج شده‌اند؛ هر کارت دارای دسته‌بندی علمی، منبع و تاریخ برداشت است.'
              : 'Every metric is bound directly to verified science-engine outputs with explicit data category, provenance, and observation date.'}
          </p>
        </div>
      </div>

      <div className="ulo-kpi-grid">
        {items.map((item) => {
          const cat = CATEGORY_LABELS[item.category];
          return (
            <article
              key={item.id}
              className={`ulo-kpi-card ulo-tone-${item.tone ?? 'normal'} ${item.unavailable ? 'ulo-kpi-unavailable' : ''}`}
            >
              <div className="ulo-kpi-top">
                <span className="ulo-kpi-icon">{item.icon}</span>
                <span className={`ulo-cat-pill ulo-cat-${item.category}`}>
                  {isFa ? cat.fa : cat.en}
                </span>
              </div>

              <h3 className="ulo-kpi-title">{isFa ? item.titleFa : item.titleEn}</h3>

              <div className="ulo-kpi-value-row">
                <span className={item.unavailable ? 'ulo-val-unavail' : 'ulo-kpi-value'}>
                  {item.value}
                </span>
                {(isFa ? item.unitFa : item.unitEn) && (
                  <span className="ulo-kpi-unit">{isFa ? item.unitFa : item.unitEn}</span>
                )}
              </div>

              <p className="ulo-kpi-subtext">{isFa ? item.subtextFa : item.subtextEn}</p>

              <div className="ulo-kpi-meta">
                <div>
                  <strong>{isFa ? 'منبع: ' : 'Source: '}</strong>
                  <span>{isFa ? item.sourceFa : item.sourceEn}</span>
                </div>
                <div>
                  <strong>{isFa ? 'تاریخ داده: ' : 'Obs. Date: '}</strong>
                  <span dir="ltr">{item.dateLabel}</span>
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
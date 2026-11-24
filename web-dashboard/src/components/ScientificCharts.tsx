import { useMemo, useState } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine
} from 'recharts';
import type {
  Lang,
  LakeHydrologyDataset,
  LakeScientificAnalytics
} from '../types/observatory';

interface ScientificChartsProps {
  lang: Lang;
  hydrology: LakeHydrologyDataset;
  analytics: LakeScientificAnalytics;
}

type TimeRangeFilter = 'ALL' | '10Y' | '5Y';

export default function ScientificCharts({
  lang,
  hydrology,
  analytics
}: ScientificChartsProps) {
  const isFa = lang === 'fa';
  const [rangeFilter, setRangeFilter] = useState<TimeRangeFilter>('ALL');

  const ecologicalTargetM = hydrology.current_status.ecological_target_m_asl;
  const fullTrend = analytics.statistical_trends.periods.full_record;

  // Build water level + Theil-Sen regression overlay dataset
  const filteredSeries = useMemo(() => {
    const raw = hydrology.water_level_timeseries ?? [];
    if (raw.length === 0) return [];

    const firstDateMs = new Date(raw[0].date).getTime();
    const lastDateMs = new Date(raw[raw.length - 1].date).getTime();
    const msPerYear = 365.25 * 24 * 3600 * 1000;

    return raw
      .filter((pt) => {
        if (rangeFilter === 'ALL') return true;
        const ptMs = new Date(pt.date).getTime();
        const cutoffYears = rangeFilter === '10Y' ? 10 : 5;
        return ptMs >= lastDateMs - cutoffYears * msPerYear;
      })
      .map((pt) => {
        const elapsedYears = (new Date(pt.date).getTime() - firstDateMs) / msPerYear;
        const senLine = Number(
          (
            fullTrend.sens_slope_m.intercept +
            fullTrend.sens_slope_m.slope_per_year * elapsedYears
          ).toFixed(3)
        );
        return {
          ...pt,
          yearLabel: pt.date.slice(0, 7),
          ecological_target_m: ecologicalTargetM,
          sen_trend_m: senLine
        };
      });
  }, [hydrology.water_level_timeseries, rangeFilter, ecologicalTargetM, fullTrend]);

  const climateMonthly = hydrology.basin_climate_era5?.monthly_summary ?? [];
  const hypsometry = hydrology.hypsometry_curve ?? [];

  return (
    <section className="ulo-charts-section">
      <div className="ulo-section-head ulo-flex-between">
        <div>
          <h2>
            {isFa
              ? 'نمودارهای تعاملی سری‌های زمانی هیدرولوژیک و اقلیمی'
              : 'Interactive Hydrological & Climatic Time-Series Visualizations'}
          </h2>
          <p>
            {isFa
              ? 'تمامی نمودارها مجهز به ابزارک بازرسی دقیق مقادیر (Tooltip)، خط مبنای تراز اکولوژیک و کنترل بازه زمانی هستند.'
              : 'Interactive scientific plots featuring hover inspection, ecological reference datum, and temporal window controls.'}
          </p>
        </div>

        <div className="ulo-filter-group" role="group" aria-label="Time Window Filter">
          {(['ALL', '10Y', '5Y'] as TimeRangeFilter[]).map((key) => {
            const labels: Record<TimeRangeFilter, { fa: string; en: string }> = {
              ALL: { fa: 'کل دوره (۱۹۹۵–۲۰۲۶)', en: 'Full Record (1995–2026)' },
              '10Y': { fa: '۱۰ سال اخیر', en: 'Last 10 Years' },
              '5Y': { fa: '۵ سال اخیر', en: 'Last 5 Years' }
            };
            return (
              <button
                key={key}
                type="button"
                className={`ulo-filter-btn ${rangeFilter === key ? 'active' : ''}`}
                onClick={() => setRangeFilter(key)}
              >
                {isFa ? labels[key].fa : labels[key].en}
              </button>
            );
          })}
        </div>
      </div>

      <div className="ulo-charts-grid">
        {/* CHART 1: Water Surface Elevation + Ecological Target + Sen Trend */}
        <div className="ulo-card ulo-chart-card">
          <div className="ulo-chart-header">
            <h3>
              {isFa
                ? '۱. سری زمانی تراز سطح آب دریاچه ارومیه و خط روند ناپارامتریک Sen'
                : '1. Lake Water Surface Elevation Time Series & Non-Parametric Sen Trend'}
            </h3>
            <span className="ulo-chart-tag">
              {isFa ? 'واحد: متر از سطح دریاهای آزاد (m a.s.l.)' : 'Unit: meters above sea level (m a.s.l.)'}
            </span>
          </div>

          <div className="ulo-chart-box" dir="ltr">
            <ResponsiveContainer width="100%" height={310}>
              <ComposedChart data={filteredSeries} margin={{ top: 12, right: 20, left: 8, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={28} />
                <YAxis
                  domain={[1269, 1279]}
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => `${v}m`}
                />
                <Tooltip
                  contentStyle={{ borderRadius: 10, borderColor: '#CBD5E1', fontSize: 12 }}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <ReferenceLine
                  y={ecologicalTargetM}
                  stroke="#059669"
                  strokeDasharray="6 4"
                  strokeWidth={2}
                  label={{
                    value: isFa
                      ? `تراز اکولوژیک (${ecologicalTargetM}m)`
                      : `Ecological Target (${ecologicalTargetM}m)`,
                    position: 'insideTopRight',
                    fill: '#059669',
                    fontSize: 11
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="water_level_m"
                  name={isFa ? 'تراز مشاهده‌شده (m)' : 'Observed Water Level (m)'}
                  stroke="#1565C0"
                  strokeWidth={2.6}
                  dot={{ r: 2.5, fill: '#1565C0' }}
                  activeDot={{ r: 5 }}
                />
                <Line
                  type="linear"
                  dataKey="sen_trend_m"
                  name={isFa ? 'خط شیب کل دوره Sen (m)' : 'Full-Record Sen Trend (m)'}
                  stroke="#DC2626"
                  strokeDasharray="5 5"
                  strokeWidth={1.8}
                  dot={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <p className="ulo-chart-caption">
            {isFa
              ? 'منبع: ترکیب مشاهدات آلتیمتری راداری ماهواره‌ای کالیبره‌شده (۱۹۹۵ تا ۲۰۲۶). خط سبز نشان‌دهنده تراز پایداری اکولوژیک (۱۲۷۴.۱ متر) برای بقای آرتمیا و مهار ریزگرد نمکی است.'
              : 'Source: Calibrated multi-mission satellite radar altimetry series (1995–2026). Green dashed line marks the 1274.1 m ecological threshold.'}
          </p>
        </div>

        {/* CHART 2: Water Surface Area & Storage Volume Co-evolution */}
        <div className="ulo-card ulo-chart-card">
          <div className="ulo-chart-header">
            <h3>
              {isFa
                ? '۲. تغییرات هم‌زمان مساحت پهنه مرطوب (km²) و حجم ذخیره آب (km³)'
                : '2. Surface Water Area (km²) & Storage Volume (km³) Co-Evolution'}
            </h3>
            <span className="ulo-chart-tag">
              {isFa ? 'برآورد مبتنی بر منحنی هیپسومتری' : 'Derived via Bathymetric Hypsometry'}
            </span>
          </div>

          <div className="ulo-chart-box" dir="ltr">
            <ResponsiveContainer width="100%" height={310}>
              <ComposedChart data={filteredSeries} margin={{ top: 12, right: 20, left: 8, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={28} />
                <YAxis
                  yAxisId="area"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => `${v}`}
                  label={{ value: 'km²', angle: -90, position: 'insideLeft', fontSize: 11 }}
                />
                <YAxis
                  yAxisId="vol"
                  orientation="right"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => `${v} km³`}
                />
                <Tooltip contentStyle={{ borderRadius: 10, borderColor: '#CBD5E1', fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Area
                  yAxisId="area"
                  type="monotone"
                  dataKey="area_km2"
                  name={isFa ? 'مساحت پهنه آبی (km²)' : 'Wet Surface Area (km²)'}
                  fill="#00ACC1"
                  fillOpacity={0.22}
                  stroke="#00ACC1"
                  strokeWidth={2.2}
                />
                <Line
                  yAxisId="vol"
                  type="monotone"
                  dataKey="volume_km3"
                  name={isFa ? 'حجم آب مخزن (km³)' : 'Water Volume (km³)'}
                  stroke="#0B1F3A"
                  strokeWidth={2.3}
                  dot={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <p className="ulo-chart-caption">
            {isFa
              ? 'به دلیل بستر بسیار کم‌عمق نیمه جنوبی دریاچه، افت اندک تراز در سطوح پایین منجر به گسترش شدید پلایاهای نمکی در معرض باد می‌شود.'
              : 'Due to Lake Urmia’s shallow bathymetric gradient, modest elevation drops at low stages expose vast saline mudflats.'}
          </p>
        </div>

        {/* CHART 3: ERA5 Monthly Basin Precipitation, Reference ET0 & Temperature */}
        <div className="ulo-card ulo-chart-card">
          <div className="ulo-chart-header">
            <h3>
              {isFa
                ? '۳. بیلان اقلیمی ماهانه حوضه: بارش، تبخیر-تعرق مرجع (ET₀) و دمای هوا'
                : '3. Monthly Basin Hydro-Climatic Balance: Precipitation, ET₀ & Air Temperature'}
            </h3>
            <span className="ulo-chart-tag">
              {isFa ? 'بازتحلیل زنده ECMWF ERA5' : 'Live ECMWF ERA5 Reanalysis'}
            </span>
          </div>

          <div className="ulo-chart-box" dir="ltr">
            <ResponsiveContainer width="100%" height={310}>
              <ComposedChart data={climateMonthly} margin={{ top: 12, right: 20, left: 8, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} minTickGap={20} />
                <YAxis
                  yAxisId="mm"
                  tick={{ fontSize: 11 }}
                  label={{ value: 'mm', angle: -90, position: 'insideLeft', fontSize: 11 }}
                />
                <YAxis
                  yAxisId="temp"
                  orientation="right"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => `${v}°C`}
                />
                <Tooltip contentStyle={{ borderRadius: 10, borderColor: '#CBD5E1', fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar
                  yAxisId="mm"
                  dataKey="precip_mm"
                  name={isFa ? 'بارش ماهانه (mm)' : 'Monthly Precipitation (mm)'}
                  fill="#1565C0"
                  radius={[4, 4, 0, 0]}
                />
                <Line
                  yAxisId="mm"
                  type="monotone"
                  dataKey="et0_mm"
                  name={isFa ? 'تبخیر-تعرق مرجع ET₀ (mm)' : 'Reference ET₀ (mm)'}
                  stroke="#D97706"
                  strokeWidth={2.2}
                  dot={{ r: 2 }}
                />
                <Line
                  yAxisId="temp"
                  type="monotone"
                  dataKey="temp_mean_c"
                  name={isFa ? 'دمای میانگین (°C)' : 'Mean Air Temp (°C)'}
                  stroke="#DC2626"
                  strokeWidth={1.8}
                  strokeDasharray="4 3"
                  dot={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <p className="ulo-chart-caption">
            {isFa
              ? 'شکاف شدید میان تقاضای تبخیری جو (ET₀) در ماه‌های گرم سال و بارش محدود حوضه، تنش اقلیمی حاکم بر تراز آبی دریاچه را نشان می‌دهد.'
              : 'High summer atmospheric evaporative demand (ET₀) relative to winter/spring precipitation highlights severe seasonal water deficit.'}
          </p>
        </div>

        {/* CHART 4: Bathymetric Hypsometry Curve (Elevation vs Area & Volume) */}
        <div className="ulo-card ulo-chart-card">
          <div className="ulo-chart-header">
            <h3>
              {isFa
                ? '۴. منحنی فیزیکی هیپسومتری بستر دریاچه (رابطه تراز-مساحت-حجم)'
                : '4. Lake Basin Bathymetric Hypsometry Curve (Elevation–Area–Volume)'}
            </h3>
            <span className="ulo-chart-tag">
              {isFa ? 'مدل ژئومورفولوژیک کاسه دریاچه' : 'Basin Morphometric Rating Curve'}
            </span>
          </div>

          <div className="ulo-chart-box" dir="ltr">
            <ResponsiveContainer width="100%" height={310}>
              <ComposedChart data={hypsometry} margin={{ top: 12, right: 20, left: 8, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis
                  dataKey="elevation_m"
                  type="number"
                  domain={['dataMin', 'dataMax']}
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => `${v}m`}
                />
                <YAxis yAxisId="area" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="vol" orientation="right" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ borderRadius: 10, borderColor: '#CBD5E1', fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <ReferenceLine
                  yAxisId="area"
                  x={hydrology.current_status.water_level_m_asl}
                  stroke="#DC2626"
                  strokeWidth={2}
                  strokeDasharray="4 4"
                  label={{
                    value: isFa ? 'تراز فعلی' : 'Current Stage',
                    position: 'top',
                    fill: '#DC2626',
                    fontSize: 11
                  }}
                />
                <ReferenceLine
                  yAxisId="area"
                  x={ecologicalTargetM}
                  stroke="#059669"
                  strokeWidth={2}
                  strokeDasharray="6 3"
                  label={{
                    value: isFa ? 'تراز اکولوژیک' : 'Ecological Stage',
                    position: 'insideTopLeft',
                    fill: '#059669',
                    fontSize: 11
                  }}
                />
                <Area
                  yAxisId="area"
                  type="monotone"
                  dataKey="area_km2"
                  name={isFa ? 'مساحت سطح (km²)' : 'Surface Area (km²)'}
                  fill="#1565C0"
                  fillOpacity={0.18}
                  stroke="#1565C0"
                  strokeWidth={2.2}
                />
                <Line
                  yAxisId="vol"
                  type="monotone"
                  dataKey="volume_km3"
                  name={isFa ? 'حجم مخزن (km³)' : 'Storage Volume (km³)'}
                  stroke="#00ACC1"
                  strokeWidth={2.4}
                  dot={{ r: 3 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <p className="ulo-chart-caption">
            {isFa
              ? 'نشانگر قرمز جایگاه بحرانی فعلی دریاچه در قعر منحنی هیپسومتری را در مقایسه با خط سبز تراز اکولوژیک نشان می‌دهد.'
              : 'Red marker denotes the current critical stage near the lower tail of the morphometric curve vs. the 1274.1 m ecological target.'}
          </p>
        </div>
      </div>

      {/* Transparent Unavailability Notice for Pending Satellite Raster Series */}
      <div className="ulo-card ulo-unavail-strip">
        <div>
          <strong>
            {isFa
              ? 'وضعیت سری‌های زمانی رطوبت خاک (SMAP/ERA5-Soil) و تغییر کاربری اراضی (LULC): '
              : 'Soil Moisture & Land-Cover Change (LULC) Raster Series Status: '}
          </strong>
          <span>
            {isFa
              ? 'داده معتبر در دسترس نیست — مطابق اصل صداقت علمی سامانه، تا زمان بارگذاری رسترهای ماهواره‌ای راستی‌آزمایی‌شده، از ترسیم هرگونه نمودار شبیه‌سازی‌شده یا فرضی برای شاخص‌های NDVI، رطوبت خاک و تغییر کاربری اراضی خودداری شده است.'
              : 'Data Unavailable — Per strict scientific integrity rules, synthetic or placeholder charts for NDVI, Soil Moisture, and Land-Cover Change are strictly omitted until verified raster series are ingested.'}
          </span>
        </div>
      </div>
    </section>
  );
}
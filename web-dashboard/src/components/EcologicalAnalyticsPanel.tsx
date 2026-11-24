import { Download, ShieldAlert, FlaskConical, Wind, Info } from 'lucide-react';
import type {
  Lang,
  LakeHydrologyDataset,
  LakeScientificAnalytics,
  TrendPeriodResult
} from '../types/observatory';

interface EcologicalAnalyticsPanelProps {
  lang: Lang;
  hydrology: LakeHydrologyDataset;
  analytics: LakeScientificAnalytics;
}

function downloadBlob(filename: string, content: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export default function EcologicalAnalyticsPanel({
  lang,
  hydrology,
  analytics
}: EcologicalAnalyticsPanelProps) {
  const isFa = lang === 'fa';
  const periods = analytics.statistical_trends.periods;
  const eco = analytics.ecological_and_hazard_assessment;

  const periodRows: { key: string; labelFa: string; labelEn: string; data?: TrendPeriodResult }[] = [
    {
      key: 'full',
      labelFa: 'کل دوره ثبت آلتیمتری',
      labelEn: 'Full Altimetry Record',
      data: periods.full_record
    },
    {
      key: '10y',
      labelFa: 'پنجره ۱۰ سال اخیر',
      labelEn: 'Trailing 10-Year Window',
      data: periods.last_10_years
    },
    {
      key: '5y',
      labelFa: 'پنجره ۵ سال اخیر',
      labelEn: 'Trailing 5-Year Window',
      data: periods.last_5_years
    }
  ];

  const handleExportCsv = () => {
    const headers = ['date,water_level_m,area_km2,volume_km3,source'];
    const rows = hydrology.water_level_timeseries.map(
      (r) => `${r.date},${r.water_level_m},${r.area_km2},${r.volume_km3},"${r.source}"`
    );
    downloadBlob(
      `urmia_lake_timeseries_${hydrology.current_status.observation_date}.csv`,
      '\uFEFF' + headers.concat(rows).join('\n'),
      'text/csv;charset=utf-8;'
    );
  };

  const handleExportJson = () => {
    const bundle = {
      exported_at_utc: new Date().toISOString(),
      hydrology,
      scientific_analytics: analytics
    };
    downloadBlob(
      `urmia_observatory_scientific_bundle_${hydrology.current_status.observation_date}.json`,
      JSON.stringify(bundle, null, 2),
      'application/json;charset=utf-8;'
    );
  };

  return (
    <section className="ulo-analytics-section">
      <div className="ulo-section-head ulo-flex-between">
        <div>
          <h2>
            {isFa
              ? 'نتایج آزمون‌های آماری روند، بیولوژی آرتمیا و مخاطرات گردوغبار نمکی'
              : 'Statistical Trend Diagnostics, Brine Ecology & Salt-Dust Hazard Assessment'}
          </h2>
          <p>
            {isFa
              ? 'خروجی مستقیم پایپ‌لاین تحلیلی فاز ۴ با ذکر دقیق سطح معناداری، فرضیات مدل و محدودیت‌های علمی.'
              : 'Direct Phase 4 analytical diagnostics reporting non-parametric trend significance, salinity saturation, and model limitations.'}
          </p>
        </div>

        <div className="ulo-export-bar">
          <button type="button" className="ulo-export-btn" onClick={handleExportCsv}>
            <Download size={16} />
            <span>{isFa ? 'خروجی CSV سری زمانی' : 'Export Time Series (CSV)'}</span>
          </button>
          <button type="button" className="ulo-export-btn secondary" onClick={handleExportJson}>
            <Download size={16} />
            <span>{isFa ? 'خروجی بسته علمی JSON' : 'Export Full Analytics (JSON)'}</span>
          </button>
        </div>
      </div>

      {/* Mann-Kendall & Theil-Sen Table */}
      <div className="ulo-card" style={{ marginBottom: '1.25rem' }}>
        <h3 style={{ marginBottom: '0.75rem' }}>
          {isFa
            ? 'جدول آزمون ناپارامتریک Mann-Kendall (با تصحیح گره‌ها) و شیب خطی Theil-Sen'
            : 'Non-Parametric Mann-Kendall Trend Test (Tie-Corrected) & Theil-Sen Slope'}
        </h3>
        <div className="ulo-table-wrap">
          <table className="ulo-table">
            <thead>
              <tr>
                <th>{isFa ? 'بازه زمانی تحلیل' : 'Analysis Window'}</th>
                <th>{isFa ? 'محدوده تاریخ' : 'Date Span'}</th>
                <th>{isFa ? 'تعداد (n)' : 'Samples (n)'}</th>
                <th>Mann-Kendall Z</th>
                <th>p-value</th>
                <th>Kendall τ</th>
                <th>{isFa ? 'شیب سالانه Sen' : 'Sen Slope / yr'}</th>
                <th>{isFa ? 'شیب دهه‌ای' : 'Slope / Decade'}</th>
                <th>{isFa ? 'وضعیت آماری (α=0.05)' : 'Significance (α=0.05)'}</th>
              </tr>
            </thead>
            <tbody>
              {periodRows.map(({ key, labelFa, labelEn, data }) => {
                if (!data) return null;
                const mk = data.mann_kendall;
                const sen = data.sens_slope_m;
                return (
                  <tr key={key}>
                    <td><strong>{isFa ? labelFa : labelEn}</strong></td>
                    <td dir="ltr">{data.start_date} → {data.end_date}</td>
                    <td dir="ltr">{mk.n}</td>
                    <td dir="ltr">{mk.z_score.toFixed(3)}</td>
                    <td dir="ltr">{mk.p_value < 0.0001 ? '< 0.0001' : mk.p_value.toFixed(5)}</td>
                    <td dir="ltr">{mk.kendall_tau.toFixed(3)}</td>
                    <td dir="ltr" className="ulo-neg-cell">{sen.slope_per_year.toFixed(4)} m/yr</td>
                    <td dir="ltr" className="ulo-neg-cell">{sen.slope_per_decade.toFixed(3)} m/dec</td>
                    <td>
                      <span className={mk.significant ? 'ulo-sig-badge' : 'ulo-nonsig-badge'}>
                        {mk.significant
                          ? isFa
                            ? 'روند نزولی معنادار'
                            : 'Significant Decreasing'
                          : isFa
                          ? 'بدون روند معنادار'
                          : 'Not Significant'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3-Column Ecological & Hazard Diagnostics */}
      <div className="ulo-eco-grid">
        <div className="ulo-card ulo-eco-box">
          <div className="ulo-eco-head">
            <FlaskConical size={20} color="#1565C0" />
            <h3>{isFa ? 'شوری شورابه و بوم‌شناسی آرتمیا اورمیانا' : 'Brine Salinity & Artemia urmiana Ecology'}</h3>
          </div>
          <ul className="ulo-eco-list">
            <li>
              <span>{isFa ? 'شوری تخمینی فعلی:' : 'Estimated Brine Salinity:'}</span>
              <strong dir="ltr">{eco.salinity_and_biology.estimated_salinity_g_l.toFixed(1)} g/L</strong>
            </li>
            <li>
              <span>{isFa ? 'آستانه تحمل زیستی آرتمیا:' : 'Artemia Viability Threshold:'}</span>
              <strong dir="ltr">{eco.salinity_and_biology.artemia_threshold_g_l.toFixed(1)} g/L</strong>
            </li>
            <li>
              <span>{isFa ? 'اشباع کانی هالیت (NaCl):' : 'Halite Supersaturation:'}</span>
              <strong>
                {eco.salinity_and_biology.halite_supersaturated
                  ? isFa ? 'بله (> ۳۴۰ گرم بر لیتر — رسوب بلور نمک در بستر)' : 'Yes (> 340 g/L — Active salt crust precipitation)'
                  : isFa ? 'خیر' : 'No'}
              </strong>
            </li>
            <li>
              <span>{isFa ? 'وضعیت زیستی زنجیره غذایی:' : 'Trophic Viability Status:'}</span>
              <strong className="ulo-text-critical">
                {isFa
                  ? 'فروپاشی فعال زیستی در اثر فوق‌اشباع نمکی'
                  : 'Collapsed Trophic State (Hypersaline Saturation)'}
              </strong>
            </li>
          </ul>
        </div>

        <div className="ulo-card ulo-eco-box">
          <div className="ulo-eco-head">
            <Wind size={20} color="#DC2626" />
            <h3>{isFa ? 'پهنه نمکزار خشک‌شده و کانون‌های ریزگرد نمکی' : 'Exposed Salt Playa & Dust Emission Hotspots'}</h3>
          </div>
          <ul className="ulo-eco-list">
            <li>
              <span>{isFa ? 'شاخص ترکیبی خطر گردوغبار نمکی:' : 'Composite Salt-Dust Hazard Index:'}</span>
              <strong className="ulo-text-critical" dir="ltr">
                {eco.salt_dust_hazard.index_0_100.toFixed(1)} / 100 ({eco.salt_dust_hazard.hazard_tier})
              </strong>
            </li>
            <li>
              <span>{isFa ? 'وسعت بستر خشک‌شده (نسبت به تراز اکولوژیک):' : 'Exposed Playa vs. Ecological Extent:'}</span>
              <strong dir="ltr">{eco.exposed_lakebed_playa.exposed_salt_playa_vs_ecological_km2.toFixed(1)} km²</strong>
            </li>
            <li>
              <span>{isFa ? 'درصد خشکیدگی پهنه اکولوژیک:' : 'Ecological Area Desiccation Ratio:'}</span>
              <strong dir="ltr">{eco.exposed_lakebed_playa.desiccation_ratio_vs_ecological_pct.toFixed(1)}%</strong>
            </li>
          </ul>
          <div className="ulo-hotspots">
            <strong>{isFa ? 'کانون‌های بحرانی فرسایش بادی:' : 'Primary Erodible Hotspot Zones:'}</strong>
            <div className="ulo-hotspot-tags">
              {eco.salt_dust_hazard.primary_hotspot_zones.map((z) => (
                <span key={z} className="ulo-hotspot-chip" dir="ltr">{z}</span>
              ))}
            </div>
          </div>
        </div>

        <div className="ulo-card ulo-eco-box ulo-uncertainty-box">
          <div className="ulo-eco-head">
            <ShieldAlert size={20} color="#0B1F3A" />
            <h3>{isFa ? 'عدم‌قطعیت، روش‌شناسی و محدودیت‌های علمی' : 'Scientific Uncertainty, Methodology & Caveats'}</h3>
          </div>
          <p className="ulo-caveat-text">
            {isFa
              ? '۱. همبستگی آماری میان متغیرهای اقلیمی و افت تراز دریاچه به‌تنهایی به‌معنای رابطه علت‌ومعلولی تک‌عاملی نیست؛ تفکیک سهم عوامل انسانی (سدسازی و برداشت کشاورزی) نیازمند مدل بیلان آب توزیعی کالیبره‌شده با دبی ایستگاه‌های هیدرومتری است.'
              : '1. Statistical correlation between climatic stress and water-level decline does not imply single-factor causality; separating anthropogenic withdrawals requires calibrated gauge inflow series.'}
          </p>
          <p className="ulo-caveat-text">
            {isFa
              ? '۲. برآورد مساحت، حجم و شوری مبتنی بر منحنی هیپسومتری مرجع و موازنه جرم نمک بوده و به دلیل رسوب‌گذاری پوسته نمکی در کف دریاچه دارای عدم‌قطعیت برآوردی حدود ±۱۰ تا ±۱۵ درصد است.'
              : '2. Surface area, volume, and brine salinity are indirect morphometric/mass-balance estimates carrying ±10–15% uncertainty due to active halite crust aggradation on the lakebed.'}
          </p>
          <div className="ulo-provenance-foot">
            <Info size={15} />
            <span>
              {isFa
                ? `حالت داده تراز آب: ${hydrology.data_provenance.water_level_mode} | اقلیم ERA5 زنده: ${hydrology.data_provenance.climate_era5_live ? 'فعال' : 'کش'}`
                : `Water-level provenance: ${hydrology.data_provenance.water_level_mode} | Live ERA5: ${hydrology.data_provenance.climate_era5_live ? 'Active' : 'Cached'}`}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
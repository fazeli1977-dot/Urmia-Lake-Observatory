import { useEffect, useState } from 'react';
import UrmiaMap from './components/UrmiaMap';
import type { MapLang } from './components/UrmiaMap';
import UloLogo from './components/UloLogo';
import KpiGrid from './components/KpiGrid';
import ScientificCharts from './components/ScientificCharts';
import EcologicalAnalyticsPanel from './components/EcologicalAnalyticsPanel';
import { ScientificResearchCenter } from './components/ScientificResearchCenter';
import { DataManagementReports } from './components/DataManagementReports';


import type {
  LakeHydrologyDataset,
  LakeScientificAnalytics
} from './types/observatory';

type ViewSection = 'overview' | 'map' | 'charts' | 'analytics';

export default function App() {
  const [lang, setLang] = useState<MapLang>('fa');
  const [activeView, setActiveView] = useState<ViewSection>('overview');
  const [hydrology, setHydrology] = useState<LakeHydrologyDataset | null>(null);
  const [analytics, setAnalytics] = useState<LakeScientificAnalytics | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'fa' ? 'rtl' : 'ltr';
  }, [lang]);

  useEffect(() => {
    let cancelled = false;
    async function loadVerifiedDatasets() {
      try {
        setLoading(true);
        const [hydroRes, anaRes] = await Promise.all([
          fetch('/data/lake_hydrology_latest.json'),
          fetch('/data/lake_scientific_analytics_latest.json')
        ]);
        if (!hydroRes.ok || !anaRes.ok) {
          throw new Error(`HTTP ${hydroRes.status} / ${anaRes.status}`);
        }
        const [hydroJson, anaJson] = await Promise.all([
          hydroRes.json() as Promise<LakeHydrologyDataset>,
          anaRes.json() as Promise<LakeScientificAnalytics>
        ]);
        if (!cancelled) {
          setHydrology(hydroJson);
          setAnalytics(anaJson);
          setLoadError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setLoadError(err instanceof Error ? err.message : 'Unknown fetch error');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    loadVerifiedDatasets();
    return () => {
      cancelled = true;
    };
  }, []);

  const isFa = lang === 'fa';

  const navItems: { id: ViewSection; fa: string; en: string }[] = [
    { id: 'overview', fa: 'نمای جامع رصدخانه', en: 'Full Observatory View' },
    { id: 'map', fa: 'نقشه تعاملی حوضه و دریاچه', en: 'Interactive Basin Map' },
    { id: 'charts', fa: 'نمودارهای سری زمانی و هیپسومتری', en: 'Time-Series & Hypsometry Charts' },
    { id: 'analytics', fa: 'آمار روند و مخاطرات اکولوژیک', en: 'Trend Statistics & Ecological Risk' }
  ];

  return (
    <div className="ulo-shell">
      <header className="ulo-header">
        <div className="ulo-brand">
          <UloLogo size={56} />
          <div>
            <h1>
              {isFa
                ? 'رصدخانه هوشمند و علمی دریاچه ارومیه'
                : 'Urmia Lake Scientific Observatory (ULO)'}
            </h1>
            <p>
              {isFa
                ? 'پلتفرم جامع سنجش از دور، هیدرولوژی، اقلیم‌شناسی و پایش اکولوژیک حوضه آبریز دریاچه ارومیه'
                : 'Open Remote Sensing, Hydrological, Climatic & Ecological Intelligence Platform for Lake Urmia Basin'}
            </p>
          </div>
        </div>

        <div className="ulo-header-actions">
          {hydrology && (
            <span className="ulo-status-pill" dir="ltr">
              {isFa ? 'آخرین مشاهده: ' : 'Latest Obs: '}
              {hydrology.current_status.observation_date}
            </span>
          )}
          <button
            type="button"
            className="ulo-lang-btn"
            onClick={() => setLang(isFa ? 'en' : 'fa')}
          >
            {isFa ? 'English (LTR)' : 'فارسی (RTL)'}
          </button>
        </div>
      </header>

      {/* Instant Section Filter Bar (Zero Reload) */}
      <nav className="ulo-nav-tabs" aria-label={isFa ? 'بخش‌های داشبورد' : 'Dashboard Views'}>
        {navItems.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`ulo-nav-tab ${activeView === tab.id ? 'active' : ''}`}
            onClick={() => setActiveView(tab.id)}
          >
            {isFa ? tab.fa : tab.en}
          </button>
        ))}
      </nav>

      {loading && (
        <div className="ulo-card">
          <p>
            {isFa
              ? 'در حال بارگذاری داده‌های علمی راستی‌آزمایی‌شده دریاچه ارومیه...'
              : 'Loading verified scientific datasets for Lake Urmia...'}
          </p>
        </div>
      )}

      {!loading && loadError && (
        <div className="ulo-card">
          <span className="ulo-badge-unavailable">
            {isFa
              ? `داده معتبر در دسترس نیست (${loadError})`
              : `Data Unavailable (${loadError})`}
          </span>
        </div>
      )}

      {!loading && hydrology && analytics && (
        <>
          {activeView === 'overview' && (
            <KpiGrid lang={lang} hydrology={hydrology} analytics={analytics} />
          )}

          {(activeView === 'overview' || activeView === 'map') && (
            <section className="ulo-map-section">
              <div className="ulo-section-head">
                <h2>
                  {isFa
                    ? 'نقشه تعاملی چندلایه حوضه آبریز، زیرحوضه‌ها و پهنه مرجع دریاچه ارومیه'
                    : 'Interactive Multi-Layer Spatial Map of Lake Urmia Basin & Sub-Basins'}
                </h2>
                <p>
                  {isFa
                    ? 'شامل ۱۳ لایه مکانی علمی (پهنه آبی فعلی، کانون‌های گردوغبار نمکی، خطوط ساحلی چندزمانه ۱۹۹۵ تا ۲۰۲۶، منحنی‌های هیپسومتری بستر، سدها و مخازن، تالاب‌های اقماری، رودخانه‌ها، زیرحوضه‌ها و ایستگاه‌های پایش) با کنترل شفافیت و شناسنامه تعاملی.'
                    : 'Includes 13 interactive GeoJSON layers (active brine water, desiccated salt-dust zones, 1995–2026 shorelines, bathymetric contours, dams & reservoirs, satellite wetlands, tributary rivers, sub-basins & monitoring stations) with opacity control.'}
                </p>
              </div>
              <UrmiaMap lang={lang} />
            </section>
          )}

          {(activeView === 'overview' || activeView === 'charts') && (
            <ScientificCharts lang={lang} hydrology={hydrology} analytics={analytics} />
          )}

          {(activeView === 'overview' || activeView === 'analytics') && (
            <EcologicalAnalyticsPanel lang={lang} hydrology={hydrology} analytics={analytics} />
          )}
        </>
      )}

      
      <ScientificResearchCenter lang={lang} />
      <DataManagementReports lang={lang} />

      <footer className="ulo-footer">
        <div>
          <strong>{isFa ? 'طراح و توسعه‌دهنده: ' : 'Architect & Developer: '}</strong>
          {isFa
            ? 'علیرضا فاضلی ثانی (alirezafazeli@live.com)'
            : 'Alireza Fazeli Sani (alirezafazeli@live.com)'}
        </div>
        <div>
          {isFa
            ? 'سلب مسئولیت علمی و حقوقی: این سامانه یک پلتفرم پژوهشی مستقل و متن‌باز است و هیچ‌گونه وابستگی سازمانی رسمی به NASA، ESA، USGS، UNESCO یا نهادهای دولتی ندارد. هیچ داده فرضی یا ساختگی در این داشبورد نمایش داده نمی‌شود.'
            : 'Disclaimer: Independent open-science research platform with no official institutional affiliation to NASA, ESA, USGS, UNESCO, or government agencies. Zero mock or fabricated data.'}
        </div>
      </footer>
    </div>
  );
}
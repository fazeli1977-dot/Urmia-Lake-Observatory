import { useEffect, useState } from 'react';
import UrmiaMap from './components/UrmiaMap';
import type { MapLang } from './components/UrmiaMap';

export default function App() {
  const [lang, setLang] = useState<MapLang>('fa');

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'fa' ? 'rtl' : 'ltr';
  }, [lang]);

  const isFa = lang === 'fa';

  return (
    <div className="ulo-shell">
      <header className="ulo-header">
        <div>
          <h1>
            {isFa
              ? 'رصدخانه هوشمند و علمی دریاچه ارومیه'
              : 'Urmia Lake Scientific Observatory (ULO)'}
          </h1>
          <p>
            {isFa
              ? 'زیرساخت پایش سنجش از دور، هیدرولوژی، اقلیم و اکولوژی حوضه آبریز دریاچه ارومیه'
              : 'Remote Sensing, Hydrology, Climate & Ecological Intelligence for Lake Urmia Basin'}
          </p>
        </div>
        <button
          type="button"
          className="ulo-lang-btn"
          onClick={() => setLang(isFa ? 'en' : 'fa')}
        >
          {isFa ? 'English (LTR)' : 'فارسی (RTL)'}
        </button>
      </header>

      <section className="ulo-map-section">
        <UrmiaMap lang={lang} />
      </section>

      <main className="ulo-card">
        <h2>
          {isFa
            ? 'وضعیت زیرساخت سامانه (گام ۲.۲ - نقشه تعاملی چندلایه)'
            : 'System Infrastructure Status (Step 2.2 - Interactive Multi-layer Map)'}
        </h2>
        <p style={{ marginTop: '0.75rem', marginBottom: '1rem' }}>
          {isFa
            ? 'پنج لایه علمی GeoJSON شامل مرز حوضه آبریز، زیرحوضه‌ها، پهنه مرجع اکولوژیک دریاچه، رودخانه‌های اصلی و نقاط شاخص پایش بر روی نقشه پایه ماهواره‌ای سوار شده‌اند. مطابق اصل صداقت علمی، هیچ داده نمایشی یا ساختگی در جدول‌ها و شاخص‌ها نمایش داده نمی‌شود.'
            : 'Five scientific GeoJSON layers (basin boundary, sub-basins, ecological lake reference extent, major rivers, monitoring landmarks) are mounted on a satellite basemap. Per strict scientific integrity rules, no mock or fabricated values are displayed.'}
        </p>
        <span className="ulo-badge-unavailable">
          {isFa
            ? 'وضعیت داده فعلی: لایه‌های مرجع مکانی فعال — سری‌های زمانی در انتظار دریافت داده معتبر'
            : 'Current Data Status: Reference spatial layers active — time series awaiting verified ingestion'}
        </span>
      </main>

      <footer className="ulo-footer">
        <div>
          <strong>{isFa ? 'طراح و توسعه‌دهنده: ' : 'Architect & Developer: '}</strong>
          {isFa
            ? 'علیرضا فاضلی ثانی (alirezafazeli@live.com)'
            : 'Alireza Fazeli Sani (alirezafazeli@live.com)'}
        </div>
        <div>
          {isFa
            ? 'سلب مسئولیت: این سامانه یک پروژه پژوهشی مستقل است و وابستگی سازمانی رسمی به NASA، ESA، USGS، UNESCO یا نهادهای دولتی ندارد.'
            : 'Disclaimer: Independent scientific platform with no official institutional affiliation to NASA, ESA, USGS, UNESCO, or government agencies.'}
        </div>
      </footer>
    </div>
  );
}
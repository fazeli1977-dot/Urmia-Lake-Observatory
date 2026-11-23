import { useEffect, useState } from 'react';

type Lang = 'fa' | 'en';

export default function App() {
  const [lang, setLang] = useState<Lang>('fa');

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
              ? 'زیرساخت پایش سنجش‌ازدور، هیدرولوژی، اقلیم و اکولوژی حوضه آبریز دریاچه ارومیه'
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

      <main className="ulo-card">
        <h2>
          {isFa
            ? 'وضعیت زیرساخت سامانه (فاز ۱ تکمیل شد)'
            : 'System Infrastructure Status (Phase 1 Initialized)'}
        </h2>
        <p style={{ marginTop: '0.75rem', marginBottom: '1rem' }}>
          {isFa
            ? 'اسکلت علمی پایتون و رابط کاربری دوزبانه آماده است. مطابق اصل صداقت علمی سامانه، پیش از اتصال به داده‌های واقعی ماهواره‌ای و اقلیمی در فازهای ۲ و ۳، هیچ داده نمایشی یا ساختگی نمایش داده نمی‌شود.'
            : 'The Python scientific engine and bilingual UI shell are operational. Per strict scientific integrity rules, no mock or fabricated values are displayed prior to live satellite and climate ingestion in Phases 2 & 3.'}
        </p>
        <span className="ulo-badge-unavailable">
          {isFa
            ? 'وضعیت داده فعلی: در انتظار دریافت داده معتبر واقعی (Data Unavailable)'
            : 'Current Data Status: Data Unavailable (Awaiting Phase 2–3 Ingestion)'}
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
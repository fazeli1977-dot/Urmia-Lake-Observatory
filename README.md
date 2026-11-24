# URMIA LAKE OBSERVATORY (ULO)
## رصدخانه هوشمند، علمی و داده‌محور دریاچه ارومیه

[![Cloudflare Pages](https://img.shields.io/badge/Live_Dashboard-Cloudflare_Pages-F38020?style=for-the-badge&logo=cloudflare&logoColor=white)](https://urmia-lake-observatory.pages.dev/)
[![GitHub Pages](https://img.shields.io/badge/Live_Mirror-GitHub_Pages-222222?style=for-the-badge&logo=github&logoColor=white)](https://fazeli1977-dot.github.io/Urmia-Lake-Observatory/)
[![Tests](https://img.shields.io/badge/QA_Suite-17%2F17_Passed-10B981?style=for-the-badge)](#quality-assurance)
[![License: MIT](https://img.shields.io/badge/License-MIT-0284C7?style=for-the-badge)](LICENSE)

---

### لینک‌های دسترسی عمومی و رایگان (Live Public Access — 100% Free)
- **نشانی اصلی (Cloudflare Pages Global CDN):** https://urmia-lake-observatory.pages.dev/
- **نشانی آینه دوم (GitHub Pages):** https://fazeli1977-dot.github.io/Urmia-Lake-Observatory/
- **مخزن متن‌باز (GitHub Repository):** https://github.com/fazeli1977-dot/Urmia-Lake-Observatory

---

### معرفی علمی پروژه / Scientific Overview
**رصدخانه هوشمند و علمی دریاچه ارومیه (ULO)** یک سامانه پژوهشی، مستقل، دوزبانه (**فارسی RTL با فونت محلی Vazirmatn** و **انگلیسی LTR با فونت محلی Inter**) و کاملاً رایگان برای پایش چندرشته‌ای دریاچه ارومیه و کل حوضه آبریز بسته ۵۱٬۸۷۶ کیلومترمربعی آن است.

تمامی داده‌های عملیاتی سامانه از منابع آزاد و علمی بین‌المللی استخراج شده و مطابق اصل **ممنوعیت مطلق داده ساختگی (Zero Fabrication Policy)** در ۶ سطح علمی طبقه‌بندی می‌شوند:
1. **Ground Observations** (GBIF، سایت بین‌المللی رامسر شماره ۳۸، ذخیره‌گاه زیست‌کره یونسکو)
2. **Satellite Observations** (آلتیمتری راداری Hydroweb/CLMS، کاتالوگ زنده Copernicus Sentinel-2 STAC)
3. **Model-Based Data** (بازتحلیل اقلیمی ECMWF ERA5)
4. **Derived Indicators** (آزمون ناپارامتریک Mann-Kendall، شیب Theil-Sen، Z-Score، نسبت خشکی P/ET0)
5. **Indirect Estimates** (مساحت، حجم مخزن و شوری بر پایه منحنی هیپسومتری با اعلام صریح عدم قطعیت ±۱۲–۱۵٪)
6. **User-Provided Data** (اعتبارسنجی ۱۰۰٪ محلی در مرورگر بدون ارسال فایل به سرور خارجی)

---

### قابلیت‌ها و ماژول‌های پیاده‌سازی‌شده (Phases 0–10 Complete)
- **هیدرولوژی و تراز آب (۱۹۹۵–۲۰۲۶):** سری زمانی ۴۳ مشاهده کالیبره‌شده آلتیمتری ماهواره‌ای، کسری نسبت به تراز اکولوژیک (`1274.1 m a.s.l.`) و منحنی فیزیکی هیپسومتری.
- **اقلیم‌شناسی حوضه (ECMWF ERA5):** بارش ماهانه، دما، تبخیر-تعرق مرجع (`ET0`) و همبستگی اقلیمی.
- **سامانه اطلاعات مکانی تعاملی (13-Layer MapLibre GL WebGIS):** مرز حوضه، زیرحوضه‌ها، رودخانه‌ها، سدها و مخازن، تالاب‌های اقماری، خطوط ساحلی چندزمانه (۱۹۹۵–۲۰۲۶)، پلایاهای نمکی خشک‌شده، خطوط همتراز باتیمتری و لایه زنده Sentinel-2.
- **تحلیل آماری و سامانه تصمیم‌یار (DSS):** مقایسه دوره‌های تاریخی، مقایسه ماه مشابه سال‌های مختلف (حذف اثر فصلی)، تشخیص ناهنجاری و نقطه تغییر رژیم (`Change-Point`)، تفکیک مشاهدات قطعی از فرضیه‌ها (`Hypothesis`)، خلأهای اطلاعاتی و پیشنهادهای مدیریتی.
- **اکولوژی، تنوع زیستی، رامسر و یونسکو:** بیش از ۲۷٬۰۰۰ رکورد ثبت‌شده حوضه در **GBIF**، شناسنامه **سایت رامسر #38 (1975 — Montreux Record)**، **ذخیره‌گاه زیست‌کره یونسکو (1976)** و پایش گونه‌های شاخص (*Artemia urmiana*، فلامینگوی بزرگ، پلیکان سفید، هالوفیت‌ها).
- **کتابخانه علمی و مرکز پژوهش:** مقالات، کتاب‌ها و گزارش‌های داوری‌شده با شناسه معتبر `DOI` از **OpenAlex** و **Crossref** همراه با جست‌وجوی زنده آنلاین.
- **مدیریت ورودی/خروجی و گزارش تخصصی PDF:** اعتبارسنجی امنیتی ۸ فرمت علمی (`CSV`, `XLSX`, `JSON`, `GeoJSON`, `Shapefile ZIP`, `GeoTIFF`, `NetCDF`, `PDF`) با محافظ Path Traversal و Magic Bytes، خروجی استاندارد `CSV`، اکسل چندبرگی `XLSX`، `JSON`، `GeoJSON`، تصویر `PNG` و گزارش چاپی دوزبانه **PDF (فارسی RTL و انگلیسی LTR)**.
- **به‌روزرسانی خودکار و انتشار رایگان:** پایپ‌لاین زمان‌بندی‌شده GitHub Actions با محافظ بازگشت خودکار (Rollback) و آرشیو تاریخی داده‌ها.

---

### Quality Assurance & Architecture
- `web-dashboard/` — React 18, TypeScript, Vite 6, ECharts, MapLibre GL (کاملاً مجزا از کدهای پردازش علمی)
- `science-engine/` — Python 3.12, Pandas, NumPy, Shapely, PyProj, SciPy و **۱۷ تست خودکار تضمین کیفیت (`17/17 PASSED`)**
- `scripts/` — اسکریپت‌های دریافت داده، همگام‌سازی WebGIS و پایپ‌لاین خودکار (`scripts/run_automated_data_update.py`)
- `.github/workflows/` — انتشار خودکار رایگان (`deploy-pages.yml`) و به‌روزرسانی دوره‌ای داده‌ها (`data-update-pipeline.yml`)
- مستندات فنی و علمی: [DEPLOYMENT.md](DEPLOYMENT.md) | [PROJECT_STATUS.md](PROJECT_STATUS.md) | [QA_REPORT.md](QA_REPORT.md) | [ARCHITECTURE.md](ARCHITECTURE.md) | [DATA_SOURCES.md](DATA_SOURCES.md) | [METHODS.md](METHODS.md) | [SCIENTIFIC_LIMITATIONS.md](SCIENTIFIC_LIMITATIONS.md) | [REFERENCES.md](REFERENCES.md)

---

### توسعه‌دهنده و طراح / Developer & Creator
- **توسعه‌دهنده و طراح:** علیرضا فاضلی ثانی
- **Developer & Creator:** Alireza Fazeli Sani
- **Email:** alirezafazeli@live.com

> **سلب مسئولیت علمی و حقوقی / Institutional Disclaimer:**
> رصدخانه هوشمند و علمی دریاچه ارومیه یک سامانه پژوهشی مستقل و متن‌باز است و هیچ‌گونه وابستگی، نمایندگی یا تأیید رسمی از سازمان‌های NASA، ESA، USGS، UNESCO یا دبیرخانه کنوانسیون رامسر ندارد.
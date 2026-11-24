import React, { useEffect, useRef, useState } from 'react';
import './DataManagementReports.css';
import {
  FileValidationReport,
  ObservatoryExportBundle,
  exportObservatoryCSV,
  exportObservatoryGeoJSON,
  exportObservatoryJSON,
  exportObservatoryXLSX,
  exportScientificSummaryPNG,
  openBilingualPdfReport,
  validateUploadedFile,
} from '../utils/dataValidationAndExport';

export interface DataManagementReportsProps {
  lang?: 'fa' | 'en' | string;
}

export const DataManagementReports: React.FC<DataManagementReportsProps> = ({ lang: propLang }) => {
  const [detectedLang, setDetectedLang] = useState<'fa' | 'en'>('fa');
  const [activeTab, setActiveTab] = useState<'all' | 'import' | 'export' | 'about'>('all');
  const [bundle, setBundle] = useState<ObservatoryExportBundle>({
    hydrology: null,
    climate: null,
    analytics: null,
    researchCenter: null,
    exportCatalog: null,
  });

  const [validationReports, setValidationReports] = useState<FileValidationReport[]>([]);
  const [validating, setValidating] = useState<boolean>(false);
  const [exportNotice, setExportNotice] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (propLang === 'en' || propLang === 'fa') {
      setDetectedLang(propLang);
      return;
    }
    const syncLang = () => {
      const dir = document.documentElement.getAttribute('dir') || document.querySelector('[dir]')?.getAttribute('dir');
      if (dir === 'ltr') {
        setDetectedLang('en');
        return;
      }
      if (dir === 'rtl') {
        setDetectedLang('fa');
        return;
      }
      const buttons = Array.from(document.querySelectorAll('button'));
      for (const b of buttons) {
        const t = (b.textContent || '').trim();
        if (t.includes('فارسی') || t.includes('Persian')) {
          setDetectedLang('en');
          return;
        }
        if (t.includes('English')) {
          setDetectedLang('fa');
          return;
        }
      }
    };
    syncLang();
    const obs = new MutationObserver(syncLang);
    obs.observe(document.documentElement, { attributes: true, subtree: true, childList: true });
    window.addEventListener('click', syncLang);
    return () => {
      obs.disconnect();
      window.removeEventListener('click', syncLang);
    };
  }, [propLang]);

  const isFa = propLang ? propLang !== 'en' : detectedLang === 'fa';

  useEffect(() => {
    const base = import.meta.env.BASE_URL;
    const safeJson = (p: string) =>
      fetch(`${base}${p}`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null);

    Promise.all([
      safeJson('data/lake_hydrology_latest.json'),
      safeJson('data/era5_climate_latest.json'),
      safeJson('data/lake_scientific_analytics_latest.json'),
      safeJson('data/scientific_research_center_latest.json'),
      safeJson('data/export_catalog_latest.json'),
    ]).then(([hydrology, climate, analytics, researchCenter, exportCatalog]) => {
      setBundle({ hydrology, climate, analytics, researchCenter, exportCatalog });
    });
  }, []);

  const handleFiles = async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    setValidating(true);
    try {
      const results: FileValidationReport[] = [];
      for (let i = 0; i < Math.min(fileList.length, 5); i++) {
        const rep = await validateUploadedFile(fileList[i]);
        results.push(rep);
      }
      setValidationReports((prev) => [...results, ...prev].slice(0, 8));
    } finally {
      setValidating(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleGeoJsonExport = async () => {
    setExportNotice(isFa ? 'در حال تجمیع لایه‌های مکانی واقعی GeoJSON...' : 'Compiling real GeoJSON layers...');
    const summary = await exportObservatoryGeoJSON(bundle);
    setExportNotice(
      isFa
        ? `فایل GeoJSON استاندارد با موفقیت دانلود شد (${summary}).`
        : `Standard GeoJSON FeatureCollection exported (${summary}).`
    );
  };

  const handlePdfExport = (targetLang: 'fa' | 'en') => {
    const opened = openBilingualPdfReport(bundle, targetLang);
    setExportNotice(
      opened
        ? isFa
          ? `پیش‌نمایش گزارش تخصصی A4 (${targetLang === 'fa' ? 'فارسی RTL' : 'English LTR'}) باز شد؛ برای ذخیره نهایی روی «ذخیره / چاپ PDF» کلیک کنید.`
          : `Official A4 report (${targetLang === 'fa' ? 'Persian RTL' : 'English LTR'}) opened; select Save as PDF.`
        : isFa
        ? 'پنجره بازشو توسط مرورگر مسدود شد؛ نسخه آماده چاپ HTML دانلود گردید (آن را در مرورگر باز و Print → Save as PDF بزنید).'
        : 'Popup blocked by browser; downloaded print-ready HTML report (open and Print → Save as PDF).'
    );
  };

  const geotiffCount = Number(bundle.exportCatalog?.geotiff_rasters_count || 0);
  const geojsonCount = Number(bundle.exportCatalog?.geojson_layers_count || 0);

  return (
    <section className="ulo-phase8-wrapper" dir={isFa ? 'rtl' : 'ltr'} id="data-management-reports">
      {/* Banner */}
      <div className="ulo-p8-banner">
        <div>
          <h2>
            {isFa
              ? 'مدیریت ورود و خروج داده‌ها، تولید گزارش تخصصی PDF و شناسنامه علمی سامانه'
              : 'Data Ingestion & Security Audit, Multi-Format Scientific Export, Bilingual PDF Reports & About'}
          </h2>
          <p>
            {isFa
              ? 'اعتبارسنجی ایمن و کاملاً محلی ۸ فرمت علمی ورودی کاربر (CSV، XLSX، JSON، GeoJSON، Shapefile ZIP، GeoTIFF، NetCDF و PDF) بدون ارسال به سرور خارجی، به همراه خروجی استاندارد داده‌ها و تولید گزارش رسمی PDF فارسی و انگلیسی.'
              : '100% local client-side security & schema validation for 8 scientific formats (CSV, XLSX, JSON, GeoJSON, Shapefile ZIP, GeoTIFF, NetCDF, PDF), multi-format data export, and print-ready bilingual A4 scientific PDF reports.'}
          </p>
        </div>

        <div className="ulo-p8-tabs">
          <button type="button" className={`ulo-p8-tab ${activeTab === 'all' ? 'active' : ''}`} onClick={() => setActiveTab('all')}>
            {isFa ? 'نمایش کامل بخش‌های فاز ۸' : 'All Data & Report Tools'}
          </button>
          <button type="button" className={`ulo-p8-tab ${activeTab === 'import' ? 'active' : ''}`} onClick={() => setActiveTab('import')}>
            {isFa ? '۱. ورود و اعتبارسنجی داده کاربر (۸ فرمت)' : '1. User Data Validation (8 Formats)'}
          </button>
          <button type="button" className={`ulo-p8-tab ${activeTab === 'export' ? 'active' : ''}`} onClick={() => setActiveTab('export')}>
            {isFa ? '۲. خروجی داده و گزارش تخصصی PDF' : '2. Scientific Exports & PDF Reports'}
          </button>
          <button type="button" className={`ulo-p8-tab ${activeTab === 'about' ? 'active' : ''}`} onClick={() => setActiveTab('about')}>
            {isFa ? '۳. درباره سامانه، روش‌شناسی و امنیت (About)' : '3. About, Methodology & Governance'}
          </button>
        </div>
      </div>

      {/* PANEL 1: SECURE MULTI-FORMAT DATA INGESTION & VALIDATION */}
      {(activeTab === 'all' || activeTab === 'import') && (
        <div className="ulo-p8-card">
          <div className="ulo-p8-card-head">
            <div>
              <h3 className="ulo-p8-card-title">
                {isFa ? 'درگاه امن ورود و اعتبارسنجی داده‌های پژوهشی کاربر (User-Provided Data)' : 'Secure User-Provided Data Validation Sandbox'}
              </h3>
              <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.82rem', color: '#64748b' }}>
                {isFa
                  ? 'تمام فایل‌ها پیش از پذیرش از نظر امنیت (Path Traversal، حجم، Magic Bytes)، ساختار، واحد، سیستم مختصات (CRS)، تاریخ، مقادیر مفقود، تکراری و پرت بررسی می‌شوند و هرگز به سرور خارجی ارسال نمی‌شوند.'
                  : 'Every file is audited locally for security (path traversal, size, magic bytes), schema, units, CRS, date validity, missing values, duplicates, and physical outliers — never transmitted externally.'}
              </p>
            </div>
            <span className="ulo-p8-status-pill PASS">
              {isFa ? 'پردازش ۱۰۰٪ محلی (Local Privacy)' : '100% Client-Side Sandbox'}
            </span>
          </div>

          <div
            className="ulo-p8-dropzone"
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              e.stopPropagation();
            }}
            onDrop={(e) => {
              e.preventDefault();
              e.stopPropagation();
              handleFiles(e.dataTransfer.files);
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".csv,.xlsx,.json,.geojson,.zip,.tif,.tiff,.nc,.pdf"
              style={{ display: 'none' }}
              onChange={(e) => handleFiles(e.target.files)}
            />
            <strong style={{ fontSize: '0.96rem', color: '#0369a1' }}>
              {validating
                ? isFa
                  ? 'در حال بررسی امنیتی و اعتبارسنجی ساختاری فایل...'
                  : 'Running security and scientific schema audit...'
                : isFa
                ? 'فایل داده را اینجا بکشید و رها کنید یا برای انتخاب کلیک کنید'
                : 'Drag & drop scientific data file here, or click to browse'}
            </strong>
            <span style={{ fontSize: '0.78rem', color: '#475569' }}>
              {isFa ? 'حداکثر حجم مجاز هر فایل: ۲۵ مگابایت | بدون تغییر در داده‌های رسمی رصدخانه' : 'Max 25 MB per file | Isolated under User-Provided Data category'}
            </span>
            <div className="ulo-p8-format-chips">
              {['CSV', 'XLSX', 'JSON', 'GeoJSON', 'Shapefile ZIP', 'GeoTIFF', 'NetCDF', 'PDF'].map((fmt) => (
                <span key={fmt} className="ulo-p8-chip">{fmt}</span>
              ))}
            </div>
          </div>

          {validationReports.map((rep, idx) => (
            <div key={idx} className={`ulo-p8-audit-box ${rep.accepted ? 'accepted' : 'rejected'}`}>
              <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}>
                <div>
                  <strong style={{ fontSize: '0.94rem', color: '#0f172a' }}>{rep.sanitizedFileName}</strong>{' '}
                  <span style={{ fontSize: '0.78rem', color: '#475569' }}>
                    ({rep.detectedFormat} • {rep.fileSizeKB} KB • {rep.dataCategory})
                  </span>
                </div>
                <span className={`ulo-p8-status-pill ${rep.accepted ? 'PASS' : 'FAIL'}`}>
                  {rep.accepted
                    ? isFa ? 'پذیرفته‌شده (تأیید امنیتی و ساختاری)' : 'ACCEPTED (Security & Schema Verified)'
                    : isFa ? 'رد شده (خطای امنیتی یا ساختاری)' : 'REJECTED (Security / Schema Failure)'}
                </span>
              </div>

              <div style={{ marginTop: '0.6rem', fontSize: '0.8rem', color: '#334155', display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
                <span><strong>{isFa ? 'تعداد رکورد:' : 'Records:'}</strong> {rep.rowCount}</span>
                <span><strong>{isFa ? 'سیستم مختصات (CRS):' : 'CRS:'}</strong> {rep.crsInfo}</span>
                <span><strong>{isFa ? 'واحدهای شناسایی‌شده:' : 'Units:'}</strong> {rep.detectedUnits.join(', ')}</span>
                <span><strong>{isFa ? 'بازه تاریخ:' : 'Date Span:'}</strong> {rep.dateRange}</span>
                <span><strong>{isFa ? 'مفقود / تکراری / نامعتبر:' : 'Missing / Dup / Invalid:'}</strong> {rep.missingValuesCount} / {rep.duplicateRowsCount} / {rep.invalidValuesCount}</span>
              </div>

              <div className="ulo-p8-check-grid">
                {rep.checks.map((chk) => (
                  <div key={chk.key} className="ulo-p8-check-item">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                      <strong>{isFa ? chk.labelFa : chk.labelEn}</strong>
                      <span className={`ulo-p8-status-pill ${chk.status}`}>{chk.status}</span>
                    </div>
                    <div style={{ color: '#475569' }}>{isFa ? chk.detailFa : chk.detailEn}</div>
                  </div>
                ))}
              </div>

              {rep.previewHeaders.length > 0 && rep.previewRows.length > 0 && (
                <div className="ulo-p8-preview-table-wrap">
                  <table className="ulo-p8-preview-table">
                    <thead>
                      <tr>
                        {rep.previewHeaders.map((h, i) => (
                          <th key={i}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {rep.previewRows.map((row, rI) => (
                        <tr key={rI}>
                          {row.map((cell, cI) => (
                            <td key={cI}>{cell}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* PANEL 2: MULTI-FORMAT EXPORTS & BILINGUAL PDF REPORTS */}
      {(activeTab === 'all' || activeTab === 'export') && (
        <div className="ulo-p8-card">
          <div className="ulo-p8-card-head">
            <div>
              <h3 className="ulo-p8-card-title">
                {isFa ? 'مرکز خروجی استاندارد داده‌ها و تولید گزارش تخصصی PDF (فارسی و انگلیسی)' : 'Multi-Format Scientific Export & Bilingual PDF Report Generator'}
              </h3>
              <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.82rem', color: '#64748b' }}>
                {isFa
                  ? 'خروجی مستقیم از داده‌های واقعی رصدخانه با درج کامل متادیتا، تاریخ، منابع، روش‌شناسی و محدودیت‌های علمی'
                  : 'Direct exports generated from verified observatory data with provenance metadata, timestamps, citations, and scientific limitations'}
              </p>
            </div>
          </div>

          {exportNotice && (
            <div style={{ marginBottom: '1rem', padding: '0.75rem 1rem', borderRadius: '10px', background: '#f0f9ff', border: '1px solid #bae6fd', color: '#0369a1', fontSize: '0.83rem', fontWeight: 600 }}>
              {exportNotice}
            </div>
          )}

          <div className="ulo-p8-export-grid">
            {/* Bilingual PDF */}
            <div className="ulo-p8-export-tile">
              <div>
                <h4>{isFa ? 'گزارش تخصصی و چاپی PDF (دوزبانه A4)' : 'Official Scientific PDF Report (Bilingual A4)'}</h4>
                <p>
                  {isFa
                    ? 'دارای نمودار برداری SVG تراز آب، جدول مقایسه دوره‌های تاریخی، توصیه‌های مدیریتی، منابع علمی OpenAlex/Crossref، روش‌شناسی و محدودیت‌های علمی.'
                    : 'Includes vector SVG hydrology chart, historical comparison tables, management actions, peer-reviewed references, methodology, and uncertainty caveats.'}
                </p>
              </div>
              <div className="ulo-p8-btn-row">
                <button type="button" className="ulo-p8-btn pdf" onClick={() => handlePdfExport('fa')}>
                  {isFa ? 'تولید گزارش PDF فارسی (RTL)' : 'Generate Persian PDF (RTL)'}
                </button>
                <button type="button" className="ulo-p8-btn secondary" onClick={() => handlePdfExport('en')}>
                  {isFa ? 'تولید گزارش PDF انگلیسی (LTR)' : 'Generate English PDF (LTR)'}
                </button>
              </div>
            </div>

            {/* XLSX & CSV */}
            <div className="ulo-p8-export-tile">
              <div>
                <h4>{isFa ? 'خروجی جدولی اکسل (XLSX) و CSV' : 'Tabular Excel Workbook (XLSX) & CSV'}</h4>
                <p>
                  {isFa
                    ? 'فایل اکسل چندبرگی واقعی (هیدرولوژی، اقلیم ERA5 و متادیتا) و فایل CSV با کدگذاری UTF-8 BOM کاملاً خوانا در نرم‌افزار Excel.'
                    : 'Multi-sheet native OpenXML Excel workbook (Hydrology, ERA5 Climate, Metadata) and UTF-8 BOM CSV file.'}
                </p>
              </div>
              <div className="ulo-p8-btn-row">
                <button
                  type="button"
                  className="ulo-p8-btn"
                  onClick={() => {
                    exportObservatoryXLSX(bundle);
                    setExportNotice(isFa ? 'فایل اکسل چندبرگی واقعی (.xlsx) دانلود شد.' : 'Multi-sheet Excel workbook (.xlsx) downloaded.');
                  }}
                >
                  {isFa ? 'دانلود اکسل XLSX' : 'Download XLSX'}
                </button>
                <button
                  type="button"
                  className="ulo-p8-btn secondary"
                  onClick={() => {
                    exportObservatoryCSV(bundle);
                    setExportNotice(isFa ? 'فایل سری زمانی CSV دانلود شد.' : 'Hydrology CSV exported.');
                  }}
                >
                  {isFa ? 'دانلود CSV' : 'Download CSV'}
                </button>
              </div>
            </div>

            {/* JSON & GeoJSON */}
            <div className="ulo-p8-export-tile">
              <div>
                <h4>{isFa ? 'خروجی ساختاری JSON و مکانی GeoJSON' : 'Structured JSON Bundle & Spatial GeoJSON'}</h4>
                <p>
                  {isFa
                    ? `بسته کامل JSON تمام ماژول‌های علمی و خروجی استاندارد RFC 7946 GeoJSON از ${geojsonCount} لایه مکانی واقعی حوضه دریاچه ارومیه.`
                    : `Full JSON scientific bundle and RFC 7946 GeoJSON FeatureCollection compiled from ${geojsonCount} real basin layers.`}
                </p>
              </div>
              <div className="ulo-p8-btn-row">
                <button
                  type="button"
                  className="ulo-p8-btn"
                  onClick={() => {
                    exportObservatoryJSON(bundle);
                    setExportNotice(isFa ? 'بسته علمی کامل JSON دانلود شد.' : 'Full scientific JSON bundle exported.');
                  }}
                >
                  {isFa ? 'دانلود JSON' : 'Download JSON'}
                </button>
                <button type="button" className="ulo-p8-btn secondary" onClick={handleGeoJsonExport}>
                  {isFa ? 'دانلود GeoJSON' : 'Download GeoJSON'}
                </button>
              </div>
            </div>

            {/* PNG & GeoTIFF */}
            <div className="ulo-p8-export-tile">
              <div>
                <h4>{isFa ? 'خروجی گرافیکی PNG و وضعیت رستر GeoTIFF' : 'High-Res Chart PNG & GeoTIFF Raster Status'}</h4>
                <p>
                  {isFa
                    ? `تصویر باکیفیت PNG از سری زمانی واقعی تراز آب (رزولوشن ۱۴۰۰×۸۲۰) برای درج مستقیم در مقاله و ارائه. وضعیت GeoTIFF: ${
                        geotiffCount > 0 ? `${geotiffCount} لایه رستر موجود` : 'Data Unavailable (رستر خام در مخزن محلی نیست — عدم تولید رستر ساختگی)'
                      }.`
                    : `Publication-grade 1400×820 PNG hydrology chart. GeoTIFF status: ${
                        geotiffCount > 0 ? `${geotiffCount} raster file(s) available` : 'Data Unavailable (no raw local GeoTIFF cached; synthetic rasters strictly prohibited)'
                      }.`}
                </p>
              </div>
              <div className="ulo-p8-btn-row">
                <button
                  type="button"
                  className="ulo-p8-btn"
                  onClick={() => {
                    exportScientificSummaryPNG(bundle, isFa);
                    setExportNotice(isFa ? 'تصویر نمودار باکیفیت PNG با موفقیت ذخیره شد.' : 'High-resolution scientific PNG chart downloaded.');
                  }}
                >
                  {isFa ? 'دانلود تصویر PNG' : 'Download PNG Chart'}
                </button>
                {geotiffCount > 0 && bundle.exportCatalog?.geotiff_rasters?.[0]?.public_path ? (
                  <a
                    href={`${import.meta.env.BASE_URL}${bundle.exportCatalog.geotiff_rasters[0].public_path}`}
                    download
                    className="ulo-p8-btn secondary"
                    style={{ textDecoration: 'none' }}
                  >
                    {isFa ? 'دانلود GeoTIFF' : 'Download GeoTIFF'}
                  </a>
                ) : (
                  <span className="ulo-p8-status-pill WARN" style={{ alignSelf: 'center' }}>
                    GeoTIFF: Data Unavailable
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* PANEL 3: ABOUT, METHODOLOGY, SCIENTIFIC GOVERNANCE & DEVELOPER (Section 16) */}
      {(activeTab === 'all' || activeTab === 'about') && (
        <div className="ulo-p8-card">
          <div className="ulo-p8-card-head">
            <h3 className="ulo-p8-card-title">
              {isFa
                ? 'درباره رصدخانه هوشمند و علمی دریاچه ارومیه (About, Methodology & Limitations)'
                : 'About Urmia Lake Observatory (ULO) — Purpose, Sources, Methodology & Disclaimer'}
            </h3>
          </div>

          <div className="ulo-p8-about-grid">
            <div className="ulo-p8-about-box">
              <h4>{isFa ? 'هدف علمی و کاربردی سامانه' : 'Scientific Purpose & Scope'}</h4>
              <p style={{ margin: 0 }}>
                {isFa
                  ? 'رصدخانه هوشمند و علمی دریاچه ارومیه (ULO) یک سامانه مستقل، رایگان و داده‌محور برای پایش چندرشته‌ای تراز آب، پهنه آبی، اقلیم حوضه، تنوع زیستی، خطرات گردوغبار نمکی و پشتیبانی تصمیم‌گیری پژوهشی و مدیریتی است.'
                  : 'Urmia Lake Observatory (ULO) is an independent, free, data-driven scientific platform dedicated to interdisciplinary monitoring of Lake Urmia water levels, basin climate, biodiversity, salt-dust hazards, and evidence-based decision support.'}
              </p>
            </div>

            <div className="ulo-p8-about-box">
              <h4>{isFa ? 'طبقه‌بندی شش‌گانه صحت علمی داده‌ها' : 'Six-Tier Scientific Data Provenance'}</h4>
              <p style={{ margin: 0 }}>
                {isFa
                  ? 'تمامی داده‌ها به ۶ دسته مجزا تفکیک می‌شوند: (۱) مشاهدات زمینی (GBIF/رامسر)، (۲) مشاهدات ماهواره‌ای (Hydroweb/CLMS/Sentinel/Landsat)، (۳) داده‌های مدل‌محور (ERA5)، (۴) شاخص‌های مشتق‌شده (Mann-Kendall/Sen/SPI)، (۵) برآوردهای غیرمستقیم (هیپسومتری حجم و شوری) و (۶) داده‌های ورودی کاربر.'
                  : 'All data are strictly classified into 6 tiers: (1) Ground Observations (GBIF/Ramsar), (2) Satellite Observations (Hydroweb/CLMS/Sentinel/Landsat), (3) Model-Based Data (ERA5), (4) Derived Indicators (Mann-Kendall/Sen), (5) Indirect Estimates (Hypsometric volume/salinity), and (6) User-Provided Data.'}
              </p>
            </div>

            <div className="ulo-p8-about-box">
              <h4>{isFa ? 'سیاست عدم استفاده از داده ساختگی و امنیت' : 'Zero-Fabrication & Data Security Policy'}</h4>
              <p style={{ margin: 0 }}>
                {isFa
                  ? 'استفاده از هرگونه عدد ساختگی یا نمایشی در محیط عملیاتی مطلقاً ممنوع است. هر شاخص فاقد رستر یا مشاهده معتبر (مانند رطوبت خاک SMAP یا شوری خاک کالیبره‌شده) با عبارت «داده معتبر در دسترس نیست / Data Unavailable» گزارش می‌شود و فایل‌های کاربر هرگز به سرویس خارجی ارسال نمی‌شوند.'
                  : 'Synthetic or placeholder operational data are strictly prohibited. Unavailable products (e.g., calibrated in-situ soil EC or raw GeoTIFFs) are transparently labeled "Data Unavailable". User files remain 100% local in the browser.'}
              </p>
            </div>

            <div className="ulo-p8-about-box">
              <h4>{isFa ? 'مشخصات توسعه‌دهنده و سلب مسئولیت رسمی' : 'Creator Attribution & Institutional Disclaimer'}</h4>
              <p style={{ margin: 0 }}>
                {isFa
                  ? 'توسعه‌دهنده و طراح: علیرضا فاضلی ثانی (Alireza Fazeli Sani) | ایمیل: alirezafazeli@live.com. این سامانه مستقل است و هیچ ادعای وابستگی، نمایندگی یا تأیید رسمی از سازمان‌های NASA، ESA، USGS، UNESCO یا کنوانسیون رامسر ندارد.'
                  : 'Developer & Creator: Alireza Fazeli Sani (علیرضا فاضلی ثانی) | Email: alirezafazeli@live.com. This observatory is an independent open-science project and makes no claim of official affiliation with or endorsement by NASA, ESA, USGS, UNESCO, or Ramsar.'}
              </p>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default DataManagementReports;

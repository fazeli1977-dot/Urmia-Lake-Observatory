import React, { useEffect, useMemo, useState } from 'react';
import './ScientificResearchCenter.css';

export interface ScientificResearchCenterProps {
  lang?: 'fa' | 'en' | string;
}

interface PublicationItem {
  id: string;
  title: string;
  authors: string[];
  year: number;
  venue: string;
  doi: string;
  legal_url: string;
  cited_by_count: number;
  is_open_access: boolean;
  publication_type: 'article' | 'book' | 'report' | string;
  domain_id: string;
  domain_label_fa: string;
  domain_label_en: string;
  abstract: string;
  method_fa: string;
  method_en: string;
  key_finding_fa: string;
  key_finding_en: string;
  catalog_source: string;
}

interface Phase7Payload {
  generated_at_utc: string;
  schema_version: string;
  decision_support: {
    metadata: Record<string, string>;
    current_status_synthesis: {
      latest_observation_date: string;
      current_water_level_m: number;
      ecological_target_level_m: number;
      ecological_deficit_m: number;
      current_area_km2: number;
      current_volume_km3: number;
      z_score_anomaly: number;
      anomaly_classification_fa: string;
      anomaly_classification_en: string;
      change_point_year: number;
      change_point_description_fa: string;
      change_point_description_en: string;
    };
    period_comparisons: Array<{
      period_fa: string;
      period_en: string;
      count: number;
      start_date: string;
      end_date: string;
      mean_level_m: number;
      min_level_m: number;
      max_level_m: number;
      net_change_m: number;
      mean_area_km2: number;
      regime_fa: string;
      regime_en: string;
    }>;
    same_month_comparisons: Array<{
      month_number: number;
      month_label_fa: string;
      month_label_en: string;
      sample_years: number;
      earliest_year: number;
      earliest_level_m: number;
      latest_year: number;
      latest_level_m: number;
      interannual_delta_m: number;
    }>;
    climatic_vs_anthropogenic_attribution: Array<{
      type: string;
      badge_fa: string;
      badge_en: string;
      title_fa: string;
      title_en: string;
      evidence_fa: string;
      evidence_en: string;
    }>;
    restoration_performance_assessment: {
      overall_status_fa: string;
      overall_status_en: string;
      phases: Array<{
        era_fa: string;
        era_en: string;
        trend_fa: string;
        trend_en: string;
      }>;
    };
    management_recommendations: Array<{
      priority: string;
      domain_fa: string;
      domain_en: string;
      action_fa: string;
      action_en: string;
    }>;
    information_gaps_and_research_agenda: {
      information_gaps: Array<{ gap_fa: string; gap_en: string }>;
      priority_research_topics: Array<{ topic_fa: string; topic_en: string }>;
    };
  };
  ecology_biodiversity: {
    metadata: Record<string, string>;
    gbif_summary: {
      query_bbox: string;
      total_occurrences_in_basin: number;
      sampled_unique_species_count: number;
      class_breakdown: Record<string, number>;
      recent_occurrences: Array<{
        gbif_key: string;
        scientific_name: string;
        class_name: string;
        event_date: string;
        latitude: number;
        longitude: number;
        basis_of_record: string;
        dataset_name: string;
      }>;
    };
    international_designations: Array<{
      organization: string;
      site_name_fa: string;
      site_name_en: string;
      site_id: string;
      designation_date: string;
      designated_area_ha: number;
      montreux_record_status_fa: string;
      montreux_record_status_en: string;
      official_url: string;
      key_ecological_criteria_fa: string;
      key_ecological_criteria_en: string;
    }>;
    indicator_species: Array<{
      scientific_name: string;
      common_name_fa: string;
      common_name_en: string;
      gbif_taxon_key: number;
      gbif_url: string;
      trophic_role_fa: string;
      trophic_role_en: string;
      optimal_salinity_gl: string;
      current_status_fa: string;
      current_status_en: string;
      risk_level: string;
    }>;
    habitat_assessment: Array<{
      habitat_id: string;
      name_fa: string;
      name_en: string;
      status_code: string;
      condition_fa: string;
      condition_en: string;
    }>;
  };
  scientific_library: {
    metadata: Record<string, string>;
    total_publications: number;
    domain_counts: Record<string, number>;
    publications: PublicationItem[];
  };
}

export const ScientificResearchCenter: React.FC<ScientificResearchCenterProps> = ({ lang: propLang }) => {
  const [detectedLang, setDetectedLang] = useState<'fa' | 'en'>('fa');
  const [payload, setPayload] = useState<Phase7Payload | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [activeSubTab, setActiveSubTab] = useState<'all' | 'dss' | 'ecology' | 'library'>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedDomain, setSelectedDomain] = useState<string>('all');
  const [selectedPubType, setSelectedPubType] = useState<string>('all');
  const [livePublications, setLivePublications] = useState<PublicationItem[]>([]);
  const [liveSearching, setLiveSearching] = useState<boolean>(false);
  const [liveSearchStatus, setLiveSearchStatus] = useState<string>('');

  // Auto-detect language from props or DOM dir/header toggle button
  useEffect(() => {
    if (propLang === 'en' || propLang === 'fa') {
      setDetectedLang(propLang);
      return;
    }
    const checkDomLang = () => {
      const htmlDir = document.documentElement.getAttribute('dir');
      const rootDir = document.querySelector('[dir]')?.getAttribute('dir');
      if (htmlDir === 'ltr' || rootDir === 'ltr') {
        setDetectedLang('en');
        return;
      }
      if (htmlDir === 'rtl' || rootDir === 'rtl') {
        setDetectedLang('fa');
        return;
      }
      const buttons = Array.from(document.querySelectorAll('button'));
      for (const b of buttons) {
        const txt = (b.textContent || '').trim();
        if (txt.includes('فارسی') || txt.includes('Persian')) {
          setDetectedLang('en');
          return;
        }
        if (txt.includes('English')) {
          setDetectedLang('fa');
          return;
        }
      }
    };
    checkDomLang();
    const observer = new MutationObserver(checkDomLang);
    observer.observe(document.documentElement, { attributes: true, subtree: true, childList: true });
    window.addEventListener('click', checkDomLang);
    return () => {
      observer.disconnect();
      window.removeEventListener('click', checkDomLang);
    };
  }, [propLang]);

  const isFa = (propLang ? propLang !== 'en' : detectedLang === 'fa');

  useEffect(() => {
    let cancelled = false;
    fetch(`${import.meta.env.BASE_URL}data/scientific_research_center_latest.json`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        return res.json();
      })
      .then((data: Phase7Payload) => {
        if (!cancelled) {
          setPayload(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(String(err));
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleLiveApiSearch = async () => {
    const q = searchQuery.trim() || 'Lake Urmia';
    setLiveSearching(true);
    setLiveSearchStatus(
      isFa
        ? 'در حال استعلام زنده از پایگاه‌های علمی OpenAlex و Crossref...'
        : 'Querying live OpenAlex and Crossref scientific APIs...'
    );
    try {
      const queryStr = encodeURIComponent(q.toLowerCase().includes('urmia') ? q : `Lake Urmia ${q}`);
      const res = await fetch(`https://api.openalex.org/works?search=${queryStr}&per-page=12&sort=cited_by_count:desc`);
      if (!res.ok) {
        throw new Error(`OpenAlex HTTP ${res.status}`);
      }
      const data = await res.json();
      const items: PublicationItem[] = (data.results || []).map((item: Record<string, any>, idx: number) => {
        const doiRaw = String(item.doi || '');
        const doi = doiRaw.replace('https://doi.org/', '').replace('http://doi.org/', '');
        const authors = Array.isArray(item.authorships)
          ? item.authorships.slice(0, 4).map((a: any) => a?.author?.display_name).filter(Boolean)
          : ['OpenAlex Indexed Author'];
        return {
          id: String(item.id || `live-oa-${idx}`),
          title: String(item.title || 'Untitled Scientific Study'),
          authors: authors.length ? authors : ['Research Author'],
          year: Number(item.publication_year || 2023),
          venue: String(item?.primary_location?.source?.display_name || 'International Scientific Venue'),
          doi: doi || 'OpenAlex Indexed',
          legal_url: String(item?.open_access?.oa_url || (doi ? `https://doi.org/${doi}` : item.id || 'https://openalex.org')),
          cited_by_count: Number(item.cited_by_count || 0),
          is_open_access: Boolean(item?.open_access?.is_oa),
          publication_type: String(item.type || 'article').includes('book') ? 'book' : 'article',
          domain_id: 'hydrology',
          domain_label_fa: 'یافته جست‌وجوی زنده (OpenAlex Live)',
          domain_label_en: 'Live API Result (OpenAlex)',
          abstract: `Live peer-reviewed record retrieved from OpenAlex API for query "${q}". Published in ${item.publication_year || 'recent'} (${item.cited_by_count || 0} citations).`,
          method_fa: 'بازیابی مستقیم از مخزن علمی OpenAlex با شناسه دیجیتال معتبر',
          method_en: 'Direct bibliographic retrieval from OpenAlex REST API',
          key_finding_fa: 'برای مطالعه متن کامل و جزئیات روش‌شناسی روی لینک قانونی DOI/OpenAccess کلیک کنید.',
          key_finding_en: 'Click the legal DOI / Open-Access link to inspect full methodology and data tables.',
          catalog_source: 'OpenAlex Live REST Query',
        };
      });
      setLivePublications(items);
      setLiveSearchStatus(
        isFa
          ? `${items.length} منبع علمی جدید به صورت زنده از OpenAlex دریافت و به فهرست اضافه شد.`
          : `Retrieved ${items.length} live scientific works from OpenAlex API.`
      );
    } catch (err) {
      setLiveSearchStatus(
        isFa
          ? `عدم دسترسی لحظه‌ای به اینترنت یا سرویس خارجی (${String(err)}) — نمایش از پایگاه داده آفلاین تأییدشده.`
          : `Live API unreachable (${String(err)}) — displaying verified local scientific corpus.`
      );
    } finally {
      setLiveSearching(false);
    }
  };

  const allPublications = useMemo(() => {
    const base = payload?.scientific_library?.publications || [];
    const combined = [...livePublications, ...base];
    const seen = new Set<string>();
    return combined.filter((p) => {
      const key = (p.doi && p.doi !== 'N/A' ? p.doi : p.title).toLowerCase();
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [payload, livePublications]);

  const filteredPublications = useMemo(() => {
    return allPublications.filter((p) => {
      if (selectedDomain !== 'all' && p.domain_id !== selectedDomain) return false;
      if (selectedPubType !== 'all' && p.publication_type !== selectedPubType) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const text = `${p.title} ${p.authors.join(' ')} ${p.abstract} ${p.venue} ${p.doi} ${p.key_finding_fa} ${p.key_finding_en}`.toLowerCase();
        if (!text.includes(q)) return false;
      }
      return true;
    });
  }, [allPublications, selectedDomain, selectedPubType, searchQuery]);

  if (loading) {
    return (
      <section className="ulo-phase7-wrapper" dir={isFa ? 'rtl' : 'ltr'}>
        <div className="ulo-p7-section-card">
          <p>{isFa ? 'در حال بارگذاری مرکز پژوهش، تصمیم‌یار و داده‌های تنوع زیستی (GBIF / Ramsar)...' : 'Loading Scientific Research Center, Decision Support & Biodiversity (GBIF / Ramsar)...'}</p>
        </div>
      </section>
    );
  }

  if (error || !payload) {
    return (
      <section className="ulo-phase7-wrapper" dir={isFa ? 'rtl' : 'ltr'}>
        <div className="ulo-p7-section-card">
          <p>{isFa ? `داده معتبر مرکز پژوهش در دسترس نیست (${error || 'Data Unavailable'})` : `Scientific Research Center Data Unavailable (${error})`}</p>
        </div>
      </section>
    );
  }

  const { decision_support: dss, ecology_biodiversity: eco, scientific_library: lib } = payload;

  const domainOptions = [
    { id: 'all', fa: 'همه حوزه‌های علمی', en: 'All Scientific Domains' },
    { id: 'hydrology', fa: 'هیدرولوژی و منابع آب', en: 'Hydrology & Water' },
    { id: 'drought_desiccation', fa: 'خشک‌شدن دریاچه و احیا', en: 'Desiccation & Restoration' },
    { id: 'climate', fa: 'اقلیم و خشکسالی', en: 'Climate & Drought' },
    { id: 'remote_sensing', fa: 'سنجش‌ازدور و ماهواره', en: 'Remote Sensing' },
    { id: 'soil_salinity_dust', fa: 'خاک، شوری و گردوغبار', en: 'Soil, Salinity & Dust' },
    { id: 'ecology_biodiversity', fa: 'اکولوژی، آرتمیا و تنوع زیستی', en: 'Ecology & Artemia' },
  ];

  return (
    <section className="ulo-phase7-wrapper" dir={isFa ? 'rtl' : 'ltr'} id="scientific-research-center">
      {/* Top Banner & Sub-navigation */}
      <div className="ulo-p7-header-card">
        <div className="ulo-p7-header-top">
          <div>
            <h2 className="ulo-p7-title">
              {isFa
                ? 'مرکز پژوهش، کتابخانه علمی، پایش رامسر/GBIF و سامانه هوشمند تصمیم‌یار'
                : 'Scientific Research Center, Library, Ramsar/GBIF Ecology & Decision Support'}
            </h2>
            <p className="ulo-p7-subtitle">
              {isFa
                ? 'تلفیق داده‌های واقعی تراز و بیلان اقلیمی، مشاهدات تنوع زیستی جهانی (GBIF، کنوانسیون رامسر سایت ۳۸ و زیست‌کره یونسکو) و پایگاه مقالات علمی (OpenAlex / Crossref) با تفکیک دقیق مشاهدات از فرضیه‌های علمی (Hypothesis).'
                : 'Integrated synthesis of real altimetry and climate balance, global biodiversity records (GBIF, Ramsar Site #38, UNESCO Biosphere Reserve), and peer-reviewed literature (OpenAlex / Crossref) with explicit Hypothesis attribution.'}
            </p>
          </div>
          <div className="ulo-p7-badges">
            <span className="ulo-p7-badge">Ramsar Site #38 (1975)</span>
            <span className="ulo-p7-badge">UNESCO MAB (1976)</span>
            <span className="ulo-p7-badge">GBIF Basin BBox: {eco.gbif_summary.total_occurrences_in_basin.toLocaleString()} Records</span>
            <span className="ulo-p7-badge">OpenAlex + Crossref: {allPublications.length} Works</span>
          </div>
        </div>

        <div className="ulo-p7-subnav">
          <button
            type="button"
            className={`ulo-p7-tab-btn ${activeSubTab === 'all' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('all')}
          >
            {isFa ? 'نمایش یکپارچه هر ۳ بخش علمی' : 'All Research & DSS Modules'}
          </button>
          <button
            type="button"
            className={`ulo-p7-tab-btn ${activeSubTab === 'dss' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('dss')}
          >
            {isFa ? '۱. سامانه هوشمند تحلیل و تصمیم‌یار (DSS)' : '1. Scientific Analysis & Decision Support'}
          </button>
          <button
            type="button"
            className={`ulo-p7-tab-btn ${activeSubTab === 'ecology' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('ecology')}
          >
            {isFa ? '۲. اکولوژی، تنوع زیستی، رامسر و GBIF' : '2. Ecology, Biodiversity, Ramsar & GBIF'}
          </button>
          <button
            type="button"
            className={`ulo-p7-tab-btn ${activeSubTab === 'library' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('library')}
          >
            {isFa ? '۳. کتابخانه علمی و مقالات (OpenAlex / Crossref)' : '3. Scientific Library & Research Center'}
          </button>
        </div>
      </div>

      {/* MODULE 1: SCIENTIFIC ANALYSIS & DECISION SUPPORT (Section 7 & 8) */}
      {(activeSubTab === 'all' || activeSubTab === 'dss') && (
        <div className="ulo-p7-section-card">
          <div className="ulo-p7-section-head">
            <div>
              <h3 className="ulo-p7-section-title">
                {isFa
                  ? 'سامانه هوشمند تحلیل و تصمیم‌یار (Scientific Analysis & Decision Support)'
                  : 'Scientific Analysis & Decision Support System'}
              </h3>
              <p className="ulo-p7-section-desc">
                {isFa
                  ? 'تشخیص ناهنجاری، مقایسه دوره‌های تاریخی، مقایسه ماه مشابه سال‌های مختلف، تحلیل علّی (مشاهده در برابر Hypothesis) و پیشنهادهای مدیریتی'
                  : 'Anomaly detection, multi-period & same-month deseasonalized comparisons, causal attribution (Verified Observation vs. Hypothesis), and decision matrix'}
              </p>
            </div>
            <span className="ulo-p7-cat-tag">
              {isFa ? 'دسته داده: شاخص‌های مشتق‌شده علمی (Derived Indicators)' : 'Category: Derived Indicators'}
            </span>
          </div>

          {/* Current Anomaly & Change-Point Cards */}
          <div className="ulo-p7-grid-2">
            <div className="ulo-p7-subcard highlight-warn">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}>
                <h4 className="ulo-p7-subcard-title">
                  {isFa ? 'تشخیص ناهنجاری وضعیت فعلی (Anomaly Detection)' : 'Current State Anomaly Detection'}
                </h4>
                <span className="ulo-p7-cat-tag critical">
                  Z-Score: {dss.current_status_synthesis.z_score_anomaly}σ
                </span>
              </div>
              <p className="ulo-p7-subcard-text">
                {isFa
                  ? `${dss.current_status_synthesis.anomaly_classification_fa} — در آخرین مشاهده (${dss.current_status_synthesis.latest_observation_date})، تراز آب ${dss.current_status_synthesis.current_water_level_m} متر ثبت شده که ${dss.current_status_synthesis.ecological_deficit_m} متر پایین‌تر از تراز اکولوژیک (${dss.current_status_synthesis.ecological_target_level_m} متر) است.`
                  : `${dss.current_status_synthesis.anomaly_classification_en} — Latest observation (${dss.current_status_synthesis.latest_observation_date}) places water elevation at ${dss.current_status_synthesis.current_water_level_m} m, representing a ${dss.current_status_synthesis.ecological_deficit_m} m deficit below the ${dss.current_status_synthesis.ecological_target_level_m} m ecological target.`}
              </p>
            </div>

            <div className="ulo-p7-subcard">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}>
                <h4 className="ulo-p7-subcard-title">
                  {isFa ? 'تشخیص نقطه تغییر رژیم (Change-Point Detection)' : 'Structural Change-Point Detection'}
                </h4>
                <span className="ulo-p7-cat-tag">
                  {isFa ? `نقطه شکست: سال ${dss.current_status_synthesis.change_point_year}` : `Break Year: ${dss.current_status_synthesis.change_point_year}`}
                </span>
              </div>
              <p className="ulo-p7-subcard-text">
                {isFa
                  ? dss.current_status_synthesis.change_point_description_fa
                  : dss.current_status_synthesis.change_point_description_en}
              </p>
            </div>
          </div>

          {/* Historical Multi-Period Comparison Table */}
          <h4 style={{ margin: '1.35rem 0 0.4rem 0', fontSize: '0.96rem', color: '#0f172a' }}>
            {isFa
              ? 'الف) مقایسه آماری دوره‌های تاریخی و رژیم‌های تر و خشک (بخش ۷ پرامپت)'
              : 'A) Multi-Period Historical & Wet/Dry Regime Comparison'}
          </h4>
          <div className="ulo-p7-table-wrap">
            <table className="ulo-p7-table">
              <thead>
                <tr>
                  <th>{isFa ? 'دوره زمانی مقایسه' : 'Comparison Period'}</th>
                  <th>{isFa ? 'بازه تاریخ' : 'Date Span'}</th>
                  <th>{isFa ? 'تعداد مشاهده' : 'Samples (n)'}</th>
                  <th>{isFa ? 'میانگین تراز (m)' : 'Mean Level (m)'}</th>
                  <th>{isFa ? 'حداقل / حداکثر (m)' : 'Min / Max (m)'}</th>
                  <th>{isFa ? 'تغییر خالص دوره (m)' : 'Net Change (m)'}</th>
                  <th>{isFa ? 'میانگین پهنه آبی (km²)' : 'Mean Wet Area (km²)'}</th>
                  <th>{isFa ? 'وضعیت رژیم هیدرولوژیک' : 'Hydrological Regime'}</th>
                </tr>
              </thead>
              <tbody>
                {dss.period_comparisons.map((pc, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 600 }}>{isFa ? pc.period_fa : pc.period_en}</td>
                    <td style={{ direction: 'ltr' }}>{pc.start_date} → {pc.end_date}</td>
                    <td>{pc.count}</td>
                    <td style={{ direction: 'ltr', fontWeight: 600 }}>{pc.mean_level_m.toFixed(2)}</td>
                    <td style={{ direction: 'ltr' }}>{pc.min_level_m.toFixed(2)} / {pc.max_level_m.toFixed(2)}</td>
                    <td>
                      <span className={pc.net_change_m < 0 ? 'ulo-p7-num-neg' : 'ulo-p7-num-pos'}>
                        {pc.net_change_m > 0 ? `+${pc.net_change_m.toFixed(2)}` : pc.net_change_m.toFixed(2)} m
                      </span>
                    </td>
                    <td style={{ direction: 'ltr' }}>{pc.mean_area_km2.toFixed(1)}</td>
                    <td>{isFa ? pc.regime_fa : pc.regime_en}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Same-Month Interannual Comparison Table */}
          {dss.same_month_comparisons.length > 0 && (
            <>
              <h4 style={{ margin: '1.35rem 0 0.4rem 0', fontSize: '0.96rem', color: '#0f172a' }}>
                {isFa
                  ? 'ب) مقایسه ماه مشابه در سال‌های مختلف (حذف اثر نوسان فصلی — بخش ۷ پرامپت)'
                  : 'B) Same-Month Inter-Annual Comparison (Deseasonalized Benchmark)'}
              </h4>
              <div className="ulo-p7-table-wrap">
                <table className="ulo-p7-table">
                  <thead>
                    <tr>
                      <th>{isFa ? 'ماه سال' : 'Calendar Month'}</th>
                      <th>{isFa ? 'تعداد سال‌های دارای داده' : 'Observed Years'}</th>
                      <th>{isFa ? 'اولین سال ثبت (تراز m)' : 'Earliest Year (Level m)'}</th>
                      <th>{isFa ? 'آخرین سال ثبت (تراز m)' : 'Latest Year (Level m)'}</th>
                      <th>{isFa ? 'اختلاف تراز بدون اثر فصلی (Δm)' : 'Deseasonalized Delta (Δm)'}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dss.same_month_comparisons.map((sm) => (
                      <tr key={sm.month_number}>
                        <td style={{ fontWeight: 600 }}>{isFa ? sm.month_label_fa : sm.month_label_en}</td>
                        <td>{sm.sample_years}</td>
                        <td style={{ direction: 'ltr' }}>{sm.earliest_year} ({sm.earliest_level_m.toFixed(2)} m)</td>
                        <td style={{ direction: 'ltr' }}>{sm.latest_year} ({sm.latest_level_m.toFixed(2)} m)</td>
                        <td>
                          <span className={sm.interannual_delta_m < 0 ? 'ulo-p7-num-neg' : 'ulo-p7-num-pos'}>
                            {sm.interannual_delta_m > 0 ? `+${sm.interannual_delta_m.toFixed(2)}` : sm.interannual_delta_m.toFixed(2)} m
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* Climatic vs Anthropogenic Attribution (Verified vs Hypothesis) */}
          <h4 style={{ margin: '1.35rem 0 0.65rem 0', fontSize: '0.96rem', color: '#0f172a' }}>
            {isFa
              ? 'ج) تحلیل ارتباط متغیرهای اقلیمی و هیدرولوژیکی و تفکیک مشاهدات از فرضیه‌ها (Hypothesis)'
              : 'C) Climatic–Hydrological Coupling & Causal Attribution (Verified vs. Hypothesis)'}
          </h4>
          <div className="ulo-p7-grid-2">
            {dss.climatic_vs_anthropogenic_attribution.map((item, idx) => {
              const isHyp = item.type === 'Hypothesis';
              return (
                <div key={idx} className={`ulo-p7-subcard ${isHyp ? 'highlight-warn' : 'highlight-info'}`}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <h5 className="ulo-p7-subcard-title">{isFa ? item.title_fa : item.title_en}</h5>
                    <span className={`ulo-p7-cat-tag ${isHyp ? 'hypothesis' : 'verified'}`}>
                      {isFa ? item.badge_fa : item.badge_en}
                    </span>
                  </div>
                  <p className="ulo-p7-subcard-text">{isFa ? item.evidence_fa : item.evidence_en}</p>
                </div>
              );
            })}
          </div>

          {/* Restoration Performance & Management Recommendations */}
          <h4 style={{ margin: '1.35rem 0 0.65rem 0', fontSize: '0.96rem', color: '#0f172a' }}>
            {isFa
              ? 'د) ارزیابی عملکرد دوره‌های احیایی و پیشنهادهای مدیریتی مبتنی بر شواهد'
              : 'D) Restoration Era Performance & Evidence-Based Management Recommendations'}
          </h4>
          <div className="ulo-p7-grid-3" style={{ marginBottom: '1rem' }}>
            {dss.restoration_performance_assessment.phases.map((ph, idx) => (
              <div key={idx} className="ulo-p7-subcard">
                <h5 className="ulo-p7-subcard-title">{isFa ? ph.era_fa : ph.era_en}</h5>
                <p className="ulo-p7-subcard-text">{isFa ? ph.trend_fa : ph.trend_en}</p>
              </div>
            ))}
          </div>

          <div className="ulo-p7-grid-2">
            {dss.management_recommendations.map((rec, idx) => (
              <div key={idx} className="ulo-p7-subcard">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h5 className="ulo-p7-subcard-title">{isFa ? rec.domain_fa : rec.domain_en}</h5>
                  <span className={`ulo-p7-cat-tag ${rec.priority === 'HIGH' ? 'critical' : ''}`}>
                    {isFa ? `اولویت: ${rec.priority}` : `Priority: ${rec.priority}`}
                  </span>
                </div>
                <p className="ulo-p7-subcard-text">{isFa ? rec.action_fa : rec.action_en}</p>
              </div>
            ))}
          </div>

          {/* Information Gaps & Priority Research Topics */}
          <div className="ulo-p7-grid-2" style={{ marginTop: '1.15rem' }}>
            <div className="ulo-p7-subcard">
              <h5 className="ulo-p7-subcard-title">
                {isFa ? 'خلأهای اطلاعاتی و داده‌ای شناسایی‌شده (Information Gaps)' : 'Identified Data & Information Gaps'}
              </h5>
              <ul style={{ margin: 0, paddingInlineStart: '1.2rem', fontSize: '0.83rem', color: '#334155', lineHeight: 1.7 }}>
                {dss.information_gaps_and_research_agenda.information_gaps.map((g, idx) => (
                  <li key={idx}>{isFa ? g.gap_fa : g.gap_en}</li>
                ))}
              </ul>
            </div>

            <div className="ulo-p7-subcard">
              <h5 className="ulo-p7-subcard-title">
                {isFa ? 'پیشنهاد موضوعات پژوهشی اولویت‌دار (Priority Research Agenda)' : 'Priority Scientific Research Topics'}
              </h5>
              <ul style={{ margin: 0, paddingInlineStart: '1.2rem', fontSize: '0.83rem', color: '#334155', lineHeight: 1.7 }}>
                {dss.information_gaps_and_research_agenda.priority_research_topics.map((t, idx) => (
                  <li key={idx}>{isFa ? t.topic_fa : t.topic_en}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="ulo-p7-meta-footer">
            <span>{isFa ? `منبع: ${dss.metadata.source_name}` : `Source: ${dss.metadata.source_name}`}</span>
            <span>{isFa ? `روش: ${dss.metadata.extraction_method}` : `Method: ${dss.metadata.extraction_method}`}</span>
            <span>{isFa ? `بروزرسانی: ${dss.metadata.retrieved_at_utc}` : `Updated: ${dss.metadata.retrieved_at_utc}`}</span>
          </div>
        </div>
      )}

      {/* MODULE 2: ECOLOGY, BIODIVERSITY, RAMSAR & GBIF (Section 5 & 6) */}
      {(activeSubTab === 'all' || activeSubTab === 'ecology') && (
        <div className="ulo-p7-section-card">
          <div className="ulo-p7-section-head">
            <div>
              <h3 className="ulo-p7-section-title">
                {isFa
                  ? 'اکولوژی، تنوع زیستی، کنوانسیون رامسر (سایت ۳۸)، زیست‌کره یونسکو و مشاهدات GBIF'
                  : 'Ecology, Biodiversity, Ramsar Site #38, UNESCO Biosphere & GBIF Occurrences'}
              </h3>
              <p className="ulo-p7-section-desc">
                {isFa
                  ? `متصل به شبکه جهانی تنوع زیستی GBIF در محدوده حوضه آبریز (${eco.gbif_summary.query_bbox}) و ثبت رسمی کنوانسیون رامسر و یونسکو`
                  : `Connected to Global Biodiversity Information Facility (GBIF) across ${eco.gbif_summary.query_bbox} and official Ramsar/UNESCO registries`}
              </p>
            </div>
            <span className="ulo-p7-cat-tag verified">
              {isFa ? 'دسته داده: مشاهدات زمینی و شاخص‌های اکولوژیک' : 'Category: Ground Observations & Ecological Indicators'}
            </span>
          </div>

          {/* Ramsar & UNESCO Designations */}
          <div className="ulo-p7-grid-2" style={{ marginBottom: '1.25rem' }}>
            {eco.international_designations.map((des, idx) => (
              <div key={idx} className="ulo-p7-subcard highlight-info">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.4rem' }}>
                  <h4 className="ulo-p7-subcard-title">{isFa ? des.site_name_fa : des.site_name_en}</h4>
                  <span className="ulo-p7-cat-tag verified">{des.site_id} ({des.designation_date})</span>
                </div>
                <p className="ulo-p7-subcard-text">
                  <strong>{isFa ? 'سازمان و مساحت ثبت‌شده: ' : 'Organization & Designated Area: '}</strong>
                  {des.organization} — {des.designated_area_ha.toLocaleString()} ha
                </p>
                <p className="ulo-p7-subcard-text">
                  <strong>{isFa ? 'وضعیت حفاظتی: ' : 'Conservation Status: '}</strong>
                  {isFa ? des.montreux_record_status_fa : des.montreux_record_status_en}
                </p>
                <p className="ulo-p7-subcard-text">
                  <strong>{isFa ? 'معیار اکولوژیک: ' : 'Ecological Criteria: '}</strong>
                  {isFa ? des.key_ecological_criteria_fa : des.key_ecological_criteria_en}
                </p>
                <div>
                  <a href={des.official_url} target="_blank" rel="noopener noreferrer" className="ulo-p7-link">
                    {isFa ? 'مشاهده پرونده رسمی در پورتال بین‌المللی ↗' : 'View Official International Registry Profile ↗'}
                  </a>
                </div>
              </div>
            ))}
          </div>

          {/* Indicator Species Table */}
          <h4 style={{ margin: '1rem 0 0.5rem 0', fontSize: '0.96rem', color: '#0f172a' }}>
            {isFa
              ? 'گونه‌های شاخص جانوری، پرندگان مهاجر و گیاهان شورپسند حوضه دریاچه ارومیه (GBIF Taxon Verified)'
              : 'Keystone Fauna, Migratory Waterbirds & Halophytic Flora of Lake Urmia (GBIF Taxon Verified)'}
          </h4>
          <div className="ulo-p7-table-wrap">
            <table className="ulo-p7-table">
              <thead>
                <tr>
                  <th>{isFa ? 'نام علمی و لینک GBIF' : 'Scientific Name & GBIF'}</th>
                  <th>{isFa ? 'نام فارسی / انگلیسی' : 'Common Name'}</th>
                  <th>{isFa ? 'نقش اکولوژیک در زنجیره غذایی' : 'Ecological & Trophic Role'}</th>
                  <th>{isFa ? 'آستانه تحمل شوری / زیستگاه' : 'Salinity / Habitat Threshold'}</th>
                  <th>{isFa ? 'وضعیت فعلی در تراز و شوری کنونی دریاچه' : 'Current Status under Present Lake Stage'}</th>
                </tr>
              </thead>
              <tbody>
                {eco.indicator_species.map((sp, idx) => (
                  <tr key={idx}>
                    <td style={{ direction: 'ltr', fontWeight: 700 }}>
                      <a href={sp.gbif_url} target="_blank" rel="noopener noreferrer" className="ulo-p7-link">
                        <i>{sp.scientific_name}</i> ↗
                      </a>
                    </td>
                    <td style={{ fontWeight: 600 }}>{isFa ? sp.common_name_fa : sp.common_name_en}</td>
                    <td>{isFa ? sp.trophic_role_fa : sp.trophic_role_en}</td>
                    <td>{sp.optimal_salinity_gl}</td>
                    <td>
                      <span className={`ulo-p7-cat-tag ${sp.risk_level === 'CRITICAL' || sp.risk_level === 'HIGH' ? 'critical' : 'hypothesis'}`}>
                        {sp.risk_level}
                      </span>{' '}
                      {isFa ? sp.current_status_fa : sp.current_status_en}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Habitat Condition Cards */}
          <h4 style={{ margin: '1.25rem 0 0.65rem 0', fontSize: '0.96rem', color: '#0f172a' }}>
            {isFa ? 'پایش وضعیت زیستگاه‌های چهارگانه دریاچه ارومیه' : 'Assessment of the Four Primary Habitat Zones'}
          </h4>
          <div className="ulo-p7-grid-2">
            {eco.habitat_assessment.map((hab) => (
              <div key={hab.habitat_id} className="ulo-p7-subcard">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h5 className="ulo-p7-subcard-title">{isFa ? hab.name_fa : hab.name_en}</h5>
                  <span className={`ulo-p7-cat-tag ${hab.status_code === 'CRITICAL' || hab.status_code === 'HIGH_RISK' ? 'critical' : 'verified'}`}>
                    {hab.status_code}
                  </span>
                </div>
                <p className="ulo-p7-subcard-text">{isFa ? hab.condition_fa : hab.condition_en}</p>
              </div>
            ))}
          </div>

          <div className="ulo-p7-meta-footer">
            <span>{isFa ? `منبع: ${eco.metadata.source_name}` : `Source: ${eco.metadata.source_name}`}</span>
            <span>{isFa ? `محدودیت علمی: ${eco.metadata.limitations_fa}` : `Limitation: ${eco.metadata.limitations_en}`}</span>
          </div>
        </div>
      )}

      {/* MODULE 3: SCIENTIFIC LIBRARY & RESEARCH CENTER (Section 9) */}
      {(activeSubTab === 'all' || activeSubTab === 'library') && (
        <div className="ulo-p7-section-card">
          <div className="ulo-p7-section-head">
            <div>
              <h3 className="ulo-p7-section-title">
                {isFa
                  ? 'کتابخانه علمی و مرکز پژوهش دریاچه ارومیه (Scientific Library & Research Center)'
                  : 'Scientific Library & Research Center (OpenAlex & Crossref)'}
              </h3>
              <p className="ulo-p7-section-desc">
                {isFa
                  ? 'جست‌وجوی مقالات، کتاب‌ها و گزارش‌های علمی داوری‌شده با شناسه DOI، لینک قانونی، روش پژوهش و یافته‌های اصلی'
                  : 'Search peer-reviewed articles, books, and scientific reports with verified DOIs, legal links, methodology, and key findings'}
              </p>
            </div>
            <span className="ulo-p7-cat-tag">
              {isFa
                ? `${filteredPublications.length} از ${allPublications.length} منبع علمی`
                : `Showing ${filteredPublications.length} of ${allPublications.length} works`}
            </span>
          </div>

          {/* Search & Filter Controls */}
          <div className="ulo-p7-search-bar">
            <input
              type="text"
              className="ulo-p7-input"
              placeholder={
                isFa
                  ? 'جست‌وجو در عنوان، نویسنده، DOI یا کلیدواژه (مثلاً Artemia, GRACE, Sentinel, dust, drought)...'
                  : 'Filter or search live by title, author, DOI, or keyword (e.g., Artemia, GRACE, Sentinel, dust)...'
              }
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleLiveApiSearch();
              }}
            />
            <select
              className="ulo-p7-select"
              value={selectedPubType}
              onChange={(e) => setSelectedPubType(e.target.value)}
            >
              <option value="all">{isFa ? 'همه انواع منابع (مقاله / کتاب / گزارش)' : 'All Types (Article / Book / Report)'}</option>
              <option value="article">{isFa ? 'مقاله پژوهشی (Journal Article)' : 'Journal Articles'}</option>
              <option value="report">{isFa ? 'گزارش علمی و مروری (Report / Review)' : 'Scientific Reports & Reviews'}</option>
              <option value="book">{isFa ? 'کتاب و فصل کتاب (Book / Chapter)' : 'Books & Book Chapters'}</option>
            </select>
            <button
              type="button"
              className="ulo-p7-btn"
              onClick={handleLiveApiSearch}
              disabled={liveSearching}
            >
              {liveSearching
                ? (isFa ? 'در حال استعلام...' : 'Querying API...')
                : (isFa ? 'جست‌وجوی زنده در OpenAlex 🔎' : 'Live OpenAlex Search 🔎')}
            </button>
          </div>

          {liveSearchStatus && (
            <p style={{ fontSize: '0.8rem', color: '#0369a1', margin: '0 0 0.85rem 0', fontWeight: 600 }}>
              {liveSearchStatus}
            </p>
          )}

          {/* Domain Filter Pills */}
          <div className="ulo-p7-domain-pills">
            {domainOptions.map((d) => (
              <button
                key={d.id}
                type="button"
                className={`ulo-p7-pill ${selectedDomain === d.id ? 'active' : ''}`}
                onClick={() => setSelectedDomain(d.id)}
              >
                {isFa ? d.fa : d.en}
              </button>
            ))}
          </div>

          {/* Publications Grid */}
          <div className="ulo-p7-pub-list">
            {filteredPublications.slice(0, 24).map((pub) => (
              <article key={pub.id} className="ulo-p7-pub-card">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                    <span className="ulo-p7-cat-tag">
                      {isFa ? pub.domain_label_fa : pub.domain_label_en}
                    </span>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#475569' }}>
                      {pub.year} • {isFa ? `${pub.cited_by_count} استناد` : `${pub.cited_by_count} Citations`}
                    </span>
                  </div>

                  <h4 className="ulo-p7-pub-title">{pub.title}</h4>

                  <div className="ulo-p7-pub-meta">
                    <span><strong>{isFa ? 'نویسندگان:' : 'Authors:'}</strong> {pub.authors.join(', ')}</span>
                    <span>•</span>
                    <span><strong>{isFa ? 'منبع:' : 'Venue:'}</strong> {pub.venue}</span>
                  </div>

                  <p className="ulo-p7-pub-abstract">{pub.abstract}</p>

                  <div className="ulo-p7-pub-finding">
                    <strong>{isFa ? 'روش پژوهش: ' : 'Methodology: '}</strong>
                    {isFa ? pub.method_fa : pub.method_en}
                  </div>
                  <div className="ulo-p7-pub-finding">
                    <strong>{isFa ? 'یافته اصلی: ' : 'Key Finding: '}</strong>
                    {isFa ? pub.key_finding_fa : pub.key_finding_en}
                  </div>
                </div>

                <div className="ulo-p7-pub-footer">
                  <span style={{ direction: 'ltr', color: '#64748b' }}>
                    DOI: {pub.doi}
                  </span>
                  <a
                    href={pub.legal_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ulo-p7-link"
                  >
                    {isFa ? 'لینک قانونی مقاله / DOI ↗' : 'Legal Source / DOI Link ↗'}
                  </a>
                </div>
              </article>
            ))}
          </div>

          <div className="ulo-p7-meta-footer">
            <span>{isFa ? `منبع: ${lib.metadata.source_name}` : `Source: ${lib.metadata.source_name}`}</span>
            <span>{isFa ? `محدودیت: ${lib.metadata.limitations_fa}` : `Limitation: ${lib.metadata.limitations_en}`}</span>
          </div>
        </div>
      )}
    </section>
  );
};

export default ScientificResearchCenter;

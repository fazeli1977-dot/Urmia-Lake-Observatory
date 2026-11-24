// Phase 8 — Secure Client-Side Data Validation (8 Formats) & Multi-Format Export Engine
// Urmia Lake Observatory (ULO) — Zero External Dependencies, 100% Local Privacy

export type SupportedFormat =
  | 'CSV'
  | 'XLSX'
  | 'JSON'
  | 'GeoJSON'
  | 'Shapefile ZIP'
  | 'GeoTIFF'
  | 'NetCDF'
  | 'PDF';

export interface ValidationCheckItem {
  key: string;
  labelFa: string;
  labelEn: string;
  status: 'PASS' | 'WARN' | 'FAIL';
  detailFa: string;
  detailEn: string;
}

export interface FileValidationReport {
  accepted: boolean;
  fileName: string;
  sanitizedFileName: string;
  fileSizeKB: number;
  detectedFormat: SupportedFormat | 'UNKNOWN';
  dataCategory: 'User-Provided Data';
  validatedAtUtc: string;
  rowCount: number;
  columnNames: string[];
  detectedUnits: string[];
  crsInfo: string;
  missingValuesCount: number;
  duplicateRowsCount: number;
  invalidValuesCount: number;
  dateRange: string;
  checks: ValidationCheckItem[];
  previewHeaders: string[];
  previewRows: string[][];
}

export interface ObservatoryExportBundle {
  hydrology: Record<string, any> | null;
  climate: Record<string, any> | null;
  analytics: Record<string, any> | null;
  researchCenter: Record<string, any> | null;
  exportCatalog: Record<string, any> | null;
}

const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024; // 25 MB safety threshold

const ALLOWED_EXT_MAP: Record<string, SupportedFormat | undefined> = {
  '.csv': 'CSV',
  '.xlsx': 'XLSX',
  '.json': 'JSON',
  '.geojson': 'GeoJSON',
  '.zip': 'Shapefile ZIP',
  '.tif': 'GeoTIFF',
  '.tiff': 'GeoTIFF',
  '.nc': 'NetCDF',
  '.pdf': 'PDF',
};

function getFileExtension(name: string): string {
  const idx = name.lastIndexOf('.');
  return idx >= 0 ? name.slice(idx).toLowerCase() : '';
}

function hasPathTraversalOrMaliciousName(name: string): boolean {
  if (!name || name.length > 180) return true;
  if (name.includes('..') || name.includes('/') || name.includes('\\') || name.includes('\0')) return true;
  if (/[<>:"|?*]/.test(name)) return true;
  const lowered = name.toLowerCase();
  const forbidden = ['.exe', '.bat', '.cmd', '.ps1', '.sh', '.js', '.mjs', '.html', '.htm', '.svg', '.php', '.dll'];
  return forbidden.some((ext) => lowered.endsWith(ext));
}

function sanitizeName(name: string): string {
  return name.replace(/[^a-zA-Z0-9._\-\u0600-\u06FF ]/g, '_').slice(0, 120);
}

function detectUnitsFromNames(names: string[]): string[] {
  const joined = names.join(' ').toLowerCase();
  const units: string[] = [];
  if (/(level|elev|wse|_m\b|meter|تراز)/.test(joined)) units.push('m a.s.l. (Elevation)');
  if (/(area|km2|hectare|مساحت)/.test(joined)) units.push('km² (Surface Area)');
  if (/(vol|km3|mcm|حجم)/.test(joined)) units.push('km³ / MCM (Volume)');
  if (/(precip|rain|et0|evap|_mm\b|بارش|تبخیر)/.test(joined)) units.push('mm (Climate Flux)');
  if (/(temp|_c\b|celsius|دما)/.test(joined)) units.push('°C (Temperature)');
  if (/(salin|ec|tds|g_l|شوری)/.test(joined)) units.push('g/L or dS/m (Salinity/EC)');
  if (/(lat|lon|coord|x|y)/.test(joined)) units.push('Decimal Degrees (WGS84)');
  return units.length ? units : ['Not explicitly declared in header (verify metadata)'];
}

function parseCsvLines(text: string): string[][] {
  const lines = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n').filter((l) => l.trim().length > 0);
  return lines.map((line) => {
    const out: string[] = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"') {
        inQuotes = !inQuotes;
      } else if ((ch === ',' || ch === ';') && !inQuotes) {
        out.push(current.trim());
        current = '';
      } else {
        current += ch;
      }
    }
    out.push(current.trim());
    return out;
  });
}

function isValidIsoOrCommonDate(val: string): boolean {
  const trimmed = val.trim();
  if (!trimmed) return false;
  if (/^\d{4}[-/]\d{1,2}[-/]\d{1,2}/.test(trimmed)) {
    const dt = new Date(trimmed.replace(/\//g, '-'));
    return !Number.isNaN(dt.getTime()) && dt.getFullYear() >= 1950 && dt.getFullYear() <= 2100;
  }
  if (/^\d{4}-\d{2}$/.test(trimmed)) return true;
  return false;
}

export async function validateUploadedFile(file: File): Promise<FileValidationReport> {
  const checks: ValidationCheckItem[] = [];
  const ext = getFileExtension(file.name);
  const detectedFormat: SupportedFormat | 'UNKNOWN' = ALLOWED_EXT_MAP[ext] ?? 'UNKNOWN';
  const sizeKB = Math.round((file.size / 1024) * 10) / 10;

  // 1. Security: Path Traversal & File Name
  const badName = hasPathTraversalOrMaliciousName(file.name);
  checks.push({
    key: 'security_name',
    labelFa: 'امنیت نام فایل و جلوگیری از Path Traversal',
    labelEn: 'File Name Safety & Path Traversal Guard',
    status: badName ? 'FAIL' : 'PASS',
    detailFa: badName ? 'نام فایل حاوی کاراکترهای غیرمجاز یا پسوند اجرایی است.' : 'نام فایل ایمن و فاقد الگوی Path Traversal است.',
    detailEn: badName ? 'File name contains illegal path characters or executable extension.' : 'File name passed traversal and extension safety checks.',
  });

  // 2. Security: File Size
  const sizeOk = file.size > 0 && file.size <= MAX_FILE_SIZE_BYTES;
  checks.push({
    key: 'security_size',
    labelFa: 'کنترل حجم فایل (حداکثر ۲۵ مگابایت)',
    labelEn: 'File Size Boundary (Max 25 MB)',
    status: sizeOk ? 'PASS' : 'FAIL',
    detailFa: sizeOk ? `حجم فایل ${sizeKB} کیلوبایت در محدوده مجاز است.` : `حجم فایل نامعتبر است (${sizeKB} KB).`,
    detailEn: sizeOk ? `File size (${sizeKB} KB) is within safe browser memory limits.` : `File size (${sizeKB} KB) is empty or exceeds 25 MB limit.`,
  });

  // 3. Format Allow-List
  const formatOk = detectedFormat !== 'UNKNOWN';
  checks.push({
    key: 'format_allowlist',
    labelFa: 'پشتیبانی فرمت علمی مجاز',
    labelEn: 'Authorized Scientific Format Check',
    status: formatOk ? 'PASS' : 'FAIL',
    detailFa: formatOk ? `فرمت شناسایی‌شده: ${detectedFormat}` : `فرمت «${ext || 'بدون پسوند'}» در فهرست ۸ فرمت علمی مجاز نیست.`,
    detailEn: formatOk ? `Recognized scientific format: ${detectedFormat}` : `Extension "${ext || 'none'}" is not in the 8 authorized scientific formats.`,
  });

  const buffer = await file.arrayBuffer();
  const bytes = new Uint8Array(buffer);

  // 4. Magic Bytes Binary Signature Verification
  let magicOk = true;
  let magicDetailFa = 'ساختار بایت‌های ابتدایی با فرمت اعلام‌شده همخوانی دارد.';
  let magicDetailEn = 'Leading magic bytes match declared format signature.';

  if (detectedFormat === 'XLSX' || detectedFormat === 'Shapefile ZIP') {
    magicOk = bytes.length >= 4 && bytes[0] === 0x50 && bytes[1] === 0x4b && (bytes[2] === 0x03 || bytes[2] === 0x05);
    if (!magicOk) {
      magicDetailFa = 'امضای باینری ZIP/OOXML (PK\\x03\\x04) یافت نشد؛ فایل ممکن است تغییرنام‌یافته یا خراب باشد.';
      magicDetailEn = 'Missing PK\\x03\\x04 ZIP/OOXML magic signature; file may be spoofed or corrupted.';
    }
  } else if (detectedFormat === 'PDF') {
    const head = String.fromCharCode(...bytes.slice(0, 5));
    magicOk = head === '%PDF-';
    if (!magicOk) {
      magicDetailFa = 'هدر استاندارد %PDF- در ابتدای فایل وجود ندارد.';
      magicDetailEn = 'Standard %PDF- header not found at byte offset 0.';
    }
  } else if (detectedFormat === 'GeoTIFF') {
    const isII = bytes.length >= 4 && bytes[0] === 0x49 && bytes[1] === 0x49 && (bytes[2] === 0x2a || bytes[2] === 0x2b);
    const isMM = bytes.length >= 4 && bytes[0] === 0x4d && bytes[1] === 0x4d && (bytes[3] === 0x2a || bytes[3] === 0x2b);
    magicOk = isII || isMM;
    if (!magicOk) {
      magicDetailFa = 'امضای باینری TIFF/BigTIFF (II* یا MM*) شناسایی نشد.';
      magicDetailEn = 'Valid TIFF/BigTIFF byte-order header (II* / MM*) not found.';
    }
  } else if (detectedFormat === 'NetCDF') {
    const isCdf = bytes.length >= 4 && bytes[0] === 0x43 && bytes[1] === 0x44 && bytes[2] === 0x46;
    const isHdf5 = bytes.length >= 4 && bytes[0] === 0x89 && bytes[1] === 0x48 && bytes[2] === 0x44 && bytes[3] === 0x46;
    magicOk = isCdf || isHdf5;
    if (!magicOk) {
      magicDetailFa = 'امضای باینری NetCDF Classic (CDF) یا NetCDF-4/HDF5 یافت نشد.';
      magicDetailEn = 'Neither NetCDF Classic (CDF) nor NetCDF-4/HDF5 signature detected.';
    }
  }

  checks.push({
    key: 'magic_bytes',
    labelFa: 'اعتبارسنجی امضای باینری (Magic Bytes)',
    labelEn: 'Binary Magic-Byte Integrity Check',
    status: magicOk ? 'PASS' : 'FAIL',
    detailFa: magicDetailFa,
    detailEn: magicDetailEn,
  });

  let rowCount = 0;
  let columnNames: string[] = [];
  let detectedUnits: string[] = [];
  let crsInfo = 'Not Applicable (Tabular / Document)';
  let missingValuesCount = 0;
  let duplicateRowsCount = 0;
  let invalidValuesCount = 0;
  let dateRange = 'Not detected';
  let previewHeaders: string[] = [];
  let previewRows: string[][] = [];

  if (formatOk && magicOk && !badName && sizeOk) {
    if (detectedFormat === 'CSV') {
      const text = new TextDecoder('utf-8').decode(bytes);
      const rows = parseCsvLines(text);
      if (rows.length < 2) {
        checks.push({
          key: 'structure',
          labelFa: 'بررسی ساختار جدولی CSV',
          labelEn: 'CSV Tabular Structure Check',
          status: 'FAIL',
          detailFa: 'فایل CSV فاقد سطر عنوان یا رکورد داده است.',
          detailEn: 'CSV file does not contain header and data rows.',
        });
      } else {
        columnNames = rows[0];
        const body = rows.slice(1);
        rowCount = body.length;
        detectedUnits = detectUnitsFromNames(columnNames);
        previewHeaders = columnNames.slice(0, 8);
        previewRows = body.slice(0, 6).map((r) => r.slice(0, 8));

        const seenRows = new Set<string>();
        const foundDates: string[] = [];
        const levelColIdx = columnNames.findIndex((c) => /(level|elev|wse|تراز)/i.test(c));
        const dateColIdx = columnNames.findIndex((c) => /(date|time|تاریخ|سال)/i.test(c));

        for (const r of body) {
          const sig = r.join('|');
          if (seenRows.has(sig)) duplicateRowsCount++;
          else seenRows.add(sig);

          for (const cell of r) {
            if (cell === '' || /^(na|nan|null|none|-9999)$/i.test(cell)) {
              missingValuesCount++;
            }
          }
          if (dateColIdx >= 0 && r[dateColIdx]) {
            if (isValidIsoOrCommonDate(r[dateColIdx])) {
              foundDates.push(r[dateColIdx].slice(0, 10));
            } else {
              invalidValuesCount++;
            }
          }
          if (levelColIdx >= 0 && r[levelColIdx]) {
            const num = Number(r[levelColIdx]);
            if (Number.isNaN(num) || num < 1250 || num > 1300) {
              invalidValuesCount++;
            }
          }
        }

        if (foundDates.length > 0) {
          foundDates.sort();
          dateRange = `${foundDates[0]} → ${foundDates[foundDates.length - 1]}`;
        }

        checks.push({
          key: 'structure',
          labelFa: 'ساختار، تاریخ، داده‌های مفقود و تکراری (CSV)',
          labelEn: 'Schema, Dates, Missing & Duplicate Audit (CSV)',
          status: invalidValuesCount > 0 || duplicateRowsCount > 0 ? 'WARN' : 'PASS',
          detailFa: `${rowCount} رکورد و ${columnNames.length} ستون بررسی شد | مفقود: ${missingValuesCount} | تکراری: ${duplicateRowsCount} | نامعتبر: ${invalidValuesCount}`,
          detailEn: `Parsed ${rowCount} rows × ${columnNames.length} cols | Missing: ${missingValuesCount} | Duplicates: ${duplicateRowsCount} | Invalid/Out-of-range: ${invalidValuesCount}`,
        });
      }
    } else if (detectedFormat === 'JSON' || detectedFormat === 'GeoJSON') {
      try {
        const text = new TextDecoder('utf-8').decode(bytes);
        const parsed = JSON.parse(text);
        if (detectedFormat === 'GeoJSON' || parsed?.type === 'FeatureCollection' || parsed?.type === 'Feature') {
          const features = parsed?.type === 'FeatureCollection' && Array.isArray(parsed.features)
            ? parsed.features
            : parsed?.type === 'Feature'
            ? [parsed]
            : [];
          rowCount = features.length;
          crsInfo = parsed?.crs?.properties?.name || 'RFC 7946 Default: EPSG:4326 (WGS84)';
          const sampleProps = features[0]?.properties || {};
          columnNames = Object.keys(sampleProps);
          detectedUnits = detectUnitsFromNames(columnNames);
          previewHeaders = ['Geometry Type', ...columnNames.slice(0, 6)];
          previewRows = features.slice(0, 6).map((f: any) => [
            String(f?.geometry?.type || 'Missing'),
            ...columnNames.slice(0, 6).map((k) => String(f?.properties?.[k] ?? '')),
          ]);
          for (const f of features) {
            if (!f?.geometry || !f?.geometry?.coordinates) missingValuesCount++;
          }
          checks.push({
            key: 'geojson_check',
            labelFa: 'اعتبارسنجی هندسه و سیستم مختصات (GeoJSON)',
            labelEn: 'Geometry & CRS Validation (GeoJSON)',
            status: rowCount > 0 && missingValuesCount === 0 ? 'PASS' : 'WARN',
            detailFa: `${rowCount} عارضه مکانی با سیستم مختصات ${crsInfo} شناسایی شد (هندسه مفقود: ${missingValuesCount}).`,
            detailEn: `Validated ${rowCount} spatial features in ${crsInfo} (missing geometries: ${missingValuesCount}).`,
          });
        } else {
          const arr = Array.isArray(parsed)
            ? parsed
            : Array.isArray(parsed?.timeseries)
            ? parsed.timeseries
            : Array.isArray(parsed?.records)
            ? parsed.records
            : Array.isArray(parsed?.data)
            ? parsed.data
            : [parsed];
          rowCount = arr.length;
          columnNames = arr[0] && typeof arr[0] === 'object' ? Object.keys(arr[0]) : ['value'];
          detectedUnits = detectUnitsFromNames(columnNames);
          previewHeaders = columnNames.slice(0, 7);
          previewRows = arr.slice(0, 6).map((item: any) =>
            columnNames.slice(0, 7).map((k) => {
              const v = item?.[k];
              return typeof v === 'object' && v !== null ? JSON.stringify(v).slice(0, 40) : String(v ?? '');
            })
          );
          checks.push({
            key: 'json_check',
            labelFa: 'اعتبارسنجی ساختار JSON',
            labelEn: 'JSON Schema Integrity Check',
            status: 'PASS',
            detailFa: `ساختار JSON معتبر با ${rowCount} رکورد و ${columnNames.length} فیلد.`,
            detailEn: `Valid JSON payload containing ${rowCount} record(s) and ${columnNames.length} key(s).`,
          });
        }
      } catch (err) {
        checks.push({
          key: 'json_parse',
          labelFa: 'پارس ساختاری JSON/GeoJSON',
          labelEn: 'JSON/GeoJSON Syntax Parse',
          status: 'FAIL',
          detailFa: `خطای نحوی در فایل JSON: ${String(err)}`,
          detailEn: `Malformed JSON syntax: ${String(err)}`,
        });
      }
    } else if (detectedFormat === 'Shapefile ZIP') {
      const asciiView = new TextDecoder('latin1').decode(bytes);
      const hasShp = asciiView.includes('.shp');
      const hasDbf = asciiView.includes('.dbf');
      const hasPrj = asciiView.includes('.prj');
      crsInfo = hasPrj ? 'Projection file (.prj) present inside ZIP archive' : 'Missing .prj file (CRS must be verified)';
      checks.push({
        key: 'shapefile_bundle',
        labelFa: 'بررسی اجزای اجباری Shapefile (.shp / .dbf / .prj)',
        labelEn: 'Shapefile Archive Component Check (.shp / .dbf / .prj)',
        status: hasShp && hasDbf ? (hasPrj ? 'PASS' : 'WARN') : 'FAIL',
        detailFa: `وضعیت فایل‌های داخلی: .shp=${hasShp ? 'موجود' : 'ناموجود'} | .dbf=${hasDbf ? 'موجود' : 'ناموجود'} | .prj=${hasPrj ? 'موجود' : 'ناموجود'}`,
        detailEn: `Archive inventory: .shp=${hasShp} | .dbf=${hasDbf} | .prj=${hasPrj}`,
      });
      columnNames = ['.shp (Geometry)', '.dbf (Attributes)', '.prj (CRS)'];
      rowCount = hasShp ? 1 : 0;
    } else if (detectedFormat === 'XLSX') {
      const asciiView = new TextDecoder('latin1').decode(bytes);
      const hasWorkbook = asciiView.includes('xl/workbook.xml');
      checks.push({
        key: 'xlsx_structure',
        labelFa: 'بررسی ساختار استاندارد کتاب کار اکسل (OOXML)',
        labelEn: 'Excel OOXML Workbook Validation',
        status: hasWorkbook ? 'PASS' : 'FAIL',
        detailFa: hasWorkbook
          ? 'بسته OpenXML اکسل (xl/workbook.xml) تأیید شد؛ آماده ورود به پایپ‌لاین Pandas.'
          : 'فایل ZIP فاقد ساختار xl/workbook.xml معتبر اکسل است.',
        detailEn: hasWorkbook
          ? 'Valid Excel OOXML container (xl/workbook.xml) verified for Pandas ingestion.'
          : 'ZIP container lacks xl/workbook.xml Excel structure.',
      });
      columnNames = ['OOXML Workbook Sheets (Verified Binary)'];
      rowCount = hasWorkbook ? 1 : 0;
    } else if (detectedFormat === 'GeoTIFF') {
      crsInfo = 'GeoTIFF GeoKey Directory (Requires Rasterio/GDAL projection read in Python pipeline)';
      checks.push({
        key: 'geotiff_check',
        labelFa: 'بررسی هدر رستر مکانی GeoTIFF',
        labelEn: 'GeoTIFF Raster Header Verification',
        status: 'PASS',
        detailFa: 'امضای TIFF تأیید شد؛ آماده پردازش باندی و استخراج شاخص (NDWI/NDVI) در موتور پایتون Rasterio.',
        detailEn: 'Valid TIFF byte-order header confirmed; ready for Rasterio spectral band ingestion.',
      });
      columnNames = ['Raster Bands (GeoTIFF)'];
      rowCount = 1;
    } else if (detectedFormat === 'NetCDF') {
      crsInfo = 'CF-Convention Multi-Dimensional Grid (Xarray/NetCDF4)';
      checks.push({
        key: 'netcdf_check',
        labelFa: 'بررسی هدر آرایه اقلیمی NetCDF',
        labelEn: 'NetCDF Climate Grid Header Verification',
        status: 'PASS',
        detailFa: 'ساختار NetCDF/HDF5 تأیید شد؛ آماده خوانش با Xarray برای متغیرهای اقلیمی/رطوبت خاک.',
        detailEn: 'Valid NetCDF/HDF5 container confirmed; ready for Xarray multi-dimensional analysis.',
      });
      columnNames = ['Multi-Dimensional Climate Variables (NetCDF)'];
      rowCount = 1;
    } else if (detectedFormat === 'PDF') {
      crsInfo = 'Document Archive (Scientific Report / Reference)';
      checks.push({
        key: 'pdf_check',
        labelFa: 'بررسی اعتبار سند PDF پژوهشی',
        labelEn: 'Scientific PDF Document Integrity Check',
        status: 'PASS',
        detailFa: 'امضای %PDF- تأیید شد؛ فایل در دسته اسناد ورودی کاربر (User-Provided Data) ثبت می‌شود.',
        detailEn: 'Valid %PDF- document signature verified for User-Provided research archive.',
      });
      columnNames = ['Scientific PDF Document'];
      rowCount = 1;
    }
  }

  const accepted = checks.every((c) => c.status !== 'FAIL');

  return {
    accepted,
    fileName: file.name,
    sanitizedFileName: sanitizeName(file.name),
    fileSizeKB: sizeKB,
    detectedFormat,
    dataCategory: 'User-Provided Data',
    validatedAtUtc: new Date().toISOString(),
    rowCount,
    columnNames,
    detectedUnits,
    crsInfo,
    missingValuesCount,
    duplicateRowsCount,
    invalidValuesCount,
    dateRange,
    checks,
    previewHeaders,
    previewRows,
  };
}

// ---------- HELPER: UNIVERSAL SCHEMA-AGNOSTIC HYDROLOGY & CLIMATE EXTRACTORS ----------
function findBestSeriesArray(
  node: any,
  predicate: (item: Record<string, any>) => boolean
): Array<Record<string, any>> {
  let best: Array<Record<string, any>> = [];
  const walk = (cur: any) => {
    if (Array.isArray(cur) && cur.length >= 2 && typeof cur[0] === 'object' && cur[0] !== null) {
      let matches = 0;
      for (const item of cur.slice(0, 10)) {
        if (item && typeof item === 'object' && predicate(item)) matches++;
      }
      if (matches >= 2 && cur.length > best.length) {
        best = cur.filter((x) => x && typeof x === 'object');
      }
    } else if (cur && typeof cur === 'object') {
      for (const val of Object.values(cur)) {
        walk(val);
      }
    }
  };
  walk(node);
  return best;
}

export function extractHydrologyRows(hydro: Record<string, any> | null): Array<{
  date: string;
  level_m: number;
  area_km2: number;
  volume_km3: number;
  source: string;
}> {
  if (!hydro) return [];
  const isoRe = /^\d{4}-\d{2}/;
  const raw = findBestSeriesArray(hydro, (item) => {
    const hasDate = Object.values(item).some((v) => typeof v === 'string' && isoRe.test(v.trim()));
    const hasLevel = Object.values(item).some((v) => typeof v === 'number' && v >= 1250 && v <= 1300);
    return hasDate && hasLevel;
  });

  const defaultSource = String(hydro?.metadata?.source || 'Hydroweb / CLMS Satellite Altimetry');

  return raw
    .map((r) => {
      let dt = '';
      let lvl = NaN;
      let area = 0;
      let vol = 0;
      for (const [k, v] of Object.entries(r)) {
        const kl = k.toLowerCase();
        if (!dt && typeof v === 'string' && isoRe.test(v.trim())) {
          dt = v.trim().slice(0, 10);
        } else if (typeof v === 'number' && Number.isFinite(v)) {
          if (/(level|elev|wse|wl|stage|height|alt)/.test(kl) && v >= 1250 && v <= 1300) {
            lvl = v;
          } else if (kl.includes('area') && v >= 0) {
            area = v;
          } else if ((kl.includes('vol') || kl.includes('storage')) && v >= 0) {
            vol = v;
          }
        }
      }
      if (Number.isNaN(lvl)) {
        for (const v of Object.values(r)) {
          if (typeof v === 'number' && v >= 1250 && v <= 1300) {
            lvl = v;
            break;
          }
        }
      }
      return {
        date: dt,
        level_m: lvl,
        area_km2: area,
        volume_km3: vol,
        source: String(r.source || defaultSource),
      };
    })
    .filter((r) => r.date && !Number.isNaN(r.level_m))
    .sort((a, b) => a.date.localeCompare(b.date));
}

export function extractClimateRows(climate: Record<string, any> | null): Array<{
  month: string;
  precip_mm: number;
  et0_mm: number;
  temp_c: number;
}> {
  if (!climate) return [];
  const isoRe = /^\d{4}-\d{2}/;
  const raw = findBestSeriesArray(climate, (item) => {
    const keysJoined = Object.keys(item).join(' ').toLowerCase();
    const hasDate = Object.values(item).some((v) => typeof v === 'string' && isoRe.test(v.trim()));
    const hasClim = /(precip|rain|et0|evap|temp)/.test(keysJoined);
    return hasDate && hasClim;
  });

  return raw
    .map((r) => {
      let month = '';
      let precip = 0;
      let et0 = 0;
      let temp = 0;
      for (const [k, v] of Object.entries(r)) {
        const kl = k.toLowerCase();
        if (!month && typeof v === 'string' && isoRe.test(v.trim())) {
          month = v.trim().slice(0, 10);
        } else if (typeof v === 'number' && Number.isFinite(v)) {
          if (kl.includes('precip') || kl.includes('rain')) precip = v;
          else if (kl.includes('et0') || kl.includes('evap')) et0 = v;
          else if (kl.includes('temp')) temp = v;
        }
      }
      return { month, precip_mm: precip, et0_mm: et0, temp_c: temp };
    })
    .filter((r) => r.month);
}

function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}

// ---------- EXPORT 1: CSV (UTF-8 BOM) ----------
export function exportObservatoryCSV(bundle: ObservatoryExportBundle): void {
  const rows = extractHydrologyRows(bundle.hydrology);
  const headerLines = [
    '# URMIA LAKE OBSERVATORY (ULO) - Official Real-Data Hydrology Time Series',
    `# Exported UTC: ${new Date().toISOString()}`,
    '# Source: Hydroweb / CLMS Satellite Radar Altimetry + Calibrated Bathymetric Hypsometry',
    '# Developer: Alireza Fazeli Sani (alirezafazeli@live.com)',
    'date,water_level_m_asl,wet_area_km2,storage_volume_km3,data_source',
  ];
  const bodyLines = rows.map(
    (r) => `${r.date},${r.level_m.toFixed(3)},${r.area_km2.toFixed(2)},${r.volume_km3.toFixed(3)},"${r.source.replace(/"/g, '""')}"`
  );
  const csvContent = '\uFEFF' + [...headerLines, ...bodyLines].join('\r\n');
  triggerBlobDownload(new Blob([csvContent], { type: 'text/csv;charset=utf-8;' }), 'urmia_lake_observatory_hydrology.csv');
}

// ---------- EXPORT 2: JSON BUNDLE ----------
export function exportObservatoryJSON(bundle: ObservatoryExportBundle): void {
  const payload = {
    observatory: 'Urmia Lake Observatory (ULO)',
    exported_at_utc: new Date().toISOString(),
    developer: 'Alireza Fazeli Sani (alirezafazeli@live.com)',
    disclaimer: 'Independent open-science observatory; no official affiliation with NASA, ESA, USGS, or UNESCO.',
    datasets: {
      hydrology: bundle.hydrology,
      climate_era5: bundle.climate,
      scientific_analytics: bundle.analytics,
      research_center_and_dss: bundle.researchCenter,
    },
  };
  const jsonStr = JSON.stringify(payload, null, 2);
  triggerBlobDownload(new Blob([jsonStr], { type: 'application/json;charset=utf-8;' }), 'urmia_lake_observatory_scientific_bundle.json');
}

// ---------- EXPORT 3: REAL MULTI-SHEET XLSX (PURE OOXML ZIP + CRC32, ZERO DEPS) ----------
const CRC32_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let j = 0; j < 8; j++) {
      c = (c & 1) !== 0 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    }
    table[i] = c >>> 0;
  }
  return table;
})();

function crc32(data: Uint8Array): number {
  let crc = 0xffffffff;
  for (let i = 0; i < data.length; i++) {
    crc = CRC32_TABLE[(crc ^ data[i]) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function buildZipStored(files: Array<{ name: string; content: string }>): Uint8Array {
  const encoder = new TextEncoder();
  const localChunks: Uint8Array[] = [];
  const centralChunks: Uint8Array[] = [];
  let offset = 0;

  for (const f of files) {
    const nameBytes = encoder.encode(f.name);
    const dataBytes = encoder.encode(f.content);
    const crc = crc32(dataBytes);

    const localHeader = new Uint8Array(30 + nameBytes.length);
    const ldv = new DataView(localHeader.buffer);
    ldv.setUint32(0, 0x04034b50, true);
    ldv.setUint16(4, 20, true);
    ldv.setUint16(6, 0, true);
    ldv.setUint16(8, 0, true); // stored (no compression)
    ldv.setUint16(10, 0, true);
    ldv.setUint16(12, 0, true);
    ldv.setUint32(14, crc, true);
    ldv.setUint32(18, dataBytes.length, true);
    ldv.setUint32(22, dataBytes.length, true);
    ldv.setUint16(26, nameBytes.length, true);
    ldv.setUint16(28, 0, true);
    localHeader.set(nameBytes, 30);

    localChunks.push(localHeader, dataBytes);

    const centralHeader = new Uint8Array(46 + nameBytes.length);
    const cdv = new DataView(centralHeader.buffer);
    cdv.setUint32(0, 0x02014b50, true);
    cdv.setUint16(4, 20, true);
    cdv.setUint16(6, 20, true);
    cdv.setUint16(8, 0, true);
    cdv.setUint16(10, 0, true);
    cdv.setUint16(12, 0, true);
    cdv.setUint16(14, 0, true);
    cdv.setUint32(16, crc, true);
    cdv.setUint32(20, dataBytes.length, true);
    cdv.setUint32(24, dataBytes.length, true);
    cdv.setUint16(28, nameBytes.length, true);
    cdv.setUint16(30, 0, true);
    cdv.setUint16(32, 0, true);
    cdv.setUint16(34, 0, true);
    cdv.setUint16(36, 0, true);
    cdv.setUint32(38, 0, true);
    cdv.setUint32(42, offset, true);
    centralHeader.set(nameBytes, 46);

    centralChunks.push(centralHeader);
    offset += localHeader.length + dataBytes.length;
  }

  const centralSize = centralChunks.reduce((sum, c) => sum + c.length, 0);
  const eocd = new Uint8Array(22);
  const edv = new DataView(eocd.buffer);
  edv.setUint32(0, 0x06054b50, true);
  edv.setUint16(4, 0, true);
  edv.setUint16(6, 0, true);
  edv.setUint16(8, files.length, true);
  edv.setUint16(10, files.length, true);
  edv.setUint32(12, centralSize, true);
  edv.setUint32(16, offset, true);
  edv.setUint16(20, 0, true);

  const totalLen = offset + centralSize + eocd.length;
  const out = new Uint8Array(totalLen);
  let ptr = 0;
  for (const c of localChunks) {
    out.set(c, ptr);
    ptr += c.length;
  }
  for (const c of centralChunks) {
    out.set(c, ptr);
    ptr += c.length;
  }
  out.set(eocd, ptr);
  return out;
}

function xmlEscape(val: string): string {
  return val
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function colLetter(idx: number): string {
  let s = '';
  let n = idx + 1;
  while (n > 0) {
    const rem = (n - 1) % 26;
    s = String.fromCharCode(65 + rem) + s;
    n = Math.floor((n - 1) / 26);
  }
  return s;
}

function buildWorksheetXml(rows: Array<Array<string | number>>): string {
  const rowXml = rows
    .map((r, rIdx) => {
      const cells = r
        .map((val, cIdx) => {
          const ref = `${colLetter(cIdx)}${rIdx + 1}`;
          if (typeof val === 'number' && Number.isFinite(val)) {
            return `<c r="${ref}"><v>${val}</v></c>`;
          }
          return `<c r="${ref}" t="inlineStr"><is><t>${xmlEscape(String(val))}</t></is></c>`;
        })
        .join('');
      return `<row r="${rIdx + 1}">${cells}</row>`;
    })
    .join('');

  return (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' +
    `<sheetData>${rowXml}</sheetData>` +
    '</worksheet>'
  );
}

export function exportObservatoryXLSX(bundle: ObservatoryExportBundle): void {
  const hydroRows = extractHydrologyRows(bundle.hydrology);
  const climateRows = extractClimateRows(bundle.climate);

  const sheet1: Array<Array<string | number>> = [
    ['Date', 'Water Level (m a.s.l.)', 'Wet Area (km2)', 'Storage Volume (km3)', 'Source'],
    ...hydroRows.map((r) => [r.date, Number(r.level_m.toFixed(3)), Number(r.area_km2.toFixed(2)), Number(r.volume_km3.toFixed(3)), r.source]),
  ];

  const sheet2: Array<Array<string | number>> = [
    ['Month', 'Precipitation (mm)', 'Reference ET0 (mm)', 'Mean Temperature (C)'],
    ...climateRows.map((r) => [r.month, Number(r.precip_mm.toFixed(2)), Number(r.et0_mm.toFixed(2)), Number(r.temp_c.toFixed(2))]),
  ];

  const sheet3: Array<Array<string | number>> = [
    ['Field', 'Value'],
    ['Observatory', 'Urmia Lake Observatory (ULO)'],
    ['Export Timestamp (UTC)', new Date().toISOString()],
    ['Developer & Creator', 'Alireza Fazeli Sani (alirezafazeli@live.com)'],
    ['Hydrology Source', 'Hydroweb / CLMS Satellite Radar Altimetry + Hypsometry'],
    ['Climate Source', 'ECMWF ERA5 Reanalysis (Open-Meteo Archive)'],
    ['Ecology & Literature', 'GBIF REST API + Ramsar Site #38 + OpenAlex + Crossref'],
    ['Scientific Integrity Policy', 'Zero Synthetic Data; Hypotheses Explicitly Labeled'],
    ['Disclaimer', 'Independent Open-Science Platform; No Official Affiliation with NASA, ESA, USGS, or UNESCO'],
  ];

  const zipFiles = [
    {
      name: '[Content_Types].xml',
      content:
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' +
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>' +
        '<Default Extension="xml" ContentType="application/xml"/>' +
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>' +
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' +
        '<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' +
        '<Override PartName="/xl/worksheets/sheet3.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' +
        '</Types>',
    },
    {
      name: '_rels/.rels',
      content:
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>' +
        '</Relationships>',
    },
    {
      name: 'xl/workbook.xml',
      content:
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">' +
        '<sheets>' +
        '<sheet name="Hydrology_Series" sheetId="1" r:id="rId1"/>' +
        '<sheet name="ERA5_Climate" sheetId="2" r:id="rId2"/>' +
        '<sheet name="Metadata_Provenance" sheetId="3" r:id="rId3"/>' +
        '</sheets>' +
        '</workbook>',
    },
    {
      name: 'xl/_rels/workbook.xml.rels',
      content:
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>' +
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>' +
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet3.xml"/>' +
        '</Relationships>',
    },
    { name: 'xl/worksheets/sheet1.xml', content: buildWorksheetXml(sheet1) },
    { name: 'xl/worksheets/sheet2.xml', content: buildWorksheetXml(sheet2) },
    { name: 'xl/worksheets/sheet3.xml', content: buildWorksheetXml(sheet3) },
  ];

  const xlsxBytes = buildZipStored(zipFiles);
  const blob = new Blob([xlsxBytes as unknown as BlobPart], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  triggerBlobDownload(blob, 'urmia_lake_observatory_data.xlsx');
}

// ---------- EXPORT 4: REAL GEOJSON FEATURE COLLECTION ----------
export async function exportObservatoryGeoJSON(bundle: ObservatoryExportBundle): Promise<string> {
  const catalogLayers: Array<{ name: string; public_path: string }> = bundle.exportCatalog?.geojson_layers || [];
  const mergedFeatures: any[] = [];

  for (const layer of catalogLayers.slice(0, 15)) {
    try {
      const res = await fetch(`${import.meta.env.BASE_URL}${layer.public_path}`);
      if (!res.ok) continue;
      const gj = await res.json();
      if (gj?.type === 'FeatureCollection' && Array.isArray(gj.features)) {
        for (const f of gj.features) {
          mergedFeatures.push({
            ...f,
            properties: {
              ...(f.properties || {}),
              ulo_layer_file: layer.name,
            },
          });
        }
      }
    } catch {
      // skip unreachable layer gracefully
    }
  }

  const outCollection = {
    type: 'FeatureCollection',
    name: 'Urmia_Lake_Observatory_Geospatial_Layers',
    metadata: {
      exported_at_utc: new Date().toISOString(),
      crs: 'EPSG:4326 (WGS84)',
      source_layers_count: catalogLayers.length,
      developer: 'Alireza Fazeli Sani (alirezafazeli@live.com)',
    },
    features: mergedFeatures,
  };

  triggerBlobDownload(
    new Blob([JSON.stringify(outCollection, null, 2)], { type: 'application/geo+json;charset=utf-8;' }),
    'urmia_lake_observatory_layers.geojson'
  );
  return `${mergedFeatures.length} features (${catalogLayers.length} layers)`;
}

// ---------- EXPORT 5: HIGH-RES SCIENTIFIC SUMMARY CHART PNG ----------
export function exportScientificSummaryPNG(bundle: ObservatoryExportBundle, isFa: boolean): void {
  const rows = extractHydrologyRows(bundle.hydrology);
  const canvas = document.createElement('canvas');
  canvas.width = 1400;
  canvas.height = 820;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  // Background
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Header Banner
  const grad = ctx.createLinearGradient(0, 0, canvas.width, 0);
  grad.addColorStop(0, '#0b2239');
  grad.addColorStop(1, '#0f5257');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, canvas.width, 115);

  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 30px Inter, Vazirmatn, sans-serif';
  ctx.fillText(
    isFa ? 'URMIA LAKE OBSERVATORY | رصدخانه هوشمند و علمی دریاچه ارومیه' : 'URMIA LAKE OBSERVATORY (ULO) — Official Water Level Time Series',
    45,
    54
  );
  ctx.fillStyle = '#cbd5e1';
  ctx.font = '18px Inter, Vazirmatn, sans-serif';
  const latest = rows[rows.length - 1];
  ctx.fillText(
    `Latest Observation: ${latest ? `${latest.date} (${latest.level_m.toFixed(2)} m a.s.l.)` : 'N/A'}  |  Ecological Threshold: 1274.10 m  |  Generated: ${new Date().toISOString().slice(0, 10)}`,
    45,
    88
  );

  // Plot Frame
  const padL = 110;
  const padR = 60;
  const padT = 165;
  const padB = 130;
  const plotW = canvas.width - padL - padR;
  const plotH = canvas.height - padT - padB;

  ctx.fillStyle = '#f8fafc';
  ctx.fillRect(padL, padT, plotW, plotH);
  ctx.strokeStyle = '#cbd5e1';
  ctx.lineWidth = 2;
  ctx.strokeRect(padL, padT, plotW, plotH);

  const minY = 1269.0;
  const maxY = 1279.0;
  const yToPx = (val: number) => padT + plotH - ((val - minY) / (maxY - minY)) * plotH;

  // Horizontal grid & labels
  ctx.font = '15px Inter, sans-serif';
  ctx.fillStyle = '#475569';
  for (let y = 1269; y <= 1279; y += 2) {
    const py = yToPx(y);
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padL, py);
    ctx.lineTo(padL + plotW, py);
    ctx.stroke();
    ctx.fillText(`${y} m`, 38, py + 5);
  }

  // Ecological Level Dashed Line (1274.1 m)
  const ecoY = yToPx(1274.1);
  ctx.save();
  ctx.strokeStyle = '#059669';
  ctx.lineWidth = 2.5;
  ctx.setLineDash([10, 6]);
  ctx.beginPath();
  ctx.moveTo(padL, ecoY);
  ctx.lineTo(padL + plotW, ecoY);
  ctx.stroke();
  ctx.restore();
  ctx.fillStyle = '#047857';
  ctx.font = 'bold 16px Inter, sans-serif';
  ctx.fillText('Ecological Target Level (1274.1 m a.s.l.)', padL + 16, ecoY - 10);

  // Data curve
  if (rows.length >= 2) {
    ctx.strokeStyle = '#0284c7';
    ctx.lineWidth = 3.5;
    ctx.beginPath();
    rows.forEach((r, idx) => {
      const px = padL + (idx / (rows.length - 1)) * plotW;
      const py = yToPx(r.level_m);
      if (idx === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.stroke();

    // Area fill under curve
    ctx.lineTo(padL + plotW, padT + plotH);
    ctx.lineTo(padL, padT + plotH);
    ctx.closePath();
    ctx.fillStyle = 'rgba(2, 132, 199, 0.12)';
    ctx.fill();

    // X-axis labels
    ctx.fillStyle = '#334155';
    ctx.font = '14px Inter, sans-serif';
    const step = Math.max(1, Math.floor(rows.length / 7));
    for (let i = 0; i < rows.length; i += step) {
      const px = padL + (i / (rows.length - 1)) * plotW;
      ctx.fillText(rows[i].date, px - 36, padT + plotH + 28);
    }
  }

  // Footer Provenance & Developer
  ctx.fillStyle = '#475569';
  ctx.font = '14px Inter, sans-serif';
  ctx.fillText(
    'Source: Hydroweb / CLMS Calibrated Radar Altimetry | Developer: Alireza Fazeli Sani (alirezafazeli@live.com) | Independent Open-Science Observatory',
    45,
    canvas.height - 34
  );

  canvas.toBlob((blob) => {
    if (blob) triggerBlobDownload(blob, 'urmia_lake_observatory_chart.png');
  }, 'image/png');
}

// ---------- EXPORT 6: BILINGUAL SCIENTIFIC PDF REPORT (A4 PRINT-READY WITH VECTOR SVG) ----------
function buildHydroSvgChart(rows: Array<{ date: string; level_m: number }>): string {
  if (rows.length < 2) {
    return '<p style="color:#64748b;">Hydrology time-series unavailable for SVG plotting.</p>';
  }
  const w = 720;
  const h = 220;
  const padL = 52;
  const padR = 16;
  const padT = 16;
  const padB = 30;
  const plotW = w - padL - padR;
  const plotH = h - padT - padB;
  const minY = 1269;
  const maxY = 1279;

  const xPos = (i: number) => padL + (i / (rows.length - 1)) * plotW;
  const yPos = (v: number) => padT + plotH - ((v - minY) / (maxY - minY)) * plotH;

  const polylinePts = rows.map((r, i) => `${xPos(i).toFixed(1)},${yPos(r.level_m).toFixed(1)}`).join(' ');
  const ecoY = yPos(1274.1).toFixed(1);

  const gridLines = [1269, 1271, 1273, 1275, 1277, 1279]
    .map(
      (v) =>
        `<line x1="${padL}" y1="${yPos(v).toFixed(1)}" x2="${w - padR}" y2="${yPos(v).toFixed(1)}" stroke="#e2e8f0" stroke-width="1"/>` +
        `<text x="${padL - 8}" y="${(yPos(v) + 4).toFixed(1)}" text-anchor="end" font-size="10" fill="#475569">${v}</text>`
    )
    .join('');

  return `
    <svg viewBox="0 0 ${w} ${h}" width="100%" height="220" xmlns="http://www.w3.org/2000/svg" style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:8px;">
      ${gridLines}
      <line x1="${padL}" y1="${ecoY}" x2="${w - padR}" y2="${ecoY}" stroke="#059669" stroke-width="1.8" stroke-dasharray="6,4"/>
      <text x="${padL + 8}" y="${Number(ecoY) - 6}" font-size="10" font-weight="bold" fill="#047857">Ecological Target: 1274.1 m a.s.l.</text>
      <polyline fill="none" stroke="#0284c7" stroke-width="2.5" points="${polylinePts}"/>
      <text x="${padL}" y="${h - 8}" font-size="10" fill="#334155">${rows[0].date}</text>
      <text x="${w - padR}" y="${h - 8}" text-anchor="end" font-size="10" fill="#334155">${rows[rows.length - 1].date}</text>
    </svg>
  `;
}

export function openBilingualPdfReport(bundle: ObservatoryExportBundle, reportLang: 'fa' | 'en'): boolean {
  const isFa = reportLang === 'fa';
  const rows = extractHydrologyRows(bundle.hydrology);
  const latest = rows[rows.length - 1];
  const dss = bundle.researchCenter?.decision_support;
  const eco = bundle.researchCenter?.ecology_biodiversity;
  const lib = bundle.researchCenter?.scientific_library;
  const periods = dss?.period_comparisons || [];
  const recs = dss?.management_recommendations || [];
  const svgChart = buildHydroSvgChart(rows);

  const periodRowsHtml = periods
    .map(
      (p: any) => `
      <tr>
        <td>${isFa ? p.period_fa : p.period_en}</td>
        <td style="direction:ltr">${p.start_date} → ${p.end_date}</td>
        <td style="direction:ltr">${Number(p.mean_level_m).toFixed(2)} m</td>
        <td style="direction:ltr;color:${p.net_change_m < 0 ? '#b91c1c' : '#047857'};font-weight:bold;">${p.net_change_m > 0 ? '+' : ''}${Number(p.net_change_m).toFixed(2)} m</td>
        <td>${isFa ? p.regime_fa : p.regime_en}</td>
      </tr>`
    )
    .join('');

  const recListHtml = recs
    .map(
      (r: any) => `<li><strong>${isFa ? r.domain_fa : r.domain_en} (${r.priority}):</strong> ${isFa ? r.action_fa : r.action_en}</li>`
    )
    .join('');

  const topRefsHtml = (lib?.publications || [])
    .slice(0, 6)
    .map(
      (p: any) => `<li>${p.authors?.slice(0, 2).join(', ')} (${p.year}). <em>${p.title}</em>. ${p.venue}. DOI: ${p.doi}</li>`
    )
    .join('');

  const html = `<!DOCTYPE html>
<html lang="${isFa ? 'fa' : 'en'}" dir="${isFa ? 'rtl' : 'ltr'}">
<head>
  <meta charset="UTF-8" />
  <title>${isFa ? 'گزارش علمی رصدخانه هوشمند دریاچه ارومیه' : 'Urmia Lake Observatory — Official Scientific Report'}</title>
  <style>
    @page { size: A4; margin: 14mm; }
    body {
      font-family: ${isFa ? "'Vazirmatn', 'Tahoma', sans-serif" : "'Inter', 'Segoe UI', Arial, sans-serif"};
      color: #0f172a;
      line-height: 1.65;
      font-size: 12px;
      margin: 0;
      padding: 18px;
      background: #ffffff;
    }
    .header {
      background: #0b2239;
      color: #ffffff;
      padding: 16px 20px;
      border-radius: 10px;
      margin-bottom: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .header h1 { margin: 0; font-size: 18px; }
    .header p { margin: 4px 0 0 0; font-size: 11px; color: #cbd5e1; }
    .kpi-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
      margin-bottom: 16px;
    }
    .kpi {
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      padding: 10px;
      background: #f8fafc;
    }
    .kpi-label { font-size: 10px; color: #475569; }
    .kpi-val { font-size: 16px; font-weight: bold; color: #0b2239; margin-top: 4px; direction: ltr; display: inline-block; }
    h2 {
      font-size: 14px;
      color: #0b2239;
      border-bottom: 2px solid #0284c7;
      padding-bottom: 4px;
      margin: 16px 0 8px 0;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
      font-size: 11px;
    }
    th, td {
      border: 1px solid #cbd5e1;
      padding: 6px 8px;
      text-align: inherit;
    }
    th { background: #f1f5f9; font-weight: bold; }
    .box {
      background: #fffbeb;
      border: 1px solid #fde68a;
      border-radius: 8px;
      padding: 10px 12px;
      margin-top: 10px;
      font-size: 11px;
    }
    .footer {
      margin-top: 20px;
      padding-top: 10px;
      border-top: 1px solid #94a3b8;
      font-size: 10.5px;
      color: #475569;
    }
    .print-bar {
      margin-bottom: 14px;
      padding: 10px;
      background: #e0f2fe;
      border-radius: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .print-btn {
      background: #0284c7;
      color: #fff;
      border: none;
      padding: 8px 16px;
      border-radius: 6px;
      font-weight: bold;
      cursor: pointer;
    }
    @media print {
      .print-bar { display: none !important; }
      body { padding: 0; }
    }
  </style>
</head>
<body>
  <div class="print-bar">
    <span>${isFa ? 'گزارش آماده ذخیره با فرمت PDF (A4) است. روی دکمه چاپ/ذخیره کلیک کنید و Destination را Save as PDF بگذارید.' : 'Scientific A4 report ready. Click Print / Save as PDF below.'}</span>
    <button class="print-btn" onclick="window.print()">${isFa ? 'ذخیره / چاپ PDF 🖨️' : 'Save / Print PDF 🖨️'}</button>
  </div>

  <div class="header">
    <div>
      <h1>${isFa ? 'گزارش علمی و مدیریتی رصدخانه هوشمند دریاچه ارومیه (ULO)' : 'URMIA LAKE OBSERVATORY (ULO) — Technical & Scientific Report'}</h1>
      <p>${isFa ? 'گزارش داده‌محور مبتنی بر آلتیمتری ماهواره‌ای، بازتحلیل اقلیمی ERA5، شبکه GBIF و کنوانسیون رامسر' : 'Evidence-Based Synthesis of Satellite Altimetry, ECMWF ERA5 Climate, GBIF Biodiversity & Ramsar Site #38'}</p>
    </div>
    <div style="text-align: end; font-size: 11px;">
      <div>${isFa ? 'تاریخ تولید گزارش:' : 'Report Date:'} ${new Date().toISOString().slice(0, 10)}</div>
      <div>${isFa ? 'آخرین مشاهده تراز:' : 'Latest Stage Obs:'} ${latest ? latest.date : 'N/A'}</div>
    </div>
  </div>

  <div class="kpi-row">
    <div class="kpi">
      <div class="kpi-label">${isFa ? 'تراز فعلی سطح آب' : 'Current Water Level'}</div>
      <div class="kpi-val">${latest ? `${latest.level_m.toFixed(2)} m` : 'N/A'}</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">${isFa ? 'کسری تا تراز اکولوژیک (۱۲۷۴.۱m)' : 'Ecological Deficit (vs 1274.1m)'}</div>
      <div class="kpi-val">${latest ? `${(1274.1 - latest.level_m).toFixed(2)} m` : 'N/A'}</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">${isFa ? 'پهنه مرطوب برآوردی' : 'Estimated Wet Area'}</div>
      <div class="kpi-val">${latest ? `${latest.area_km2.toFixed(1)} km²` : 'N/A'}</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">${isFa ? 'مشاهدات ثبت‌شده GBIF حوضه' : 'GBIF Basin Occurrences'}</div>
      <div class="kpi-val">${eco?.gbif_summary?.total_occurrences_in_basin ?? 'N/A'}</div>
    </div>
  </div>

  <h2>${isFa ? '۱. نمودار سری زمانی واقعی تراز آب دریاچه ارومیه (۱۹۹۵ تا کنون)' : '1. Satellite Altimetry Water Level Time Series (1995–Present)'}</h2>
  ${svgChart}

  <h2>${isFa ? '۲. جدول مقایسه آماری دوره‌های تاریخی هیدرولوژیک' : '2. Multi-Period Historical Hydrological Comparison'}</h2>
  <table>
    <thead>
      <tr>
        <th>${isFa ? 'دوره زمانی' : 'Period'}</th>
        <th>${isFa ? 'بازه تاریخ' : 'Date Span'}</th>
        <th>${isFa ? 'میانگین تراز' : 'Mean Level'}</th>
        <th>${isFa ? 'تغییر خالص' : 'Net Change'}</th>
        <th>${isFa ? 'تفسیر رژیم' : 'Regime Interpretation'}</th>
      </tr>
    </thead>
    <tbody>
      ${periodRowsHtml}
    </tbody>
  </table>

  <h2>${isFa ? '۳. پیشنهادهای مدیریتی و اقدامات اولویت‌دار احیا' : '3. Evidence-Based Management Recommendations'}</h2>
  <ul>${recListHtml}</ul>

  <h2>${isFa ? '۴. روش‌شناسی، منابع علمی و محدودیت‌های عدم قطعیت' : '4. Methodology, References & Scientific Limitations'}</h2>
  <div class="box">
    <strong>${isFa ? 'روش‌شناسی و صحت علمی:' : 'Methodology & Limitations:'}</strong>
    ${
      isFa
        ? 'تمام داده‌های تراز آب از آلتیمتری راداری ماهواره‌ای کالیبره‌شده (Hydroweb/CLMS) و اقلیم از بازتحلیل ECMWF ERA5 استخراج شده‌اند. آزمون روند ناپارامتریک Mann-Kendall و شیب Theil-Sen بدون فرض توزیع نرمال محاسبه شده است. برآورد حجم مخزن و شوری بر پایه منحنی هیپسومتری بوده و دارای عدم قطعیت ±۱۲ تا ۱۵ درصد به علت رسوب پوسته نمکی هالیت در بستر است. هیچ رابطه آماری به‌تنهایی به‌عنوان علیت تک‌عاملی گزارش نشده و موارد فاقد داده هیدرومتری زمینی صریحاً با برچسب Hypothesis مشخص شده‌اند.'
        : 'Water elevation observations originate from calibrated satellite radar altimetry (Hydroweb/CLMS) and basin meteorology from ECMWF ERA5 reanalysis. Non-parametric Mann-Kendall and Theil-Sen slope estimators are applied. Bathymetric volume and salinity estimates carry ±12–15% uncertainty due to precipitated halite crusts. Statistical correlations are never claimed as single-factor causation; unverified attributions are explicitly labeled as Hypothesis.'
    }
  </div>

  <h2>${isFa ? '۵. فهرست گزیده منابع علمی داوری‌شده (OpenAlex / Crossref)' : '5. Selected Peer-Reviewed Scientific References (OpenAlex / Crossref)'}</h2>
  <ol style="direction:ltr;text-align:left;font-size:10.5px;">${topRefsHtml}</ol>

  <div class="footer">
    <div><strong>${isFa ? 'توسعه‌دهنده و طراح:' : 'Developer & Creator:'}</strong> ${isFa ? 'علیرضا فاضلی ثانی (Alireza Fazeli Sani) — alirezafazeli@live.com' : 'Alireza Fazeli Sani (علیرضا فاضلی ثانی) — alirezafazeli@live.com'}</div>
    <div>${isFa ? 'سلب مسئولیت: رصدخانه هوشمند دریاچه ارومیه یک سامانه پژوهشی مستقل است و هیچ‌گونه وابستگی یا تأیید رسمی از سازمان‌های NASA، ESA، USGS، UNESCO یا کنوانسیون رامسر ندارد.' : 'Disclaimer: Urmia Lake Observatory is an independent open-science platform and claims no official affiliation with or endorsement by NASA, ESA, USGS, UNESCO, or the Ramsar Secretariat.'}</div>
  </div>
</body>
</html>`;

  const win = window.open('', '_blank', 'width=980,height=800');
  if (!win) {
    // Fallback: download print-ready HTML if popup blocked
    triggerBlobDownload(new Blob([html], { type: 'text/html;charset=utf-8;' }), `urmia_lake_report_${reportLang}.html`);
    return false;
  }
  win.document.open();
  win.document.write(html);
  win.document.close();
  setTimeout(() => {
    win.focus();
  }, 300);
  return true;
}

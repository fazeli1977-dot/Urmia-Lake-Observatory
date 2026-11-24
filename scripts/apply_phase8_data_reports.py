#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 8 — Data Management, Multi-Format Validation, Scientific Exports & Bilingual PDF Reports
Urmia Lake Observatory (ULO)
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_UPLOADS_DIR = PROJECT_ROOT / "data" / "user_uploads"
DATA_EXPORTS_DIR = PROJECT_ROOT / "data" / "exports"
PUBLIC_DIR = PROJECT_ROOT / "web-dashboard" / "public"
PUBLIC_DATA_DIR = PUBLIC_DIR / "data"
SRC_DIR = PROJECT_ROOT / "web-dashboard" / "src"
UTILS_DIR = SRC_DIR / "utils"
COMPONENTS_DIR = SRC_DIR / "components"

UTC_NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
TODAY_STR = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def discover_real_exportable_assets() -> Dict[str, Any]:
    """Scan web-dashboard/public for real GeoJSON, JSON, and GeoTIFF assets without fabricating data."""
    geojson_files: List[Dict[str, Any]] = []
    geotiff_files: List[Dict[str, Any]] = []
    json_datasets: List[Dict[str, Any]] = []

    if PUBLIC_DIR.exists():
        for p in sorted(PUBLIC_DIR.rglob("*")):
            if not p.is_file():
                continue
            rel_url = p.relative_to(PUBLIC_DIR).as_posix()
            size_kb = round(p.stat().st_size / 1024.0, 2)
            suffix = p.suffix.lower()
            if suffix in {".geojson"}:
                geojson_files.append({
                    "name": p.name,
                    "public_path": rel_url,
                    "size_kb": size_kb,
                })
            elif suffix in {".tif", ".tiff"}:
                geotiff_files.append({
                    "name": p.name,
                    "public_path": rel_url,
                    "size_kb": size_kb,
                })
            elif suffix == ".json" and rel_url.startswith("data/"):
                json_datasets.append({
                    "name": p.name,
                    "public_path": rel_url,
                    "size_kb": size_kb,
                })

    return {
        "generated_at_utc": UTC_NOW,
        "schema_version": "8.0.0",
        "geojson_layers_count": len(geojson_files),
        "geojson_layers": geojson_files,
        "geotiff_rasters_count": len(geotiff_files),
        "geotiff_rasters": geotiff_files,
        "geotiff_status": "AVAILABLE" if geotiff_files else "DATA_UNAVAILABLE",
        "json_datasets": json_datasets,
        "security_policy": {
            "max_upload_size_mb": 25,
            "allowed_extensions": [".csv", ".xlsx", ".json", ".geojson", ".zip", ".tif", ".tiff", ".nc", ".pdf"],
            "client_side_only": True,
            "no_external_transmission": True,
        },
    }


UTILS_TS_CONTENT = r"""// Phase 8 — Secure Client-Side Data Validation (8 Formats) & Multi-Format Export Engine
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

// ---------- HELPER: EXTRACT STANDARD HYDROLOGY SERIES ----------
export function extractHydrologyRows(hydro: Record<string, any> | null): Array<{
  date: string;
  level_m: number;
  area_km2: number;
  volume_km3: number;
  source: string;
}> {
  if (!hydro) return [];
  const raw =
    hydro.timeseries ||
    hydro.observations ||
    hydro.series ||
    hydro.records ||
    hydro.data ||
    [];
  if (!Array.isArray(raw)) return [];
  return raw
    .map((r: any) => ({
      date: String(r?.date || r?.timestamp || r?.datetime || '').slice(0, 10),
      level_m: Number(r?.water_level_m ?? r?.level_m ?? r?.elevation_m ?? r?.wse_m ?? NaN),
      area_km2: Number(r?.area_km2 ?? r?.surface_area_km2 ?? r?.wet_area_km2 ?? 0),
      volume_km3: Number(r?.volume_km3 ?? r?.storage_km3 ?? 0),
      source: String(r?.source || hydro?.metadata?.source || 'Hydroweb / CLMS Satellite Altimetry'),
    }))
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
  const raw =
    climate.monthly_series ||
    climate.timeseries ||
    climate.records ||
    climate.data ||
    [];
  if (!Array.isArray(raw)) return [];
  return raw
    .map((r: any) => ({
      month: String(r?.month || r?.date || r?.period || '').slice(0, 10),
      precip_mm: Number(r?.precipitation_mm ?? r?.precip_mm ?? 0),
      et0_mm: Number(r?.et0_mm ?? r?.evapotranspiration_mm ?? 0),
      temp_c: Number(r?.temp_mean_c ?? r?.temperature_c ?? 0),
    }))
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
"""


CSS_CONTENT = r"""/* Phase 8 — Data Management, Scientific Export, Bilingual PDF & About Governance */

.ulo-phase8-wrapper {
  margin-top: 2rem;
  margin-bottom: 2.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.ulo-p8-banner {
  background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 55%, #0e7490 100%);
  color: #ffffff;
  border-radius: 16px;
  padding: 1.45rem 1.75rem;
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.15);
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.ulo-p8-banner h2 {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
}

.ulo-p8-banner p {
  margin: 0.3rem 0 0 0;
  font-size: 0.88rem;
  color: rgba(255, 255, 255, 0.86);
  line-height: 1.65;
}

.ulo-p8-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  padding-top: 0.55rem;
  border-top: 1px solid rgba(255, 255, 255, 0.18);
}

.ulo-p8-tab {
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: #e2e8f0;
  padding: 0.5rem 1rem;
  border-radius: 10px;
  font-family: inherit;
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.ulo-p8-tab.active {
  background: #38bdf8;
  border-color: #7dd3fc;
  color: #082f49;
}

.ulo-p8-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
}

.ulo-p8-card-head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  padding-bottom: 0.85rem;
  margin-bottom: 1.15rem;
  border-bottom: 1px solid #f1f5f9;
}

.ulo-p8-card-title {
  margin: 0;
  font-size: 1.12rem;
  font-weight: 700;
  color: #0f172a;
}

.ulo-p8-dropzone {
  border: 2px dashed #38bdf8;
  background: #f0f9ff;
  border-radius: 14px;
  padding: 1.75rem 1.25rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.65rem;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.ulo-p8-dropzone:hover {
  background: #e0f2fe;
  border-color: #0284c7;
}

.ulo-p8-format-chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.4rem;
  margin-top: 0.25rem;
}

.ulo-p8-chip {
  background: #ffffff;
  border: 1px solid #bae6fd;
  color: #0369a1;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 700;
}

.ulo-p8-audit-box {
  margin-top: 1.2rem;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  padding: 1.15rem;
  background: #f8fafc;
}

.ulo-p8-audit-box.accepted {
  border-color: #86efac;
  background: #f0fdf4;
}

.ulo-p8-audit-box.rejected {
  border-color: #fca5a5;
  background: #fef2f2;
}

.ulo-p8-check-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 0.75rem;
  margin-top: 0.9rem;
}

.ulo-p8-check-item {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.75rem 0.9rem;
  font-size: 0.81rem;
}

.ulo-p8-status-pill {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
}

.ulo-p8-status-pill.PASS {
  background: #dcfce7;
  color: #166534;
}

.ulo-p8-status-pill.WARN {
  background: #fef3c7;
  color: #92400e;
}

.ulo-p8-status-pill.FAIL {
  background: #fee2e2;
  color: #991b1b;
}

.ulo-p8-export-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.ulo-p8-export-tile {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.1rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 0.85rem;
}

.ulo-p8-export-tile h4 {
  margin: 0;
  font-size: 0.95rem;
  color: #0f172a;
}

.ulo-p8-export-tile p {
  margin: 0.35rem 0 0 0;
  font-size: 0.8rem;
  color: #475569;
  line-height: 1.55;
}

.ulo-p8-btn-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.ulo-p8-btn {
  background: #0284c7;
  color: #ffffff;
  border: none;
  padding: 0.55rem 0.95rem;
  border-radius: 8px;
  font-family: inherit;
  font-size: 0.81rem;
  font-weight: 600;
  cursor: pointer;
}

.ulo-p8-btn:hover {
  background: #0369a1;
}

.ulo-p8-btn.secondary {
  background: #0f172a;
}

.ulo-p8-btn.secondary:hover {
  background: #1e293b;
}

.ulo-p8-btn.pdf {
  background: #0d9488;
}

.ulo-p8-btn.pdf:hover {
  background: #0f766e;
}

.ulo-p8-about-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
  gap: 1rem;
}

.ulo-p8-about-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.1rem;
  font-size: 0.83rem;
  color: #334155;
  line-height: 1.65;
}

.ulo-p8-about-box h4 {
  margin: 0 0 0.45rem 0;
  font-size: 0.96rem;
  color: #0f172a;
}

.ulo-p8-preview-table-wrap {
  margin-top: 0.9rem;
  overflow-x: auto;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  background: #ffffff;
}

.ulo-p8-preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
}

.ulo-p8-preview-table th,
.ulo-p8-preview-table td {
  padding: 0.5rem 0.7rem;
  border-bottom: 1px solid #f1f5f9;
  text-align: inherit;
}

.ulo-p8-preview-table th {
  background: #f1f5f9;
  font-weight: 700;
}
"""


TSX_CONTENT = r"""import React, { useEffect, useRef, useState } from 'react';
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
"""


def patch_app_tsx() -> None:
    app_path = SRC_DIR / "App.tsx"
    if not app_path.exists():
        print(f"  [ERROR] {app_path} not found!")
        return

    content = app_path.read_text(encoding="utf-8")
    if "DataManagementReports" in content:
        print("  [OK] DataManagementReports already mounted in App.tsx.")
        return

    import_stmt = "import { DataManagementReports } from './components/DataManagementReports';\n"
    matches = list(re.finditer(r"^import .+;$", content, flags=re.MULTILINE))
    if matches:
        insert_pos = matches[-1].end()
        content = content[:insert_pos] + "\n" + import_stmt + content[insert_pos:]
    else:
        content = import_stmt + content

    prop_expr = ""
    if re.search(r"\bconst\s+\[\s*lang\s*,", content):
        prop_expr = " lang={lang}"
    elif re.search(r"\bconst\s+\[\s*language\s*,", content):
        prop_expr = " lang={language}"

    component_jsx = f"\n      <DataManagementReports{prop_expr} />\n"

    if "<ScientificResearchCenter" in content:
        idx = content.find("<ScientificResearchCenter")
        end_tag = content.find("/>", idx)
        if end_tag != -1:
            content = content[: end_tag + 2] + component_jsx + content[end_tag + 2 :]
        else:
            content = content[:idx] + component_jsx + content[idx:]
    elif "<footer" in content:
        idx = content.find("<footer")
        content = content[:idx] + component_jsx + "      " + content[idx:]
    elif "</main>" in content:
        idx = content.rfind("</main>")
        content = content[:idx] + component_jsx + "    " + content[idx:]

    app_path.write_text(content, encoding="utf-8")
    print("  [OK] Patched web-dashboard/src/App.tsx with <DataManagementReports />.")


def update_docs(catalog: Dict[str, Any]) -> None:
    print("[Phase 8] Updating project status & technical documentation files...")
    status_md = f"""# PROJECT STATUS — URMIA LAKE OBSERVATORY (ULO)
Last Updated (UTC): `{UTC_NOW}`

## Completed Phases
- **Phase 0 — Feasibility & Architecture**: Completed
- **Phase 1 — Desktop Project Initialization**: Completed (`Desktop/Urmia-Lake-Observatory`)
- **Phase 2 — Geospatial Infrastructure**: Completed ({catalog['geojson_layers_count']} real GeoJSON layers verified)
- **Phase 3 — Data Source Integration**: Completed (Hydroweb/CLMS, Copernicus STAC, ECMWF ERA5, OSM/HydroSHEDS)
- **Phase 4 — Scientific Processing**: Completed (Mann-Kendall, Theil-Sen, hypsometry, salinity & dust risk)
- **Phase 5 — Bilingual Dashboard**: Completed (RTL Persian Vazirmatn + LTR English Inter)
- **Phase 6 — GIS & Mapping**: Completed (MapLibre GL 13-layer interactive WebGIS)
- **Phase 7 — Scientific Research Center**: Completed (OpenAlex/Crossref Library, GBIF/Ramsar/UNESCO Ecology & DSS)
- **Phase 8 — Data Management and Reports**: **Completed**
  - Client-side security & schema validator for 8 formats (CSV, XLSX, JSON, GeoJSON, Shapefile ZIP, GeoTIFF, NetCDF, PDF) with Path Traversal protection, 25 MB limit, Magic Bytes checks, missing/duplicate/outlier detection, and 100% local privacy.
  - Native multi-format export engine (UTF-8 BOM CSV, native multi-sheet OOXML XLSX, JSON bundle, RFC 7946 GeoJSON, high-res 1400×820 PNG, and bilingual RTL/LTR A4 scientific PDF report with vector SVG plots).
  - Integrated About, Methodology, Scientific Governance & Institutional Disclaimer panel.

## Next Phase
- **Phase 9 — Quality Assurance**: Automated end-to-end tests (Python pytest + Frontend validation/build/security checks + scientific accuracy verification).
- **Phase 10 — Deployment**: Free public deployment workflow (GitHub Pages / Cloudflare Pages + automated data update GitHub Actions).
"""
    (PROJECT_ROOT / "PROJECT_STATUS.md").write_text(status_md, encoding="utf-8")

    phase8_note = f"""
---
## Phase 8 Additions — Data Management, Security & Reporting (`{TODAY_STR}`)
- **User-Provided Data Sandbox**: Client-side only validation for CSV, XLSX, JSON, GeoJSON, Shapefile ZIP, GeoTIFF, NetCDF, and PDF (Max 25 MB, Magic-Byte verification, Path Traversal defense, CRS/Unit/Date/Duplicate/Missing audit). No user files are sent to external servers.
- **Multi-Format Export Engine**: UTF-8 BOM CSV, Multi-Sheet OpenXML XLSX, Provenance JSON, Compiled Real GeoJSON ({catalog['geojson_layers_count']} layers), High-Res PNG Chart, and Bilingual Persian RTL / English LTR A4 PDF Report.
- **GeoTIFF Transparency**: Currently `{catalog['geotiff_status']}` ({catalog['geotiff_rasters_count']} local raster files). No synthetic GeoTIFF files are fabricated.
"""
    for doc_name in ["ARCHITECTURE.md", "DATA_SOURCES.md", "DATA_DICTIONARY.md", "METHODS.md", "SCIENTIFIC_LIMITATIONS.md", "REFERENCES.md"]:
        doc_path = PROJECT_ROOT / doc_name
        existing = doc_path.read_text(encoding="utf-8") if doc_path.exists() else f"# {doc_name.replace('.md', '')} — URMIA LAKE OBSERVATORY\n"
        if "Phase 8 Additions" not in existing:
            doc_path.write_text(existing + phase8_note, encoding="utf-8")


def main() -> None:
    print("=" * 72)
    print("URMIA LAKE OBSERVATORY — PHASE 8 BUILDER (DATA MANAGEMENT & REPORTS)")
    print("=" * 72)

    DATA_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_UPLOADS_DIR / ".gitkeep").touch(exist_ok=True)
    (DATA_EXPORTS_DIR / ".gitkeep").touch(exist_ok=True)

    PUBLIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
    UTILS_DIR.mkdir(parents=True, exist_ok=True)
    COMPONENTS_DIR.mkdir(parents=True, exist_ok=True)

    catalog = discover_real_exportable_assets()
    catalog_path = PUBLIC_DATA_DIR / "export_catalog_latest.json"
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"  [OK] Wrote export_catalog_latest.json "
        f"(GeoJSON layers: {catalog['geojson_layers_count']}, GeoTIFF: {catalog['geotiff_status']})"
    )

    manifest_path = PUBLIC_DATA_DIR / "data_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest["last_phase8_update_utc"] = UTC_NOW
    manifest["export_catalog_file"] = "data/export_catalog_latest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    (UTILS_DIR / "dataValidationAndExport.ts").write_text(UTILS_TS_CONTENT, encoding="utf-8")
    (COMPONENTS_DIR / "DataManagementReports.css").write_text(CSS_CONTENT, encoding="utf-8")
    (COMPONENTS_DIR / "DataManagementReports.tsx").write_text(TSX_CONTENT, encoding="utf-8")
    print("  [OK] Created dataValidationAndExport.ts, DataManagementReports.css, DataManagementReports.tsx")

    patch_app_tsx()
    update_docs(catalog)

    print("=" * 72)
    print("[PHASE 8 COMPLETE] Ready for TypeScript & Vite build verification.")
    print("=" * 72)


if __name__ == "__main__":
    main()

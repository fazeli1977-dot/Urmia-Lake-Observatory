# راهنمای انتشار رایگان و عمومی — رصدخانه هوشمند و علمی دریاچه ارومیه (ULO)
## Free Public Deployment Guide — Urmia Lake Observatory

آخرین به‌روزرسانی: `2026-11-24T14:52:26Z`

این سامانه با معماری **Static Scientific Dashboard + Automated Python Pipeline** طراحی شده است و برای نمایش عمومی به هیچ سرور پولی (Paid Backend) نیاز ندارد.

---

## ۱. انتشار رایگان در GitHub Pages

آدرس عمومی شما:
```text
https://fazeli1977-dot.github.io/Urmia-Lake-Observatory/
```

### گام‌های فعال‌سازی:
1. در حساب گیت‌هاب `https://github.com/fazeli1977-dot` یک مخزن عمومی (Public) جدید با نام دقیق `Urmia-Lake-Observatory` بدون README بسازید.
2. دستور زیر را در PowerShell اجرا کنید:
```powershell
git remote add origin https://github.com/fazeli1977-dot/Urmia-Lake-Observatory.git
git push -u origin main
```
3. در صفحه مخزن در GitHub به **Settings → Pages → Build and deployment** بروید و **Source** را روی **GitHub Actions** قرار دهید.

---

## ۲. انتشار رایگان در Cloudflare Pages

آدرس عمومی شما:
```text
https://urmia-lake-observatory.pages.dev/
```

### گام‌های فعال‌سازی:
1. وارد [Cloudflare Dashboard](https://dash.cloudflare.com/) شوید: **Workers & Pages → Create → Pages → Connect to Git**.
2. مخزن `fazeli1977-dot/Urmia-Lake-Observatory` را انتخاب کنید و تنظیمات بیلد را دقیقاً وارد کنید:
   - **Root directory**: `web-dashboard`
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
   - **Environment variable**: `VITE_BASE_PATH` = `/`
3. روی **Save and Deploy** کلیک کنید.

---

## ۳. تفاوت زیردامنه رایگان و دامنه اختصاصی

| ویژگی | زیردامنه رایگان (`*.github.io` / `*.pages.dev`) | دامنه اختصاصی (`urmialake.org` / `.ir`) |
|---|---|---|
| هزینه سالانه | کاملاً رایگان ($0) | نیازمند خرید و تمدید سالانه |
| گواهی HTTPS (SSL) | خودکار و رایگان | خودکار و رایگان پس از تنظیم DNS |
| امکانات علمی و WebGIS | کاملاً یکسان | کاملاً یکسان |

## ۴. محدودیت‌های سرویس‌های رایگان و تداوم خدمات
- **GitHub Pages**: سقف ۱ گیگابایت حجم سایت، ۱۰۰ گیگابایت پهنای باند ماهانه؛ اجرای زمان‌بندی خودکار در صورت عدم فعالیت ۶۰ روزه نیازمند یک کلیک تمدید است.
- **Cloudflare Pages**: پهنای باند نامحدود برای فایل‌های ایستا، حداکثر ۵۰۰ بیلد ماهانه، سقف ۲۵ مگابایت برای هر فایل.
- **پایداری آفلاین**: فونت‌های `Vazirmatn` و `Inter` و تمامی داده‌های معتبر درون بیلد ذخیره شده‌اند؛ در صورت قطع سرویس‌های خارجی، داشبورد بدون خطا آخرین داده معتبر را نمایش می‌دهد.

**توسعه‌دهنده و طراح:** علیرضا فاضلی ثانی (Alireza Fazeli Sani) — `alirezafazeli@live.com`

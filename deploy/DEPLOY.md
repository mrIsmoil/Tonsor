# Tonsor — PythonAnywhere'ga joylash

Bosqichlar tartib bilan. Har biri oldingisiga bog'liq, o'tkazib yubormang.

---

## 0. Nega PythonAnywhere, nega Vercel emas

**Qaror: PythonAnywhere bepul tarifi — MVP va tanlov uchun yetarli.**

Sabab bitta va hal qiluvchi: **Tonsor'da doimiy disk kerak.** Saytda sartarosh
video yuklaydi, profil rasmi va salon suratlari saqlanadi, baza esa SQLite
fayl. Vercel serverless — u yerda har bir so'rov toza muhitda ishlaydi va
diskka yozilgan narsa keyingi so'rovda yo'q bo'ladi. Ya'ni Vercel'da:

- `db.sqlite3` har deploy'da (va sovuq startda) nolga qaytadi;
- yuklangan video va rasmlar saqlanmaydi;
- ishlashi uchun alohida PostgreSQL + alohida fayl ombori (S3/Cloudinary)
  ulash va `MEDIA_ROOT`ni qayta yozish kerak — bu bir-ikki kunlik ish,
  tanlovda ko'rinadigan hech qanday foyda bermaydi.

PythonAnywhere'da disk doimiy, server doim uyg'oq (sovuq start yo'q) va
siz u bilan allaqachon tanishsiz.

### Bepul tarif chegaralari va bizning holatimiz

| Chegara | Bizda | Holat |
|---|---|---|
| Disk — 512 MB | kod ~15 MB + media 14 MB + baza 0.4 MB | ✅ bemalol |
| Bitta web-ishchi | Telegram xabarlari fonda yuboriladi, so'rovni ushlab turmaydi | ✅ |
| Tashqi tarmoq — oq ro'yxat | `api.telegram.org` va Google OAuth ro'yxatda bor | ⚠️ 8-bosqichda tekshiriladi |
| Custom domen yo'q | `tonsor.hair` GitHub Pages orqali yo'naltiriladi | ✅ [pastga qarang](#tonsorhair-domeni) |
| Har 3 oyda "renew" | tugmani bosish kerak | ⚠️ pastga qarang |

⚠️ **Har 3 oyda Web bo'limidagi "Run until 3 months from today" tugmasini
bosing.** Bosilmasa sayt o'chib qoladi. Telefoningizga eslatma qo'ying.

Media hajmi 512 MB ga yaqinlashganda yoki kunlik bronlar yuzlab bo'lganda
**Developer tarifiga ($10/oy)** o'tiladi: oq ro'yxat olib tashlanadi, disk
5 GB bo'ladi, custom domen to'g'ridan-to'g'ri ulanadi va 3 oylik yangilash
kerak bo'lmaydi — **kodga bitta ham o'zgartirish kerak emas**. PostgreSQL
kerak bo'lsa ham shunchaki `.env` ga `DATABASE_URL=postgres://...` yoziladi.
Yillik to'lovda 12 oy o'rniga 10 oy hisoblanadi.

---

## 1. Kodni serverga olib chiqish

Loyiha git omboriga solingan va birinchi commit qilingan (`.env`, baza,
media va `staticfiles` ataylab omborga kirmaydi).

**Avval o'z kompyuteringizda** GitHub'ga yuklang. github.com/new sahifasida
bo'sh **private** ombor oching, keyin:

```bash
cd ~/Documents/Tonsor
git remote add origin https://github.com/<foydalanuvchi>/tonsor.git
git branch -M main
git push -u origin main
```

**So'ng PythonAnywhere'da** Bash console oching:

```bash
cd ~
git clone https://github.com/<foydalanuvchi>/tonsor.git Tonsor
cd Tonsor
```

> Private ombor uchun GitHub parol emas, **Personal Access Token** so'raydi:
> github.com/settings/tokens → *Generate new token (classic)* → `repo`
> ruxsati. Token parol o'rniga kiritiladi.

**GitHub'siz ham bo'ladi:** loyihani zip qilib, PythonAnywhere'ning
*Files* bo'limidan yuklang va `unzip` qiling. Faqat keyin har yangilanishda
qaytadan yuklashga to'g'ri keladi — git bilan esa `git pull` yetarli.

## 2. Virtual muhit va kutubxonalar

```bash
cd ~/Tonsor
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 3. `.env` faylini yaratish

```bash
cd ~/Tonsor
nano .env
```

Ichiga quyidagilarni yozing (qiymatlarni o'zingiznikiga almashtiring):

```
SECRET_KEY=<uzun-tasodifiy-satr>
DEBUG=False
ALLOWED_HOSTS=<foydalanuvchi>.pythonanywhere.com

GOOGLE_OAUTH_CLIENT_ID=<...>
GOOGLE_OAUTH_SECRET=<...>
YANDEX_MAPS_API_KEY=<...>

TELEGRAM_BOT_TOKEN=<YANGI token — eskisi ochilgan!>
TELEGRAM_BOT_USERNAME=tonsorbot
TELEGRAM_WEBHOOK_SECRET=<uzun-tasodifiy-satr>
```

`SECRET_KEY` yaratish uchun:

```bash
.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(50))"
```

⚠️ `DEBUG=False` majburiy. `True` qolsa, xato sahifalarida sozlamalaringiz va
fayl yo'llaringiz begonalarga ko'rinadi.

## 4. Baza va static fayllar

```bash
cd ~/Tonsor
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py createsuperuser
```

## 5. Web ilovani sozlash

PythonAnywhere → **Web** bo'limi → *Add a new web app* → **Manual configuration**
→ **Python 3.12**.

Keyin shu bo'limda:

**Virtualenv:**
```
/home/<foydalanuvchi>/Tonsor/.venv
```

**WSGI configuration file** — ustiga bosing va butun mazmunini
`deploy/pythonanywhere_wsgi.py` bilan almashtiring (ichidagi `PROJECT_PATH`ni
o'zingiznikiga moslang).

**Static files** — ikkita qator qo'shing:

| URL | Directory |
|---|---|
| `/static/` | `/home/<foydalanuvchi>/Tonsor/staticfiles` |
| `/media/` | `/home/<foydalanuvchi>/Tonsor/media` |

Oxirida yashil **Reload** tugmasini bosing.

## 6. Sayt domenini bazaga yozish

Google login domenni Django'ning Sites jadvalidan oladi. Noto'g'ri qolsa
`redirect_uri_mismatch` xatosi chiqadi:

```bash
cd ~/Tonsor
.venv/bin/python manage.py shell -c "
from django.contrib.sites.models import Site
s = Site.objects.get(id=1)
s.domain = '<foydalanuvchi>.pythonanywhere.com'
s.name = 'Tonsor'
s.save()
print('domen:', s.domain)
"
```

## 7. Google OAuth (buni siz Google Console'da qilasiz)

console.cloud.google.com → APIs & Services → Credentials → OAuth 2.0 Client ID.

**Authorized redirect URIs** ro'yxatiga qo'shing:

```
https://<foydalanuvchi>.pythonanywhere.com/auth/google/login/callback/
```

Eski `http://127.0.0.1:8000/...` qatorini o'chirmang — lokal ishlash uchun kerak.

## 8. Telegram webhook'ni ulash

Lokalda bot `telegram_poll` orqali ishlagan. Serverda webhook ishlaydi —
bir marta ro'yxatdan o'tkaziladi:

```bash
cd ~/Tonsor
.venv/bin/python manage.py shell -c "
import os
from core.telegram import set_webhook
ok = set_webhook(
    'https://<foydalanuvchi>.pythonanywhere.com/telegram/webhook/',
    secret_token=os.getenv('TELEGRAM_WEBHOOK_SECRET'),
)
print('webhook o\\'rnatildi:', ok)
"
```

Buyruq `True` qaytarsa — bot ishlayapti.

**Agar `False` qaytarsa**, avval tarmoq ochiqligini tekshiring:

```bash
cd ~/Tonsor
.venv/bin/python -c "
import requests
for url in ['https://api.telegram.org', 'https://oauth2.googleapis.com']:
    try:
        r = requests.get(url, timeout=10)
        print('OK  ', url, r.status_code)
    except Exception as e:
        print('BLOK', url, type(e).__name__)
"
```

`BLOK` chiqsa, bu domen bepul tarifning oq ro'yxatida yo'q degani.
www.pythonanywhere.com/whitelist/ sahifasidan qo'shishni so'rang yoki
Hacker tarifiga o'ting. Bot ishlamasa ham **sayt normal ishlayveradi** —
xabarnomalar jimgina o'chiq turadi, bron qilish buzilmaydi.

## 9. Tekshirish ro'yxati

Sayt ochilgach quyidagilarni birma-bir sinab ko'ring:

- [ ] Bosh sahifa ochiladi va **uslubli** ko'rinadi (CSS ishlayapti)
- [ ] Email bilan kirish
- [ ] Telefon raqami bilan kirish
- [ ] Google bilan kirish
- [ ] `/shops/quick-add/` — admin hisobi bilan salon qo'shish
- [ ] `/claim/` — kod bilan salonni olish
- [ ] Bron qilish → sartaroshga Telegram xabari keladimi
- [ ] Tasdiqlanmagan salonda bron tugmasi **yo'qligi**
- [ ] Katta rasm yuklash → "Fayl juda katta" xabari chiqadimi
- [ ] Oddiy telefon rasmi yuklash → yuklanadi va tez ochiladi

## 10. Keyingi o'zgarishlarni chiqarish

```bash
cd ~/Tonsor
git pull
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
```

So'ng **Web** bo'limidagi **Reload** tugmasi.

---

## Baza haqida

Hozir SQLite ishlatilyapti va PythonAnywhere diski doimiy — ya'ni ma'lumot
yo'qolmaydi. MVP va dastlabki foydalanuvchilar uchun bu yetarli.

Bir vaqtning o'zida ko'p yozuv boshlanganda (taxminan kunlik yuzlab bron)
PostgreSQL'ga o'tish kerak bo'ladi. Buning uchun kodga tegish shart emas —
`.env` ga bitta qator qo'shiladi:

```
DATABASE_URL=postgres://foydalanuvchi:parol@host:5432/baza
```

So'ng `migrate` va Reload. Bu qator bo'lmasa SQLite ishlayveradi.

**Zaxira nusxa.** SQLite — oddiy fayl, shuning uchun zaxirasi ham oddiy:

```bash
cd ~/Tonsor
cp db.sqlite3 ~/backup-$(date +%F).sqlite3
```

Haqiqiy mijozlar kela boshlagach buni haftasiga bir marta bajaring.

---

## Disk to'lib qolmasligi haqida

Bepul tarifda 512 MB disk bor, telefon rasmi esa 4–8 MB keladi. Shuning
uchun rasmlar **saqlanishdan oldin avtomatik kichraytiriladi** (eng uzun
tomoni 1600px, JPEG sifat 82) — amalda 95% gacha joy tejaydi va ko'zga
bilinmaydi. Chegaradan oshgan fayl esa umuman qabul qilinmaydi:

| Fayl turi | Eng katta hajm |
|---|---|
| Rasm | 10 MB (saqlanishdan oldin siqiladi) |
| Video | 50 MB |

Agar kelajakda siqilmagan eski rasmlar paydo bo'lsa, bir marta yugurtiring:

```bash
.venv/bin/python manage.py compress_media --dry-run   # avval ko'rib oling
.venv/bin/python manage.py compress_media             # keyin bajaring
```

---

## tonsor.hair domeni

Sayt `MIM.pythonanywhere.com` da turadi, lekin odamlar **tonsor.hair** yozib
ham kira oladi. Buning sxemasi:

```
tonsor.hair  ->  GitHub Pages (gh-pages shoxobchasi)  ->  mim.pythonanywhere.com
```

### Nega bunday

PythonAnywhere **bepul** tarifi o'z domeningizni qo'llamaydi — bu faqat
pullik tarifda (Developer, $10/oy). Namecheap'ning bepul "URL Redirect"
imkoniyati esa **HTTPS bermaydi**: 443-port umuman javob bermasdi, brauzer
esa avval `https://` ni sinaydi va o'n soniyalab kutib qolardi.

GitHub Pages ikkalasini ham bepul hal qiladi: domen uchun Let's Encrypt
sertifikatini o'zi chiqaradi va avtomatik yangilab turadi.

### Qanday sozlangan

**1. `gh-pages` shoxobchasi** — faqat yo'naltirish uchun, asosiy kodga
aloqasi yo'q:

| Fayl | Vazifasi |
|---|---|
| `index.html` | Bosh sahifani yo'naltiradi |
| `404.html` | Boshqa yo'llarni yo'naltiradi (`/login/` -> `/login/`) |
| `CNAME` | GitHub'ga domen nomini aytadi |

Yo'naltirish JavaScript orqali va **yo'lni saqlaydi**, shuning uchun
`tonsor.hair/login/` to'g'ri sahifaga tushadi.

**2. Namecheap Advanced DNS** — beshta yozuv:

| Type | Host | Value |
|---|---|---|
| A Record | `@` | `185.199.108.153` |
| A Record | `@` | `185.199.109.153` |
| A Record | `@` | `185.199.110.153` |
| A Record | `@` | `185.199.111.153` |
| CNAME Record | `www` | `mrismoil.github.io.` |

Bu IP manzillar GitHub Pages'niki va o'zgarmaydi.

**3. GitHub Pages** — `gh-pages` shoxobchasi push qilinganda **o'zi yoqiladi**.
Sertifikat DNS to'g'rilangandan ~7 daqiqa keyin chiqdi.

### Keyinchalik nima qilish kerak

- Domen har yili Namecheap'da yangilanishi kerak (avtomatik to'lovni yoqing)
- Sertifikatni GitHub o'zi yangilaydi, aralashish shart emas
- Agar bir kun **Developer tarifiga** o'tsangiz, `tonsor.hair` ni
  to'g'ridan-to'g'ri PythonAnywhere'ga ulaysiz va manzil qatorida
  yo'naltirish emas, domenning o'zi qoladi. Unda `gh-pages` shoxobchasi va
  A yozuvlari o'chiriladi.

### Ma'lum kamchilik

Ichki sahifalar (`tonsor.hair/login/`) foydalanuvchi uchun normal ishlaydi,
lekin server javobida `404` kodi qaytadi — GitHub Pages statik xosting
bo'lgani uchun noma'lum yo'lga boshqa kod qaytara olmaydi. Bu brauzerga
ta'sir qilmaydi; faqat Telegram yoki Facebook'da **ichki** havolaning
oldindan ko'rinishi chiqmasligi mumkin. Asosiy `tonsor.hair` havolasi esa
`200` qaytaradi va normal ko'rinadi.

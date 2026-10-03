# Salon bazasi

## `salonlar_toshkent.csv`

Toshkentdagi 25 ta haqiqiy sartaroshxona va go'zallik saloni.

Kiritish:

```bash
.venv/bin/python manage.py import_shops data/salonlar_toshkent.csv --dry-run
.venv/bin/python manage.py import_shops data/salonlar_toshkent.csv
```

`--dry-run` hech narsa saqlamaydi, faqat nima bo'lishini ko'rsatadi. Buyruq
bir xil nom va manzilni ikki marta kiritmaydi, shuning uchun qayta ishga
tushirish xavfsiz.

Kiritilgan salonlar `is_claimed=False` bo'ladi — ya'ni **bron qabul qilmaydi**.
Bu ataylab: o'zi bilmagan sartaroshga mijozni yuborib bo'lmaydi. Har biriga
`TNS-XXXX` ko'rinishidagi kod beriladi, sartarosh shu kod bilan salonni
o'ziniki qilib oladi.

## Ma'lumot qayerdan olingan

**OpenStreetMap** — `shop=hairdresser` va `shop=beauty` obyektlari, Toshkent
hududi (41.17–41.40 N, 69.12–69.42 E), Overpass API orqali. Manzili
yo'qlari koordinatadan Nominatim bilan aniqlangan.

2GIS ishlatilmadi: uning ma'lumotlari o'z kompaniyasiga tegishli va ommaviy
nusxa olishga ruxsat bermaydi. OpenStreetMap ochiq litsenziyali, ya'ni
qonuniy jihatdan toza va havola ko'rsatilsa bemalol ishlatiladi.

### Havola majburiyati

OpenStreetMap ma'lumoti **ODbL** litsenziyasi ostida tarqatiladi. Uni ochiq
ko'rsatganda manbani eslatish shart:

> © OpenStreetMap hissadorlari

Hozir bu havola `/api/docs/` sahifasida bor. Agar salonlar ro'yxati
sahifasida ham ko'rsatilsa, to'liq to'g'ri bo'ladi.

## Nimalar to'liq emas

| Maydon | Holat |
|---|---|
| Nom, koordinata | 25/25 — hammasida bor |
| Manzil | 25/25 |
| Telefon | 9/25 — OpenStreetMap'da qolganlariniki yo'q |
| Xizmatlar va narxlar | yo'q — buni sartaroshning o'zi kiritadi |
| Ish vaqti | yo'q |

`tur` (erkaklar/ayollar) maydoni ko'pchilik uchun **taxmin**: OpenStreetMap'da
aniq teg faqat bir nechtasida bor, qolganlari nom bo'yicha chamalangan.
Admin panelida qo'lda to'g'rilash mumkin.

## Qayta yig'ish

Skriptlar saqlanmagan — ular bir martalik ish edi. Yangi shahar kerak
bo'lsa, Overpass API'ga shu so'rov yuboriladi (chegaralarni almashtirib):

```
[out:json][timeout:90];
(
  node["shop"="hairdresser"](41.17,69.12,41.40,69.42);
  way["shop"="hairdresser"](41.17,69.12,41.40,69.42);
  node["shop"="beauty"](41.17,69.12,41.40,69.42);
  way["shop"="beauty"](41.17,69.12,41.40,69.42);
);
out center tags;
```

So'rovda `User-Agent` sarlavhasi bo'lishi shart — busiz `406` qaytadi.

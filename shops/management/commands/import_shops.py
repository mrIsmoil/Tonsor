"""Salonlarni CSV fayldan ommaviy kiritadi.

Nima uchun kerak: bitta-bitta forma to'ldirish 300 ta salon uchun bir
necha soat bosish demak. Ma'lumotni 2GIS yoki xaritadan jadvalga yig'ib,
bu buyruq bilan bir zumda kiritish mumkin.

Faylning birinchi qatori — ustun nomlari. Tartibi muhim emas, faqat
nomlari mos bo'lsin (o'zbekcha yoki inglizcha):

    nom,telefon,manzil,tur,lat,lng
    Chilonzor Barber,+998901234567,"Toshkent, Chilonzor 12",erkaklar,41.2790,69.2080

Faqat `nom` majburiy. Koordinata bo'lmasa salon baribir kiritiladi,
lekin "menga eng yaqini" saralashida oxirida turadi.

    python manage.py import_shops salonlar.csv --dry-run
    python manage.py import_shops salonlar.csv
"""

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from shops.models import BarberProfile

# Ustun nomlari har xil yozilishi mumkin — hammasini qabul qilamiz.
FIELDS = {
    'nom': ('nom', 'name', 'salon', 'shop_name', 'nomi'),
    'telefon': ('telefon', 'phone', 'tel', 'raqam', 'contact_phone'),
    'manzil': ('manzil', 'address', 'adres', 'joylashuv'),
    'tur': ('tur', 'type', 'shop_type', 'turi'),
    'lat': ('lat', 'latitude', 'kenglik'),
    'lng': ('lng', 'lon', 'longitude', 'uzunlik'),
}

WOMEN_WORDS = ('ayol', 'women', 'woman', 'jensk', 'ж')


def _pick(row, key):
    """Qatordan kerakli ustunni topadi, nomi qanday yozilganidan qat'i nazar."""
    for name in FIELDS[key]:
        for col, value in row.items():
            if col and col.strip().lower() == name:
                return (value or '').strip()
    return ''


def _coord(raw):
    if not raw:
        return None
    try:
        # Jadval dasturlari vergul qo'yishi mumkin: 41,2790
        value = float(str(raw).replace(',', '.'))
    except ValueError:
        return None
    return value if -180 <= value <= 180 else None


class Command(BaseCommand):
    help = "Salonlarni CSV fayldan kiritadi va har biriga kod beradi."

    def add_arguments(self, parser):
        parser.add_argument('csv_file', help='CSV faylning yo\'li')
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Hech narsa saqlamasdan, nima bo\'lishini ko\'rsatadi.',
        )

    def handle(self, *args, **options):
        path = Path(options['csv_file']).expanduser()
        if not path.exists():
            raise CommandError(f'Fayl topilmadi: {path}')

        dry = options['dry_run']
        created, skipped, bad = [], [], []

        with path.open(encoding='utf-8-sig', newline='') as fh:
            for line_no, row in enumerate(csv.DictReader(fh), start=2):
                name = _pick(row, 'nom')
                if not name:
                    bad.append((line_no, 'nomi yo\'q'))
                    continue

                phone = _pick(row, 'telefon')
                address = _pick(row, 'manzil')
                lat = _coord(_pick(row, 'lat'))
                lng = _coord(_pick(row, 'lng'))
                shop_type = 'women' if any(
                    w in _pick(row, 'tur').lower() for w in WOMEN_WORDS) else 'men'

                # Bir salonni ikki marta kiritib yubormaslik uchun.
                duplicate = BarberProfile.objects.filter(shop_name__iexact=name)
                if address:
                    duplicate = duplicate.filter(address__iexact=address)
                if duplicate.exists():
                    skipped.append(name)
                    continue

                if dry:
                    created.append((name, 'TNS-????', phone, bool(lat and lng)))
                    continue

                shop = BarberProfile.objects.create(
                    shop_name=name,
                    contact_phone=phone,
                    address=address,
                    shop_type=shop_type,
                    location_lat=lat,
                    location_lng=lng,
                    user=None,
                    is_claimed=False,
                )
                shop.generate_claim_code()
                created.append((name, shop.claim_code, phone, bool(lat and lng)))

        self.stdout.write('')
        if created:
            self.stdout.write(self.style.SUCCESS('--- Kiritilgan salonlar ---'))
            self.stdout.write(f'{"Salon":<38} {"Kod":<10} {"Telefon":<18} Xarita')
            for name, code, phone, has_map in created:
                self.stdout.write(
                    f'{name[:37]:<38} {code:<10} {(phone or "—")[:17]:<18} '
                    f'{"bor" if has_map else "YO\'Q"}'
                )
        if skipped:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                f'Allaqachon bazada bor, o\'tkazib yuborildi: {len(skipped)} ta'))
            for name in skipped[:10]:
                self.stdout.write(f'  {name}')
        if bad:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'Xatolik: {len(bad)} ta qator'))
            for line_no, why in bad[:10]:
                self.stdout.write(f'  {line_no}-qator: {why}')

        self.stdout.write('')
        mode = 'SINOV — hech narsa saqlanmadi' if dry else 'BAJARILDI'
        self.stdout.write(self.style.SUCCESS(
            f'--- {mode} --- kiritildi: {len(created)} | '
            f'o\'tkazildi: {len(skipped)} | xato: {len(bad)}'))
        if not dry and created:
            self.stdout.write(
                'Kodlarni sartaroshlarga bering. Ro\'yxatni keyin ham '
                'admin panelidan ko\'rish mumkin.')
        self.stdout.write('')

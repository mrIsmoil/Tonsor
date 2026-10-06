"""Saytga qancha odam kirganini ko'rsatadi.

Ma'lumot ikki joydan olinadi:

  1. Server access log — har bir so'rov, ya'ni ro'yxatdan o'tmagan
     mehmonlar ham. Bu PythonAnywhere tomonidan birinchi kundan beri
     yozib kelinyapti, hech narsa sozlash kerak emas.
  2. Baza — ro'yxatdan o'tganlar, salonlar, bronlar.

Nega alohida tahlil kerak: log faylda robotlar (Google, Bing, turli
skanerlar) ham bor va ular so'rovlarning katta qismini tashkil qiladi.
Ularni ajratmasdan "kuniga 400 tashrif" desangiz, raqam soxta bo'ladi.
Investorga aytiladigan son faqat haqiqiy odamlarniki bo'lishi kerak.
"""

import gzip
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

LOG_DIR = Path('/var/log')

# nginx "combined" format:
# IP - - [10/Oct/2026:12:10:05 +0000] "GET /path HTTP/1.1" 200 1234 "ref" "ua"
LINE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] '
    r'"(?P<method>[A-Z]+) (?P<path>[^ "]*)[^"]*" '
    r'(?P<status>\d{3}) (?P<size>\S+) '
    r'"(?P<ref>[^"]*)" "(?P<ua>[^"]*)"'
)

BOT = re.compile(
    r'bot|crawl|spider|slurp|facebookexternalhit|preview|monitor|scan'
    r'|curl|wget|python-requests|go-http|okhttp|headless|lighthouse'
    r'|uptime|pingdom|semrush|ahrefs|mj12|dotbot|petal|bytespider',
    re.I)

# Sahifa emas — rasm, uslub, skript. Tashrif sanashda hisobga olinmaydi.
ASSET = re.compile(r'\.(css|js|png|jpe?g|gif|svg|ico|woff2?|ttf|map|webp)$', re.I)


class Command(BaseCommand):
    help = "Saytga qancha odam kirganini ko'rsatadi."

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=14,
            help="Necha kunlik ma'lumot ko'rsatilsin (standart 14).")
        parser.add_argument(
            '--log', default='',
            help='Access log fayli. Berilmasa o\'zi topadi.')
        parser.add_argument(
            '--bots', action='store_true',
            help='Robotlarni ham alohida ro\'yxat bilan ko\'rsatadi.')

    def handle(self, *args, **options):
        days = options['days']
        self._database()
        self._traffic(options['log'], days, options['bots'])

    # --- Bazadagi sonlar -------------------------------------------------

    def _database(self):
        User = get_user_model()
        from bookings.models import Appointment
        from shops.models import BarberProfile

        now = timezone.now()
        week = now - timedelta(days=7)

        total = User.objects.count()
        barbers = User.objects.filter(is_barber=True).count()
        new_week = User.objects.filter(date_joined__gte=week).count()

        shops = BarberProfile.objects.count()
        claimed = BarberProfile.objects.filter(is_claimed=True).count()

        bookings = Appointment.objects.count()
        bookings_week = Appointment.objects.filter(created_at__gte=week).count()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== BAZA ==='))
        self.stdout.write(f'  Ro\'yxatdan o\'tganlar  {total}  '
                          f'(shundan sartarosh: {barbers}, oxirgi 7 kunda yangi: {new_week})')
        self.stdout.write(f'  Salonlar              {shops}  '
                          f'(egasi tasdiqlagan: {claimed})')
        self.stdout.write(f'  Bronlar               {bookings}  '
                          f'(oxirgi 7 kunda: {bookings_week})')

    # --- Log tahlili -----------------------------------------------------

    def _find_log(self):
        candidates = sorted(LOG_DIR.glob('*.access.log'))
        if not candidates:
            return None
        # Eng katta fayl — asosiy sayt. Qolganlari odatda bo'sh qoladi.
        return max(candidates, key=lambda p: p.stat().st_size)

    def _open(self, path):
        if path.suffix == '.gz':
            return gzip.open(path, 'rt', errors='replace')
        return path.open(errors='replace')

    def _traffic(self, log_arg, days, show_bots):
        path = Path(log_arg) if log_arg else self._find_log()

        self.stdout.write('')
        if path is None or not path.exists():
            self.stdout.write(self.style.WARNING('=== TASHRIFLAR ==='))
            self.stdout.write('  Access log topilmadi.')
            self.stdout.write('  Bu buyruq serverda ishlatilishi kerak — '
                              'lokal kompyuterda log fayl yo\'q.')
            self.stdout.write(f'  Qidirilgan joy: {LOG_DIR}/*.access.log')
            return

        cutoff = datetime.now() - timedelta(days=days)

        # Log fayl eskisi bilan birga: access.log, access.log.1, .gz
        files = [path]
        for extra in sorted(path.parent.glob(path.name + '.*')):
            files.append(extra)

        by_day = defaultdict(lambda: {'ips': set(), 'views': 0})
        bot_by_day = defaultdict(lambda: {'ips': set(), 'views': 0})
        pages = Counter()
        referrers = Counter()
        bot_names = Counter()
        unparsed = 0

        for fh_path in files:
            try:
                fh = self._open(fh_path)
            except OSError:
                continue
            with fh:
                for line in fh:
                    m = LINE.match(line)
                    if not m:
                        unparsed += 1
                        continue

                    try:
                        when = datetime.strptime(
                            m['time'].split()[0], '%d/%b/%Y:%H:%M:%S')
                    except ValueError:
                        unparsed += 1
                        continue
                    if when < cutoff:
                        continue

                    path_hit = m['path']
                    if ASSET.search(path_hit) or path_hit.startswith('/static/'):
                        continue

                    day = when.strftime('%Y-%m-%d')
                    ua = m['ua']

                    if BOT.search(ua):
                        bot_by_day[day]['ips'].add(m['ip'])
                        bot_by_day[day]['views'] += 1
                        name = re.search(r'([A-Za-z]+[Bb]ot|[A-Za-z]+[Ss]pider)', ua)
                        bot_names[name.group(1) if name else 'boshqa'] += 1
                        continue

                    by_day[day]['ips'].add(m['ip'])
                    by_day[day]['views'] += 1
                    pages[path_hit.split('?')[0]] += 1

                    ref = m['ref']
                    if ref and ref != '-' and 'tonsor' not in ref and 'mim.python' not in ref:
                        referrers[ref.split('?')[0][:70]] += 1

        self.stdout.write(self.style.SUCCESS(
            f'=== TASHRIFLAR (oxirgi {days} kun) ==='))
        self.stdout.write(f'  Fayl: {path}')
        self.stdout.write('')

        if not by_day and not bot_by_day:
            self.stdout.write('  Bu davrda yozuv yo\'q.')
            return

        all_days = sorted(set(by_day) | set(bot_by_day))
        self.stdout.write(f'  {"Sana":<13}{"Odam":>7}{"Ko\'rish":>10}{"Robot":>9}')
        total_people, total_views = set(), 0
        for day in all_days:
            human = by_day.get(day, {'ips': set(), 'views': 0})
            bot = bot_by_day.get(day, {'ips': set(), 'views': 0})
            total_people |= human['ips']
            total_views += human['views']
            self.stdout.write(
                f'  {day:<13}{len(human["ips"]):>7}{human["views"]:>10}'
                f'{bot["views"]:>9}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'  JAMI: {len(total_people)} xil odam, {total_views} sahifa ko\'rish'))
        self.stdout.write(
            '  ("xil odam" = IP manzil soni. Bitta odam telefon va '
            'kompyuterdan\n   kirsa ikki marta sanaladi; bitta uydagi '
            'ikki odam esa bitta sanaladi.)')

        if pages:
            self.stdout.write('')
            self.stdout.write('  --- Eng ko\'p ochilgan sahifalar ---')
            for page, count in pages.most_common(10):
                self.stdout.write(f'  {count:>6}  {page[:60]}')

        if referrers:
            self.stdout.write('')
            self.stdout.write('  --- Qayerdan kelishgan ---')
            for ref, count in referrers.most_common(8):
                self.stdout.write(f'  {count:>6}  {ref}')

        if show_bots and bot_names:
            self.stdout.write('')
            self.stdout.write('  --- Robotlar ---')
            for name, count in bot_names.most_common(10):
                self.stdout.write(f'  {count:>6}  {name}')

        if unparsed:
            self.stdout.write('')
            self.stdout.write(f'  ({unparsed} qator o\'qilmadi — boshqa formatda)')

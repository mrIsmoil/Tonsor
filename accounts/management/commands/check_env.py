"""Serverdagi sozlamalar to'g'ri to'ldirilganini tekshiradi.

Maqsad — deploy paytida "nega ishlamayapti?" degan savolga bir qarashda
javob berish. Maxfiy qiymatlar hech qachon ekranga chiqarilmaydi: faqat
to'ldirilgan-to'ldirilmagani va uzunligi ko'rsatiladi, shunda natijani
xavfsiz ravishda boshqasiga ko'rsatish mumkin.

    python manage.py check_env
"""

import os

from django.conf import settings
from django.core.management.base import BaseCommand

# (nom, majburiymi, u bo'lmasa nima ishlamaydi)
CHECKS = [
    ('SECRET_KEY', True, 'Sessiyalar va xavfsizlik'),
    ('GOOGLE_OAUTH_CLIENT_ID', False, 'Google orqali kirish'),
    ('GOOGLE_OAUTH_SECRET', False, 'Google orqali kirish'),
    ('YANDEX_MAPS_API_KEY', False, 'Xarita (joylashuvni belgilash)'),
    ('TELEGRAM_BOT_TOKEN', False, 'Telegram xabarnomalari'),
    ('TELEGRAM_BOT_USERNAME', False, 'Telegram ulash havolasi'),
    ('TELEGRAM_WEBHOOK_SECRET', False, 'Telegram webhook himoyasi'),
]


class Command(BaseCommand):
    help = "Sozlamalar to'liqligini tekshiradi (maxfiy qiymatlarni ko'rsatmaydi)."

    def handle(self, *args, **options):
        ok = self.style.SUCCESS
        warn = self.style.WARNING
        bad = self.style.ERROR

        self.stdout.write('')
        self.stdout.write('--- Asosiy sozlamalar ---')

        debug = settings.DEBUG
        if debug:
            self.stdout.write(bad('DEBUG = True  <-- PRODUCTION UCHUN XAVFLI'))
            self.stdout.write('    .env faylida DEBUG=False qilib qo\'ying.')
        else:
            self.stdout.write(ok('DEBUG = False'))

        hosts = list(settings.ALLOWED_HOSTS)
        self.stdout.write(f'ALLOWED_HOSTS = {", ".join(hosts)}')
        if not debug and any(h in ('127.0.0.1', 'localhost') for h in hosts) \
                and len(hosts) <= 2:
            self.stdout.write(warn(
                '    Bu yerda saytingiz domeni bo\'lishi kerak '
                '(masalan <foydalanuvchi>.pythonanywhere.com)'))

        engine = settings.DATABASES['default']['ENGINE'].rsplit('.', 1)[-1]
        self.stdout.write(f'Baza = {engine}')

        self.stdout.write('')
        self.stdout.write('--- Kalitlar ---')

        problems = []
        for name, required, purpose in CHECKS:
            value = os.getenv(name, '') or getattr(settings, name, '')
            filled = bool(value) and value != 'TOLDIRING'

            if filled:
                self.stdout.write(ok(f'{name:<26} to\'ldirilgan ({len(value)} belgi)'))
            elif required:
                self.stdout.write(bad(f'{name:<26} YO\'Q  — {purpose}'))
                problems.append(name)
            else:
                self.stdout.write(warn(f'{name:<26} yo\'q   — {purpose} ishlamaydi'))

        self.stdout.write('')
        if problems:
            self.stdout.write(bad(
                f'{len(problems)} ta majburiy sozlama yo\'q: {", ".join(problems)}'))
        elif debug:
            self.stdout.write(warn('Majburiylari joyida, lekin DEBUG=False qilish kerak.'))
        else:
            self.stdout.write(ok('Hammasi joyida — davom etishingiz mumkin.'))
        self.stdout.write('')

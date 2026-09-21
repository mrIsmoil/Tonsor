"""Telegram xabarlarini lokal kompyuterda qabul qilish.

Production'da bot xabarlarni webhook orqali oladi: Telegram bizning serverimizga
o'zi so'rov yuboradi. Lekin lokal kompyuter internetdan ochiq emas, shuning uchun
u yerda webhook ishlamaydi.

Bu buyruq teskarisini qiladi — o'zimiz Telegramdan "yangi xabar bormi?" deb
so'raymiz (getUpdates). Shu tufayli deploy'dan oldin ham botni to'liq sinash
mumkin bo'ladi.

Ishlatish:
    .venv/bin/python manage.py telegram_poll

To'xtatish: Ctrl+C
"""

import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.telegram import API_URL, redact, send_message
from core.telegram_webhook import _handle_start


class Command(BaseCommand):
    help = "Telegram xabarlarini lokal rejimda qabul qiladi (webhook o'rniga)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--once', action='store_true',
            help="Bir marta tekshirib chiqadi va to'xtaydi",
        )

    def handle(self, *args, **options):
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        if not token:
            raise CommandError(
                ".env faylida TELEGRAM_BOT_TOKEN topilmadi."
            )

        # Webhook o'rnatilgan bo'lsa, getUpdates ishlamaydi — ikkalasi bir vaqtda
        # ishlay olmaydi. Lokal rejimga o'tish uchun webhook'ni olib tashlaymiz.
        try:
            requests.post(
                API_URL.format(token=token, method='deleteWebhook'), timeout=10
            )
        except requests.RequestException as exc:
            # Xato matnida token bo'ladi — uni yashirmasdan chiqarib bo'lmaydi.
            raise CommandError(
                "Telegramga ulanib bo'lmadi. Internetni yoki VPN'ni tekshiring.\n"
                f"Sabab: {redact(exc)}"
            )

        self.stdout.write(self.style.SUCCESS(
            "Telegram tinglanmoqda... Botga /start yuboring. To'xtatish: Ctrl+C"
        ))

        offset = None
        try:
            while True:
                handled = self._poll_once(token, offset)
                if handled is not None:
                    offset = handled
                if options['once']:
                    break
        except KeyboardInterrupt:
            self.stdout.write("\nTo'xtatildi.")

    def _poll_once(self, token, offset):
        params = {'timeout': 25}
        if offset is not None:
            params['offset'] = offset

        try:
            response = requests.get(
                API_URL.format(token=token, method='getUpdates'),
                params=params, timeout=35,
            )
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            self.stderr.write(f"Ulanish xatosi: {redact(exc)}")
            time.sleep(3)
            return offset

        if not data.get('ok'):
            self.stderr.write(f"Telegram xatosi: {data.get('description')}")
            time.sleep(3)
            return offset

        for update in data.get('result', []):
            offset = update['update_id'] + 1
            message = update.get('message') or {}
            chat_id = (message.get('chat') or {}).get('id')
            text = (message.get('text') or '').strip()

            if not chat_id or not text.startswith('/start'):
                continue

            parts = text.split(maxsplit=1)
            code = parts[1].strip() if len(parts) > 1 else ''
            reply = _handle_start(chat_id, code)

            # Lokal sinovda javobni kutamiz, shunda natijani darhol ko'ramiz.
            send_message(chat_id, reply, background=False)
            self.stdout.write(f"  chat {chat_id} -> javob yuborildi")

        return offset

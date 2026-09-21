"""Telegram xabar yuborish qatlami.

Ikkita qat'iy qoida:

1. Xabar yuborish hech qachon so'rovni ushlab turmaydi. Bron qilish tezligi
   Telegram serverining tezligiga bog'liq bo'lmasligi kerak, shuning uchun
   yuborish alohida oqimda (thread) ketadi.
2. Xabar yuborish hech qachon xato ko'tarmaydi. Telegram ishlamayotgan bo'lsa,
   token noto'g'ri bo'lsa yoki foydalanuvchi botni bloklagan bo'lsa ham — bron
   muvaffaqiyatli yakunlanishi shart. Xatolar faqat logga yoziladi.
"""

import html
import logging
import threading

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

API_URL = 'https://api.telegram.org/bot{token}/{method}'
TIMEOUT_SECONDS = 10


def is_configured():
    """Bot tokeni sozlanganmi."""
    return bool(getattr(settings, 'TELEGRAM_BOT_TOKEN', ''))


def redact(text):
    """Matndan bot tokenini olib tashlaydi.

    Telegram API manzilida token URL ichida turadi, shuning uchun tarmoq xatosi
    yuz berganda `requests` uni xato matniga qo'shib yuboradi. Tokenni logga
    tushirmaslik uchun har qanday xato matni shu funksiyadan o'tkaziladi.
    """
    result = str(text)
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if token:
        result = result.replace(token, '<TOKEN>')
    return result


def esc(value):
    """Qiymatni Telegram HTML rejimi uchun xavfsiz qiladi.

    Do'kon nomi yoki mijoz ismida < > & belgilari bo'lsa, ularsiz Telegram
    xabarni rad etadi yoki noto'g'ri ko'rsatadi.
    """
    return html.escape(str(value if value is not None else ''))


def _call(method, payload):
    """Telegram API'ga so'rov. Muvaffaqiyatli bo'lsa True qaytaradi."""
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not token:
        logger.warning('Telegram: TELEGRAM_BOT_TOKEN sozlanmagan, xabar yuborilmadi')
        return False

    try:
        response = requests.post(
            API_URL.format(token=token, method=method),
            json=payload,
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        # exc matnida to'liq URL, ya'ni token bo'ladi — redact() shart.
        logger.warning('Telegram: %s so\'rovi bajarilmadi: %s', method, redact(exc))
        return False

    if response.status_code != 200:
        # Telegram xatoning sababini javob tanasida tushuntiradi
        # (masalan: 403 — foydalanuvchi botni bloklagan).
        logger.warning(
            'Telegram: %s xatosi (HTTP %s): %s',
            method, response.status_code, redact(response.text[:300]),
        )
        return False

    return True


def send_message(chat_id, text, background=True, reply_markup=None):
    """Foydalanuvchiga xabar yuboradi.

    chat_id bo'sh bo'lsa jimgina to'xtaydi — sartarosh hali Telegramga
    ulanmagan bo'lishi mumkin, bu xato emas, oddiy holat.
    """
    if not chat_id:
        return False

    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True,
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup

    if not background:
        return _call('sendMessage', payload)

    # Daemon oqim: so'rov javobini kutib turmaydi va server o'chganda
    # jarayonni ushlab qolmaydi.
    threading.Thread(
        target=_call,
        args=('sendMessage', payload),
        daemon=True,
    ).start()
    return True


def set_webhook(url, secret_token=None):
    """Telegram yangiliklarni qaysi manzilga yuborishini belgilaydi.

    Deploy'dan keyin bir marta chaqiriladi (management buyrug'i orqali).
    """
    payload = {'url': url, 'allowed_updates': ['message']}
    if secret_token:
        payload['secret_token'] = secret_token
    return _call('setWebhook', payload)


def delete_webhook():
    """Webhook'ni o'chiradi (lokal ishlashga qaytish uchun)."""
    return _call('deleteWebhook', {})

"""Telegramdan keladigan yangiliklarni qabul qiluvchi endpoint.

Hozircha bitta vazifa bajaradi: `/start KOD` buyrug'i orqali foydalanuvchi
akkauntini Telegram chat'iga bog'laydi.

Xavfsizlik: Telegram har bir so'rovga `X-Telegram-Bot-Api-Secret-Token`
sarlavhasini qo'shadi. TELEGRAM_WEBHOOK_SECRET sozlangan bo'lsa, mos
kelmagan so'rovlar rad etiladi — aks holda manzilni bilgan har kim soxta
"yangilik" yuborib, begona akkauntni o'z Telegramiga bog'lab olishi mumkin.
"""

import json
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core import telegram

logger = logging.getLogger(__name__)

WELCOME_LINKED = (
    "✅ <b>Ulandi!</b>\n\n"
    "Endi yangi bronlar shu yerga keladi. Botni o'chirmang."
)
WELCOME_NO_CODE = (
    "👋 <b>Tonsor</b>\n\n"
    "Akkauntingizni ulash uchun saytdagi <b>«Telegramga ulash»</b> "
    "tugmasini bosing."
)
CODE_INVALID = (
    "❌ Kod eskirgan yoki noto'g'ri.\n\n"
    "Saytdan yangi havolani oling."
)


def _secret_ok(request):
    expected = getattr(settings, 'TELEGRAM_WEBHOOK_SECRET', '')
    if not expected:
        # Sir sozlanmagan — mahalliy sinov rejimi.
        return True
    return request.headers.get('X-Telegram-Bot-Api-Secret-Token') == expected


def _handle_start(chat_id, code):
    """/start buyrug'ini bajaradi. Botga yuboriladigan javob matnini qaytaradi."""
    if not code:
        return WELCOME_NO_CODE

    User = get_user_model()
    user = User.objects.filter(telegram_link_code=code).first()
    if user is None:
        return CODE_INVALID

    user.telegram_chat_id = str(chat_id)
    # Kod bir martalik: bog'langandan keyin tozalanadi.
    user.telegram_link_code = ''
    user.save(update_fields=['telegram_chat_id', 'telegram_link_code'])
    logger.info('Telegram: %s akkaunti chat %s ga bog\'landi', user.username, chat_id)
    return WELCOME_LINKED


@csrf_exempt
@require_POST
def telegram_webhook(request):
    """Telegram POST qiladigan manzil.

    Har doim 200 qaytaradi (sir noto'g'ri bo'lgan holatdan tashqari): aks holda
    Telegram xabarni qayta-qayta yuborishga urinadi.
    """
    if not _secret_ok(request):
        logger.warning('Telegram webhook: sir mos kelmadi, so\'rov rad etildi')
        return JsonResponse({'status': 'forbidden'}, status=403)

    try:
        update = json.loads(request.body or b'{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.warning('Telegram webhook: JSON o\'qib bo\'lmadi')
        return JsonResponse({'status': 'ignored'})

    message = update.get('message') or {}
    chat_id = (message.get('chat') or {}).get('id')
    text = (message.get('text') or '').strip()

    if not chat_id or not text.startswith('/start'):
        # Boshqa xabarlarga hozircha javob bermaymiz.
        return JsonResponse({'status': 'ok'})

    parts = text.split(maxsplit=1)
    code = parts[1].strip() if len(parts) > 1 else ''

    try:
        reply = _handle_start(chat_id, code)
    except Exception:
        # Webhook hech qachon 500 qaytarmasligi kerak.
        logger.exception('Telegram webhook: /start ishlov berishda xato')
        return JsonResponse({'status': 'error'})

    telegram.send_message(chat_id, reply)
    return JsonResponse({'status': 'ok'})

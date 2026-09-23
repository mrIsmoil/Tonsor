"""Bron bo'yicha Telegram xabarnomalari.

Bu yerda faqat "kimga nima yozish" hal qilinadi. Xabarni yetkazish
`core.telegram` zimmasida — u xato ko'tarmaydi va so'rovni ushlab turmaydi,
shuning uchun bu funksiyalarni bron yaratish oqimidan bemalol chaqirish mumkin.

Til: xabar oluvchining saytdagi tanlagan tili emas, sodda o'zbekcha. Telegram
xabari qisqa bo'lishi kerak — uni telefon ekranida bir qarashda o'qiydi.
"""

import functools
import logging

from django.utils.dateparse import parse_date, parse_time

from core.telegram import esc, send_message

logger = logging.getLogger(__name__)


def _safe(fn):
    """Xabarnoma xatosi bron qilishni buzmasligi uchun.

    Modul va'dasi shu edi: bu funksiyalarni bron oqimidan bemalol chaqirish
    mumkin. Amalda esa bitta formatlash xatosi butun so'rovni qulatib,
    mijozga 500 sahifasini ko'rsatdi — bron esa allaqachon yaratilgan edi.
    Endi har qanday xato jurnalga yoziladi va oqim davom etadi.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            logger.warning('Xabarnoma yuborilmadi (%s): %s', fn.__name__, exc)
    return wrapper


def _as_date(value):
    return parse_date(value) if isinstance(value, str) else value


def _as_time(value):
    return parse_time(value) if isinstance(value, str) else value


def _when(appointment):
    """Sana va vaqtni o'qishga qulay ko'rinishda qaytaradi.

    Yangi yaratilgan obyektda bu maydonlar matn bo'lishi mumkin (Django uni
    bazaga yozadi, lekin xotirada almashtirmaydi), shuning uchun avval
    haqiqiy sana/vaqtga o'giriladi.
    """
    date = _as_date(appointment.date)
    time = _as_time(appointment.time)
    if date is None or time is None:
        return f"{appointment.date} {appointment.time}".strip()
    return f"{date:%d.%m.%Y}, {time:%H:%M}"


def _service_name(appointment):
    return appointment.service.name if appointment.service else 'Xizmat'


def _client_name(appointment):
    client = appointment.client
    full = (client.get_full_name() or '').strip()
    return full or client.username


@_safe
def notify_barber_new_booking(appointment):
    """Sartaroshga: yangi bron keldi.

    Mahsulotning eng muhim xabari — busiz sartarosh bronni faqat saytni
    ochib qaraganda ko'radi.
    """
    barber_user = getattr(appointment.barber, 'user', None)
    if barber_user is None or not barber_user.telegram_chat_id:
        return

    lines = [
        "🔔 <b>Yangi bron</b>",
        "",
        f"👤 {esc(_client_name(appointment))}",
        f"✂️ {esc(_service_name(appointment))}",
        f"🕐 {esc(_when(appointment))}",
    ]
    if appointment.employee:
        lines.append(f"💈 {esc(appointment.employee.first_name)}")
    if appointment.client_comment:
        lines.append(f"💬 {esc(appointment.client_comment)}")
    lines += ["", "Tasdiqlash uchun saytga kiring."]

    send_message(barber_user.telegram_chat_id, "\n".join(lines))


@_safe
def notify_client_accepted(appointment):
    """Mijozga: sartarosh bronni tasdiqladi."""
    client = appointment.client
    if not client.telegram_chat_id:
        return

    text = "\n".join([
        "✅ <b>Broningiz tasdiqlandi</b>",
        "",
        f"💈 {esc(appointment.barber.shop_name)}",
        f"✂️ {esc(_service_name(appointment))}",
        f"🕐 {esc(_when(appointment))}",
    ])
    send_message(client.telegram_chat_id, text)


@_safe
def notify_client_canceled(appointment, reason=''):
    """Mijozga: bron bekor qilindi."""
    client = appointment.client
    if not client.telegram_chat_id:
        return

    lines = [
        "❌ <b>Bron bekor qilindi</b>",
        "",
        f"💈 {esc(appointment.barber.shop_name)}",
        f"🕐 {esc(_when(appointment))}",
    ]
    if reason:
        lines.append(f"💬 {esc(reason)}")
    lines += ["", "Boshqa vaqtga yozilishingiz mumkin."]

    send_message(client.telegram_chat_id, "\n".join(lines))


@_safe
def notify_barber_client_canceled(appointment, reason=''):
    """Sartaroshga: mijoz bronni bekor qildi.

    Sartarosh bo'shagan vaqtni boshqa mijozga bera olishi uchun buni
    imkon qadar tez bilishi kerak.
    """
    barber_user = getattr(appointment.barber, 'user', None)
    if barber_user is None or not barber_user.telegram_chat_id:
        return

    lines = [
        "⚠️ <b>Mijoz bronni bekor qildi</b>",
        "",
        f"👤 {esc(_client_name(appointment))}",
        f"🕐 {esc(_when(appointment))}",
    ]
    if reason:
        lines.append(f"💬 {esc(reason)}")

    send_message(barber_user.telegram_chat_id, "\n".join(lines))

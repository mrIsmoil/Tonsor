"""Bron bo'yicha Telegram xabarnomalari.

Bu yerda faqat "kimga nima yozish" hal qilinadi. Xabarni yetkazish
`core.telegram` zimmasida — u xato ko'tarmaydi va so'rovni ushlab turmaydi,
shuning uchun bu funksiyalarni bron yaratish oqimidan bemalol chaqirish mumkin.

Til: xabar oluvchining saytdagi tanlagan tili emas, sodda o'zbekcha. Telegram
xabari qisqa bo'lishi kerak — uni telefon ekranida bir qarashda o'qiydi.
"""

import logging

from core.telegram import esc, send_message

logger = logging.getLogger(__name__)


def _when(appointment):
    """Sana va vaqtni o'qishga qulay ko'rinishda qaytaradi."""
    return f"{appointment.date:%d.%m.%Y}, {appointment.time:%H:%M}"


def _service_name(appointment):
    return appointment.service.name if appointment.service else 'Xizmat'


def _client_name(appointment):
    client = appointment.client
    full = (client.get_full_name() or '').strip()
    return full or client.username


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

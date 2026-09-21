"""PythonAnywhere uchun WSGI sozlamasi.

PythonAnywhere Procfile ishlatmaydi — u "Web" bo'limidagi WSGI faylga tayanadi.
Bu faylning mazmunini o'sha yerga (Web -> WSGI configuration file) nusxalang va
QUYIDAGI ikkita qatorni o'z foydalanuvchi nomingizga moslang.
"""

import os
import sys

# --- 1-qadam: loyiha yo'lini o'zingiznikiga almashtiring ---
# PythonAnywhere'da odatda: /home/<foydalanuvchi>/Tonsor
PROJECT_PATH = '/home/SIZNING_FOYDALANUVCHI_NOMINGIZ/Tonsor'

if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)

# --- 2-qadam: .env faylini yuklash ---
# Bu bo'lmasa SECRET_KEY, Telegram tokeni va Google kalitlari topilmaydi.
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_PATH, '.env'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

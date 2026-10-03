#!/usr/bin/env bash
#
# Serverdagi saytni yangilash. PythonAnywhere konsolida:
#
#     bash ~/Tonsor/deploy/update.sh
#
# Nega skript kerak: serverda to'rtta har xil Python o'rnatilgan va ularda
# Django'ning turli versiyalari yotibdi (python3.9 da 4.2, python3.10 da 5.0,
# qolganlarida esa kerakli kutubxonalar yo'q). Shunchaki `python manage.py ...`
# deb yozsangiz, qaysi biriga tushishingiz tasodifga bog'liq bo'lib qoladi.
# `collectstatic` noto'g'ri muhitda ishga tushsa shunchaki xato beradi, lekin
# `migrate` noto'g'ri Django versiyasida ishlasa bazaga sayt tushunmaydigan
# o'zgarish yozib qo'yadi. Shuning uchun bu yerda yo'l aniq ko'rsatilgan.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"
PIP="$PROJECT_DIR/.venv/bin/pip"

cd "$PROJECT_DIR"

if [ ! -x "$PYTHON" ]; then
    echo "XATO: virtual muhit topilmadi — $PYTHON" >&2
    echo "Uni yaratish uchun DEPLOY.md ning 2-bo'limiga qarang." >&2
    exit 1
fi

echo "==> Muhit"
"$PYTHON" -c "import sys, django; print('   Python', sys.version.split()[0], '| Django', django.get_version())"

echo "==> Kodni olish"
git pull

echo "==> Kutubxonalar"
"$PIP" install -q -r requirements.txt

echo "==> Sozlamalarni tekshirish"
# Migratsiyadan OLDIN tekshiramiz: sozlamada xato bo'lsa, bazaga tegmay
# shu yerda to'xtagan ma'qul.
"$PYTHON" manage.py check

echo "==> Shablonlar"
"$PYTHON" manage.py check_templates

echo "==> Baza"
"$PYTHON" manage.py migrate

echo "==> Statik fayllar"
"$PYTHON" manage.py collectstatic --noinput

echo
echo "Tayyor. Endi PythonAnywhere -> Web -> Reload tugmasini bosing."
echo "Reload'siz sayt eski kodda ishlayveradi."

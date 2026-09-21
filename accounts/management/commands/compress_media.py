"""Diskda allaqachon yotgan rasmlarni kichraytiradi.

Siqish qoidasi yangi yuklanadigan rasmlarga model darajasida qo'shildi, lekin
undan oldin saqlangan fayllar xom holda qolgan. Bu buyruq ularni bir marta
tozalab chiqadi — ayniqsa disk chegarasi qattiq bo'lgan hostingda kerak.

    python manage.py compress_media --dry-run   # faqat hisobot
    python manage.py compress_media             # haqiqatan siqadi
"""

import os
from io import BytesIO

from django.conf import settings
from django.core.management.base import BaseCommand

from core.uploads import JPEG_QUALITY, MAX_IMAGE_DIM

IMAGE_DIRS = ['profile_photos', 'shop_images', 'service_images']
IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}


class Command(BaseCommand):
    help = "Mavjud rasmlarni kichraytiradi (fayl nomi o'zgarmaydi)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Hech narsani o'zgartirmasdan, qancha joy tejalishini ko'rsatadi.",
        )
        parser.add_argument(
            '--all-dirs', action='store_true',
            help='social_videos ichidagi rasmlarni ham qamrab oladi.',
        )

    def handle(self, *args, **options):
        from PIL import Image, ImageOps

        dry = options['dry_run']
        dirs = IMAGE_DIRS + (['social_videos'] if options['all_dirs'] else [])

        before_total = after_total = 0
        changed = skipped = failed = 0

        for folder in dirs:
            root = os.path.join(settings.MEDIA_ROOT, folder)
            if not os.path.isdir(root):
                continue

            for dirpath, _dirnames, filenames in os.walk(root):
                for filename in sorted(filenames):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext not in IMAGE_EXT:
                        continue

                    path = os.path.join(dirpath, filename)
                    original = os.path.getsize(path)

                    try:
                        with Image.open(path) as img:
                            img.load()
                            img = ImageOps.exif_transpose(img)
                            img.thumbnail(
                                (MAX_IMAGE_DIM, MAX_IMAGE_DIM),
                                Image.Resampling.LANCZOS,
                            )
                            buffer = BytesIO()
                            # Fayl nomi o'zgarmagani uchun format ham
                            # o'zgarmasligi shart — aks holda .png nomli
                            # faylning ichida JPEG yotib qolardi va server
                            # brauzerga noto'g'ri turni e'lon qilardi.
                            if ext in ('.jpg', '.jpeg'):
                                img.convert('RGB').save(
                                    buffer, format='JPEG', quality=JPEG_QUALITY,
                                    optimize=True, progressive=True)
                            elif ext == '.png':
                                img.save(buffer, format='PNG', optimize=True)
                            elif ext == '.webp':
                                img.save(buffer, format='WEBP',
                                         quality=JPEG_QUALITY, method=6)
                            else:
                                skipped += 1
                                continue
                            data = buffer.getvalue()
                    except Exception as exc:
                        failed += 1
                        self.stderr.write(f'  ! {filename}: {exc}')
                        continue

                    before_total += original

                    # Faqat sezilarli yutuq bo'lsa almashtiramiz. Aks holda
                    # rasmni qayta-qayta siqib sifatini bekorga pasaytiramiz.
                    if len(data) >= original * 0.9:
                        after_total += original
                        skipped += 1
                        continue

                    after_total += len(data)
                    changed += 1
                    saved_pct = 100 * (1 - len(data) / original)
                    self.stdout.write(
                        f'  {filename[:52]:<52} '
                        f'{original/1048576:6.2f} MB -> {len(data)/1048576:5.2f} MB '
                        f'({saved_pct:.0f}%)'
                    )

                    if not dry:
                        # Nomi o'zgarmaydi — bazadagi yo'llar shundoq qoladi.
                        # Avval yonidagi vaqtinchalik faylga yozamiz, so'ng
                        # o'rniga qo'yamiz: uzilib qolsa ham asl fayl butun.
                        tmp = path + '.tmp'
                        with open(tmp, 'wb') as fh:
                            fh.write(data)
                        os.replace(tmp, path)

        self.stdout.write('')
        mode = 'SINOV (hech narsa o\'zgarmadi)' if dry else 'BAJARILDI'
        self.stdout.write(self.style.SUCCESS(f'--- {mode} ---'))
        self.stdout.write(
            f'Siqildi: {changed} | tegilmadi: {skipped} | xato: {failed}')
        if before_total:
            self.stdout.write(
                f'Hajm: {before_total/1048576:.1f} MB -> {after_total/1048576:.1f} MB '
                f'({100*(1-after_total/before_total):.0f}% tejaldi)'
            )

"""Yuklangan fayllarni tekshirish va siqish.

Ikkita muammoni hal qiladi:

1. **Disk to'lib qolishi.** Telefondan kelgan rasm odatda 4–8 MB. Ular xom
   holda saqlansa, yuzta salon bir necha gigabayt joy egallaydi. Saytda
   rasm hech qachon 1600px dan katta ko'rsatilmaydi, shuning uchun uni
   saqlashdan oldin kichraytiramiz — sifat ko'zga bilinmaydi, hajm esa
   20–40 barobar kamayadi.

2. **Suiiste'mol.** Hech qanday chegara bo'lmasa, bitta foydalanuvchi
   500 MB lik fayl yuklab diskni to'ldirib qo'yishi mumkin.
"""

from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile

# Qabul qilinadigan eng katta hajm (siqishdan OLDIN).
MAX_IMAGE_BYTES = 10 * 1024 * 1024   # 10 MB — zamonaviy telefon rasmi bemalol sig'adi
MAX_VIDEO_BYTES = 50 * 1024 * 1024   # 50 MB — ~60 soniyalik telefon videosi

# Saqlanadigan rasmning eng uzun tomoni.
MAX_IMAGE_DIM = 1600
JPEG_QUALITY = 82

IMAGE_FIELDS = {'profile_photo', 'shop_logo', 'image',
                'shop_image_1', 'shop_image_2', 'shop_image_3', 'shop_image_4'}
VIDEO_FIELDS = {'video_file'}


def limit_for(field_name):
    """Shu maydon uchun ruxsat etilgan eng katta hajm (bayt)."""
    if field_name in VIDEO_FIELDS:
        return MAX_VIDEO_BYTES
    return MAX_IMAGE_BYTES


def human_mb(num_bytes):
    return f'{num_bytes / (1024 * 1024):.0f} MB'


def _is_fresh_upload(field_file):
    """Maydonda hozir yuklangan yangi fayl bormi?

    Bazadan o'qilgan yozuvni qayta saqlaganda maydon allaqachon diskdagi
    faylga ishora qiladi — uni qayta siqish shart emas (va har safar
    siqilaverib sifati pasayib ketardi).
    """
    if not field_file:
        return False
    return isinstance(getattr(field_file, 'file', None), UploadedFile)


def compress_image(field_file):
    """Maydondagi yangi rasmni joyida kichraytiradi.

    Hech qachon xato ko'tarmaydi: rasmni ocholmasa yoki siqilgani aslidan
    kichik chiqmasa, faylni tegmasdan qoldiradi. Ya'ni eng yomon holatda
    ilgarigidek ishlaydi.
    """
    if not _is_fresh_upload(field_file):
        return False

    upload = field_file.file
    original_size = getattr(upload, 'size', 0)
    if original_size > MAX_IMAGE_BYTES:
        # Bunchalik kattasini Pillow xotiraga ochishi xavfli.
        # Hajm chegarasini UploadLimitMiddleware allaqachon ushlab qolgan.
        return False

    try:
        from PIL import Image, ImageOps

        upload.seek(0)
        img = Image.open(upload)
        img.load()

        # Telefon rasmlari EXIF'da "yonboshlagan" holda keladi; buni
        # hisobga olmasak, siqilgandan keyin rasm yonboshlab qoladi.
        img = ImageOps.exif_transpose(img)

        has_alpha = img.mode in ('RGBA', 'LA') or (
            img.mode == 'P' and 'transparency' in img.info
        )

        img.thumbnail((MAX_IMAGE_DIM, MAX_IMAGE_DIM), Image.Resampling.LANCZOS)

        buffer = BytesIO()
        if has_alpha:
            # Shaffof logotip oq fonli kvadratga aylanib qolmasligi uchun.
            img.convert('RGBA').save(buffer, format='PNG', optimize=True)
            suffix = '.png'
        else:
            img.convert('RGB').save(
                buffer, format='JPEG',
                quality=JPEG_QUALITY, optimize=True, progressive=True,
            )
            suffix = '.jpg'

        data = buffer.getvalue()
    except Exception:
        # Buzuq fayl, qo'llab-quvvatlanmaydigan format, xotira yetishmovchiligi —
        # qaysi biri bo'lsa ham yuklashni to'xtatishga arzimaydi.
        try:
            upload.seek(0)
        except Exception:
            pass
        return False

    if original_size and len(data) >= original_size:
        # Allaqachon yaxshi siqilgan kichik rasm — tegmaymiz.
        upload.seek(0)
        return False

    name = field_file.name or 'image'
    base = name.rsplit('/', 1)[-1].rsplit('.', 1)[0][:60] or 'image'
    field_file.save(base + suffix, ContentFile(data), save=False)
    return True

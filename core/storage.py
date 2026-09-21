"""Static fayllar uchun saqlash sinfi."""

import logging

from whitenoise.storage import CompressedManifestStaticFilesStorage, MissingFileError

logger = logging.getLogger(__name__)


class ForgivingStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """Yetishmayotgan yordamchi fayl tufayli deploy to'xtab qolmaydi.

    `collectstatic` har bir JS/CSS fayl ichidagi havolalarni topib, ularni
    hash qo'shilgan nomga almashtiradi. Havola qilingan fayl topilmasa,
    butun jarayon xato bilan to'xtaydi.

    Bizdagi `model-viewer.min.js` oxirida `sourceMappingURL=...js.map`
    qatori bor, lekin `.map` fayli kutubxona bilan birga kelmagan. U faqat
    brauzer dasturchi vositasi uchun kerak — saytda hech narsani buzmaydi.
    Shu bitta qator tufayli deploy to'xtab qolmasligi uchun bunday
    havolalarni ogohlantirish sifatida o'tkazib yuboramiz.

    Fayl baribir nusxalanadi va uzatiladi — faqat nomiga hash qo'shilmaydi.
    """

    # Manifestda yo'q fayl so'ralsa xato ko'tarmasin, oddiy nomga qaytsin.
    manifest_strict = False

    def post_process(self, paths, dry_run=False, **options):
        for name, hashed_name, processed in super().post_process(paths, dry_run, **options):
            if isinstance(processed, MissingFileError):
                logger.warning(
                    "Static: '%s' ichidagi havola topilmadi, hash qo'shilmadi (%s)",
                    name, processed,
                )
                # (nom, nom, False) — collectstatic buni "o'tkazib yuborildi"
                # deb yozadi va davom etadi.
                yield name, hashed_name or name, False
            else:
                yield name, hashed_name, processed

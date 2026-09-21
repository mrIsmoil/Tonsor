"""Shablonlardagi jim buziladigan xatolarni topadi.

Django shablon lekseri teg ichida qator o'tishini tushunmaydi: `{% ... %}` yoki
`{# ... #}` ikki qatorga bo'linsa, u teg sifatida umuman tanilmaydi va sahifada
oddiy matn bo'lib chiqib qoladi. Django bunga xato bermaydi — shuning uchun
buni faqat sahifaga qarab yoki shu tekshiruv bilan bilish mumkin.

Ishlatish:
    .venv/bin/python manage.py check_templates
"""

import glob
import os

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Qator oshib ketgan shablon teglari va izohlarini topadi"

    def handle(self, *args, **options):
        problems = []

        for path in sorted(glob.glob('templates/**/*.html', recursive=True)):
            with open(path, encoding='utf-8') as fh:
                for number, line in enumerate(fh, 1):
                    if '{#' in line and '#}' not in line:
                        problems.append((path, number, 'izoh', line.strip()[:70]))
                    if line.count('{%') > line.count('%}'):
                        problems.append((path, number, 'teg', line.strip()[:70]))
                    if line.count('{{') > line.count('}}'):
                        problems.append((path, number, "o'zgaruvchi", line.strip()[:70]))

        if not problems:
            self.stdout.write(self.style.SUCCESS(
                'Barcha shablonlar toza — qator oshib ketgan teg topilmadi.'
            ))
            return

        self.stdout.write(self.style.ERROR(
            f'{len(problems)} ta muammo topildi (teg bir qatorda tugashi shart):'
        ))
        for path, number, kind, text in problems:
            self.stdout.write(f'  {path}:{number} [{kind}] {text}')

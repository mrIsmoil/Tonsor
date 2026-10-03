"""Loyiha taqdimoti sahifalari.

Mahsulotning o'zidan ajratilgan: bu sahifalar mijoz uchun emas, loyihani
baholayotgan odam uchun — tanlov hakamlari, investorlar, hamkorlar.
"""

from django.conf import settings
from django.shortcuts import render


def project(request):
    """Muammo, yechim, jamoa, yo'l xaritasi va amalga oshirish rejasi."""
    return render(request, 'pages/project.html')


def demo(request):
    """Demo video, uning tavsifi va ishlayotgan prototipga havola.

    Video havolasi .env orqali beriladi, shunda uni almashtirish uchun
    kodga tegish shart emas.
    """
    return render(request, 'pages/demo.html', {
        'demo_video_embed': getattr(settings, 'DEMO_VIDEO_EMBED', ''),
    })

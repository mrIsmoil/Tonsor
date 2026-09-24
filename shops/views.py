from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from bookings import notifications
from bookings.models import Appointment
from .models import BarberProfile, ShopInvite
from social.models import VideoPost, Follower, Like

@login_required
def dashboard(request):
    if not hasattr(request.user, 'barber_profile'):
        if request.user.is_barber:
            return redirect('accounts:barber_setup')
        return redirect('accounts:home')
        
    profile = request.user.barber_profile
    
    # Auto-complete finished services
    from datetime import timedelta
    now = timezone.now()
    in_progress = profile.appointments.filter(status='in_progress')
    for app in in_progress:
        if app.started_at:
            duration = app.service.duration_minutes if app.service else 30
            if now >= app.started_at + timedelta(minutes=duration):
                app.status = 'completed'
                app.completed_at = now
                app.save()

    pending_appointments = profile.appointments.filter(status='pending').select_related('client', 'service', 'employee').order_by('date', 'time')
    upcoming_appointments = profile.appointments.filter(status='accepted').select_related('client', 'service', 'employee').order_by('date', 'time')
    in_progress_appointments = profile.appointments.filter(status='in_progress').select_related('client', 'service', 'employee').order_by('started_at')
    
    # Client cancellations (visible for 5 mins)
    client_cancelled = profile.appointments.filter(
        status='canceled', client_cancel_reason__gt='',
        cancelled_at__gte=now - timedelta(minutes=5)
    ).select_related('client', 'service', 'employee').order_by('-cancelled_at')
    
    # Telegram xabarnomalari: sartarosh ulanmagan bo'lsa, bog'lash havolasini
    # ko'rsatamiz. Mavjud kod qayta ishlatiladi — aks holda sahifani yangilash
    # avval ochilgan havolani o'lik qilib qo'yardi.
    telegram_linked = bool(request.user.telegram_chat_id)
    telegram_link_url = ''
    bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', '')
    if not telegram_linked and bot_username:
        code = request.user.telegram_link_code or request.user.issue_telegram_link_code()
        telegram_link_url = f'https://t.me/{bot_username}?start={code}'

    context = {
        'pending_appointments': pending_appointments,
        'upcoming_appointments': upcoming_appointments,
        'in_progress_appointments': in_progress_appointments,
        'client_cancelled': client_cancelled,
        'telegram_linked': telegram_linked,
        'telegram_link_url': telegram_link_url,
    }
    return render(request, 'shops/dashboard.html', context)

@login_required
def appointment_action(request, id, action):
    appointment = get_object_or_404(Appointment, id=id, barber__user=request.user)
    cancel_note = ''
    if action == 'accept':
        appointment.status = 'accepted'
    elif action == 'cancel':
        appointment.status = 'canceled'
        if request.method == 'POST':
            note = request.POST.get('note', '')
            if note:
                appointment.barber_note = note
                cancel_note = note
    elif action == 'arrived':
        appointment.status = 'in_progress'
        appointment.started_at = timezone.now()
    elif action == 'no_show':
        appointment.status = 'no_show'

    appointment.save()

    # Mijoz javobni kutib o'tirmasligi uchun darhol xabar beramiz.
    if action == 'accept':
        notifications.notify_client_accepted(appointment)
    elif action == 'cancel':
        notifications.notify_client_canceled(appointment, cancel_note)

    return redirect('shops:dashboard')

def barber_profile(request, barber_id):
    barber = get_object_or_404(BarberProfile, id=barber_id)
    videos = VideoPost.objects.filter(barber=barber).order_by('-created_at')
    
    # Add like status for each video
    for video in videos:
        video.is_liked = False
        if request.user.is_authenticated:
            video.is_liked = Like.objects.filter(user=request.user, video=video).exists()
        video.like_count = video.likes.count()

    is_following = False
    if request.user.is_authenticated:
        is_following = Follower.objects.filter(client=request.user, barber=barber).exists()
    
    follower_count = barber.followers.count()

    # Tasdiqlanmagan salonda mijozlar "meni shu yerga yozing" signalini qoldiradi.
    invite_count = 0
    already_invited = False
    if not barber.is_claimed:
        invite_count = barber.invites.count()
        if request.user.is_authenticated:
            already_invited = barber.invites.filter(client=request.user).exists()

    context = {
        'barber': barber,
        'videos': videos,
        'is_following': is_following,
        'follower_count': follower_count,
        'invite_count': invite_count,
        'already_invited': already_invited,
    }
    return render(request, 'shops/barber_profile.html', context)

@login_required
def toggle_shop_status(request):
    """Manually toggle the open/closed status for flexible-hour barbers."""
    if request.method == 'POST' and hasattr(request.user, 'barber_profile'):
        profile = request.user.barber_profile
        profile.is_open_now = not profile.is_open_now
        profile.save()
        return JsonResponse({'status': 'ok', 'is_open_now': profile.is_open_now})
    return JsonResponse({'status': 'error'}, status=400)

def get_shop_status(barber):
    """Calculates if a barber is currently open."""
    if barber.depends_on_owner:
        return barber.is_open_now
    
    # Fixed schedule calculation
    now = timezone.localtime(timezone.now())
    current_day = now.strftime('%a') # Mon, Tue, etc.
    current_time = now.time()
    
    allowed_days = barber.work_days.split(',') if barber.work_days else []
    if current_day not in allowed_days:
        return False
        
    if barber.open_time and barber.close_time:
        return barber.open_time <= current_time <= barber.close_time
        
    return False

@login_required
def today_schedule(request):
    if not hasattr(request.user, 'barber_profile'):
        return redirect('accounts:home')
        
    profile = request.user.barber_profile
    from django.utils import timezone
    from django.db.models import Sum
    now_local = timezone.localtime(timezone.now())
    today = now_local.date()
    
    appointments = Appointment.objects.filter(
        barber=profile, 
        date=today
    ).select_related('client', 'service', 'employee').order_by('time')
    
    # Simple summary stats
    completed_count = appointments.filter(status='completed').count()
    pending_count = appointments.filter(status__in=['pending', 'accepted', 'in_progress']).count()
    
    # Earnings
    daily_earnings = appointments.filter(status='completed').aggregate(Sum('service__price'))['service__price__sum'] or 0
    
    # Calculate this month
    monthly_earnings = Appointment.objects.filter(
        barber=profile,
        status='completed',
        date__month=now_local.month,
        date__year=now_local.year
    ).aggregate(Sum('service__price'))['service__price__sum'] or 0
    
    # Calculate last month
    last_month = now_local.month - 1 or 12
    last_month_year = now_local.year if now_local.month > 1 else now_local.year - 1
    last_month_earnings = Appointment.objects.filter(
        barber=profile,
        status='completed',
        date__month=last_month,
        date__year=last_month_year
    ).aggregate(Sum('service__price'))['service__price__sum'] or 0
    
    # Yearly earnings by month (12 values)
    from django.db.models.functions import ExtractMonth
    yearly_query = Appointment.objects.filter(
        barber=profile,
        status='completed',
        date__year=now_local.year
    ).annotate(month=ExtractMonth('date')).values('month').annotate(total=Sum('service__price')).order_by('month')
    
    yearly_earnings_by_month = [0] * 12
    for entry in yearly_query:
        if 1 <= entry['month'] <= 12:
            yearly_earnings_by_month[entry['month'] - 1] = float(entry['total'] or 0)
    
    context = {
        'appointments': appointments,
        'today': today,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'daily_earnings': daily_earnings,
        'monthly_earnings': monthly_earnings,
        'last_month_earnings': last_month_earnings,
        'yearly_earnings_by_month': yearly_earnings_by_month,
    }
    return render(request, 'shops/schedule.html', context)

def get_all_shop_statuses(request):
    """API endpoint to get the status of all barbers."""
    barbers = BarberProfile.objects.all()
    statuses = {b.id: get_shop_status(b) for b in barbers}
    return JsonResponse(statuses)


@login_required
def quick_add_shop(request):
    """Sartaroshxonani tez qo'shish — baza yig'ish uchun asosiy vosita.

    Salon yig'ayotganda siz sartaroshxona ichida turgan bo'lasiz, ya'ni telefoningizning
    GPS koordinatasi aynan do'kon manzili. Shuning uchun "hozirgi joylashuvim"
    asosiy usul, xaritani qo'lda surish esa zaxira.

    Faqat xodimlar (is_staff) uchun: bu forma orqali kiritilgan profil egasiz
    bo'ladi va bron qabul qilmaydi, shuning uchun uni ochiq qoldirib bo'lmaydi.
    """
    if not request.user.is_staff:
        return redirect('accounts:home')

    error = None
    created = None

    if request.method == 'POST':
        shop_name = (request.POST.get('shop_name') or '').strip()
        phone = (request.POST.get('contact_phone') or '').strip()
        address = (request.POST.get('address') or '').strip()
        shop_type = request.POST.get('shop_type', 'men')
        lat_raw = request.POST.get('location_lat') or ''
        lng_raw = request.POST.get('location_lng') or ''

        try:
            lat = float(lat_raw) if lat_raw else None
            lng = float(lng_raw) if lng_raw else None
        except ValueError:
            lat = lng = None

        if not shop_name:
            error = 'Please enter the shop name.'
        elif shop_type not in dict(BarberProfile.SHOP_TYPE_CHOICES):
            error = 'Please choose the shop type.'
        else:
            profile = BarberProfile.objects.create(
                shop_name=shop_name,
                shop_type=shop_type,
                contact_phone=phone,
                address=address,
                location_lat=lat,
                location_lng=lng,
                user=None,
                is_claimed=False,
            )
            profile.generate_claim_code()
            created = profile

    context = {
        'error': error,
        'created': created,
        'shop_count': BarberProfile.objects.count(),
        'unclaimed_count': BarberProfile.objects.filter(is_claimed=False).count(),
        'YANDEX_MAPS_API_KEY': getattr(settings, 'YANDEX_MAPS_API_KEY', ''),
    }
    return render(request, 'shops/quick_add.html', context)


@login_required
def invite_shop(request, barber_id):
    """Mijoz tasdiqlanmagan salonni Tonsorga taklif qilishni so'raydi.

    Bu bron emas — hech kimga va'da berilmaydi. Faqat "menga shu salon kerak"
    degan signal. To'plangan signallar sartaroshga borganda dalil bo'ladi:
    "Tonsorda N kishi sizni so'radi".
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)

    shop = get_object_or_404(BarberProfile, id=barber_id)
    if shop.is_claimed:
        # Tasdiqlangan salonni taklif qilishning ma'nosi yo'q — u allaqachon shu yerda.
        return JsonResponse({'status': 'error', 'reason': 'already_claimed'}, status=400)

    ShopInvite.objects.get_or_create(shop=shop, client=request.user)
    return JsonResponse({'status': 'ok', 'count': shop.invites.count()})

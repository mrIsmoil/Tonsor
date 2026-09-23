from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.geo import format_distance, haversine_km, parse_coords
from shops.models import BarberProfile, Service
from social.models import VideoPost
from . import notifications
from .models import Appointment

@login_required
def client_home(request):
    from social.models import VideoPost, SavedPost
    videos = VideoPost.objects.all().order_by('-created_at').prefetch_related('likes', 'comments', 'comments__user')
    # Fetch unrated completed appointments
    unrated_appointments = Appointment.objects.filter(client=request.user, status='completed', is_rated=False).select_related('barber', 'service')
    
    return render(request, 'bookings/client_home.html', {
        'videos': videos,
        'unrated_appointments': unrated_appointments
    })

@login_required
def my_appointments(request):
    from django.utils import timezone
    from datetime import timedelta
    now = timezone.now()
    
    # Auto-complete finished services on client load too
    in_progress = Appointment.objects.filter(client=request.user, status='in_progress')
    for app in in_progress:
        if app.started_at:
            duration = app.service.duration_minutes if app.service else 30
            if now >= app.started_at + timedelta(minutes=duration):
                app.status = 'completed'
                app.completed_at = now
                app.save()

    all_appointments = Appointment.objects.filter(client=request.user).select_related('barber', 'service', 'employee').order_by('-date', '-time')
    
    upcoming = all_appointments.filter(status__in=['pending', 'accepted'])
    live = all_appointments.filter(status='in_progress')
    past = all_appointments.filter(status__in=['completed', 'canceled', 'no_show'])
    
    context = {
        'upcoming': upcoming,
        'live': live,
        'past': past,
    }
    return render(request, 'bookings/my_appointments.html', context)

@login_required
def rate_appointment(request, id):
    appointment = get_object_or_404(Appointment, id=id, client=request.user)
    if request.method == 'POST':
        is_good = request.POST.get('rating') == 'good'
        appointment.is_rated = True
        appointment.rating_is_good = is_good
        appointment.save()
        
        # Update Barber Rating
        barber = appointment.barber
        if is_good:
            barber.good_ratings_count += 1
            if barber.good_ratings_count >= 5:
                barber.rating = min(5.0, barber.rating + 0.5)
                barber.good_ratings_count = 0
        else:
            barber.bad_ratings_count += 1
            if barber.bad_ratings_count >= 2:
                barber.rating = max(0.0, barber.rating - 0.5)
                barber.bad_ratings_count = 0
        barber.save()
        
        return redirect('bookings:client_home')
    return redirect('bookings:client_home')

@login_required
def book_appointment(request, barber_id):
    if request.user.is_barber:
        return redirect('shops:dashboard')
        
    barber = get_object_or_404(BarberProfile, id=barber_id)

    # Egasi tasdiqlamagan salonga bron qabul qilinmaydi: sartarosh bu haqda
    # xabar ololmaydi, ya'ni mijozga bajarilmaydigan va'da berilgan bo'lardi.
    # Tugma shablonda ham yashirilgan, lekin manzilni qo'lda kiritish mumkin —
    # shuning uchun asosiy to'siq shu yerda.
    if not barber.is_claimed:
        return redirect('shops:barber_profile', barber_id=barber.id)

    services = barber.services.all()

    if request.method == 'POST':
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        service_id = request.POST.get('service_id')
        comment = request.POST.get('comment', '')
        
        if not date_str or not time_str:
            return render(request, 'bookings/book_appointment.html', {
                'barber': barber,
                'services': services,
                'error': "Please select both a date and time for your appointment."
            })
        
        # Server-side validation
        try:
            from datetime import datetime
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            selected_time = datetime.strptime(time_str, '%H:%M').time()
            
            # Check work days
            day_name = selected_date.strftime('%a') # Mon, Tue, etc.
            allowed_days = barber.work_days.split(',') if barber.work_days else []
            
            is_valid = True
            error_msg = None
            
            if allowed_days and day_name not in allowed_days:
                is_valid = False
                error_msg = f"The shop is closed on {selected_date.strftime('%A')}s."
            
            if is_valid and barber.open_time and barber.close_time:
                if not (barber.open_time <= selected_time <= barber.close_time):
                    is_valid = False
                    error_msg = f"Please select a time between {barber.open_time.strftime('%H:%M')} and {barber.close_time.strftime('%H:%M')}."
            
            if not is_valid:
                return render(request, 'bookings/book_appointment.html', {
                    'barber': barber,
                    'services': services,
                    'error': error_msg
                })
                
        except (ValueError, TypeError):
            return render(request, 'bookings/book_appointment.html', {
                'barber': barber,
                'services': services,
                'error': "Invalid date or time format selected."
            })

        service = None
        if service_id:
            service = get_object_or_404(Service, id=service_id)

        employee = None
        employee_id = request.POST.get('employee_id')
        if employee_id:
            from shops.models import Employee
            employee = get_object_or_404(Employee, id=employee_id, profile=barber)
            
        appointment = Appointment.objects.create(
            client=request.user,
            barber=barber,
            service=service,
            employee=employee,
            # Matn emas, yuqorida tekshirilgan haqiqiy sana/vaqt obyektlari.
            # Matn uzatilsa Django uni bazaga to'g'ri yozadi, lekin xotiradagi
            # obyektda matn bo'lib qoladi — keyin uni sana sifatida
            # formatlamoqchi bo'lgan kod qulaydi.
            date=selected_date,
            time=selected_time,
            client_comment=comment
        )
        notifications.notify_barber_new_booking(appointment)
        return redirect('bookings:client_home')
        
    context = {
        'barber': barber,
        'services': services
    }
    return render(request, 'bookings/book_appointment.html', context)

@login_required
def search_barbers(request):
    """Salon qidiruvi — nomi bo'yicha va joylashuvi bo'yicha.

    Mijoz uchun eng muhim savol "qaysi salon yaqin?" bo'lgani uchun,
    joylashuv ma'lum bo'lsa ro'yxat masofa bo'yicha saralanadi va har bir
    kartochkada masofa ko'rsatiladi. Joylashuv noma'lum bo'lsa oldingidek
    oddiy ro'yxat chiqadi — hech narsa buzilmaydi.
    """
    query = (request.GET.get('q') or '').strip()

    barbers = BarberProfile.objects.all()
    if query:
        barbers = barbers.filter(
            Q(shop_name__icontains=query) | Q(address__icontains=query)
        )

    # Joylashuv uch manbadan kelishi mumkin, ishonch tartibida:
    # 1) so'rovdagi koordinata (brauzer hozir aniqladi),
    # 2) profilda saqlangan koordinata,
    # 3) umuman yo'q.
    coords = parse_coords(request.GET.get('lat'), request.GET.get('lng'))
    if coords is None and request.user.is_authenticated:
        coords = parse_coords(request.user.latitude, request.user.longitude)

    barbers = list(barbers)
    lang = request.session.get('masterpiece_lang', 'uz')

    if coords:
        user_lat, user_lng = coords
        for shop in barbers:
            shop.distance_km = haversine_km(
                user_lat, user_lng, shop.location_lat, shop.location_lng
            )
            shop.distance_text = format_distance(shop.distance_km, lang)
        # Koordinatasi yo'q salonlar oxirida tursin — ularni yashirish
        # noto'g'ri bo'lardi, chunki ular ham haqiqiy salonlar.
        barbers.sort(key=lambda s: (s.distance_km is None, s.distance_km or 0))
    else:
        for shop in barbers:
            shop.distance_km = None
            shop.distance_text = ''

    return render(request, 'bookings/search_barbers.html', {
        'barbers': barbers,
        'query': query,
        'has_location': bool(coords),
    })

@login_required
def cancel_appointment(request, id):
    from django.http import JsonResponse
    import json
    appointment = get_object_or_404(Appointment, id=id, client=request.user)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            reason = data.get('reason', '').strip()
        except Exception:
            reason = ''
        appointment.status = 'canceled'
        appointment.client_cancel_reason = reason
        from django.utils import timezone
        appointment.cancelled_at = timezone.now()
        appointment.save()
        notifications.notify_barber_client_canceled(appointment, reason)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def mark_notification_read(request):
    from django.http import JsonResponse
    import json
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])
            Appointment.objects.filter(
                id__in=ids, client=request.user, status='accepted'
            ).update(client_notified=True)
            return JsonResponse({'status': 'ok'})
        except Exception:
            pass
    return JsonResponse({'status': 'error'}, status=400)

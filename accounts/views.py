import re

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth import authenticate, login, get_user_model, update_session_auth_hash
from django.utils import translation

USERNAME_RE = re.compile(r'^[A-Za-z0-9_.]{3,30}$')


def _post_login_redirect(user):
    """Send a freshly authenticated user to the right home, mirroring `home`."""
    if user.is_barber:
        return redirect('shops:dashboard')
    if not user.is_client:
        user.is_client = True
        user.save(update_fields=['is_client'])
    return redirect('bookings:client_home')


def home(request):
    if request.user.is_authenticated:
        if not request.user.is_barber and not request.user.is_client:
            request.user.is_client = True
            request.user.save()
            return redirect('bookings:client_home')
        elif request.user.is_barber:
            return redirect('shops:dashboard')
        else:
            return redirect('bookings:client_home')
    return render(request, 'accounts/home.html')

def login_view(request):
    """Sign-in. Accepts a phone number, an email address or a username.

    Telefon — sartaroshlar uchun asosiy identifikator: claim orqali kelganlarda
    email umuman bo'lmaydi. Raqam har xil yozilishi mumkin, shuning uchun
    normallashtirilgan ko'rinishda qidiriladi.
    """
    if request.user.is_authenticated:
        return _post_login_redirect(request.user)

    error = None
    identifier = ''

    if request.method == 'POST':
        identifier = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''

        if not identifier or not password:
            error = 'Please enter your email and password.'
        else:
            user = authenticate(request, username=identifier, password=password)

            # Identifikator email yoki telefon bo'lishi mumkin — ikkalasi ham
            # haqiqiy username emas, shuning uchun egasini topib, keyin uning
            # username'i bilan autentifikatsiya qilamiz.
            if user is None:
                from accounts.models import normalize_phone
                User = get_user_model()
                match = User.objects.filter(email__iexact=identifier).first()
                if match is None:
                    phone = normalize_phone(identifier)
                    if phone:
                        match = User.objects.filter(phone=phone).first()
                if match:
                    user = authenticate(request, username=match.get_username(), password=password)

            if user is None:
                error = 'Email or password is incorrect.'
            elif not user.is_active:
                error = 'This account has been deactivated.'
            else:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return _post_login_redirect(user)

    return render(request, 'accounts/login.html', {'error': error, 'identifier': identifier})

def barber_entry(request):
    from shops.services_config import MENS_SERVICES, WOMENS_SERVICES
    
    # Prepare keys for services to avoid complex template logic (Men)
    prepared_mens_services = []
    for cat in MENS_SERVICES:
        cat_services = []
        for svc in cat['services']:
            key = svc.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace('-', '_').replace('✂️', '').replace('🧔', '').replace('💇‍♂️', '').replace('🧴', '').replace('👂', '').replace('🔥', '').replace('📦', '').strip('_')
            cat_services.append({'name': svc, 'key': key})
        prepared_mens_services.append({
            'category': cat['category'], 
            'services': cat_services,
            'icon': cat.get('icon', 'fas fa-star')
        })

    # Prepare keys for services (Women)
    prepared_womens_services = []
    for cat in WOMENS_SERVICES:
        cat_services = []
        for svc in cat['services']:
            # Create a simple, safe key for women's services too
            key = svc.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace('-', '_').replace('💇‍♀️', '').replace('🎨', '').replace('✨', '').replace('💅', '').replace('🧴', '').replace('👁️', '').replace('💄', '').replace('🧖‍♀️', '').replace('💆‍♀️', '').replace('👰', '').strip('_')
            cat_services.append({'name': svc, 'key': key})
        prepared_womens_services.append({
            'category': cat['category'], 
            'services': cat_services,
            'icon': cat.get('icon', 'fas fa-star')
        })

    # Only registration/login submissions run the block below; GET falls through
    if request.method == 'POST':
        action = request.POST.get('action', 'register')
        
        if action == 'login':
            login_email = request.POST.get('login_email')
            login_password = request.POST.get('login_password')
            login_shop_name = request.POST.get('login_shop_name')
            
            from django.contrib.auth import authenticate, login
            # Use email as username for authentication
            user = authenticate(request, username=login_email, password=login_password)
            
            if user is not None:
                if user.is_barber and hasattr(user, 'barber_profile'):
                    profile = user.barber_profile
                    if profile.shop_name.strip().lower() == login_shop_name.strip().lower():
                        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                        return redirect('shops:dashboard')
                    else:
                        error = 'Invalid Shop Name for this account.'
                else:
                    error = 'This account is not a barber account.'
            else:
                error = 'Invalid Email or Password.'
                
            return render(request, 'accounts/barber_entry.html', {
                'error': error,
                'YANDEX_MAPS_API_KEY': getattr(settings, 'YANDEX_MAPS_API_KEY', ''),
                'MENS_SERVICES': prepared_mens_services,
                'WOMENS_SERVICES': prepared_womens_services
            })

        # Handle manual registration (default action)
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        shop_name = request.POST.get('shop_name')
        shop_type = request.POST.get('shop_type', 'men')
        location = request.POST.get('location')
        location_lat = request.POST.get('location_lat')
        location_lng = request.POST.get('location_lng')
        depends_on_owner = request.POST.get('depends_on_owner') == 'on'
        open_time = request.POST.get('open_time') if not depends_on_owner else None
        close_time = request.POST.get('close_time') if not depends_on_owner else None
        work_days_list = request.POST.getlist('work_days')
        work_days = ",".join(work_days_list) if not depends_on_owner and work_days_list else "Mon,Tue,Wed,Thu,Fri,Sat,Sun"
        
        if password and (not password.isdigit() or len(password) != 6):
            return render(request, 'accounts/barber_entry.html', {
                'error': 'Password must be exactly 6 digits.',
                'YANDEX_MAPS_API_KEY': getattr(settings, 'YANDEX_MAPS_API_KEY', ''),
                'MENS_SERVICES': prepared_mens_services,
                'WOMENS_SERVICES': prepared_womens_services
            })
            
        if email and password and first_name and shop_name:
            from django.contrib.auth import get_user_model, login
            User = get_user_model()
            from shops.models import BarberProfile
            
            # Use email as username if not provided
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_barber=True
                )
                
                # Parse decimals safely
                try:
                    lat = float(location_lat) if location_lat else None
                    lng = float(location_lng) if location_lng else None
                except ValueError:
                    lat = None
                    lng = None

                currency = request.POST.get('currency', 'UZS')
                if shop_type == 'women':
                    currency = request.POST.get('currency_women', 'UZS')

                profile = BarberProfile.objects.create(
                    user=user, 
                    shop_name=shop_name,
                    shop_type=shop_type,
                    currency=currency,
                    address=location,
                    location_lat=lat,
                    location_lng=lng,
                    depends_on_owner=depends_on_owner,
                    open_time=open_time if open_time else None,
                    close_time=close_time if close_time else None,
                    work_days=work_days if not depends_on_owner else ""
                )

                # Handle Shop Logo
                if 'shop_logo' in request.FILES:
                    user.profile_photo = request.FILES['shop_logo']
                    user.save()

                # Handle Atmosphere Photos
                from shops.models import ShopImage
                for i in range(1, 5):
                    img_key = f'shop_image_{i}'
                    if img_key in request.FILES:
                        ShopImage.objects.create(
                            profile=profile,
                            image=request.FILES[img_key],
                            is_logo=False
                        )

                # Process Workers
                from shops.models import Employee
                worker_first_names = request.POST.getlist('worker_first_name')
                worker_last_names = request.POST.getlist('worker_last_name')
                
                for fn, ln in zip(worker_first_names, worker_last_names):
                    if fn.strip():
                        Employee.objects.create(
                            profile=profile,
                            first_name=fn.strip(),
                            last_name=ln.strip() if ln else "",
                            role='professional'
                        )

                # Handle selected services
                if shop_type == 'men':
                    from shops.models import Service
                    selected_service_keys = request.POST.getlist('selected_services')
                    for category_item in prepared_mens_services:
                        for svc in category_item['services']:
                            if svc['key'] in selected_service_keys:
                                price_key = f"service_price_{svc['key']}"
                                duration_hours = request.POST.get(f"service_duration_hours_{svc['key']}", 0)
                                duration_mins = request.POST.get(f"service_duration_mins_{svc['key']}", 30)
                                duration = (int(duration_hours) * 60) + int(duration_mins)
                                price = request.POST.get(price_key)

                                currency = "UZS"

                                if price and float(price) > 0:
                                    Service.objects.create(
                                        profile=profile,
                                        name=svc['name'],
                                        price=float(price),
                                        currency=currency,
                                        duration_minutes=int(duration)
                                    )
                elif shop_type == 'women':
                    from shops.models import Service
                    selected_service_keys = request.POST.getlist('selected_services')
                    for category_item in prepared_womens_services:
                        for svc in category_item['services']:
                            if svc['key'] in selected_service_keys:
                                price_key = f"service_price_{svc['key']}"
                                duration_hours = request.POST.get(f"service_duration_hours_{svc['key']}", 0)
                                duration_mins = request.POST.get(f"service_duration_mins_{svc['key']}", 30)
                                duration = (int(duration_hours) * 60) + int(duration_mins)
                                price = request.POST.get(price_key)

                                currency = "UZS"

                                if price and float(price) > 0:
                                    Service.objects.create(
                                        profile=profile,
                                        name=svc['name'],
                                        price=float(price),
                                        currency=currency,
                                        duration_minutes=int(duration)
                                    )
                
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return redirect('shops:dashboard')
            else:
                # Handle error: user already exists
                return render(request, 'accounts/barber_entry.html', {
                    'error': 'A user with this email already exists.',
                    'YANDEX_MAPS_API_KEY': getattr(settings, 'YANDEX_MAPS_API_KEY', ''),
                    'MENS_SERVICES': prepared_mens_services,
                    'WOMENS_SERVICES': prepared_womens_services
                })
        else:
            # Required fields missing — say so instead of silently redisplaying an empty form
            return render(request, 'accounts/barber_entry.html', {
                'error': 'Please fill in your name, email, PIN and shop name.',
                'YANDEX_MAPS_API_KEY': getattr(settings, 'YANDEX_MAPS_API_KEY', ''),
                'MENS_SERVICES': prepared_mens_services,
                'WOMENS_SERVICES': prepared_womens_services
            })

    return render(request, 'accounts/barber_entry.html', {
        'YANDEX_MAPS_API_KEY': getattr(settings, 'YANDEX_MAPS_API_KEY', ''),
        'MENS_SERVICES': prepared_mens_services,
        'WOMENS_SERVICES': prepared_womens_services
    })

@login_required
def barber_setup(request):
    from shops.services_config import MENS_SERVICES, WOMENS_SERVICES
    # Prepare keys for services (Men)
    prepared_mens_services = []
    for cat in MENS_SERVICES:
        cat_services = []
        for svc in cat['services']:
            key = svc.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace('-', '_').replace('✂️', '').replace('🧔', '').replace('💇‍♂️', '').replace('🧴', '').replace('👂', '').replace('🔥', '').replace('📦', '').strip('_')
            cat_services.append({'name': svc, 'key': key})
        prepared_mens_services.append({
            'category': cat['category'], 
            'services': cat_services,
            'icon': cat.get('icon', 'fas fa-star')
        })

    # Prepare keys for services (Women)
    prepared_womens_services = []
    for cat in WOMENS_SERVICES:
        cat_services = []
        for svc in cat['services']:
            key = svc.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace('-', '_').replace('💇‍♀️', '').replace('🎨', '').replace('✨', '').replace('💅', '').replace('🧴', '').replace('👁️', '').replace('💄', '').replace('🧖‍♀️', '').replace('💆‍♀️', '').replace('👰', '').strip('_')
            cat_services.append({'name': svc, 'key': key})
        prepared_womens_services.append({
            'category': cat['category'], 
            'services': cat_services,
            'icon': cat.get('icon', 'fas fa-star')
        })

    if request.method == 'POST':
        shop_name = request.POST.get('shop_name')
        shop_type = request.POST.get('shop_type', 'men')
        depends_on_owner = request.POST.get('depends_on_owner') == 'on'
        open_time = request.POST.get('open_time') if not depends_on_owner else None
        close_time = request.POST.get('close_time') if not depends_on_owner else None
        work_days_list = request.POST.getlist('work_days')
        work_days = ",".join(work_days_list) if not depends_on_owner and work_days_list else "Mon,Tue,Wed,Thu,Fri,Sat,Sun"
        
        currency = request.POST.get('currency', 'UZS')
        if shop_type == 'women':
            currency = request.POST.get('currency_women', 'UZS')

        from shops.models import BarberProfile
        profile = BarberProfile.objects.create(
            user=request.user, 
            shop_name=shop_name,
            shop_type=shop_type,
            currency=currency,
            depends_on_owner=depends_on_owner,
            open_time=open_time if open_time else None,
            close_time=close_time if close_time else None,
            work_days=work_days if not depends_on_owner else ""
        )

        # Handle Shop Logo
        if 'shop_logo' in request.FILES:
            request.user.profile_photo = request.FILES['shop_logo']
            request.user.save()

        # Handle Atmosphere Photos
        from shops.models import ShopImage
        for i in range(1, 5):
            img_key = f'shop_image_{i}'
            if img_key in request.FILES:
                ShopImage.objects.create(
                    profile=profile,
                    image=request.FILES[img_key],
                    is_logo=False
                )

        # Handle selected services
        if shop_type == 'men':
            from shops.models import Service
            selected_service_keys = request.POST.getlist('selected_services')
            for category_item in prepared_mens_services:
                for svc in category_item['services']:
                    if svc['key'] in selected_service_keys:
                        price_key = f"service_price_{svc['key']}"
                        duration_hours = request.POST.get(f"service_duration_hours_{svc['key']}", 0)
                        duration_mins = request.POST.get(f"service_duration_mins_{svc['key']}", 30)
                        duration = (int(duration_hours) * 60) + int(duration_mins)
                        price = request.POST.get(price_key)

                        currency = "UZS"

                        if price and float(price) > 0:
                            Service.objects.create(
                                profile=profile,
                                name=svc['name'],
                                price=float(price),
                                currency=currency,
                                duration_minutes=int(duration)
                            )
        elif shop_type == 'women':
            from shops.models import Service
            selected_service_keys = request.POST.getlist('selected_services')
            for category_item in prepared_womens_services:
                for svc in category_item['services']:
                    if svc['key'] in selected_service_keys:
                        price_key = f"service_price_{svc['key']}"
                        duration_hours = request.POST.get(f"service_duration_hours_{svc['key']}", 0)
                        duration_mins = request.POST.get(f"service_duration_mins_{svc['key']}", 30)
                        duration = (int(duration_hours) * 60) + int(duration_mins)
                        price = request.POST.get(price_key)

                        currency = "UZS"

                        if price and float(price) > 0:
                            Service.objects.create(
                                profile=profile,
                                name=svc['name'],
                                price=float(price),
                                currency=currency,
                                duration_minutes=int(duration)
                            )
        return redirect('shops:dashboard')
    return render(request, 'accounts/barber_setup.html', {
        'MENS_SERVICES': prepared_mens_services,
        'WOMENS_SERVICES': prepared_womens_services
    })

@login_required
def profile_view(request):
    user = request.user
    from social.models import Follower, SavedPost, VideoPost
    from bookings.models import Appointment
    from django.utils import timezone
    from datetime import timedelta
    five_mins_ago = timezone.now() - timedelta(minutes=5)
    
    context = {'user': user}
    
    if user.is_barber and hasattr(user, 'barber_profile'):
        profile = user.barber_profile
        followers = Follower.objects.filter(barber=profile).select_related('client')
        posts = VideoPost.objects.filter(barber=profile).order_by('-created_at')
        today = timezone.localtime(timezone.now()).date()
        today_appointments = Appointment.objects.filter(
            barber=profile, date=today
        ).select_related('client', 'service').order_by('time')
        
        context.update({
            'barber_profile': profile,
            'followers': followers,
            'own_posts': posts,
            'today_appointments': today_appointments,
        })
    else:
        followed_barbers = Follower.objects.filter(client=user).select_related('barber')
        saved_posts = SavedPost.objects.filter(user=user).select_related('video', 'video__barber')
        
        context.update({
            'followed_barbers': followed_barbers,
            'saved_posts': [sp.video for sp in saved_posts],
        })

    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.age = request.POST.get('age') if request.POST.get('age') else None
        
        if 'profile_photo' in request.FILES:
            user.profile_photo = request.FILES['profile_photo']
            
        user.save()
        
        if user.is_barber and hasattr(user, 'barber_profile'):
            profile = user.barber_profile
            profile.shop_name = request.POST.get('shop_name', profile.shop_name)
            
            depends_on_owner = request.POST.get('depends_on_owner') == 'on'
            open_time = request.POST.get('open_time')
            close_time = request.POST.get('close_time')
            work_days_list = request.POST.getlist('work_days')
            
            profile.depends_on_owner = depends_on_owner
            profile.open_time = open_time if (not depends_on_owner and open_time) else None
            profile.close_time = close_time if (not depends_on_owner and close_time) else None
            profile.work_days = ",".join(work_days_list) if not depends_on_owner and work_days_list else ("Mon,Tue,Wed,Thu,Fri,Sat,Sun" if not depends_on_owner else "")
            
            profile.address = request.POST.get('location', profile.address)
            lat = request.POST.get('location_lat')
            lng = request.POST.get('location_lng')
            if lat and lng:
                try:
                    profile.location_lat = float(lat)
                    profile.location_lng = float(lng)
                except ValueError:
                    pass
            profile.save()

            # Handle atmosphere photos update
            from shops.models import ShopImage
            for i in range(1, 5):
                img_key = f'shop_image_{i}'
                file_id_key = f'existing_image_id_{i}'
                
                if img_key in request.FILES:
                    # If an ID is provided, update existing, else create
                    existing_id = request.POST.get(file_id_key)
                    if existing_id:
                        try:
                            shop_img = ShopImage.objects.get(id=existing_id, profile=profile)
                            shop_img.image = request.FILES[img_key]
                            shop_img.save()
                        except ShopImage.DoesNotExist:
                            ShopImage.objects.create(profile=profile, image=request.FILES[img_key], is_logo=False)
                    else:
                        ShopImage.objects.create(profile=profile, image=request.FILES[img_key], is_logo=False)
            
            from shops.models import Employee
            worker_first_names = request.POST.getlist('worker_first_name')
            worker_last_names = request.POST.getlist('worker_last_name')
            
            # Rebuild worker list
            profile.employees.all().delete()
            for fn, ln in zip(worker_first_names, worker_last_names):
                if fn.strip():
                    Employee.objects.create(
                        profile=profile,
                        first_name=fn.strip(),
                        last_name=ln.strip() if ln else "",
                        role='professional'
                    )
            
        return redirect('accounts:profile')
        
    from django.conf import settings
    context = {
        'YANDEX_MAPS_API_KEY': getattr(settings, 'YANDEX_MAPS_API_KEY', '')
    }
    
    if request.user.is_barber and hasattr(request.user, 'barber_profile'):
        context['shop_images'] = request.user.barber_profile.images.filter(is_logo=False)
        
    return render(request, 'accounts/edit_profile.html', context)

@login_required
def delete_account_confirm(request):
    return render(request, 'accounts/delete_confirm.html')

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        from django.contrib.auth import logout
        logout(request)
        user.delete()
        return redirect('accounts:home')
    return redirect('accounts:home')

@login_required
def update_location(request):
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            lat = data.get('latitude')
            lng = data.get('longitude')
            
            if lat is not None and lng is not None:
                request.user.latitude = lat
                request.user.longitude = lng
                request.user.save()
                return JsonResponse({'status': 'success'})
        except (json.JSONDecodeError, ValueError):
            pass
    return JsonResponse({'status': 'error'}, status=400)

def set_language_direct(request):
    lang = request.POST.get('language', 'uz')
    next_url = request.POST.get('next', '/')
    response = redirect(next_url)

    if lang in ['en', 'uz', 'ru']:
        request.session['masterpiece_lang'] = lang
        # Keep Django's own i18n ({% trans %}, date formats) in sync with the custom switcher.
        # Django 5 LocaleMiddleware reads the language cookie, not the session.
        translation.activate(lang)
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME, lang,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            samesite=settings.LANGUAGE_COOKIE_SAMESITE,
        )

    return response

def check_email_exists(request):
    email = request.GET.get('email', '').strip()
    exists = False
    if email:
        User = get_user_model()
        exists = User.objects.filter(email__iexact=email).exists()
@login_required
def complete_profile(request):
    if request.user.is_profile_complete:
        if request.user.is_barber:
            return redirect('shops:dashboard')
        return redirect('bookings:client_home')

    if request.method == 'POST':
        user = request.user
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''

        User = get_user_model()
        error = None
        if not username:
            error = 'Please choose a username.'
        elif not USERNAME_RE.match(username):
            error = 'Username must be 3-30 characters and can only contain letters, numbers, dots and underscores.'
        elif User.objects.exclude(pk=user.pk).filter(username__iexact=username).exists():
            error = 'This username is already taken.'
        elif not password.isdigit() or len(password) != 6:
            error = 'Password must be exactly 6 digits.'

        if error:
            return render(request, 'accounts/complete_profile.html', {
                'error': error,
                'username': username,
            })

        if age:
            try:
                parsed_age = int(age)
            except ValueError:
                parsed_age = None
            if parsed_age is not None and 1 <= parsed_age <= 120:
                user.age = parsed_age
        if gender in dict(user.GENDER_CHOICES):
            user.gender = gender

        if 'profile_photo' in request.FILES:
            user.profile_photo = request.FILES['profile_photo']

        # Default to client if not specified (Social logins are usually clients)
        if not user.is_barber and not user.is_client:
            user.is_client = True

        user.username = username
        user.set_password(password)
        user.is_profile_complete = True
        user.save()

        # Keep the current session valid after changing the password,
        # so a client who signed up via Google isn't logged out mid-flow.
        update_session_auth_hash(request, user)

        if user.is_barber:
            return redirect('shops:dashboard')
        return redirect('bookings:client_home')

    return render(request, 'accounts/complete_profile.html')


def claim_shop(request):
    """Sartarosh salonni o'ziniki qilib oladi.

    Ikki xil sharoitda ishlaydi va ikkalasida ham bir xil forma:
      1. Siz sartaroshxonada turgansiz — telefoningizdan ochib, sartaroshning
         raqami va u o'ylagan parolni kiritasiz. 30 soniya.
      2. Sartarosh keyinroq o'zi kiradi — qog'ozdagi kod bilan.

    Kod brute-force qilinmasligi uchun urinishlar soni cheklangan: aks holda
    TNS-XXXX ning atigi 10 000 varianti borligi sababli begona odam boshqa
    salonni egallab olishi mumkin edi.
    """
    from django.core.cache import cache
    from shops.models import BarberProfile
    from accounts.models import normalize_phone

    error = None
    shop = None
    code_input = (request.POST.get('claim_code') or request.GET.get('code') or '').strip().upper()

    # Bir IP dan ketma-ket noto'g'ri urinishlarni cheklaymiz.
    attempt_key = f"claim_attempts:{request.META.get('REMOTE_ADDR', '')}"
    attempts = cache.get(attempt_key, 0)
    MAX_ATTEMPTS = 10

    if code_input:
        if attempts >= MAX_ATTEMPTS:
            error = 'Too many attempts. Please try again later.'
        else:
            shop = BarberProfile.objects.filter(
                claim_code=code_input, is_claimed=False
            ).first()
            if shop is None:
                cache.set(attempt_key, attempts + 1, 900)  # 15 daqiqa
                error = 'This code is not valid.'

    # Ikki bosqich bitta manzilda: birinchisida faqat kod yuboriladi, ikkinchisida
    # hisob ma'lumotlari. `step` maydonisiz birinchi bosqichdayoq "telefonni
    # kiriting" xatosi chiqib qolardi — foydalanuvchi hali hech narsa
    # yozmagan bo'lsa ham.
    is_details_step = request.POST.get('step') == 'details'

    if request.method == 'POST' and shop and not error and is_details_step:
        phone = normalize_phone(request.POST.get('phone'))
        password = request.POST.get('password') or ''
        first_name = (request.POST.get('first_name') or '').strip()

        User = get_user_model()
        if not phone:
            error = 'Please enter a valid phone number.'
        elif not password.isdigit() or len(password) != 6:
            error = 'Password must be exactly 6 digits.'
        elif User.objects.filter(phone=phone).exists():
            error = 'An account with this phone already exists.'
        else:
            user = User.objects.create_user(
                username=phone.lstrip('+'),
                password=password,
                first_name=first_name,
                is_barber=True,
                is_profile_complete=True,
            )
            user.phone = phone
            user.save(update_fields=['phone'])

            shop.user = user
            shop.is_claimed = True
            shop.claim_code = ''      # kod bir martalik
            shop.save(update_fields=['user', 'is_claimed', 'claim_code'])

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('shops:dashboard')

    return render(request, 'accounts/claim_shop.html', {
        'error': error,
        'shop': shop,
        'code_input': code_input,
    })

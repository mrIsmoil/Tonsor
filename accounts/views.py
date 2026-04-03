from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth import login, get_user_model

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
    return render(request, 'accounts/login.html')

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
                    'YANDEX_MAPS_API_KEY': getattr(settings, 'YANDEX_MAPS_API_KEY', '')
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
    lang = request.POST.get('language', 'en')
    if lang in ['en', 'uz', 'ru']:
        request.session['masterpiece_lang'] = lang
    
    next_url = request.POST.get('next', '/')
    return redirect(next_url)

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
        
        if age:
            user.age = int(age)
        if gender:
            user.gender = gender
        
        if 'profile_photo' in request.FILES:
            user.profile_photo = request.FILES['profile_photo']
            
        # Default to client if not specified (Social logins are usually clients)
        if not user.is_barber and not user.is_client:
            user.is_client = True
            
        user.is_profile_complete = True
        user.save()
        
        if user.is_barber:
            return redirect('shops:dashboard')
        return redirect('bookings:client_home')
        
    return render(request, 'accounts/complete_profile.html')

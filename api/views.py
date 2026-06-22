from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils.text import slugify
from django.shortcuts import get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.conf import settings
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import mixins, viewsets, status
from rest_framework.authtoken.models import Token
from django.db.models import Q
import urllib.parse
import re

from .models import Provider, Service, Registration, ProviderPortfolioImage, UserProfile, clean_phone_number, Booking
from .serializers import (
    ProviderSerializer, 
    ServiceSerializer, 
    RegistrationSerializer,
    UserSerializer,
    UserProfileSerializer,
    ProviderPortfolioImageSerializer,
    BookingSerializer
)


@api_view(["GET"])
def health_check(_request):
    return Response({"name": "SALUNI API", "status": "ok"})


# --- Authentication Views ---

@api_view(["POST"])
def register_user(request):
    username = request.data.get("username")
    password = request.data.get("password")
    role = request.data.get("role", "client")
    first_name = request.data.get("first_name", "")
    last_name = request.data.get("last_name", "")
    email = request.data.get("email", "")

    if not username or not password:
        return Response({"error": "Username/phone and password are required."}, status=status.HTTP_400_BAD_REQUEST)

    # Standardize phone number for username
    username = clean_phone_number(username)

    if User.objects.filter(username=username).exists():
        return Response({"error": "A user with this username/phone number already exists."}, status=status.HTTP_400_BAD_REQUEST)

    if role not in ["client", "professional"]:
        return Response({"error": "Invalid role specified."}, status=status.HTTP_400_BAD_REQUEST)

    # Create user
    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        email=email
    )

    # Create user profile
    UserProfile.objects.create(user=user, role=role)

    # Create associated provider profile if registering as a professional
    if role == "professional":
        business_name = request.data.get("business_name", f"{first_name}'s Beauty" if first_name else "New Beauty Business")
        whatsapp_number = clean_phone_number(request.data.get("whatsapp_number", username))
        phone_number = clean_phone_number(request.data.get("phone_number", username))
        
        # Generate unique slug
        base_slug = slugify(business_name)
        if not base_slug:
            base_slug = "beauty-pro"
        slug = base_slug
        counter = 1
        while Provider.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        provider = Provider.objects.create(
            user=user,
            name=business_name,
            slug=slug,
            owner_name=f"{first_name} {last_name}".strip() or "Owner",
            whatsapp_number=whatsapp_number,
            phone_number=phone_number,
            status="pending",
            is_active=True
        )

        # Create a default consultation service
        Service.objects.create(
            provider=provider,
            name="Consultation",
            category="Beauty & Wellness",
            description="Initial beauty consultation to discuss treatments.",
            duration_minutes=30,
            starting_price=0.00,
            is_active=True
        )

    token, _ = Token.objects.get_or_create(user=user)
    user_serializer = UserSerializer(user, context={"request": request})

    return Response({
        "token": token.key,
        "user": user_serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def login_user(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Username/phone and password are required."}, status=status.HTTP_400_BAD_REQUEST)

    # Standardize input username/phone number for checking
    username = clean_phone_number(username)

    user = authenticate(username=username, password=password)
    if not user:
        return Response({"error": "Invalid credentials. Please check your username/phone and password."}, status=status.HTTP_401_UNAUTHORIZED)

    token, _ = Token.objects.get_or_create(user=user)
    user_serializer = UserSerializer(user, context={"request": request})

    return Response({
        "token": token.key,
        "user": user_serializer.data
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
def logout_user(request):
    if request.user.is_authenticated:
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
    return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_me(request):
    if not request.user.is_authenticated:
        return Response({"error": "Not authenticated."}, status=status.HTTP_401_UNAUTHORIZED)
    
    user_serializer = UserSerializer(request.user, context={"request": request})
    return Response(user_serializer.data)


# --- Dashboard Views (For Professionals) ---

@api_view(["GET", "PUT", "PATCH"])
def dashboard_profile(request):
    if not request.user.is_authenticated or not hasattr(request.user, "profile") or request.user.profile.role != "professional":
        return Response({"error": "Unauthorized. Professional access only."}, status=status.HTTP_403_FORBIDDEN)

    try:
        provider = request.user.provider
    except Provider.DoesNotExist:
        # Failsafe creation
        base_slug = slugify(request.user.username)
        slug = base_slug
        counter = 1
        while Provider.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        provider = Provider.objects.create(
            user=request.user,
            name=f"{request.user.first_name}'s Beauty" if request.user.first_name else "My Business",
            slug=slug,
            owner_name=f"{request.user.first_name} {request.user.last_name}".strip() or "Owner",
            whatsapp_number=request.user.username,
            phone_number=request.user.username,
            status="pending",
            is_active=True
        )

    if request.method == "GET":
        serializer = ProviderSerializer(provider, context={"request": request})
        return Response(serializer.data)

    elif request.method in ["PUT", "PATCH"]:
        data = request.data
        provider.name = data.get("name", provider.name)
        provider.owner_name = data.get("owner_name", provider.owner_name)
        
        if "whatsapp_number" in data:
            provider.whatsapp_number = clean_phone_number(data.get("whatsapp_number"))
        if "phone_number" in data:
            provider.phone_number = clean_phone_number(data.get("phone_number"))
            
        provider.specialty = data.get("specialty", provider.specialty)
        provider.location = data.get("location", provider.location)
        provider.bio = data.get("bio", provider.bio)

        # Upload files if present
        hero_image = request.FILES.get("hero_image") or request.FILES.get("profile_image") or request.FILES.get("cover_image")
        if hero_image:
            provider.hero_image = hero_image

        profile_pic = request.FILES.get("profile_pic") or request.FILES.get("profile_picture")
        if profile_pic:
            provider.profile_pic = profile_pic

        provider.save()
        serializer = ProviderSerializer(provider, context={"request": request})
        return Response(serializer.data)



@api_view(["GET", "POST", "DELETE"])
def dashboard_portfolio(request, image_id=None):
    if not request.user.is_authenticated or not hasattr(request.user, "profile") or request.user.profile.role != "professional":
        return Response({"error": "Unauthorized. Professional access only."}, status=status.HTTP_403_FORBIDDEN)

    try:
        provider = request.user.provider
    except Provider.DoesNotExist:
        return Response({"error": "Provider profile not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        images = provider.portfolio_images.all()
        serializer = ProviderPortfolioImageSerializer(images, many=True, context={"request": request})
        return Response(serializer.data)

    elif request.method == "POST":
        image_file = request.FILES.get("image") or request.FILES.get("file")
        if not image_file:
            return Response({"error": "No image file uploaded."}, status=status.HTTP_400_BAD_REQUEST)
        
        portfolio_img = ProviderPortfolioImage.objects.create(
            provider=provider,
            image=image_file
        )
        serializer = ProviderPortfolioImageSerializer(portfolio_img, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    elif request.method == "DELETE":
        if not image_id:
            return Response({"error": "Image ID is required for deletion."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            portfolio_img = provider.portfolio_images.get(id=image_id)
            portfolio_img.delete()
            return Response({"message": "Portfolio image deleted successfully."}, status=status.HTTP_200_OK)
        except ProviderPortfolioImage.DoesNotExist:
            return Response({"error": "Portfolio image not found or not owned by you."}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET", "POST", "PUT", "PATCH", "DELETE"])
def dashboard_services(request, service_id=None):
    if not request.user.is_authenticated or not hasattr(request.user, "profile") or request.user.profile.role != "professional":
        return Response({"error": "Unauthorized. Professional access only."}, status=status.HTTP_403_FORBIDDEN)

    try:
        provider = request.user.provider
    except Provider.DoesNotExist:
        return Response({"error": "Provider profile not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        services = provider.services.filter(is_active=True)
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)

    elif request.method == "POST":
        name = request.data.get("name")
        category = request.data.get("category", "General")
        description = request.data.get("description", "")
        duration_minutes = request.data.get("duration_minutes", 60)
        starting_price = request.data.get("starting_price")
        display_order = request.data.get("display_order", 0)

        if not name or starting_price is None:
            return Response({"error": "Service name and starting price are required."}, status=status.HTTP_400_BAD_REQUEST)

        image_file = request.FILES.get("image") or request.FILES.get("service_image")

        service = Service.objects.create(
            provider=provider,
            name=name,
            category=category,
            description=description,
            duration_minutes=int(duration_minutes),
            starting_price=starting_price,
            image=image_file,
            display_order=int(display_order) if display_order is not None else 0,
            is_active=True
        )
        serializer = ServiceSerializer(service)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    elif request.method in ["PUT", "PATCH"]:
        if not service_id:
            return Response({"error": "Service ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            service = provider.services.get(id=service_id)
        except Service.DoesNotExist:
            return Response({"error": "Service not found or not owned by you."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        service.name = data.get("name", service.name)
        service.category = data.get("category", service.category)
        service.description = data.get("description", service.description)
        if "duration_minutes" in data:
            service.duration_minutes = int(data.get("duration_minutes"))
        if "starting_price" in data:
            service.starting_price = data.get("starting_price")
        if "display_order" in data:
            service.display_order = int(data.get("display_order"))
        if "is_active" in data:
            is_active_val = data.get("is_active")
            if isinstance(is_active_val, str):
                service.is_active = is_active_val.lower() == "true"
            else:
                service.is_active = bool(is_active_val)

        image_file = request.FILES.get("image") or request.FILES.get("service_image")
        if image_file:
            service.image = image_file

        service.save()
        serializer = ServiceSerializer(service)
        return Response(serializer.data)

    elif request.method == "DELETE":
        if not service_id:
            return Response({"error": "Service ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            service = provider.services.get(id=service_id)
            service.delete()
            return Response({"message": "Service deleted successfully."}, status=status.HTTP_200_OK)
        except Service.DoesNotExist:
            return Response({"error": "Service not found or not owned by you."}, status=status.HTTP_404_NOT_FOUND)



# --- Public Marketplace API ---

class ProviderViewSet(ReadOnlyModelViewSet):
    serializer_class = ProviderSerializer
    lookup_field = "slug"

    def get_queryset(self):
        # Only show active and approved providers in public marketplace listings
        queryset = Provider.objects.filter(is_active=True, status="approved").prefetch_related("services", "portfolio_images")
        
        # Featured filter
        featured = self.request.query_params.get("featured")
        if featured == "true":
            queryset = queryset.filter(is_featured=True)
            
        # Recent filter
        recent = self.request.query_params.get("recent")
        if recent == "true":
            queryset = queryset.order_by("-created_at")
            
        # Location filter (case-insensitive contains)
        location = self.request.query_params.get("location")
        if location:
            queryset = queryset.filter(location__icontains=location)
            
        # Category filter
        category = self.request.query_params.get("category")
        if category:
            if category.lower() != "all":
                queryset = queryset.filter(
                    Q(specialty__icontains=category) | Q(services__category__iexact=category)
                ).distinct()

        # Text search (searches name, specialty, bio)
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(specialty__icontains=search) | Q(bio__icontains=search)
            ).distinct()
            
        return queryset


class ServiceViewSet(ReadOnlyModelViewSet):
    queryset = Service.objects.filter(is_active=True).select_related("provider")
    serializer_class = ServiceSerializer


class RegistrationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer

from django.http import JsonResponse




def admin_send_welcome_redirect(request, *args, **kwargs):
    provider_id = kwargs.get("provider_id")

    return JsonResponse({
        "success": True,
        "provider_id": provider_id,
        "message": "Welcome redirect ready"
    })


from datetime import timedelta
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_booking_request(request):
    user = request.user
    provider_id = request.data.get("provider")
    service_ids = request.data.get("services", [])
    booking_date = request.data.get("booking_date")
    notes = request.data.get("notes", "")

    if not provider_id or not service_ids or not booking_date:
        return Response({"error": "Provider, services, and booking_date are required."}, status=status.HTTP_400_BAD_REQUEST)

    provider = get_object_or_404(Provider, id=provider_id)

    # 1. Anti-spam: Max 5 bookings per day per user
    today = timezone.now().date()
    daily_count = Booking.objects.filter(user=user, created_at__date=today).count()
    if daily_count >= 5:
        return Response({"error": "You have reached your daily limit of 5 booking requests. Please try again tomorrow."}, status=status.HTTP_400_BAD_REQUEST)

    # 2. Cooldown: 1 request to the same provider every 10 minutes
    ten_minutes_ago = timezone.now() - timedelta(minutes=10)
    recent_booking = Booking.objects.filter(
        user=user, 
        provider=provider, 
        created_at__gte=ten_minutes_ago
    ).exists()
    if recent_booking:
        return Response({"error": "You can only send one booking request to this professional every 10 minutes."}, status=status.HTTP_400_BAD_REQUEST)

    # 3. Duplicate Prevention: identical services, date, notes, user, provider
    duplicate_bookings = Booking.objects.filter(
        user=user,
        provider=provider,
        booking_date=booking_date,
        notes=notes
    )
    for b in duplicate_bookings:
        b_service_ids = set(b.services.values_list('id', flat=True))
        if b_service_ids == set(service_ids):
            return Response({"error": "An identical booking request has already been sent."}, status=status.HTTP_400_BAD_REQUEST)

    # Create Booking
    booking = Booking.objects.create(
        user=user,
        provider=provider,
        booking_date=booking_date,
        notes=notes,
        status="pending"
    )
    # Add services
    for s_id in service_ids:
        service = get_object_or_404(Service, id=s_id, provider=provider)
        booking.services.add(service)

    serializer = BookingSerializer(booking, context={"request": request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_dashboard_bookings(request):
    # Retrieve bookings for the active professional (provider)
    try:
        provider = request.user.provider
    except Provider.DoesNotExist:
        return Response({"error": "Authenticated user does not have a professional profile."}, status=status.HTTP_400_BAD_REQUEST)

    bookings = Booking.objects.filter(provider=provider).order_by("-created_at")
    serializer = BookingSerializer(bookings, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_booking_status(request, booking_id):
    try:
        provider = request.user.provider
    except Provider.DoesNotExist:
        return Response({"error": "Only professionals can manage booking statuses."}, status=status.HTTP_403_FORBIDDEN)

    booking = get_object_or_404(Booking, id=booking_id, provider=provider)
    new_status = request.data.get("status")

    if new_status not in ["confirmed", "cancelled", "completed"]:
        return Response({"error": "Invalid status code specified."}, status=status.HTTP_400_BAD_REQUEST)

    booking.status = new_status
    booking.save()

    serializer = BookingSerializer(booking, context={"request": request})
    return Response(serializer.data)

@api_view(["GET"])
def home(request):
    return Response({
        "message": "SALUNI Backend is running 🚀"
    })
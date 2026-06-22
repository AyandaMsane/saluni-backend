from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Provider, Service, Registration, ProviderPortfolioImage, UserProfile, Booking



class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["role"]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    provider_slug = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "profile", "provider_slug"]

    def get_provider_slug(self, obj):
        try:
            if hasattr(obj, "provider") and obj.provider:
                return obj.provider.slug
        except Exception:
            pass
        return None


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id",
            "provider",
            "name",
            "category",
            "description",
            "duration_minutes",
            "starting_price",
            "image",
            "display_order",
            "is_active",
        ]
        read_only_fields = ["id"]


class ProviderPortfolioImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderPortfolioImage
        fields = ["id", "image"]


class ProviderSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)
    portfolio_images = ProviderPortfolioImageSerializer(many=True, read_only=True)

    class Meta:
        model = Provider
        fields = [
            "id",
            "name",
            "slug",
            "owner_name",
            "phone_number",
            "whatsapp_number",
            "specialty",
            "location",
            "profile_pic",
            "hero_image",
            "bio",
            "status",
            "is_featured",
            "is_active",
            "approved_at",
            "welcome_sent_at",
            "services",
            "portfolio_images",
        ]
        read_only_fields = ["id"]





class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = [
            "id",
            "business_name",
            "primary_service",
            "email",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class BookingSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source="user", read_only=True)
    provider_name = serializers.CharField(source="provider.name", read_only=True)
    services_details = ServiceSerializer(source="services", many=True, read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "user",
            "user_details",
            "provider",
            "provider_name",
            "services",
            "services_details",
            "booking_date",
            "notes",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]


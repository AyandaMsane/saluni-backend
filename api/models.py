from django.db import models
from django.contrib.auth.models import User
import re


def clean_phone_number(number):
    if not number:
        return ""
    # Remove spaces, brackets, dashes, and invalid characters
    cleaned = re.sub(r'[^0-9+]', '', str(number).strip())
    # Convert local zero to +27
    if cleaned.startswith('0'):
        cleaned = '+27' + cleaned[1:]
    # Add + prefix if it starts with 27
    elif cleaned.startswith('27'):
        cleaned = '+' + cleaned
    # Ensure it starts with +27 if it's digit-only
    elif cleaned and not cleaned.startswith('+'):
        cleaned = '+27' + cleaned
    return cleaned


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("client", "Client"),
        ("professional", "Professional"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="client")

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Provider(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("suspended", "Suspended"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="provider", null=True, blank=True
    )
    name = models.CharField(max_length=160)  # Business name
    slug = models.SlugField(unique=True)
    owner_name = models.CharField(max_length=160, blank=True)
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    whatsapp_number = models.CharField(max_length=30, blank=True, null=True)
    specialty = models.CharField(max_length=160, blank=True)
    location = models.CharField(max_length=160, blank=True)
    profile_pic = models.FileField(upload_to="providers/profiles/", blank=True, null=True)
    hero_image = models.FileField(upload_to="providers/", blank=True, null=True)
    bio = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    welcome_sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if self.whatsapp_number:
            self.whatsapp_number = clean_phone_number(self.whatsapp_number)
        if self.phone_number:
            self.phone_number = clean_phone_number(self.phone_number)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProviderPortfolioImage(models.Model):
    provider = models.ForeignKey(
        Provider, related_name="portfolio_images", on_delete=models.CASCADE
    )
    image = models.FileField(upload_to="portfolios/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Portfolio Image {self.id} for {self.provider.name}"



class Service(models.Model):
    provider = models.ForeignKey(
        Provider, related_name="services", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=80, default="General")
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.FileField(upload_to="services/", blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.name} - {self.provider.name}"


class Registration(models.Model):
    business_name = models.CharField(max_length=160)
    primary_service = models.CharField(max_length=160)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.business_name} ({self.email})"


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="bookings")
    services = models.ManyToManyField(Service, related_name="bookings")
    booking_date = models.DateField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, default="pending", choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking {self.id} by {self.user.username} for {self.provider.name} ({self.status})"



from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Provider, Service, ProviderPortfolioImage, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "User Profile Details"


# Re-register UserAdmin with the inline UserProfile
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]


class ProviderPortfolioImageInline(admin.TabularInline):
    model = ProviderPortfolioImage
    extra = 1


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner_name",
        "whatsapp_number",
        "specialty",
        "location",
        "status",
        "whatsapp_welcome_link",
        "is_featured",
        "is_active",
    )
    list_filter = ("status", "is_featured", "is_active", "location")
    list_editable = ("status", "is_featured", "is_active")
    readonly_fields = ("whatsapp_welcome_link", "approved_at", "welcome_sent_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "owner_name", "specialty", "location")
    inlines = [ProviderPortfolioImageInline]
    actions = [
        "approve_providers",
        "reject_providers",
        "suspend_providers",
        "feature_providers",
        "unfeature_providers",
    ]

    @admin.display(description="WhatsApp Welcome")
    def whatsapp_welcome_link(self, obj):
        from django.utils.html import format_html
        if obj.status == "approved":
            link = f"/api/admin/providers/{obj.id}/send-welcome/"
            if obj.welcome_sent_at:
                local_time = obj.welcome_sent_at.strftime('%Y-%m-%d %H:%M')
                return format_html(
                    '<a href="{}" target="_blank" style="display:inline-block; padding: 4px 8px; background:#25D366; color:white; border-radius:4px; text-decoration:none; font-weight:bold; font-size:11px;">Resend (Sent {})</a>',
                    link, local_time
                )
            else:
                return format_html(
                    '<a href="{}" target="_blank" style="display:inline-block; padding: 4px 8px; background:#128C7E; color:white; border-radius:4px; text-decoration:none; font-weight:bold; font-size:11px;">Send Welcome</a>',
                    link
                )
        return "Pending Approval"

    @admin.action(description="Approve selected providers")
    def approve_providers(self, request, queryset):
        from django.utils import timezone
        queryset.update(status="approved", approved_at=timezone.now())

    @admin.action(description="Reject selected providers")
    def reject_providers(self, request, queryset):
        queryset.update(status="rejected")

    @admin.action(description="Suspend selected providers")
    def suspend_providers(self, request, queryset):
        queryset.update(status="suspended")

    @admin.action(description="Feature selected providers")
    def feature_providers(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description="Unfeature selected providers")
    def unfeature_providers(self, request, queryset):
        queryset.update(is_featured=False)

    def save_model(self, request, obj, form, change):
        from django.utils import timezone
        if obj.status == "approved" and not obj.approved_at:
            obj.approved_at = timezone.now()
        super().save_model(request, obj, form, change)



@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "category", "duration_minutes", "starting_price", "is_active")
    list_filter = ("is_active", "provider", "category")
    search_fields = ("name", "provider__name", "category")


@admin.register(ProviderPortfolioImage)
class ProviderPortfolioImageAdmin(admin.ModelAdmin):
    list_display = ("id", "provider", "image", "created_at")
    list_filter = ("provider",)



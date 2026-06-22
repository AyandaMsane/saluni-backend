from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ProviderViewSet, 
    ServiceViewSet, 
    RegistrationViewSet, 
    health_check,
    register_user,
    login_user,
    logout_user,
    get_me,
    dashboard_profile,
    dashboard_portfolio,
    dashboard_services,
    admin_send_welcome_redirect,
    create_booking_request,
    list_dashboard_bookings,
    update_booking_status
)

router = DefaultRouter()
router.register("providers", ProviderViewSet, basename="provider")
router.register("services", ServiceViewSet, basename="service")
router.register("registrations", RegistrationViewSet, basename="registration")

urlpatterns = [
    path("health/", health_check, name="health-check"),
    
    # Auth endpoints
    path("auth/register/", register_user, name="auth-register"),
    path("auth/login/", login_user, name="auth-login"),
    path("auth/logout/", logout_user, name="auth-logout"),
    path("auth/me/", get_me, name="auth-me"),
    
    # Professional dashboard endpoints
    path("dashboard/profile/", dashboard_profile, name="dashboard-profile"),
    path("dashboard/portfolio/", dashboard_portfolio, name="dashboard-portfolio"),
    path("dashboard/portfolio/<int:image_id>/", dashboard_portfolio, name="dashboard-portfolio-delete"),
    path("dashboard/services/", dashboard_services, name="dashboard-services"),
    path("dashboard/services/<int:service_id>/", dashboard_services, name="dashboard-service-detail"),
    
    # Dashboard Bookings
    path("dashboard/bookings/", list_dashboard_bookings, name="dashboard-bookings"),
    path("dashboard/bookings/<int:booking_id>/status/", update_booking_status, name="dashboard-booking-status"),

    # Bookings client request endpoint
    path("bookings/", create_booking_request, name="create-booking"),

    # Custom admin welcomes redirect tracker
    path("admin/providers/<int:provider_id>/send-welcome/", admin_send_welcome_redirect, name="admin-send-welcome"),
    
    path("", include(router.urls)),
]



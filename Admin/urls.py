from django.urls import path
from .views import admin_dashboard_api, create_order_api, orders_page_api




urlpatterns = [
    path('dashboard/', admin_dashboard_api, name='admin_dashboard_api'),
    path('order/', orders_page_api, name='admin_dashboard_api'),
    path('order-create/', create_order_api, name='admin_dashboard_api'),
]
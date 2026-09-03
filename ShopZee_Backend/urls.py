from django.contrib import admin
from ShopZee_App import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from ShopZee_App.views import (
    CategoryViewSet,
    CustomerViewSet,
    LedgerViewSet,
    NotificationViewSet,
    OrderItemViewSet,
    OrderViewSet,
    PaymentViewSet,
    ProductViewSet,
    RouteViewSet,
    UserViewSet,
    VisitViewSet,
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'routes', RouteViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'ledger', LedgerViewSet)
router.register(r'visits', VisitViewSet)
router.register(r'notifications', NotificationViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/login/', views.login_api, name='login_api'),
    path('api/v1/dashboard-stats/', views.admin_dashboard_api, name='admin_dashboard_api'),
    path('api/v1/orders-page/', views.orders_page_api, name='orders_page_api'),
    path('api/v1/orders/create/', views.create_order_api, name='create_order_api'),
    path('api/v1/routes-page/', views.routes_page_api, name='routes_page_api'),
    path('api/v1/salesmen-page/', views.salesmen_page_api, name='salesmen_page_api'),
    path('api/v1/orders/<int:order_id>/update/', views.update_order_api, name='update_order_api'),
    path('api/v1/salesman-detail/<int:pk>/', views.salesman_detail_api, name='salesman_detail_api'),
    path('api/v1/salesman-update/<int:pk>/', views.salesman_update_api, name='salesman_update_api'),
    path('api/v1/shopkeepers-page/', views.shopkeepers_page_api, name='shopkeepers_page_api'),
    path('api/v1/shopkeepers-update/<int:pk>/', views.shopkeeper_update_api, name='shopkeeper_update_api'),
    path('api/v1/shopkeepers-create/', views.shopkeeper_create_api, name='shopkeeper_create_api'),
    path('api/v1/shopkeeper-detail/<int:pk>/', views.shopkeeper_detail_api, name='shopkeeper_detail_api'),
    path('api/v1/notifications-page/', views.notifications_page_api, name='notifications_page_api'),
    path('api/v1/notification-action/<int:pk>/', views.notification_action_api, name='notification_action_api'),
    path('api/v1/settings/', views.settings_api, name='settings_api'),

    path('api/v1/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
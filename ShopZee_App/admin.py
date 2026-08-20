from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User,
    Category,
    Product,
    Route,
    Customer,
    Order,
    OrderItem,
    Payment,
    Ledger,
    Visit,
    Notification,
)

# 1. Custom User Admin જેથી એડમિન પેનલમાંથી როლ (Role) અને મોબાઈલ નંબર સાથે યુઝર ઉમેરી શકાય
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'mobile', 'role', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    
    # એડમિન ફોર્મમાં કઈ કઈ ફિલ્ડ્સ દેખાશે તેની ગોઠવણી
    fieldsets = UserAdmin.fieldsets + (
        ('ShopZee Role & Mobile Info', {'fields': ('role', 'mobile')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('ShopZee Role & Mobile Info', {'fields': ('role', 'mobile', 'email', 'first_name', 'last_name')}),
    )

# બધા મોડેલ્સને એડમિનમાં રજિસ્ટર કરવા
admin.site.register(User, CustomUserAdmin)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Route)
admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(Ledger)
admin.site.register(Visit)
admin.site.register(Notification)
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


# 1. Custom User Admin (રોલ, મોબાઈલ અને ટાર્ગેટ સાથે)
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = [
        'username',
        'email',
        'mobile',
        'role',
        'monthly_target',
        'is_staff',
        'is_active',
    ]
    list_filter = ['role', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'mobile']

    fieldsets = UserAdmin.fieldsets + (
        (
            'ShopZee Role, Mobile & Target',
            {'fields': ('role', 'mobile', 'monthly_target')},
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            'ShopZee Role, Mobile & Target',
            {
                'fields': (
                    'role',
                    'mobile',
                    'monthly_target',
                    'email',
                    'first_name',
                    'last_name',
                )
            },
        ),
    )


# 2. Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    search_fields = ['name']
    list_filter = ['is_active']


# 3. Product Admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'sku',
        'size',
        'category',
        'selling_price',
        'mrp',
        'current_stock',
        'is_active',
    ]
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'sku', 'size']


# 4. Route Admin (Updated with area_name and shop_address)
@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['name', 'salesman', 'is_active', 'created_at']
    readonly_fields = ['route_id',]
    list_filter = ['is_active', 'salesman']
    search_fields = ['name']


# 5. Customer Admin
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        'shop_name',
        'owner_name',
        'city',
        'route',
        'credit_limit',
        'outstanding_amount',
        'status',
    ]
    list_filter = ['city', 'state', 'status', 'route']
    search_fields = ['shop_name', 'owner_name', 'gst_number', 'city']


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(role='shopkeeper')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# 6. OrderItem Inline (ઓર્ડરની અંદર જ પ્રોડક્ટ્સ જોવા માટે)
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['price', 'item_total']


# 6.1 Payment Inline (ઓર્ડરની અંદર જ પેમેન્ટ વિગતો જોવા અને ભરવા માટે)
class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    readonly_fields = ['total_amount', 'pending_amount', 'payment_status']
    fields = [
        'paid_amount',
        'payment_method',
        'total_amount',
        'pending_amount',
        'payment_status',
    ]


# 7. Order Admin (ડિસ્કાઉન્ટ, ટેક્સ અને ગ્રાન્ડ ટોટલ મેનેજમેન્ટ સાથે)
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'customer',
        'salesman',
        'order_status',
        'subtotal',
        'grand_total',
        'created_at',
    ]
    list_filter = ['order_status', 'created_at']
    search_fields = ['customer__shop_name', 'id']
    readonly_fields = [
        'calculated_discount_amount',
        'calculated_tax_amount',
        'grand_total',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        (
            'Order Information',
            {'fields': ('customer', 'salesman', 'order_status')},
        ),
        (
            'Billing & Calculation',
            {
                'fields': (
                    'subtotal',
                    ('discount_value', 'discount_type'),
                    'calculated_discount_amount',
                    ('tax_value', 'tax_type'),
                    'calculated_tax_amount',
                    'grand_total',
                )
            },
        ),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    inlines = [OrderItemInline, PaymentInline]


# 8. Payment Admin
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'customer',
        'order',
        'total_amount',
        'paid_amount',
        'pending_amount',
        'payment_method',
        'payment_status',
        'created_at',
    ]
    list_filter = ['payment_status', 'payment_method', 'created_at']
    search_fields = ['customer__shop_name', 'order__id']
    readonly_fields = ['total_amount', 'pending_amount', 'payment_status']


# 9. Ledger Admin
@admin.register(Ledger)
class LedgerAdmin(admin.ModelAdmin):
    list_display = ['customer', 'date', 'description', 'debit', 'credit', 'balance']
    list_filter = ['date']
    search_fields = ['customer__shop_name', 'description']


# 10. Visit Admin
@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = [
        'salesman',
        'customer',
        'route',
        'status',
        'start_time',
        'end_time',
    ]
    list_filter = ['status', 'route']
    search_fields = ['customer__shop_name', 'salesman__username']


# 11. Notification Admin
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['title', 'user__username']
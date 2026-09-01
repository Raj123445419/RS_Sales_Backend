from decimal import Decimal
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

# Create your models here.


# 1. Custom User Model (સેલ્સમેન માટે monthly_target ઉમેરેલ છે)
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('salesman', 'Salesman'),
        ('shopkeeper', 'Shopkeeper'),
    )
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default='shopkeeper'
    )
    mobile = models.CharField(max_length=15, unique=True, null=True, blank=True)
    monthly_target = models.DecimalField(
        max_digits=12, decimal_places=2, default=50000.00
    )  # સેલ્સમેનના ડેશબોર્ડ ટાર્ગેટ માટે
    is_active = models.BooleanField(default=True)

    # Added related_name to avoid clashes with default auth.User
    groups = models.ManyToManyField(
        Group,
        verbose_name=('groups'),
        blank=True,
        help_text=(
            'The groups this user belongs to. A user will get all permissions'
            ' granted to each of their groups.'
        ),
        related_name='shopzee_user_set',
        related_query_name='shopzee_user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=('user permissions'),
        blank=True,
        help_text=('Specific permissions for this user.'),
        related_name='shopzee_user_permissions_set',
        related_query_name='shopzee_user',
    )

    def __str__(self):
        return f'{self.username} ({self.role})'


# 2. Category Model
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# 3. Product Model
class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='products'
    )
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=50, default='pcs')  # e.g., pcs, kg, box
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    min_order_quantity = models.PositiveIntegerField(default=1)
    current_stock = models.PositiveIntegerField(default=0)
    low_stock_limit = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} - {self.sku}'


# 4. Route Model
class Route(models.Model):
    route_id = models.CharField(max_length=50, unique=True, blank=True)
    name = models.CharField(max_length=100, unique=True)
    salesman = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'salesman'},
        related_name='assigned_routes',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.route_id:
            last_route = Route.objects.all().order_by('id').last()
            next_id = 1 if not last_route else last_route.id + 1
            self.route_id = f"RT-{next_id:03d}"  # આનાથી RT-001
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.route_id} - {self.name}"


# 5. Customer / Shopkeeper Profile
class Customer(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='customer_profile'
    )
    shop_name = models.CharField(max_length=200)
    owner_name = models.CharField(max_length=100)
    business_type = models.CharField(max_length=100, blank=True, null=True)
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField()
    area = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    route = models.ForeignKey(
        Route,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers',
    )
    credit_limit = models.DecimalField(
        max_digits=12, decimal_places=2, default=50000.00
    )
    outstanding_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.shop_name} ({self.owner_name})'


# 6. Salesman Visit Management
class Visit(models.Model):
    VISIT_STATUS = (
        ('planned', 'Planned'),
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
        ('cancelled', 'Cancelled'),
    )
    salesman = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'salesman'},
        related_name='visits',
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='visits'
    )
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, choices=VISIT_STATUS, default='planned'
    )
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f'Visit: {self.customer.shop_name} by {self.salesman.username} -'
            f' {self.status}'
        )


# 7. Order Model (Updated with automatic calculations for discount & tax in ₹ or %)
class Order(models.Model):
    ORDER_STATUS = (
        ('placed', 'Placed'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('ready_for_delivery', 'Ready for Delivery'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
        ('pending', 'Pending'),
        
    )

    DISCOUNT_TYPE_CHOICES = (
        ('rs', '₹ (Rupees)'),
        ('percent', '% (Percentage)'),
    )

    TAX_TYPE_CHOICES = (
        ('rs', '₹ (Rupees)'),
        ('percent', '% (Percentage)'),
    )

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='orders'
    )
    salesman = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'salesman'},
        related_name='orders_created',
    )
    order_status = models.CharField(
        max_length=30, choices=ORDER_STATUS, default='placed'
    )

    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )

    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    discount_type = models.CharField(
        max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='rs'
    )
    calculated_discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, editable=False
    )

    tax_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    tax_type = models.CharField(
        max_length=10, choices=TAX_TYPE_CHOICES, default='percent'
    )
    calculated_tax_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, editable=False
    )

    grand_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, editable=False
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # જો ઓર્ડર પહેલેથી ડેટાબેઝમાં હોય, તો તેની સાથે જોડાયેલી તમામ આઇટમ્સનો સરવાળો કરીને સબટોટલ જાતે જ અપડეტ કરી દેવું
        if self.pk:
            calculated_subtotal = sum(item.item_total for item in self.items.all())
            self.subtotal = calculated_subtotal

        # 1. Discount Calculation (₹ or %)
        disc_val = self.discount_value or Decimal('0.00')
        if self.discount_type == 'percent':
            self.calculated_discount_amount = (self.subtotal * disc_val) / Decimal('100.00')
        else:
            self.calculated_discount_amount = disc_val

        # 2. Tax Calculation (₹ or %) applied on subtotal after discount
        taxable_amount = self.subtotal - self.calculated_discount_amount
        if taxable_amount < 0:
            taxable_amount = Decimal('0.00')
            
        tax_val = self.tax_value or Decimal('0.00')
        if self.tax_type == 'percent':
            self.calculated_tax_amount = (taxable_amount * tax_val) / Decimal('100.00')
        else:
            self.calculated_tax_amount = tax_val

        # 3. Grand Total Automatic Calculation
        self.grand_total = taxable_amount + self.calculated_tax_amount

        super().save(*args, **kwargs)

        # 4. AUTO PAYMENT RECORD CREATION & SYNC
        payment_obj, created = Payment.objects.get_or_create(
            order=self,
            defaults={
                'customer': self.customer,
                'paid_amount': Decimal('0.00'),
                'payment_method': 'cash'
            }
        )
        payment_obj.total_amount = self.grand_total
        payment_obj.customer = self.customer
        payment_obj.save()

    def __str__(self):
        return f'Order #{self.id} - {self.customer.shop_name} (Payable: ₹{self.grand_total})'

# 8. Order Item Model
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items'
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    item_total = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        # જો પ્રાઇસ મેન્યુઅલ નાખી ન હોય તો પ્રોડક્ટની સેલિંગ પ્રાઇસ લેવી
        if not self.price and self.product:
            self.price = self.product.selling_price
        
        # આઇટમનું કુલ ટોટલ (પ્રાઇસ × ક્વન્ટિટી) ઓટોમેટિક કેલ્ક્યુલેટ કરવું
        price_val = self.price or Decimal('0.00')
        qty_val = Decimal(str(self.quantity or 1))
        self.item_total = price_val * qty_val

        super().save(*args, **kwargs)

        # જ્યારે આઇટમ સેવ કે અપડેટ થાય, ત્યારે તેના પેરેન્ટ ઓર્ડરનું સબટોટલ અને ગ્રાન્ડ ટોટલ પણ ઓટોમેટિક રી-કેલ્ક્યુલેટ થઈ જવું જોઈએ
        if self.order:
            self.order.save()

    def delete(self, *args, **kwargs):
        order_ref = self.order
        super().delete(*args, **kwargs)
        if order_ref:
            order_ref.save()

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

# 9. Payment Management (Updated to link with Order and auto-calculate pending amount)
class Payment(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('other', 'Other'),
    )
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        null=True,      # આ ઉમેરી દેવું
        blank=True,     # આ ઉમેરી દેવું
        related_name='payment_detail',
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='payments'
    )
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, editable=False
    )
    paid_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )
    pending_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, editable=False
    )
    payment_method = models.CharField(
        max_length=30, choices=PAYMENT_METHODS, default='cash'
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS, default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.order:
            self.total_amount = self.order.grand_total
            self.customer = self.order.customer

        paid = self.paid_amount or Decimal('0.00')
        total = self.total_amount or Decimal('0.00')

        self.pending_amount = total - paid

        if self.pending_amount <= 0:
            self.payment_status = 'paid'
            self.pending_amount = Decimal('0.00')
        elif paid > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'pending'

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f'Payment for Order #{self.order.id if self.order else ""} - Status:'
            f' {self.payment_status} (Pending: ₹{self.pending_amount})'
        )


# 10. Customer Ledger
class Ledger(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='ledger_entries'
    )
    date = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self, *args, **kwargs):
        return (
            f'Ledger: {self.customer.shop_name} | Debit: {self.debit} | Credit:'
            f' {self.credit}'
        )


# 11. Notification Model
class Notification(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications'
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notification to {self.user.username}: {self.title}'
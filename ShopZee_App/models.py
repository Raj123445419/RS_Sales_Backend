from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
# Create your models here.






# 1. Custom User Model
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

  def __str__(self):
    return self.name


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


# 7. Order Model
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
  subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
  discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
  tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
  grand_total = models.DecimalField(
      max_digits=12, decimal_places=2, default=0.00
  )
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f'Order #{self.id} - {self.customer.shop_name}'


# 8. Order Item Model
class OrderItem(models.Model):
  order = models.ForeignKey(
      Order, on_delete=models.CASCADE, related_name='items'
  )
  product = models.ForeignKey(Product, on_delete=models.CASCADE)
  quantity = models.PositiveIntegerField(default=1)
  price = models.DecimalField(
      max_digits=10, decimal_places=2
  )  # Fetched securely from backend Product price
  item_total = models.DecimalField(max_digits=12, decimal_places=2)

  def save(self, *args, **kwargs):
    # Backend calculation security rule
    self.price = self.product.selling_price
    self.item_total = self.price * self.quantity
    super().save(*args, **kwargs)

  def __str__(self):
    return f'{self.product.name} x {self.quantity}'


# 9. Payment Management
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
  order = models.ForeignKey(
      Order,
      on_delete=models.SET_NULL,
      null=True,
      blank=True,
      related_name='payments',
  )
  customer = models.ForeignKey(
      Customer, on_delete=models.CASCADE, related_name='payments'
  )
  total_amount = models.DecimalField(max_digits=12, decimal_places=2)
  paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
  pending_amount = models.DecimalField(
      max_digits=12, decimal_places=2, default=0
  )
  payment_method = models.CharField(
      max_length=30, choices=PAYMENT_METHODS, default='cash'
  )
  payment_status = models.CharField(
      max_length=20, choices=PAYMENT_STATUS, default='pending'
  )
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return (
        f'Payment {self.id} - {self.customer.shop_name} -'
        f' {self.payment_status}'
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

  def __str__(self):
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
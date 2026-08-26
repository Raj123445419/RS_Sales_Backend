from datetime import datetime, timedelta
import json
from django.contrib.auth import authenticate, get_user_model  # આ લાઈન પરફેક્ટ છે
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from .models import (
    Category,
    Customer,
    Ledger,
    Notification,
    Order,
    OrderItem,
    Payment,
    Product,
    Route,
    User,
    Visit,
)
from .serializers import (
    CategorySerializer,
    CustomerSerializer,
    LedgerSerializer,
    NotificationSerializer,
    OrderItemSerializer,
    OrderSerializer,
    PaymentSerializer,
    ProductSerializer,
    RouteSerializer,
    UserSerializer,
    VisitSerializer,
)

# ViewSets
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


class LedgerViewSet(viewsets.ModelViewSet):
    queryset = Ledger.objects.all()
    serializer_class = LedgerSerializer


class VisitViewSet(viewsets.ModelViewSet):
    queryset = Visit.objects.all()
    serializer_class = VisitSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer


# Login API
@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email_input = data.get('identifier', '').strip().lower()
            password_input = data.get('password', '').strip()

            if not email_input or not password_input:
                return JsonResponse(
                    {
                        'success': False,
                        'error': 'Please enter both email and password.',
                    },
                    status=400,
                )

            try:
                user_obj = User.objects.get(email__iexact=email_input)
            except User.DoesNotExist:
                return JsonResponse(
                    {
                        'success': False,
                        'error': 'User not found with this email.',
                    },
                    status=404,
                )

            password_matched = False
            if user_obj.password == password_input or user_obj.check_password(
                password_input
            ):
                password_matched = True

            if password_matched:
                if user_obj.is_active:
                    user_role = (user_obj.role or 'shopkeeper').lower()

                    return JsonResponse(
                        {
                            'success': True,
                            'message': f'Successfully logged in as {user_role.capitalize()}!',
                            'user': {
                                'id': user_obj.id,
                                'username': user_obj.username,
                                'email': user_obj.email,
                                'role': user_role,
                            },
                        }
                    )
                else:
                    return JsonResponse(
                        {'success': False, 'error': 'Account is disabled.'},
                        status=403,
                    )
            else:
                return JsonResponse(
                    {'success': False, 'error': 'Incorrect password.'},
                    status=401,
                )

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'error': 'Only POST method allowed'}, status=405)


# Admin Dashboard API
def admin_dashboard_api(request):
    try:
        time_filter = request.GET.get('filter', 'This Week')
        now = timezone.now()

        if time_filter == 'This Month':
            start_date = now.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
        elif time_filter == 'This Year':
            start_date = now.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
        else:
            start_date = now - timedelta(days=7)

        # 1. Metric Cards Data
        filtered_orders = Order.objects.filter(created_at__gte=start_date)
        total_sales = (
            filtered_orders.aggregate(total=Sum('grand_total'))['total'] or 0
        )
        total_orders_count = filtered_orders.count()
        total_customers = Customer.objects.count()

        # Live Pending Payment calculation from Payment Model
        pending_payment = (
            Payment.objects.aggregate(
                total_pending=Sum('pending_amount')
            )['total_pending']
            or 0
        )

        # 2. Sales Overview Chart Data
        sales_overview_data = []
        if time_filter == 'This Year':
            for m in range(1, 13):
                m_sales = (
                    Order.objects.filter(
                        created_at__year=now.year, created_at__month=m
                    ).aggregate(total=Sum('grand_total'))['total']
                    or 0
                )
                month_name = timezone.datetime(now.year, m, 1).strftime('%b')
                sales_overview_data.append(
                    {'label': month_name, 'value': float(m_sales)}
                )
        elif time_filter == 'This Month':
            sales_overview_data = [
                {
                    'label': 'Week 1',
                    'value': float(
                        filtered_orders.filter(
                            created_at__day__lte=7
                        ).aggregate(t=Sum('grand_total'))['t']
                        or 0
                    ),
                },
                {
                    'label': 'Week 2',
                    'value': float(
                        filtered_orders.filter(
                            created_at__day__gt=7, created_at__day__lte=14
                        ).aggregate(t=Sum('grand_total'))['t']
                        or 0
                    ),
                },
                {
                    'label': 'Week 3',
                    'value': float(
                        filtered_orders.filter(
                            created_at__day__gt=14, created_at__day__lte=21
                        ).aggregate(t=Sum('grand_total'))['t']
                        or 0
                    ),
                },
                {
                    'label': 'Week 4',
                    'value': float(
                        filtered_orders.filter(
                            created_at__day__gt=21
                        ).aggregate(t=Sum('grand_total'))['t']
                        or 0
                    ),
                },
            ]
        else:
            for i in range(6, -1, -1):
                d = now.date() - timedelta(days=i)
                d_sales = (
                    Order.objects.filter(created_at__date=d).aggregate(
                        total=Sum('grand_total')
                    )['total']
                    or 0
                )
                sales_overview_data.append(
                    {'label': d.strftime('%a'), 'value': float(d_sales)}
                )

# 3. Top Selling Products (સ્માર્ટ કલર મેચિંગ સાથે)
        top_items = (
            OrderItem.objects.values('product__name')
            .annotate(total_qty=Sum('quantity'))
            .order_by('-total_qty')[:4]
        )
        
        # ફોલબેક કલર્સ જો લિસ્ટમાં ન હોય તો
        fallback_colors = ['#3F2B96', '#22C55E', '#DEBA89', '#D71920', '#14B8A6']
        
        top_products_data = []
        valid_items = [item for item in top_items if item['total_qty'] and item['total_qty'] > 0]
        total_qty_sum = sum(i['total_qty'] for i in valid_items) if valid_items else 0

        for idx, item in enumerate(valid_items):
            prod_name = item['product__name']
            name_lower = prod_name.strip().lower()
            
            # સ્માર્ટ કલર અસાઇનમેન્ટ (શબ્દ કન્ટેન થતો હોય તો પરફેક્ટ કલર મળશે)
            if 'coca' in name_lower or 'coke' in name_lower:
                assigned_color = '#D71920'  # Red
            elif 'pepsi' in name_lower:
                assigned_color = '#2563EB'  # Blue
            elif 'sprite' in name_lower:
                assigned_color = '#22C55E'  # Green
            elif 'fanta' in name_lower:
                assigned_color = '#F97316'  # Orange
            elif 'nescafe' in name_lower or 'coffee' in name_lower:
                assigned_color = '#6F4E37'  # Brown
            elif 'thumbs up' in name_lower:
                assigned_color = '#1E3A8A'  # Dark Blue
            elif 'limca' in name_lower:
                assigned_color = '#84CC16'  # Lime Green
            elif 'dew' in name_lower:
                assigned_color = '#10B981'  # Emerald
            else:
                assigned_color = fallback_colors[idx % len(fallback_colors)]

            pct = int((item['total_qty'] / total_qty_sum) * 100) if total_qty_sum > 0 else 0
            
            top_products_data.append({
                'name': prod_name,
                'pct': pct,
                'color': assigned_color,
                'count': f"{pct}%"
            })
        # 4. Recent Orders
        recent_orders_qs = Order.objects.prefetch_related(
            'items__product'
        ).order_by('-created_at')[:6]
        recent_orders_data = []

        for ord in recent_orders_qs:
            items = ord.items.all()
            first_item = items.first()

            if first_item:
                prod_name = first_item.product.name
                item_size = (
                    first_item.size
                    if hasattr(first_item, 'size') and first_item.size
                    else 'N/A'
                )
                qty_size = f'{first_item.quantity} × {item_size}'
            else:
                prod_name = 'N/A'
                qty_size = 'N/A'

            total_items_count = items.count()
            if total_items_count > 1:
                prod_display_name = (
                    f'{prod_name} + {total_items_count - 1} products'
                )
            else:
                prod_display_name = prod_name

            raw_status = ord.order_status
            formatted_status = raw_status.replace('_', ' ').title()

            recent_orders_data.append(
                {
                    'id': f'#RS10{ord.id}',
                    'customer': ord.customer.shop_name,
                    'product': prod_display_name,
                    'qty': qty_size,
                    'amount': f'₹{ord.grand_total:,.0f}',
                    'status': formatted_status,
                }
            )

        # 5. Salesmen Performance
        salesmen = User.objects.filter(role='salesman')
        salesmen_perf_data = []
        for sm in salesmen:
            sm_orders = Order.objects.filter(salesman=sm)
            sm_sales = (
                sm_orders.aggregate(total=Sum('grand_total'))['total'] or 0
            )
            target = (
                float(sm.monthly_target)
                if hasattr(sm, 'monthly_target') and sm.monthly_target
                else 50000.0
            )
            achiev_pct = (
                int((float(sm_sales) / target) * 100) if target > 0 else 0
            )

            if achiev_pct < 40:
                bar_color = 'bg-red-500'
            elif achiev_pct <= 75:
                bar_color = 'bg-amber-400'
            else:
                bar_color = 'bg-emerald-500'

            salesmen_perf_data.append(
                {
                    'name': sm.username,
                    'sales': f'₹{sm_sales:,.0f}',
                    'target': f'₹{target:,.0f}',
                    'achiev': f'{achiev_pct}%',
                    'pct': min(achiev_pct, 100),
                    'barColor': bar_color,
                }
            )

        return JsonResponse(
            {
                'success': True,
                'metrics': {
                    'total_sales': f'₹{total_sales:,.0f}',
                    'total_orders': f'{total_orders_count:,}',
                    'customers': f'{total_customers:,}',
                    'pending_payment': f'₹{pending_payment:,.0f}',
                },
                'salesOverview': sales_overview_data,
                'recentOrders': recent_orders_data,
                'topProducts': top_products_data,
                'salesmenPerformance': salesmen_perf_data,
            }
        )
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
from datetime import datetime, timedelta
import json
from decimal import Decimal
from django.db.models import Q
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

# 3. Top Selling Products 
        top_items = (
            OrderItem.objects.values('product__name')
            .annotate(total_qty=Sum('quantity'))
            .order_by('-total_qty', 'product__name')[:5]  # -total_qty એટલે સૌથી વધુ વેચાણવાળી પહેલા આવશે
        )
        
        fallback_colors = ['#3F2B96', '#22C55E', '#DEBA89', '#D71920', '#14B8A6']
        valid_items = [item for item in top_items if item['total_qty'] and item['total_qty'] > 0]
        total_qty_sum = sum(i['total_qty'] for i in valid_items) if valid_items else 0

        raw_percentages = []
        for item in valid_items:
            exact_pct = (item['total_qty'] / total_qty_sum * 100) if total_qty_sum > 0 else 0
            raw_percentages.append({
                'item': item,
                'exact': exact_pct,
                'floor': int(exact_pct),
                'remainder': exact_pct - int(exact_pct)
            })

        # ફ્લોર વેલ્યુઝનો સરવાળો કરો
        current_sum = sum(p['floor'] for p in raw_percentages)
        difference = 100 - current_sum  # 100 માંથી જેટલી ઘટે (દા.ત. 1%)

        # જેમના રીમેઇન્ડર (Point પછીની રકમ) સૌથી વધુ હોય તેમને 1% વધારીને ટોટલ 100 પૂરા કરો
        raw_percentages.sort(key=lambda x: x['remainder'], reverse=True)
        for i in range(abs(difference)):
            if i < len(raw_percentages):
                if difference > 0:
                    raw_percentages[i]['floor'] += 1
                elif difference < 0 and raw_percentages[i]['floor'] > 0:
                    raw_percentages[i]['floor'] -= 1

        top_products_data = []
        for idx, p in enumerate(raw_percentages):
            prod_name = p['item']['product__name']
            name_lower = prod_name.strip().lower()
            pct = p['floor']

            # સ્માર્ટ કલર અસાઇનમેન્ટ
            if 'coca' in name_lower or 'coke' in name_lower:
                assigned_color = '#D71920'
            elif 'pepsi' in name_lower:
                assigned_color = '#4223BE'
            elif 'sprite' in name_lower:
                assigned_color = '#2DA12F'
            elif 'fanta' in name_lower:
                assigned_color = '#F97316'
            elif 'nescafe' in name_lower or 'coffee' in name_lower:
                assigned_color = '#E4C495'
            elif 'thumbs up' in name_lower:
                assigned_color = '#1E3A8A'
            elif 'limca' in name_lower:
                assigned_color = '#84CC16'
            elif 'dew' in name_lower:
                assigned_color = '#10B981'
            else:
                assigned_color = fallback_colors[idx % len(fallback_colors)]

            top_products_data.append({
                'name': prod_name,
                'pct': pct,
                'color': assigned_color,
                'count': f"{pct}%"
            })
        # 4. Recent Orders
     # 4. Recent Orders (ડેટાબેઝની ઓરિજિનલ ઓર્ડર આઈડી સાથે)
        recent_orders_qs = Order.objects.prefetch_related('items__product').order_by('-created_at')[:6]
        recent_orders_data = []

        for ord in recent_orders_qs:
            items = ord.items.all()
            first_item = items.first()
            
            if first_item:
                prod_name = first_item.product.name
                item_size = first_item.size if hasattr(first_item, 'size') and first_item.size else 'N/A'
                qty_size = f"{first_item.quantity} × {item_size}"
            else:
                prod_name = 'N/A'
                qty_size = 'N/A'

            total_items_count = items.count()
            if total_items_count > 1:
                prod_display_name = f"{prod_name} + {total_items_count - 1} products"
            else:
                prod_display_name = prod_name

            raw_status = ord.order_status
            formatted_status = raw_status.replace('_', ' ').title()
            
            recent_orders_data.append({
                'id': f"#{ord.id}",  # હવે અહીં ડેટાબેઝની અસલી આઈડી (#1, #2, #3, #4) જ દેખાશે
                'customer': ord.customer.shop_name,
                'product': prod_display_name,
                'qty': qty_size,
                'amount': f"₹{ord.grand_total:,.0f}",
                'status': formatted_status
            })

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

            # પર્સન્ટેજ મુજબ હેક્સ કલર સેટ કર્યા
            if achiev_pct < 40:
                bar_color = '#EF4444'  # Red (Low)
            elif achiev_pct <= 75:
                bar_color = '#F59E0B'  # Amber / Yellow (Medium)
            else:
                bar_color = '#10B981'  # Green / Emerald (High)

            salesmen_perf_data.append(
                {
                    'name': sm.username,
                    'sales': f'₹{sm_sales:,.0f}',
                    'target': f'₹{target:,.0f}',
                    'achiev': f'{achiev_pct}%',
                    'pct': min(achiev_pct, 100),
                    'barColor': bar_color,  # હેક્સ કલર મોકલ્યો
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



def orders_page_api(request):
    try:
        total_orders_count = Order.objects.count()
        pending_count = Order.objects.filter(order_status__in=['placed', 'confirmed', 'pending']).count()
        processing_count = Order.objects.filter(order_status__in=['processing', 'ready_for_delivery', 'out_for_delivery']).count()
        delivered_count = Order.objects.filter(order_status__in=['delivered', 'completed']).count()

        # Parameters
        search_query = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', 'All')
        salesman_filter = request.GET.get('salesman', 'All')
        shopkeeper_filter = request.GET.get('shopkeeper', 'All')
        payment_filter = request.GET.get('payment', 'All')
        date_filter = request.GET.get('date', 'All')
        time_filter = request.GET.get('timeFilter', 'This Week')

        now = timezone.now()
        orders_qs = Order.objects.all().order_by('-created_at')

        
        chart_data = []
        if time_filter == 'This Year':
            for m in range(1, 13):
                m_sales = Order.objects.filter(created_at__year=now.year, created_at__month=m).aggregate(total=Sum('grand_total'))['total'] or 0
                month_name = timezone.datetime(now.year, m, 1).strftime('%b')
                chart_data.append({'day': month_name, 'value': float(m_sales)})
        elif time_filter == 'This Month':
            chart_data = [
                {'day': 'Week 1', 'value': float(Order.objects.filter(created_at__year=now.year, created_at__month=now.month, created_at__day__lte=7).aggregate(t=Sum('grand_total'))['t'] or 0)},
                {'day': 'Week 2', 'value': float(Order.objects.filter(created_at__year=now.year, created_at__month=now.month, created_at__day__gt=7, created_at__day__lte=14).aggregate(t=Sum('grand_total'))['t'] or 0)},
                {'day': 'Week 3', 'value': float(Order.objects.filter(created_at__year=now.year, created_at__month=now.month, created_at__day__gt=14, created_at__day__lte=21).aggregate(t=Sum('grand_total'))['t'] or 0)},
                {'day': 'Week 4', 'value': float(Order.objects.filter(created_at__year=now.year, created_at__month=now.month, created_at__day__gt=21).aggregate(t=Sum('grand_total'))['t'] or 0)},
            ]
        else:
            for i in range(6, -1, -1):
                d = now.date() - timedelta(days=i)
                d_sales = Order.objects.filter(created_at__date=d).aggregate(total=Sum('grand_total'))['total'] or 0
                chart_data.append({'day': d.strftime('%a'), 'value': float(d_sales)})

        
        if search_query:
            orders_qs = orders_qs.filter(
                Q(id__icontains=search_query) |
                Q(customer__shop_name__icontains=search_query) |
                Q(salesman__username__icontains=search_query) |
                Q(items__product__name__icontains=search_query)
            ).distinct()

        if status_filter != 'All':
            formatted_status = status_filter.lower().replace(' ', '_')
            orders_qs = orders_qs.filter(order_status__iexact=formatted_status)

        if salesman_filter != 'All':
            orders_qs = orders_qs.filter(salesman__username__iexact=salesman_filter)

        if shopkeeper_filter != 'All':
            orders_qs = orders_qs.filter(customer__shop_name__iexact=shopkeeper_filter)

        if payment_filter != 'All':
            orders_qs = orders_qs.filter(payment_detail__payment_status__iexact=payment_filter)

        if date_filter != 'All':
            if date_filter == 'Today':
                orders_qs = orders_qs.filter(created_at__date=now.date())
            elif date_filter == 'This Week':
                start_week = now - timedelta(days=7)
                orders_qs = orders_qs.filter(created_at__gte=start_week)
            elif date_filter == 'This Month':
                orders_qs = orders_qs.filter(created_at__year=now.year, created_at__month=now.month)
            elif date_filter == 'This Year':
                orders_qs = orders_qs.filter(created_at__year=now.year)

        orders_data = []
        for ord in orders_qs:
            payment_obj = getattr(ord, 'payment_detail', None)
            pay_status = payment_obj.payment_status if payment_obj else 'Pending'

            orders_data.append({
                'id': f"#{ord.id}",
                'date': ord.created_at.strftime('%d %b %Y'),
                'customer': ord.customer.shop_name if ord.customer else 'N/A',
                'salesman': ord.salesman.username if ord.salesman else 'Unassigned',
                'amount': f"₹{ord.grand_total:,.0f}",
                'status': ord.order_status.replace('_', ' ').title(),
                'payment_status': pay_status.title()
            })

        return JsonResponse({
            'success': True,
            'metrics': {
                'total': f"{total_orders_count:,}",
                'pending': f"{pending_count:,}",
                'processing': f"{processing_count:,}",
                'delivered': f"{delivered_count:,}"
            },
            'orderValueChart': chart_data,
            'orders': orders_data,
            'dropdowns': {
                'salesmen': list(User.objects.filter(role='salesman').values_list('username', flat=True).distinct()),
                'shopkeepers': list(Customer.objects.values_list('shop_name', flat=True).distinct())
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# 2. Create Order API (નવો ઓર્ડર ડેટાબેઝમાં સેવ કરવા માટે)
@csrf_exempt
def create_order_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            shop_name = data.get('shopkeeper')
            salesman_name = data.get('salesman')
            product_id = data.get('product_id')
            size_selected = data.get('size', '500ml')  # સિલેક્ટ કરેલી સાઈઝ (જેમ કે 250ml, 500ml વગેરે)
            quantity = int(data.get('quantity', 1))
            status = data.get('status', 'placed').lower().replace(' ', '_')
            payment_status = data.get('payment_status', 'pending').lower()
            
           
            discount_val = Decimal(str(data.get('discount_value', '0.00')))
            discount_type = data.get('discount_type', 'rs')
            tax_val = Decimal(str(data.get('tax_value', '0.00')))
            tax_type = data.get('tax_type', 'percent')

            customer = Customer.objects.filter(shop_name__iexact=shop_name).first()
            salesman = User.objects.filter(username__iexact=salesman_name, role='salesman').first()
            product = Product.objects.filter(id=product_id).first()

            if not customer:
                customer = Customer.objects.first()
            if not product:
                product = Product.objects.first()


            unit_price = product.selling_price if product else Decimal('100.00')
            

            initial_item_total = unit_price * quantity


            new_order = Order.objects.create(
                customer=customer,
                salesman=salesman,
                order_status=status,
                subtotal=Decimal('0.00'),
                discount_value=discount_val,
                discount_type=discount_type,
                tax_value=tax_val,
                tax_type=tax_type
            )


            order_item = OrderItem.objects.create(
                order=new_order,
                product=product,
                size=size_selected,
                quantity=quantity,
                price=unit_price,
                item_total=initial_item_total
            )


            calculated_subtotal = sum(item.item_total for item in new_order.items.all())

            new_order.subtotal = calculated_subtotal
            new_order.save()


            if hasattr(new_order, 'payment_detail'):
                pay_obj = new_order.payment_detail
                pay_obj.payment_status = payment_status
                if payment_status == 'paid':
                    pay_obj.paid_amount = new_order.grand_total
                pay_obj.save()

            return JsonResponse({
                'success': True, 
                'message': 'Order created successfully with auto calculations!',
                'grand_total': float(new_order.grand_total)
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
            
    return JsonResponse({'success': False, 'error': 'Only POST allowed'}, status=405)

# routes


def routes_page_api(request):
    try:
        search_query = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', 'All')
        salesman_filter = request.GET.get('salesman', 'All')
        area_filter = request.GET.get('area', 'All')
        route_filter = request.GET.get('route', 'All')
        time_filter = request.GET.get('timeFilter', 'This Week') 

        now = timezone.now()
        if time_filter == 'This Month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif time_filter == 'This Year':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif time_filter == 'Today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = now - timedelta(days=7)

        routes_qs = Route.objects.all().prefetch_related('customers', 'salesman')

        # --- Filters ---
        if search_query:
            routes_qs = routes_qs.filter(
                Q(name__icontains=search_query) |
                Q(salesman__username__icontains=search_query) |
                Q(customers__area__icontains=search_query) |
                Q(customers__shop_name__icontains=search_query)
            ).distinct()

        if salesman_filter != 'All':
            routes_qs = routes_qs.filter(salesman__username__iexact=salesman_filter)

        if route_filter != 'All':
            routes_qs = routes_qs.filter(name__iexact=route_filter)


        routes_data = []

        performance_data = []

        for rt in routes_qs:
            customers = rt.customers.all()
            if area_filter != 'All':
                customers = customers.filter(area__iexact=area_filter)
                if not customers.exists():
                    continue

            shops_count = customers.count()
            visited_count = Visit.objects.filter(route=rt, status='completed', created_at__gte=start_date).count()
            total_sales = Order.objects.filter(customer__route=rt, created_at__gte=start_date).aggregate(t=Sum('grand_total'))['t'] or 0

            status_val = 'Active' if rt.is_active else 'Completed'

            routes_data.append({
                'id': rt.id,
                'route': rt.name,
                'area': customers.first().area if customers.first() else 'N/A',
                'salesman': rt.salesman.username if rt.salesman else 'Unassigned',
                'shops': shops_count,
                'visited': visited_count,
                'sales': f"₹{total_sales:,.1f}K" if total_sales > 0 else "₹0.0K",
                'status': status_val
            })


            perf_pct = int((visited_count / shops_count * 100) if shops_count > 0 else 0)
            if perf_pct > 100:
                perf_pct = 100

            performance_data.append({
                'name': rt.name,
                'performance': perf_pct
            })


        routes_shops_data = []
        customers_qs = Customer.objects.filter(route__isnull=False).select_related('route', 'user')
        if area_filter != 'All':
            customers_qs = customers_qs.filter(area__iexact=area_filter)

        for cust in customers_qs:
            routes_shops_data.append({
                'id': cust.id,
                'route': cust.route.name if cust.route else 'N/A',
                'area': cust.area,
                'shop': cust.shop_name,
                'salesman': cust.route.salesman.username if (cust.route and cust.route.salesman) else 'Unassigned'
            })

        total_routes_count = Route.objects.count()
        active_routes_count = Route.objects.filter(is_active=True).count()
        completed_routes_count = total_routes_count - active_routes_count

        return JsonResponse({
            'success': True,
            'routeStatus': {
                'total': total_routes_count,
                'categories': [
                    {'label': 'Active', 'count': active_routes_count, 'color': '#3525BE', 'percentage': int((active_routes_count / total_routes_count * 100) if total_routes_count > 0 else 0)},
                    {'label': 'Completed', 'count': completed_routes_count, 'color': '#22A847', 'percentage': int((completed_routes_count / total_routes_count * 100) if total_routes_count > 0 else 0)},
                    {'label': 'Pending', 'count': 0, 'color': '#D7262D', 'percentage': 0}
                ]
            },
            'routePerformance': performance_data,  
            'routes': routes_data,
            'routesAndShops': routes_shops_data,
            'dropdowns': {
                'salesmen': list(User.objects.filter(role='salesman').values_list('username', flat=True).distinct()),
                'areas': list(Customer.objects.values_list('area', flat=True).distinct()),
                'routes': list(Route.objects.values_list('name', flat=True).distinct()),
                'shops': list(Customer.objects.values_list('shop_name', flat=True).distinct())
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)




# Salesman


def salesmen_page_api(request):
    try:
        time_filter = request.GET.get('timeFilter', 'This Week')
        now = timezone.now()

        if time_filter == 'This Month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif time_filter == 'This Year':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif time_filter == 'Today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = now - timedelta(days=7)

        salesmen_qs = User.objects.filter(role='salesman')
        
        # 1. Stat Cards Metrics
        total_salesmen_count = salesmen_qs.count()
        
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_sales = Order.objects.filter(created_at__gte=today_start).aggregate(t=Sum('grand_total'))['t'] or 0

        # 2. Sales Performance List & Average Achievement Calculation
        sales_performance_data = []
        table_data = []
        total_achievement_pct = 0

        for sm in salesmen_qs:
            sm_orders = Order.objects.filter(salesman=sm, created_at__gte=start_date)
            sm_sales = sm_orders.aggregate(t=Sum('grand_total'))['t'] or 0
            target = float(sm.monthly_target) if hasattr(sm, 'monthly_target') and sm.monthly_target else 50000.0
            achiev_pct = int((float(sm_sales) / target) * 100) if target > 0 else 0
            if achiev_pct > 100:
                achiev_pct = 100

            total_achievement_pct += achiev_pct

            sales_performance_data.append({
                'name': sm.username,
                'sales': f"₹{sm_sales:,.0f} Sales",
                'target': f"Target ₹{target:,.0f}",
                'pct': achiev_pct
            })

            # Table Data calculations
            assigned_route = Route.objects.filter(salesman=sm).first()
            area_name = assigned_route.customers.first().area if (assigned_route and assigned_route.customers.first()) else 'N/A'
            shops_count = Customer.objects.filter(route=assigned_route).count() if assigned_route else 0
            orders_count = sm_orders.count()
            
            # Status determination
            status_val = 'Active' if sm.is_active else 'Completed'

            table_data.append({
                'id': sm.id,
                'salesman': sm.username,
                'area': area_name,
                'shops': shops_count,
                'orders': orders_count,
                'sales': f"₹{sm_sales:,.1f}K" if sm_sales > 0 else "₹0.0K",
                'target': f"₹{target:,.1f}K",
                'achievement': f"{achiev_pct}%",
                'status': status_val
            })

        avg_achievement = int(total_achievement_pct / total_salesmen_count) if total_salesmen_count > 0 else 0

        return JsonResponse({
            'success': True,
            'metrics': {
                'totalSalesmen': total_salesmen_count,
                'totalSalesToday': f"₹{today_sales:,.0f}",
                'avgAchievement': f"{avg_achievement}%"
            },
            'salesPerformance': sales_performance_data,
            'salesmenTable': table_data,
            'dropdowns': {
                'salesmen': list(salesmen_qs.values_list('username', flat=True).distinct()),
                'areas': list(Customer.objects.values_list('area', flat=True).distinct()),
                'statuses': ['Active', 'On Route', 'Completed', 'Pending']
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)    
from decimal import Decimal
import json
from django.shortcuts import render
from django.db.models import Q, Sum
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
from ShopZee_App.models import Customer, Order, OrderItem, Payment, Product, User
from django.views.decorators.csrf import csrf_exempt


# Admin Dashbord Api
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

        # 1. Cards Data
        filtered_orders = Order.objects.filter(created_at__gte=start_date)
        total_sales = (
            filtered_orders.aggregate(total=Sum('grand_total'))['total'] or 0
        )
        total_orders_count = filtered_orders.count()
        total_customers = Customer.objects.count()

        
        pending_payment = (
            Payment.objects.aggregate(
                total_pending=Sum('pending_amount')
            )['total_pending']
            or 0
        )

        # 2. Sales Chart Data
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

        current_sum = sum(p['floor'] for p in raw_percentages)
        difference = 100 - current_sum 

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
            elif 'maaz' in name_lower:
                assigned_color = '#F7941D'                
            else:
                assigned_color = fallback_colors[idx % len(fallback_colors)]

            top_products_data.append({
                'name': prod_name,
                'pct': pct,
                'color': assigned_color,
                'count': f"{pct}%"
            })

        # 4. Recent Orders
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
                'id': f"#{ord.id}",
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

            if achiev_pct < 40:
                bar_color = '#EF4444'  
            elif achiev_pct <= 75:
                bar_color = '#F59E0B'   
            else:
                bar_color = '#10B981'   

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


# Order Api
def orders_page_api(request):
    try:
        total_orders_count = Order.objects.count()
        pending_count = Order.objects.filter(order_status__in=['placed', 'confirmed', 'pending']).count()
        processing_count = Order.objects.filter(order_status__in=['processing', 'ready_for_delivery', 'out_for_delivery']).count()
        delivered_count = Order.objects.filter(order_status__in=['delivered', 'completed']).count()

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

            first_item = ord.items.first()

            orders_data.append({
                'raw_id': ord.id,
                'id': f"#{ord.id}",
                'date': ord.created_at.strftime('%d %b %Y'),
                'customer': ord.customer.shop_name if ord.customer else 'N/A',
                'salesman': ord.salesman.username if ord.salesman else 'Unassigned',
                'amount': f"₹{ord.grand_total:,.0f}",
                'status': ord.order_status.replace('_', ' ').title(),
                'payment_status': pay_status.title(),
                'quantity': first_item.quantity if first_item else 1,
                'discount_value': float(ord.discount_value),
                'discount_type': ord.discount_type,
                'tax_value': float(ord.tax_value)
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
        'shopkeepers': list(Customer.objects.values_list('shop_name', flat=True).distinct()),
        'products': list(Product.objects.filter(is_active=True).values('id', 'name', 'current_stock'))
    }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# Create Order API 
@csrf_exempt
def create_order_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            shop_name = data.get('shopkeeper')
            salesman_name = data.get('salesman')
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
            status = data.get('status', 'placed').lower().replace(' ', '_')
            
            discount_val = Decimal(str(data.get('discount_value', '0.00') or '0.00'))
            discount_type = data.get('discount_type', 'rs')
            tax_val = Decimal(str(data.get('tax_value', '0.00') or '0.00'))
            tax_type = data.get('tax_type', 'percent')

            customer = Customer.objects.filter(shop_name__iexact=shop_name).first()
            salesman = User.objects.filter(username__iexact=salesman_name, role='salesman').first()
            
            if product_id:
                product = Product.objects.filter(id=product_id).first()
            else:
                product = Product.objects.first()

            if not customer:
                customer = Customer.objects.first()
            if not product:
                return JsonResponse({'success': False, 'error': 'No products available in database! Please add a product first.'}, status=400)

            unit_price = product.selling_price
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

            OrderItem.objects.create(
                order=new_order,
                product=product,
                quantity=quantity,
                price=unit_price,
                item_total=initial_item_total
            )

            new_order.save()

            return JsonResponse({
                'success': True, 
                'message': 'Order created successfully!',
                'grand_total': float(new_order.grand_total)
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
            
    return JsonResponse({'success': False, 'error': 'Only POST allowed'}, status=405)




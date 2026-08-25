from django.shortcuts import render
from rest_framework import viewsets
from django.contrib.auth import authenticate
from django.http import JsonResponse
import json
from django.contrib.auth import authenticate, get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
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
# Create your views here.
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





@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email_input = data.get('identifier', '').strip().lower() # ફ્રન્ટએન્ડમાંથી આવેલો ઈમેલ
            password_input = data.get('password', '').strip()

            if not email_input or not password_input:
                return JsonResponse({'success': False, 'error': 'Please enter both email and password.'}, status=400)

            # 1. તમારા કસ્ટમ User ટેબલમાંથી ઈમેલથી યુઝર શોધો
            try:
                user_obj = User.objects.get(email__iexact=email_input)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'User not found with this email.'}, status=404)

            # 2. પાસવર્ડ ચેક કરો (પ્લેન ટેક્સ્ટ અથવા હેશ થયેલો બંને કામ કરશે)
            password_matched = False
            if user_obj.password == password_input or user_obj.check_password(password_input):
                password_matched = True

            if password_matched:
                if user_obj.is_active:
                    # 3. તમારા મોડેલની અંદર આપેલો role ડાયરેક્ટ લો (admin, salesman, shopkeeper)
                    user_role = (user_obj.role or 'shopkeeper').lower()

                    return JsonResponse({
                        'success': True,
                        'message': f'Successfully logged in as {user_role.capitalize()}!',
                        'user': {
                            'id': user_obj.id,
                            'username': user_obj.username,
                            'email': user_obj.email,
                            'role': user_role
                        }
                    })
                else:
                    return JsonResponse({'success': False, 'error': 'Account is disabled.'}, status=403)
            else:
                return JsonResponse({'success': False, 'error': 'Incorrect password.'}, status=401)
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST method allowed'}, status=405)
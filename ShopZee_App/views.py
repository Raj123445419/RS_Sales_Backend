from django.shortcuts import render
from rest_framework import viewsets
from django.contrib.auth import authenticate
from django.http import JsonResponse
import json
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




  from django.contrib.auth import authenticate
from django.http import JsonResponse
import json

def admin_login_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email_or_username = data.get('email')
        password = data.get('password')
        role = data.get('role')

        if role == 'admin':
            # Django ના authentication બેઝથી યુઝર ચેક કરવો
            user = authenticate(username=email_or_username, password=password)
            
            if user is not None and (user.is_staff or user.is_superuser):
                return JsonResponse({'isAdmin': True, 'message': 'Success'})
            else:
                return JsonResponse({'isAdmin': False, 'error': 'You are not in admin list or data'}, status=401)
                
        return JsonResponse({'isAdmin': True})
from rest_framework import serializers
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


class UserSerializer(serializers.ModelSerializer):
  class Meta:
    model = User
    fields = [
        'id',
        'username',
        'email',
        'mobile',
        'role',
        'first_name',
        'last_name',
    ]


class CategorySerializer(serializers.ModelSerializer):
  class Meta:
    model = Category
    fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
      model = Product
      fields = '__all__'

    def get_image(self, obj):
      request = self.context.get('request')
      if obj.image:
        return request.build_absolute_uri(obj.image.url)
      return None


class RouteSerializer(serializers.ModelSerializer):
  salesman_name = serializers.ReadOnlyField(source='salesman.username')

  class Meta:
    model = Route
    fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
  user = UserSerializer(read_only=True)
  route_name = serializers.ReadOnlyField(source='route.name')

  class Meta:
    model = Customer
    fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
  product_name = serializers.ReadOnlyField(source='product.name')

  class Meta:
    model = OrderItem
    fields = ['id', 'product', 'product_name', 'quantity', 'price', 'item_total']


class OrderSerializer(serializers.ModelSerializer):
  items = OrderItemSerializer(many=True, read_only=True)
  shop_name = serializers.ReadOnlyField(source='customer.shop_name')

  class Meta:
    model = Order
    fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
  class Meta:
    model = Payment
    fields = '__all__'


class LedgerSerializer(serializers.ModelSerializer):
  class Meta:
    model = Ledger
    fields = '__all__'


class VisitSerializer(serializers.ModelSerializer):
  class Meta:
    model = Visit
    fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
  class Meta:
    model = Notification
    fields = '__all__'
from rest_framework import serializers
from .models import Product, Cart, CartItem
from django.conf import settings
from django.contrib.auth import get_user_model

class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = ["id", "name", "slug", "image", "description", "category", "price"]

    def get_image(self, obj):
        return settings.MEDIA_URL + str(obj.image)    


class DetailedProductSerializer(serializers.ModelSerializer):
    similar_products = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "price", "slug", "image", "description", "similar_products"]

    def get_similar_products(self, product):
        products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
        serializer = ProductSerializer(products, many=True)
        return serializer.data
    
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "quantity", "product", "total"]

    def get_total(self, cartitem):
        price = cartitem.product.price * cartitem.quantity
        return price


    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(read_only=True, many=True)
    sum_total = serializers.SerializerMethodField()
    num_of_items = serializers.SerializerMethodField()
    class Meta:
        model = Cart
        fields = ["id", "cart_code", "items", "sum_total", "num_of_items", "created_at", "modified_at"]

    def get_sum_total(self, cart):
        items = cart.items.all()
        total = sum([item.product.price * item.quantity for item in items])
        return total

    def get_num_of_items(self, cart):
        items = cart.items.all()
        total = sum([item.quantity for item in items])
        return total

class  SimpleCartSerializer(serializers.ModelSerializer):
    num_of_items = serializers.SerializerMethodField()
    class Meta:
        model = Cart
        fields = ["id", "cart_code", "num_of_items"]

    def get_num_of_items(self, cart):
        num_of_items = sum([item.quantity for item in cart.items.all()])
        return num_of_items

class NewCartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    order_id = serializers.SerializerMethodField()
    order_date = serializers.SerializerMethodField()
    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "order_id", "order_date"]

    def get_order_id(self, cartitem):
        order_id = cartitem.cart.cart_code    
        return order_id
    
    def get_order_date(self, cartitem):
        order_date = cartitem.cart.modified_at
        return order_date




class UserSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "first_name", "last_name", "email", "city", "state", "address", "phone", "items"]


    def get_items(self, user):
        cartitems = CartItem.objects.filter(cart__user=user, cart__paid=True)[:10]   
        serializer = NewCartItemSerializer(cartitems, many=True)
        return serializer.data






class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'city', 'state', 'address', 'phone']

    def create(self, validated_data):
        user = get_user_model().objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
            city=validated_data.get('city', ''),  
            state=validated_data.get('state', ''),  
            address=validated_data.get('address', ''),  
            phone=validated_data.get('phone', ''), 
        )
        return user
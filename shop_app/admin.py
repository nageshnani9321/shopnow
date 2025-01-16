from django.contrib import admin
from .models import Product, Cart, CartItem


# Register each model 
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)

from django.urls import path
from . import views




urlpatterns = [
        path("products", views.products, name="products"),
        path("product_details/<slug:slug>", views.product_details, name="product_details"),
        path("add_item/", views.add_item, name="add_item"),
        path("product_in_cart", views.product_in_cart, name="product_in_cart"),
        path("get_cart_stat", views.get_cart_stat, name="get_cart_stat"),
        path("get_cart", views.get_cart, name="get_cart"),
        path("update_quantity/", views.update_quantity, name="update_quantity"),
        path("delete_cartitem/", views.delete_cartitem, name="delete_cartitem"),
        path("get_username", views.get_username, name="get_username"),
        path("user_info", views.user_info, name="user_info"),
        path("register/", views.register_user, name="register_user"),
        path("initiate_payment/", views.initiate_payment, name="initiate_payment"),
        path("payment_callback/", views.payment_callback, name="payment_callback" ),
        path("initiate_paypal_payment/", views.initiate_paypal_payment, name="initiate_paypal_payment"),
        path("paypal_payment_callback/", views.paypal_payment_callback, name="paypal_payment_callback")

]

# fetching all_products: http://127.0.0.1:8000/products/
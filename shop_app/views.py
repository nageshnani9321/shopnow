from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from .models import Product, Cart, CartItem, Transaction
from .serializers import ProductSerializer, DetailedProductSerializer, CartItemSerializer, SimpleCartSerializer, CartSerializer, UserSerializer, UserRegistrationSerializer
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from django.conf import settings
import uuid
import requests
import paypalrestsdk








# Create your views here.
BASE_URL = settings.REACT_BASE_URL




@api_view(["GET"])
def products(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

# @api_view(["GET"])
# def product_details(request, slug):
#     product = Product.objects.get(slug=slug)
#     serializer = DetailedProductSerializer(product)
#     return Response(serializer.data)







@api_view(["GET"])
def product_details(request, slug):
    try:
        product = Product.objects.get(slug=slug)
    except Product.DoesNotExist:
        raise NotFound(f"Product with slug {slug} not found.") 
    
    serializer = DetailedProductSerializer(product)
    return Response(serializer.data)





@api_view(["POST"])
def add_item(request):
    try:
        cart_code = request.data.get("cart_code")
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)

        if not cart_code or not product_id:
            return Response({"error": "cart_code and product_id are required"}, status=400)

        cart, created = Cart.objects.get_or_create(cart_code=cart_code)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise NotFound(f"Product with id {product_id} not found.")  

        cart_item = cart.items.filter(product=product).first()  

        if not cart_item:
            cart_item = CartItem(cart=cart, product=product, quantity=quantity)
            cart_item.save()
        else:
            cart_item.quantity += quantity
            cart_item.save()

        # Serialize the CartItem object
        serializer = CartItemSerializer(cart_item)

        return Response({"data": serializer.data, "message": "Cart item updated successfully"}, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(['GET'])
def product_in_cart(request):
    cart_code = request.query_params.get("cart_code")
    product_id = request.query_params.get("product_id")

    cart = Cart.objects.get(cart_code=cart_code)
    product = Product.objects.get(id=product_id)

    product_exists_in_cart = CartItem.objects.filter(cart=cart, product=product).exists()

    return Response({'product_in_cart': product_exists_in_cart})
    

@api_view(['GET'])    
def get_cart_stat(request):
    cart_code = request.query_params.get("cart_code")
    cart = Cart.objects.get(cart_code=cart_code, paid=False)
    serializer = SimpleCartSerializer(cart)
    return Response(serializer.data)


@api_view(['GET'])    
def get_cart(request):
    cart_code = request.query_params.get("cart_code")
    try:
        cart = Cart.objects.get(cart_code=cart_code, paid=False)
    except Cart.DoesNotExist:
        return Response({"error": f"Cart with code {cart_code} not found or already paid."}, status=404)
    
    serializer = CartSerializer(cart)
    return Response(serializer.data)

@api_view(['PATCH']) 
def update_quantity(request):
    try:
        cartitem_id = request.data.get("item_id")  
        quantity = request.data.get("quantity")   
        
        quantity = int(quantity)
        
        cartitem = CartItem.objects.get(id=cartitem_id)
        
        cartitem.quantity = quantity 
        cartitem.save() 
        
        serializer = CartItemSerializer(cartitem)
        
        return Response({
            "data": serializer.data,
            "message": "Cart item updated successfully!" 
        })
    except Exception as e:
        return Response({'error': str(e)}, status=400)
    
@api_view(["POST"])
def delete_cartitem(request):
    cartitem_id = request.data.get("item_id")
    cartitem = CartItem.objects.get(id=cartitem_id)
    cartitem.delete()
    return Response({"message": "Item deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
    
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_username(request):
    user = request.user
    return Response({"username": user.username})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_info(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data)


@api_view(["POST"])
def register_user(request):
    if request.method == 'POST':
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)







@api_view(["POST"])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    if request.user:
        try:
            tx_ref = str(uuid.uuid4())
            cart_code = request.data.get("cart_code")
            cart = Cart.objects.get(cart_code=cart_code)
            user = request.user

            # Calculate the total amount
            amount = sum([item.quantity * item.product.price for item in cart.items.all()])
            tax = Decimal("4.00")
            total_amount = amount + tax
            currency = "USD"
            redirect_url = f"{BASE_URL}/payment-status/"

            transaction = Transaction.objects.create(
                ref=tx_ref,
                cart=cart,
                amount=total_amount,
                currency=currency,
                user=user,
                status='pending'
            )

            flutterwave_payload = {
                "tx_ref": tx_ref,
                "amount": str(total_amount),
                "currency": currency,
                "redirect_url": redirect_url,
                "customer": {
                    "email": user.email,
                    "name": user.username,
                    "phonenumber": user.phone
                },
                "customizations": {
                    "title": "ShopNow Payment"
                }
            }

            headers = {
                "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
                "Content-type": "application/json"
            }

            response = requests.post(
                'https://api.flutterwave.com/v3/payments',
                json=flutterwave_payload,
                headers=headers
            )

            print(f"Flutterwave Response Status: {response.status_code}")
            print(f"Flutterwave Response Body: {response.text}")

            if response.status_code == 200:
                return Response(response.json(), status=status.HTTP_200_OK)
            else:
                return Response(response.json(), status=response.status_code)

        except requests.exceptions.RequestException as e:
            print(f"Error occurred while calling Flutterwave: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Cart.DoesNotExist:
            return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["POST"])
def payment_callback(request):
    status = request.GET.get("status")
    tx_ref = request.GET.get("tx_ref")
    transaction_id = request.GET.get("transaction_id")
    user = request.user

    if status == 'successful':
        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"
        }
        response = requests.get(f'https://api.flutterwave.com/v3/transactions/{transaction_id}/verify', headers=headers)
        response_data = response.json()
        
        if response_data['status'] == 'success':
            try:
                transaction = Transaction.objects.get(ref=tx_ref)
                
                if (response_data['data']['status'] == 'successful' and
                        float(response_data['data']['amount']) == float(transaction.amount) and
                        response_data['data']['currency'] == transaction.currency):
                    
                    transaction.status = 'completed'
                    transaction.save()

                    cart = transaction.cart
                    cart.paid = True
                    cart.user = user
                    cart.save()

                    return Response({
                        'message': 'Payment successful!',
                        'subMessage': 'You have successfully completed your payment.'
                    })
                else:
                    return Response({
                        'message': 'Payment verification failed!',
                        'subMessage': 'Transaction details do not match.'
                    }, status=400)
            except Transaction.DoesNotExist:
                return Response({
                    'message': 'Transaction not found!',
                    'subMessage': 'No transaction found with the provided reference.'
                }, status=404)
        else:
            return Response({
                'message': 'Payment verification failed!',
                'subMessage': 'Flutterwave API verification failed.'
            }, status=400)
    else:
        return Response({
            'message': 'Payment failed!',
            'subMessage': 'The payment status was not successful.'
        }, status=400)




from uuid import uuid4
from rest_framework.decorators import api_view
from rest_framework.response import Response
import paypalrestsdk
from .models import Cart, Transaction

@api_view(["POST"])
def initiate_paypal_payment(request):
    if request.method == 'POST' and request.user.is_authenticated:
        tx_ref = str(uuid4())  
        user = request.user
        cart_code = request.data.get("cart_code")
        
        try:
            cart = Cart.objects.get(cart_code=cart_code)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=404)
        
        total_amount = sum(item.product.price * item.quantity for item in cart.items.all())
        
        tax_amount = 4 
        total_amount_with_tax = total_amount + tax_amount
        
        paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET,
        })
        
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": f"{BASE_URL}/payment-status?paymentStatus=success&ref={tx_ref}",
                "cancel_url": f"{BASE_URL}/payment-status?paymentStatus=cancel&ref={tx_ref}"
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": "Cart Items",
                        "sku": cart_code,
                        "price": str(total_amount_with_tax),
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": str(total_amount_with_tax),
                    "currency": "USD"
                },
                "description": "Payment for items in cart including tax."
            }]
        })
        
        transaction, created = Transaction.objects.get_or_create(
            ref=tx_ref,
            cart=cart,
            amount=total_amount_with_tax,
            user=user,
            status='pending'
        )
        
        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = str(link.href)
                    return Response({"approval_url": approval_url})
        else:
            return Response({"error": payment.error}, status=400)

    else:
        return Response({"error": "Unauthorized request"}, status=401)




from rest_framework.decorators import api_view
from rest_framework.response import Response
import paypalrestsdk
from .models import Transaction


@api_view(['POST'])
def paypal_payment_callback(request):
    payment_id = request.query_params.get('paymentId')
    payer_id = request.query_params.get('PayerID')
    ref = request.query_params.get('ref')
    user = request.user

    print("Reference:", ref)

    transaction = Transaction.objects.get(ref=ref)

    if payment_id and payer_id:
        payment = paypalrestsdk.Payment.find(payment_id)

        if payment.state == 'approved':
            transaction.status = 'completed'
            transaction.save()

            cart = transaction.cart
            cart.paid = True
            cart.user = user
            cart.save()

            return Response({
                'message': 'Payment successful',
                'subMessage': 'You have successfully made a payment for the items you purchased.'
            })
        else:
            return Response({
                'error': 'Payment not approved or failed.'
            }, status=400)
    else:
        return Response({
            'error': 'Invalid payment details.'
        }, status=400)
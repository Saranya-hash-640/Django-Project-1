from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Product, Order, OrderItem,Cart, CartItem
from .forms import ProductForm


# ---------------- HOME ----------------
def welcome(request):
    return render(request, 'ecomm_app/welcome.html')

def home(request):
    products = Product.objects.all()
    return render(request, 'ecomm_app/home.html', {'products': products})


def home(request):
    products = Product.objects.all()
    recently_viewed_ids = request.session.get('recently_viewed', [])
    recently_viewed = Product.objects.filter(id__in=recently_viewed_ids)
    return render(request, 'ecomm_app/home.html', {
        'products': products,
        'recently_viewed': recently_viewed
    })

# ---------------- PRODUCT LIST / DETAIL ----------------
def product_list(request):
    products = Product.objects.all()
    return render(request, 'ecomm_app/product_list.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)

    recently_viewed = request.session.get('recently_viewed', [])
    if pk in recently_viewed:
        recently_viewed.remove(pk)
    recently_viewed.insert(0, pk)
    request.session['recently_viewed'] = recently_viewed[:5]

    return render(request, 'ecomm_app/product_detail.html', {'product': product})

# ---------------- CART (SESSION) ----------------

# def cart_view(request):
#     cart = request.session.get('cart', {})
#     items, total = [], Decimal('0.00')

#     for pid, qty in cart.items():
#         product = get_object_or_404(Product, pk=int(pid))
#         subtotal = product.price * qty
#         total += subtotal
#         items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})

#     return render(request, 'ecomm_app/cart.html', {'items': items, 'total': total})

# def add_to_cart(request, product_id):
#     cart = request.session.get('cart', {})
#     pid = str(product_id)
#     cart[pid] = cart.get(pid, 0) + 1
#     request.session['cart'] = cart
#     request.session.modified = True
#     return redirect('ecomm_app:cart')

# def remove_from_cart(request, product_id):
#     cart = request.session.get('cart', {})
#     cart.pop(str(product_id), None)
#     request.session['cart'] = cart
#     request.session.modified = True
#     return redirect('ecomm_app:cart')

# def increase_quantity(request, product_id):
#     cart = request.session.get('cart', {})
#     pid = str(product_id)
#     cart[pid] = cart.get(pid, 0) + 1
#     request.session['cart'] = cart
#     request.session.modified = True
#     return redirect('ecomm_app:cart')

# def decrease_quantity(request, product_id):
#     cart = request.session.get('cart', {})
#     pid = str(product_id)
#     if pid in cart:
#         cart[pid] -= 1
#         if cart[pid] <= 0:
#             del cart[pid]
#     request.session['cart'] = cart
#     request.session.modified = True
#     return redirect('ecomm_app:cart')
# ---------------- CART HELPERS ----------------
def get_user_cart(user):
    cart, created = Cart.objects.get_or_create(user=user)
    return cart


# ---------------- CART VIEWS ----------------
@login_required
def cart_view(request):
    cart = get_user_cart(request.user)
    items = cart.items.all()
    total = cart.total()
    return render(request, 'ecomm_app/cart.html', {'items': items, 'total': total})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
    except (ValueError, TypeError):
        messages.error(request, "Invalid quantity")
        return redirect('ecomm_app:product_detail', pk=product_id)

    cart = get_user_cart(request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()
    messages.success(request, f"Added {product.name} to cart.")
    return redirect('ecomm_app:cart')


@login_required
def remove_from_cart(request, product_id):
    cart = get_user_cart(request.user)
    cart_item = cart.items.filter(product__id=product_id).first()
    if cart_item:
        cart_item.delete()
        messages.success(request, "Item removed from cart.")
    return redirect('ecomm_app:cart')


@login_required
def increase_quantity(request, product_id):
    cart = get_user_cart(request.user)
    cart_item = cart.items.filter(product__id=product_id).first()
    if cart_item:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('ecomm_app:cart')


@login_required
def decrease_quantity(request, product_id):
    cart = get_user_cart(request.user)
    cart_item = cart.items.filter(product__id=product_id).first()
    if cart_item:
        cart_item.quantity -= 1
        if cart_item.quantity <= 0:
            cart_item.delete()
        else:
            cart_item.save()
    return redirect('ecomm_app:cart')

# ---------------- CHECKOUT ----------------
def checkout(request):
    cart = get_user_cart(request.user)
    cart_items = cart.items.all()

    if not cart_items:
        messages.info(request, "Your cart is empty.")
        return redirect('ecomm_app:product_list')

    if request.method == 'POST':
        # Create order
        order = Order.objects.create(user=request.user)
        for item in cart_items:
            product = item.product
            if product.stock < item.quantity:
                messages.error(request, f"Not enough stock for {product.name}.")
                order.delete()
                return redirect('ecomm_app:cart')

            OrderItem.objects.create(order=order, product=product, quantity=item.quantity)
            product.stock -= item.quantity
            product.save()

        cart.items.all().delete()
        messages.success(request, f"Order #{order.id} placed successfully!")
        return redirect('ecomm_app:order_history')

    return render(request, 'ecomm_app/checkout.html', {'cart_items': cart_items, 'cart': cart})

# ---------------- ORDER HISTORY ----------------
@login_required
def order_history(request):
    orders = request.user.orders.all()
    return render(request, 'ecomm_app/order_history.html', {'orders': orders})

# ---------------- ADMIN PRODUCT CRUD ----------------
@staff_member_required
def admin_product_list(request):
    products = Product.objects.all()
    return render(request, 'ecomm_app/admin_product_list.html', {'products': products})

@staff_member_required
def admin_add_product(request):
    form = ProductForm(request.POST, request.FILES)
    if form.is_valid():
        form.save()
        return redirect('ecomm_app:admin_product_list')
    return render(request, 'ecomm_app/admin_add_product.html', {'form': form})

@staff_member_required
def admin_update_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST, request.FILES, instance=product)
    if form.is_valid():
        form.save()
        return redirect('ecomm_app:admin_product_list')
    return render(request, 'ecomm_app/admin_update_product.html', {'form': form})

@staff_member_required
def admin_delete_product(request, pk):
    get_object_or_404(Product, pk=pk).delete()
    return redirect('ecomm_app:admin_product_list')

# ---------------- ADMIN ORDER CRUD ----------------
@staff_member_required
def admin_order_list(request):
    orders = Order.objects.all()
    return render(request, 'ecomm_app/admin_order_list.html', {'orders': orders})

@staff_member_required
def admin_update_order(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.status = request.POST.get('status')
        order.save()
        return redirect('ecomm_app:admin_order_list')
    return render(request, 'ecomm_app/admin_update_order.html', {'order': order})

@staff_member_required
def admin_delete_order(request, pk):
    get_object_or_404(Order, pk=pk).delete()
    return redirect('ecomm_app:admin_order_list')

# ---------------- ADMIN DASHBOARD ----------------
@staff_member_required
def admin_dashboard(request):
    context = {
        'total_products': Product.objects.count(),
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(status='P').count(),
        'shipped_orders': Order.objects.filter(status='S').count(),
        'delivered_orders': Order.objects.filter(status='D').count(),
        'latest_orders': Order.objects.order_by('-order_date')[:5],
        'latest_products': Product.objects.order_by('-created_at')[:5],
    }
    return render(request, 'ecomm_app/admin_dashboard.html', context)

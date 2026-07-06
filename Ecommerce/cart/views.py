
import random as rnd
import ast
from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail
from ml.predictor import predict_price
from .models import Review
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import auth, messages
from django.contrib.auth.models import User

from cart.forms import ProductForm
from cart.models import *
from cart.utils import (
    run_autonomous_agent,
    normalize_product_images,
    normalize_image_url,
    decide_for_product,
)
from cart.decorators import admin_required, is_admin
from django.shortcuts import render
from chatbot.query_to_sql import ask_sql, generate_response


# 🔹 Home
from cart.models import Product

import ast

def home(request):

    featured_products = Product.objects.exclude(
        image_url=""
    )[:8]

    trending_products = Product.objects.exclude(
        image_url=""
    ).order_by('-id')[:8]

    top_rated = Product.objects.exclude(
        rating=None
    ).exclude(
        image_url=""
    ).order_by('-rating')[:8]

    normalize_product_images(
        list(featured_products)
        + list(trending_products)
        + list(top_rated)
    )

    from cart.categories import STANDARD_CATEGORIES
    from django.db.models import Count

    shop_categories = Category.objects.filter(
        name__in=STANDARD_CATEGORIES
    ).annotate(
        product_count=Count('product')
    ).filter(product_count__gt=0).order_by('name')

    context = {

        'featured_products': featured_products,

        'trending_products': trending_products,

        'top_rated': top_rated,

        'shop_categories': shop_categories,

    }

    return render(
        request,
        'home.html',
        context
    )

def base_home(request):
    return render(request, 'base_home.html')

# 🔹 Login

def login(request):

    if request.method == 'POST':

        username = request.POST.get("username")
        password = request.POST.get("password")

        # ✅ remember me checkbox
        remember_me = request.POST.get("remember_me")

        user = auth.authenticate(
            username=username,
            password=password
        )

        if user is not None:

            auth.login(request, user)

            # ✅ SESSION SETTINGS
            if not remember_me:
                # logout when browser closes
                request.session.set_expiry(0)

            else:
                # keep login for 7 days
                request.session.set_expiry(60 * 60 * 24 * 7)

            # ✅ REDIRECT
            if user.is_superuser:
                return redirect('admin_login')
            else:
                return redirect('user_login')

        else:
            messages.error(
                request,
                "Invalid username or password"
            )

            return redirect('login')

    return render(request, 'login.html')


# 🔹 Logout
def logout(request):
    auth.logout(request)
    return redirect('login')


# 🔹 Admin Register
def admin_register(request):
    if request.method == 'POST':

        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        image = request.FILES.get('image')

        # Only one admin
        if User.objects.filter(is_superuser=True).exists():
            messages.error(request, 'Admin already exists')
            return redirect('admin_register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('admin_register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return redirect('admin_register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # 🔥 Make admin
        user.is_superuser = True
        user.is_staff = True
        user.save()

        # Create profile
        UserProfile.objects.create(
            user=user,
            phone=phone,
            address=address,
            profile_image=image
        )

        messages.success(request, 'Admin registered successfully')
        return redirect('login')

    return render(request, 'admin_register.html')


# 🔹 User Register
def user_register(request):
    if request.method == 'POST':

        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        username = request.POST.get('username')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        image = request.FILES.get('image')

        if User.objects.filter(email=email).exists():
            messages.success(request, 'Email already exists')
            return redirect('user_register')

        if User.objects.filter(username=username).exists():
            messages.success(request, 'Username already taken')
            return redirect('user_register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Create profile
        UserProfile.objects.create(
            user=user,
            phone=phone,
            address=address,
            profile_image=image,
        )

        messages.success(request, 'Registration successful')
        return redirect('login')

    return render(request, 'user_register.html')


# 🔹 Admin Dashboard Access
def admin_login(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if not request.user.is_superuser:
        return redirect('home')

    # 📊 COUNTS
    product_count = Product.objects.count()
    user_count = User.objects.count()
    order_count = Order.objects.count()

    # 💰 TOTAL REVENUE
    total_revenue = sum(order.total_amount for order in Order.objects.all())

    # 📦 RECENT ORDERS
    orders = Order.objects.all().order_by('-id')[:5]

    return render(request, 'admin_login.html', {
        'product_count': product_count,
        'user_count': user_count,
        'order_count': order_count,
        'total_revenue': total_revenue,
        'orders': orders
    })

def user_login(request):
    all_logs = AgentLog.objects.all().order_by('-created_at')

    # 🔹 Now safe filtering
    buy_logs = all_logs.filter(decision="BUY").count()

    # 🔹 Now slice for display
    logs = all_logs[:10]

    # 🔹 Orders
    orders = Order.objects.filter(user=request.user)
    total_spent = sum(o.total_amount for o in orders)
    total_saved = int(total_spent * 0.1)

    # 🔹 Trust %
    total_logs = all_logs.count()
    trust = int((buy_logs / total_logs) * 100) if total_logs > 0 else 0

    # 🔹 Activity
    activities = UserActivity.objects.filter(user=request.user)
    if not request.user.is_authenticated:
        return redirect('login')

    return render(request, 'user_log.html',{ 'logs': logs,
        'total_saved': total_saved,
        'total_logs': total_logs,
        'activities': activities,
        'trust': trust,})

def products_by_category(request, id):
    products = Product.objects.filter(category_id=id)
    normalize_product_images(products)
    categories = Category.objects.all()

    return render(request, 'featured_cat.html', {
        'products': products,
        'categories': categories
    })

from django.core.paginator import Paginator
from django.db.models import Q, Count
def products(request):

    products = Product.objects.select_related('category')

    # VALID IMAGES ONLY
    products = products.exclude(image_url__isnull=True)
    products = products.exclude(image_url="")
    products = products.exclude(image_url__iexact="nan")
    products = products.exclude(image_url__iexact="none")

    # SEARCH
    query = request.GET.get('q')

    if query:
        products = products.filter(
            Q(name__icontains=query)
        )

    # CATEGORY
    category = request.GET.get('category')

    if category:

        if category.isdigit():

            products = products.filter(
                category_id=category
            )

        else:

            products = products.filter(
                category__name=category
            )

    # ====================================
    # SEE ALL SECTIONS
    # ====================================

    section = request.GET.get('section')

    if section == "featured":

        products = products.order_by(
            '-rating',
            '-id'
        )

    elif section == "trending":

        products = products.order_by(
            '?'
        )

    # ====================================
    # SORTING
    # ====================================

    sort = request.GET.get('sort')

    if sort == 'low':

        products = products.order_by('price')

    elif sort == 'high':

        products = products.order_by('-price')

    elif sort == 'rating':

        products = products.order_by(
            '-rating',
            '-id'
        )

    else:

        if not section:
            products = products.order_by('-id')

    # PAGINATION

    paginator = Paginator(products, 24)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    normalize_product_images(
        page_obj.object_list
    )

    from cart.categories import STANDARD_CATEGORIES

    categories = Category.objects.filter(
        name__in=STANDARD_CATEGORIES
    ).order_by('name')

    return render(

        request,

        'product.html',

        {

            'products': page_obj,
            'categories': categories,
            'page_obj': page_obj,
            'section': section,
            'sort': sort

        }

    )
@login_required()
def user_reviews(request):
    from django.core.paginator import Paginator

    if request.method == "POST":
        product_id = request.POST.get('product')
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        try:
            product = Product.objects.get(id=product_id)
            Review.objects.create(
                user=request.user,
                product=product,
                rating=rating,
                comment=comment
            )
            messages.success(request, 'Review submitted successfully! ✅')
        except Product.DoesNotExist:
            messages.error(request, 'Invalid product selected.')

        return redirect('user_reviews')

    # Paginate — only load 10 reviews at a time
    all_reviews = Review.objects.filter(user=request.user).order_by('-id')
    paginator = Paginator(all_reviews, 10)
    page_number = request.GET.get('page', 1)
    reviews = paginator.get_page(page_number)

    # Don't pass all 10,000 products — use AJAX search instead
    return render(request, 'user_reviews.html', {
        'reviews': reviews,
        'page_obj': reviews,
    })


def product_search_ajax(request):
    """AJAX endpoint: returns up to 15 products matching a search query."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})
    products = Product.objects.filter(name__icontains=q)[:15]
    results = [{'id': p.id, 'name': p.name} for p in products]
    return JsonResponse({'results': results})

from django.shortcuts import render
from .models import (
    Product,
    PriceHistory,
    Review,
    UserActivity
)

def product_detail(request, id):

    product = Product.objects.get(id=id)

    product.image_url = normalize_image_url(
        product.image_url
    )

    # =====================================
    # USER ACTIVITY
    # =====================================

    if request.user.is_authenticated:

        UserActivity.objects.create(
            user=request.user,
            product=product,
            action="view"
        )

    # =====================================
    import json as _json

    history = list(
        PriceHistory.objects.filter(product=product).order_by('date')
    )

    # price_list = Python list used for all calculations below
    price_list = [round(float(h.price), 2) for h in history]

    # Serialize as proper JSON strings so Chart.js gets valid JS arrays
    dates  = _json.dumps([h.date.strftime("%d %b %y") for h in history])
    prices = _json.dumps(price_list)

    current_price = float(product.price)


    # =====================================
    # STORE COMPARISON
    # =====================================

    store_prices = Product.objects.filter(
        name=product.name
    )

    normalize_product_images(store_prices)

    all_prices = [
        float(p.price)
        for p in store_prices
        if p.price
    ]

    if all_prices:

        lowest_price = min(all_prices)

        highest_price = max(all_prices)

        avg_price = round(
            sum(all_prices) / len(all_prices),
            2
        )

    else:

        lowest_price = current_price
        highest_price = current_price
        avg_price = current_price

    # =====================================
    # REVIEWS
    # =====================================

    amazon_reviews = Review.objects.filter(
        product__name=product.name,
        platform='Amazon'
    )

    flipkart_reviews = Review.objects.filter(
        product__name=product.name,
        platform='Flipkart'
    )

    amazon_avg = 0
    flipkart_avg = 0

    if amazon_reviews.exists():

        amazon_avg = round(
            sum(r.rating for r in amazon_reviews)
            / amazon_reviews.count(),
            1
        )

    else:

        amazon_product = Product.objects.filter(
            name=product.name,
            platform__iexact='Amazon'
        ).first()

        if amazon_product and amazon_product.rating:
            amazon_avg = round(
                float(amazon_product.rating),
                1
            )

    if flipkart_reviews.exists():

        flipkart_avg = round(
            sum(r.rating for r in flipkart_reviews)
            / flipkart_reviews.count(),
            1
        )

    else:

        flipkart_product = Product.objects.filter(
            name=product.name,
            platform__iexact='Flipkart'
        ).first()

        if flipkart_product and flipkart_product.rating:
            flipkart_avg = round(
                float(flipkart_product.rating),
                1
            )

    # =====================================
    # OVERALL RATING
    # =====================================

    if amazon_avg and flipkart_avg:

        combined_rating = round(
            (amazon_avg + flipkart_avg) / 2,
            1
        )

    elif amazon_avg:

        combined_rating = amazon_avg

    elif flipkart_avg:

        combined_rating = flipkart_avg

    else:

        combined_rating = float(
            product.rating or 0
        )

    # =====================================
    # AI BUYING SCORE (SMART VERSION)
    # =====================================

    # Rating Score (40%)
    rating_score = min(
        (combined_rating / 5) * 40,
        40
    )

    # Price Score (30%)
    if highest_price > lowest_price:

        price_position = (
                (highest_price - current_price)
                /
                (highest_price - lowest_price)
        )

        price_score = price_position * 30

    else:

        price_score = 15

    # Review Count Score (20%)
    review_count = (
            amazon_reviews.count()
            +
            flipkart_reviews.count()
    )

    review_score = min(
        review_count / 10,
        20
    )

    # Trend Score (10%)
    trend_score = 10

    score = round(
        rating_score +
        price_score +
        review_score +
        trend_score
    )

    score = min(score, 100)

    angle = (score / 100) * 180 - 90

    # Decision Text

    if score >= 90:

        decision_text = "🔥 Excellent Buy"
        decision_color = "#00c853"

    elif score >= 80:

        decision_text = "✅ Strong Buy"
        decision_color = "#22c55e"

    elif score >= 70:

        decision_text = "👍 Buy Now"
        decision_color = "#84cc16"

    elif score >= 60:

        decision_text = "🤔 Consider Buying"
        decision_color = "#f59e0b"

    else:

        decision_text = "⏳ Wait For Better Price"
        decision_color = "#ef4444"
    # =====================================
    # FUTURE PRICE PREDICTION
    # =====================================

    days = int(
        request.GET.get("days", 7)
    )

    if len(price_list) >= 2:

        recent_change = (
                price_list[-1]
                -
                price_list[0]
        )

        daily_change = (
                recent_change
                /
                len(price_list)
        )

    else:

        daily_change = 0


    predicted_price = round(
        current_price +
        (daily_change * days),
        2
    )

    predicted_savings = max(
        round(
            current_price - predicted_price,
            2
        ),
        0
    )

    if predicted_price < current_price:

        future_trend = (
            f"Price may drop in {days} days 📉"
        )

    elif predicted_price > current_price:

        future_trend = (
            f"Price may increase in {days} days 📈"
        )

    else:

        future_trend = "Stable Price 📊"
    # =====================================
    # BEST PLATFORM
    # =====================================

    amazon_product = Product.objects.filter(
        name=product.name,
        platform__iexact="Amazon"
    ).first()

    flipkart_product = Product.objects.filter(
        name=product.name,
        platform__iexact="Flipkart"
    ).first()

    amazon_price = float(amazon_product.price) if amazon_product else 999999

    flipkart_price = float(flipkart_product.price) if flipkart_product else 999999

    amazon_score = (amazon_avg * 20)
    flipkart_score = (flipkart_avg * 20)

    # Lower price gets bonus

    if amazon_price < flipkart_price:

        amazon_score += 20

    elif flipkart_price < amazon_price:

        flipkart_score += 20

    # Final Recommendation

    if amazon_score > flipkart_score:

        best_platform = "Amazon"
        platform_reason = (
            f"Amazon offers better value with a price of ₹{amazon_price:.2f} "
            f"and rating of {amazon_avg}/5."
        )

    elif flipkart_score > amazon_score:

        best_platform = "Flipkart"
        platform_reason = (
            f"Flipkart offers better value with a price of ₹{flipkart_price:.2f} "
            f"and rating of {flipkart_avg}/5."
        )

    else:

        best_platform = "Either Platform"
        platform_reason = (
            "Both platforms provide similar value."
        )

    # =====================================
    # REVIEW SUMMARY
    # =====================================
    total_reviews = (
            amazon_reviews.count()
            +
            flipkart_reviews.count()
    )
    review_summary = (
        f"Based on {total_reviews} customer reviews collected from Amazon and Flipkart, "
        f"the product has an average rating of {combined_rating}/5. "
    )

    if combined_rating >= 4.5:

        review_summary += (
            "Customers consistently praise product quality, performance, "
            "durability, and overall value for money. "
            "Negative feedback is minimal."
        )

    elif combined_rating >= 4:

        review_summary += (
            "Most customers report a positive experience. "
            "Users particularly appreciate usability, quality, "
            "and reliability. A small number of users reported minor issues."
        )

    elif combined_rating >= 3:

        review_summary += (
            "Customer opinions are mixed. While many buyers are satisfied, "
            "others mention concerns regarding performance, quality consistency, "
            "or value for money."
        )

    else:

        review_summary += (
            "Customer feedback is generally negative. "
            "Common complaints include product quality, performance issues, "
            "and unmet expectations."
        )

    # =====================================
    # AI TAGS
    # =====================================

    ai_tags = []

    if combined_rating >= 4.5:
        ai_tags.append("Top Rated")

    if current_price == lowest_price:
        ai_tags.append("Best Price")

    if score >= 85:
        ai_tags.append("AI Recommended")

    if not ai_tags:
        ai_tags = [
            "Trending Product",
            "Popular Choice"
        ]

    # =====================================
    # EXPERT ANALYSIS
    # =====================================

    if score >= 90:

        expert_analysis = (
            f"The {product.name} is currently one of the strongest options "
            f"in the {product.category.name if product.category else 'product'} category. "
            f"It combines excellent customer ratings ({combined_rating}/5), "
            f"competitive pricing, and strong market sentiment. "
            f"Our AI recommends purchasing immediately."
        )

    elif score >= 80:

        expert_analysis = (
            f"The {product.name} offers strong overall value. "
            f"With a customer rating of {combined_rating}/5 and pricing close "
            f"to the market low of ₹{lowest_price}, it represents a smart purchase. "
            f"The product performs well compared to similar alternatives."
        )

    elif score >= 70:

        expert_analysis = (
            f"The {product.name} is a reliable choice with positive customer feedback. "
            f"Although it is not currently at its lowest historical price, "
            f"the product maintains good ratings and stable demand."
        )

    elif score >= 60:

        expert_analysis = (
            f"The {product.name} delivers average value for money. "
            f"Customer satisfaction is moderate ({combined_rating}/5), "
            f"and better deals may be available from competing brands. "
            f"Comparing alternatives before purchase is recommended."
        )

    else:

        expert_analysis = (
            f"The {product.name} currently shows weaker buying signals. "
            f"Ratings, pricing trends, or customer feedback suggest that "
            f"waiting for a better offer or exploring alternatives could be beneficial."
        )
    # =====================================
    # RENDER
    # =====================================

    return render(

        request,

        'product_detail.html',

        {

            'product': product,

            'dates': dates,
            'prices': prices,

            'score': score,
            'angle': angle,

            'decision_text': decision_text,
            'decision_color': decision_color,

            'highest_price': highest_price,
            'lowest_price': lowest_price,
            'avg_price': avg_price,
            'best_price': lowest_price,

            'predicted_price': predicted_price,
            'predicted_savings': predicted_savings,

            'future_trend': future_trend,

            'store_prices': store_prices,

            'amazon_reviews': amazon_reviews,
            'flipkart_reviews': flipkart_reviews,

            'amazon_avg': amazon_avg,
            'flipkart_avg': flipkart_avg,

            'combined_rating': combined_rating,

            'platform_reason': platform_reason,

            'review_summary': review_summary,

            'ai_tags': ai_tags,

            'expert_analysis': expert_analysis,

        }

    )


@login_required
def add_to_cart(request, id):

    product = Product.objects.get(id=id)
    user = request.user

    # 🔹 Get or create cart item
    cart_item, created = Cart.objects.get_or_create(
        user=user,
        product=product
    )

    # 🔹 If already exists increase quantity
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    # ✅ WEBSITE NOTIFICATION
    message = f"{product.name} added to cart successfully 🛒"

    Notification.objects.create(
        user=user,
        message=message
    )

    # ✅ EMAIL NOTIFICATION
    if user.email:
        send_notification_email(user, message)

    return redirect('cart_page')

@login_required
def cart_page(request):
    cart_items = Cart.objects.filter(user=request.user)

    total = 0
    for item in cart_items:
        total += item.product.price * item.quantity

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def increase_qty(request, id):
    cart_item = get_object_or_404(Cart, id=id, user=request.user)

    cart_item.quantity += 1
    cart_item.save()

    return redirect('cart_page')


# ➖ Decrease Quantity
@login_required
def decrease_qty(request, id):
    cart_item = get_object_or_404(Cart, id=id, user=request.user)

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        # If quantity = 1 → remove item
        cart_item.delete()

    return redirect('cart_page')

def send_notification_email(user, message):

    send_mail(
        subject="🛒 OptiCart Order Confirmation",
        message=f"""
Hello {user.username},

{message}

Thank you for shopping with OptiCart!

- Team OptiCart
""",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=True,
    )

@login_required
def test_email(request):
    send_notification_email(
        request.user,
        "Test Email Working ✅"
    )
    return HttpResponse(f"Email sent to {request.user.email}")

@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)

    total = 0
    for item in cart_items:
        total += item.product.price * item.quantity

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def place_order(request):

    cart_items = Cart.objects.filter(user=request.user)

    if not cart_items.exists():
        return redirect('cart_page')

    total = 0
    for item in cart_items:
        total += item.product.price * item.quantity

    order = Order.objects.create(
        user=request.user,
        total_amount=total,
        is_simulated=True,
    )

    # ✅ CREATE ORDER ITEMS
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity
        )

    # ✅ SAVE NOTIFICATION (DB)
    message = f"Your order #{order.id} has been placed successfully ✅"

    Notification.objects.create(
        user=request.user,
        message=message
    )

    # ✅ 🔥 SEND EMAIL (ADD THIS)
    if request.user.email:
        send_notification_email(request.user, message)

    # ✅ CLEAR CART
    cart_items.delete()

    return redirect('order_success')

# @login_required
# def buy_now(request, id):
#     product = get_object_or_404(Product, id=id)
#
#     if request.method == "POST":
#         name = request.POST.get('name')
#         address = request.POST.get('address')
#         payment = request.POST.get('payment')
#
#         # ✅ Create Order
#         order = Order.objects.create(
#             user=request.user,
#             total_amount=product.price,
#             status='Placed',
#             is_simulated=True,
#         )
#
#         # ✅ Create Order Item
#         OrderItem.objects.create(
#             order=order,
#             product=product,
#             quantity=1
#         )
#
#         # ✅ Message
#         message = f"You bought {product.name} successfully 🎉"
#
#         # ✅ Save Notification
#         Notification.objects.create(
#             user=request.user,
#             message=message
#         )
#
#         # ✅ 🔥 SEND EMAIL (THIS WAS MISSING)
#         if request.user.email:
#             send_notification_email(request.user, message)
#
#         return redirect('orders')
#
#     return render(request, 'buy_now.html', {
#         'product': product
#     })
@login_required
def buy_now(request, id):
    """
    Smart Buy Now — finds the cheapest platform for the product
    and redirects directly to Amazon or Flipkart.
    """
    product = get_object_or_404(Product, id=id)

    # Get all listings for this product across platforms, sorted cheapest first
    all_listings = list(
        Product.objects.filter(name=product.name).order_by('price')
    )

    cheapest = all_listings[0] if all_listings else product

    # If the user confirmed and wants to redirect to external site
    if request.GET.get('confirm') == '1' and cheapest.product_url:
        return redirect(cheapest.product_url)

    # Otherwise show comparison/confirmation page
    savings = None
    if len(all_listings) >= 2:
        savings = round(all_listings[-1].price - cheapest.price, 2)

    return render(request, 'buy_now.html', {
        'product': product,
        'cheapest': cheapest,
        'all_listings': all_listings,
        'savings': savings,
    })
@login_required
def cancel_order(request, id):

    order = get_object_or_404(Order, id=id, user=request.user)

    # Only allow cancel if not delivered
    if order.status != 'Delivered':

        order.status = 'Cancelled'
        order.save()

        # ✅ MESSAGE
        message = f"Order #{order.id} has been cancelled ❌"

        # ✅ WEBSITE NOTIFICATION
        Notification.objects.create(
            user=request.user,
            message=message
        )

        # ✅ EMAIL NOTIFICATION
        if request.user.email:
            send_notification_email(request.user, message)

    return redirect('orders')


@login_required
def remove_from_cart(request, id):
    cart_item = Cart.objects.get(id=id, user=request.user)
    cart_item.delete()
    return redirect('cart_page')

@login_required
def order_success(request):
    return render(request, 'order_success.html')

@login_required
def orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-id')

    return render(request, 'orders.html', {
        'orders': orders
    })

@admin_required
def update_order_status(request, id):
    order = get_object_or_404(Order, id=id)

    if request.method == "POST":
        status = request.POST.get('status')
        order.status = status
        order.save()
    Notification.objects.create(
        user=order.user,
        message=f"Your order #{order.id} is now {status} 🚚"
    )
    return redirect('admin_orders')

@login_required
def invoice(request, id):
    order = Order.objects.get(id=id, user=request.user)
    items = OrderItem.objects.filter(order=order)

    return render(request, 'invoice.html', {
        'order': order,
        'items': items
    })

@login_required
def add_to_wishlist(request, id):
    product = get_object_or_404(Product, id=id)

    # Prevent duplicates
    Wishlist.objects.get_or_create(user=request.user, product=product)
    Notification.objects.create(
        user=request.user,
        message=f"{product.name} added to wishlist ❤️"
    )
    return redirect('wishlist')


# ❌ Remove from Wishlist
@login_required
def remove_from_wishlist(request, id):
    item = get_object_or_404(Wishlist, id=id, user=request.user)
    item.delete()
    return redirect('wishlist')


# ❤️ Wishlist Page
@login_required
def wishlist_page(request):
    items = Wishlist.objects.filter(user=request.user)
    return render(request, 'wishlist.html', {'items': items})


@login_required
def profile(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        # ✅ Update email
        request.user.email = request.POST.get('email')
        request.user.save()

        # ✅ Update profile fields
        profile.phone = request.POST.get('phone')
        profile.address = request.POST.get('address')

        # ✅ Prevent NULL error
        profile.preferred_category = (
            request.POST.get('category') or ""
        )

        # ✅ Profile image
        if request.FILES.get('image'):
            profile.profile_image = request.FILES.get('image')

        profile.save()

    return render(request, 'profile.html', {
        'profile': profile
    })
@admin_required
def admin_products(request):

    products = Product.objects.select_related('category').all()

    return render(
        request,
        'admin_products.html',
        {
            'products': products
        }
    )

@admin_required
def delete_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == "POST":
        product.delete()

    return redirect('admin_products')

# 🔻 PRICE DROP CHECK
def check_price_drop(product, old_price, new_price):

    if new_price < old_price:

        users = User.objects.all()

        for user in users:

            message = f"🔻 Price dropped for {product.name} from ₹{old_price} to ₹{new_price}"

            # WEBSITE NOTIFICATION
            Notification.objects.create(
                user=user,
                message=message
            )

            # EMAIL NOTIFICATION
            if user.email:
                send_notification_email(user, message)


@admin_required
def edit_product(request, id):

    product = get_object_or_404(Product, id=id)

    # ✅ Store old values
    old_price = product.price
    old_stock = product.stock

    if request.method == "POST":

        form = ProductForm(request.POST, request.FILES, instance=product)

        if form.is_valid():

            updated_product = form.save()

            # ✅ SAVE PRICE HISTORY
            if old_price != updated_product.price:

                PriceHistory.objects.create(
                    product=updated_product,
                    price=updated_product.price
                )

                # ✅ PRICE DROP ALERT
                if updated_product.price < old_price:

                    users = User.objects.all()

                    for user in users:

                        message = (
                            f"🔻 Price dropped for "
                            f"{updated_product.name}\n"
                            f"From ₹{old_price} to ₹{updated_product.price}"
                        )

                        # WEBSITE NOTIFICATION
                        Notification.objects.create(
                            user=user,
                            message=message
                        )

                        # EMAIL
                        if user.email:
                            send_notification_email(user, message)

            # ✅ BACK IN STOCK ALERT
            if old_stock == 0 and updated_product.stock > 0:

                users = User.objects.all()

                for user in users:

                    message = f"🔥 {updated_product.name} is back in stock!"

                    # WEBSITE
                    Notification.objects.create(
                        user=user,
                        message=message
                    )

                    # EMAIL
                    if user.email:
                        send_notification_email(user, message)

            return redirect('admin_products')

    else:
        form = ProductForm(instance=product)

    return render(request, 'add_product.html', {
        'form': form
    })



# Categories Page
@admin_required
def admin_categories(request):
    categories = Category.objects.all()
    return render(request, 'admin_categories.html', {'categories': categories})


# Users Page
@admin_required
def admin_users(request):
    users = User.objects.all()
    return render(request, 'admin_user.html', {'users': users})

@admin_required
def delete_user(request, id):
    if request.method == "POST":
        user = get_object_or_404(User, id=id)


        if user != request.user:
            user.delete()

    return redirect('admin_users')


# Orders Page
@admin_required
def admin_orders(request):
    orders = Order.objects.all()
    return render(request, 'admin_orders.html', {'orders': orders})


# Reviews (Dummy for now)
from django.db.models import Avg

@admin_required
def admin_reviews(request):
    reviews = Review.objects.select_related(
        'user',
        'product'
    ).all().order_by('-id')

    high_rating_count = reviews.filter(rating__gte=4).count()
    medium_rating_count = reviews.filter(rating=3).count()
    low_rating_count = reviews.filter(rating__lte=2).count()

    avg_rating = reviews.aggregate(
        avg=Avg('rating')
    )['avg'] or 0

    return render(request, 'admin_reviews.html', {
        'reviews': reviews,
        'high_rating_count': high_rating_count,
        'medium_rating_count': medium_rating_count,
        'low_rating_count': low_rating_count,
        'avg_rating': round(avg_rating, 1),
    })

@admin_required
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin_products')  # change if needed
    else:
        form = ProductForm()

    return render(request, 'add_product.html', {'form': form})
# 🔔 Show notifications
@login_required
def notifications_page(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifications})


# ✅ Mark as read
@login_required
def mark_as_read(request, id):
    notification = get_object_or_404(Notification, id=id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications')

@login_required
def mark_all_as_read(request):

    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    return redirect('notifications')

def price_graph(request, id):
    product = Product.objects.get(id=id)

    data = product.pricehistory_set.all().order_by('date')

    dates = [d.date.strftime("%d %b") for d in data]
    prices = [float(d.price) for d in data]

    return JsonResponse({
        'dates': dates,
        'prices': prices
    })

def product_image_proxy(request, product_id):
    """Serve cached/downloaded image or category placeholder."""
    from cart.image_fetch import serve_product_image

    product = get_object_or_404(Product.objects.select_related("category"), pk=product_id)
    content, content_type = serve_product_image(product)

    response = HttpResponse(content, content_type=content_type)
    response["Cache-Control"] = "public, max-age=86400"
    return response


def compare_products(request):
    query = request.GET.get('q')

    compared = []
    lowest_price = None

    if query:
        compared = Product.objects.filter(name__icontains=query)
        normalize_product_images(compared)

        if compared:
            lowest_price = min(p.price for p in compared)

    return render(request, 'compare.html', {
        'compared': compared,
        'lowest_price': lowest_price
    })


from .models import Product, AgentLog


def _ai_simulation_context(request):
    """Shared context for AI Simulation / Agent Logs dashboard."""

    if AgentLog.objects.count() == 0:
        products = Product.objects.exclude(price__isnull=True)[:100]
        for product in products:
            decision, reason = decide_for_product(product)
            AgentLog.objects.create(
                product=product,
                decision=decision,
                reason=reason,
            )

    query = request.GET.get('q', '').strip()

    logs = AgentLog.objects.select_related('product').order_by('-created_at')

    if query:
        logs = logs.filter(
            Q(product__name__icontains=query)
            | Q(decision__icontains=query)
            | Q(reason__icontains=query)
        )

    filtered_logs = list(logs[:200])

    return {
        'logs': filtered_logs,
        'query': query,
        'total': logs.count(),
        'bought': logs.filter(decision='BUY').count(),
        'waited': logs.filter(decision='WAIT').count(),
        'skipped': logs.filter(decision='SKIP').count(),
        'showing': len(filtered_logs),
    }


def ai_simulation(request):
    return render(
        request,
        'ai_simulation.html',
        _ai_simulation_context(request),
    )

def price_predict(request, id):
    product = get_object_or_404(Product, id=id)
    days = int(request.GET.get('days', 3))

    history = list(
        PriceHistory.objects.filter(product=product)
        .order_by('date')
        .values_list('price', flat=True)
    )
    history_prices = [float(p) for p in history[-10:]]
    current_price = float(product.price or 0)
    while len(history_prices) < 10:
        history_prices.append(current_price)

    product_data = {
        "current_price": current_price,
        "rating": float(product.rating or 0),
        "price_day_1": history_prices[0],
        "price_day_2": history_prices[1],
        "price_day_3": history_prices[2],
        "price_day_4": history_prices[3],
        "price_day_5": history_prices[4],
        "price_day_6": history_prices[5],
        "price_day_7": history_prices[6],
        "price_day_8": history_prices[7],
        "price_day_9": history_prices[8],
        "price_day_10": history_prices[9],
        "avg_price": sum(history_prices) / len(history_prices),
        "max_price": max(history_prices),
        "min_price": min(history_prices),
        "volatility": max(history_prices) - min(history_prices),
        "trend": history_prices[-1] - history_prices[0],
        "trend_percent": (
            (history_prices[-1] - history_prices[0]) / history_prices[0]
            if history_prices[0]
            else 0
        ),
    }

    predicted = predict_price(product_data)
    savings_pct = (
        ((current_price - predicted) / current_price) * 100
        if current_price
        else 0
    )

    if predicted < current_price and savings_pct >= 5:
        score, text, color = 75, "Buy Soon", "green"
    elif predicted < current_price:
        score, text, color = 55, "Wait a bit", "orange"
    else:
        score, text, color = 30, "Wait for drop", "red"

    if days == 7:
        score = max(20, score - 15)
    elif days >= 14:
        score = max(10, score - 25)

    return JsonResponse({
        "score": score,
        "text": text,
        "color": color,
        "predicted_price": predicted,
    })



def run_agent(request):
    run_autonomous_agent()

    # ✅ Redirect to results page
    return redirect('agent_logs')


def agent_logs(request):
    return render(
        request,
        'ai_simulation.html',
        _ai_simulation_context(request),
    )

@login_required
def settings_page(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        # ✅ BASIC INFO
        profile.phone = request.POST.get('phone')
        profile.address = request.POST.get('address')

        # safer float handling
        budget = request.POST.get('budget')
        profile.budget = budget if budget else None

        profile.preferred_category = request.POST.get('category')

        # ✅ PROFILE IMAGE
        if request.FILES.get('image'):
            profile.profile_image = request.FILES.get('image')

        # 🔔 NOTIFICATION SETTINGS
        profile.email_alerts = 'email_alerts' in request.POST
        profile.price_drop_alerts = 'price_drop_alerts' in request.POST

        # 🔐 SECURITY SETTINGS
        profile.login_alerts = 'login_alerts' in request.POST
        profile.two_factor_auth = 'two_factor_auth' in request.POST

        # 💳 PAYMENT SETTINGS
        profile.preferred_payment = request.POST.get(
            'preferred_payment'
        )

        profile.upi_id = request.POST.get('upi_id') or profile.upi_id

        # 🔒 CHANGE PASSWORD
        new_password = request.POST.get('new_password')

        if new_password:

            request.user.set_password(new_password)
            request.user.save()

            # ✅ keeps user logged in
            update_session_auth_hash(request, request.user)

        # ✅ SAVE
        profile.save()

        messages.success(
            request,
            "Settings updated successfully ✅"
        )

        return redirect('settings')

    return render(request, 'setting.html', {
        'profile': profile
    })



@login_required
def user_activity_log(request):

    # 🔹 Get all logs first (NO slicing here)
    all_logs = AgentLog.objects.all().order_by('-created_at')

    # 🔹 Now safe filtering
    buy_logs = all_logs.filter(decision="BUY").count()

    # 🔹 Now slice for display
    logs = all_logs[:10]

    # 🔹 Orders
    orders = Order.objects.filter(user=request.user)
    total_spent = sum(o.total_amount for o in orders)
    total_saved = int(total_spent * 0.1)

    # 🔹 Trust %
    total_logs = all_logs.count()
    trust = int((buy_logs / total_logs) * 100) if total_logs > 0 else 0

    # 🔹 Activity
    activities = UserActivity.objects.filter(user=request.user)

    return render(request, 'user_activity.html', {
        'logs': logs,
        'total_saved': total_saved,
        'total_logs': total_logs,
        'activities': activities,
        'trust': trust,
    })





@login_required
def add_payment(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        profile.preferred_payment = request.POST.get('payment_type') or profile.preferred_payment
        profile.upi_id = request.POST.get('upi_id') or profile.upi_id
        profile.save(update_fields=['preferred_payment', 'upi_id'])

        messages.success(
            request,
            "Payment Method Added ✅"
        )

        return redirect('settings')

    return redirect('settings')



import json

from django.http import JsonResponse
from django.shortcuts import render


from django.http import JsonResponse
import json

from service.chatbot_service import final_result


def chatbot_page(request):

    if request.method == "POST":

        data = json.loads(request.body)

        user_query = data.get("message")

        print("USER QUERY:", user_query)

        try:

            response = final_result(user_query)

        except Exception as e:

            response = str(e)

        return JsonResponse({
            "response": response
        })

    return JsonResponse({
        "response": "Invalid request"
    })
# def chatbot_page(request):
#
#     response = ""
#     user_query = ""
#
#     if request.method == "POST":
#
#         user_query = request.POST.get("message")
#
#         if user_query:
#
#             response = final_result(user_query)
#
#     return render(request,
#                   "chatbot.html",
#                   {
#                       "response": response,
#                       "user_query": user_query
#                   })




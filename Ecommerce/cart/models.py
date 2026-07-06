from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


# 🔹 1. User Profile (Accounts + Registration Extension)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    #  Registration Fields
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    password = models.CharField(max_length=200, null=True)

    # Existing Fields
    budget = models.FloatField(null=True, blank=True)
    preferred_category = models.CharField(max_length=100, blank=True,null=True)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)

    # 🔐 Security Settings
    email_alerts = models.BooleanField(default=True)
    price_drop_alerts = models.BooleanField(default=True)
    login_alerts = models.BooleanField(default=False)
    two_factor_auth = models.BooleanField(default=False)

    # 💳 Payment Settings
    card_name = models.CharField(max_length=100, null=True, blank=True)
    card_number = models.CharField(max_length=20, null=True, blank=True)
    expiry_date = models.CharField(max_length=10, null=True, blank=True)
    cvv = models.CharField(max_length=5, null=True, blank=True)
    upi_id = models.CharField(max_length=100, null=True, blank=True)

    PAYMENT_CHOICES = (
        ('Card', 'Card'),
        ('UPI', 'UPI'),
        ('COD', 'Cash on Delivery'),
    )

    preferred_payment = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default='COD'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


#  2. Category (Product Module)
class Category(models.Model):
    name = models.CharField(max_length=100,null=True)

    def __str__(self):
        return self.name



class Product(models.Model):

    PLATFORM_CHOICES = (
        ('Amazon', 'Amazon'),
        ('Flipkart', 'Flipkart'),
    )

    name = models.CharField(max_length=200,null=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,null=True
    )

    price = models.FloatField(null=True)

    rating = models.FloatField(
        null=True,
        blank=True
    )
    ai_score = models.FloatField(default=0.0)
    platform = models.CharField(
        max_length=50,
        choices=PLATFORM_CHOICES,null=True,
        default='Amazon'
    )

    image_url = models.URLField(
        blank=True,
        null=True
    )

    product_url = models.URLField(null=True,blank=True)

    description = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name

# 🔹 4. Wishlist Module
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,null=True)
    added_at = models.DateTimeField(auto_now_add=True,null=True)

    class Meta:
        unique_together = ('user', 'product')  # 🔥 prevents duplicates

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


#  5. Cart Module
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    is_agent = models.BooleanField(default=False)
    added_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


#  6. Price History Module
class PriceHistory(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.FloatField()
    date = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return f"{self.product.name} - {self.price}"


#  7. Notification Module
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    message = models.TextField(null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return f"Notification for {self.user.username}"


#  8. User Activity (Analytics Module)
class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=100)  # viewed, added_to_cart, etc.
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action}"


#  9. Contact (Static Pages Module)
class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()

    def __str__(self):
        return self.name


class Registration(models.Model):
    Password = models.CharField(max_length=200, null=True)
    Registration_date = models.DateField(auto_now_add=True, null=True)
    User_role = models.CharField(max_length=200, null=True)
    user = models.OneToOneField(User,on_delete = models.CASCADE, null = True)

    def __str__(self):
        return self.Password

class Order(models.Model):
    STATUS_CHOICES = (
        ('Placed', 'Placed'),
        ('Shipped', 'Shipped'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.FloatField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Placed")
    is_simulated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()




class AgentLog(models.Model):
    DECISION_CHOICES = (
        ('BUY', 'BUY'),
        ('WAIT', 'WAIT'),
        ('SKIP', 'SKIP'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    decision = models.CharField(max_length=10, choices=DECISION_CHOICES)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.decision}"


class Review(models.Model):

    PLATFORM_CHOICES = (
        ('Amazon', 'Amazon'),
        ('Flipkart', 'Flipkart'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    # ✅ ADD THIS
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        null=True,
        blank=True
    )

    rating = models.IntegerField()

    comment = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return f"{self.product.name} - {self.platform} - {self.rating}"
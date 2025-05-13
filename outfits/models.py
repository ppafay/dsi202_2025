# dsi202/outfits/models.py

from django.db import models
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

class Outfit(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='outfits/', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00')) # Price per day
    is_rented = models.BooleanField(default=False) # General availability flag

    def __str__(self):
        return self.name

class Cart(models.Model):
    RENTAL_STATUS_CHOICES = [
        ('pending_payment', 'รอการชำระเงิน'),
        ('payment_confirmed', 'ยืนยันการชำระเงินแล้ว'),
        ('processing', 'กำลังเตรียมชุด'),
        ('shipped', 'จัดส่งแล้ว'),
        ('delivered', 'ลูกค้าได้รับแล้ว'),
        ('customer_returning', 'ลูกค้ากำลังส่งคืน'),
        ('returned_received', 'ร้านได้รับชุดคืนแล้ว'),
        ('completed', 'เสร็จสมบูรณ์'),
        ('issue_reported', 'ลูกค้าแจ้งปัญหา'),
        ('cancelled', 'ยกเลิกแล้ว'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carts'
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_paid = models.BooleanField(default=False)
    payment_slip = models.ImageField(upload_to='payment_slips/', blank=True, null=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    rental_status = models.CharField(
        max_length=25, # Increased length
        choices=RENTAL_STATUS_CHOICES,
        default='pending_payment',
        null=True, blank=True
    )
    customer_uploaded_image = models.ImageField(
        upload_to='customer_order_issues/',
        null=True,
        blank=True,
        help_text="ลูกค้าสามารถแนบรูปภาพที่เกี่ยวข้องกับคำสั่งซื้อนี้ (เช่น แจ้งปัญหา)"
    )

    def __str__(self):
        if self.user:
            return f"Cart/Order {self.id} for {self.user.username}"
        return f"Guest Cart/Order {self.id}"

    def calculate_total_price(self):
        total = Decimal('0.00')
        for item in self.cart_items_cart.all():
            total += item.get_total_item_price()
        self.total_price = total
        return total

    def get_total_price(self):
        return self.calculate_total_price()

    @property
    def item_count(self):
        return self.cart_items_cart.aggregate(total_quantity=models.Sum('quantity'))['total_quantity'] or 0

    def mark_as_paid(self, payment_slip_file):
        self.is_paid = True
        self.payment_slip = payment_slip_file
        self.paid_at = timezone.now()
        self.rental_status = 'payment_confirmed' # Changed status upon payment confirmation
        self.save()

    def get_latest_return_date(self):
        latest_date = None
        for item in self.cart_items_cart.filter(end_date__isnull=False):
            if latest_date is None or item.end_date > latest_date:
                latest_date = item.end_date
        return latest_date

class CartItem(models.Model):
    outfit = models.ForeignKey(Outfit, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1) # Should be 1 for rentals
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='cart_items_cart'
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    item_price_at_rental = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"{self.quantity} x {self.outfit.name} in Cart {self.cart.id}"

    def get_rental_days(self):
        if self.start_date and self.end_date and self.start_date <= self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    def get_total_item_price(self):
        rental_days = self.get_rental_days()
        if rental_days > 0:
            return self.outfit.price * rental_days * self.quantity
        return Decimal('0.00')

    def save(self, *args, **kwargs):
        if self.start_date and self.end_date:
            self.item_price_at_rental = self.get_total_item_price()
        else:
            self.item_price_at_rental = Decimal('0.00')
        super().save(*args, **kwargs)
        if self.cart:
            self.cart.calculate_total_price()
            self.cart.save(update_fields=['total_price'])

    @property
    def is_date_selection_pending(self):
        return not self.start_date or not self.end_date
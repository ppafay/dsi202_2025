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
    is_rented = models.BooleanField(default=False) # General availability flag (can be enhanced for multi-stock)

    def __str__(self):
        return self.name

class Cart(models.Model):
    RENTAL_STATUS_CHOICES = [
        ('pending_payment', 'รอการชำระเงิน'),
        ('payment_confirmed', 'ยืนยันการชำระเงินแล้ว'),
        ('processing', 'กำลังเตรียมชุด'),
        ('shipped', 'จัดส่งแล้ว'),
        ('delivered', 'ลูกค้าได้รับแล้ว'),
        ('customer_returning', 'ลูกค้าแจ้งส่งคืนแล้ว'),
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
        max_length=25,
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
    return_tracking_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="เลขพัสดุส่งคืน"
    )
    return_shipment_image = models.ImageField(
        upload_to='return_shipments/',
        null=True,
        blank=True,
        verbose_name="รูปภาพหลักฐานการส่งคืน"
    )

    def __str__(self):
        status_info = f" (สถานะ: {self.get_rental_status_display()})" if self.is_paid and self.rental_status else " (ยังไม่ได้ชำระเงิน)"
        user_info = f"ของ {self.user.username}" if self.user else "(Guest)"
        return f"คำสั่งซื้อ #{self.id} {user_info}{status_info}"

    def calculate_and_set_total_price(self):
        """Calculates total price from items and updates self.total_price."""
        current_total = Decimal('0.00')
        for item in self.cart_items_cart.all(): # Ensure this related_name is correct
            current_total += item.get_total_item_price()
        
        if self.total_price != current_total:
            self.total_price = current_total
            # self.save(update_fields=['total_price']) # Avoid saving here to prevent recursion if called during save
                                                    # The calling function (e.g., view or CartItem.save) should handle saving the Cart.
        return self.total_price

    def get_total_price(self):
        # Returns the current total_price field.
        # For display, it's assumed this field is kept up-to-date.
        return self.total_price

    @property
    def item_count(self):
        """Returns the total number of individual items (sum of quantities)."""
        count = self.cart_items_cart.aggregate(total_quantity=models.Sum('quantity'))['total_quantity']
        return count or 0

    def mark_as_paid(self, payment_slip_file):
        """Marks the cart as paid and sets relevant fields. View should save."""
        self.is_paid = True
        self.payment_slip = payment_slip_file
        self.paid_at = timezone.now()
        self.rental_status = 'payment_confirmed'

    def get_latest_return_date(self):
        latest_date = None
        items = self.cart_items_cart.filter(end_date__isnull=False)
        if not items.exists():
            return None
        for item in items:
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
        return f"{self.quantity} x {self.outfit.name} ในตะกร้า {self.cart.id}"

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
        # Update the item's stored price based on current dates
        if self.start_date and self.end_date:
            self.item_price_at_rental = self.get_total_item_price()
        else:
            self.item_price_at_rental = Decimal('0.00')
        
        super().save(*args, **kwargs) # Save the CartItem itself first

        # After saving the CartItem, update its Cart's total_price
        if self.cart:
            new_cart_total = self.cart.calculate_and_set_total_price() # Calculate and set on cart instance
            if self.cart.total_price != new_cart_total : # Check if recalculation changed it
                 self.cart.total_price = new_cart_total
            self.cart.save(update_fields=['total_price']) # Save only the total_price of the cart

    def delete(self, *args, **kwargs):
        cart_to_update = self.cart
        super().delete(*args, **kwargs) # Delete the CartItem
        if cart_to_update:
            new_cart_total = cart_to_update.calculate_and_set_total_price()
            if cart_to_update.total_price != new_cart_total:
                cart_to_update.total_price = new_cart_total
            cart_to_update.save(update_fields=['total_price'])

    @property
    def is_date_selection_pending(self):
        return not self.start_date or not self.end_date
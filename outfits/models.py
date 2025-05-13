from django.db import models
from decimal import Decimal
from django.conf import settings


class Outfit(models.Model):
    """
    โมเดลสำหรับเก็บข้อมูลชุดแต่งกาย
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='outfits/', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_rented = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Cart(models.Model):
    """
    โมเดลสำหรับเก็บข้อมูลตะกร้าสินค้า
    """
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

    def __str__(self):
        if self.user:
            return f"Cart {self.id} for {self.user.username}"
        return f"Guest Cart {self.id}"

    def get_total_price(self):
        total = Decimal('0.00')
        for item in self.cart_items_cart.all():  # ต้องใช้ related_name เดียวกับ CartItem
            total += item.get_total_item_price()
        self.total_price = total
        return total

    @property
    def item_count(self):
        return self.cart_items_cart.count()


class CartItem(models.Model):
    """
    โมเดลสำหรับเก็บข้อมูลรายการสินค้าในตะกร้า
    """
    outfit = models.ForeignKey(Outfit, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='cart_items_cart'  # ใช้ชื่อเดียวกับใน Cart
    )

    def __str__(self):
        return f"{self.quantity} x {self.outfit.name} in Cart {self.cart.id}"

    def get_total_item_price(self):
        return self.outfit.price * self.quantity

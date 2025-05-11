# project/main/dsi202/outfits/models.py
from django.db import models
from decimal import Decimal # Import Decimal
from django.conf import settings # สำหรับ AUTH_USER_MODEL
from django.utils import timezone # สำหรับ default value ของ DateTimeField ถ้าจำเป็น

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

class Cart(models.Model): # <--- แก้ไข Cart Model ตรงนี้
    """
    โมเดลสำหรับเก็บข้อมูลตะกร้าสินค้า
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, # หรือ models.SET_NULL ถ้าไม่อยากให้ลบตะกร้าเมื่อ user ถูกลบ
        null=True,  # อนุญาตให้ guest (ไม่มี user) มีตะกร้าได้
        blank=True, # อนุญาตให้ field นี้ว่างได้ในฟอร์ม (ถ้ามี)
        related_name='carts' # ชื่อสำหรับอ้างอิงจาก User model มายัง Cart (เช่น user.carts.all())
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True) # Django จะใส่เวลาตอนสร้าง object ให้อัตโนมัติ
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)     # Django จะใส่เวลาตอน save object ให้อัตโนมัติ

    def __str__(self):
        if self.user:
            return f"Cart {self.id} for {self.user.username}"
        return f"Guest Cart {self.id}"

    def get_total_price(self):
        total = Decimal('0.00')
        # 'cart_items_cart' คือ related_name จาก CartItem.cart มายัง Cart
        # ตรวจสอบให้แน่ใจว่า related_name ใน CartItem.cart คือ 'cart_items_cart'
        for item in self.cart_items_cart.all():
            total += item.get_total_item_price()
        self.total_price = total
        # ไม่จำเป็นต้อง save() ที่นี่ทุกครั้งที่ get_total_price()
        # ควร save() ใน view เมื่อมีการเปลี่ยนแปลงที่ทำให้ total_price เปลี่ยน
        return total

    # (Optional) เพิ่ม property เพื่อความสะดวกในการเรียกจำนวนสินค้าในตะกร้า
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
        Cart, # แก้จาก 'Cart' (string) เป็น Cart (class) โดยตรงถ้า Cart ถูก define ไว้ข้างบนแล้ว
        on_delete=models.CASCADE,
        related_name='cart_items_cart' # related_name สำหรับ Cart model เรียก CartItem
    )

    def __str__(self):
        return f"{self.quantity} x {self.outfit.name} in Cart {self.cart.id}"

    def get_total_item_price(self):
        # คำนวณราคารวมสำหรับ CartItem นี้
        return self.outfit.price * self.quantity
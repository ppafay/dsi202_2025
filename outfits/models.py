# project/main/dsi202/outfits/models.py
from django.db import models
from decimal import Decimal # Import Decimal

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

class CartItem(models.Model):
    """
    โมเดลสำหรับเก็บข้อมูลรายการสินค้าในตะกร้า
    """
    outfit = models.ForeignKey(Outfit, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, related_name='cart_items_cart')

    def __str__(self):
        return f"{self.outfit.name} x {self.quantity}"

    # ---> ตรวจสอบให้แน่ใจว่า method นี้เขียนถูกต้อง <---
    def get_total_item_price(self):  # ต้องมี def, self, และเครื่องหมาย :
        # คำนวณราคารวมสำหรับ CartItem นี้
        return self.outfit.price * self.quantity

class Cart(models.Model):
    """
    โมเดลสำหรับเก็บข้อมูลตะกร้าสินค้า
    """
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"Cart {self.id}"

    def get_total_price(self):
        total = Decimal('0.00')
        for item in self.cart_items_cart.all(): # ใช้ related_name ที่ถูกต้อง
            total += item.get_total_item_price() # เรียกใช้ method ที่ถูกต้องของ CartItem
        self.total_price = total
        # ไม่จำเป็นต้อง save() ที่นี่ทุกครั้งที่ get_total_price()
        # อาจจะ save() เมื่อมีการเปลี่ยนแปลงจริงๆ เช่น ใน view add_to_cart, update_cart, remove_from_cart
        # self.save() # พิจารณาว่าจะ save ที่นี่ หรือใน view
        return total
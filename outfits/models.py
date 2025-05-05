from django.db import models

class Outfit(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='outfits/', null=True, blank=True)
    price = models.FloatField(default=0.0)
    is_rented = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # ... ฟิลด์อื่น ๆ ที่เกี่ยวข้องกับสินค้า (เช่น รูปภาพ, รายละเอียด)

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # เชื่อมโยงกับ Product
    quantity = models.PositiveIntegerField(default=1)
    # ... ฟิลด์อื่น ๆ ที่เกี่ยวข้องกับรายการในตะกร้า

class Cart(models.Model):
    items = models.ManyToManyField(CartItem)  # เชื่อมโยงกับ CartItem
    # ... ฟิลด์อื่น ๆ ที่เกี่ยวข้องกับตะกร้าสินค้า

class Outfit(models.Model):  # โมเดล Outfit ของคุณ
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='outfits/', null=True, blank=True)
    price = models.FloatField(default=0.0)
    is_rented = models.BooleanField(default=False)

    def __str__(self):
        return self.name
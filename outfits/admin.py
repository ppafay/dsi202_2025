# project/main/dsi202/outfits/admin.py

from django.contrib import admin
from .models import Outfit, Cart, CartItem # <--- 1. Import Cart และ CartItem เข้ามา

# Admin for Outfit (อันนี้ซิสมีอยู่แล้ว)
@admin.register(Outfit)
class OutfitAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_rented', 'id') # เพิ่ม id เข้าไปดูด้วยก็ได้
    list_filter = ('is_rented',)
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_rented') # ทำให้แก้ไขราคาและสถานะการเช่าจากหน้ารายการได้เลย (optional)

# --- 2. Register Model Cart และ CartItem ---

# วิธีที่ 1: Register แบบง่ายๆ ก่อน (ยังไม่ custom อะไรมาก)
# admin.site.register(Cart)
# admin.site.register(CartItem)

# วิธีที่ 2: Register พร้อมปรับแต่งการแสดงผลด้วย ModelAdmin (แนะนำ)

class CartItemInline(admin.TabularInline): # หรือจะใช้ admin.StackedInline ก็ได้ แล้วแต่ชอบหน้าตา
    model = CartItem
    extra = 0  # จำนวนฟอร์มเปล่าๆ ของ CartItem ที่จะแสดงในหน้า Cart (0 คือไม่แสดงฟอร์มเปล่า)
    readonly_fields = ('outfit_name', 'item_price', 'total_item_price_display') # Field ที่อยากให้แสดง แต่แก้ไขไม่ได้ใน inline
    fields = ('outfit', 'outfit_name', 'quantity', 'item_price', 'total_item_price_display') # เรียง field ตามนี้

    def outfit_name(self, obj):
        return obj.outfit.name
    outfit_name.short_description = 'ชื่อชุด'

    def item_price(self, obj):
        return obj.outfit.price
    item_price.short_description = 'ราคาต่อหน่วย'

    def total_item_price_display(self, obj):
        if obj.pk: # เช็คว่า obj มีจริงใน DB (กรณีเพิ่มใหม่ยังไม่มี pk)
            return obj.get_total_item_price()
        return "N/A"
    total_item_price_display.short_description = 'ราคารวมรายการนี้'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_display', 'total_price_display', 'created_at_display', 'updated_at_display', 'item_count') # เพิ่มฟังก์ชันแสดงจำนวน item และวันเวลา
    list_filter = ('user',) # ถ้า Cart มี foreign key ไปที่ User
    search_fields = ('id', 'user__username') # ค้นหาจาก ID ของ Cart หรือ username ของ User (ถ้ามี)
    readonly_fields = ('id', 'total_price', 'created_at', 'updated_at') # Field ที่ไม่ควรแก้ไขได้โดยตรงในหน้า Admin
    inlines = [CartItemInline] # <--- ทำให้เราเห็นและแก้ไข CartItem ที่อยู่ใน Cart นั้นๆ ได้เลย

    fieldsets = (
        (None, {
            'fields': ('user', 'id', 'created_at', 'updated_at') # ถ้ามี field user, created_at, updated_at ใน Cart model
        }),
        ('สรุปยอดตะกร้า', {
            'fields': ('total_price',), # total_price จะถูกคำนวณและแสดงผล (อาจจะ readonly)
        }),
    )

    def user_display(self, obj):
        if obj.user:
            return obj.user.username
        return "Guest Cart" # หรือ Anonymous Cart
    user_display.short_description = 'ผู้ใช้งาน'

    def total_price_display(self, obj):
        return f"฿{obj.total_price:,.2f}" # Format ให้สวยงาม
    total_price_display.short_description = 'ราคารวมสุทธิ'

    def item_count(self, obj):
        return obj.cart_items_cart.count() # cart_items_cart คือ related_name จาก CartItem -> Cart
    item_count.short_description = 'จำนวนรายการ'

    def created_at_display(self, obj):
        if obj.created_at: # สมมติว่า Cart model มี field created_at
            return obj.created_at.strftime("%d %b %Y, %H:%M")
        return "-"
    created_at_display.short_description = 'วันที่สร้าง'

    def updated_at_display(self, obj):
        if obj.updated_at: # สมมติว่า Cart model มี field updated_at
            return obj.updated_at.strftime("%d %b %Y, %H:%M")
        return "-"
    updated_at_display.short_description = 'วันที่อัปเดตล่าสุด'

    # Override queryset เพื่อให้ get_total_price ถูกเรียกเมื่อโหลด list view
    # (แต่อาจจะไม่จำเป็นถ้า total_price ใน model ถูกอัปเดตเสมอเมื่อมีการเปลี่ยนแปลง CartItem)
    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
    #     for cart_instance in qs:
    #         cart_instance.get_total_price() # เรียกเพื่อให้ total_price update
    #         cart_instance.save() # อาจจะไม่ต้อง save ทุกครั้งถ้า get_total_price ไม่ได้ save
    #     return qs


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart_id_display', 'outfit_link', 'quantity', 'calculated_price')
    list_filter = ('cart__user', 'outfit__name') # Filter จาก user ของตะกร้า หรือ ชื่อชุด
    search_fields = ('outfit__name', 'cart__id', 'cart__user__username')
    autocomplete_fields = ['outfit', 'cart'] # ทำให้ช่อง Outfit กับ Cart ค้นหาได้ง่ายขึ้น (ถ้ามีข้อมูลเยอะ)
    list_editable = ('quantity',) # แก้ไขจำนวนจากหน้ารายการได้เลย

    def cart_id_display(self, obj):
        return obj.cart.id
    cart_id_display.short_description = 'ID ตะกร้า'

    def outfit_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse("admin:outfits_outfit_change", args=[obj.outfit.id]) # outfits_outfit คือ appname_modelname
        return format_html('<a href="{}">{}</a>', link, obj.outfit.name)
    outfit_link.short_description = 'ชุด (คลิกเพื่อแก้ไข)'
    outfit_link.admin_order_field = 'outfit__name' # ทำให้ sort ตามชื่อ outfit ได้

    def calculated_price(self, obj):
        return f"฿{obj.get_total_item_price():,.2f}"
    calculated_price.short_description = 'ราคารวมรายการนี้'

    # ควรจะ save Cart object ด้วยเมื่อ CartItem มีการเปลี่ยนแปลง (เพื่อให้ total_price ของ Cart อัปเดต)
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.cart: # ถ้า CartItem นี้มีตะกร้าผูกอยู่
            obj.cart.get_total_price() # คำนวณราคารวมของตะกร้าใหม่
            obj.cart.save()            # บันทึกตะกร้า

    def delete_model(self, request, obj):
        cart_to_update = obj.cart
        super().delete_model(request, obj)
        if cart_to_update:
            cart_to_update.get_total_price()
            cart_to_update.save()

    def delete_queryset(self, request, queryset):
        carts_to_update = set()
        for item in queryset:
            carts_to_update.add(item.cart)
        super().delete_queryset(request, queryset)
        for cart_instance in carts_to_update:
            if cart_instance:
                cart_instance.get_total_price()
                cart_instance.save()
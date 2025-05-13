from django.contrib import admin
from .models import Outfit, Cart, CartItem
from django.utils.html import format_html
from django.urls import reverse

@admin.register(Outfit)
class OutfitAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_rented', 'id')
    list_filter = ('is_rented',)
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_rented')

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('outfit_name', 'item_price', 'total_item_price_display')
    fields = ('outfit', 'outfit_name', 'quantity', 'item_price', 'total_item_price_display')

    def outfit_name(self, obj):
        return obj.outfit.name
    def item_price(self, obj):
        return obj.outfit.price
    def total_item_price_display(self, obj):
        return obj.get_total_item_price() if obj.pk else "N/A"

    outfit_name.short_description = 'ชื่อชุด'
    item_price.short_description = 'ราคาต่อหน่วย'
    total_item_price_display.short_description = 'ราคารวมรายการนี้'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_display', 'total_price_display', 'created_at_display', 'updated_at_display', 'item_count')
    search_fields = ('id', 'user__username')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [CartItemInline]

    def user_display(self, obj):
        return obj.user.username if obj.user else "Guest"
    def total_price_display(self, obj):
        return f"฿{obj.get_total_price():,.2f}"
    def item_count(self, obj):
        return obj.cart_items_cart.count()
    def created_at_display(self, obj):
        return obj.created_at.strftime("%d %b %Y, %H:%M") if obj.created_at else "-"
    def updated_at_display(self, obj):
        return obj.updated_at.strftime("%d %b %Y, %H:%M") if obj.updated_at else "-"

    user_display.short_description = 'ผู้ใช้งาน'
    total_price_display.short_description = 'ราคารวม'
    item_count.short_description = 'จำนวน'
    created_at_display.short_description = 'สร้างเมื่อ'
    updated_at_display.short_description = 'อัปเดตล่าสุด'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart_id_display', 'outfit_link', 'quantity', 'calculated_price')
    search_fields = ('outfit__name', 'cart__id', 'cart__user__username')
    autocomplete_fields = ['outfit', 'cart']
    list_editable = ('quantity',)

    def cart_id_display(self, obj):
        return obj.cart.id
    def outfit_link(self, obj):
        link = reverse("admin:outfits_outfit_change", args=[obj.outfit.id])
        return format_html('<a href="{}">{}</a>', link, obj.outfit.name)
    def calculated_price(self, obj):
        return f"฿{obj.get_total_item_price():,.2f}"

    cart_id_display.short_description = 'ID ตะกร้า'
    outfit_link.short_description = 'ชุด (คลิก)'
    calculated_price.short_description = 'ราคารวม'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.cart:
            obj.cart.save()

    def delete_model(self, request, obj):
        cart_to_update = obj.cart
        super().delete_model(request, obj)
        if cart_to_update:
            cart_to_update.save()

    def delete_queryset(self, request, queryset):
        carts_to_update = set(item.cart for item in queryset)
        super().delete_queryset(request, queryset)
        for cart in carts_to_update:
            cart.save()

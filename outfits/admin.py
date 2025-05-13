# dsi202/outfits/admin.py

from django.contrib import admin
from .models import Outfit, Cart, CartItem
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone # Import timezone for actions

@admin.register(Outfit)
class OutfitAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_per_day_display', 'is_rented', 'id')
    list_filter = ('is_rented',)
    search_fields = ('name', 'description')
    list_editable = ('is_rented',)
    fields = ('name', 'description', 'price', 'image', 'is_rented')

    def price_per_day_display(self, obj):
        return f"฿{obj.price:,.2f} / วัน"
    price_per_day_display.short_description = 'ราคาเช่าต่อวัน'

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = (
        'outfit_link_inline', 'outfit_price_per_day',
        'rental_days_display', 'calculated_item_price'
    )
    fields = (
        'outfit', 'outfit_link_inline', 'quantity',
        'start_date', 'end_date', 'outfit_price_per_day',
        'rental_days_display', 'calculated_item_price'
    )

    def outfit_link_inline(self, obj):
        if obj.outfit:
            link = reverse("admin:outfits_outfit_change", args=[obj.outfit.id])
            return format_html('<a href="{}">{}</a>', link, obj.outfit.name)
        return "-"
    outfit_link_inline.short_description = 'ชื่อชุด (คลิก)'

    def outfit_price_per_day(self, obj):
        return f"฿{obj.outfit.price:,.2f}" if obj.outfit else "N/A"
    outfit_price_per_day.short_description = 'ราคา/วัน'

    def rental_days_display(self, obj):
        return obj.get_rental_days()
    rental_days_display.short_description = 'จำนวนวันเช่า'

    def calculated_item_price(self, obj):
        price_to_display = obj.item_price_at_rental if obj.item_price_at_rental > 0 else obj.get_total_item_price()
        return f"฿{price_to_display:,.2f}"
    calculated_item_price.short_description = 'ราคารวมรายการนี้'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user_display', 'total_price_display',
        'is_paid',  # Use direct field name for list_editable
        'rental_status', # Use direct field name for list_editable
        'paid_at_display', 'created_at_display', 'item_count_display'
    )
    list_filter = ('is_paid', 'rental_status', 'created_at', 'paid_at', 'user')
    search_fields = ('id', 'user__username', 'cart_items_cart__outfit__name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'paid_at', 'total_price_display_field', 'payment_slip_preview', 'customer_uploaded_image_preview')
    fieldsets = (
        (None, {
            'fields': ('id', 'user', ('is_paid', 'paid_at'), 'payment_slip_preview', 'payment_slip') # Group is_paid and paid_at
        }),
        ('Rental Information', {
            'fields': ('rental_status', 'customer_uploaded_image_preview', 'customer_uploaded_image')
        }),
        ('Pricing & Timestamps', {
            'fields': ('total_price_display_field', 'created_at', 'updated_at')
        }),
    )
    inlines = [CartItemInline]
    list_per_page = 20
    list_editable = ('rental_status', 'is_paid') # These fields are now directly in list_display

    actions = ['mark_as_payment_confirmed', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_customer_returning','mark_as_returned_received', 'mark_as_completed', 'mark_as_cancelled']

    def mark_as_payment_confirmed(self, request, queryset):
        queryset.update(rental_status='payment_confirmed', is_paid=True, paid_at=timezone.now())
        self.message_user(request, "สถานะเปลี่ยนเป็น 'ยืนยันการชำระเงินแล้ว'")
    mark_as_payment_confirmed.short_description = "สถานะ: ยืนยันการชำระเงิน"

    def mark_as_processing(self, request, queryset):
        queryset.update(rental_status='processing')
        self.message_user(request, "สถานะเปลี่ยนเป็น 'กำลังเตรียมชุด'")
    mark_as_processing.short_description = "สถานะ: กำลังเตรียมชุด"

    def mark_as_shipped(self, request, queryset):
        queryset.update(rental_status='shipped')
        self.message_user(request, "สถานะเปลี่ยนเป็น 'จัดส่งแล้ว'")
    mark_as_shipped.short_description = "สถานะ: จัดส่งแล้ว"

    def mark_as_delivered(self, request, queryset):
        queryset.update(rental_status='delivered')
        self.message_user(request, "สถานะเปลี่ยนเป็น 'ลูกค้าได้รับแล้ว'")
    mark_as_delivered.short_description = "สถานะ: ลูกค้าได้รับแล้ว"

    def mark_as_customer_returning(self, request, queryset):
        queryset.update(rental_status='customer_returning')
        self.message_user(request, "สถานะเปลี่ยนเป็น 'ลูกค้ากำลังส่งคืน'")
    mark_as_customer_returning.short_description = "สถานะ: ลูกค้ากำลังส่งคืน"

    def mark_as_returned_received(self, request, queryset):
        queryset.update(rental_status='returned_received')
        self.message_user(request, "สถานะเปลี่ยนเป็น 'ร้านได้รับชุดคืนแล้ว'")
    mark_as_returned_received.short_description = "สถานะ: ร้านได้รับชุดคืนแล้ว"

    def mark_as_completed(self, request, queryset):
        queryset.update(rental_status='completed')
        self.message_user(request, "สถานะเปลี่ยนเป็น 'เสร็จสมบูรณ์'")
    mark_as_completed.short_description = "สถานะ: เสร็จสมบูรณ์"

    def mark_as_cancelled(self, request, queryset):
        queryset.update(rental_status='cancelled')
        self.message_user(request, "สถานะเปลี่ยนเป็น 'ยกเลิกแล้ว'")
    mark_as_cancelled.short_description = "สถานะ: ยกเลิกแล้ว"


    def user_display(self, obj): return obj.user.username if obj.user else "Guest"
    user_display.short_description = 'ผู้ใช้งาน'

    def total_price_display(self, obj):
        obj.calculate_total_price(); return f"฿{obj.total_price:,.2f}"
    total_price_display.short_description = 'ยอดรวม'; total_price_display.admin_order_field = 'total_price'

    def total_price_display_field(self, obj): # For readonly field in detail view
        obj.calculate_total_price(); return f"฿{obj.total_price:,.2f}"
    total_price_display_field.short_description = 'ยอดรวม (คำนวณล่าสุด)'

    # No longer need is_paid_display if 'is_paid' (boolean field) is in list_display
    # No longer need rental_status_display if 'rental_status' (field with choices) is in list_display
    # Django admin handles boolean and choices fields well in list_display.

    def paid_at_display(self, obj): return obj.paid_at.strftime("%d %b %Y, %H:%M") if obj.paid_at else "-"
    paid_at_display.short_description = 'ชำระเงินเมื่อ'; paid_at_display.admin_order_field = 'paid_at'

    def created_at_display(self, obj): return obj.created_at.strftime("%d %b %Y, %H:%M") if obj.created_at else "-"
    created_at_display.short_description = 'สร้างเมื่อ'; created_at_display.admin_order_field = 'created_at'

    def item_count_display(self, obj): return obj.item_count
    item_count_display.short_description = 'จำนวนรายการทั้งหมด'


    def payment_slip_preview(self, obj):
        if obj.payment_slip: return format_html('<a href="{}" target="_blank"><img src="{}" width="100" height="100" style="object-fit: cover;"/></a>', obj.payment_slip.url, obj.payment_slip.url)
        return "(No slip)"
    payment_slip_preview.short_description = 'สลิป'

    def customer_uploaded_image_preview(self, obj):
        if obj.customer_uploaded_image: return format_html('<a href="{}" target="_blank"><img src="{}" width="100" height="100" style="object-fit: cover;"/></a>', obj.customer_uploaded_image.url, obj.customer_uploaded_image.url)
        return "(No image)"
    customer_uploaded_image_preview.short_description = 'รูปจากลูกค้า'

    def save_model(self, request, obj, form, change):
        obj.calculate_total_price(); super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if formset.instance and isinstance(formset.instance, Cart):
            formset.instance.calculate_total_price(); formset.instance.save(update_fields=['total_price'])

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart_link', 'outfit_link', 'quantity', 'start_date_display', 'end_date_display', 'rental_days_display', 'calculated_price_display')
    list_filter = ('start_date', 'end_date', 'cart__is_paid')
    search_fields = ('outfit__name', 'cart__id', 'cart__user__username')
    autocomplete_fields = ['outfit', 'cart']
    list_editable = ('quantity',) # start_date and end_date are edited in detail view now
    list_per_page = 25
    ordering = ('-cart__id', 'id')
    fields = ('cart', 'outfit', 'quantity', 'start_date', 'end_date', 'item_price_at_rental_display')
    readonly_fields = ('item_price_at_rental_display',)

    def cart_link(self, obj):
        if obj.cart: link = reverse("admin:outfits_cart_change", args=[obj.cart.id]); user_info = f" (User: {obj.cart.user.username})" if obj.cart.user else " (Guest)"; return format_html('<a href="{}">Cart #{} {}</a>', link, obj.cart.id, user_info)
        return "N/A"
    cart_link.short_description = 'ตะกร้า (คลิก)'; cart_link.admin_order_field = 'cart__id'

    def outfit_link(self, obj):
        if obj.outfit: link = reverse("admin:outfits_outfit_change", args=[obj.outfit.id]); return format_html('<a href="{}">{}</a>', link, obj.outfit.name)
        return "N/A"
    outfit_link.short_description = 'ชุด (คลิก)'; outfit_link.admin_order_field = 'outfit__name'

    def start_date_display(self, obj): return obj.start_date.strftime("%d %b %Y") if obj.start_date else "-"
    start_date_display.short_description = 'วันเริ่มเช่า'; start_date_display.admin_order_field = 'start_date'

    def end_date_display(self, obj): return obj.end_date.strftime("%d %b %Y") if obj.end_date else "-"
    end_date_display.short_description = 'วันคืน'; end_date_display.admin_order_field = 'end_date'

    def rental_days_display(self, obj): return obj.get_rental_days()
    rental_days_display.short_description = 'จำนวนวัน'

    def calculated_price_display(self, obj):
        price = obj.item_price_at_rental if obj.item_price_at_rental > 0 else obj.get_total_item_price(); return f"฿{price:,.2f}"
    calculated_price_display.short_description = 'ราคารวมรายการ'; calculated_price_display.admin_order_field = 'item_price_at_rental'

    def item_price_at_rental_display(self,obj): return f"฿{obj.item_price_at_rental:,.2f}"
    item_price_at_rental_display.short_description = 'ราคาที่คำนวณแล้ว'

    def save_model(self, request, obj, form, change):
        obj.item_price_at_rental = obj.get_total_item_price(); super().save_model(request, obj, form, change)
        if obj.cart: obj.cart.calculate_total_price(); obj.cart.save(update_fields=['total_price'])

    def delete_model(self, request, obj):
        cart_to_update = obj.cart; super().delete_model(request, obj)
        if cart_to_update: cart_to_update.calculate_total_price(); cart_to_update.save(update_fields=['total_price'])

    def delete_queryset(self, request, queryset):
        carts_to_update = set(); [carts_to_update.add(item.cart) for item in queryset if item.cart]
        super().delete_queryset(request, queryset)
        for cart_obj in carts_to_update: cart_obj.calculate_total_price(); cart_obj.save(update_fields=['total_price'])
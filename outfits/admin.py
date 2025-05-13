
from django.contrib import admin
from .models import Outfit, Cart, CartItem, Category # <<< ตรวจสอบว่า import Category
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

# 1. CategoryAdmin (ควรจะประกาศก่อน OutfitAdmin ถ้า Outfit อ้างอิงถึง Category)
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'outfit_count_display') # เปลี่ยน outfit_count เป็น outfit_count_display
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

    def outfit_count_display(self, obj): # เปลี่ยนชื่อ method ให้ชัดเจน
        return obj.outfits.count()
    outfit_count_display.short_description = "จำนวนชุดในหมวดหมู่นี้"

# 2. OutfitAdmin (เหลือเพียงอันเดียว และแก้ไข list_display/list_editable)
@admin.register(Outfit)
class OutfitAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price_per_day_display', 'is_rented', 'id') # <<< ใช้ 'category' โดยตรง
    list_filter = ('is_rented', 'category')
    search_fields = ('name', 'description', 'category__name')
    list_editable = ('is_rented', 'category') # <<< 'category' สามารถแก้ไขได้แล้ว
    autocomplete_fields = ['category']
    fields = ('name', 'category', 'description', 'price', 'image', 'is_rented')

    def price_per_day_display(self, obj):
        return f"฿{obj.price:,.2f} / วัน"
    price_per_day_display.short_description = 'ราคาเช่าต่อวัน'
    # ไม่จำเป็นต้องมี category_display method อีกต่อไปถ้าใช้ 'category' ใน list_display โดยตรง

# 3. CartItemInline (เหมือนเดิมจากครั้งก่อน)
class CartItemInline(admin.TabularInline):
    model = CartItem; extra = 0
    readonly_fields = ('outfit_link_inline', 'outfit_price_per_day', 'rental_days_display', 'calculated_item_price', 'item_price_at_rental')
    fields = ('outfit', 'outfit_link_inline', 'quantity', 'start_date', 'end_date', 'outfit_price_per_day', 'rental_days_display', 'item_price_at_rental', 'calculated_item_price')

    def outfit_link_inline(self, obj):
        if obj.outfit: link = reverse("admin:outfits_outfit_change", args=[obj.outfit.id]); return format_html('<a href="{}">{}</a>', link, obj.outfit.name)
        return "-"
    outfit_link_inline.short_description = 'ชื่อชุด'
    def outfit_price_per_day(self, obj): return f"฿{obj.outfit.price:,.2f}" if obj.outfit else "N/A"
    outfit_price_per_day.short_description = 'ราคา/วัน'
    def rental_days_display(self, obj): return obj.get_rental_days()
    rental_days_display.short_description = 'วันเช่า'
    def calculated_item_price(self, obj): return f"฿{obj.get_total_item_price():,.2f}" # ราคาที่คำนวณสด
    calculated_item_price.short_description = 'ราคารวม (สด)'
    # item_price_at_rental แสดงราคาที่ถูกบันทึกไว้ตอนเช่า

# 4. CartAdmin (เหมือนเดิมจากครั้งก่อนที่แก้ไข IndentationError และ list_editable แล้ว)
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id','user_display','total_price_display','is_paid', 'rental_status','paid_at_display','created_at_display','item_count_display','return_tracking_number')
    list_filter = ('is_paid', 'rental_status', 'created_at', 'paid_at', 'user')
    search_fields = ('id', 'user__username', 'cart_items_cart__outfit__name')
    readonly_fields = ('id','created_at','updated_at','paid_at','total_price_display_field','payment_slip_preview','customer_uploaded_image_preview','return_shipment_image_preview')
    fieldsets = (
        (None, {'fields': ('id', 'user', ('is_paid', 'paid_at'), 'payment_slip_preview', 'payment_slip')}),
        ('Rental Information', {'fields': ('rental_status','customer_uploaded_image_preview','customer_uploaded_image','return_tracking_number','return_shipment_image_preview','return_shipment_image')}),
        ('Pricing & Timestamps', {'fields': ('total_price_display_field', 'created_at', 'updated_at')}),
    )
    inlines = [CartItemInline]; list_per_page = 20
    list_editable = ('rental_status', 'is_paid') # ถูกต้องแล้วเพราะ 'rental_status' และ 'is_paid' อยู่ใน list_display

    actions = ['mark_as_payment_confirmed', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_customer_returning','mark_as_returned_received', 'mark_as_completed', 'mark_as_cancelled']

    def _update_status(self, request, queryset, status_key, message_suffix):
        updated_count = queryset.update(rental_status=status_key)
        if status_key == 'payment_confirmed':
            queryset.update(is_paid=True, paid_at=timezone.now())
        self.message_user(request, f"{updated_count} รายการถูกเปลี่ยนสถานะเป็น '{message_suffix}'")

    def mark_as_payment_confirmed(self, r, qs): self._update_status(r, qs, 'payment_confirmed', "ยืนยันการชำระเงินแล้ว")
    mark_as_payment_confirmed.short_description = "สถานะ: ยืนยันการชำระเงิน"
    # ... (actions อื่นๆ เหมือนเดิม) ...
    def mark_as_processing(self, r, qs): self._update_status(r, qs, 'processing', "กำลังเตรียมชุด")
    mark_as_processing.short_description = "สถานะ: กำลังเตรียมชุด"
    def mark_as_shipped(self, r, qs): self._update_status(r, qs, 'shipped', "จัดส่งแล้ว")
    mark_as_shipped.short_description = "สถานะ: จัดส่งแล้ว"
    def mark_as_delivered(self, r, qs): self._update_status(r, qs, 'delivered', "ลูกค้าได้รับแล้ว")
    mark_as_delivered.short_description = "สถานะ: ลูกค้าได้รับแล้ว"
    def mark_as_customer_returning(self, r, qs): self._update_status(r, qs, 'customer_returning', "ลูกค้ากำลังส่งคืน")
    mark_as_customer_returning.short_description = "สถานะ: ลูกค้ากำลังส่งคืน"
    def mark_as_returned_received(self, r, qs): self._update_status(r, qs, 'returned_received', "ร้านได้รับชุดคืนแล้ว")
    mark_as_returned_received.short_description = "สถานะ: ร้านได้รับชุดคืนแล้ว"
    def mark_as_completed(self, r, qs): self._update_status(r, qs, 'completed', "เสร็จสมบูรณ์")
    mark_as_completed.short_description = "สถานะ: เสร็จสมบูรณ์"
    def mark_as_cancelled(self, r, qs): self._update_status(r, qs, 'cancelled', "ยกเลิกแล้ว")
    mark_as_cancelled.short_description = "สถานะ: ยกเลิกแล้ว"


    def user_display(self, o): return o.user.username if o.user else "Guest"; user_display.short_description='ผู้ใช้งาน'
    def total_price_display(self, o): o.calculate_and_set_total_price(); return f"฿{o.total_price:,.2f}"; total_price_display.short_description='ยอดรวม'; total_price_display.admin_order_field='total_price'
    def total_price_display_field(self, o): o.calculate_and_set_total_price(); return f"฿{o.total_price:,.2f}"; total_price_display_field.short_description='ยอดรวม (คำนวณ)'
    def paid_at_display(self, o): return o.paid_at.strftime("%d %b %Y, %H:%M") if o.paid_at else "-"; paid_at_display.short_description='ชำระเงินเมื่อ'; paid_at_display.admin_order_field='paid_at'
    def created_at_display(self, o): return o.created_at.strftime("%d %b %Y, %H:%M") if o.created_at else "-"; created_at_display.short_description='สร้างเมื่อ'; created_at_display.admin_order_field='created_at'
    def item_count_display(self, o): return o.item_count; item_count_display.short_description='จำนวนรายการ'
    def payment_slip_preview(self, o):
        if o.payment_slip: return format_html(f'<a href="{o.payment_slip.url}" target="_blank"><img src="{o.payment_slip.url}" width="100" height="100" style="object-fit:cover;border:1px solid #ddd;"/></a>')
        return "(No slip)"; payment_slip_preview.short_description='สลิป'
    def customer_uploaded_image_preview(self, o):
        if o.customer_uploaded_image: return format_html(f'<a href="{o.customer_uploaded_image.url}" target="_blank"><img src="{o.customer_uploaded_image.url}" width="100" height="100" style="object-fit:cover;border:1px solid #ddd;"/></a>')
        return "(No image)"; customer_uploaded_image_preview.short_description='รูปจากลูกค้า'
    def return_shipment_image_preview(self, o):
        if o.return_shipment_image: return format_html(f'<a href="{o.return_shipment_image.url}" target="_blank"><img src="{o.return_shipment_image.url}" width="100" height="100" style="object-fit:cover;border:1px solid #ddd;"/></a>')
        return "(No return image)"; return_shipment_image_preview.short_description='รูปหลักฐานส่งคืน'

    def save_model(self, request, obj, form, change):
        obj.calculate_and_set_total_price()
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if formset.instance and isinstance(formset.instance, Cart):
            current_total = formset.instance.calculate_and_set_total_price()
            if formset.instance.total_price != current_total:
                 formset.instance.total_price = current_total
            formset.instance.save(update_fields=['total_price'])

# 5. CartItemAdmin (เหมือนเดิมจากครั้งก่อนที่แก้ไข IndentationError และ list_editable แล้ว)
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id','cart_link','outfit_link','quantity','start_date_display','end_date_display','rental_days_display','calculated_price_display', 'item_price_at_rental_display_col')
    list_filter = ('start_date', 'end_date', 'cart__is_paid'); search_fields = ('outfit__name', 'cart__id', 'cart__user__username')
    autocomplete_fields = ['outfit', 'cart']; list_editable = ('quantity',); list_per_page = 25; ordering = ('-cart__id', 'id')
    fields = ('cart','outfit','quantity','start_date','end_date','item_price_at_rental_display'); readonly_fields = ('item_price_at_rental_display',)

    def cart_link(self, o):
        if o.cart: l=reverse("admin:outfits_cart_change",args=[o.cart.id]);ui=f" (User: {o.cart.user.username})" if o.cart.user else " (Guest)"; return format_html(f'<a href="{l}">Cart #{o.cart.id}{ui}</a>')
        return "N/A"; cart_link.short_description='ตะกร้า'; cart_link.admin_order_field='cart__id'
    def outfit_link(self, o):
        if o.outfit: l=reverse("admin:outfits_outfit_change",args=[o.outfit.id]); return format_html(f'<a href="{l}">{o.outfit.name}</a>')
        return "N/A"; outfit_link.short_description='ชุด'; outfit_link.admin_order_field='outfit__name'
    def start_date_display(self, o): return o.start_date.strftime("%d %b %Y") if o.start_date else "-"; start_date_display.short_description='เริ่มเช่า'; start_date_display.admin_order_field='start_date'
    def end_date_display(self, o): return o.end_date.strftime("%d %b %Y") if o.end_date else "-"; end_date_display.short_description='วันคืน'; end_date_display.admin_order_field='end_date'
    def rental_days_display(self, o): return o.get_rental_days(); rental_days_display.short_description='วัน'
    def calculated_price_display(self, o): return f"฿{o.get_total_item_price():,.2f}"; calculated_price_display.short_description='ราคารวม (สด)'
    def item_price_at_rental_display_col(self,o): return f"฿{o.item_price_at_rental:,.2f}"; item_price_at_rental_display_col.short_description='ราคาที่บันทึก'; item_price_at_rental_display_col.admin_order_field='item_price_at_rental'
    def item_price_at_rental_display(self,o): return f"฿{o.item_price_at_rental:,.2f}"; item_price_at_rental_display.short_description='ราคาที่บันทึกไว้สำหรับรายการนี้'

    def save_model(self, request, obj, form, change):
        # item_price_at_rental is set in CartItem.save()
        super().save_model(request, obj, form, change)
        # CartItem.save() now handles updating the cart's total_price.

    def delete_model(self, request, obj):
        # CartItem.delete() (overridden method) now handles updating the cart's total_price.
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        carts_to_update=set()
        for item in queryset:
            if item.cart: carts_to_update.add(item.cart)
        super().delete_queryset(request, queryset)
        for cart_obj in carts_to_update:
            current_total = cart_obj.calculate_and_set_total_price()
            if cart_obj.total_price != current_total:
                cart_obj.total_price = current_total
            cart_obj.save(update_fields=['total_price'])
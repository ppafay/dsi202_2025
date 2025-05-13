# dsi202/outfits/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

from .models import Outfit, CartItem, Cart
from .forms import (
    OutfitForm,
    PaymentConfirmationForm,
    CartItemDateSelectionForm,
    CustomerOrderImageUploadForm,
    ReturnShipmentForm
)

import base64
import io
import qrcode

# ---------------- หน้า home
def home(request):
    return render(request, 'outfits/home.html')

# ---------------- ชุดทั้งหมด
class OutfitListView(View):
    def get(self, request):
        outfits = Outfit.objects.all()
        return render(request, 'outfits/list.html', {'outfits': outfits})

# ---------------- ค้นหา
class OutfitSearchView(View):
    def get(self, request):
        query = request.GET.get('q')
        results = []
        if query:
            results = Outfit.objects.filter(name__icontains=query)
        return render(request, 'outfits/search.html', {'results': results, 'query': query})

# ---------------- รายละเอียดชุด
class OutfitDetailView(View):
    def get(self, request, pk):
        outfit = get_object_or_404(Outfit, pk=pk)
        return render(request, 'outfits/detail.html', {'outfit': outfit})

# ---------------- ฟอร์มเพิ่มชุด (สำหรับ Admin/Staff)
@login_required
def create_outfit(request):
    if not request.user.is_staff:
        messages.error(request, "คุณไม่มีสิทธิ์ในการเพิ่มชุดสินค้า")
        return redirect('outfits:home')
    if request.method == 'POST':
        form = OutfitForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, f"ชุด '{form.cleaned_data['name']}' ถูกเพิ่มเข้าระบบแล้ว")
            return redirect('outfits:outfit-list')
    else:
        form = OutfitForm()
    return render(request, 'outfits/rent_form.html', {'form': form})

# --- Helper function to get or create cart ---
def get_or_create_cart(request):
    cart_id = request.session.get('cart_id')
    cart = None
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, is_paid=False)
        if created and cart_id: # User logged in, had a guest cart session
            try:
                guest_cart = Cart.objects.get(id=cart_id, user__isnull=True, is_paid=False)
                if guest_cart.cart_items_cart.exists() and not cart.cart_items_cart.exists():
                    for item in guest_cart.cart_items_cart.all(): # Reassign items
                        item.cart = cart; item.save()
                    guest_cart.delete() # Delete old guest cart
                elif not guest_cart.cart_items_cart.exists(): guest_cart.delete()
            except Cart.DoesNotExist: pass
        request.session['cart_id'] = cart.id
    else: # Guest user
        if cart_id:
            try: cart = Cart.objects.get(id=cart_id, user__isnull=True, is_paid=False)
            except Cart.DoesNotExist: cart = Cart.objects.create(); request.session['cart_id'] = cart.id
        else: cart = Cart.objects.create(); request.session['cart_id'] = cart.id
    return cart

# ---------------- ตะกร้าสินค้า (Cart View)
def cart_view(request):
    cart = get_or_create_cart(request)
    cart_items_queryset = cart.cart_items_cart.all().order_by('id')
    forms_with_items = []
    all_dates_selected_for_cart = True if cart_items_queryset.exists() else False # False if cart is empty

    for item in cart_items_queryset:
        date_form = CartItemDateSelectionForm(instance=item, prefix=f"item_{item.id}")
        forms_with_items.append({'item': item, 'date_form': date_form})
        if item.is_date_selection_pending: all_dates_selected_for_cart = False

    # Ensure cart total is accurate before rendering.
    # The CartItem.save() and delete() methods should handle updating the cart's total_price.
    # An explicit call here is a fallback.
    new_total_price = cart.calculate_total_price()
    if cart.total_price != new_total_price:
        cart.total_price = new_total_price
        cart.save(update_fields=['total_price'])

    return render(request, 'shop/cart.html', {
        'cart': cart,
        'forms_with_items': forms_with_items,
        'all_dates_selected_for_cart': all_dates_selected_for_cart,
    })

# ---------------- เพิ่มชุดลงตะกร้า
def add_to_cart(request, outfit_id):
    outfit_obj = get_object_or_404(Outfit, id=outfit_id)
    cart = get_or_create_cart(request)
    # For rentals, ensure quantity is 1.
    cart_item, created = CartItem.objects.get_or_create(cart=cart, outfit=outfit_obj, defaults={'quantity': 1})
    if not created: # If item already existed
        if cart_item.quantity != 1: cart_item.quantity = 1
        # Reset dates if re-adding, prompting user to select dates again for this specific item
        cart_item.start_date = None; cart_item.end_date = None; cart_item.item_price_at_rental = Decimal('0.00')
        cart_item.save() # Triggers cart total update
        messages.info(request, f"'{outfit_obj.name}' อยู่ในตะกร้าแล้ว จำนวนถูกตั้งเป็น 1 และกรุณาเลือกวันเช่าใหม่")
    else:
        messages.success(request, f"'{outfit_obj.name}' ถูกเพิ่มลงในตะกร้า กรุณาเลือกวันเช่า")
    return redirect('outfits:cart')

# ---------------- อัปเดตวันเช่าในตะกร้า
def update_cart_item_dates(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart = get_or_create_cart(request)
    if cart_item.cart != cart:
        messages.error(request, "ไม่สามารถอัปเดตรายการนี้ได้"); return redirect('outfits:cart')

    if request.method == 'POST':
        form = CartItemDateSelectionForm(request.POST, instance=cart_item, prefix=f"item_{item_id}")
        if form.is_valid():
            form.save() # This calls CartItem.save(), which updates item_price and cart total
            messages.success(request, f"อัปเดตวันเช่าสำหรับ '{cart_item.outfit.name}' เรียบร้อยแล้ว")
        else:
            error_list = [f"{(form.fields.get(f).label if form.fields.get(f) else f.replace('_', ' ').title())}: {', '.join(e)}" for f, e in form.errors.items()]
            messages.error(request, f"เกิดข้อผิดพลาดในการอัปเดตวันเช่า '{cart_item.outfit.name}': {'; '.join(error_list)}")
    return redirect('outfits:cart')

# ---------------- ลบจากตะกร้า
def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)
    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        outfit_name = cart_item.outfit.name
        cart_item.delete() # This now calls the overridden delete method in CartItem which updates cart total
        messages.success(request, f"'{outfit_name}' ถูกลบออกจากตะกร้าแล้ว")
    except CartItem.DoesNotExist:
        messages.error(request, "ไม่พบรายการที่ต้องการลบในตะกร้า")
    return redirect('outfits:cart')

# ---------------- PromptPay QR Functions
def format_promptpay_payload(phone: str, amount: float = None):
    phone = phone.strip().replace("-", "");
    if phone.startswith("0"): phone = "66" + phone[1:]
    payload = f"00020101021229370016A00000067701011101130066{phone}"
    if amount: amt_str = f"{amount:.2f}"; payload += f"54{len(amt_str):02d}{amt_str}"
    payload += "5802TH5303764"
    crc_payload = payload + "6304"; crc_value = 0xFFFF; polynomial = 0x1021
    for byte in crc_payload.encode('ascii'):
        crc_value ^= (byte << 8)
        for _ in range(8): crc_value = ((crc_value << 1) ^ polynomial) if (crc_value & 0x8000) else (crc_value << 1)
    return payload + f"6304{crc_value & 0xFFFF:04X}"

def generate_qr_base64(phone, amount):
    qr_code_img = qrcode.make(format_promptpay_payload(phone, float(amount)), error_correction=qrcode.constants.ERROR_CORRECT_M)
    buffered = io.BytesIO(); qr_code_img.save(buffered, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"

# ---------------- แสดงหน้าชำระเงิน
@login_required
def payment_qr_view(request):
    cart = get_or_create_cart(request)
    if not cart.cart_items_cart.exists(): messages.warning(request, "ตะกร้าของคุณว่างเปล่า"); return redirect('outfits:cart')
    for item in cart.cart_items_cart.all():
        if item.is_date_selection_pending: messages.error(request, f"กรุณาเลือกวันเช่าสำหรับ '{item.outfit.name}' ก่อนชำระเงิน"); return redirect('outfits:cart')
    
    # Ensure total_price is accurate before payment
    current_total = cart.calculate_total_price()
    if cart.total_price != current_total:
        cart.total_price = current_total
        cart.save(update_fields=['total_price'])
    total = cart.total_price

    if total <= 0: messages.error(request, "ยอดชำระเงินไม่ถูกต้อง (฿0.00)"); return redirect('outfits:cart')
    return render(request, 'outfits/payment_qr.html', {'cart': cart, 'total': total, 'qr_image': generate_qr_base64(settings.PROMPTPAY_NUMBER, total)})

# ---------------- ยืนยันการโอนเงิน
@login_required
def confirm_payment_view(request):
    try: cart = Cart.objects.get(user=request.user, is_paid=False)
    except Cart.DoesNotExist: messages.info(request, "ไม่พบตะกร้าที่รอการชำระเงิน"); return redirect('outfits:order_history')
    
    if request.method == 'POST':
        form = PaymentConfirmationForm(request.POST, request.FILES) # This is a simple forms.Form
        if form.is_valid():
            cart.payment_slip = form.cleaned_data['slip']
            cart.is_paid = True
            cart.paid_at = timezone.now()
            cart.rental_status = 'payment_confirmed'
            cart.save() # Save all changes to the cart
            if 'cart_id' in request.session and request.session['cart_id'] == cart.id: del request.session['cart_id']
            messages.success(request, "การชำระเงินได้รับการยืนยันแล้ว"); return redirect('outfits:payment_success')
        else: messages.error(request, "ข้อมูลในฟอร์มยืนยันการชำระเงินไม่ถูกต้อง")
    else: form = PaymentConfirmationForm()
    return render(request, 'outfits/confirm_payment.html', {'form': form, 'cart': cart})

# ---------------- หน้าแสดงผลการชำระเงินสำเร็จ
@login_required
def payment_success_view(request):
    return render(request, 'outfits/payment_success.html')

# ---------------- ประวัติคำสั่งซื้อที่ชำระแล้ว
@login_required
def order_history_view(request):
    orders_qs = Cart.objects.filter(user=request.user, is_paid=True).order_by('-paid_at')
    processed_orders_context = []
    
    # Store forms with errors if POST fails, to re-render them
    error_forms = {} # Key: order_id, Value: {'upload_form': form_with_error, 'return_form': form_with_error}

    if request.method == 'POST':
        order_id_from_post = request.POST.get('order_id')
        try:
            order_instance = Cart.objects.get(id=order_id_from_post, user=request.user, is_paid=True)
            if 'upload_customer_image' in request.POST:
                form = CustomerOrderImageUploadForm(request.POST, request.FILES, instance=order_instance, prefix=f"order_img_{order_instance.id}")
                if form.is_valid():
                    form.save(); messages.success(request, f"รูปภาพสำหรับคำสั่งซื้อ #{order_instance.id} ถูกอัปโหลดแล้ว")
                    # Optionally update status: order_instance.rental_status = 'issue_reported'; order_instance.save()
                    return redirect('outfits:order_history')
                else:
                    messages.error(request, f"อัปโหลดรูปภาพแจ้งปัญหาล้มเหลว: {form.errors.as_text()}")
                    error_forms[order_instance.id] = {'upload_form': form}
            elif 'submit_return_shipment' in request.POST:
                form = ReturnShipmentForm(request.POST, request.FILES, instance=order_instance, prefix=f"return_shipment_{order_instance.id}")
                if form.is_valid():
                    form.save() # Saves tracking_number and image to order_instance
                    order_instance.rental_status = 'customer_returning'
                    order_instance.save(update_fields=['rental_status','return_tracking_number','return_shipment_image'])
                    messages.success(request, f"ข้อมูลการส่งคืนสำหรับคำสั่งซื้อ #{order_instance.id} ได้รับการบันทึกแล้ว")
                    return redirect('outfits:order_history')
                else:
                    messages.error(request, f"บันทึกข้อมูลการส่งคืนล้มเหลว: {form.errors.as_text()}")
                    error_forms[order_instance.id] = {'return_form': form}
        except Cart.DoesNotExist: messages.error(request, "ไม่พบคำสั่งซื้อ")

    today = timezone.now().date()
    for order in orders_qs:
        # Use form with error if it exists for this order, otherwise create a new one
        upload_form_instance = error_forms.get(order.id, {}).get('upload_form') or \
                               CustomerOrderImageUploadForm(instance=order, prefix=f"order_img_{order.id}")
        return_form_instance = error_forms.get(order.id, {}).get('return_form') or \
                               ReturnShipmentForm(instance=order, prefix=f"return_shipment_{order.id}")
        
        show_return_form_flag = False
        latest_return_date_for_order = order.get_latest_return_date()
        if order.is_paid and \
           order.rental_status in ['shipped', 'delivered'] and \
           not order.return_tracking_number:
            if latest_return_date_for_order and latest_return_date_for_order <= today:
                show_return_form_flag = True
        
        items_details_list = [{
            'name': item.outfit.name,
            'image_url': item.outfit.image.url if item.outfit.image and hasattr(item.outfit.image, 'url') else None,
            'quantity': item.quantity, 'start_date': item.start_date, 'end_date': item.end_date,
            'days': item.get_rental_days(), 'price': item.item_price_at_rental
        } for item in order.cart_items_cart.all()]
        
        processed_orders_context.append({
            'order': order, 'upload_form': upload_form_instance, 'return_form': return_form_instance,
            'show_return_form': show_return_form_flag, 'items_details': items_details_list,
            'latest_return_date': latest_return_date_for_order
        })
        
    return render(request, 'outfits/order_history.html', {'orders_with_forms': processed_orders_context})
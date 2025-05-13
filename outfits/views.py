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
    CustomerOrderImageUploadForm
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
    return render(request, 'outfits/rent_form.html', {'form': form}) # ตรวจสอบชื่อ template นี้

# --- Helper function to get or create cart ---
def get_or_create_cart(request):
    cart_id = request.session.get('cart_id')
    cart = None
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, is_paid=False)
        if created and cart_id:
            try:
                guest_cart = Cart.objects.get(id=cart_id, user__isnull=True, is_paid=False)
                if guest_cart.cart_items_cart.exists() and not cart.cart_items_cart.exists():
                    for item in guest_cart.cart_items_cart.all():
                        item.cart = cart
                        item.save()
                    guest_cart.delete()
                elif not guest_cart.cart_items_cart.exists():
                    guest_cart.delete()
            except Cart.DoesNotExist:
                pass
        request.session['cart_id'] = cart.id
    else:
        if cart_id:
            try:
                cart = Cart.objects.get(id=cart_id, user__isnull=True, is_paid=False)
            except Cart.DoesNotExist:
                cart = Cart.objects.create()
                request.session['cart_id'] = cart.id
        else:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    return cart

# ---------------- ตะกร้าสินค้า (Cart View)
def cart_view(request):
    cart = get_or_create_cart(request)
    cart_items_queryset = cart.cart_items_cart.all().order_by('id')
    forms_with_items = []
    all_dates_selected_for_cart = True  # <<< ตั้งค่าเริ่มต้นเป็น True

    for item in cart_items_queryset:
        date_form = CartItemDateSelectionForm(instance=item, prefix=f"item_{item.id}")
        forms_with_items.append({'item': item, 'date_form': date_form})
        if item.is_date_selection_pending:
            all_dates_selected_for_cart = False  # <<< ถ้ามีรายการไหนยังไม่ได้เลือกวัน ให้เปลี่ยนเป็น False

    current_total_price = cart.calculate_total_price()
    if cart.total_price != current_total_price: # บันทึกเฉพาะเมื่อมีการเปลี่ยนแปลง
        cart.total_price = current_total_price
        cart.save(update_fields=['total_price'])

    return render(request, 'shop/cart.html', {
        'cart': cart,
        'forms_with_items': forms_with_items,
        'all_dates_selected_for_cart': all_dates_selected_for_cart,  # <<< ส่ง flag นี้ไปให้ template
    })

# ---------------- เพิ่มชุดลงตะกร้า
def add_to_cart(request, outfit_id):
    outfit_obj = get_object_or_404(Outfit, id=outfit_id)
    cart = get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        outfit=outfit_obj,
        defaults={'quantity': 1}
    )
    if not created:
        if cart_item.quantity != 1:
            cart_item.quantity = 1
        cart_item.start_date = None
        cart_item.end_date = None
        cart_item.item_price_at_rental = Decimal('0.00')
        cart_item.save()
        messages.info(request, f"'{outfit_obj.name}' ถูกปรับจำนวนเป็น 1 และกรุณาเลือกวันเช่าใหม่")
    else:
        messages.success(request, f"'{outfit_obj.name}' ถูกเพิ่มลงตะกร้าแล้ว กรุณาเลือกวันเช่า")
    return redirect('outfits:cart')

# ---------------- อัปเดตวันเช่าในตะกร้า
def update_cart_item_dates(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart = get_or_create_cart(request)
    if cart_item.cart != cart:
        messages.error(request, "ไม่สามารถอัปเดตรายการนี้ได้")
        return redirect('outfits:cart')
    if request.method == 'POST':
        form = CartItemDateSelectionForm(request.POST, instance=cart_item, prefix=f"item_{item_id}")
        if form.is_valid():
            form.save()
            messages.success(request, f"อัปเดตวันเช่าสำหรับ '{cart_item.outfit.name}' เรียบร้อยแล้ว")
        else:
            error_list = []
            for field, errors in form.errors.items():
                label = form.fields.get(field).label if form.fields.get(field) else field.replace("_", " ").title()
                error_list.append(f"{label}: {', '.join(errors)}")
            messages.error(request, f"เกิดข้อผิดพลาดในการอัปเดตวันเช่า '{cart_item.outfit.name}': {'; '.join(error_list)}")
    return redirect('outfits:cart')

# ---------------- ลบจากตะกร้า
def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)
    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        outfit_name = cart_item.outfit.name
        cart_item.delete()
        cart.calculate_total_price()
        cart.save(update_fields=['total_price'])
        messages.success(request, f"'{outfit_name}' ถูกลบออกจากตะกร้าแล้ว")
    except CartItem.DoesNotExist:
        messages.error(request, "ไม่พบรายการที่ต้องการลบในตะกร้า")
    return redirect('outfits:cart')

# ---------------- PromptPay QR Functions
def format_promptpay_payload(phone: str, amount: float = None):
    phone = phone.strip().replace("-", "")
    if phone.startswith("0"):
        phone = "66" + phone[1:]
    payload = (
        "000201"
        "010212"
        f"29370016A00000067701011101130066{phone}"
    )
    if amount:
        amt_str = f"{amount:.2f}"
        payload += f"54{len(amt_str):02d}{amt_str}"
    payload += "5802TH"
    payload += "5303764"
    crc_payload = payload + "6304"
    crc_value = 0xFFFF
    polynomial = 0x1021
    for byte in crc_payload.encode('ascii'):
        crc_value ^= (byte << 8)
        for _ in range(8):
            if (crc_value & 0x8000):
                crc_value = ((crc_value << 1) ^ polynomial)
            else:
                crc_value = (crc_value << 1)
    crc_value &= 0xFFFF
    return payload + f"6304{crc_value:04X}"

def generate_qr_base64(phone, amount):
    payload = format_promptpay_payload(phone, float(amount))
    qr_code_img = qrcode.make(payload, error_correction=qrcode.constants.ERROR_CORRECT_M)
    buffered = io.BytesIO()
    qr_code_img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# ---------------- แสดงหน้าชำระเงิน
@login_required
def payment_qr_view(request):
    cart = get_or_create_cart(request)
    if not cart.cart_items_cart.exists():
        messages.warning(request, "ตะกร้าของคุณว่างเปล่า")
        return redirect('outfits:cart')
    for item in cart.cart_items_cart.all():
        if item.is_date_selection_pending:
            messages.error(request, f"กรุณาเลือกวันเช่าสำหรับ '{item.outfit.name}' ก่อนชำระเงิน")
            return redirect('outfits:cart')
    cart.calculate_total_price()
    cart.save(update_fields=['total_price'])
    total = cart.total_price
    if total <= 0:
        messages.error(request, "ยอดชำระเงินไม่ถูกต้อง (฿0.00) กรุณาตรวจสอบตะกร้าและวันเช่าของคุณ")
        return redirect('outfits:cart')
    qr_image_data = generate_qr_base64(settings.PROMPTPAY_NUMBER, total)
    return render(request, 'outfits/payment_qr.html', {
        'cart': cart,
        'total': total,
        'qr_image': qr_image_data,
    })

# ---------------- ยืนยันการโอนเงิน
@login_required
def confirm_payment_view(request):
    try:
        cart = Cart.objects.get(user=request.user, is_paid=False)
    except Cart.DoesNotExist:
        messages.info(request, "ไม่พบตะกร้าที่รอการชำระเงิน หรือคุณได้ชำระเงินไปแล้ว")
        return redirect('outfits:order_history')
    if request.method == 'POST':
        form = PaymentConfirmationForm(request.POST, request.FILES)
        if form.is_valid():
            slip_file = form.cleaned_data['slip']
            cart.mark_as_paid(slip_file)
            if 'cart_id' in request.session and request.session['cart_id'] == cart.id:
                del request.session['cart_id']
            messages.success(request, "การชำระเงินได้รับการยืนยันแล้ว คำสั่งซื้อของคุณกำลังดำเนินการ")
            return redirect('outfits:payment_success')
        else:
            messages.error(request, "ข้อมูลในฟอร์มยืนยันการชำระเงินไม่ถูกต้อง กรุณาลองใหม่")
    else:
        form = PaymentConfirmationForm()
    return render(request, 'outfits/confirm_payment.html', {'form': form, 'cart': cart})

# ---------------- หน้าแสดงผลการชำระเงินสำเร็จ
@login_required
def payment_success_view(request):
    return render(request, 'outfits/payment_success.html')

# ---------------- ประวัติคำสั่งซื้อที่ชำระแล้ว
@login_required
def order_history_view(request):
    orders = Cart.objects.filter(user=request.user, is_paid=True).order_by('-paid_at')
    orders_with_forms_and_details = []
    upload_form_from_post_with_error = None

    if request.method == 'POST' and 'upload_customer_image' in request.POST:
        order_id_to_update = request.POST.get('order_id')
        try:
            order_instance = Cart.objects.get(id=order_id_to_update, user=request.user, is_paid=True)
            upload_form_from_post = CustomerOrderImageUploadForm(request.POST, request.FILES, instance=order_instance, prefix=f"order_img_{order_instance.id}")
            if upload_form_from_post.is_valid():
                upload_form_from_post.save()
                messages.success(request, f"รูปภาพสำหรับคำสั่งซื้อ #{order_instance.id} ถูกอัปโหลดแล้ว")
                return redirect('outfits:order_history')
            else:
                upload_form_from_post_with_error = upload_form_from_post # Store form with errors
                messages.error(request, f"เกิดข้อผิดพลาดในการอัปโหลดรูปภาพสำหรับคำสั่งซื้อ #{order_instance.id}: {upload_form_from_post.errors.as_text()}")
        except Cart.DoesNotExist:
            messages.error(request, "ไม่พบคำสั่งซื้อที่ต้องการอัปโหลดรูปภาพ")

    for order in orders:
        current_upload_form = None
        if upload_form_from_post_with_error and str(order.id) == request.POST.get('order_id'):
            current_upload_form = upload_form_from_post_with_error
        else:
            current_upload_form = CustomerOrderImageUploadForm(instance=order, prefix=f"order_img_{order.id}")

        items_details_list = []
        for item in order.cart_items_cart.all():
            items_details_list.append({
                'name': item.outfit.name,
                'image_url': item.outfit.image.url if item.outfit.image else None,
                'quantity': item.quantity,
                'start_date': item.start_date,
                'end_date': item.end_date,
                'days': item.get_rental_days(),
                'price': item.item_price_at_rental
            })
        orders_with_forms_and_details.append({
            'order': order,
            'upload_form': current_upload_form,
            'items_details': items_details_list,
            'latest_return_date': order.get_latest_return_date()
        })

    return render(request, 'outfits/order_history.html', {
        'orders_with_forms': orders_with_forms_and_details,
    })
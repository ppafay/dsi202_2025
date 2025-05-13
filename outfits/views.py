from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.conf import settings

from .models import Outfit, CartItem, Cart
from .forms import OutfitForm, RentForm, PaymentConfirmationForm

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
        results = Outfit.objects.filter(name__icontains=query)
        return render(request, 'outfits/search.html', {'results': results, 'query': query})

# ---------------- รายละเอียดชุด
class OutfitDetailView(View):
    def get(self, request, pk):
        outfit = get_object_or_404(Outfit, pk=pk)
        form = RentForm()
        return render(request, 'outfits/detail.html', {'outfit': outfit, 'form': form})

    def post(self, request, pk):
        outfit = get_object_or_404(Outfit, pk=pk)
        form = RentForm(request.POST)
        if form.is_valid():
            duration = form.cleaned_data['duration']
            total_price = duration * outfit.price
            outfit.is_rented = True
            outfit.save()
            return render(request, 'outfits/rent_success.html', {
                'outfit': outfit,
                'duration': duration,
                'total_price': total_price
            })
        return render(request, 'outfits/detail.html', {'outfit': outfit, 'form': form})

# ---------------- ฟอร์มเพิ่มชุด
def create_outfit(request):
    if request.method == 'POST':
        form = OutfitForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('outfit-list')
    else:
        form = OutfitForm()
    return render(request, 'outfits/rental_form.html', {'form': form})

# ---------------- ตะกร้า
def cart_view(request):
    cart_id = request.session.get('cart_id')
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    else:
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id

    cart.get_total_price()
    return render(request, 'shop/cart.html', {'cart': cart, 'cart_items_list': cart.cart_items_cart.all()})

# ---------------- เพิ่มชุดลงตะกร้า
def add_to_cart(request, outfit_id):
    outfit_obj = get_object_or_404(Outfit, id=outfit_id)
    cart_id = request.session.get('cart_id')
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    else:
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id

    try:
        cart_item = CartItem.objects.get(cart=cart, outfit=outfit_obj)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(cart=cart, outfit=outfit_obj, quantity=1)

    cart.get_total_price()
    return redirect('outfits:cart')

# ---------------- แก้ไขจำนวน
def update_cart(request, item_id):
    cart_id = request.session.get('cart_id')
    if not cart_id:
        return redirect('outfits:cart')

    try:
        cart = Cart.objects.get(id=cart_id)
    except Cart.DoesNotExist:
        return redirect('outfits:cart')

    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
    else:
        quantity = int(request.GET.get('quantity', cart_item.quantity))

    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()

    cart.get_total_price()
    return redirect('outfits:cart')

# ---------------- ลบจากตะกร้า
def remove_from_cart(request, item_id):
    cart_id = request.session.get('cart_id')
    if not cart_id:
        return redirect('outfits:cart')

    try:
        cart = Cart.objects.get(id=cart_id)
    except Cart.DoesNotExist:
        return redirect('outfits:cart')

    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    cart.get_total_price()
    return redirect('outfits:cart')

# ---------------- Login / Logout / Register
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'accounts/login.html')

def user_logout(request):
    logout(request)
    return redirect('home')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

# ---------------- PromptPay QR ฟังก์ชัน
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
    payload += "5802TH5303764"
    crc = calculate_crc16(payload + "6304")
    return payload + f"6304{crc}"

def calculate_crc16(payload):
    poly = 0x1021
    result = 0xFFFF
    for ch in payload:
        result ^= ord(ch) << 8
        for _ in range(8):
            if result & 0x8000:
                result = ((result << 1) ^ poly) & 0xFFFF
            else:
                result = (result << 1) & 0xFFFF
    return f"{result:04X}"

def generate_qr_base64(phone, amount):
    payload = format_promptpay_payload(phone, amount)
    qr = qrcode.make(payload)
    buffered = io.BytesIO()
    qr.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# ---------------- แสดงหน้าชำระเงิน
def payment_qr_view(request):
    cart_id = request.session.get('cart_id')
    if not cart_id:
        return redirect('outfits:cart')

    try:
        cart = Cart.objects.get(id=cart_id)
    except Cart.DoesNotExist:
        return redirect('outfits:cart')

    total = cart.get_total_price()
    qr_image = generate_qr_base64(settings.PROMPTPAY_NUMBER, total)

    return render(request, 'outfits/payment_qr.html', {
        'cart': cart,
        'total': total,
        'qr_image': qr_image,
    })

# ---------------- ยืนยันการโอนเงิน
def confirm_payment_view(request):
    cart_id = request.session.get('cart_id')
    if not cart_id:
        return redirect('outfits:cart')

    cart = get_object_or_404(Cart, id=cart_id)

    if request.method == 'POST':
        form = PaymentConfirmationForm(request.POST, request.FILES)
        if form.is_valid():
            slip = form.cleaned_data['slip']
            cart.payment_slip = slip
            cart.is_paid = True
            cart.save()
            return render(request, 'outfits/payment_success.html')
    else:
        form = PaymentConfirmationForm()

    return render(request, 'outfits/confirm_payment.html', {'form': form, 'cart': cart})

# ---------------- ประวัติคำสั่งซื้อที่ชำระแล้ว
@login_required
def order_history_view(request):
    carts = Cart.objects.filter(is_paid=True)
    return render(request, 'outfits/order_history.html', {'carts': carts})
